# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

**Last updated:** 2026-03-17 — Session 13 (production deployment + SendGrid email)

> Full reference: see `Agent_MD.md` for complete architecture, routes, session history, and roadmap.

---

## Running the App (Local Dev)

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

Requires PostgreSQL at `localhost:5432/estimator_db` (user: `postgres`, password: `Builder`).

**Do not run `seed_csi.py`** — CSI data is already seeded.

Local `.env` (gitignored):
```
SECRET_KEY=anything-for-dev
DATABASE_URL=postgresql://postgres:Builder@localhost:5432/estimator_db
ANTHROPIC_API_KEY=sk-ant-...
FLASK_DEBUG=true
MAIL_PASSWORD=                  # leave blank locally unless testing email
MAIL_DEFAULT_SENDER=noreply@zenbid.io
```

---

## Production Deployment (DigitalOcean)

Live at: **zenbid.io** — ✅ back online (2026-03-17)

- Gunicorn via `Procfile` + `gunicorn.conf.py`; systemd service `zenbid`
- Nginx reverse-proxies port 80 → Gunicorn port 8000
- Migrations + seeding run automatically in `gunicorn.conf.py → on_starting()`
- `FLASK_DEBUG` must be `false` in production `.env`

```bash
# Deploy an update (on the droplet):
bash /var/www/zenbid/deploy/update.sh
```

### Server `.env` required vars
```
SECRET_KEY=<strong-random>
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
FLASK_DEBUG=false
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=2525
MAIL_USERNAME=apikey
MAIL_PASSWORD=<sendgrid-api-key>
MAIL_DEFAULT_SENDER=thomas@zenbid.io
```

**SendGrid notes:**
- `MAIL_USERNAME` must be the literal string `apikey` — not the API key itself
- `MAIL_PORT=2525` — port 587 is blocked by DigitalOcean; 2525 works
- Verified sender: `thomas@zenbid.io` (Single Sender Verification in SendGrid)

---

## Architecture

Single-file Flask app (`app.py`, ~3450 lines) + Jinja2 templates in `Templates/`. Vanilla JS + `fetch()`. No frontend framework. No test suite.

**Two template bases:**
- `Templates/base.html` — marketing site (light theme, public)
- `Templates/app_base.html` — app interface (dark sidebar, login-required)

**Key models** (all in `app.py`):
- `Company` / `User` — multi-tenant auth (Flask-Login); User has `reset_token` + `reset_token_expires`
- `CSILevel1` / `CSILevel2` — read-only CSI hierarchy (seeded, never alter)
- `Project` → `Assembly` → `LineItem` — core estimating hierarchy
- `AssemblyComposition` — FK→assembly + library_item; formula-driven quantities
- `LibraryItem` — company-scoped reusable item definitions
- `Assembly.is_template = True` — marks assemblies as global templates
- `WBSProperty` / `WBSValue` / `LineItemWBS` — project-scoped work breakdown structure
- `ProductionRateStandard` — global (no company_id) reference rates; seeded at startup

**Schema migrations:** Always extend `run_migrations()` with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Never drop/recreate tables.

---

## Authentication & Multi-Tenancy

- Flask-Login; `@login_required` on all app routes
- Public exceptions: `/`, `/login`, `/logout`, `/signup`, `/forgot-password`, `/reset-password/<token>`, marketing pages, `/uploads/logo/<f>`
- Login accepts **email** (username fallback for legacy accounts)
- Isolation helpers: `get_project_or_403()`, `get_assembly_or_403()`, `get_lineitem_or_403()`, `get_library_item_or_403()`
- Roles: `admin` | `estimator` | `viewer` — only `/admin` routes enforce role check

---

## Critical Patterns

**`/project/<id>/summary` must return JSON** — `project.html` fetches it on load. Do not change its response type.

**CSRF:**
- `CSRFProtect(app)` is active — all POST requests require a CSRF token
- HTML forms: add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- `fetch()` POST calls: covered automatically by monkey-patch in `app_base.html <head>` — do not remove it
- Both base templates have `<meta name="csrf-token" content="{{ csrf_token() }}">`

**JSON data embedding:**
```html
<script id="my-data" type="application/json">{{ data | tojson | safe }}</script>
```
Parsed in JS: `JSON.parse(document.getElementById('my-data').textContent)` — XSS-safe.

**CSI dropdowns:** Level 1 from Jinja; Level 2 from embedded JSON blob filtered in JS.

**Cascade delete:** Python only — no `ON DELETE CASCADE` in DB.

**`CSI_COLORS` dict:** defined in `app.py` module level AND duplicated in `estimate.html` JS — keep both in sync.

**No Jinja tags in `agentx_panel.html`** — pure HTML/JS partial.

**Datetime:** `datetime.now(timezone.utc)` — never `datetime.utcnow()`.

---

## UI Rules

### App (dark theme) — CSS vars in `app_base.html`
- `--app-bg: #0F1419` | `--app-card: #1A1F26` | `--app-sidebar: #16181D` | `--app-input: #252B33`
- `--primary-brand: #2D5BFF` | `--accent-coral: #FF6B35`
- `--error-bg: #3a0a12` | `--error: #EF4444`
- **Do NOT hardcode** `#1a1a2e`, `#16213e`, `#0f3460`, `#e94560` — use CSS variables

### Marketing (light theme) — CSS vars in `base.html`
- `--primary-brand: #2D5BFF` | `--accent-coral: #FF6B35` | `--marketing-bg: #FFFFFF`

---

## Known Gaps (Active — pre-beta)

| Gap | Priority |
|-----|----------|
| Privacy Policy & Terms — placeholder routes | CRITICAL |
| ANTHROPIC_API_KEY needs server verification | CRITICAL |
| Proposal route not using `get_project_or_403()` | High |
| Viewer role not enforced on write routes | Medium |
| Edit project fields UI (city/state/zip/type/sector) | High |
| Welcome email on signup | High |
| 7 marketing placeholder routes return plain text | Medium |
| WBS/rate features not live-tested post-deploy | Medium |
| AgentX AI panel not live-tested post-deploy | Medium |
