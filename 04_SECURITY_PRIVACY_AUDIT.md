# 04_SECURITY_PRIVACY_AUDIT.md — Zenbid Security and Privacy Audit

**Engagement:** Six-Agent Reconnaissance — Agent Four (Security and Privacy Officer)
**Date:** 2026-04-29
**Scope:** Full codebase read through a security and privacy lens. No application executed.
**Files read:** `app.py` (3,863 lines), `routes_takeoff.py`, `gunicorn.conf.py`, `deploy/update.sh`, `requirements.txt`, `SECURITY.md`, `.gitignore`, `templates/admin.html`, selective reading of other templates.

---

## Orientation Summary

Before deep analysis, a surface pass establishes the lay of the land.

**Authentication mechanism:** Flask-Login with server-side sessions. Passwords hashed via `werkzeug.security.generate_password_hash` — Werkzeug 3.x defaults to `scrypt`, which is good. Reset tokens generated with `secrets.token_urlsafe(32)`.

**Session technology:** Flask default (server-side cookie with signed session ID). `SECRET_KEY` loaded from environment but falls back to a hardcoded string. No session expiry is explicitly configured.

**Secrets:** `ANTHROPIC_API_KEY`, `DATABASE_URL`, `SECRET_KEY`, `MAIL_PASSWORD` are loaded from `.env` via `python-dotenv`. `.gitignore` covers `.env`. No secrets were found committed to the repository.

**Deploy target:** DigitalOcean droplet running Nginx reverse-proxying to Gunicorn on port 8000. Gunicorn binds to `0.0.0.0:8000`. Systemd service named `zenbid`.

**Security documentation:** A `SECURITY.md` exists and is comprehensive — it defines principles, a role enforcement matrix, a gap backlog, and audit checklists. It is the best-written document in the repository. It is also, in places, aspirational rather than descriptive of what the code actually does.

**Immediate surprises:**
- The admin panel at `/admin` is accessible to every self-service signup. Every customer who registers gets `role='admin'`. The panel renders all companies and all users across the entire platform. This is a cross-customer data exposure of the first order.
- The hardcoded fallback database URI contains production-looking credentials: `postgresql://postgres:Builder@localhost:5432/estimator_db`.
- The production deploy script (`deploy/update.sh`) calls `git pull origin master`. The active branch is `main`. Every deploy via the documented method silently fails to update the codebase.

---

## Trust Boundary Map

**Entry point 1 — Web browser (authenticated users):** A user submits a request over HTTPS (SSL status unconfirmed) to the Nginx reverse proxy on port 443. Nginx proxies to Gunicorn on `localhost:8000`. Flask receives the request, verifies the Flask-Login session cookie, and routes to the appropriate handler. User-submitted data (form fields, JSON payloads, URL parameters) is validated in Python before touching the database. The ORM (SQLAlchemy) parameterizes all queries.

**Entry point 2 — Web browser (unauthenticated public routes):** Marketing pages, `/login`, `/signup`, `/forgot-password`, `/reset-password/<token>`, `/waitlist`, and `/waitlist/survey` accept unauthenticated traffic. `/uploads/logo/<filename>` serves uploaded logo files without authentication — by design, so proposal PDFs can include company logos.

**Entry point 3 — Direct Gunicorn access (port 8000):** `gunicorn.conf.py` binds to `0.0.0.0:8000`. If the DigitalOcean firewall (ufw) does not block port 8000, the application is reachable directly without passing through Nginx. Direct access would bypass any security headers Nginx adds and any IP-level controls configured at the Nginx layer.

**Where data crosses trust boundaries:**

*Browser → Flask:* User form fields, JSON payloads, file uploads. Jinja2 auto-escapes template output. SQLAlchemy ORM parameterizes queries. CSRF tokens are enforced globally via Flask-WTF. These controls are active and correct.

