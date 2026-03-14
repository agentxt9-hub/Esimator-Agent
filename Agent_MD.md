# Construction Estimating Tool — Working Reference
**Last updated:** 2026-03-12 | **Current session:** 10
**Prepared by:** Claude (claude-sonnet-4-6)

---

## Quick Start

```bash
pip install flask psycopg2-binary sqlalchemy flask-sqlalchemy flask-login anthropic python-dotenv
python app.py
```

App runs at `http://localhost:5000`.
DB: `postgresql://postgres:Builder@localhost:5432/estimator_db`
**Do NOT re-run `seed_csi.py`** — CSI data is already seeded.

### First-Time Bootstrap (auth setup)
1. Run `migration.sql` in pgAdmin
2. `python app.py` (creates tables + runs migrations automatically)
3. Create first admin via Python shell:
   ```python
   from app import app, db, Company, User
   with app.app_context():
       co = Company(company_name="Your Company")
       db.session.add(co)
       db.session.flush()
       u = User(company_id=co.id, username="admin", email="you@example.com", role="admin")
       u.set_password("strong-password")
       db.session.add(u)
       db.session.commit()
   ```
4. Assign existing data to company (run in pgAdmin):
   ```sql
   UPDATE projects          SET company_id = 1 WHERE company_id IS NULL;
   UPDATE library_items     SET company_id = 1 WHERE company_id IS NULL;
   UPDATE global_properties SET company_id = 1 WHERE company_id IS NULL;
   UPDATE company_profile   SET company_id = 1 WHERE company_id IS NULL;
   ```

---

## Architecture

Single-file Flask app (`app.py`) with Jinja2 templates in `Templates/`. No frontend framework — vanilla JS + `fetch()` throughout. No test suite.

**Data flow:**
```
Assembly measurements (user input)
    → qty_formula per composition item → derived quantities
    → production_rate → labor/equipment hours
    → cost rates → line item costs
    → grouped/summed → project totals
```

**Design philosophy (NORTHSTAR.md):**
> *Could a rigid (Excel-minded) estimator use this comfortably? Could a flexible (AI-native) estimator use this expressively?* If either is "no," reconsider.
- Flexibility Over Dogma | AI as Optional Augmentation | Offline-First

---

## File Structure

```
Estimator Agent/
├── app.py                          ← ~1900+ lines; all routes + models
├── .env                            ← ANTHROPIC_API_KEY (real key set)
├── migration.sql                   ← Run once in pgAdmin before first auth startup
├── seed_csi.py                     ← Already run — DO NOT run again
├── NORTHSTAR.md                    ← Philosophy reference — read before major decisions
├── CLAUDE.md                       ← Claude Code quick-start reference
├── Agent_MD.md                     ← This file — single working reference
└── Templates/
    ├── nav.html                    ← Jinja2 include partial — injected in all templates
    ├── agentx_panel.html           ← AgentX AI panel partial — injected in all templates
    ├── login.html                  ← /login — standalone, no auth required, NO AgentX
    ├── proposal.html               ← Bid proposal — light theme print/PDF, NO AgentX
    ├── admin.html                  ← /admin — manage companies + users
    ├── profile.html                ← /profile — change own password
    ├── index.html                  ← Dashboard (company-scoped projects)
    ├── new_project.html            ← Create project (city/state/zip + type/sector)
    ├── project.html                ← Project detail + edit modal
    ├── settings.html               ← Company profile + Global Properties
    ├── summary.html                ← Assembly summary report
    ├── estimate.html               ← Full estimate (2-step Add Line Item, toggle views)
    ├── library.html                ← Library CRUD (company-scoped)
    ├── assembly_builder.html       ← Builder + "Create New Library Item" mini-modal
    ├── csi_report.html             ← CSI-grouped report with print
    ├── templates.html              ← Template browse (company-scoped)
    ├── production_rates.html       ← Production rate standards (global reference)
    └── ...
```

---

## Database Models

