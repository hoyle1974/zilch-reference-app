#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ZILCH_GCP_DIR="/Users/jstrohm/code/zilch-gcp"

echo "🚀 Zilch Deploy Script"
echo "====================="
echo ""

# Check if Python 3.13 is available
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 not found. Install with:"
    echo "   brew install python@3.13"
    exit 1
fi

echo "✓ Python 3.13 found: $(python3.13 --version)"
echo ""

# Remove old venv if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🗑️  Removing old virtual environment..."
    rm -rf "$SCRIPT_DIR/venv"
fi

echo ""
echo "🔧 Creating Python 3.13 virtual environment..."
python3.13 -m venv "$SCRIPT_DIR/venv"

echo "✓ Virtual environment created"
echo ""

# Activate venv
source "$SCRIPT_DIR/venv/bin/activate"

echo "📦 Installing dependencies from $ZILCH_GCP_DIR/requirements.txt..."
pip install --quiet -r "$ZILCH_GCP_DIR/requirements.txt"

echo "✓ Dependencies installed"
echo ""

echo "🚀 Running deployment..."
echo "======================="
echo ""

python3 "$ZILCH_GCP_DIR/zilch.py" deploy --auto

echo ""
echo "✓ Deployment complete!"
