# Zilch Reference Application

A minimal but complete Cloud Run application that demonstrates **all Zilch services** (Phase 1 through Phase 4) and their current status.

## Overview

This Flask application provides a real-time dashboard showing:
- ✅ Which Zilch services are enabled
- 📊 Live environment variable values
- 🔍 Service descriptions and quota limits
- 📡 JSON API endpoint for programmatic access

## Quick Start

### 1. Deploy with Zilch

Clone the Zilch framework and customize for this app:

```bash
# Copy the reference app
cd ~/code/zilch-reference-app

# Update .zilch.config with your settings
nano .zilch.config
# Change: gcp_project_id to your actual GCP project ID
# Change: github_owner to your GitHub username
# Customize: app_name, enable services as needed

# Run Zilch deployment
bash ~/code/zilch-gcp/deploy.sh

# Script will prompt for configuration and then run Terraform
```

### Real Deployment Example

Here's what a successful deployment looks like:

```
=================================================================
 🎉 SUCCESS: Zilch Architecture Instantiated Successfully!
=================================================================
📍 Service Endpoint URL: https://gulp-app-atnajubp4a-uc.a.run.app
👤 Bound Run Identity:   gulp-app@test-z-1-499406.iam.gserviceaccount.com
🌐 Operational Region:   us-central1

📋 Available Runtime Application Discovery Environment Tunnels:
  ↳ ZILCH_FIRESTORE_DATABASE : (default)
  ↳ ZILCH_SECRET_PREFIX      : gulp-app-

💡 Reminder: Your setup operates completely on Google's Free tier limits.
   Track parameters safely via: https://cloud.google.com/always-free

📚 Next Steps:
   1. Deploy your code: gcloud run deploy gulp-app --source .
   2. View logs: gcloud run logs read gulp-app --region=us-central1
=================================================================
```

**What this tells you:**
- ✅ Cloud Run service is live at the URL shown
- ✅ Service account created with proper IAM binding
- ✅ Firestore database created (ZILCH_FIRESTORE_DATABASE env var)
- ✅ Secret Manager enabled (ZILCH_SECRET_PREFIX env var)
- ✅ All resources in Always Free tier region (us-central1)

### 2. View the Dashboard

Once deployed, visit your Cloud Run URL:

```
https://zilch-reference-app-<random>.run.app
```

### 3. Check Raw Status (JSON)

Programmatic access:

```bash
curl https://zilch-reference-app-<random>.run.app/.json | jq
```

## Features

### Dashboard View (`/`)

Beautiful HTML dashboard showing:
- **Service Cards** - Enable/disable status for each service
- **Environment Info** - Project ID, app name, configuration
- **Environment Variables** - Raw values Zilch injected
- **Quota Information** - Free tier limits for each service

### JSON API (`/.json`)

Machine-readable status:

```json
{
  "timestamp": "2026-06-14T12:34:56.789012",
  "project": "my-gcp-project",
  "app_name": "zilch-reference-app",
  "environment": {
    "project_id": "my-gcp-project",
    "firestore_db": "(default)",
    "storage_bucket": "zilch-reference-app-storage-abcd1234",
    "secret_prefix": "zilch-reference-app-",
    "firebase_enabled": "true",
    "vertex_ai_enabled": "true"
  },
  "services": {
    "Cloud Run": {
      "enabled": true,
      "status": "✅ ACTIVE",
      "description": "Serverless container platform",
      "environment_variables": ["ZILCH_PROJECT_ID", "ZILCH_APP_NAME"]
    },
    ...
  }
}
```

### Health Check Endpoints

**Basic Health Check (`/health`)** — Cloud Run and Kubernetes-compatible:

```bash
curl https://zilch-reference-app-<random>.run.app/health
# {"status":"healthy"}
```

**Service Status Check (`/health-check`)** — Detailed status for all Zilch services:

```bash
curl https://zilch-reference-app-<random>.run.app/health-check
# {
#   "BigQuery": {"status": "disabled", "message": "BigQuery not configured"},
#   "Cloud Storage": {"status": "disabled", "message": "Cloud Storage not configured"},
#   "Firestore": {"status": "disabled", "message": "Firestore not configured"},
#   "MySQL Database": {
#     "status": "online",
#     "message": "Connected successfully..."
#   },
#   "Pub/Sub": {"status": "disabled", "message": "Pub/Sub not configured"}
# }
```

The `/health-check` endpoint tests actual connectivity to each service and displays:
- **enabled/disabled** — Whether service is provisioned
- **online/offline** — Whether service is reachable and working
- **message** — Connection details or error message

## What It Demonstrates

### Phase 1 Services

