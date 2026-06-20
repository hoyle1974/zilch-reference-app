#!/usr/bin/env python3
"""
Zilch Reference Application
Demonstrates all Zilch services and their status.
"""

import os
import json
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import mysql.connector
from google.cloud import firestore, storage, bigquery, pubsub_v1, secretmanager

app = Flask(__name__)

_secret_cache = {}

def resolve_secret(value):
    """Resolve sm:// prefixed secrets from Secret Manager."""
    if not value or not value.startswith("sm://"):
        return value

    if value in _secret_cache:
        return _secret_cache[value]

    try:
        secret_id = value[5:]  # Remove "sm://" prefix
        project = os.getenv("ZILCH_PROJECT_ID", "")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        _secret_cache[value] = secret_value
        return secret_value
    except Exception:
        return value


def check_service_status():
    """Check which Zilch services are enabled and available."""
    services = {
        "Cloud Run": {
            "enabled": True,  # Always enabled
            "env_vars": ["ZILCH_PROJECT_ID", "ZILCH_APP_NAME"],
            "description": "Serverless container platform",
            "status": "✅ ACTIVE",
        },
        "Firestore": {
            "enabled": os.getenv("ZILCH_FIRESTORE_DATABASE") != "",
            "env_vars": ["ZILCH_FIRESTORE_DATABASE"],
            "description": "NoSQL database (1GB free tier, 50K reads/day)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_FIRESTORE_DATABASE") else "⭕ DISABLED",
        },
        "Secret Manager": {
            "enabled": os.getenv("ZILCH_SECRET_PREFIX") != "",
            "env_vars": ["ZILCH_SECRET_PREFIX"],
            "description": "Secure credential storage (6 secrets, 10K API calls/month)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_SECRET_PREFIX") else "⭕ DISABLED",
        },
        "Cloud Storage": {
            "enabled": os.getenv("ZILCH_STORAGE_BUCKET") != "",
            "env_vars": ["ZILCH_STORAGE_BUCKET"],
            "description": "Object storage (5GB free tier, 1GB/month egress)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_STORAGE_BUCKET") else "⭕ DISABLED",
        },
        "Firebase Auth": {
            "enabled": os.getenv("ZILCH_FIREBASE_ENABLED") == "true",
            "env_vars": ["ZILCH_FIREBASE_ENABLED"],
            "description": "User authentication (unlimited free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_FIREBASE_ENABLED") == "true" else "⭕ DISABLED",
        },
        "Vertex AI": {
            "enabled": os.getenv("ZILCH_VERTEX_AI_ENABLED") == "true",
            "env_vars": ["ZILCH_VERTEX_AI_ENABLED"],
            "description": "ML/AI APIs including Gemini (free tier limits apply)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_VERTEX_AI_ENABLED") == "true" else "⭕ DISABLED",
        },
        "Pub/Sub": {
            "enabled": os.getenv("ZILCH_PUBSUB_TOPIC") != "",
            "env_vars": ["ZILCH_PUBSUB_TOPIC", "ZILCH_PUBSUB_SUBSCRIPTION"],
            "description": "Event streaming and messaging (10 GB/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_PUBSUB_TOPIC") else "⭕ DISABLED",
        },
        "Cloud Tasks": {
            "enabled": os.getenv("ZILCH_CLOUD_TASKS_QUEUE") != "",
            "env_vars": ["ZILCH_CLOUD_TASKS_QUEUE"],
            "description": "Async job queues (1M tasks/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_CLOUD_TASKS_QUEUE") else "⭕ DISABLED",
        },
        "BigQuery": {
            "enabled": os.getenv("ZILCH_BIGQUERY_DATASET") != "",
            "env_vars": ["ZILCH_BIGQUERY_DATASET"],
            "description": "Analytics warehouse (1 TB queried/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_BIGQUERY_DATASET") else "⭕ DISABLED",
        },
        "Cloud KMS": {
            "enabled": os.getenv("ZILCH_KMS_KEY_ID") != "",
            "env_vars": ["ZILCH_KMS_KEY_ID"],
            "description": "Encryption key management (6 keys, 10K API calls/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_KMS_KEY_ID") else "⭕ DISABLED",
        },
        "Vision AI": {
            "enabled": os.getenv("ZILCH_VISION_AI_ENABLED") == "true",
            "env_vars": ["ZILCH_VISION_AI_ENABLED"],
            "description": "Image processing and analysis (1,000 images/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_VISION_AI_ENABLED") == "true" else "⭕ DISABLED",
        },
        "Speech-to-Text": {
            "enabled": os.getenv("ZILCH_SPEECH_TO_TEXT_ENABLED") == "true",
            "env_vars": ["ZILCH_SPEECH_TO_TEXT_ENABLED"],
            "description": "Audio transcription (60 minutes/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_SPEECH_TO_TEXT_ENABLED") == "true" else "⭕ DISABLED",
        },
        "Translation API": {
            "enabled": os.getenv("ZILCH_TRANSLATION_ENABLED") == "true",
            "env_vars": ["ZILCH_TRANSLATION_ENABLED"],
            "description": "Multi-language support (500K characters/month free tier)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_TRANSLATION_ENABLED") == "true" else "⭕ DISABLED",
        },
        "MySQL Database": {
            "enabled": os.getenv("ZILCH_MYSQL_HOST") != "",
            "env_vars": ["ZILCH_MYSQL_HOST", "ZILCH_MYSQL_PORT", "ZILCH_MYSQL_USER", "ZILCH_MYSQL_PASSWORD", "ZILCH_MYSQL_DATABASE"],
            "description": "Relational database on e2-micro VM (~$1.26/month)",
            "status": "✅ ENABLED" if os.getenv("ZILCH_MYSQL_HOST") else "⭕ DISABLED",
        },
    }

    return services