| Model | Table | Notes |
|-------|-------|-------|
| `Company` | `companies` | Tenant companies |
| `User(UserMixin)` | `users` | company_id FK; role: admin/estimator/viewer |
| `CSILevel1` | `csi_level_1` | Seeded, never alter |
| `CSILevel2` | `csi_level_2` | Seeded, never alter |
| `Project` | `projects` | company_id FK; city, state, zip_code, project_type_id, market_sector_id |
| `Assembly` | `assemblies` | FK→project; is_template, measurement_params (JSON) |
| `AssemblyComposition` | `assembly_composition` | FK→assembly + library_item; qty_formula, costs |
| `LibraryItem` | `library_items` | company_id FK; item_type, prod_base, all cost fields |
| `LineItem` | `line_items` | assembly_id NULLABLE; csi FKs, item_type, prod_base, trade |
| `GlobalProperty` | `global_properties` | company_id FK; category: trade/project_type/market_sector |
| `CompanyProfile` | `company_profile` | company_id FK; name, address, logo_path |
| `ProductionRateStandard` | `production_rate_standards` | Global (no company_id); min/typical/max rates |

### Cost Calculation Logic (`calculate_item_costs()`)
```
equipment:           equipment_cost = qty × equipment_cost_per_unit; labor = 0
L&M + prod_base ON:  labor_hours = qty / production_rate; labor_cost = hours × labor_cost_per_hour
L&M + prod_base OFF: labor_cost = qty × labor_cost_per_unit; labor_hours = 0
total = material + labor + equipment
```
Client-side `recalcItem()` in `estimate.html` mirrors this exactly — keep in sync.

### Schema Migration Pattern
Always extend `run_migrations()` in `app.py` with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
Never drop/recreate tables. Never run `db.create_all()` on existing tables.

---

## All Routes

All routes require `@login_required` except `/login`, `/logout`, `/uploads/logo/<f>`.
`/admin/*` additionally requires `@admin_required`.

| Method | Route | Purpose |
|--------|-------|---------|
| GET/POST | `/login` | Auth |
| GET | `/logout` | Auth |
| GET | `/admin` | List companies + users |
| POST | `/admin/company/new` | Create company + seed default properties |
| POST | `/admin/user/new` | Create user |
| POST | `/admin/user/<id>/delete` | Delete user |
| POST | `/admin/user/<id>/edit` | Edit role/email/password |
| GET/POST | `/profile` | Change own password |
| GET | `/` | Dashboard (company-scoped) |
| GET/POST | `/project/new` | Create project |
| GET | `/project/<id>` | Project detail |
| POST | `/project/<id>/assembly/new` | Create assembly |
| POST | `/assembly/<id>/update` | Edit assembly |
| POST | `/assembly/<id>/lineitem/new` | New line item under assembly |
| POST | `/project/<id>/lineitem/new` | New standalone line item (returns full JSON) |
| GET | `/project/<id>/summary` | **JSON only** — live totals bar |
| GET | `/project/<id>/report` | Assembly summary HTML |
| GET | `/project/<id>/estimate` | Full estimate table |
| GET | `/project/<id>/estimate/csv` | CSV download |
| GET | `/project/<id>/report/csi` | CSI-grouped report |
| GET | `/project/<id>/assembly/builder` | Assembly Builder (`?from_template=<id>` supported) |
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
| GET | `/project/<id>/proposal` | Bid proposal |
| GET | `/production-rates` | Production rate standards |
| POST | `/production-rates/new` | Add standard |
| POST | `/production-rate/<id>/update` | Edit standard |
| POST | `/production-rate/<id>/delete` | Delete standard |
| GET | `/production-rates/search` | Search standards (JSON) |
| GET | `/uploads/logo/<filename>` | Serve uploaded logo |
| **POST** | **`/ai/chat`** | **AgentX — multi-mode AI chat (estimate/research/chat)** |
| **POST** | **`/ai/apply`** | **AgentX — apply a write proposal to the estimate** |

---

## AgentX AI Panel

### Overview
A sliding panel (fixed right, z-index 1200) available on every page. Implemented as `Templates/agentx_panel.html` partial — included via `{% include 'agentx_panel.html' %}` just before `</body>` in all templates except `login.html` and `proposal.html`.