| Service | Demonstrated |
|---------|--------------|
| **Cloud Run** | ✅ Always enabled (core platform) |
| **Firestore** | ✅ Reads `ZILCH_FIRESTORE_DATABASE` env var |
| **Secret Manager** | ✅ Reads `ZILCH_SECRET_PREFIX` env var |
| **Cloud Storage** | ✅ Reads `ZILCH_STORAGE_BUCKET` env var |
| **Firebase Auth** | ✅ Reads `ZILCH_FIREBASE_ENABLED` env var |
| **Vertex AI** | ✅ Reads `ZILCH_VERTEX_AI_ENABLED` env var |

### Phase 2: CI/CD Features

| Feature | How It's Used |
|---------|---------------|
| **Cloud Build** | This app is deployed via Cloud Build on every `git push` |
| **Artifact Registry** | Container image stored in private registry |
| **GitOps Workflow** | Push code → auto-build → auto-deploy |
| **Environment Variables** | All Zilch config injected automatically |

### Phase 3: Advanced Services

| Service | Demonstrated |
|---------|--------------|
| **Pub/Sub** | ✅ Reads `ZILCH_PUBSUB_TOPIC` env var |
| **Cloud Tasks** | ✅ Reads `ZILCH_CLOUD_TASKS_QUEUE` env var |
| **BigQuery** | ✅ Reads `ZILCH_BIGQUERY_DATASET` env var |
| **Cloud KMS** | ✅ Reads `ZILCH_KMS_KEY_ID` env var |
| **Vision AI** | ✅ Reads `ZILCH_VISION_AI_ENABLED` env var |
| **Speech-to-Text** | ✅ Reads `ZILCH_SPEECH_TO_TEXT_ENABLED` env var |
| **Translation** | ✅ Reads `ZILCH_TRANSLATION_ENABLED` env var |

### Phase 4: Scheduler & Monitoring

| Service | How It's Used |
|---------|---------------|
| **Cloud Scheduler** | Optional cron jobs that POST to `/api/cron` endpoint |
| **Cloud Monitoring** | Error rate alerts and emergency circuit breaker |
| **Budget Alerts** | Notifications when spending approaches limits |

### MySQL Database

| Feature | How It's Used |
|---------|---------------|
| **MySQL Database** | ✅ Reads `ZILCH_MYSQL_HOST`, `ZILCH_MYSQL_PORT`, `ZILCH_MYSQL_USER`, `ZILCH_MYSQL_PASSWORD`, `ZILCH_MYSQL_DATABASE` env vars |
| **Connection** | Public IP + randomized port with strong password (non-standard port provides security layer) |
| **Migrations** | Database schema managed via migration scripts in `db/migrations/` |
| **Health Checks** | `/health-check` endpoint verifies MySQL connectivity and displays status |
| **Security** | MySQL password securely injected by Cloud Run from Secret Manager (not in env vars or Terraform state) |

**Implementation Details:**

- Cloud Run service receives MySQL connection info from Terraform outputs
- Password is injected securely via `secret_key_ref` (Secret Manager reference)
- App reads standard `ZILCH_MYSQL_*` environment variables
- Health check endpoint tests connectivity and reports status in real-time
- Firewall rules restrict access to non-standard port from specific sources

## Local Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set test environment variables (Phase 1 + 2)
export ZILCH_PROJECT_ID="test-project"
export ZILCH_APP_NAME="zilch-reference-app"
export ZILCH_FIRESTORE_DATABASE="(default)"
export ZILCH_STORAGE_BUCKET="test-bucket"
export ZILCH_SECRET_PREFIX="test-"
export ZILCH_FIREBASE_ENABLED="true"

# Phase 3 services (optional)
export ZILCH_PUBSUB_TOPIC="test-topic"
export ZILCH_PUBSUB_SUBSCRIPTION="test-subscription"
export ZILCH_CLOUD_TASKS_QUEUE="projects/test-project/locations/us-central1/queues/test-queue"
export ZILCH_BIGQUERY_DATASET="test_dataset"
export ZILCH_VISION_AI_ENABLED="true"
export ZILCH_SPEECH_TO_TEXT_ENABLED="true"
export ZILCH_TRANSLATION_ENABLED="true"

# MySQL database (optional)
export ZILCH_MYSQL_HOST="127.0.0.1"
export ZILCH_MYSQL_PORT="3306"
export ZILCH_MYSQL_USER="test_user"
export ZILCH_MYSQL_PASSWORD="test_password"
export ZILCH_MYSQL_DATABASE="test_db"

# Run Flask app
python app.py

