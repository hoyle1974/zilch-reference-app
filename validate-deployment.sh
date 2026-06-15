#!/bin/bash
# Validates Zilch deployment by checking all expected resources and outputs

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get configuration
APP_NAME=$(grep "app_name=" .zilch.config | cut -d'=' -f2)
GCP_PROJECT=$(grep "gcp_project_id=" .zilch.config | cut -d'=' -f2)
REGION=$(grep "gcp_region=" .zilch.config | cut -d'=' -f2)

echo "=================================================="
echo "🔍 Zilch Deployment Validation"
echo "=================================================="
echo "App Name: $APP_NAME"
echo "Project: $GCP_PROJECT"
echo "Region: $REGION"
echo ""

# Helper functions
check_pass() {
    echo -e "${GREEN}✅${NC} $1"
}

check_fail() {
    echo -e "${RED}❌${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Counter
passed=0
failed=0
warnings=0

# 1. Check Cloud Run service exists
echo "1. Checking Cloud Run service..."
if gcloud run services describe "$APP_NAME" --region="$REGION" --project="$GCP_PROJECT" &>/dev/null; then
    check_pass "Cloud Run service exists"
    ((passed++))

    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$APP_NAME" --region="$REGION" --project="$GCP_PROJECT" --format='value(status.url)')
    echo "   URL: $SERVICE_URL"
else
    check_fail "Cloud Run service not found"
    ((failed++))
    exit 1
fi

# 2. Check service account
echo ""
echo "2. Checking Service Account..."
if gcloud iam service-accounts describe "$APP_NAME@$GCP_PROJECT.iam.gserviceaccount.com" --project="$GCP_PROJECT" &>/dev/null; then
    check_pass "App service account exists"
    ((passed++))
else
    check_fail "Service account not found"
    ((failed++))
fi

# 3. Check Cloud Build service account (if Cloud Build enabled)
if grep -q "enable_cloud_build=true" .zilch.config; then
    echo ""
    echo "3. Checking Cloud Build service account..."
    if gcloud iam service-accounts describe "$APP_NAME-builder@$GCP_PROJECT.iam.gserviceaccount.com" --project="$GCP_PROJECT" &>/dev/null; then
        check_pass "Cloud Build service account exists"
        ((passed++))
    else
        check_warn "Cloud Build service account not found (may still be creating)"
        ((warnings++))
    fi
fi

# 4. Check IAM bindings
echo ""
echo "4. Checking IAM bindings..."
if gcloud projects get-iam-policy "$GCP_PROJECT" --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$APP_NAME@*" --format="value(bindings.role)" 2>/dev/null | grep -q "run.invoker"; then
    check_pass "Cloud Run invoker role bound"
    ((passed++))
else
    check_fail "Cloud Run invoker role not bound"
    ((failed++))
fi

# 5. Check Firestore
if grep -q "enable_firestore=true" .zilch.config; then
    echo ""
    echo "5. Checking Firestore..."
    if gcloud firestore databases list --project="$GCP_PROJECT" 2>/dev/null | grep -q "(default)"; then
        check_pass "Firestore database exists"
        ((passed++))
    else
        check_warn "Firestore database not found (may still be creating)"
        ((warnings++))
    fi

    # Check IAM binding
    if gcloud projects get-iam-policy "$GCP_PROJECT" --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$APP_NAME@* AND bindings.role:datastore.user" --format="value(bindings.role)" 2>/dev/null | grep -q "datastore.user"; then
        check_pass "Firestore IAM role bound"
        ((passed++))
    else
        check_warn "Firestore IAM role not yet bound"
        ((warnings++))
    fi
fi

# 6. Check Secret Manager
if grep -q "enable_secret_manager=true" .zilch.config; then
    echo ""
    echo "6. Checking Secret Manager..."
    SECRET_COUNT=$(gcloud secrets list --project="$GCP_PROJECT" --filter="name:$APP_NAME*" --format="value(name)" 2>/dev/null | wc -l)
    if [ "$SECRET_COUNT" -gt 0 ]; then
        check_pass "Secret Manager secrets exist ($SECRET_COUNT secrets)"
        ((passed++))
    else
        check_warn "No secrets found for this app (may need manual creation)"
        ((warnings++))
    fi
fi

# 7. Check Cloud Storage
if grep -q "enable_cloud_storage=true" .zilch.config; then
    echo ""
    echo "7. Checking Cloud Storage..."
    if gsutil ls -b -p "$GCP_PROJECT" 2>/dev/null | grep -q "$APP_NAME-storage"; then
        check_pass "Storage bucket exists"
        ((passed++))
    else
        check_warn "Storage bucket not found"
        ((warnings++))
    fi
fi

# 8. Test health endpoint
echo ""
echo "8. Testing health endpoint..."
HEALTH_URL="${SERVICE_URL}health"
if curl -s -f "$HEALTH_URL" &>/dev/null; then
    check_pass "Health endpoint responding"
    ((passed++))
else
    check_warn "Health endpoint not responding (service may still be starting)"
    ((warnings++))
fi

# 9. Test main dashboard
echo ""
echo "9. Testing main dashboard..."
if curl -s -f "$SERVICE_URL" &>/dev/null; then
    check_pass "Dashboard is accessible"
    ((passed++))
else
    check_warn "Dashboard not responding yet"
    ((warnings++))
fi

# Summary
echo ""
echo "=================================================="
echo "📊 Validation Summary"
echo "=================================================="
echo -e "Passed: ${GREEN}$passed${NC} | Failed: ${RED}$failed${NC} | Warnings: ${YELLOW}$warnings${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment validation PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Visit dashboard: $SERVICE_URL"
    echo "2. Check JSON API: ${SERVICE_URL}.json"
    echo "3. View logs: gcloud run logs read $APP_NAME --region=$REGION"
    exit 0
else
    echo -e "${RED}❌ Deployment validation FAILED${NC}"
    echo ""
    echo "Issues found:"
    echo "- Check that ./deploy.sh completed successfully"
    echo "- Resources may still be creating (give it 1-2 minutes)"
    echo "- Review Terraform output for errors"
    exit 1
fi