### Three Modes
| Mode | Behavior | When Available |
|------|----------|----------------|
| **Estimate** | Sends full project context (assemblies, line items, totals, CSI codes, production rate standards) to Claude; supports write proposals | Only when URL matches `/project/<id>` |
| **Research** | Construction knowledge base Q&A; no project data | Always |
| **Chat** | General assistant | Always |

### Page Context Detection
```javascript
const AX_PROJECT_ID = (function() {
    const m = window.location.pathname.match(/\/project\/(\d+)/);
    return m ? parseInt(m[1]) : null;
})();
```
- If `AX_PROJECT_ID` is not null → Estimate mode enabled, defaults active
- If `AX_PROJECT_ID` is null → Estimate button disabled (grayed, tooltip), defaults to Research

### Write Proposals
- User asks AgentX to "suggest items" or similar with Estimate mode + write permission enabled
- Claude returns a fenced ` ```json ``` ` block parsed by regex in `/ai/chat`
- Frontend renders a proposal card with line item preview + Apply/Dismiss buttons
- "Apply" POSTs to `/ai/apply` which creates the assembly (if new) and inserts line items via `calculate_item_costs()`
- Proposal card stores proposal data as DOM property `card._proposal`

### `/ai/chat` Route
- Builds mode-specific system prompt
- In Estimate mode: queries all assemblies + line items for the project, CSI maps, production rate standards, live totals → formats as structured text context for Claude
- Calls `anthropic.Anthropic(api_key=...).messages.create(model="claude-sonnet-4-20250514", max_tokens=2048, ...)`
- Strips ` ```json ``` ` write proposal from reply text before sending to frontend
- Returns: `{success, reply, write_proposal (optional), mode}`

### `/ai/apply` Route
- Receives `{proposal, project_id}` from frontend
- If `proposal.new_assembly` present: creates a new Assembly row, flushes to get ID
- If `proposal.target_assembly_id`: looks up existing assembly (verifies it belongs to project)
- Inserts each `line_items[]` entry as a `LineItem`, runs `calculate_item_costs()` on each
- Returns: `{success, assembly_id, items_inserted}`

### Critical: No Jinja Tags in agentx_panel.html
`agentx_panel.html` is pure HTML/CSS/JS — no `{% %}` or `{{ }}` tags.
**Lesson learned:** Jinja2 processes `{% %}` tags even inside HTML comments (`<!-- -->`). The original file had `{% include 'agentx_panel.html' %}` in a comment — this caused a RecursionError. Fixed by replacing the multi-line comment with a plain one-line comment.

---

## Critical Patterns — Do Not Change

**`/project/<id>/summary` must return JSON** — `project.html` fetches it on load for the live totals bar.

**JSON data embedding in templates:**
```html
<script id="my-data" type="application/json">{{ data | tojson | safe }}</script>
```
Parsed in JS with `JSON.parse(document.getElementById('my-data').textContent)`. XSS-safe.

**CSI dropdowns:** Level 1 rendered by Jinja; Level 2 populated by JS filtering an embedded JSON blob.

**Cascade delete:** Handled in Python (delete children before parent). No `ON DELETE CASCADE` in DB.

**Datetime:** Always `datetime.now(timezone.utc)` — never `datetime.utcnow()` (deprecated in Python 3.14).

**`CSI_COLORS` dict:** Defined at module level in `app.py` AND duplicated in `estimate.html` JS — keep both in sync.

**Template pre-load:** `assembly_builder.html` accepts `?from_template=<id>`. When no template, pass `json.dumps(None)` → JS reads `null` → skips pre-fill.

---

## UI Rules — Dark Theme, No Exceptions

| Element | Value |
|---------|-------|
| Page background | `#1a1a2e` |
| Card/container background | `#16213e` |
| Panel/input background | `#0f3460` |
| Primary accent | `#e94560` |
| Primary accent hover | `#c73652` |
| Danger button bg | `#3a0a12` |
| Danger button text/border | `#e94560` |
| Danger hover | full red bg |
| Body text | `#eee` |
| Muted text | `#888` / `#aaa` |
| Font | Arial, sans-serif |
| AgentX panel header bg | `#0d1b2a` |

CSS classes: `.btn`, `.btn-secondary`, `.btn-danger`, `.btn-sm`

