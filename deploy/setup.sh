#!/bin/bash
# DigitalOcean Droplet — one-time setup script
# Run as root after cloning the repo

set -e

APP_DIR="/var/www/zenbid"
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/zenbid.service"

echo "==> Updating system packages..."
apt-get update -qq && apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx

echo "==> Creating virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

echo "==> Creating systemd service..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Zenbid Gunicorn App
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn app:app --config $APP_DIR/gunicorn.conf.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable zenbid
systemctl start zenbid

echo "==> Configuring Nginx..."
cat > /etc/nginx/sites-available/zenbid <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
    }
}
EOF

ln -sf /etc/nginx/sites-available/zenbid /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "==> Done! Zenbid is running at http://$(curl -s ifconfig.me)"
