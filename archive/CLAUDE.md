# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

**Last updated:** 2026-03-18 — Session 16 (mobile responsive, ZENBID spacing fix, waitlist push, CTA cleanup)

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

## Production Infrastructure (DigitalOcean)

### Droplet 1 — Zenbid App Server
Live at: **zenbid.io** — ✅ fully operational (2026-03-18)

- Gunicorn via `Procfile` + `gunicorn.conf.py`; systemd service `zenbid`
- Nginx reverse-proxies port 80 → Gunicorn port 8000
- Migrations + seeding run automatically in `gunicorn.conf.py → on_starting()`
- `FLASK_DEBUG` must be `false` in production `.env`

```bash
# Deploy an update (on the droplet):
bash /var/www/zenbid/deploy/update.sh
```

#### Server `.env` required vars
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

### Droplet 2 — Growth Hub (45.55.33.136)
Agentic Growth Marketer infrastructure. All services run via Docker Compose in `/opt/agentx-hub/`.

| Service | URL |
|---------|-----|
| n8n (workflow automation) | flows.zenbid.io |
| Flowise (AI agent builder) | agents.zenbid.io |
| Dashy (dashboard) | hub.zenbid.io |
| Portainer (Docker management) | docker.zenbid.io |
| Uptime Kuma (monitoring) | status.zenbid.io |
| Nginx Proxy Manager | proxy.zenbid.io |

**n8n Workflow — "Lead Magnet — Waitlist Welcome":**
- Fires on every waitlist signup via webhook: `https://flows.zenbid.io/webhook/waitlist`
- Calls Anthropic API (HTTP Request node) + sends via Gmail (`zenbid.notifications@gmail.com`)
- The `/waitlist` route in `app.py` POSTs to this webhook on every successful signup using the `requests` library (installed in venv)

---

## Architecture

Single-file Flask app (`app.py`, ~3450 lines) + Jinja2 templates in `templates/` (lowercase — required for Linux case-sensitivity). Vanilla JS + `fetch()`. No frontend framework. No test suite.

**Two template bases:**
- `templates/base.html` — marketing site (light theme, public)
- `templates/app_base.html` — app interface (dark sidebar, login-required)

**Logo (Concept C — updated Session 15):**
- SVG mark: stacked estimate bars fading down, coral TOTAL row + coral circle
- Wordmark is `ZENBID` (all caps, one word) — `ZEN` in context color, `BID` in coral via `<span>`
- App dark (sidebar): mark with light bars + `ZEN` white + `BID` coral
- Marketing light (nav): mark with dark bars + `ZEN` dark + `BID` coral
- Footer (dark bg): mark with light bars + `ZEN` white + `BID` coral

**Key models** (all in `app.py`):
- `Company` / `User` — multi-tenant auth (Flask-Login); User has `reset_token` + `reset_token_expires`
- `CSILevel1` / `CSILevel2` — read-only CSI hierarchy (seeded, never alter)
- `Project` → `Assembly` → `LineItem` — core estimating hierarchy
- `AssemblyComposition` — FK→assembly + library_item; formula-driven quantities
- `LibraryItem` — company-scoped reusable item definitions
- `Assembly.is_template = True` — marks assemblies as global templates
- `WBSProperty` / `WBSValue` / `LineItemWBS` — project-scoped work breakdown structure
- `ProductionRateStandard` — global (no company_id) reference rates; seeded at startup
- `WaitlistEntry` — email + first name + created_at; unique email constraint
- `WaitlistSurvey` — FK→WaitlistEntry; comma-separated response keys (speed/ai/pricing/structure/team)

**Schema migrations:** Always extend `run_migrations()` with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Never drop/recreate tables.

---

## Authentication & Multi-Tenancy

- Flask-Login; `@login_required` on all app routes
- Public exceptions: `/`, `/login`, `/logout`, `/signup`, `/forgot-password`, `/reset-password/<token>`, `/waitlist`, `/waitlist/survey`, marketing pages, `/uploads/logo/<f>`
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
| Privacy Policy & Terms — placeholder routes needed | CRITICAL |
| ANTHROPIC_API_KEY needs server verification | CRITICAL |
| Smoke test waitlist flow + micro-survey on production (check DB entries) | High |
| Welcome email on signup | High |
| Proposal route not using `get_project_or_403()` | High |
| Edit project fields UI (city/state/zip/type/sector) | High |
| Viewer role not enforced on write routes | Medium |
| WBS/rate features not live-tested post-deploy | Medium |
| AgentX AI panel not live-tested post-deploy | Medium |

## Next Session Queue (Session 17)

1. **Smoke test waitlist** — check DB entries on server, confirm micro-survey saving
2. **Welcome email** — add `mail.send()` in `/signup` route (flask-mail already wired)
3. **Privacy Policy & Terms pages** — build minimal real pages (not plain text 404s)
4. **Proposal route fix** — swap `Project.query.get()` → `get_project_or_403()`
5. **Edit project fields UI** — add city/state/zip/type/sector to Edit Project modal

---

## Session History (condensed)

**Session 16 — 2026-03-18**
- Fixed `ZENBID` wordmark gap: wrapped `ZEN<span>BID</span>` in outer `<span>` so flex `gap: 10px` only separates SVG mark from text, not ZEN from BID — fixed in 7 templates + CSS updated to `.bid-accent` class
- Navbar "Join Waitlist" button white font fix: added `.navbar-links a.btn-primary { color: white }` to override `.navbar-links a` color
- All "Start Free Trial" CTAs → "Join Waitlist" → `/waitlist` (navbar, landing hero, landing CTA section)
- Login page "Sign up" link → "Join the waitlist" → `/waitlist`
- Footer: removed `<a>` tags from 7 placeholder links (About/Blog/Careers/Contact/Privacy/Terms/Security) — text only until pages are built
- Pushed previously uncommitted waitlist work: `app.py` routes + models, `waitlist.html`, `pricing.html` CTA updates
- Mobile responsive pass on `base.html`: hamburger menu, footer 2-col on mobile, banner text wrap fix
- Mobile responsive pass on `landing.html`: hero stacks, hide app mockup, features/testimonials/pricing 1-col, CTA buttons stack

**Session 15 — 2026-03-18**
- Logo wordmark updated to all-caps `ZENBID` (one word) across all 7 locations: sidebar, marketing nav, footer, login, signup, forgot password, reset password, landing hero mockup
- Added dismissible waitlist banner to `base.html` (dark navy + coral, above navbar, localStorage dismiss)
- Pricing page: all 3 tier CTA buttons → "Join Waitlist" → `/waitlist`
- Built full waitlist flow: `GET/POST /waitlist`, `WaitlistEntry` model, `waitlist.html` (first name required + email)
- Post-submit micro-survey: 5 checkbox options, stores to `WaitlistSurvey` via `POST /waitlist/survey` (fetch, non-blocking)
- Both new DB tables auto-created via `run_migrations()` on deploy
- Promotion readiness audit: identified 4 high-priority items for Session 16 (see Known Gaps)

**Session 14 — 2026-03-18**
- Fixed `Templates/` → `templates/` case-sensitivity in git (Linux was seeing two separate dirs)
- Fixed stale DB connections: added `pool_pre_ping=True` to SQLAlchemy config
- Set up SendGrid: verified sender `thomas@zenbid.io`, `MAIL_USERNAME=apikey`, `MAIL_PORT=2525` (587 blocked by DO)
- Forgot password + reset email flow confirmed working end-to-end
- Concept C logo (SVG mark + ZENBID wordmark) deployed to production
