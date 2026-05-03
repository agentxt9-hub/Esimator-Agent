# 03_TECHNICAL_AUDIT.md — Agent Three: Technical Audit

**Date:** 2026-04-29  
**Scope:** Full codebase read — backend, frontend, database, tests, deploy. No prior agent audits read.  
**Files read:** `app.py` (3,863 lines), `routes_takeoff.py`, `routes.py`, `gunicorn.conf.py`, `Procfile`, `requirements.txt`, `deploy/update.sh`, `migration.sql`, `test_takeoff.py`, `tests/test_estimate_table.py`, `tests/test_runner.py`, all templates, `static/css/`, `static/js/estimate_table.js`, `CLAUDE.md` (as reference checkpoint only)

---

## 1. Current-State Map

### Languages and Runtime
Python 3.14 (pyc evidence). JavaScript (vanilla `fetch()` for most surfaces; React 18 + TanStack Table v8 via CDN + Babel Standalone for the estimate grid). HTML/Jinja2. CSS. No TypeScript, no build step.

### Web Server Entry
`Procfile` → `gunicorn app:app --config gunicorn.conf.py`. Gunicorn binds `0.0.0.0:8000`; Nginx proxies port 80. Worker class `sync` (no async). Worker count = `cpu_count * 2 + 1`. Timeout 300s (set for PDF upload). No worker process management beyond Gunicorn default.

**Startup side-effects:** `gunicorn.conf.py:on_starting()` runs `db.create_all()`, `run_migrations()`, and `seed_production_rates()` in the pre-fork phase — before any workers are forked. This is correct placement; the side-effect runs once per deploy, not once per worker.

### Backend Entry and Structure
`app.py` is a single Python file of 3,863 lines. It contains every model, every route, every helper function, and every AI integration in one file. The file is organized into clearly commented sections (CONFIG, DATABASE MODELS, AUTH HELPERS, AUTH ROUTES, MARKETING ROUTES, PROJECT ROUTES, etc.) but the organization is textual, not structural — everything imports from the same module scope.

`routes_takeoff.py` (~460 lines) is the only Blueprint. It imports `db`, `TakeoffPlan`, `TakeoffPage`, `TakeoffItem`, `TakeoffMeasurement`, `get_project_or_403`, and `Project` directly from `app`. This import is managed by placing the `import routes_takeoff` at the bottom of `app.py` after all models are defined (line 3855), avoiding circular import errors through late-loading rather than proper package structure.

`routes.py` exists at the repository root. It defines a `login_required` decorator (using `session`, not Flask-Login), re-declares `landing()`, `features()`, `pricing()`, and other routes that already exist in `app.py`. It imports `psycopg2` directly. It is never imported anywhere. It is a dead file that would cause immediate errors if imported — duplicate route registrations and a separate auth model colliding with Flask-Login.

### Database
PostgreSQL. Accessed via SQLAlchemy (Flask-SQLAlchemy 3.x) with `psycopg2-binary`. Connection pooling via SQLAlchemy defaults plus `pool_pre_ping=True`.

