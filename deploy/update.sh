#!/bin/bash
# Run on the droplet to pull latest code and restart
set -e

APP_DIR="/var/www/zenbid"
VENV_DIR="$APP_DIR/venv"

echo "==> Pulling latest code..."
cd "$APP_DIR"
git pull origin main
if ! git diff --quiet HEAD; then
    echo "ERROR: working tree is dirty after pull — aborting deploy"
    exit 1
fi

echo "==> Installing any new dependencies..."
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt

echo "==> Restarting service..."
systemctl restart zenbid

echo "==> Done! Status:"
systemctl status zenbid --no-pager