def check_mysql_health():
    """Check MySQL database connectivity."""
    if not os.getenv("ZILCH_MYSQL_HOST"):
        return {"status": "disabled", "message": "MySQL not configured"}

    host = os.getenv("ZILCH_MYSQL_HOST")
    port = os.getenv("ZILCH_MYSQL_PORT", "3306")
    user = os.getenv("ZILCH_MYSQL_USER")
    password_env = os.getenv("ZILCH_MYSQL_PASSWORD", "")
    database = os.getenv("ZILCH_MYSQL_DATABASE")

    try:
        password = resolve_secret(password_env)
        debug_info = f"Connecting to {host}:{port} as {user}. Password env: {password_env[:20]}{'...' if len(password_env) > 20 else ''} (resolved: {len(password)} chars)"

        conn = mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            connection_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "online", "message": f"Connected successfully. {debug_info}"}
    except Exception as e:
        debug_info = f"Tried {host}:{port} as {user}. Password env: {password_env[:20]}{'...' if len(password_env) > 20 else ''}"
        return {"status": "offline", "message": f"{str(e)[:100]}. {debug_info}"}


def check_firestore_health():
    """Check Firestore connectivity."""
    if not os.getenv("ZILCH_FIRESTORE_DATABASE"):
        return {"status": "disabled", "message": "Firestore not configured"}

    try:
        project = os.getenv("ZILCH_PROJECT_ID", "")
        db = firestore.Client(project=project)
        db.collection("_health_check").limit(1).get()
        return {"status": "online", "message": "Connected successfully"}
    except Exception as e:
        return {"status": "offline", "message": str(e)[:100]}