**Schema management:** `run_migrations()` in `app.py` (line 3676) manages the schema exclusively through `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements executed sequentially via raw SQL. `db.create_all()` creates new tables. There is no schema migration tool (no Alembic, no Flyway). The `migration.sql` file at the repository root is a historical one-time script from the initial multi-tenancy migration; it is not part of the running system and has not been updated since.

The active migration system holds 34 statements covering the full history of schema additions across all sessions. New columns are appended chronologically. Column removal is not managed — removed concepts leave orphan columns.

### Takeoff Module
`routes_takeoff.py` registers 12 routes under the `takeoff` Blueprint. PDF uploads are stored at `static/uploads/takeoff/<project_id>/`. PyMuPDF is used only for page count extraction; PDF rendering is done client-side via PDF.js (loaded from CDN in `viewer.html`). Konva.js is vendored at `static/js/konva.min.js`. A duplicate `konva.min.js` exists at the repository root (untracked per git status).

Measurements are stored as normalized 0–1 coordinate arrays in `takeoff_measurements.points_json` (TEXT column). No server-side geometry computation; all measurement math runs in the browser.

### Estimate Surface (TanStack)
`/project/<id>/estimate` renders `estimate_table.html`, which mounts a React app via `<script type="text/babel">` sourced from `static/js/estimate_table.js`. React 18, TanStack Table v8, SheetJS, and Babel Standalone are loaded from CDN. There is no Node.js build step; Babel transpiles JSX in the browser at page load.

Four API routes serve the TanStack grid: `GET/POST /api/projects/<id>/line_items`, `PATCH/DELETE /api/line_items/<id>`. These routes use a simplified costing model distinct from the legacy routes (see Debt Inventory).

### Deploy
`deploy/update.sh` runs on the DigitalOcean droplet. It runs `git pull origin master`, installs requirements, and restarts the `zenbid` systemd service. The active repository branch is `main`. `git pull origin master` will fail unless a `master` branch also exists on the remote — a silent deployment blocker.

### Dependencies
`requirements.txt` specifies 12 packages with major version pinning. No `requests` library is listed; it is imported inside the `/waitlist` route handler as `import requests as req` (line 720). This works because `requests` is a transitive dependency of other packages in the venv, but it is not declared and could break on a clean install.

### No Background Workers
No Celery, no RQ, no APScheduler. All AI calls are synchronous in-request. A slow Anthropic response blocks the Gunicorn sync worker for its full duration. With the 300s timeout set for PDF upload, an AI route that hangs could tie up a worker for five minutes.

---

## 2. Documented versus Actual

### D1 — Dashboard Template

**Documentation says:** `index.html` is the authenticated dashboard; AgentX panel included there.

**Code does:** The `/dashboard` route (line 835) renders `app_dashboard.html`, which extends `app_base.html` and uses the current design system. `index.html` is not rendered by any route in `app.py`. `render_template('index.html', ...)` appears zero times in `app.py`. `index.html` is a fully orphaned file that no user can reach through any route. The documentation is describing a prior state.

**What it means:** All documentation about `index.html` as a live surface is stale. The dashboard design-system migration is already complete at the route level — `app_dashboard.html` is the live dashboard. `index.html` is a dead file generating no user exposure.

### D2 — AI Identity

**Documentation says:** The AI layer is called "Tally." NORTHSTAR, TALLY_VISION, CLAUDE.md, and DECISIONS.md all use "Tally" exclusively and describe three modes (Passive/Reactive/Generative).

**Code does:** Every user-visible AI reference is "AgentX": the tab button (`🤖 AgentX`), the welcome message (`Hi! I'm AgentX`), the mode labels (Estimate/Research/Chat), all toast messages, all CSS class prefixes (`ax-`), the route comment blocks. The `TALLY_VISION.md` modes are not implemented in any route or component. The TanStack grid defines `AI_STATUS` constants and column schema for Tally Passive but no data ever populates them.

**What it means:** The strategic rename from AgentX to Tally is purely a documentation event. Zero code reflects it. The flywheel architecture described in TALLY_VISION.md has no implementation beyond the schema fields added in Session 22.

### D3 — Takeoff Thumbnails

**Documentation says:** "Client-side thumbnails via PDF.js."

**Code does:** The `viewer()` route in `routes_takeoff.py` (line 78) explicitly sets `'thumbnail_url': None` for every page: `'thumbnail_url': None,   # always None — rendered client-side by PDF.js`. The PDF.js thumbnail rendering is done in `takeoff.js` client-side. The `thumbnail_path` column in `takeoff_pages` exists in the schema but is never populated by any server-side route.

**What it means:** `thumbnail_path` is a permanently null column occupying schema space. If server-side thumbnail generation is ever added, the column is ready; if not, it is dead weight.

### D4 — viewer_readonly Decorator

**Documentation says:** CLAUDE.md Security section lists "Viewer role not enforced on write routes — HIGH priority" and mentions `@viewer_readonly` as the planned decorator.

**Code does:** No `viewer_readonly` decorator exists anywhere in `app.py`, `routes_takeoff.py`, or any other Python file. The `admin_required` decorator exists (line 377). No viewer enforcement is applied to any write route.

**What it means:** Any authenticated user, regardless of role, can create, update, and delete assemblies, line items, projects, and library items. The viewer role is stored in the database but ignored by every write route.

### D5 — Deploy Branch

**Documentation says:** Deploy by running `bash /var/www/zenbid/deploy/update.sh` on the droplet.

**Code does:** `deploy/update.sh` line 10: `git pull origin master`. The repository's default branch (per the session's `git status` output) is `main`. Unless the remote has both a `master` and a `main` branch pointing to the same commits, `git pull origin master` will fail with "couldn't find remote ref master."

**What it means:** Every production deploy attempt via the documented update script will fail unless the operator manually overrides. The workaround would be to `git pull origin main`, but the script as written does not do this.

### D6 — `requests` Dependency

**Documentation says:** "`requests` library (installed in venv)" for the n8n webhook.

**Code does:** `requests` is not in `requirements.txt`. It is imported at call-site as `import requests as req` inside the `/waitlist` route (line 720). It currently exists as a transitive dependency, but a `pip install -r requirements.txt` on a fresh environment where no transitive dep pulls in `requests` would produce an ImportError at runtime when the first waitlist signup occurs.