**Exception:** `proposal.html` uses a light/white theme — intentional for client-facing print output.

---

## Authentication & Multi-Tenancy

- **Flask-Login** — `current_user` auto-available in all templates
- **All routes** require `@login_required`; `/login`, `/logout` are public
- **`admin_required` decorator** — aborts 403 if `current_user.role != 'admin'`
- **Isolation helpers:** `get_project_or_403(id)`, `get_assembly_or_403(id)`, `get_lineitem_or_403(id)`, `get_library_item_or_403(id)` — abort 403 on cross-company access
- **Templates** filtered through `Project.company_id` JOIN (Assembly → Project → company_id)
- **`_seed_company_properties(company_id)`** — seeds default trades/types/sectors on company creation
- **SECRET_KEY** — set via `SECRET_KEY` env var; dev default in code — MUST change for production

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

## Feature Status

| # | Feature | Status |
|---|---------|--------|
| 1 | Project CRUD + dashboard | ✅ |
| 2 | Assembly + Line Item CRUD with cost calculation | ✅ |
| 3 | Edit Assembly modal | ✅ |
| 4 | Line Item Library (company-scoped CRUD) | ✅ |
| 5 | Assembly Builder v2 (measurements + formula-driven quantities) | ✅ |
| 6 | Estimate Toggle Views (Assembly/CSI/Trade/Flat, collapsible, color-coded) | ✅ |
| 7 | Export / Reporting (CSV, CSI report, print, bid proposal) | ✅ |
| 8 | Assembly Templates (browse, clone, open-in-builder) | ✅ |
| 9 | Global Properties, Company Profile, Project Type/Sector, item_type/prod_base logic | ✅ |
| 10 | Authentication + Multi-Tenancy (Flask-Login, Company/User models, full isolation) | ✅ (untested end-to-end) |
| 11 | Production Rate Standards (global reference, CRUD, lookup modal in Library) | ✅ (untested end-to-end) |
| 12 | Bid Proposal (light-theme, company branding, print/PDF) | ✅ (untested end-to-end) |
| 13 | **AgentX AI Panel** (Claude-powered, 3 modes, write proposals, voice, all pages) | ✅ live-tested, working |
| 14 | **Scope Gap Detector** (`POST /ai/scope-gap` + AgentX UI panel) | ✅ **NEW — needs live test** |

---

## Known Issues / Gaps

1. **AgentX panel scroll** — persistent issue across multiple fix attempts. The panel renders content and the scrollbar thumb appears, but scroll events may not propagate on some browser/OS combinations. Root-cause history: tried `min-height: 0`, `overflow: hidden` on panel, `flex: 1 1 0`, `max-height: 100%`, and finally converted `.ax-messages` from `display: flex` to `display: block` (the most reliable approach). **Needs live confirmation that scroll now works after the block layout change.**
2. **Scope Gap Detector not live-tested** — `POST /ai/scope-gap` route and UI complete; needs a real project with assemblies to verify Claude returns valid JSON, severity sorting, and the "Fix Gaps" chat trigger works.
3. **Sessions 10–12 untested end-to-end** — auth, bid proposal, and production rates code is complete but no confirmed live server run.
4. **Bootstrap chicken-and-egg** — no self-serve admin UI; first user created via Python shell.
5. **Existing data has NULL company_id** — must run the 4 UPDATE statements after migration.sql.
6. **`/project/<id>/proposal` not using `get_project_or_403()`** — verify before multi-company deployment.
7. **Viewer role not enforced on write routes** — viewer can currently POST/edit data; only blocked from `/admin`.
8. **SECRET_KEY is dev placeholder** — must set env var before any hosted deployment.
9. **`equipment_hours` field** — exists on LineItem, always 0; deprecated by item_type logic. Harmless.

---

## Next Session: Confirm Scroll + AI UX Enhancements

### FIRST — Confirm the Scroll Fix Works
Before building anything new, open a project, open AgentX, run a Scope Gap Check, and confirm the results card scrolls. If scroll still does not work after the `display: block` change, the next thing to try is replacing the messages container entirely with a non-flex wrapper:

