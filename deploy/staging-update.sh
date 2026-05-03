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

echo "==> Checking SECRET_KEY strength before restart..."
_sk=$(grep '^SECRET_KEY=' "$STAGING_DIR/.env" 2>/dev/null | cut -d'=' -f2-)
if [ ${#_sk} -lt 32 ]; then
    echo "ERROR: SECRET_KEY in $STAGING_DIR/.env is missing or too short (${#_sk} chars). Set a strong key (>= 32 chars) before deploying."
    exit 1
fi
unset _sk

echo "==> Restarting staging service..."
systemctl restart zenbid-staging

echo "==> Done! Staging status:"
systemctl status zenbid-staging --no-pager