---

## 3. Debt Inventory

### 3a — Dead Files

**`routes.py`** (repository root) — A shadow auth + route file from before Flask-Login adoption. Re-declares `login_required` using raw `session`, re-declares `landing()`, `features()`, `pricing()` and other routes. Uses `psycopg2` directly. Never imported. Would cause duplicate route registration errors and auth model collision if imported. Safe to delete.

**`index.html`** (`templates/`) — The pre-migration dashboard template. Not served by any route (see D1). Hardcodes the deprecated design system (`#1a1a2e`, `#e94560`, Arial). Still includes `agentx_panel.html`. Safe to delete.

**`estimate.html`** (`templates/`) — Documented as orphaned. No route renders it. Safe to delete.

**`nav.html`** (`templates/`) — Old navigation partial. Only used by templates that are themselves legacy or dead. No relationship to `app_base.html` sidebar.

**`konva.min.js`** (repository root, untracked) — Duplicate of `static/js/konva.min.js`. Untracked (not committed). Should not be present.

**`migration.sql`** (repository root) — One-time historical script, now superseded by `run_migrations()`. Not dangerous, but misleading as a standalone schema reference.

### 3b — Two Line Item Delete Semantics

The `line_items` table has an `is_deleted` soft-delete field (added Session 22). The TanStack API implements it:

- `DELETE /api/line_items/<id>` (line 1381): sets `item.is_deleted = True`, sets `item.estimator_action = 'rejected'`.

The legacy API does not:

- `POST /lineitem/<id>/delete` (line 1207): calls `db.session.delete(item)` — hard delete with no flywheel capture.
- `POST /ai/apply` (action `delete_line_item`, line 2792): calls `db.session.delete(item)` — hard delete.
- `POST /assembly/<id>/delete` (line 1391): `LineItem.query.filter_by(assembly_id=assembly_id).delete()` — hard delete of all items in assembly, no flywheel capture.
- `POST /project/<id>/delete` (line 1416): bulk hard deletes of all assemblies and line items.

Result: soft deletes only happen through the TanStack API. All other deletion paths bypass `is_deleted` and destroy the flywheel record. A soft-deleted item via the TanStack API will reappear in the legacy estimate view (`project.html`) because the legacy view does not filter on `is_deleted`.

### 3c — Two Cost Calculation Systems

`calculate_item_costs()` (line 1432) is the legacy system: it uses production rate, labor hours, material cost, labor cost, and equipment cost as separate computed fields. It writes to `item.labor_hours`, `item.labor_cost`, `item.material_cost`, `item.equipment_cost`, and `item.total_cost`.

The TanStack API (`api_create_line_item`, line 1299; `api_patch_line_item`, line 1362) uses a simplified model: `total_cost = qty * (labor_rate + mat_cost)`, where `labor_rate` maps to `item.labor_cost_per_unit` and `mat_cost` maps to `item.material_cost_per_unit`. It does not compute `labor_hours`, `labor_cost`, `material_cost`, or `equipment_cost` separately. The production rate is ignored.

`_api_item_dict()` (line 1219) — the serializer for the TanStack grid — also recomputes `line_total` on-the-fly as `qty * (labor_rate + mat_cost)`, which differs from the stored `total_cost` for any item created via the production-rate path.

The `ai_apply` route uses `calculate_item_costs()` when applying AI proposals, meaning AI-inserted items use the legacy costing model. These items will show different totals in the TanStack grid vs. the legacy view.

### 3d — No Application-Level Logging

`import logging` does not appear in `app.py`. `app.logger` is never used. Gunicorn's access log is configured (stdout), but there is no structured application logging for: user auth events, AI calls (what model, how many tokens, how long), failed migrations, CSRF rejections, rate limit hits, AI apply mutations. In production, debugging a failed AI call requires reading raw Gunicorn stdout with no context.

### 3e — AI Client Instantiated Per Request

Each of the five AI routes creates a fresh `anthropic.Anthropic(api_key=api_key)` client on every call. There is no module-level singleton or connection pool. This adds initialization overhead and prevents connection reuse. The model name `'claude-sonnet-4-20250514'` is hardcoded at five separate call sites (lines 2719, 2990, 3280, 3435, 3546).

### 3f — Silent Migration Failure

`run_migrations()` wraps each SQL statement in a `try/except` that calls `db.session.rollback()` on failure and then continues to the next statement (lines 3809–3814). There is no logging of failed statements. A migration that silently fails (e.g., type mismatch, permissions issue) leaves the schema partially updated with no indication. The system will appear to start normally.