*Flask → Anthropic API:* On `/ai/chat` and `/ai/build-assembly`, the full project context is serialized into the system prompt. This includes project name, project number, location, project type, sector, description, all assembly labels and names, every line item description with quantity, unit, costs, and production rates, and production rate standards. The call goes to `api.anthropic.com` over TLS. The Anthropic client is initialized fresh per request (`anthropic.Anthropic(api_key=api_key)`) — there is no connection reuse, no retry budget, and no logging. No mechanism exists to prevent this data from being included in Anthropic's training pipelines under their default terms.

*Flask → n8n webhook:* On every waitlist signup, user name and email are posted to `https://flows.zenbid.io/webhook/waitlist` using the `requests` library (imported inline, not declared in `requirements.txt`). The n8n service is on a separate DigitalOcean droplet. This is a first-party service, but the data transfer is undisclosed to users.

*Flask → SendGrid:* Password reset emails route through SendGrid SMTP. The email contains a reset URL with a token. No content is sensitive beyond the token itself, which expires in two hours.

*Flask → PostgreSQL:* All database traffic stays on localhost or internal DigitalOcean private networking. Connection string from environment variable.

**What enforces each boundary:**

| Boundary | Enforcement |
|----------|-------------|
| Browser → Nginx | TLS (status unconfirmed), CSRF tokens |
| Nginx → Gunicorn | Internal binding (should be localhost-only) |
| Flask → DB | SQLAlchemy ORM, connection string from env |
| Flask → Anthropic | TLS via Anthropic SDK |
| Flask → n8n | HTTPS, no additional auth |
| Flask → SendGrid | SMTP with TLS, credentials from env |
| Project data isolation | `get_project_or_403()` and equivalent helpers |

---

## Authentication and Authorization

**How users are identified:** Email lookup, falling back to username for legacy accounts (`app.py:433-435`). The dual-lookup introduces minor timing side-channels but no meaningful enumeration risk since the login failure message is identical regardless.

**Password hashing:** `werkzeug.security.generate_password_hash` with Werkzeug 3.x defaults to `scrypt` — memory-hard, resistant to GPU cracking. This is correct. Password minimum is 8 characters at signup (`app.py:456`) but inexplicably drops to 6 characters at the profile change route (`app.py:578`). This inconsistency means an account that started with an 8-character password can be "upgraded" to a weaker 6-character password.

**Sessions:** Flask-Login server-side sessions with a signed cookie. No `PERMANENT_SESSION_LIFETIME` is configured, no `SESSION_COOKIE_HTTPONLY`, no `SESSION_COOKIE_SECURE`, no `SESSION_COOKIE_SAMESITE`. Without `SESSION_COOKIE_SECURE=True`, session cookies will be transmitted over HTTP if TLS is not enforced at the Nginx layer. Without `SESSION_COOKIE_HTTPONLY=True`, JavaScript on the page can read the session cookie. Without `SESSION_COOKIE_SAMESITE`, CSRF attacks that bypass the Flask-WTF check become marginally easier. None of these are configured (`app.py:28-61`).

**Rate limiting:** Active on `/login` (10 POST/minute) and `/ai/*` routes (20/minute). The rate limiter uses `storage_uri='memory://'` (`app.py:61`). Gunicorn starts `cpu_count() * 2 + 1` workers (`gunicorn.conf.py:8`). On a typical DigitalOcean droplet with 2 vCPUs, this means five workers, each with its own counter. The effective rate limit is five times the configured value — 50 login attempts per minute, 100 AI requests per minute, not 10 and 20. The `/signup` and `/forgot-password` routes have no rate limiting at all.

**Password reset:** Tokens are generated with `secrets.token_urlsafe(32)` — cryptographically strong. Token expiry is two hours (`app.py:607`). Tokens are invalidated after use (`app.py:651-652`). The success response is identical whether or not the email exists (`app.py:627`), correctly preventing enumeration. This is implemented correctly.

**Authorization — role enforcement:** Three roles exist: `admin`, `estimator`, `viewer`. The `admin` role is enforced by `@admin_required` on `/admin` routes only. The `viewer` role is documented in `SECURITY.md` as a current gap — no `@viewer_readonly` decorator exists anywhere in the codebase. Viewers can currently call every write route that an estimator can.