# Visit http://localhost:8080
```

### Using Secrets Locally

For the MySQL password and other sensitive values, use environment variables or a `.env.local` file:

**Option 1: Set environment variable directly**

```bash
export ZILCH_MYSQL_PASSWORD="local_test_password"
python app.py
```

**Option 2: Create `.env.local` file (recommended)**

```bash
cat > .env.local <<EOF
export ZILCH_MYSQL_PASSWORD="local_test_password"
EOF

source .env.local
python app.py
```

The `.env.local` file is git-ignored and safe for storing local test credentials.

**In production (Cloud Run):** The app fetches `ZILCH_MYSQL_PASSWORD` from Google Secret Manager, not from environment variables.

### Build Docker Image Locally

```bash
docker build -t zilch-reference-app:latest .
docker run -p 8080:8080 \
  -e ZILCH_PROJECT_ID="test-project" \
  -e ZILCH_APP_NAME="zilch-reference-app" \
  -e ZILCH_FIRESTORE_DATABASE="(default)" \
  zilch-reference-app:latest
```

## Code Structure

- **`app.py`** - Main Flask application
  - `check_service_status()` - Query all Zilch services
  - `get_environment_info()` - Read injected env vars
  - `@app.route("/")` - HTML dashboard
  - `@app.route("/.json")` - JSON API
  - `@app.route("/health")` - Health check

- **`Dockerfile`** - Container definition
  - Base: `python:3.11-slim`
  - Health check endpoint
  - PORT environment variable for Cloud Run

- **`.zilch.config`** - Zilch deployment configuration
  - GitHub integration settings
  - Feature toggles (enable/disable services)
  - Cloud Build integration

- **`requirements.txt`** - Python dependencies

## Integration with Zilch

### How Environment Variables Are Injected

When you deploy this app with Zilch:

1. **Initial Setup** - `./deploy.sh` reads `.zilch.config`
2. **Feature Toggles** - You choose which services to enable
3. **Terraform** - Provisions resources (Firestore, Storage, etc.)
4. **Cloud Run** - Injects environment variables before starting the container
5. **App** - Reads `ZILCH_*` env vars and reports status

### Example Deployment Flow

```bash
# 1. Configure the app
cd ~/code/zilch-reference-app
nano .zilch.config

# 2. Run Zilch (from Zilch repo)
bash ~/code/zilch-gcp/deploy.sh

# Prompts for:
# - Project ID, app name, region
# - Feature toggles (Firestore, Storage, etc.)
# - Cloud Build (GitHub integration)

# 3. Zilch creates:
# - Cloud Run service with env vars
# - Firestore database (if enabled)
# - Storage bucket (if enabled)
# - Cloud Build trigger (if enabled)

# 4. App starts automatically with all env vars set

# 5. Visit dashboard to see what's available
```

## Testing the Dashboard

### Verify All Services Are Visible

After deployment, check:

```bash
# Get app URL
APP_URL=$(gcloud run services describe zilch-reference-app \
  --region=us-central1 \
  --format='value(status.url)')

# View dashboard
open $APP_URL

# Check API
curl $APP_URL/.json | jq .services
```

### Simulate Partial Setup

To test with only some services enabled:

```bash
# Edit .zilch.config to disable services
nano .zilch.config

# Set only these to true:
enable_firestore=true
enable_secret_manager=false
enable_cloud_storage=false

# Re-run deploy.sh
bash ~/code/zilch-gcp/deploy.sh

# Dashboard now shows disabled services
```

## Always Free Tier Compliance

This reference app demonstrates sustainable usage:

- **Flask** - Minimal resource footprint
- **No background jobs** - Everything on-demand
- **No expensive APIs** - Just reads environment variables
- **Health checks** - Cloud Run can auto-restart if needed

All services accessed are within Always Free tier limits:
- Cloud Run: 2M requests/month free
- Firestore: 1GB storage, 50K reads/day free
- Cloud Storage: 5GB free
- No ongoing charges (except data egress)

## Troubleshooting

### Dashboard shows "Not set" for environment variables

**Cause:** Service was not enabled during deployment

**Fix:** 
1. Verify `.zilch.config` has the service enabled
2. Re-run `./deploy.sh` to update infrastructure
3. Cloud Run will restart with new env vars

### Verifying Deployment Success

After running `./deploy.sh`, look for:

```
✅ Resources: 4 added, 1 changed, 0 destroyed.
✅ Service Endpoint URL: https://...
✅ Bound Run Identity: app-name@project.iam.gserviceaccount.com
✅ Available Runtime Application Discovery Environment Tunnels
```

**If you see these**, the deployment succeeded!

### Health check fails after deployment

**Cause:** Container startup time or port misconfiguration

**Check logs:**
```bash
gcloud run logs read app-name --region=us-central1 --limit=50
```

**Check service:**
```bash
gcloud run services describe app-name --region=us-central1
```

### App returns 503 or times out

**Cause:** Cloud Run is still starting the container

**Wait:** Cloud Run takes 30-60 seconds to start after deployment

**Check:**
```bash
curl -v https://your-app-url/health
```

### "Hello World" image appears instead of your app

**Cause:** Cloud Build hasn't deployed yet (Phase 2 only)

**Check:**
```bash
gcloud builds log --stream LATEST
```

**Expected:** Build takes 3-5 minutes. Cloud Run auto-pulls new image when ready.

### Terraform shows "resource already exists"

**Cause:** Re-running `./deploy.sh` on existing infrastructure

**Solution:** This is normal. Terraform updates resources in-place. If you see:
```
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

