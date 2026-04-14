# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

**Last updated:** 2026-04-13

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

## Security Framework

**MANDATORY:** Before building any new feature, consult `SECURITY.md` for security requirements.

### Pre-Build Security Checklist (Always Run)
- Multi-tenant isolation: Does this feature access tenant data? Use `get_project_or_403()` helpers
- Input validation: Does this feature accept user input? Server-side validation required
- CSRF protection: New HTML forms need `{{ csrf_token() }}` hidden field
- Rate limiting: AI routes need `@limiter.limit()` decorator
- Viewer role: Write routes need `@viewer_readonly` decorator (HIGH priority gap)
- AI prompt injection: User input in prompts needs sanitization (HIGH priority gap)

### Security Gap Backlog
See `SECURITY.md` Part 11 for prioritized remediation list:
- **CRITICAL:** SSL certificate, Privacy Policy, Terms of Service, API key validation
- **HIGH:** Proposal route isolation, viewer role enforcement, Nginx headers, prompt injection hardening

**Full framework:** `SECURITY.md` (authentication, authorization, input validation, rate limiting, data protection, infrastructure hardening, logging, legal compliance, agentic workflow security)

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

### Droplet 2 — Zenhub (45.55.33.136)
Zenhub — Internal growth and automation infrastructure. All services run via Docker Compose in `/opt/agentx-hub/`. **Separate repo:** `github.com/agentxt9-hub/zenhub` (pending creation)

| Service | URL |
|---------|-----|
| n8n (workflow automation) | flows.zenbid.io |
| Flowise (AI agent builder) | agents.zenbid.io |
| Dashy (dashboard) | hub.zenbid.io |
| Portainer (Docker management) | docker.zenbid.io |
| Uptime Kuma (monitoring) | status.zenbid.io |
| Nginx Proxy Manager | proxy.zenbid.io |

**Naming Note:** Server infrastructure uses `/opt/agentx-hub/` and `agentx-hub_` volume prefixes. In all product branding, documentation, and UI references, this is called "Zenhub."

**n8n Workflow — "Lead Magnet — Waitlist Welcome":**
- Fires on every waitlist signup via webhook: `https://flows.zenbid.io/webhook/waitlist`
- Calls Anthropic API (HTTP Request node) + sends via Gmail (`zenbid.notifications@gmail.com`)
- The `/waitlist` route in `app.py` POSTs to this webhook on every successful signup using the `requests` library (installed in venv)

---

## Architecture

Single-file Flask app (`app.py`, ~3500+ lines) + `routes_takeoff.py` (Takeoff Blueprint) + Jinja2 templates in `templates/` (lowercase — required for Linux case-sensitivity). Vanilla JS + `fetch()` for most surfaces. TanStack Table v8 (React via CDN + Babel Standalone) for the estimate grid.

**Test suites:** `test_takeoff.py` (99/99), `tests/test_estimate_table.py` (29/29).

**Two template bases:**
- `templates/base.html` — marketing site (light theme, public)
- `templates/app_base.html` — app interface (dark sidebar, login-required)

**Logo (Concept C — updated Session 15):**
- SVG mark: stacked estimate bars fading down, coral TOTAL row + coral circle
- Wordmark is `ZENBID` (all caps, one word) — `ZEN` in context color, `BID` in coral via `<span>`
- App dark (sidebar): mark with light bars + `ZEN` white + `BID` coral
- Marketing light (nav): mark with dark bars + `ZEN` dark + `BID` coral
- Footer (dark bg): mark with light bars + `ZEN` white + `BID` coral

