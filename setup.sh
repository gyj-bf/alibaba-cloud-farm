#!/bin/bash
# Setup script for Alibaba Cloud Farm — Linux venv
set -e

echo "🌽 Setting up Alibaba Cloud Farm..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install dependencies
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Install Playwright Firefox
echo "Installing Playwright Firefox browser..."
PLAYWRIGHT_DOWNLOAD_TIMEOUT=120000 playwright install firefox

# Install system dependencies (requires sudo)
echo ""
echo "Installing system dependencies for Firefox (requires sudo)..."
sudo .venv/bin/playwright install-deps firefox

# Copy .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Created .env — edit it with your credentials!"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the farm:"
echo "  python farm.py"
echo ""
echo "To run the dashboard:"
echo "  python dashboard.py --port 8888"