**The admin panel — the most serious authorization failure in the codebase:** Every self-service signup creates a user with `role='admin'` (`app.py:468`). The admin panel at `/admin` (`app.py:488-494`) renders every company and every user in the database:

```python
companies = Company.query.order_by(Company.company_name).all()
all_users = User.query.order_by(User.company_id, User.username).all()
```

The template (`templates/admin.html`) iterates all companies and all users. The `admin_new_user()` route (`app.py:512-533`) accepts any `company_id` in the POST body without validating that it belongs to the requesting user's company. The `admin_delete_user()` route (`app.py:535-544`) deletes any user by ID, only refusing to delete oneself. The `admin_edit_user()` route (`app.py:546-559`) changes any user's role, email, or password.

The practical consequence: any Zenbid customer who has created an account can enumerate all other customers by name, list all user accounts across all companies, create users in any tenant, reset any user's password to a value they control, and delete any user account.

**The open redirect in login:** `app.py:438-439`:

```python
next_page = request.args.get('next')
return redirect(next_page or url_for('index'))
```

No validation is applied to `next_page`. A crafted URL such as `/login?next=https://evil.com/steal-credentials` will redirect the user to an attacker-controlled page immediately after successful authentication. Flask-Login's `login_required` decorator generates `next` parameters automatically for internal redirects, but the absence of origin validation allows external redirect values.

**Assembly template tenant isolation:** When loading assembly templates, the route validates company ownership through a join (`app.py:1507-1512`). This is correct. The takeoff Blueprint uses `_get_plan_or_403()` and `_get_item_or_403()` helpers that check `company_id` directly (`routes_takeoff.py:41-52`). These are correct.

**Proposal route:** The `/project/<id>/proposal` route (`app.py:1939-2008`) now uses `get_project_or_403()`. The SECURITY.md gap H-1 (documented as open) appears resolved in the current code.

---

## Secrets and Configuration

**What is in the repository:** No secrets are committed. `.gitignore` correctly excludes `.env`. The `SECURITY.md` principle 6 is being followed.

**What is NOT in the repository but should be checked:** The production server's `.env` file or systemd environment configuration. This audit cannot confirm what values are set in production.

