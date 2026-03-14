# Session 7 Handoff — Authentication & Multi-Tenancy
**Date:** 2026-03-11
**Status:** Code complete, untested end-to-end

---

## What Was Accomplished

### Core deliverable: Full auth + multi-tenant isolation layer

**New files created:**
- `migration.sql` — idempotent SQL to run in pgAdmin once before first auth startup
- `Templates/nav.html` — Jinja2 include partial with nav bar CSS + HTML; used via `{% include 'nav.html' %}` in all templates
- `Templates/login.html` — login page at `/login` (standalone, no auth required)
- `Templates/admin.html` — admin panel at `/admin`; create/delete companies and users
- `Templates/profile.html` — password change at `/profile`

**Files modified:**
- `app.py` — complete rewrite incorporating all auth + isolation logic (see breakdown below)
- All 9 existing templates — `{% include 'nav.html' %}` injected at top of each page body

### app.py changes in detail

1. **New imports:** `flask_login` (LoginManager, UserMixin, login_user, logout_user, login_required, current_user), `werkzeug.security` (generate_password_hash, check_password_hash), `functools.wraps`
2. **New config:** `SECRET_KEY` from env var with dev fallback
3. **New models:** `Company`, `User(UserMixin)` with `set_password()` / `check_password()` helpers
4. **Modified models:** Added `company_id` FK to `Project`, `LibraryItem`, `GlobalProperty`, `CompanyProfile`
5. **Login manager:** `login_manager.login_view = 'login'`; `@login_manager.user_loader` returning `User.query.get(int(user_id))`
6. **Auth helpers/decorators:**
   - `admin_required(f)` — decorator, aborts 403 if role != 'admin'
   - `get_project_or_403(id)` — fetch + company check
   - `get_assembly_or_403(id)` — fetch + chain through project for company check
   - `get_lineitem_or_403(id)` — fetch + chain through assembly or project
   - `get_library_item_or_403(id)` — fetch + direct company_id check
7. **New routes:** `/login`, `/logout`, `/admin`, `/admin/company/new`, `/admin/user/new`, `/admin/user/<id>/delete`, `/admin/user/<id>/edit`, `/profile`
8. **All existing routes:** `@login_required` added; project/assembly/lineitem routes replaced `get_or_404()` with `get_*_or_403()`; all query filters updated to scope by `current_user.company_id`
9. **`_seed_company_properties(company_id)`** — seeds default trades/types/sectors for new company; called inside `/admin/company/new` route before commit
10. **`run_migrations()`** — extended with 4 new `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements for company_id on projects/library_items/global_properties/company_profile
11. **`seed_global_properties()`** — removed (replaced by `_seed_company_properties`; old function was global, new one is per-company)

---

## Current State of the Codebase

### What's working (code complete, untested):
- Full Flask-Login authentication with session persistence
- Login page → redirect to originally requested URL after auth
- All routes return 401/redirect to `/login` if unauthenticated
- All project/assembly/lineitem/library routes return 403 for cross-company access
- `/admin` creates companies (with seeded default properties) and users
- `/profile` allows password change with current-password confirmation
- Nav bar appears on all pages showing company name, username, role-gated admin link, logout
- Templates and library items are company-scoped
- GlobalProperties and CompanyProfile are company-scoped

### What has NOT been tested:
- Full end-to-end live server run with the new auth code
- Bootstrap flow (first company + admin user creation)
- All 403 cross-company scenarios
- Session persistence across browser refresh
- Flash message display on login failure
- `_seed_company_properties` called on company creation

### Known working (unchanged from Session 6):
- All cost calculation logic (calculate_item_costs, recalcItem in JS)
- Assembly Builder (measurements, formula-driven quantities)
- Estimate views (all grouping modes)
- CSV export, CSI report, bid proposal
- Ollama AI suggestions
- Library CRUD, template clone/load

---

## Exact Next Steps

### Step 1 — First-time deployment setup (DO THIS BEFORE ANYTHING ELSE)
```bash
pip install flask-login
```

Run `migration.sql` in pgAdmin (creates `companies`, `users` tables; adds `company_id` columns to existing tables).

### Step 2 — Bootstrap the first admin account
Since there's no self-serve admin creation, use Python shell:
```python
# Run once from project directory
from app import app, db, Company, User
with app.app_context():
    co = Company(company_name="Your Company Name")
    db.session.add(co)
    db.session.flush()
    u = User(company_id=co.id, username="admin", email="you@example.com", role="admin")
    u.set_password("choose-a-strong-password")
    db.session.add(u)
    db.session.commit()
    print(f"Created company id={co.id}, user id={u.id}")
