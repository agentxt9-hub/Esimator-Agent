# Zenbid — Master Reference Document
**Last updated:** 2026-03-17 | **Current session:** 13
**Live at:** zenbid.io ✅ (back online as of 2026-03-17)

---

## Product Vision

### Problem
Construction estimating is split between rigid Excel/legacy-software estimators and a new generation of AI-native workflows. Neither current tool serves both. AgentX bridges the gap.

### Core Philosophy
1. **Flexibility Over Dogma** — the tool adapts to the user's mental model, not the reverse
2. **AI as Optional Augmentation** — Claude is always available, never required; a user can build a complete estimate without touching AI once
3. **Predictable Output, Unpredictable Process** — professional reports regardless of how the estimate was assembled
4. **Institutional Knowledge at Your Fingertips** — scope gap detection, rate validation, and AI suggestions level the playing field for junior estimators
5. **Generational Inclusivity** — works for the 60-year-old Excel estimator and the 28-year-old AI-native equally

### The Test (from NORTHSTAR.md)
> *Could a rigid (Excel-minded) estimator use this comfortably? Could a flexible (AI-native) estimator use this expressively?* If either answer is "no," reconsider the design.

---

## Current State (Session 12 — 2026-03-15)

### What's working (code-complete, locally tested)
- Full multi-tenant auth: Company → User (admin/estimator/viewer), Flask-Login, email+username login
- Complete estimating workflow: project → assembly → line item → cost calc → reports
- Assembly Builder wizard with measurement-driven quantity formulas
- AI integration (Claude Sonnet): chat (3 modes), assembly auto-builder, scope gap analysis, rate lookup, rate validation
- WBS panel with inline editing and drag-to-reorder (not live-tested post-deploy)
- Marketing site live: landing, pricing, signup, login — at zenbid.io (when up)
- Password reset via email (`/forgot-password`, `/reset-password/<token>`) — Session 12
- CSRF protection on all forms and fetch() calls — Session 12
- Rate limiting on all AI routes and login — Session 12

### Not yet live-tested
- WBS inline editing and drag-to-reorder (code complete Session 11)
- Validate rate right-click badge (code complete Session 11)
- Rate lookup panel with production_rate_standards data (sparse — only 20 seeded rows)
- Password reset email (requires MAIL_PASSWORD env var on server)
- CSRF / rate limiter (requires server deployment)

### Needs deployment (code-complete locally, not yet on server)
- CSRF protection (HTML forms + fetch monkey-patch)
- Rate limiting on login + AI routes
- Password reset via email (requires MAIL_PASSWORD on server)

---

## Architecture

Single-file Flask app (`app.py`, ~3450 lines) with Jinja2 templates in `Templates/`. No frontend framework — vanilla JS + `fetch()` throughout. No test suite.

### Stack
| Layer | Tool |
|-------|------|
| Backend | Python 3.14 / Flask 3.x |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login |
| CSRF | Flask-WTF (CSRFProtect) |
| Rate limiting | Flask-Limiter (in-memory) |
| Email | Flask-Mail (SendGrid SMTP) |
| AI | Anthropic Claude API (`claude-sonnet-4-6`) |
| Database | PostgreSQL (`localhost:5432/estimator_db`) |
| Production | Gunicorn + Nginx + systemd on DigitalOcean |
| Backup | Dropbox auto-sync |

### Two template bases
- `Templates/base.html` — marketing site (light theme, public routes)
- `Templates/app_base.html` — app interface (dark sidebar, login-required routes)

### Data flow
```
Assembly measurements (user input)
    → qty_formula per composition item → derived quantities
    → production_rate → labor/equipment hours
    → cost rates → line item costs
    → grouped/summed → project totals
```