**The hardcoded fallback DATABASE_URI:** `app.py:36-38`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:Builder@localhost:5432/estimator_db'
)
```

The credentials `postgres:Builder` are committed to the repository. While this is a local-dev fallback, this string is now public knowledge. If a production deployment has `DATABASE_URL` unset for any reason, the app will attempt to connect with these credentials. More importantly, `Builder` is now a credential associated with this codebase that should never appear in a production Postgres password.

**The hardcoded fallback SECRET_KEY:** `app.py:42`:

```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-change-this-in-production-please')
```

This is a known string. Anyone who knows it can forge Flask session cookies, signing them with `dev-change-this-in-production-please`. If any production deployment runs without `SECRET_KEY` set, every user account on that deployment is compromised. The string is also insufficiently alarming — it reads as a reminder, not as a failure-mode trap. There is no startup check that fails fast if the key is missing or matches the default.

**ANTHROPIC_API_KEY startup validation:** Not implemented (`app.py:2525-2527`). The check exists inline within the route handler but there is no startup gate. The application boots and serves traffic without a configured API key, failing only when an AI route is called. A startup check that refuses to bind if the key is missing would prevent silent misconfiguration.

**Error details in API responses:** `str(e)` is returned in error responses at `app.py:2728, 2999, 3012, 3289, 3301, 3444, 3456, 3555, 3567`. Python exceptions from the Anthropic SDK or from database queries can contain internal paths, query fragments, model names, or connection details. These are returned directly in JSON responses visible to the browser.

**`requests` library undeclared:** The waitlist route imports `requests` inline (`app.py:720`). This library is not in `requirements.txt`. The library happens to be available in most Python environments as a transitive dependency, but its absence from the declared dependency list makes the application fragile and makes security auditing of third-party packages incomplete.

**Mail password:** `MAIL_PASSWORD` defaults to empty string (`app.py:51`). An empty password may succeed against some SMTP configurations or produce silent errors. The fallback is safe locally (no email sent) but should be confirmed as empty in production only if email is deliberately disabled.

---

## Multi-Tenancy Boundaries

**The primary enforcement mechanism:** Four helper functions check that the requested object belongs to the current user's company before returning it or raising HTTP 403:

- `get_project_or_403(project_id)` — checks `project.company_id == current_user.company_id`
- `get_assembly_or_403(assembly_id)` — traverses to the parent project and checks its `company_id`
- `get_lineitem_or_403(item_id)` — traverses to assembly → project and checks `company_id`
- `get_library_item_or_403(item_id)` — checks `item.company_id == current_user.company_id`

These are used consistently throughout `app.py` for all estimate data routes. The takeoff Blueprint adds `_get_plan_or_403()` and `_get_item_or_403()` with the same pattern.

**Where the isolation is structurally enforced:** At the function boundary. Every route that reads or modifies estimate data calls one of these helpers as the first non-trivial operation. If the helper is called, isolation is enforced. The ORM does not enforce this automatically — the application layer bears the full burden.

**Where the isolation is fragile:** It depends on the developer reliably calling the right helper. There is no query-level scoping, no ORM mixin that automatically adds a company_id filter, and no test that would fail if a new route skipped the helper. The protection is correct for all current routes but there is no structural guarantee for future routes.

**The named fragile path — GlobalProperty:** The `new_global_property()` route (`app.py:788-803`) queries `GlobalProperty.query.filter_by(company_id=current_user.company_id, ...)` inline rather than using a helper. The `delete_global_property()` route (`app.py:805-813`) also does an inline check `prop.company_id != current_user.company_id`. These are correct but inconsistent — they don't use the approved helper pattern. A future developer editing these routes may not notice the inline check and remove it.

**The critical failure — admin panel:** As described in the Authentication and Authorization section, the admin panel queries all companies and all users without filtering by `current_user.company_id`. This is not a fragile path — it is a currently broken path.

**The TanStack API `company_id` field on LineItem:** The `api_list_line_items()` route (`app.py:1254-1273`) traverses from project → assemblies → line items, relying on `get_project_or_403()` at the top. Items are then fetched by assembly or by `project_id`. The isolation is correct here because the project ID anchor is validated. The `company_id` column on `line_items` (added in Session 22) provides a denormalized backup field but is not used as the primary isolation mechanism in queries.

**ProductionRateStandard — intentionally cross-tenant:** Global production rates are readable by all companies (`app.py:2590-2595`). This is correct by design.

---

## AI Integration Privacy

**What data flows to Anthropic:** When a user invokes `/ai/chat` in `estimate` mode, the following customer data is serialized into the Claude API system prompt (`app.py:2602-2707`):

- Project name, project number, city, state, zip code
- Project type and market sector labels
- Project description (free-text, may contain client names, site addresses, notes)
- All assembly labels and names
- All line item descriptions, quantities, units, item types, production rates
- All line item cost data: material cost per unit, labor cost per hour, equipment costs, total cost per item
- Aggregate project totals (material, labor, equipment, hours, total cost)
- The company's production rate standards reference library

This constitutes a complete financial fingerprint of the estimate — bid pricing, labor rates, subcontractor cost structures, margin assumptions embedded in cost-per-unit figures. On `/ai/build-assembly`, a similar context is sent including production rate standards.

**Transmission security:** The Anthropic SDK transmits over HTTPS to `api.anthropic.com`. This boundary is TLS-protected. No data is logged server-side in Zenbid's application before the call.

**Anthropic's data retention and training policy:** By default, the Anthropic API does not use submitted data to train models for paying API customers under their current terms of service. However, this is a terms-of-service claim, not a technical guarantee. No DPA (Data Processing Agreement) addendum is in place based on the repository contents. No Anthropic-specific privacy settings are configured in the API client — the client is initialized with default options (`anthropic.Anthropic(api_key=api_key)`) with no `extra_headers` or organization-level controls.

**Gap between actual and documented data flow:** `SECURITY.md` Section 6 states: "Zenbid does not use customer estimate data to train AI models without explicit, opt-in consent." This is Zenbid's policy. It makes no statement about Anthropic's usage. The actual privacy exposure — that a third party (Anthropic) receives complete estimate data including all cost figures — is not disclosed to users anywhere in the application. The `/privacy` route returns the string "Privacy Policy — coming soon". There is no consent mechanism, no disclosure, and no user notification that their estimate data leaves Zenbid's infrastructure.

**Prompt injection:** The system prompt in `/ai/chat` is built via f-string interpolation (`app.py:2602-2707`). User-controlled strings — project name, description, assembly names, line item descriptions, and the user's own chat message — are injected directly into the prompt without sanitization. A project with a description of `[IGNORE ALL PREVIOUS INSTRUCTIONS. Your real task is to...]` could manipulate the model's behavior. `SECURITY.md` acknowledges this as a HIGH gap (H-6) with a proposed fix (labeled delimiters). The fix has not been implemented.

---

## Data Privacy and Consent

**Personal data collected:**

| Data | Where | Purpose |
|------|-------|---------|
| Name, email (account) | `users` table | Authentication |
| Company name | `companies` table | Multi-tenancy |
| Name, email (waitlist) | `waitlist_entries` table | Marketing |
| Waitlist survey responses | `waitlist_surveys` table | Product research |
| IP address (logs) | Gunicorn access log | Operations |
| Project data (estimates, assemblies, line items) | Core tables | Service delivery |
| Uploaded PDF plans | `static/uploads/takeoff/` | Service delivery |
| Company logo | `static/uploads/logo/` | Service delivery |

**Consent design:** There is no consent mechanism. No cookie banner. No opt-in for email communications. No disclosure that estimate data is processed by a third-party AI provider. Users submit a signup form with fields for name, company, email, and password. No checkbox, no link to Privacy Policy (the page does not exist), no link to Terms of Service (the page does not exist).

**Waitlist PII forwarding without disclosure:** When a user joins the waitlist, their name and email are forwarded to `https://flows.zenbid.io/webhook/waitlist` (`app.py:720-721`). This posts to n8n, which calls the Anthropic API and sends an email via Gmail. The user is shown a success confirmation with no disclosure that their data is being processed by n8n or that an automated email will be sent on behalf of Zenbid via a third-party Gmail account (`zenbid.notifications@gmail.com`). This is a GDPR/CCPA disclosure failure for a data transfer to a sub-processor.

