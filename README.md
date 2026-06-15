# Zilch Reference Application

A minimal but complete Cloud Run application that demonstrates **all Zilch services** (Phase 1 + Phase 2) and their current status.

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
# Change: gcp_project_id to your actual GCP project
# Change: github_owner to your GitHub username

# Run Zilch deployment
bash ~/code/zilch-gcp/deploy.sh

# On prompts:
# - Use settings from .zilch.config
# - Enable all services you want to demonstrate
# - Cloud Build: yes (GitOps deployment)
```

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

### Health Check (`/health`)

Cloud Run and Kubernetes-compatible:

```bash
curl https://zilch-reference-app-<random>.run.app/health
# {"status":"healthy"}
```

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

### Phase 2 Features

| Feature | How It's Used |
|---------|---------------|
| **Cloud Build** | This app is deployed via Cloud Build on every `git push` |
| **Artifact Registry** | Container image stored in private registry |
| **GitOps Workflow** | Push code → auto-build → auto-deploy |
| **Environment Variables** | All Zilch config injected automatically |

## Local Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set some test environment variables
export ZILCH_PROJECT_ID="test-project"
export ZILCH_APP_NAME="zilch-reference-app"
export ZILCH_FIRESTORE_DATABASE="(default)"
export ZILCH_STORAGE_BUCKET="test-bucket"
export ZILCH_SECRET_PREFIX="test-"
export ZILCH_FIREBASE_ENABLED="true"

# Run Flask app
python app.py

# Visit http://localhost:8080
```

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
3. Cloud Build will redeploy with new env vars

### Health check fails after deployment

**Cause:** Container startup time or port misconfiguration

**Check:**
```bash
gcloud run logs read zilch-reference-app --region=us-central1 --limit=50
```

### "Hello World" image appears instead of reference app

**Cause:** Cloud Build didn't deploy yet, Cloud Run is still running initial image

**Fix:**
1. Check Cloud Build status: `gcloud builds log --stream LATEST`
2. Wait for build to complete (3-5 minutes)
3. Cloud Run will auto-pull new image

## Next Steps

After reviewing the reference app:

1. **Customize** - Modify `app.py` to demo specific services
2. **Add Features** - Integrate with Firestore, Storage, Firebase
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
    Environment variables injected:
    - ZILCH_PROJECT_ID
    - ZILCH_FIRESTORE_DATABASE
    - ZILCH_STORAGE_BUCKET
    - ZILCH_SECRET_PREFIX
    - ZILCH_FIREBASE_ENABLED
    - ZILCH_VERTEX_AI_ENABLED
         ↓
    App reads env vars & displays status
```

## License

MIT - Use freely as a reference for your own Zilch applications.

---

**Made with ❤️ for the Zilch framework**

For more information, see the main [Zilch repository](https://github.com/anthropics/zilch-gcp).