### File structure
```
Estimator Agent/
├── app.py                      ← ~3450 lines; all routes + models
├── requirements.txt
├── Procfile                    ← gunicorn app:app
├── gunicorn.conf.py            ← runs migrations + seeding on_starting()
├── .env                        ← local dev (gitignored)
├── NORTHSTAR.md                ← philosophy reference
├── CLAUDE.md                   ← Claude Code project instructions
├── Agent_MD.md                 ← This file — master reference
├── seed_csi.py                 ← Already run — DO NOT run again
├── deploy/
│   ├── setup.sh
│   └── update.sh               ← `bash /var/www/zenbid/deploy/update.sh`
└── Templates/
    ├── base.html               ← Marketing base (light theme)
    ├── app_base.html           ← App base (dark theme, CSS vars, CSRF fetch patch)
    ├── login.html              ← /login
    ├── signup.html             ← /signup
    ├── forgot_password.html    ← /forgot-password  ← NEW Session 12
    ├── reset_password.html     ← /reset-password/<token>  ← NEW Session 12
    ├── index.html              ← Dashboard (app)
    ├── new_project.html
    ├── project.html            ← Project detail + inline estimate table + WBS
    ├── settings.html
    ├── library.html
    ├── assembly_builder.html
    ├── templates.html
    ├── production_rates.html
    ├── proposal.html           ← Light theme, print/PDF
    ├── profile.html
    ├── admin.html
    ├── summary.html
    ├── estimate.html           ← Legacy full-estimate route (still exists)
    ├── csi_report.html
    └── agentx_panel.html       ← AI panel partial, no Jinja tags
```

---

## Database Models

| Model | Table | Notes |
|-------|-------|-------|
| `Company` | `companies` | Tenant root |
| `User` | `users` | company_id FK; role: admin/estimator/viewer; reset_token + reset_token_expires |
| `CSILevel1` | `csi_level_1` | Seeded, never alter |
| `CSILevel2` | `csi_level_2` | Seeded, never alter |
| `Project` | `projects` | company_id FK; city, state, zip_code, project_type_id, market_sector_id |
| `Assembly` | `assemblies` | FK→project; is_template, measurement_params (JSON) |
| `AssemblyComposition` | `assembly_composition` | FK→assembly + library_item; qty_formula |
| `LibraryItem` | `library_items` | company_id FK; item_type, prod_base, all cost fields |
| `LineItem` | `line_items` | assembly_id NULLABLE; csi FKs, item_type, prod_base, trade |
| `GlobalProperty` | `global_properties` | company_id FK; category: trade/project_type/market_sector |
| `CompanyProfile` | `company_profile` | company_id FK; name, address, logo_path |
| `ProductionRateStandard` | `production_rate_standards` | Global (no company_id); min/typical/max rates |
| `WBSProperty` | `wbs_properties` | project_id FK; property_type, display_order |
| `WBSValue` | `wbs_values` | wbs_property_id FK; value_name, value_code, display_order |
| `LineItemWBS` | `line_item_wbs` | FK→line_item + wbs_property + wbs_value |

### Cost calculation logic (`calculate_item_costs()`)
```
equipment:           equipment_cost = qty × equipment_cost_per_unit; labor = 0
L&M + prod_base ON:  labor_hours = qty / production_rate; labor_cost = hours × labor_cost_per_hour
L&M + prod_base OFF: labor_cost = qty × labor_cost_per_unit; labor_hours = 0
total = material + labor + equipment
```
Client-side `recalcItem()` in `estimate.html` mirrors this exactly — keep in sync.

### Schema migration pattern
Always extend `run_migrations()` in `app.py` with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
Never drop/recreate tables. Never run `db.create_all()` on existing tables.

---

## All Routes