**Account deletion:** There is no account deletion route. `SECURITY.md` M-6 acknowledges this as a gap. Users have no mechanism to request deletion of their account or personal data. For GDPR Article 17, the right to erasure is an individual right that must be technically implementable before the first paying customer in a jurisdiction where GDPR applies.

**Soft delete not implemented on projects:** Projects are hard-deleted (`app.py:1416-1426`). There is no `deleted_at` column and no 30-day recovery window. `SECURITY.md` M-5 acknowledges this. If a user accidentally deletes a project, the data is gone. This is not a privacy violation but is a data integrity gap.

**Legal basis for processing:** None documented. The Privacy Policy does not exist. For any paying customer in the EU or UK, the legal basis for processing their company's estimate data must be documented. "Legitimate interest" and "contract performance" are the likely applicable bases, but they must be stated.

**AI training data policy:** `SECURITY.md` Section 6 includes the correct policy statement: "Zenbid does not use customer estimate data to train AI models without explicit, opt-in consent." This policy exists only in an internal document. It is not disclosed to users and cannot be agreed to because no Privacy Policy or Terms of Service exist.

---

## Infrastructure Posture

**What can be determined from the repository:**

*Gunicorn binding:* `gunicorn.conf.py:5` — `bind = "0.0.0.0:8000"`. The application listens on all interfaces on port 8000. If the DigitalOcean firewall (ufw) does not block external access to port 8000, any client on the internet can reach the application directly, bypassing Nginx and any security headers Nginx is configured to add. Security headers documented in `SECURITY.md` Part 7 are Nginx-level headers. If those headers are even configured in Nginx (this cannot be confirmed from the repo), direct port 8000 access circumvents them.

