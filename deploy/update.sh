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

echo "==> Checking SECRET_KEY strength before restart..."
_sk=$(grep '^SECRET_KEY=' "$APP_DIR/.env" 2>/dev/null | cut -d'=' -f2-)
if [ ${#_sk} -lt 32 ]; then
    echo "ERROR: SECRET_KEY in $APP_DIR/.env is missing or too short (${#_sk} chars). Set a strong key (>= 32 chars) before deploying."
    exit 1
fi
unset _sk

echo "==> Restarting service..."
systemctl restart zenbid

echo "==> Done! Status:"
systemctl status zenbid --no-pager