All require `@login_required` except marketing routes, `/login`, `/logout`, `/signup`, `/forgot-password`, `/reset-password/<token>`, `/uploads/logo/<f>`.
`/admin/*` additionally requires `@admin_required`.
AI routes additionally have `@limiter.limit('20 per minute')` (scope-gap: 10/min).
`/login` POST has `@limiter.limit('10 per minute')`.

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/` | Landing page |
| GET | `/pricing` | Pricing page |
| GET | `/features` | → redirect `/#features` |
| GET | `/about` | Placeholder |
| GET | `/blog` | Placeholder |
| GET | `/careers` | Placeholder |
| GET | `/contact` | Placeholder |
| GET | `/privacy` | Placeholder |
| GET | `/terms` | Placeholder |
| GET | `/security` | Placeholder |
| GET/POST | `/login` | Auth (rate limited 10/min POST) |
| GET | `/logout` | Auth |
| GET/POST | `/signup` | Create Company + admin User |
| GET/POST | `/forgot-password` | **NEW** Send reset email |
| GET/POST | `/reset-password/<token>` | **NEW** Set new password |
| GET | `/admin` | List companies + users |
| POST | `/admin/company/new` | Create company |
| POST | `/admin/user/new` | Create user |
| POST | `/admin/user/<id>/delete` | Delete user |
| POST | `/admin/user/<id>/edit` | Edit role/email/password |
| GET/POST | `/profile` | Change own password |
| GET | `/` (dashboard) | Dashboard (company-scoped projects) |
| GET/POST | `/project/new` | Create project |
| GET | `/project/<id>` | Project detail + inline estimate |
| POST | `/project/<id>/assembly/new` | Create assembly |
| POST | `/assembly/<id>/update` | Edit assembly |
| POST | `/assembly/<id>/lineitem/new` | New line item under assembly |
| POST | `/project/<id>/lineitem/new` | New standalone line item (JSON) |
| GET | `/project/<id>/summary` | **JSON only** — live totals bar |
| GET | `/project/<id>/report` | Assembly summary HTML |
| GET | `/project/<id>/estimate` | Full estimate table (legacy) |
| GET | `/project/<id>/estimate/csv` | CSV download |
| GET | `/project/<id>/report/csi` | CSI-grouped report |
| GET | `/project/<id>/assembly/builder` | Assembly Builder |
| POST | `/project/<id>/assembly/builder/save` | Save builder assembly |
| GET | `/templates` | Browse company templates |
| POST | `/project/<id>/assembly/load-template/<tid>` | Clone template into project |
| POST | `/lineitem/<id>/update` | Auto-save + recalculate |
| POST | `/lineitem/<id>/delete` | Delete line item |
| POST | `/assembly/<id>/delete` | Delete assembly + children |
| POST | `/project/<id>/update` | Edit project fields |
| POST | `/project/<id>/delete` | Delete project + children |
| GET | `/library` | Library (company-scoped) |
| POST | `/library/item/new` | Create library item |
| POST | `/library/item/<id>/update` | Edit library item |
| POST | `/library/item/<id>/delete` | Delete library item |
| GET | `/settings` | Settings page |
| POST | `/settings/company/update` | Upsert CompanyProfile |
| POST | `/settings/property/new` | Add GlobalProperty |
| POST | `/settings/property/<id>/delete` | Delete GlobalProperty |
| GET | `/settings/properties` | JSON list of company properties |
| GET | `/project/<id>/proposal` | Bid proposal (needs get_project_or_403 fix) |
| GET | `/production-rates` | Production rate standards |
| POST | `/production-rates/new` | Add standard |
| POST | `/production-rate/<id>/update` | Edit standard |
| POST | `/production-rate/<id>/delete` | Delete standard |
| GET | `/production-rates/search` | Search standards (JSON) |
| GET | `/uploads/logo/<filename>` | Serve uploaded logo |
| POST | `/ai/chat` | AgentX — chat (estimate/research/chat modes) |
| POST | `/ai/apply` | AgentX — apply write proposal |
| POST | `/ai/build-assembly` | AgentX — assembly auto-builder |
| POST | `/ai/scope-gap` | AgentX — scope gap analysis |
| POST | `/ai/production-rate` | AI rate lookup (RS Means style) |
| POST | `/ai/validate-rate` | Validate line item rate vs industry |
| POST | `/project/<id>/wbs/initialize` | Seed/backfill WBS properties |
| GET | `/project/<id>/wbs` | Get all WBS properties + values |
| POST | `/project/<id>/wbs/property` | Upsert WBS property name |
| POST | `/project/<id>/wbs/value` | Add WBS value |
| PUT | `/project/<id>/wbs/value/<id>` | Edit WBS value inline |
| POST | `/project/<id>/wbs/value/reorder` | Reorder WBS values |
| DELETE | `/project/<id>/wbs/value/<id>` | Delete WBS value |
| POST | `/line-item/<id>/wbs` | Assign WBS value to line item |

