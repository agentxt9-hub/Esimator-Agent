# Staging Environment

Staging runs on the same DigitalOcean droplet as production. Separate app directory, separate database, separate systemd service, separate Nginx virtual host.

## Architecture

| | Production | Staging |
|---|---|---|
| App directory | `/var/www/zenbid` | `/var/www/zenbid-staging` |
| Database | `zenbid` (or `estimator_db`) | `zenbid_staging` |
| Gunicorn port | `8000` | `8001` |
| Systemd service | `zenbid` | `zenbid-staging` |
| Domain | `zenbid.io` | `staging.zenbid.io` |
| Gunicorn config | `gunicorn.conf.py` | `gunicorn.staging.conf.py` |

## First-time setup

Run once on the droplet after production is already running:

```bash
# On the droplet as root
bash /var/www/zenbid/deploy/staging-setup.sh
```

The script will:
1. Clone the repo to `/var/www/zenbid-staging`
2. Create a Python venv and install dependencies
3. Create the `zenbid_staging` PostgreSQL database
4. Create `/var/www/zenbid-staging/gunicorn.staging.conf.py`
5. Create the `zenbid-staging` systemd service
6. Add the Nginx virtual host for `staging.zenbid.io`

After the script completes:

1. Edit `/var/www/zenbid-staging/.env` with staging secrets (use `.env.staging.example` as the template — it's in the repo root)
2. Point `staging.zenbid.io` DNS A record to the droplet IP
3. Issue the staging TLS certificate: `certbot --nginx -d staging.zenbid.io`
4. Start the service: `systemctl start zenbid-staging`
5. Smoke-test: `curl -I https://staging.zenbid.io/login`

## Deploying code to staging

```bash
bash /var/www/zenbid/deploy/staging-update.sh
```

Or directly on the droplet:

```bash
cd /var/www/zenbid-staging
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart zenbid-staging
```

## Smoke-test checklist

After a staging deploy, verify:

- [ ] `https://staging.zenbid.io/login` returns 200
- [ ] Can create a new account (signup flow works)
- [ ] Can log in with a test account
- [ ] Can create a project and add line items
- [ ] AI routes respond (requires `ANTHROPIC_API_KEY` in staging `.env`)
- [ ] Takeoff canvas loads on a project with a PDF page

## Keeping staging and production in sync

- Both pull from `main`. Staging is always on the same code as production after a `staging-update.sh` run.
- Database schemas may diverge if staging runs migrations that production has not yet received. Run migrations explicitly: `python -c "from app import run_migrations; run_migrations()"` after each staging deploy.
- Secrets are different between staging and production. Never copy a production `.env` to staging — generate fresh keys.

## Logs

```bash
# Gunicorn application logs
journalctl -u zenbid-staging -f

# Nginx access log
tail -f /var/log/nginx/access.log | grep staging

# Gunicorn file logs (if configured)
tail -f /var/log/zenbid-staging-error.log
```

## Teardown (if staging is ever decommissioned)

```bash
systemctl stop zenbid-staging
systemctl disable zenbid-staging
rm /etc/systemd/system/zenbid-staging.service
rm /etc/nginx/sites-enabled/zenbid-staging
rm /etc/nginx/sites-available/zenbid-staging
systemctl daemon-reload
nginx -t && systemctl reload nginx
# Optionally drop the database:
# su -c "dropdb zenbid_staging" postgres
```
