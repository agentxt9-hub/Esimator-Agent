# Monitoring & Observability

## What's wired

### Sentry (error tracking)

- **SDK:** `sentry-sdk[flask]` — FlaskIntegration captures unhandled exceptions automatically
- **Config:** `SENTRY_DSN` env var. If blank, Sentry is disabled (safe for local dev)
- **Environment tag:** reads `FLASK_ENV` — production errors show as `environment: production`, staging as `environment: production` (staging sets `FLASK_ENV=production`; differentiate by using a separate Sentry project for staging if desired)
- **PII:** `send_default_pii=False` — no user IP/email sent automatically
- **Trace sampling:** 10% (`traces_sample_rate=0.1`) — enough signal without billing overhead

### Structured logging

- **Production:** rotates daily to `/var/log/zenbid/app.log`, 14-day retention
- **Dev/staging:** stdout
- **Log level:** `LOG_LEVEL` env var, default `INFO`
- **Format:** `%(asctime)s %(levelname)s %(name)s %(message)s`

### What gets logged

| Event | Level | Key fields |
|---|---|---|
| Successful login | INFO | `auth.login user_id= email= ip=` |
| Failed login | WARNING | `auth.login_failed email= ip=` |
| Signup | INFO | `auth.signup user_id= email= company= ip=` |
| Logout | INFO | `auth.logout user_id= ip=` |
| Admin panel access | INFO | `admin.panel_access user_id= ip=` |
| AI call (all routes) | — | written to `ai_call_log` table (see D.1) |
| 500/502/503 responses | ERROR | `http.5XX path= method= ip=` |
| Unhandled exceptions | ERROR | via Sentry + `app.logger.exception()` in each AI route |

### Uptime Kuma (uptime alerting)

Uptime Kuma must be installed and configured manually on the production server (or a separate monitoring host).

**Setup steps:**
1. Install: `docker run -d --restart=always -p 3001:3001 -v uptime-kuma:/app/data --name uptime-kuma louislam/uptime-kuma:1`
2. Access at `http://<droplet-ip>:3001` and create an account
3. Add monitor for `https://zenbid.io/_health` — HTTP(s), 60s interval, 2 retries before alert
4. Add monitor for `https://staging.zenbid.io/_health` — same settings
5. Set alert destination: notification → Email → `thomas@zenbid.io`
6. Optional: add Slack or Discord webhook notification channel

The `/_health` endpoint returns `{"status": "ok"}` with HTTP 200. It hits the DB-free fast path — if Gunicorn is down, Nginx returns 502 and Kuma fires.

## New environment variables

| Variable | Required | Notes |
|---|---|---|
| `SENTRY_DSN` | Recommended in prod | Get from sentry.io → Project Settings → Client Keys |
| `LOG_LEVEL` | No (default: INFO) | DEBUG / INFO / WARNING / ERROR |

## How to verify wiring

### Sentry test (non-production only)

```bash
curl https://staging.zenbid.io/_sentry-test
```

This route deliberately raises `RuntimeError('Sentry test exception — wiring verified')`. It is blocked in production (returns 404). After hitting it on staging, check the Sentry dashboard — the exception should appear within ~30 seconds under the Issues tab.

The route is at [app.py](../app.py) — guarded by `if os.environ.get('FLASK_ENV') == 'production': return 404`.

### Uptime Kuma test

Stop the staging Gunicorn process:
```bash
sudo systemctl stop zenbid-staging
```
Wait ~2 minutes (2 consecutive 60s checks). Uptime Kuma should fire an alert email to `thomas@zenbid.io`. Restore with `sudo systemctl start zenbid-staging`.

### Log verification

```bash
# Production
sudo tail -f /var/log/zenbid/app.log

# Staging (stdout → journald)
sudo journalctl -u zenbid-staging -f
```

Log in to the app and confirm you see `auth.login user_id=...` entries.