---

## Critical Patterns

**`/project/<id>/summary` must return JSON** — `project.html` fetches it on load for the live totals bar. Do not change its response type.

**JSON data embedding in templates:**
```html
<script id="my-data" type="application/json">{{ data | tojson | safe }}</script>
```
Parsed in JS: `JSON.parse(document.getElementById('my-data').textContent)`. XSS-safe.

**CSRF tokens:**
- All HTML `<form method="POST">` must include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- All `fetch()` POST calls are covered by the monkey-patch in `app_base.html` `<head>` — do not remove it
- Both `base.html` and `app_base.html` have `<meta name="csrf-token" content="{{ csrf_token() }}">`

**CSI dropdowns:** Level 1 rendered by Jinja; Level 2 populated by JS filtering an embedded JSON blob. No API round-trip.

**Cascade delete:** Handled in Python (delete children before parent). No `ON DELETE CASCADE` in DB.

**Datetime:** Always `datetime.now(timezone.utc)` — never `datetime.utcnow()` (deprecated in Python 3.14).

**`CSI_COLORS` dict:** Defined at module level in `app.py` AND duplicated in `estimate.html` JS — keep both in sync.

**Template pre-load:** `assembly_builder.html` accepts `?from_template=<id>`. When no template, pass `json.dumps(None)` → JS reads `null` → skips pre-fill.

**No Jinja tags in `agentx_panel.html`** — it's a pure HTML/CSS/JS partial. Jinja processes `{% %}` even in HTML comments, which caused a RecursionError in the past.

---

## UI Rules / Branding

### Typography
**Font stack (both themes):**
```
-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif
```
No external font imports (no Google Fonts). System UI stack only.

| Context | Size |
|---|---|
| Body / inputs / table cells | 13px |
| Labels / badges | 11–12px |
| Section headings (h2) | 16px |
| Stat / KPI numbers | 28px |

---

### Shared Brand Colors (both themes)
| Token | Hex | Use |
|---|---|---|
| `--primary-brand` | `#2D5BFF` | Buttons, links, active states |
| `--primary-hover` | `#1E40E0` | Button hover |
| `--accent-coral` | `#FF6B35` | CTAs, highlights, stat numbers |
| `--accent-hover` | `#E85A2A` | Coral hover |
| `--success` | `#10B981` | Positive states |
| `--warning` | `#F59E0B` | Caution states |
| `--error` | `#EF4444` | Destructive / error states |

---

### App (dark theme) — CSS variables in `app_base.html`
| Token | Hex | Use |
|---|---|---|
| `--app-bg` | `#0F1419` | Page background |
| `--app-card` | `#1A1F26` | Card / panel background |
| `--app-input` | `#252B33` | Input field background |
| `--app-hover` | `#2A3139` | Row / item hover |
| `--app-border` | `#2D3748` | Borders / dividers |
| `--app-sidebar` | `#16181D` | Sidebar background |
| `--text-primary` | `#E8EAED` | Primary text |
| `--text-secondary` | `#9CA3AF` | Labels / secondary text |
| `--text-muted` | `#6B7280` | Muted / placeholder |
| `--success-bg` | `rgba(16,185,129,0.1)` | Success badge background |
| `--warning-bg` | `rgba(245,158,11,0.1)` | Warning badge background |
| `--error-bg` | `rgba(239,68,68,0.1)` | Error badge background |
| `--info` | `#3B82F6` | Info states |
| `--info-bg` | `rgba(59,130,246,0.1)` | Info badge background |

**Do NOT hardcode old colors** (`#1a1a2e`, `#16213e`, `#0f3460`, `#e94560`) — use CSS variables.

