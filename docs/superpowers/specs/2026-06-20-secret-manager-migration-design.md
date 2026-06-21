# Google Secret Manager Integration Design

**Date:** 2026-06-20  
**Project:** Zilch Reference App  
**Scope:** Migrate sensitive credentials (MySQL password) from environment variables to Google Secret Manager

## Overview

Replace direct environment variable reads for sensitive values with Google Secret Manager API calls. Start with MySQL password (`ZILCH_MYSQL_PASSWORD`), extend to other credentials as needed.

## Problem Statement

Currently, the app reads MySQL password from the `ZILCH_MYSQL_PASSWORD` environment variable. Environment variables:
- Are visible in process listings (`ps aux`)
- Get logged in CI/CD pipelines and error messages
- Are exposed if the application crashes and dumps memory
- Cannot be rotated without restarting the service

Google Secret Manager provides:
- Encrypted at-rest storage
- Access audit logs
- Fine-grained IAM permissions
- Rotation support without restart

## Requirements

### Functional Requirements
1. Fetch MySQL password from Google Secret Manager at app startup
2. Cache the value in memory for the lifetime of the app
3. Support local development via environment variables or `.env.local` file
4. Gracefully handle Secret Manager unavailability (log error, allow app to start)

### Non-Functional Requirements
- No external dependencies beyond what's already imported (`google.cloud.secretmanager`)
- Minimal performance impact (one API call on startup)
- No change to app's public interface or endpoints
- Full cutover (no env var fallback in production)

## Design Approach: Direct API Call on Startup

### Architecture

```
App Startup
    ↓
Load environment variables
    ↓
Call get_secret("projects/{project_id}/secrets/ZILCH_MYSQL_PASSWORD/versions/latest")
    ↓
Cache value in module-level variable
    ↓
Use cached value in MySQL connection (line 128-135)
    ↓
Serve requests
```

### Implementation Details

**Secret Manager Client Setup:**
- Use `google.cloud.secretmanager.SecretManagerServiceClient` (already available via `google-cloud-*` imports)
- Call at module load time (top-level code in `app.py`)
- Secret name format: `projects/{PROJECT_ID}/secrets/ZILCH_MYSQL_PASSWORD/versions/latest`

**Caching Strategy:**
- Store secret value in a module-level variable (e.g., `_cached_mysql_password`)
- Set once at startup, never refresh
- If Secret Manager is unavailable, use empty string and log a warning (allows graceful degradation)

**Local Development:**
- Check if `ZILCH_MYSQL_PASSWORD` environment variable is set
- If set, use it directly (bypass Secret Manager)
- If not set, fall back to Secret Manager API
- Developers create `.env.local` file with `export ZILCH_MYSQL_PASSWORD="test_password"` or set directly in shell

**Fallback Logic:**
```
1. If ZILCH_MYSQL_PASSWORD env var is set → use it (local dev)
2. Else, try Secret Manager API
3. If Secret Manager fails → log warning, use empty string
4. If empty string at MySQL connect time → connection fails gracefully with error
```

### Code Changes

#### `app.py`

**New import (line ~12):**
```python
from google.cloud import secretmanager
```

**New function (before `check_service_status()`):**
```python
def get_secret(secret_name):
    """Fetch secret from Google Secret Manager."""
    # Check if env var is set first (local dev)
    env_key = secret_name.split('/')[-2]  # Extract "ZILCH_MYSQL_PASSWORD"
    if os.getenv(env_key):
        return os.getenv(env_key)
    
    # Try Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        app.logger.warning(f"Failed to fetch {secret_name}: {e}")
        return ""
```

**Module-level secret loading (after app initialization, line ~15):**
```python
_cached_mysql_password = None

def _load_secrets():
    """Load secrets on app startup."""
    global _cached_mysql_password
    project_id = os.getenv("ZILCH_PROJECT_ID", "")
    if project_id and os.getenv("ZILCH_MYSQL_HOST"):
        secret_name = f"projects/{project_id}/secrets/ZILCH_MYSQL_PASSWORD/versions/latest"
        _cached_mysql_password = get_secret(secret_name)

_load_secrets()
```

**Update MySQL connection logic (line ~125):**
```python
password = _cached_mysql_password or os.getenv("ZILCH_MYSQL_PASSWORD", "")
```

#### `README.md`

Add section under "Local Development" > "Run Locally":
```
### Using Secrets Locally

For MySQL password and other sensitive values:

Option 1: Set environment variable
export ZILCH_MYSQL_PASSWORD="your_test_password"
python app.py

Option 2: Create .env.local file (git-ignored)
cat > .env.local <<EOF
export ZILCH_MYSQL_PASSWORD="your_test_password"
EOF
source .env.local
python app.py
```

#### `.gitignore`

Ensure `.env.local` is ignored (add if missing):
```
.env.local
```

#### `requirements.txt`

Verify `google-cloud-secret-manager` is included (should be via existing `google-cloud-*` imports):
```
google-cloud-secretmanager>=2.0.0
```

### Error Handling

**Scenario: Secret Manager unavailable at startup**
- Log warning to stderr: "Failed to fetch ZILCH_MYSQL_PASSWORD: [error]"
- Set `_cached_mysql_password = ""`
- App continues to start
- When MySQL connection is attempted, it fails with clear error: "Access denied for user X"
- Developer sees the auth error and realizes they need to set env var or check Secret Manager

**Scenario: Secret doesn't exist in Secret Manager**
- Same as above — graceful fallback

**Scenario: Service account lacks Secret Manager permissions**
- Same as above — graceful fallback with error log

### Testing

**Local (without Secret Manager):**
1. Set `ZILCH_MYSQL_PASSWORD` env var
2. Run `python app.py`
3. Verify MySQL health check succeeds (if MySQL is running)

**Cloud Run (with Secret Manager):**
1. Deploy with Terraform (manages secret creation)
2. Cloud Run service account has `secretmanager.secretAccessor` role
3. Verify app startup logs show successful secret fetch
4. Verify MySQL health check endpoint works

**Graceful degradation:**
1. Unset `ZILCH_MYSQL_PASSWORD` env var
2. Delete secret from Secret Manager (or remove service account permissions)
3. Run app locally
4. Verify warning is logged and app starts
5. Verify MySQL health check returns "offline" with auth error

### Migration Path

**Phase 1 (this task):** MySQL password
**Phase 2 (future):** Other credentials as they are identified

## Files Modified

- `app.py` — Add `get_secret()`, `_load_secrets()`, update MySQL password handling
- `README.md` — Add local development instructions for secrets
- `.gitignore` — Ensure `.env.local` is ignored
- `requirements.txt` — Verify dependencies

## Success Criteria

- ✅ App reads MySQL password from Secret Manager in Cloud Run
- ✅ App falls back to env var for local development
- ✅ Health check endpoint reports MySQL status correctly
- ✅ App logs indicate successful secret fetch at startup
- ✅ README provides clear instructions for local development
- ✅ All existing endpoints work unchanged

## Out of Scope

- Rotating secrets dynamically (app restart required for now)
- Migrating non-sensitive config (feature flags, database names) to Secret Manager
- Automatic secret creation via Terraform (assume Terraform already manages this)
- Audit logging integration (GCP handles this automatically)

## Dependencies

- **google-cloud-secretmanager** — Already included in `google-cloud-*` requirements
- **ZILCH_PROJECT_ID** env var — Must be set for Secret Manager access
- **Service account permissions** — Cloud Run service account needs `roles/secretmanager.secretAccessor`