This means Terraform safely updated only what changed.

### Service account permissions errors

**Cause:** IAM roles not yet applied

**Check:**
```bash
gcloud projects get-iam-policy test-z-1-499406 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:app-name@*"
```

**Expected:** Service account should have these roles:
- `roles/run.invoker` (public access)
- `roles/datastore.user` (if Firestore enabled)
- `roles/secretmanager.secretAccessor` (if Secret Manager enabled)

## Using MySQL with the Reference App

If you enabled MySQL during `./deploy.sh`, your app receives connection details automatically:

### Connecting to MySQL from Python

```python
import mysql.connector
import os

if os.getenv('ZILCH_MYSQL_HOST'):
    db = mysql.connector.connect(
        host=os.getenv('ZILCH_MYSQL_HOST'),
        port=int(os.getenv('ZILCH_MYSQL_PORT', 3306)),
        user=os.getenv('ZILCH_MYSQL_USER'),
        password=os.getenv('ZILCH_MYSQL_PASSWORD'),
        database=os.getenv('ZILCH_MYSQL_DATABASE')
    )
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"✅ Connected to MySQL: {result}")
```

### Database Migrations

The reference app includes migration tooling:

```bash
# View available migrations
ls db/migrations/

# Apply migrations
./db/migrate.sh up

# Check migration status
./db/migrate.sh status

# Create a new migration
cat > db/migrations/002-add-users-table.sql <<EOF
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

# Apply the new migration
./db/migrate.sh up
```

### Direct Database Access

For local development or debugging:

```bash
# Using Cloud SQL Proxy (local access)
cloud-sql-proxy compute/PROJECT_ID/REGION/zilch-mysql-vm &
mysql -h 127.0.0.1 -u zilch_user -p

# Using SSH (bastion access)
gcloud compute ssh zilch-mysql-vm --zone=us-central1-a
mysql -u zilch_user -p
```

## Next Steps

After reviewing the reference app:

1. **Customize** - Modify `app.py` to demo specific services
2. **Add Features** - Integrate with Firestore, Storage, Firebase, MySQL
3. **Use as Template** - Base your own app on this structure
4. **Phase 2 Demo** - Show how Cloud Build auto-deploys on git push

## Architecture Diagram

```
GitHub Repo (this code)
    ↓
    └─→ git push main
         ↓
    Cloud Build (watches GitHub)
         ↓
    Docker build & push to Artifact Registry
         ↓
    Cloud Run (auto-pulls latest image)
         ↓
    Environment variables injected (Phase 1-4):
    - ZILCH_PROJECT_ID
    - ZILCH_FIRESTORE_DATABASE
    - ZILCH_STORAGE_BUCKET
    - ZILCH_SECRET_PREFIX
    - ZILCH_FIREBASE_ENABLED
    - ZILCH_VERTEX_AI_ENABLED
    - ZILCH_PUBSUB_TOPIC
    - ZILCH_CLOUD_TASKS_QUEUE
    - ZILCH_BIGQUERY_DATASET
    - ZILCH_KMS_KEY_ID
    - ZILCH_VISION_AI_ENABLED
    - ZILCH_SPEECH_TO_TEXT_ENABLED
    - ZILCH_TRANSLATION_ENABLED
    - ZILCH_MYSQL_HOST
    - ZILCH_MYSQL_PORT
    - ZILCH_MYSQL_USER
    - ZILCH_MYSQL_PASSWORD
    - ZILCH_MYSQL_DATABASE
    - ZILCH_SCHEDULER_ENABLED (Phase 4)
    - ZILCH_MONITORING_ENABLED (Phase 4)
         ↓
    App reads env vars & displays status
```

## License

MIT - Use freely as a reference for your own Zilch applications.

---

**Made with ❤️ for the Zilch framework**

For more information, see the main [Zilch repository](https://github.com/anthropics/zilch-gcp).