**Key models** (all in `app.py` except Takeoff models in `routes_takeoff.py`):
- `Company` / `User` — multi-tenant auth (Flask-Login); User has `reset_token` + `reset_token_expires`
- `CSILevel1` / `CSILevel2` — read-only CSI hierarchy (seeded, never alter)
- `Project` → `Assembly` → `LineItem` — core estimating hierarchy
- `LineItem` — extended Session 22: `ai_generated`, `estimator_action`, `edit_delta`, `ai_status`, `ai_confidence`, `ai_note`, `is_deleted`, `company_id`, `phase`, `csi_division` (flywheel + TanStack fields)
- `AssemblyComposition` — FK→assembly + library_item; formula-driven quantities
- `LibraryItem` — company-scoped reusable item definitions
- `Assembly.is_template = True` — marks assemblies as global templates
- `WBSProperty` / `WBSValue` / `LineItemWBS` — project-scoped work breakdown structure
- `ProductionRateStandard` — global (no company_id) reference rates; seeded at startup
- `WaitlistEntry` — email + first name + created_at; unique email constraint
- `WaitlistSurvey` — FK→WaitlistEntry; comma-separated response keys
- `TakeoffPlan` / `TakeoffPage` / `TakeoffItem` / `TakeoffMeasurement` — in `routes_takeoff.py`; company_id isolated

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

**`CSI_COLORS` dict:** defined in `app.py` module level AND duplicated in `estimate_table.js` — keep both in sync. (`estimate.html` is now orphaned; `estimate_table.js` is the canonical JS.)

**No Jinja tags in `agentx_panel.html`** — pure HTML/JS partial. (Retirement planned in Pass 3.)

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
| ANTHROPIC_API_KEY startup validation missing | CRITICAL |
| SSL certificate status unconfirmed | CRITICAL |
| Proposal route not using `get_project_or_403()` | High |
| Welcome email on signup | High |
| Edit project fields UI (city/state/zip/type/sector) | High |
| Viewer role not enforced on write routes | Medium |
| Legacy estimate table in `project.html` (deprecated, retire in Pass 3) | Medium |
| `agentx_panel.html` still live (retire in Pass 3) | Low |

## Next Sessions — Four-Pass Sequence

Full scope: see `FEATURE_ROADMAP.md`.

- **Pass 2:** 90-Second Confidence Study — zzTakeoff walkthrough, upload→scale→measurement punch list
- **Pass 3:** Bridge + Table Migration — TanStack canonical, legacy retired, AgentX purged, measurement link, dual-costing expandable row, Tally stub hooks
- **Pass 4:** Tally Intelligence Wiring — Passive/Reactive/Generative backend

---

## Session History (condensed)

**Session 22 — 2026-04-07**
- TanStack Table v8 estimate grid: `estimate_table.html`, `estimate_table.js`, `estimate_table.css`
- LineItem model extended with flywheel fields + TanStack columns; 4 API routes; 29/29 tests
- `/project/<id>/estimate` route now serves `estimate_table.html` (canonical); `estimate.html` orphaned
- ADR-021 added; Tally footer banner rendered in grid

**Session 21 — 2026-04-07**
- Takeoff polish (Session 2 complete): ARCH_SCALES labels, ortho mode, close-polygon, Start button, Ortho/Snap toggles, page rename, area SF+FT panel; 99/99 tests

**Session 20 — 2026-04-07**
- Takeoff drawing tools: scale calibration, linear/area/count tools, renderMeasurements(), properties panel, project-level totals; 7 new API routes

**Session 19 — 2026-04-07**
- Konva.js migration: 3-layer stage (pdfLayer, measureLayer, uiLayer). Fixed black canvas, missing thumbnails, plans disappearing. Konva vendored locally.

**Session 18 — 2026-04-06**
- Takeoff module foundation: 4 DB tables, Blueprint (`routes_takeoff.py`), three-panel viewer, PDF upload (PyMuPDF page count only), client-side thumbnails, item CRUD; 31/31 tests

**Session 17 — 2026-03-21**
- NORTHSTAR.md updates, SECURITY.md framework added, Zenhub naming, n8n webhook for waitlist

**Session 16 — 2026-03-18**
- Fixed ZENBID wordmark gap (flex issue). Navbar/login CTAs → "Join Waitlist". Footer links de-linked. Mobile responsive pass on base.html + landing.html.

**Session 15 — 2026-03-18**
- ZENBID wordmark (all-caps) across 7 locations. Waitlist flow (WaitlistEntry + WaitlistSurvey). Dismissible waitlist banner. Pricing CTAs → Join Waitlist.

**Session 14 — 2026-03-18**
- `Templates/` → `templates/` case-sensitivity fix in git. `pool_pre_ping=True`. SendGrid confirmed working (MAIL_PORT=2525). Concept C logo deployed.