CSS classes: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-coral`, `.btn-ghost`, `.btn-sm`, `.card`, `.badge-*`

---

### Marketing (light theme) — CSS variables in `base.html`
| Token | Hex | Use |
|---|---|---|
| `--marketing-bg` | `#FFFFFF` | Page background |
| `--marketing-section` | `#F9FAFB` | Alternating section background |
| `--marketing-card` | `#FFFFFF` | Card background |
| `--text-dark` | `#1F2937` | Primary text |
| `--text-gray` | `#6B7280` | Secondary text |
| `--text-light` | `#9CA3AF` | Muted / footer text |
| `--border-light` | `#E5E7EB` | Subtle dividers |
| `--border-medium` | `#D1D5DB` | Input borders |

---

### CSI Division Colors (data visualization)
Muted pastels used for color-coding CSI divisions in estimate tables and reports.
Defined in `CSI_COLORS` dict at module level in `app.py` AND duplicated in `estimate.html` JS — keep both in sync.

| Div | Hex | Div | Hex | Div | Hex |
|---|---|---|---|---|---|
| 01 | `#7b8cde` | 09 | `#debd7b` | 22 | `#7bb8de` |
| 02 | `#de9b7b` | 10 | `#9b7bde` | 23 | `#b87bde` |
| 03 | `#7bde9b` | 11 | `#7bde7b` | 25 | `#de7bde` |
| 04 | `#de7b9b` | 12 | `#de9b9b` | 26 | `#ffd070` |
| 05 | `#7bbdde` | 13 | `#7bcfde` | 27 | `#7bffd4` |
| 06 | `#c4de7b` | 14 | `#debf7b` | 28 | `#ff8a7b` |
| 07 | `#de7bbd` | 21 | `#de7b7b` | 31 | `#a8e6cf` |
| 08 | `#7bdec4` | | | 32 | `#dcedc1` |
| | | | | 33 | `#ffd3b6` |
| | | | | 34 | `#ffaaa5` |
| | | | | 35 | `#a29bfe` |
| fallback | `#888888` | | | | |

---

### Deprecated Colors — do not use
| Old Hex | Replaced By |
|---|---|
| `#1a1a2e` | `var(--app-bg)` |
| `#16213e` | `var(--app-card)` |
| `#0f3460` | `var(--app-input)` |
| `#e94560` | `var(--accent-coral)` |

---

## Authentication & Multi-Tenancy

- Flask-Login; all app routes `@login_required`; public exceptions: `/`, `/login`, `/logout`, `/signup`, `/forgot-password`, `/reset-password/<token>`, marketing pages, `/uploads/logo/<f>`
- Login accepts **email** (username fallback for legacy accounts)
- Signup creates Company + admin User in one transaction; seeds default GlobalProperties
- Isolation helpers: `get_project_or_403()`, `get_assembly_or_403()`, `get_lineitem_or_403()`, `get_library_item_or_403()`
- Roles: `admin` | `estimator` | `viewer` — only `/admin` routes enforce role check; viewer write restriction not yet enforced

---

## AgentX AI Panel

### Overview
Sliding panel (fixed right, 400px wide) available on every app page. `Templates/agentx_panel.html` — pure HTML/JS, no Jinja. Included via `{% include 'agentx_panel.html' %}` before `</body>` in all app templates except `proposal.html`.

### Three modes
| Mode | Behavior |
|------|----------|
| **Estimate** | Sends full project context to Claude; supports write proposals. Only active when URL matches `/project/<id>` |
| **Research** | Construction knowledge Q&A; no project data. Always available |
| **Chat** | General assistant. Always available |

### Panel features
- **Scope Gap Check** (`🔍 Check Scope`) — calls `POST /ai/scope-gap`; renders gap report card with severity sorting (HIGH/MEDIUM/LOW), completeness score bar, "Fix Gaps" trigger
- **Rate Lookup** (`📊 Rates`) — calls `POST /ai/production-rate`; returns min/typ/max table; "→ Use" pre-populates chat
- **Validate Rate** — right-click context menu on estimate table rows; calls `POST /ai/validate-rate`; renders ✓/⚠ badge with 10s auto-dismiss
- **Write Proposals** — Claude returns fenced JSON block; frontend renders proposal card with Apply/Dismiss; Apply creates assembly + line items
- **Body push layout** — `body.ax-panel-open { padding-right: 410px }` — content shifts, no overlay blocking estimate table

