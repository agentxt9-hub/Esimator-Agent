#!/bin/bash
# Deploy latest code to staging environment
# Run on the droplet to pull latest main and restart staging service

set -e

STAGING_DIR="/var/www/zenbid-staging"
VENV_DIR="$STAGING_DIR/venv"

echo "==> Pulling latest code to staging..."
cd "$STAGING_DIR"
git pull origin main
if ! git diff --quiet HEAD; then
    echo "ERROR: working tree is dirty after pull — aborting staging deploy"
    exit 1
fi

echo "==> Installing any new dependencies..."
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt

echo "==> Restarting staging service..."
systemctl restart zenbid-staging

echo "==> Done! Staging status:"
systemctl status zenbid-staging --no-pager