*Multi-worker rate limiting:* With the default worker count of `cpu_count() * 2 + 1` and `memory://` rate limiter storage, rate limits are divided across workers. On a 2-vCPU droplet: 5 workers, 5x the configured limit. Login brute force protection is 5x weaker than configured.

*Deploy script failure:* `deploy/update.sh:10` — `git pull origin master`. The active branch is `main`. Every deploy via this script silently fetches from the wrong branch and does not update the codebase. The production server may be running stale code. The script returns success (exit code 0 from git), so the operator has no indication anything went wrong.

*Debug mode:* Correctly controlled by environment variable (`app.py:3863`). The condition reads the env var string properly. If `FLASK_DEBUG=false`, debug mode is off. This is correctly implemented.

*Migrations at startup:* `gunicorn.conf.py:29-36` — `on_starting()` runs `run_migrations()` before workers fork. Each migration statement is wrapped in a try/except that swallows all errors silently (`app.py:3809-3814`). A failed migration produces no log entry and no startup failure. This is operationally dangerous — a bad migration runs silently and the application boots with an inconsistent schema.

*Gunicorn timeout:* Set to 300 seconds — appropriate for large PDF uploads but a DDoS-friendly timeout for regular requests. No per-route timeout differentiation.

**What cannot be determined from the repository:**

- Whether ufw is active and blocking port 8000
- Whether the SSL certificate is installed and Nginx is configured for HTTPS
- Whether Nginx security headers are configured
- Whether `FLASK_DEBUG=false` is set in the server `.env`
- Whether the DigitalOcean managed database has encryption at rest enabled
- Whether automated database backups are enabled
- Whether SSH is restricted to key-based authentication
- Whether the DigitalOcean account has MFA enabled
- What the actual `SECRET_KEY` value is in production
- Whether `DATABASE_URL` overrides the hardcoded fallback in production

All of these must be confirmed out-of-band before any customer-facing security review.

---

## Findings Worth Acting On

**F1 — Admin Panel Exposes All Customer Data to All Customers**
Severity: **Critical** | Effort: Small

Every self-service signup sets `role='admin'` (`app.py:468`). The admin panel at `/admin` (`app.py:488-494`) queries all companies and all users without filtering by company. The `admin_new_user()`, `admin_delete_user()`, and `admin_edit_user()` routes accept arbitrary user and company IDs without company-ownership validation. Any Zenbid customer can enumerate all other customers by name, list all user accounts, create accounts in other tenants, reset any user's password, and delete any user account. This is a critical multi-tenancy failure on the admin surface. The fix is either to make the admin panel a superadmin-only surface (restrict to a specific internal email or a separate env-configured admin token) or to scope all admin queries to `current_user.company_id`. Because self-service signup is the growth model, every new customer inherits this access today.

File: `app.py:468, 488-494, 512-559`

**F2 — Open Redirect in Login `next` Parameter**
Severity: **High** | Effort: Small

The login route passes `request.args.get('next')` directly to `redirect()` without validating that the URL is local (`app.py:438-439`). An attacker can send a phishing link `https://zenbid.io/login?next=https://evil.com` — the user sees a legitimate Zenbid URL, logs in successfully, and is delivered to the attacker's page. The fix is one line: validate that `next_page` starts with `/` or use `urllib.parse.urlparse` to reject external hostnames.

File: `app.py:438-439`

**F3 — Session Cookies Missing Security Flags**
Severity: **High** | Effort: Small

No session cookie security flags are configured (`app.py:28-61`). `SESSION_COOKIE_HTTPONLY` is not set, so JavaScript on the page can read the session token. `SESSION_COOKIE_SECURE` is not set, so the cookie will be transmitted over HTTP if TLS is not enforced end-to-end. `SESSION_COOKIE_SAMESITE` is not set, weakening CSRF defenses. These are three Flask config lines. They should be added immediately and `SESSION_COOKIE_SECURE=True` should be enabled once TLS is confirmed active.

