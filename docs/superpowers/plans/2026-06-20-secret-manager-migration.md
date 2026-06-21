# Google Secret Manager Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate MySQL password from environment variables to Google Secret Manager, with fallback to env vars for local development.

**Architecture:** Add a `get_secret()` function that checks env vars first (for local dev), then calls Secret Manager API. Load secrets once at app startup into a module-level cache. Update MySQL connection logic to use the cached value instead of reading env vars directly.

**Tech Stack:** google-cloud-secretmanager (already available), Flask, Python 3.11+

## Global Constraints

- Use `ZILCH_` prefix for all secret names in Secret Manager
- Full cutover — no env var fallback in production, but support env vars for local dev via fallback logic
- Secret name format: `projects/{PROJECT_ID}/secrets/ZILCH_MYSQL_PASSWORD/versions/latest`
- Graceful degradation: log warning if secret fetch fails, allow app to start
- All changes must work with existing health-check endpoints unchanged

---

### Task 1: Add Secret Manager Integration to app.py

**Files:**
- Modify: `app.py:1-20` (imports and initialization)

**Interfaces:**
- Produces: `get_secret(secret_name: str) -> str` — fetches secret from Secret Manager or env vars
- Produces: `_cached_mysql_password: str` — module-level variable holding cached password
- Produces: `_load_secrets() -> None` — loads secrets on app startup

**Steps:**

- [ ] **Step 1: Add import for Secret Manager**

At the top of `app.py`, add the import after the existing Google Cloud imports:

```python
from google.cloud import secretmanager
```

This goes after line 12 (after the firestore, storage, bigquery imports).

- [ ] **Step 2: Add get_secret() function**

Add this function right after the imports and before `app = Flask(__name__)` (around line 14-15):

```python
def get_secret(secret_name):
    """
    Fetch secret from Google Secret Manager.
    Falls back to environment variable if set (for local development).
    """
    # Extract the secret key name (e.g., "ZILCH_MYSQL_PASSWORD" from the full path)
    env_key = secret_name.split('/')[-2]
    
    # Check env var first (local development)
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

- [ ] **Step 3: Add module-level secret cache and loader**

Add these after the `app = Flask(__name__)` line (around line 16-17):

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

- [ ] **Step 4: Verify imports and structure**

Run: `python -c "import app" 2>&1 | head -20`

Expected: No import errors. App should initialize without errors even if Secret Manager isn't available.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: add Secret Manager integration for MySQL password"
```

---

### Task 2: Update MySQL Connection to Use Cached Password

**Files:**
- Modify: `app.py:121-145` (check_mysql_health function)
- Modify: `app.py:470-480` (MySQL connection in README example — will be updated in Task 4)

**Interfaces:**
- Consumes: `_cached_mysql_password` from Task 1
- Produces: No new interfaces; updates existing behavior

**Steps:**

- [ ] **Step 1: Update check_mysql_health() to use cached password**

Find the `check_mysql_health()` function (starts around line 113). Change line 121-125 from:

```python
    host = os.getenv("ZILCH_MYSQL_HOST")
    port = os.getenv("ZILCH_MYSQL_PORT", "3306")
    user = os.getenv("ZILCH_MYSQL_USER")
    password_env = os.getenv("ZILCH_MYSQL_PASSWORD", "")
    database = os.getenv("ZILCH_MYSQL_DATABASE")
```

To:

```python
    host = os.getenv("ZILCH_MYSQL_HOST")
    port = os.getenv("ZILCH_MYSQL_PORT", "3306")
    user = os.getenv("ZILCH_MYSQL_USER")
    password_env = _cached_mysql_password or os.getenv("ZILCH_MYSQL_PASSWORD", "")
    database = os.getenv("ZILCH_MYSQL_DATABASE")
```

The key change: use `_cached_mysql_password` as primary source, fall back to env var if needed.

- [ ] **Step 2: Test the function exists and is called**

Run: `python -c "from app import check_mysql_health; print(check_mysql_health())"`

Expected: Returns a dict with `"status"` key (either "disabled", "online", or "offline" depending on your setup).

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: update MySQL connection to use Secret Manager cached password"
```

---

### Task 3: Update .gitignore to Exclude .env.local

**Files:**
- Modify: `.gitignore`

**Steps:**

- [ ] **Step 1: Check current .gitignore**

Run: `cat .gitignore`

Expected: Shows existing ignore patterns (venv, __pycache__, etc.)

- [ ] **Step 2: Add .env.local if not present**

Run: `grep -q "\.env\.local" .gitignore || echo ".env.local" >> .gitignore`

This adds `.env.local` to the end of `.gitignore` if it's not already there.

- [ ] **Step 3: Verify the change**

Run: `tail -5 .gitignore`

Expected: Last few lines should include `.env.local`

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "docs: add .env.local to gitignore for local secret files"
```

---

### Task 4: Add Local Development Instructions to README

**Files:**
- Modify: `README.md:211-248` (Local Development section)

**Steps:**

- [ ] **Step 1: Locate the Local Development section**

Run: `grep -n "### Run Locally" README.md`

Expected: Shows line number around 214

- [ ] **Step 2: Add secrets documentation after the existing "Run Locally" section**

After the "Run Flask app" command block (around line 248), add this new subsection:

```markdown
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
```

- [ ] **Step 3: Verify the markdown**

Run: `grep -A 15 "### Using Secrets Locally" README.md`