def check_cloud_storage_health():
    """Check Cloud Storage connectivity."""
    if not os.getenv("ZILCH_STORAGE_BUCKET"):
        return {"status": "disabled", "message": "Cloud Storage not configured"}

    try:
        project = os.getenv("ZILCH_PROJECT_ID", "")
        client = storage.Client(project=project)
        bucket_name = os.getenv("ZILCH_STORAGE_BUCKET")
        list(client.list_blobs(bucket_name, max_results=1))
        return {"status": "online", "message": "Connected successfully"}
    except Exception as e:
        return {"status": "offline", "message": str(e)[:100]}


def check_bigquery_health():
    """Check BigQuery connectivity."""
    if not os.getenv("ZILCH_BIGQUERY_DATASET"):
        return {"status": "disabled", "message": "BigQuery not configured"}

    try:
        project = os.getenv("ZILCH_PROJECT_ID", "")
        client = bigquery.Client(project=project)
        dataset_id = os.getenv("ZILCH_BIGQUERY_DATASET")
        dataset = client.get_dataset(dataset_id)
        return {"status": "online", "message": "Connected successfully"}
    except Exception as e:
        return {"status": "offline", "message": str(e)[:100]}


def check_pubsub_health():
    """Check Pub/Sub connectivity."""
    if not os.getenv("ZILCH_PUBSUB_TOPIC"):
        return {"status": "disabled", "message": "Pub/Sub not configured"}

    try:
        project = os.getenv("ZILCH_PROJECT_ID", "")
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project, os.getenv("ZILCH_PUBSUB_TOPIC"))
        publisher.get_topic(request={"topic": topic_path})
        return {"status": "online", "message": "Connected successfully"}
    except Exception as e:
        return {"status": "offline", "message": str(e)[:100]}


def get_all_health_checks():
    """Get health checks for all services."""
    health_status = {
        "MySQL Database": check_mysql_health(),
        "Firestore": check_firestore_health(),
        "Cloud Storage": check_cloud_storage_health(),
        "BigQuery": check_bigquery_health(),
        "Pub/Sub": check_pubsub_health(),
    }
    return health_status


def get_environment_info():
    """Get Zilch environment information."""
    return {
        "project_id": os.getenv("ZILCH_PROJECT_ID", "Not set"),
        "app_name": os.getenv("ZILCH_APP_NAME", "Not set"),
        "firestore_db": os.getenv("ZILCH_FIRESTORE_DATABASE", "Not set"),
        "secret_prefix": os.getenv("ZILCH_SECRET_PREFIX", "Not set"),
        "storage_bucket": os.getenv("ZILCH_STORAGE_BUCKET", "Not set"),
        "firebase_enabled": os.getenv("ZILCH_FIREBASE_ENABLED", "Not set"),
        "vertex_ai_enabled": os.getenv("ZILCH_VERTEX_AI_ENABLED", "Not set"),
        "pubsub_topic": os.getenv("ZILCH_PUBSUB_TOPIC", "Not set"),
        "pubsub_subscription": os.getenv("ZILCH_PUBSUB_SUBSCRIPTION", "Not set"),
        "cloud_tasks_queue": os.getenv("ZILCH_CLOUD_TASKS_QUEUE", "Not set"),
        "bigquery_dataset": os.getenv("ZILCH_BIGQUERY_DATASET", "Not set"),
        "kms_key_id": os.getenv("ZILCH_KMS_KEY_ID", "Not set"),
        "vision_ai_enabled": os.getenv("ZILCH_VISION_AI_ENABLED", "Not set"),
        "speech_to_text_enabled": os.getenv("ZILCH_SPEECH_TO_TEXT_ENABLED", "Not set"),
        "translation_enabled": os.getenv("ZILCH_TRANSLATION_ENABLED", "Not set"),
        "mysql_host": os.getenv("ZILCH_MYSQL_HOST", "Not set"),
        "mysql_port": os.getenv("ZILCH_MYSQL_PORT", "Not set"),
        "mysql_user": os.getenv("ZILCH_MYSQL_USER", "Not set"),
        "mysql_password": os.getenv("ZILCH_MYSQL_PASSWORD", "Not set"),
        "mysql_database": os.getenv("ZILCH_MYSQL_DATABASE", "Not set"),
    }