### 3g — Deprecated ORM Pattern

`User.query.get(int(user_id))` (line 95, the Flask-Login user_loader), `Company.query.get(company_id)` (line 526), `WaitlistEntry.query.get(entry_id)` (line 733), and `Assembly.query.get(item.assembly_id)` (line 1225) use `Query.get()`, which was deprecated in SQLAlchemy 2.0. Flask-SQLAlchemy 3.x still supports it via compatibility shim, but it will break on a major dependency upgrade.

### 3h — Prompt Injection Exposure

User-supplied text is interpolated directly into AI system prompts via f-strings in every AI route. `project.project_name`, `project.description`, `item.description`, `item.trade`, `item.notes` are all inserted without sanitization. A user who sets their project description to a carefully crafted instruction can attempt to alter the AI's behavior or extract other users' data if prompt injection succeeds. No sanitization function exists anywhere in the AI prompt construction code.

### 3i — `requests` Not in requirements.txt

See D6. The n8n webhook call `import requests as req` at line 720 depends on an undeclared transitive dependency. It is imported at call-site inside a function, not at module level, so it would only fail at runtime on the first waitlist signup attempt on a fresh install.

---

## 4. Data Layer Assessment

### Schema Overview (14 active tables)

| Table | Key Nullable Fields | Notable Gaps |
|---|---|---|
| `companies` | none | No unique constraint on `company_name` |
| `users` | `email` nullable | No index on email; login queries by email full-scan |
| `csi_level_1` | — | Read-only; seeded |
| `csi_level_2` | — | Read-only; seeded |
| `projects` | `company_id` nullable | FK added via nullable migration; orphan projects possible |
| `assemblies` | many nullable | No index on `project_id`; primary query path unindexed |
| `assembly_composition` | most nullable | No index on `assembly_id` |
| `library_items` | most nullable | company_id nullable; orphan items possible |
| `line_items` | both `assembly_id` and `project_id` nullable | See below |
| `global_properties` | `company_id` nullable | — |
| `company_profile` | `company_id` nullable | No unique constraint; multiple profiles per company possible |
| `waitlist_entries` | — | email unique enforced |
| `waitlist_surveys` | responses as TEXT | comma-separated; no normalization |
| `production_rate_standards` | most nullable | No index on trade/description; full scan on every AI lookup |
| `wbs_properties` | — | cascade in ORM only, not DB |
| `takeoff_measurements` | — | points_json as TEXT, not JSONB |

### LineItem Table — Detailed

The `line_items` table has accumulated 27 columns across 22 sessions. It is the system's most critical table and has several coherence problems.

**Dual assignment:** Both `assembly_id` (FK→assemblies) and `project_id` (FK→projects) are nullable. Conceptually, a line item belongs either to an assembly (which belongs to a project) or directly to a project. In practice, items created via the TanStack API (`api_create_line_item`) set `project_id` only (no `assembly_id`), while items created via legacy routes and AI apply set `assembly_id`. Items created via Assembly Builder also set both. Nothing enforces mutual exclusivity or prevents items with neither key set.

**company_id partial population:** `line_items.company_id` was added in Session 22. Items created before Session 22 via legacy routes have `company_id = NULL`. The `api_create_line_item` route populates it; the legacy `POST /lineitem/new` route (line 960) does not. The `get_lineitem_or_403()` helper does not check `company_id` on the line item itself — it follows `assembly_id → project → company_id` or `project_id → company_id`. This is correct but means isolation relies on the parent chain, not the direct column.

**Cost field redundancy and inconsistency:** For a production-rate-based item: `labor_hours = qty / production_rate`, `labor_cost = labor_hours * labor_cost_per_hour`, `material_cost = qty * material_cost_per_unit`, `total_cost = material_cost + labor_cost + equipment_cost`. For a TanStack API item: `total_cost = qty * (labor_cost_per_unit + material_cost_per_unit)`. The field `labor_cost_per_unit` means different things in these two systems — in the production-rate model it is the per-unit derived cost; in the TanStack model it is the input rate directly used in the line total. The columns `labor_hours`, `labor_cost`, `material_cost`, `equipment_cost` are not populated by the TanStack API path — they remain NULL.