```html
<!-- Replace <div class="ax-messages" id="ax-messages"> with: -->
<div id="ax-messages" style="flex:1;min-height:0;overflow-y:scroll;padding:14px;"></div>
```
Using inline style bypasses any CSS cascade conflicts from template stylesheets. If that still fails, the issue is a browser event capture problem (scroll events being caught by a parent), not a CSS sizing issue.

---

### Priority 2 — Conversation Memory (per-session)
Currently each `/ai/chat` call is completely stateless. Add a JS array `axHistory = []` that accumulates `{role, content}` pairs. On each send, append the user message, POST the full history to `/ai/chat`, and append Claude's reply. Backend passes `axHistory` as the `messages` array to the Anthropic API (system prompt stays separate). This makes every interaction dramatically better — Claude remembers what it said two turns ago.

**Frontend change:** `axHistory` array, push to it in `axSend()`, send as `history` in the POST body.
**Backend change:** In `/ai/chat`, use `data.get('history', [])` as the messages list; fall back to `[{'role':'user','content':message}]` if empty.

### Priority 3 — Quick-Action Chips
Zero backend work. Add a row of prompt buttons below the welcome bubble (only shown when no conversation has started yet). Each chip sets the input value and calls `axSend()`:
- "What's the most expensive assembly?"
- "Are any labor rates unusually high?"
- "Summarize this estimate for a client"
- "What's missing from this estimate?"

Hide the chips after first send (`axHistory.length > 0`).

### Priority 4 — Streaming Responses
Replace the static "AgentX is thinking…" bubble with token-by-token streaming using the Anthropic streaming API (`stream=True`). Flask yields SSE chunks; frontend uses `EventSource` or manual `fetch` + `ReadableStream` to update the bubble content as tokens arrive. Makes the panel feel far more responsive for long answers.

**Backend:** Replace `client.messages.create(...)` with `client.messages.stream(...)` in a generator route that yields `data: token\n\n`.
**Frontend:** Use `fetch` with `response.body.getReader()` to consume the stream.

### Priority 5 — Write Proposal UX Polish
- After "Apply" succeeds, show an "Open Estimate →" link in the confirmation message
- Add "Reject with feedback" button on proposal cards — pre-populates input with "That's not right because…" and sends as a follow-up message
- Show an item count badge on proposal cards: "3 new line items"

### Priority 6 — Research Mode: Source Context
When in Research mode, search `ProductionRateStandard` rows for terms matching the user's query and inject the top 10 matches into the system prompt. Grounds construction knowledge answers in the project's actual rate data rather than generic knowledge.

---

## Session History

| Session | Date | Key Work |
|---------|------|----------|
| 1 | 2026-03-08 | Core app: project/assembly/line item CRUD, estimate table, summary report |
| 2 | 2026-03-08 | CSI dropdowns, delete routes for all levels |
| 3 | 2026-03-09 | NORTHSTAR.md, Edit Assembly, Line Item Library, Assembly Builder v2 |
| 4 | 2026-03-09 | Estimate toggle views, AI/Ollama layer, CSV export, CSI report, Assembly Templates |
| 5 | 2026-03-10 | CLAUDE.md, full app audit, bug fixes (KeyError, datetime deprecation) |
| 6 | 2026-03-10 | Global Properties, Company Profile, item_type/prod_base logic, 2-step Add Line Item |
| 7 | 2026-03-11 | Authentication + Multi-Tenancy (Flask-Login, Company/User models, full isolation) |
| 8 | 2026-03-11 | Bid Proposal template, Production Rate Standards CRUD + lookup modal |
| 9 | 2026-03-12 | AgentX AI panel: Claude API integration, /ai/chat + /ai/apply routes, voice input, removed Ollama |
| 10 | 2026-03-12 | AgentX on every page: extracted to agentx_panel.html partial, context-aware mode init, fixed Jinja recursion bug |
| 11 | 2026-03-12 | Scope Gap Detector: POST /ai/scope-gap route + full UI in AgentX panel; panel scroll fixes (multiple attempts); body push layout (content shifts instead of panel overlapping) |

---

## Scope Gap Detector (Session 11 — 2026-03-12)