### Key AI routes
- `/ai/chat` — multi-mode, builds context from project data + production rate standards
- `/ai/apply` — creates/updates assembly + inserts line items via `calculate_item_costs()`
- `/ai/build-assembly` — auto-builds assembly from plain English description
- `/ai/scope-gap` — project completeness analysis, JSON-only Claude response
- `/ai/production-rate` — RS Means-style rate lookup with regional context
- `/ai/validate-rate` — compares line item rate vs industry benchmarks

---

## Assembly Builder Formula Keys

| Key | Calculation |
|-----|-------------|
| `fixed` | `qty_manual` value |
| `lf` | LF |
| `lf_x_2` | LF × 2 |
| `sf` | LF × Height |
| `sf_div` | (LF × Height) ÷ qty_divisor |
| `depth` | LF × Depth |
| `volume_cy` | LF × Width × Depth ÷ 27 |

---

## Deployment

### Production (zenbid.io — ✅ back online 2026-03-17)
- DigitalOcean droplet; systemd service `zenbid` → Gunicorn → Nginx
- Deploy: `bash /var/www/zenbid/deploy/update.sh`
- Migrations + seeding run automatically via `gunicorn.conf.py → on_starting()`

### Server `.env` (required)
```
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
FLASK_DEBUG=false
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=<sendgrid-api-key>
MAIL_DEFAULT_SENDER=noreply@zenbid.io
```

### Local dev
```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
# DB: postgresql://postgres:Builder@localhost:5432/estimator_db
```
**Do not run `seed_csi.py`** — CSI data is already seeded.

---

## Strategic Roadmap

### CRITICAL — must resolve before beta users

| Item | Status | Notes |
|------|--------|-------|
| Password reset | ✅ Done Session 12 | Needs MAIL_PASSWORD on server to send |
| CSRF protection | ✅ Done Session 12 | HTML forms + fetch monkey-patch |
| Rate limiting on AI routes | ✅ Done Session 12 | flask-limiter, in-memory |
| Privacy Policy & Terms | ❌ Open | Placeholder routes return plain text |
| ANTHROPIC_API_KEY on server | ⚠️ Config | Needs verification after DO is back up |

### HIGH PRIORITY — MVP for paying users

| Item | Status | Notes |
|------|--------|-------|
| Edit project fields UI | ⚠️ Partial | `POST /project/<id>/update` route exists; Edit Project modal missing city/state/zip/type/sector fields |
| Welcome email on signup | ⚠️ Easy now | flask-mail wired; just add `mail.send()` in `/signup` route |
| Contact page | ❌ Open | Placeholder |
| Viewer role enforcement | ❌ Open | Role checked only for `/admin`; viewers can currently write data |
| Proposal PDF export | ❌ Open | Print-to-PDF only; server-side PDF needs weasyprint or headless Chrome |
| Proposal route isolation | ❌ Open | `GET /project/<id>/proposal` uses bare `Project.query.get()` not `get_project_or_403()` |

### MEDIUM PRIORITY — core SaaS features

| Item | Status | Notes |
|------|--------|-------|
| Subscription / billing | ❌ | Stripe Checkout + webhook |
| Free trial gate | ❌ | Limit projects/features for new signups |
| In-app onboarding | ❌ | Empty state CTAs, first-time guide |
| About / Blog / Careers pages | ❌ | Footer links return plain text |
| Delete buttons in estimate table | ❌ | Must go to project page to delete line items |

### FUTURE — post-launch

| Item | Notes |
|------|-------|
| Audit logging | Enterprise compliance, debug support |
| Subcontractor bid requests | Send line items to subs, receive quotes |
| Takeoff file import | PDF/DWG → auto-populate assemblies |
| Public API | Webhook / REST for firm integrations |
| Mobile-responsive estimate view | Currently desktop-only |
| Streaming AI responses | Token-by-token output, SSE |
| AgentX conversation memory | `axHistory[]` array; multi-turn context |
| Quick-action chips | Zero-backend prompt shortcuts in AgentX |
| Bulk import for production rates | CSV upload to populate standards table |