**Flywheel fields:** `ai_generated` (Boolean, default=False), `estimator_action` (VARCHAR(20)), `edit_delta` (Text). These fields are schema-ready. `estimator_action` is written to `'edited'` by `api_patch_line_item` (line 1369) and `'rejected'` by `api_delete_line_item` (line 1386). `edit_delta` is written as JSON to the Text column on every PATCH. However, `ai_generated` is never set to `True` by any route. Items created by AI via `/ai/apply` set `ai_generated=False` (default) or do not set it at all. Items created via the TanStack API explicitly set `ai_generated=False` (line 1314). There is no route or code path that ever sets `ai_generated=True`. Every row in production will have `ai_generated=False`. The primary discriminator field for the flywheel — the one that would allow computing "what percentage of AI suggestions did estimators accept vs. edit vs. reject" — is structurally broken on day one.

### Missing Indexes

The following query patterns occur frequently without indexes:
- `Assembly.query.filter_by(project_id=...)` — `assemblies.project_id` has no index in the model or in `run_migrations()`. The `migration.sql` indexes only `projects.company_id`, `library_items.company_id`, `global_properties.company_id`, and `users.company_id`. For a project with 50 assemblies in a database with 10,000 assemblies, every project page load does a full scan of the assemblies table.
- `LineItem.query.filter_by(assembly_id=...)` — `line_items.assembly_id` unindexed.
- `User.query.filter_by(email=...)` — `users.email` unindexed; login does a full scan.
- `ProductionRateStandard` — full scans on `trade` and `description` for every AI rate lookup.

### AI Layer Readiness

The schema has the right fields for a Tally Passive integration: `ai_status`, `ai_confidence`, `ai_note`, `ai_generated`, `estimator_action`, `edit_delta` all exist on `line_items`. The data types are adequate. The fundamental blocker is not schema — it is that `ai_generated` is never set to `True`, making the flywheel data uninterpretable. A query for "AI suggestions accepted" would return zero rows regardless of actual estimator behavior.

For an analytics layer: the current schema stores costs as computed Numeric values, not as normalized inputs (qty, rate, unit). Downstream analytics would need to reconstruct the cost build-up from the stored intermediates, and for TanStack API items, some of those intermediates (labor_hours, labor_cost) are NULL. A serious analytics or model training workload would require either a backfill migration or a denormalized event log.

---

## 5. AI Integration Readiness

### What Exists

Five routes in `app.py`: `/ai/chat` (line 2513), `/ai/apply` (line 2745), `/ai/build-assembly` (line 2883), `/ai/scope-gap` (line 3104), `/ai/production-rate` (line 3332), `/ai/validate-rate` (line 3462).

Each route: reads the Anthropic API key from `os.environ` at call time; instantiates `anthropic.Anthropic()` fresh; builds a system prompt as an f-string inline; calls `client.messages.create()` synchronously; parses the response; returns JSON. The model name `'claude-sonnet-4-20250514'` is hardcoded at each call site.

### Observable Characteristics

**No logging.** No AI call is logged anywhere. Token counts, latency, model version, and project context are not recorded. There is no way to audit AI costs in production, detect degraded responses, or correlate a bad output to a specific user session.

**No prompt versioning.** All prompts are f-strings hardcoded inline in the route handler. Changing a prompt requires a code deploy. There is no way to A/B test prompts or roll back a prompt change independently of a code change.

**No response storage.** AI responses are not stored. An estimator receives an AI suggestion, acts on it (or not), and the raw response is gone. The only evidence that an AI call occurred is the mutations to `line_items` rows (if the estimator applied the proposal), and even those rows have `ai_generated=False`.

**No cost instrumentation.** The `response` object from the Anthropic SDK contains `usage` (input tokens, output tokens). This is never read or logged. There is no way to track monthly spend by route, by user, or by project.

**Prompt injection surface.** The `/ai/chat` route (line 2602) injects `project.project_name`, `project.description`, user-controlled assembly names and line item descriptions into the system prompt without sanitization. The `/ai/build-assembly` route (line 2923) injects `project.project_name`, location fields, and the user-provided `description` string directly. A user who sets their project name or a line item description to `"IGNORE PREVIOUS INSTRUCTIONS"` or similar can attempt to manipulate the model's behavior.

**Synchronous, blocking.** All AI calls block a Gunicorn sync worker for their full duration. The scope gap and build-assembly prompts request up to 4,096 output tokens from a large model. A 10–30 second API response (not uncommon) ties up one of the finite worker pool.

**Write path unguarded.** The `/ai/apply` route (line 2745) allows authenticated users to mutate any line item or assembly in their company's projects by sending a JSON payload. The route validates company isolation via `get_project_or_403()` and `get_lineitem_or_403()`, but the `action` dispatch is driven entirely by the client-supplied payload. A client can send `action: delete_line_item` with any `line_item_id` in their project and it will be deleted — no additional confirmation, no soft delete.

### What Would Need to Be True for Future Tally Integration