### Backend: `POST /ai/scope-gap` (app.py)
- `@login_required`, multi-tenant via `get_project_or_403()`
- Fetches: full project details, all assemblies + line items with CSI titles, live totals (mat/lab/equ/hrs/total), set of CSI divisions present, up to 80 `ProductionRateStandard` rows
- System prompt: senior estimator persona, 3-level gap analysis:
  - `MISSING_LINE_ITEM` — items missing within existing assemblies
  - `MISSING_ASSEMBLY` — entire scopes absent given project type
  - `MISSING_CSI_DIVISION` — entire divisions with no representation
- Severity: `HIGH` / `MEDIUM` / `LOW` with specific cost impact guidance
- Requires JSON-only response (no markdown), strips accidental fences via regex
- Sorts gaps `HIGH → MEDIUM → LOW` before returning
- Returns: `{ success, summary, completeness_score, gaps[], strengths[], review_notes }`

### Frontend: `agentx_panel.html`
- **`🔍 Check Scope`** button in panel header — `#0f3460` bg, `1px solid #e94560` border, disabled when no project in URL
- Inline loading bubble while waiting: "🔍 AgentX is reviewing your estimate for scope gaps…"
- **Report card rendered inline in messages area** (not a modal):
  - Header: title, project subtitle, completeness score bar (red <80%, gold 80–94%, green 95%+), summary italic
  - Gaps section: each gap as a left-border card (HIGH=red, MEDIUM=gold, LOW=blue), severity badge pill, assembly name, description, suggested action, cost impact
  - Strengths section: green bullet list
  - Review Notes: italic #aaa
  - "⚡ Fix Gaps — Build Missing Assemblies" full-width red button → populates chat input + enables write permission + fires `axSend()`
- Error handling: specific messages for empty estimate vs. API failure

---

## AgentX Panel Layout — Decision Log

### Body Push vs. Overlay (Session 11)
**Decision:** Removed the dark overlay (`agentx-overlay`) in favor of `body.ax-panel-open { padding-right: 410px }` with `transition: padding-right 0.3s ease`.
**Why:** The overlay blocked interaction with the estimate table. Users need to see their data while talking to AgentX.
**How:** `axOpen()` adds `document.body.classList.add('ax-panel-open')`, `axClose()` removes it. Since `agentx_panel.html` is included in every template's `<body>`, the CSS injection applies universally. The overlay `<div>` is still in the HTML but never shown.

### Panel Scroll — Multiple Fix Attempts (Session 11)
The messages area showed content but would not scroll. Attempted fixes in order:
1. Added `min-height: 0` to `.ax-messages` — standard flex scroll fix, did not resolve
2. Added `overflow: hidden` to `#agentx-panel` — prevents panel from growing past 100vh, did not resolve
3. Changed `flex: 1` → `flex: 1 1 0`, added `max-height: 100%` — did not resolve
4. **Final fix:** Changed `.ax-messages` from `display: flex; flex-direction: column` to `display: block`. The nested flex-child + flex-parent + overflow-scroll combination is unreliable in Chrome on Windows. A plain block element with bounded flex height + `overflow-y: scroll` works reliably in all browsers.
   - `align-self: flex-end/start` on bubbles replaced with `margin-left: auto` / `margin-right: auto`
   - `gap: 12px` replaced with `.ax-messages > * { margin-bottom: 12px }`
   - `align-self: stretch/flex-start` on proposal/scope cards replaced with `display: block; width: 100%`
**Status:** Not yet confirmed live — needs a browser test.

---

## Tech Stack

| Component | Tool | Notes |
|-----------|------|-------|
| Database | PostgreSQL | `localhost:5432/estimator_db` user: `postgres` pw: `Builder` |
| Backend | Python 3.14 / Flask | `python app.py` → localhost:5000 |
| ORM | Flask-SQLAlchemy | |
| Auth | Flask-Login | Session cookies, `current_user` in templates |
| AI | Anthropic Claude API | `claude-sonnet-4-20250514`; key in `.env` |
| Frontend | HTML/CSS/Vanilla JS (Jinja2) | No frameworks |
| Backup | Dropbox | Auto-syncing |