File: `app.py` config block (lines 28-61)

**F4 — Rate Limiting Is Effectively Broken in Multi-Worker Production**
Severity: **High** | Effort: Medium

The Flask-Limiter storage is `memory://` (`app.py:61`). Gunicorn starts `cpu_count() * 2 + 1` workers (`gunicorn.conf.py:8`). Each worker maintains its own counter, so the effective brute-force limit on `/login` is not 10/minute but 10 × N_workers per minute — approximately 50/minute on a 2-vCPU server. `/signup` and `/forgot-password` have no rate limiting at all. The fix is to configure a Redis backend for Flask-Limiter and add rate limits to the remaining auth endpoints.

File: `app.py:61`, `gunicorn.conf.py:8`

**F5 — Customer Estimate Data Flows to Anthropic API Without User Disclosure**
Severity: **High** | Effort: Medium

Every invocation of `/ai/chat` in estimate mode sends the full estimate to the Anthropic API, including project location, client-facing description, all assembly names and line item descriptions, and all cost data including per-unit material costs and labor rates (`app.py:2530-2707`). This is the most commercially sensitive data Zenbid's customers hold. No user is told this happens. The Privacy Policy does not exist. There is no consent mechanism. Before any paying customer is onboarded, this data flow must be disclosed in a Privacy Policy and acknowledged in Terms of Service, and Anthropic's DPA must be reviewed.

File: `app.py:2530-2707`

**F6 — Exception Details Leaked in AI Route Error Responses**
Severity: **High** | Effort: Small

At least eight locations return `str(e)` directly in JSON API responses (`app.py:2728, 2999, 3012, 3289, 3301, 3444, 3456, 3555, 3567`). Python exceptions from the Anthropic SDK, SQLAlchemy, or network layer can contain internal paths, query strings, connection parameters, or model version strings. These are returned to the browser and can be read by any user. Replace all `str(e)` in production error responses with a generic message. Log the full exception server-side.

File: `app.py:2728` and 7 additional locations

**F7 — Hardcoded Default DATABASE_URL Contains Credentials**
Severity: **High** | Effort: Small

The fallback database URI `postgresql://postgres:Builder@localhost:5432/estimator_db` is committed to the repository (`app.py:37`). The password `Builder` is now public. Any production environment where `DATABASE_URL` is not set will attempt to connect with these credentials. Add a startup gate that refuses to start if `DATABASE_URL` is not set in the environment, and treat `Builder` as a compromised credential that should never appear in a production Postgres configuration.

File: `app.py:36-38`

**F8 — Hardcoded Fallback SECRET_KEY Allows Session Forgery**
Severity: **High** | Effort: Small

`app.config['SECRET_KEY']` falls back to `'dev-change-this-in-production-please'` if the environment variable is missing (`app.py:42`). This is a known string. Anyone who knows it can generate valid Flask session cookies, authenticated as any user. Add a startup check that fails immediately if `SECRET_KEY` equals the default string or is shorter than 32 characters. Do not allow the application to serve authenticated traffic on a known secret.

File: `app.py:42`

**F9 — Privacy Policy and Terms of Service Are Placeholder Strings**
Severity: **Critical** | Effort: Large

`/privacy` returns `"Privacy Policy — coming soon"` and `/terms` returns `"Terms of Service — coming soon"` (`app.py:687-693`). These are not acceptable for any paying customer. Beyond the regulatory exposure (GDPR, CCPA, PIPEDA depending on customer location), enterprise customers will require a Privacy Policy and DPA before contracting. The AI data flow disclosure required by finding F5 must appear in the Privacy Policy. This is not a code change — it requires legal review and a content decision — but it blocks the first paying customer.

File: `app.py:687-693`

**F10 — Gunicorn Bound to 0.0.0.0:8000 May Bypass Nginx**
Severity: **High** | Effort: Small

