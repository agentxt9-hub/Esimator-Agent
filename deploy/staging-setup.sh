#!/bin/bash
# Staging environment — one-time setup on the production droplet
# Run as root after the production setup (setup.sh) is already complete
# Creates a parallel staging environment at /var/www/zenbid-staging

set -e

STAGING_DIR="/var/www/zenbid-staging"
PROD_DIR="/var/www/zenbid"
VENV_DIR="$STAGING_DIR/venv"
SERVICE_FILE="/etc/systemd/system/zenbid-staging.service"
STAGING_PORT=8001
STAGING_DOMAIN="staging.zenbid.io"

echo "==> Cloning repo to staging directory..."
if [ -d "$STAGING_DIR" ]; then
    echo "    $STAGING_DIR already exists — skipping clone"
else
    git clone "$(cd $PROD_DIR && git remote get-url origin)" "$STAGING_DIR"
fi

echo "==> Creating staging virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$STAGING_DIR/requirements.txt"

echo "==> Creating staging PostgreSQL database..."
# Run as postgres user — creates zenbid_staging if it doesn't exist
su -c "psql -c \"SELECT 1 FROM pg_database WHERE datname='zenbid_staging'\" | grep -q 1 || createdb zenbid_staging" postgres

echo "==> Writing staging .env (edit this file with real values)..."
if [ ! -f "$STAGING_DIR/.env" ]; then
    cp "$STAGING_DIR/.env.staging.example" "$STAGING_DIR/.env"
    echo "    IMPORTANT: Edit $STAGING_DIR/.env before starting the service"
fi

echo "==> Creating staging gunicorn config..."
cat > "$STAGING_DIR/gunicorn.staging.conf.py" <<EOF
# Staging Gunicorn config — fewer workers, staging port
import multiprocessing
bind = "127.0.0.1:${STAGING_PORT}"
workers = 2
threads = 1
timeout = 120
accesslog = "/var/log/zenbid-staging-access.log"
errorlog  = "/var/log/zenbid-staging-error.log"
loglevel  = "info"
EOF

echo "==> Creating systemd service for staging..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Zenbid Staging Gunicorn App
After=network.target postgresql.service
StartLimitBurst=3
StartLimitInterval=60s

[Service]
User=www-data
Group=www-data
WorkingDirectory=$STAGING_DIR
EnvironmentFile=$STAGING_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn app:app --config $STAGING_DIR/gunicorn.staging.conf.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable zenbid-staging

echo "==> Adding Nginx virtual host for $STAGING_DOMAIN..."
cat > /etc/nginx/sites-available/zenbid-staging <<EOF
server {
    listen 80;
    server_name ${STAGING_DOMAIN};

    client_max_body_size 200M;

    location / {
        proxy_pass http://127.0.0.1:${STAGING_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias $STAGING_DIR/static/;
        expires 1d;
    }
}
EOF

ln -sf /etc/nginx/sites-available/zenbid-staging /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo "==> Staging setup complete."
echo ""
echo "Next steps:"
echo "  1. Edit $STAGING_DIR/.env with staging secrets (different SECRET_KEY, DATABASE_URL=...zenbid_staging)"
echo "  2. Point staging.zenbid.io DNS A record to this droplet's IP"
echo "  3. Run: certbot --nginx -d ${STAGING_DOMAIN}"
echo "  4. Run: systemctl start zenbid-staging"
echo "  5. Visit https://${STAGING_DOMAIN} to smoke-test"
echo "  6. Run: bash $STAGING_DIR/deploy/staging-update.sh  to deploy code updates"
