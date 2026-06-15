#!/bin/bash
# Local development script for Zilch Reference App
# Sets up environment variables and runs the Flask app

echo "🚀 Zilch Reference App - Local Development"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --quiet -r requirements.txt

# Set Zilch environment variables (simulating what Cloud Run would do)
echo "🔧 Setting environment variables..."
export PORT=8080
export ZILCH_PROJECT_ID="local-test-project"
export ZILCH_APP_NAME="zilch-reference-app"
export ZILCH_FIRESTORE_DATABASE="(default)"
export ZILCH_SECRET_PREFIX="zilch-reference-app-"
export ZILCH_STORAGE_BUCKET="zilch-reference-app-storage-12345678"
export ZILCH_FIREBASE_ENABLED="true"
export ZILCH_VERTEX_AI_ENABLED="true"

echo ""
echo "✨ Starting Flask app on http://localhost:8080"
echo ""
echo "Available endpoints:"
echo "  📊 Dashboard: http://localhost:8080/"
echo "  📡 JSON API: http://localhost:8080/.json"
echo "  ❤️  Health: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the app
python -u app.py