---

## Known Gaps & Technical Debt

| Gap | Severity | Notes |
|-----|----------|-------|
| Proposal route not using `get_project_or_403()` | High | Any logged-in user can view any project's proposal |
| Viewer role not enforced on write routes | Medium | Low risk until teams are a feature |
| `estimate.html` route still exists | Low | Legacy `/project/<id>/estimate` alongside inline `project.html` table |
| `equipment_hours` always 0 | Low | Deprecated by item_type logic; harmless |
| No CSRF on `/forgot-password` form | Low | It's a public unauthenticated route — lower risk, but should add |
| Rate limiter is in-memory | Low | Resets on server restart; fine for now, swap to Redis for multi-worker |
| WBS `area` → `location_1` migration | Low | Old projects with `wbs_area` type auto-normalize on first project page load |
| Existing projects may have NULL company_id | Low | Fixed at deploy by UPDATE statements |

---

## Session History

| # | Date | Key Work |
|---|------|----------|
| 1 | 2026-03-08 | Core app: project/assembly/line item CRUD, estimate table, summary report |
| 2 | 2026-03-08 | CSI dropdowns, delete routes for all levels |
| 3 | 2026-03-09 | NORTHSTAR.md, Edit Assembly, Line Item Library, Assembly Builder v2 |
| 4 | 2026-03-09 | Estimate toggle views, AI/Ollama layer, CSV export, CSI report, Assembly Templates |
| 5 | 2026-03-10 | CLAUDE.md, full app audit, bug fixes (KeyError, datetime deprecation) |
| 6 | 2026-03-10 | Global Properties, Company Profile, item_type/prod_base logic, 2-step Add Line Item |
| 7 | 2026-03-11 | Authentication + Multi-Tenancy (Flask-Login, Company/User models, full isolation) |
| 8 | 2026-03-11 | Bid Proposal template, Production Rate Standards CRUD + lookup modal |
| 9 | 2026-03-12 | AgentX AI panel: Claude API, /ai/chat + /ai/apply routes, voice input, removed Ollama |
| 10 | 2026-03-12 | AgentX extracted to partial, context-aware mode init, fixed Jinja recursion bug |
| 11 | 2026-03-13 | project.html inline table overhaul: inline cell editing, multi-select Group By, WBS in Edit Project modal, Location 1/2/3 |
| 11b | 2026-03-14 | WBS value inline editing + drag-to-reorder, AI rate lookup panel, validate-rate, requirements.txt |
| 11c | 2026-03-14 | Marketing site + dark theme re-skin (CSS vars), production deployment to zenbid.io (Gunicorn+Nginx+systemd), login via email, /signup route |
| 12 | 2026-03-15 | **CSRF** (flask-wtf, meta tag, fetch monkey-patch, hidden fields on 3 forms) + **rate limiting** (flask-limiter on login + 5 AI routes) + **password reset** (flask-mail, /forgot-password, /reset-password/<token>, 2 new templates) |
| 13 | 2026-03-17 | **Production deployment**: zenbid.io back online after DO outage. Fixed landing route (was redirecting to signup), templates case-sensitivity on Linux (Templates/ → templates/), pool_pre_ping for stale DB connections, SendGrid SMTP setup (port 2525, verified sender thomas@zenbid.io). Full smoke test passed: landing, login, forgot-password, password reset all working. |

---

## Python / Framework Notes

- Python 3.14: use `datetime.now(timezone.utc)` — never `datetime.utcnow()`
- Flask-WTF CSRF: `WTF_CSRF_TIME_LIMIT = 3600`; token auto-injected by fetch monkey-patch in `app_base.html`; new HTML forms need `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- Flask-Limiter: in-memory storage — resets on restart; acceptable for now; swap to `storage_uri='redis://...'` for multi-worker production
- Flask-Mail: configured via env vars; SendGrid SMTP by default; `MAIL_PASSWORD` = SendGrid API key