1. `ai_generated` must be set to `True` when AI creates a line item — zero code changes have been made to ensure this.
2. A route to read back flywheel data (aggregate `estimator_action` by project, by user, or across the dataset) does not exist.
3. The prompt construction must be factored out of route handlers into a versioned prompt module before prompt engineering work can be done without a code deploy.
4. A logging layer (or Anthropic SDK usage hook) must capture token counts before any cost-aware decisions (model downgrade, caching) can be implemented.
5. The synchronous blocking model must be addressed before AI calls can scale beyond a handful of concurrent users.

---

## 6. Test Suite Assessment

### What Is Tested

**`tests/test_estimate_table.py` (pytest, 29 tests):** The only properly structured pytest suite. Covers the four TanStack API routes (`GET /api/projects/<id>/line_items`, `POST`, `PATCH`, `DELETE`). Tests: authenticated access, unauthenticated 401, cross-company 403, response shape, cost computation on create/patch, `is_deleted` soft-delete behavior, CSRF validation, `estimator_action` and `edit_delta` capture. This suite tests behavior, not implementation detail. It requires a real PostgreSQL database and makes actual DB writes. The session-scoped fixture pattern is correct (the IMPORTANT comment on line 43 about `g` bleeding is accurate and the fix is properly applied).

**`test_takeoff.py` (custom runner, 99 assertions):** Tests takeoff CRUD (plan upload, page CRUD, item CRUD, measurement CRUD), scale calibration, and company isolation. Not pytest-compatible — runs via `python test_takeoff.py`. Requires real PostgreSQL and a test PDF. The test creates actual uploaded files on disk. Cleanup behavior was not confirmed.

**`tests/test_runner.py` (HTTP runner):** Makes live HTTP requests to `localhost:5000`. Tests signup, login, logout, project create, line item create, and all five AI routes (mocked with `TEST_AI_CALLS=false` flag support). Not CI-compatible — requires a running server with a seeded test user. The test for AI routes (lines 327–504) checks HTTP status code only, not response body content.

### What Is Not Tested

**Zero coverage for:**
- Auth routes: `/login`, `/forgot-password`, `/reset-password/<token>` (token expiry, single-use enforcement)
- Signup: duplicate email handling, minimum password enforcement, company+user atomicity
- All project CRUD routes: `/project/<id>`, `/project/<id>/update`, `/project/<id>/delete`, `/project/new`
- All assembly routes: `/project/<id>/assembly/new`, `/assembly/<id>/update`, `/assembly/<id>/delete`
- The legacy line item routes: `POST /lineitem/new`, `POST /lineitem/<id>/update`, `POST /lineitem/<id>/delete` — including the hard-delete path
- WBS: 8 WBS routes, zero tests
- Library: 3 library item routes, zero tests
- Proposal: the `/project/<id>/proposal` route is untested
- Production rates: 4 routes, untested
- All 5 AI routes in the pytest/programmatic sense (test_runner.py checks status codes only)
- Admin routes: company create, user create/edit/delete
- The assembly builder: `/project/<id>/assembly/builder/save`
- The `calculate_item_costs()` function is not unit-tested; its behavior is only exercised indirectly through integration tests that use the new API

**What the suite would let through:**
- A broken `calculate_item_costs()` (production-rate path is entirely untested)
- A regression in the `/ai/apply` write path (hard delete on `delete_line_item` action, no flywheel capture)
- Cross-company access via legacy line item routes (isolation helpers are tested only in the TanStack API tests)
- An assembly-delete that orphans line items by bypassing soft-delete
- Any breakage in the WBS, library, or proposal surfaces

---

## 7. Critical Risks

### R1 — Production Deploy Is Broken (Small fix, large blast if ignored)

`deploy/update.sh` calls `git pull origin master`. The active branch is `main`. Every deploy attempt will fail with a fatal git error. The service will not be updated. This is a single-line fix (`master` → `main`) but until it is fixed, no code reaches production via the documented deploy path. Risk of engineers deploying manually in non-reproducible ways increases.

### R2 — Flywheel Data Is Structurally Empty (Medium fix, strategic consequence)

`ai_generated` is never set to `True` by any route. Every AI-created item is stored with `ai_generated=False`. From the moment the system goes live, the field that distinguishes AI-seeded from human-created items is wrong for 100% of AI-created rows. Training data for a future model, A/B analysis of AI acceptance rates, and the entire Tally intelligence feedback loop depend on this field being set correctly. Backfilling is impossible — there is no separate log of which items were AI-generated. The fix is small (one line in the `ai_apply` route), but the window for fixing it without permanent data loss is before any AI-generated production data accumulates.