```

### Step 3 — Assign existing data to the new company
Run in pgAdmin (replace `1` with your actual company id if different):
```sql
UPDATE projects          SET company_id = 1 WHERE company_id IS NULL;
UPDATE library_items     SET company_id = 1 WHERE company_id IS NULL;
UPDATE global_properties SET company_id = 1 WHERE company_id IS NULL;
UPDATE company_profile   SET company_id = 1 WHERE company_id IS NULL;
```

### Step 4 — Start and smoke test
```bash
python app.py
```
- Navigate to `http://localhost:5000` — should redirect to `/login`
- Log in with admin credentials
- Verify nav bar shows company name + username
- Verify all existing projects visible
- Verify `/admin` accessible, create a second test company + user
- Log in as second company user — verify they see ZERO projects
- Try navigating to `/project/1` while logged in as second company → should get 403

### Step 5 — Production deployment prep (before giving to beta companies)
- Set `SECRET_KEY` as an environment variable (not the dev default)
- Change DB password from `Builder`
- Put behind HTTPS (nginx reverse proxy recommended)
- Consider setting `SESSION_COOKIE_SECURE = True` and `SESSION_COOKIE_HTTPONLY = True`
- Consider adding viewer role enforcement (currently viewer can write — see Known Issues)

### Step 6 — Future features to consider
- Viewer role enforcement (read-only — would need to check role in write routes)
- User self-service: invite link, forgot password email
- Per-company settings: markup/overhead defaults, custom CSI views
- Audit log: who created/edited which estimate

---

## Important Decisions & Context

### Why Flask-Login (not JWT/custom sessions)
Flask-Login is the idiomatic Flask auth solution. It integrates directly with Flask's session (cookie-based), `current_user` is auto-available in templates, and it handles the redirect-after-login pattern cleanly. For a multi-user web app (not an API), session cookies are simpler and more appropriate than JWT.

### Why company_id on LibraryItem and GlobalProperty (not just Project)
True tenant isolation requires that Company A cannot see Company B's labor rates or custom trades/sectors. LibraryItems contain sensitive pricing data. GlobalProperties define the vocabulary (trade names, project types) that may vary by company. Scoping both to company_id was the only correct choice for a real SaaS deployment.

### Why templates (is_template=True assemblies) are filtered through Project JOIN, not directly
Templates don't have their own `company_id` — they're just assemblies with `is_template=True` that belong to a project. Rather than add a new column, the filter goes through the project's `company_id`. This keeps the data model clean and means templates are automatically company-scoped as a side effect of project scoping.

### Why no self-serve admin creation UI
Chicken-and-egg: to access `/admin` you need to be logged in as admin. To be admin you need to be in the DB. The bootstrap step (Python shell insert) is a one-time operation. Adding a "create first admin" page would require a security exception (allow unauthenticated access to a write endpoint) which is a meaningful attack surface. For a beta with known operators, the shell approach is the right tradeoff.

### Why `_seed_company_properties` instead of the old `seed_global_properties`
The old function seeded global (NULL company_id) properties at app startup. In a multi-tenant world, each company needs their own property set. Moving seeding to company-creation time (inside `/admin/company/new`) means new companies get sensible defaults without any manual action, and seeding is scoped to that company's `company_id` from the start.

### Why production_rate_standards has no company_id
Production rates are reference/benchmark data (industry standards, not proprietary). They're shared across all companies as a read-only reference. Each company can have their own actual labor rates in their LibraryItems. Keeping production rates global avoids duplicating ~20 seed records per company.

---

## Known Issues & Blockers

1. **CRITICAL: Untested end-to-end.** The auth code is logically correct and consistent with Flask-Login patterns, but no live server test was run this session. The bootstrap sequence (Step 1-3 above) MUST be completed before testing.

2. **Bootstrap chicken-and-egg.** No UI for first admin creation. Must use Python shell. Document this clearly for anyone deploying.

3. **NULL company_id on existing data.** All data created before auth was added will have `company_id = NULL`. The UPDATE statements in Step 3 MUST be run or existing projects will be invisible to all users (the `filter_by(company_id=...)` queries will not match NULLs).

4. **Viewer role not enforced on write routes.** Currently, `role='viewer'` is only blocked from `/admin`. A viewer can still call any POST endpoint (create project, edit line item, etc.). If viewer is intended to be read-only, every write route needs `if current_user.role == 'viewer': abort(403)` added, or a `viewer_forbidden` decorator.

5. **SECRET_KEY is a dev placeholder.** The current default `'dev-change-this-in-production-please'` is in the source code. Anyone with the code can forge sessions. Must set `SECRET_KEY` env var before any hosted deployment.

6. **`equipment_hours` field exists on LineItem but is always 0.** Deprecated by the item_type logic added in Session 6. Not broken, just dead weight. Low priority to remove.

7. **`seed_global_properties()` function removed.** The old function that seeded global (NULL company_id) properties on startup no longer exists. Any code path that relied on it (shouldn't be any) will silently get empty property lists until a company creates its own.

8. **Nav bar on print layouts** — `proposal.html` and `csi_report.html` have print-specific CSS (`@media print`). The nav bar include adds screen-only UI. Verify the nav bar doesn't appear on printed output (it should be fine since print styles typically hide nav elements, but needs a visual check).
