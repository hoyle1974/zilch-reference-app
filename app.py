#!/usr/bin/env python3
"""
Zilch Reference Application
Demonstrates all Zilch Phase 1 + Phase 2 + Phase 3 services and their status.
"""

import os
import json
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)


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
    }

    return services


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
            <div class="service-card {{ 'enabled' if service.enabled else 'disabled' }}">
                <div class="service-status">{{ service.status }}</div>
                <div class="service-name">{{ service_name }}</div>
                <p class="service-description">{{ service.description }}</p>
                <div class="service-env">
                    {% for env_var in service.env_vars %}
                    <div>{{ env_var }}</div>
                    {% endfor %}
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
            </div>
        </div>

        <div class="footer">
            <p>Generated on {{ timestamp }} | Zilch Phase 1 + Phase 2 + Phase 3 Reference Application | Revision: {{ deployment.revision }}</p>
            <p style="margin-top: 10px; color: #ccc;">💡 This app reads Zilch environment variables set by Cloud Run. Visit <code>/.json</code> for raw API response.</p>
        </div>
    </div>
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