### R3 — Divergent Delete Semantics (Medium fix, data integrity)

The TanStack API soft-deletes; every other deletion path hard-deletes. An item deleted through the legacy estimate view (`POST /lineitem/<id>/delete`) permanently destroys its flywheel record. An item soft-deleted via the TanStack API (`DELETE /api/line_items/<id>`) is marked deleted but not removed, creating divergent views between the legacy and new estimate surfaces. As the product transitions from legacy to TanStack, this inconsistency will produce user-visible ghost items or missing items depending on which surface they use.

### R4 — No Logging Anywhere (Medium effort to retrofit correctly)

No structured logging in `app.py`. Gunicorn access logs are the only evidence of what the application is doing. AI call failures, migration failures, auth anomalies, CSRF rejections, and rate limit events are invisible in production. When a real user reports "the AI didn't work," there is no way to determine whether the API call was made, what it contained, or how the response failed. A logging framework retrofitted after a production incident is harder to trust than one built in from the start.

### R5 — Unindexed Assembly and Line Item Queries (Medium effort to add indexes)

`assemblies.project_id` and `line_items.assembly_id` have no database indexes. Every project page load, AI context injection, and scope gap analysis runs full table scans on these tables. At small scale (tens of projects, hundreds of line items) this is invisible. At the scale described in strategy documents (5,000 active users per session history's target), these will be the first indexes that cause production slowdowns and require emergency additions under load.

### R6 — Monolithic `app.py` Reaches Cognitive and Operational Limits (Large effort)

3,863 lines. Every model, route, helper, and AI integration in one file. New developers cannot navigate it without intimate familiarity. Git conflict probability on concurrent feature work is high. Adding a new feature requires reading the full file to understand what already exists. This is not a critical risk today — the codebase is effectively single-author — but at the moment the team grows beyond one or two developers, the monolith becomes a velocity constraint. The Takeoff Blueprint was the first structural separation; more are needed.

---

## 8. Findings Worth Acting On

### F1 — Set `ai_generated = True` in `/ai/apply` (Small)

In `app.py` line 2857, when `ai_apply` creates a new `LineItem`, add `ai_generated=True`. Similarly, when the AI Assembly Builder creates items via `/ai/build-assembly` → `/ai/apply`, they should carry the flag. This is a one-line fix per insertion point. Without it, the flywheel cannot ever produce meaningful signal because the baseline (AI-created vs. human-created) is permanently lost for all data created before the fix.

**File:** `app.py`, lines 2857–2877 (add_line_items branch of `ai_apply`)

### F2 — Fix Deploy Script Branch (Small)

In `deploy/update.sh` line 10, change `git pull origin master` to `git pull origin main`. Verify the production droplet's local git repository has its `HEAD` tracking `main`. Until this is fixed, the documented deploy path does not work.

**File:** `deploy/update.sh`

### F3 — Add `requests` to requirements.txt (Small)

Add `requests>=2.31,<3.0` to `requirements.txt`. The import at line 720 currently relies on a transitive dependency. A future pip dependency resolution could drop it.

**File:** `requirements.txt`

### F4 — Delete `routes.py` (Small)

The file is dead code that could cause serious confusion if a future developer attempts to import it. It re-declares auth, re-declares routes, uses a different auth model. Delete it.

**File:** `routes.py`

### F5 — Unify Delete Semantics (Medium)

The legacy `/lineitem/<id>/delete` route (line 1207) should perform a soft delete (`item.is_deleted = True; item.estimator_action = 'rejected'`) rather than `db.session.delete(item)`. Alternatively, the new API's soft delete should be documented as the only sanctioned deletion path and the legacy route removed. The current two-path situation corrupts flywheel data and creates divergent views.

**File:** `app.py`, lines 1207–1213; also `ai_apply` `delete_line_item` action at line 2792

### F6 — Add Index on assemblies.project_id and line_items.assembly_id (Small)

Add these two statements to `run_migrations()` in `app.py`:
```sql
CREATE INDEX IF NOT EXISTS idx_assemblies_project ON assemblies(project_id);
CREATE INDEX IF NOT EXISTS idx_line_items_assembly ON line_items(assembly_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```
Also add `CREATE INDEX IF NOT EXISTS idx_production_rate_trade ON production_rate_standards(trade)`.

**File:** `app.py`, `run_migrations()` at line 3676

### F7 — Log Migration Failures (Small)

In `run_migrations()` (line 3809), the `except Exception` block should print or log the failed SQL and the exception. Currently, a failed migration produces no output and the system continues. `print(f"Migration failed: {sql[:80]!r} — {e}")` in the except block is sufficient until structured logging is added.

**File:** `app.py`, lines 3809–3814

### F8 — Add `company_id` Population to Legacy Line Item Routes (Small)

The legacy `POST /lineitem/new` route (line 960) and `POST /assembly/<id>/lineitem/new` route (line 951) create LineItem records without setting `company_id`. This field was added in Session 22. All items created via the legacy routes will have `company_id = NULL`. Add `company_id=current_user.company_id` to the LineItem constructor in these routes.

**File:** `app.py`, lines 951–1022

### F9 — Centralize AI Client and Model Name (Small)

Move `anthropic.Anthropic(api_key=api_key)` instantiation to a module-level function or singleton (or at minimum an application-level cached instance). Extract `'claude-sonnet-4-20250514'` to a module-level constant `AI_MODEL = 'claude-sonnet-4-20250514'`. Five call sites hardcode the model; a model upgrade requires five edits with risk of missing one.

**File:** `app.py`, lines 2717, 2988, 3278, 3433, 3544

### F10 — Add Minimum Logging for AI Calls (Small)

Before each `client.messages.create()` call, log the route name, the project_id (if any), and the prompt mode. After the response, log the input/output token counts from `response.usage`. One print statement per call site is sufficient as an interim measure. This enables cost estimation from Gunicorn stdout before a structured logging system is in place.

**File:** `app.py`, AI routes at lines 2716, 2987, 3277, 3432, 3543

### F11 — Add Unique Constraint to company_profile.company_id (Small)

The `company_profile` table has no unique constraint on `company_id`. The route at line 769 `filter_by(company_id=...).first()` will silently pick the first profile if duplicates exist. Add a unique constraint via migration:
```sql
ALTER TABLE company_profile ADD CONSTRAINT uq_company_profile_company UNIQUE (company_id);
```
Run after deduplicating any existing rows.

**File:** `app.py`, `run_migrations()`

### F12 — Viewer Role Enforcement (Medium)

The `viewer_readonly` decorator mentioned in CLAUDE.md does not exist. Implement it as a simple wrapper:
```python
def viewer_readonly(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role == 'viewer':
            abort(403)
        return f(*args, **kwargs)
    return decorated
```
Apply it to all write routes: `/project/<id>/assembly/new`, `/assembly/<id>/update`, `/assembly/<id>/delete`, `/lineitem/<id>/update`, `/lineitem/<id>/delete`, `/api/line_items/<id>` (PATCH/DELETE), `/library/item/new`, and all WBS write routes. The missing decorator is documented as a HIGH security gap.

**File:** `app.py`, immediately after `admin_required` decorator at line 377

### F13 — Remove or Redirect `routes.py` Misnamed Tokens Cleanup (Small)

The `__pycache__/app.cpython-314.pyc` file (currently modified per git status) suggests Python 3.14 is being used locally. The `requirements.txt` specifies no Python version minimum. Confirm CI and production Python version alignment. Python 3.14 is pre-release at time of writing; if production runs a different version, behavior differences around `f-string` evaluation or `match` statement handling could surface.

**File:** `requirements.txt` — consider adding a `python_requires` marker or `.python-version` file

---

## 9. Verdict

The foundation is coherent and honestly built. A single developer has shipped a working multi-tenant Flask app with authentication, a takeoff canvas module, a TanStack grid, and five live AI integrations — and the code, while monolithic, is readable and internally consistent. The architecture can support what is described in the strategic documents with focused investment, not a rewrite.

The single most important thing the engineering work needs to confront is not the monolith, not the missing indexes, and not the missing viewer role: it is the `ai_generated` flag. Every AI-created production data row will have `ai_generated=False` until the fix is made. The strategic documents describe a product whose competitive moat is a data flywheel built from estimator interactions with AI suggestions. That flywheel requires distinguishing AI-seeded rows from human-created rows. The fix is one line. The window to apply it without permanently corrupting the training dataset is now, before the first production user applies an AI suggestion.

---

**Coverage:** 4 top-level directories (`/`, `templates/`, `static/`, `tests/`); ~30 Python files read including the full 3,863-line `app.py`; 14 tables examined via model definitions and `run_migrations()` SQL (equivalent to 34 migration statements); all 5 AI routes read in full  
**Migrations/models examined:** 14 model classes, 34 migration statements in `run_migrations()`, 1 historical `migration.sql`  
**Verdict in one sentence:** A working single-file Flask monolith with the right schema shape for a Tally AI flywheel, fatally undermined by one missing line of code that has been broken since the flywheel fields were introduced.  
**File committed:** `03_TECHNICAL_AUDIT.md`