Expected: Shows the new section with proper formatting

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Secret Manager setup instructions for local development"
```

---

### Task 5: Verify requirements.txt includes google-cloud-secretmanager

**Files:**
- Check: `requirements.txt`
- Modify if needed: `requirements.txt`

**Steps:**

- [ ] **Step 1: Check if google-cloud-secretmanager is listed**

Run: `grep -i "google-cloud-secretmanager\|google-cloud" requirements.txt`

Expected: Should show at least `google-cloud-secretmanager` or a catch-all like `google-cloud-*`

- [ ] **Step 2: If missing, add the dependency**

If not present, run:

```bash
echo "google-cloud-secretmanager>=2.0.0" >> requirements.txt
```

- [ ] **Step 3: Verify**

Run: `grep "secretmanager" requirements.txt`

Expected: Shows `google-cloud-secretmanager>=2.0.0`

- [ ] **Step 4: Commit (if changed)**

```bash
git add requirements.txt
git commit -m "deps: ensure google-cloud-secretmanager is in requirements"
```

---

### Task 6: Test Local Development Flow

**Files:**
- Test: Local app execution

**Steps:**

- [ ] **Step 1: Create .env.local with test password**

```bash
cat > /Users/jstrohm/code/zilch-reference-app/.env.local <<EOF
export ZILCH_MYSQL_PASSWORD="test_password_123"
export ZILCH_PROJECT_ID="test-project"
export ZILCH_APP_NAME="zilch-reference-app"
EOF
```

- [ ] **Step 2: Source the env file and run the app**

```bash
cd /Users/jstrohm/code/zilch-reference-app
source .env.local
python app.py &
APP_PID=$!
sleep 3
```

Expected: App starts without errors. Look for "Running on" in output.

- [ ] **Step 3: Test the health endpoint**

```bash
curl http://localhost:8080/health
```

Expected: `{"status":"healthy"}`

- [ ] **Step 4: Check that app loaded the secret (view logs)**

```bash
# The app should show no warnings about missing secrets if env var was set
# Kill the app
kill $APP_PID
```

- [ ] **Step 5: Test without .env.local (graceful degradation)**

```bash
unset ZILCH_MYSQL_PASSWORD
unset ZILCH_PROJECT_ID
unset ZILCH_APP_NAME

# Run app again
python app.py &
APP_PID=$!
sleep 3

# Should start but log a warning
curl http://localhost:8080/health

kill $APP_PID
```

Expected: Health check still returns `{"status":"healthy"}`, but app logs show warning about missing ZILCH_PROJECT_ID or failed secret fetch.

- [ ] **Step 6: Verify .env.local is ignored by git**

```bash
git status
```

Expected: `.env.local` is NOT listed in "Changes not staged" or "Untracked files"

- [ ] **Step 7: Commit test results**

No new files to commit from this task (`.env.local` is git-ignored). Move to next task.

---

### Task 7: Integration Test with Health Check Endpoint

**Files:**
- Test: Existing health-check endpoint

**Steps:**

- [ ] **Step 1: Start app with env var set**

```bash
export ZILCH_MYSQL_PASSWORD="test_password"
export ZILCH_PROJECT_ID="test-project"
export ZILCH_APP_NAME="zilch-reference-app"
export ZILCH_MYSQL_HOST="127.0.0.1"  # or skip if MySQL not running locally
export ZILCH_MYSQL_PORT="3306"
export ZILCH_MYSQL_USER="test_user"
export ZILCH_MYSQL_DATABASE="test_db"

python app.py &
APP_PID=$!
sleep 2
```

- [ ] **Step 2: Call the /.json endpoint**

```bash
curl http://localhost:8080/.json | python -m json.tool | head -30
```

Expected: Returns valid JSON with environment info. Should NOT show `ZILCH_MYSQL_PASSWORD` in the output (it's hidden from the dashboard for security).

- [ ] **Step 3: Call the /health-check endpoint**

```bash
curl http://localhost:8080/health-check | python -m json.tool
```

Expected: Returns JSON with service status. If MySQL is running: `{"MySQL Database": {"status": "online", ...}}`. If not: `{"MySQL Database": {"status": "offline", ...}}`.

- [ ] **Step 4: Verify password is NOT logged**

```bash
# The password should never appear in logs or HTTP responses
# Check that ZILCH_MYSQL_PASSWORD doesn't leak anywhere
curl http://localhost:8080/.json | grep -i "mysql_password" || echo "Password not exposed (good!)"
```

Expected: No password in the JSON response.

- [ ] **Step 5: Stop the app**

```bash
kill $APP_PID
wait $APP_PID 2>/dev/null || true
```

- [ ] **Step 6: Commit (no code changes in this task)**

Task is verification only. No commit needed.

---

## Plan Self-Review

**Spec coverage check:**
- ✅ Secret Manager integration: Task 1 (get_secret function, module-level cache)
- ✅ MySQL password update: Task 2 (uses cached value)
- ✅ Local development support: Tasks 3-4 (.env.local, README instructions)
- ✅ Error handling: Task 1 (graceful fallback with logging)
- ✅ Testing: Tasks 6-7 (local flow, health checks)
- ✅ Dependencies: Task 5 (verify requirements.txt)

**Placeholder scan:**
- ✅ No TBDs or "implement later" instructions
- ✅ All code blocks are complete and ready to use
- ✅ All commands have expected output described
- ✅ No "similar to Task X" references

**Type consistency:**
- ✅ `get_secret(secret_name: str) -> str` defined in Task 1, used in Task 1
- ✅ `_cached_mysql_password` type is `str | None`, handled correctly in Task 2
- ✅ All function signatures consistent across tasks