def get_deployment_info():
    """Get Cloud Run deployment metadata."""
    return {
        "revision": os.getenv("K_REVISION", "local-development"),
        "service": os.getenv("K_SERVICE", "local"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Zilch Status Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 900px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 0.95em;
        }
        .info-box {
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 4px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 10px;
        }
        .info-item {
            display: flex;
            flex-direction: column;
        }
        .info-label {
            color: #999;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .info-value {
            color: #333;
            font-weight: 500;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 0.95em;
            word-break: break-all;
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .service-card {
            border: 2px solid #eee;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        .service-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
        }
        .service-card.enabled {
            background: #f0f9ff;
            border-color: #10b981;
        }
        .service-card.disabled {
            background: #fef3f2;
            border-color: #f97316;
            opacity: 0.8;
        }
        .service-status {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .service-name {
            color: #333;
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .service-description {
            color: #666;
            font-size: 0.9em;
            line-height: 1.4;
            margin-bottom: 12px;
        }
        .service-env {
            background: white;
            padding: 10px;
            border-radius: 4px;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 0.85em;
            color: #333;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 0.9em;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
            margin-right: 5px;
        }
        .badge-enabled {
            background: #d1fae5;
            color: #065f46;
        }
        .badge-disabled {
            background: #fee2e2;
            color: #991b1b;
        }
        .section-title {
            color: #333;
            font-size: 1.3em;
            font-weight: 700;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .deployment-badge {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 4px solid #047857;
        }
        .deployment-status {
            font-size: 1.1em;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .deployment-details {
            font-size: 0.95em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .detail-label {
            font-weight: 600;
            min-width: 80px;
        }
        .deployment-badge code {
            background: rgba(0, 0, 0, 0.2);
            padding: 4px 8px;
            border-radius: 4px;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 0.9em;
        }
        .health-status {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            font-size: 0.9em;
        }
        .health-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .health-indicator.online {
            background: #10b981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }
        .health-indicator.offline {
            background: #ef4444;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
        }
        .health-indicator.disabled {
            background: #9ca3af;
        }
        .health-message {
            color: #666;
            font-size: 0.85em;
        }
        .health-message.error {
            color: #dc2626;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 Zilch Status Dashboard</h1>
        <p class="subtitle">Service availability and configuration for this Cloud Run deployment</p>

        <div class="deployment-badge">
            <div class="deployment-status">🚀 LIVE DEPLOYMENT</div>
            <div class="deployment-details">
                <span class="detail-label">Revision:</span> <code>{{ deployment.revision }}</code>
            </div>
            <div class="deployment-details">
                <span class="detail-label">Deployed:</span> <span>{{ deployment.timestamp }}</span>
            </div>
        </div>

        <div class="info-box">
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Project ID</span>
                    <span class="info-value">{{ env.project_id }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Application Name</span>
                    <span class="info-value">{{ env.app_name }}</span>
                </div>
            </div>
        </div>

        <h2 class="section-title">📦 Available Services</h2>
        <div class="services-grid">
            {% for service_name, service in services.items() %}
            <div class="service-card {{ 'enabled' if service.enabled else 'disabled' }}" data-service="{{ service_name }}">
                <div class="service-status">{{ service.status }}</div>
                <div class="service-name">{{ service_name }}</div>
                <p class="service-description">{{ service.description }}</p>
                <div class="service-env">
                    {% for env_var in service.env_vars %}
                    <div>{{ env_var }}</div>
                    {% endfor %}
                </div>
                <div class="health-status" id="health-{{ service_name | replace(' ', '-') }}" style="display: none;">
                    <span class="health-indicator"></span>
                    <span class="health-message"></span>
                </div>
            </div>
            {% endfor %}
        </div>

        <h2 class="section-title">🔐 Environment Variables</h2>
        <div class="info-box">
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Firestore Database</span>
                    <span class="info-value">{{ env.firestore_db }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Secret Prefix</span>
                    <span class="info-value">{{ env.secret_prefix }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Storage Bucket</span>
                    <span class="info-value">{{ env.storage_bucket }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Firebase Enabled</span>
                    <span class="info-value">{{ env.firebase_enabled }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Vertex AI Enabled</span>
                    <span class="info-value">{{ env.vertex_ai_enabled }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Pub/Sub Topic</span>
                    <span class="info-value">{{ env.pubsub_topic }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Cloud Tasks Queue</span>
                    <span class="info-value">{{ env.cloud_tasks_queue }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">BigQuery Dataset</span>
                    <span class="info-value">{{ env.bigquery_dataset }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">KMS Key ID</span>
                    <span class="info-value">{{ env.kms_key_id }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Vision AI Enabled</span>
                    <span class="info-value">{{ env.vision_ai_enabled }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Speech-to-Text Enabled</span>
                    <span class="info-value">{{ env.speech_to_text_enabled }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Translation Enabled</span>
                    <span class="info-value">{{ env.translation_enabled }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">MySQL Host</span>
                    <span class="info-value">{{ env.mysql_host }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">MySQL Port</span>
                    <span class="info-value">{{ env.mysql_port }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">MySQL User</span>
                    <span class="info-value">{{ env.mysql_user }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">MySQL Password</span>
                    <span class="info-value">{{ env.mysql_password }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">MySQL Database</span>
                    <span class="info-value">{{ env.mysql_database }}</span>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated on {{ timestamp }} | Zilch Reference Application | Revision: {{ deployment.revision }}</p>
            <p style="margin-top: 10px; color: #ccc;">💡 This app reads Zilch environment variables set by Cloud Run. Visit <code>/.json</code> for raw API response.</p>
        </div>
    </div>

    <script>
        async function loadHealthChecks() {
            try {
                const response = await fetch('/health-check');
                const data = await response.json();

                for (const [serviceName, health] of Object.entries(data)) {
                    const elementId = 'health-' + serviceName.replace(/ /g, '-');
                    const element = document.getElementById(elementId);

                    if (element) {
                        const indicator = element.querySelector('.health-indicator');
                        const message = element.querySelector('.health-message');

                        indicator.className = 'health-indicator ' + health.status;
                        message.className = 'health-message' + (health.status === 'offline' ? ' error' : '');

                        if (health.status === 'online') {
                            message.textContent = 'Online';
                        } else if (health.status === 'offline') {
                            message.textContent = 'Offline: ' + health.message;
                        } else if (health.status === 'disabled') {
                            message.textContent = 'Disabled';
                        }

                        element.style.display = 'flex';
                    }
                }
            } catch (error) {
                console.error('Failed to load health checks:', error);
            }
        }

        document.addEventListener('DOMContentLoaded', loadHealthChecks);
    </script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    """Display the Zilch services dashboard."""
    services = check_service_status()
    env = get_environment_info()
    deployment = get_deployment_info()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    return render_template_string(
        HTML_TEMPLATE,
        services=services,
        env=env,
        deployment=deployment,
        timestamp=timestamp
    )


@app.route("/.json")
def dashboard_json():
    """Return status as JSON API."""
    services = check_service_status()
    env = get_environment_info()

    # Convert services to JSON-serializable format
    services_json = {}
    for name, info in services.items():
        services_json[name] = {
            "enabled": info["enabled"],
            "status": info["status"],
            "description": info["description"],
            "environment_variables": info["env_vars"],
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "project": env["project_id"],
        "app_name": env["app_name"],
        "environment": env,
        "services": services_json,
    }


@app.route("/health")
def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}, 200


@app.route("/health-check")
def health_check_endpoint():
    """Return health status for all services."""
    health_status = get_all_health_checks()
    return jsonify(health_status)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