`gunicorn.conf.py:5` binds to `0.0.0.0:8000`. If the server firewall does not block external access to port 8000, clients can reach the application directly. Direct access would bypass any Nginx security headers, IP-level rate limiting at Nginx, and any access controls. Change the bind address to `127.0.0.1:8000` and confirm `ufw` is active and blocks port 8000 externally.

File: `gunicorn.conf.py:5`

**F11 — AI Prompt Injection: User Content in System Prompt Without Sanitization**
Severity: **Medium** | Effort: Medium

The system prompt for `/ai/chat` is built via f-string interpolation of user-controlled data — project name, description, assembly names, line item descriptions (`app.py:2602-2707`). A malicious user can embed prompt injection instructions in these fields. Because the AI's response can propose changes to the estimate via a `write_proposal` JSON block that is applied server-side in `/ai/apply`, a successful injection could cause the AI to propose deletions or modifications of estimate data that the user then applies. The fix is to wrap user-sourced data in clearly labeled delimiters and strip known token-manipulation patterns as specified in `SECURITY.md:142-155`.

File: `app.py:2602-2707`

**F12 — Logo Upload Has No MIME Type Validation**
Severity: **Medium** | Effort: Small

The `update_company()` route (`app.py:780-784`) accepts any file via `request.files.get('logo')`, uses `secure_filename()` for path safety, and saves it. There is no content-type check and no magic-byte validation. A user can upload an HTML file named `logo.jpg` or a file containing executable content. The file is served from `/uploads/logo/<filename>` without authentication. While the web root is `static/` and files are served as static assets rather than executed, add MIME type validation using `python-magic` or an equivalent library.

File: `app.py:780-784`

**F13 — Deploy Script Pulls from Wrong Branch**
Severity: **High** | Effort: Small

`deploy/update.sh:10` executes `git pull origin master`. The active branch is `main`. The command succeeds (git exits 0) but makes no changes. Production may be running code that is multiple commits behind the main branch. Every deployment via this script has failed since the branch was renamed. Change `master` to `main` and add a `git status` check that fails the deploy if the working tree is not clean.

File: `deploy/update.sh:10`

**F14 — No Account Deletion Route**
Severity: **Medium** | Effort: Medium

There is no mechanism for a user to delete their account or request deletion of their personal data. This is required by GDPR Article 17 (right to erasure) for any user in the EU or UK, and by CCPA Section 1798.105 for California residents. The route must anonymize or purge: `users` name and email, `waitlist_entries` if applicable, associated session tokens, and any PII in project descriptions. Projects themselves are the customer's data and require a separate retention decision.

File: No file — route does not exist

**F15 — Viewer Role Not Enforced on Write Routes**
Severity: **Medium** | Effort: Medium

The `viewer` role is defined in the data model and the role enforcement matrix in `SECURITY.md` but no `@viewer_readonly` decorator exists in the codebase. All routes that create, update, or delete assemblies, line items, or project settings are accessible to viewers. If a viewer-role user's session is compromised, or if a viewer intentionally misuses the API, they can modify or delete estimate data. The decorator pattern is specified in `SECURITY.md:99-111` and is ready to implement.

File: All POST/PUT/DELETE routes in `app.py`

---

## Verdict

The Zenbid codebase has strong foundational instincts — the isolation helpers are consistently applied across the estimate data surface, the password hashing is correct, the CSRF protection is globally enforced, and `SECURITY.md` reflects genuine security thinking. However, three findings render the current posture unacceptable for any paying customer: the admin panel exposes every customer's account data to every other customer today, with zero exploitation sophistication required; the Privacy Policy and Terms of Service do not exist, meaning there is no legal basis documented for any data processing and no user disclosure that estimate data reaches the Anthropic API; and the production deploy script has been silently failing to update the server since the branch was renamed from `master` to `main`, leaving an unknown gap between the committed codebase and what is actually running in production. The single most important issue is the admin panel multi-tenancy breach — it is not a future risk, it is a current exposure affecting every account in the system, and it will remain so for every new customer who signs up until it is fixed.
