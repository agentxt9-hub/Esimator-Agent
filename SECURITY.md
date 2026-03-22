# SECURITY.md — Zenbid Security & Data Protection Framework

> **Purpose:** This is a living, mandatory reference document. Every feature build, bug fix, route addition, schema change, and AI integration must be evaluated against this framework before implementation. Security is not a feature — it is the foundation.

> **Audience:** Claude Code (primary), AgentX (decision-maker), future contractors or team members.

> **Philosophy:** Zenbid is built on a simple promise — contractor data is sacred. Bid pricing, labor rates, subcontractor relationships, and project financials are among the most sensitive data a construction company holds. We protect it like it's our own.

---

## PART 1 — SECURITY PRINCIPLES (Non-Negotiable)

These apply to every line of code written for Zenbid. No exceptions.

### 1. Least Privilege by Default
Every user, every route, every AI action, every DB query should access only what it needs and nothing more. When in doubt, restrict first and open up deliberately.

### 2. Defense in Depth
No single security control is sufficient. Layer authentication + authorization + input validation + rate limiting + logging. If one layer fails, others catch it.

### 3. Multi-Tenant Isolation is Sacred
A company's data must never be accessible by another company's users — not by accident, not by URL manipulation, not by any means. Every DB query that touches tenant data must include a `company_id` filter or go through an `_or_403()` helper. This is the single most important invariant in the system.

### 4. AI Actions Require Human Authorization
The AI layer (AgentX / Claude API) may suggest, propose, and draft — but it must never autonomously modify estimate data, user records, or financial figures without an explicit user action. The `apply` step is mandatory and must never be bypassed.

### 5. Inputs Are Untrusted Until Validated
All user input — form fields, URL parameters, JSON payloads, AI-generated content, file uploads — is untrusted until explicitly validated server-side. Client-side validation is UX convenience only. Never rely on it for security.

### 6. Secrets Never Touch Code or Logs
API keys, database credentials, tokens, and passwords live only in `.env` files (local) and server environment variables (production). They are never committed to Git, never logged, never embedded in templates, never exposed in API responses.

### 7. Fail Secure
When something goes wrong, deny access rather than grant it. A 500 error is better than unauthorized data exposure. Errors should never leak stack traces, database structure, or internal paths to end users.

### 8. Log Everything Security-Relevant
Authentication events, authorization failures, AI actions, rate limit triggers, and admin operations must be logged with timestamp, user ID, company ID, and IP address. Logs are the audit trail that enterprise customers will ask for.

### 9. Security Work Is Never "Done"
Every sprint includes a security review step. New features introduce new attack surfaces. Dependencies introduce vulnerabilities. This document is updated whenever the security posture changes.

---

## PART 2 — AUTHENTICATION & SESSION SECURITY

### Standards
- Flask-Login with server-side sessions is the authentication layer. JWT may be added for future API routes only.
- Passwords must be hashed with `werkzeug.security.generate_password_hash` (bcrypt-backed). Never store plaintext passwords. Never log passwords.
- Session cookies must be `HttpOnly`, `Secure` (HTTPS only), and `SameSite=Lax` at minimum.
- `SECRET_KEY` must be a cryptographically random string of at least 32 characters. Never use default or weak keys.
- Sessions expire after 24 hours of inactivity by default. "Remember me" extends to 30 days maximum.

### Checklist for Every New Route
- [ ] Is `@login_required` applied?
- [ ] Does the route access tenant data? If yes, does it use `get_project_or_403()` or equivalent?
- [ ] Are URL parameters (e.g. `project_id`, `assembly_id`) validated against the current user's company?
- [ ] Does the route accept POST/PUT/DELETE? If yes, is CSRF token validated?

### Password Reset
- Reset tokens must be cryptographically random (use `secrets.token_urlsafe(32)`).
- Tokens expire after 1 hour maximum.
- Tokens are single-use — invalidated immediately upon use.
- The reset endpoint must not confirm or deny whether an email exists (prevents user enumeration).

### MFA (Target State — pre-revenue milestone)
- TOTP-based MFA (authenticator app) for all admin role users.
- Required for any user with billing access.
- Backup codes generated at enrollment.

---

## PART 3 — AUTHORIZATION & MULTI-TENANT ISOLATION

### The Rule
**Every route that touches Project, Assembly, LineItem, LibraryItem, WBSProperty, WBSValue, ProductionRateStandard, or any company-owned model must validate company ownership before responding.**

### Approved Isolation Helpers (use these — never query directly without them)
```python
get_project_or_403(project_id)       # validates project.company_id == current_user.company_id
get_assembly_or_403(assembly_id)     # validates via project chain
get_lineitem_or_403(item_id)         # validates via assembly → project chain
get_library_item_or_403(item_id)     # validates item.company_id == current_user.company_id
```

### Role Enforcement Matrix
| Action | admin | estimator | viewer |
|--------|-------|-----------|--------|
| Read projects/estimates | ✅ | ✅ | ✅ |
| Create/edit/delete projects | ✅ | ✅ | ❌ |
| Create/edit/delete line items | ✅ | ✅ | ❌ |
| Manage company users | ✅ | ❌ | ❌ |
| Access /admin routes | ✅ | ❌ | ❌ |
| Trigger AI apply actions | ✅ | ✅ | ❌ |
| Export proposals/PDFs | ✅ | ✅ | ✅ |

### Viewer Role Enforcement (Current Gap — HIGH priority)
All POST/PUT/DELETE routes must check for viewer role and return 403 before processing. Implement via `@viewer_readonly` decorator:
```python
from functools import wraps
from flask_login import current_user
from flask import jsonify, abort

def viewer_readonly(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role == 'viewer':
            abort(403)
        return f(*args, **kwargs)
    return decorated
```
Apply to all write routes in addition to `@login_required`.

### Proposal Route (Current Gap — HIGH priority)
`/project/<id>/proposal` must use `get_project_or_403(project_id)` before rendering. Any logged-in user from any company can currently access any proposal by URL — this must be fixed.

---

## PART 4 — INPUT VALIDATION & INJECTION PREVENTION

### SQL Injection
- All database queries must use SQLAlchemy ORM or parameterized queries. Raw `f-string` SQL is forbidden.
- Never interpolate user input directly into query strings.
- Reviewed and safe: SQLAlchemy ORM used throughout. Maintain this pattern strictly.

### XSS Prevention
- Jinja2 auto-escaping is active and must remain active. Never use `| safe` on user-supplied content.
- The approved pattern for embedding data in templates is:
```html
<script id="my-data" type="application/json">{{ data | tojson | safe }}</script>
```
Parsed in JS with: `JSON.parse(document.getElementById('my-data').textContent)` — this is XSS-safe.
- Never use `innerHTML` to inject user-supplied data in JavaScript. Use `textContent` or DOM methods.

### CSRF Protection
- `CSRFProtect(app)` from Flask-WTF is active globally.
- All HTML forms must include: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- All `fetch()` POST/PUT/DELETE calls are covered by the monkey-patch in `app_base.html`. Do not remove it.
- The `/forgot-password` form is currently unprotected (public route). Add CSRF as low-priority hardening.

### Prompt Injection (AI Routes)
This is a critical, Zenbid-specific attack vector. User-supplied content (project names, assembly labels, line item descriptions, notes) flows into Claude API prompts. A malicious user could embed instructions in these fields to manipulate AI behavior.

**Rules for all `/ai/*` routes:**
- System prompt must be structurally separated from user content. Never concatenate them.
- User-sourced data inserted into prompts must be clearly labeled and bounded:
```python
# CORRECT
system = "You are a construction estimating assistant..."
user_content = f"[ESTIMATE DATA START]\n{estimate_context}\n[ESTIMATE DATA END]\n\nUser question: {message}"

# INCORRECT — user input can escape context
prompt = f"You are an assistant. Here is context: {estimate_context}. Answer: {message}"
```
- Strip or escape any `[INST]`, `<|system|>`, `###`, or similar token-manipulation patterns from user-supplied text before inserting into prompts.
- Validate that AI `write_proposal` responses only modify fields in the allowed set before applying them. Never apply AI-proposed changes to fields outside the approved whitelist.

### File Uploads (Future)
When file uploads are implemented (PDF takeoffs, logo images):
- Validate MIME type server-side (not just file extension).
- Scan file content, not just the name.
- Store uploads outside the web root or in object storage (S3/DigitalOcean Spaces).
- Never execute uploaded files.
- Restrict maximum file size at both Nginx and application layer.

---

## PART 5 — RATE LIMITING & ABUSE PREVENTION

### Current State
Flask-Limiter with in-memory storage is active on:
- `/login` — 10 requests/minute (POST only)
- `/ai/chat` — 20 requests/minute
- `/ai/apply` — covered under AI routes

### Rules
- All authentication endpoints (`/login`, `/signup`, `/forgot-password`, `/reset-password`) must be rate limited.
- All AI routes must be rate limited to prevent cost abuse.
- Any route that sends email must be rate limited (max 3-5 per hour per IP).
- When scaling to multi-worker production, migrate Flask-Limiter storage to Redis: `storage_uri='redis://...'` — in-memory resets on restart and doesn't share across workers.

### Future: IP Blocking
For persistent abuse, add IP-level blocking at the Nginx layer. Document the process in the deployment guide.

---

## PART 6 — DATA PROTECTION & PRIVACY

### Data Classification
| Data Type | Classification | Handling |
|-----------|---------------|---------|
| Estimate line items, quantities, costs | **Confidential** | Company-isolated, never shared across tenants, never used for training without explicit opt-in |
| User credentials (hashed) | **Restricted** | DB only, never logged, never in responses |
| API keys (Anthropic, SendGrid) | **Restricted** | Env vars only, never in code or logs |
| Project names, client names | **Confidential** | Company-isolated |
| Company profile (name, address) | **Internal** | Company-isolated |
| Anonymous usage metrics | **Internal** | Aggregated only, no PII |

### Encryption
- **In transit:** HTTPS/TLS required for all traffic. Nginx must redirect HTTP → HTTPS (pending SSL cert — CRITICAL).
- **At rest:** DigitalOcean managed PostgreSQL enables encryption at rest by default. Confirm this is active in cluster settings.
- **Backups:** Ensure DigitalOcean automated backups are enabled on the managed DB cluster.

### Data Retention
- User data is retained for the duration of the account plus 90 days after account closure.
- Deleted projects are soft-deleted initially (add `deleted_at` column) and purged after 30 days.
- Audit logs are retained for 1 year minimum.
- Password reset tokens are purged after use or expiry.

### AI Training Data Policy (Critical for Enterprise Sales)
This must be clearly stated in the Privacy Policy and Terms of Service:

> **Zenbid does not use customer estimate data to train AI models without explicit, opt-in consent.**

The data flywheel / Cost Intelligence strategy is built on a future opt-in program with clear value exchange. No customer data flows to any AI training pipeline without:
1. A clear opt-in consent event with description of what data is used.
2. A documented data anonymization process before any training use.
3. An opt-out mechanism that is as easy as opt-in.

This policy must be in writing before the first paying customer.

### GDPR / CCPA Awareness
Zenbid collects personal data (name, email, company) from users. Even if initial customers are US-based:
- Privacy Policy must disclose what data is collected, why, and how long it is retained.
- Users must be able to request deletion of their account and data.
- Implement a `/account/delete` route that purges or anonymizes all user PII.
- Do not sell or share user data with third parties (advertising, data brokers).

---

## PART 7 — INFRASTRUCTURE & DEPLOYMENT SECURITY

### Server Hardening (DigitalOcean Droplet)
- SSH access via key-based authentication only. Password SSH must be disabled.
- `ufw` (firewall) must be active and allow only ports 22 (SSH), 80 (HTTP → redirects), 443 (HTTPS).
- All other ports must be closed.
- Keep system packages updated: `apt update && apt upgrade` on a regular cadence.
- `FLASK_DEBUG=false` in production at all times. Debug mode exposes an interactive shell.

### Nginx Configuration
- Redirect all HTTP traffic to HTTPS (pending SSL cert — CRITICAL).
- Add security headers to all responses:
```nginx
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```
- Disable Nginx version disclosure: `server_tokens off;`
- Set reasonable client body size limits to prevent large upload abuse.

### Secret Management
- All secrets live in `.env` (local, gitignored) and server environment variables (production).
- **Never** commit `.env` to Git. Confirm `.gitignore` covers it.
- Rotate `SECRET_KEY` if it is ever exposed or suspected compromised.
- The `ANTHROPIC_API_KEY` on the server must be verified present before the app starts (add startup check).
- Future: migrate to DigitalOcean Secrets Manager or Doppler as the team grows.

### Dependency Security
- `requirements.txt` with pinned exact versions is mandatory. It prevents silent version drift and supply chain surprises.
- Run `pip audit` against `requirements.txt` before each production deploy to check for known CVEs.
- Update dependencies deliberately (test before deploying updates).
- Never `pip install` unpinned packages in production.

### Database Security
- The managed PostgreSQL cluster must not be publicly accessible — bind to internal network / trusted IP only.
- The app's DB user should have minimum necessary permissions (SELECT, INSERT, UPDATE, DELETE on app tables — not CREATE, DROP, or superuser).
- Enable automated backups on the DigitalOcean managed cluster. Test restore at least once.
- Never log full SQL queries in production (may contain sensitive data).

### DigitalOcean Account Security
- Enable MFA on the DigitalOcean account (authenticator app).
- Add a backup email address.
- Audit team member access — only necessary accounts should have access.

---

## PART 8 — LOGGING & MONITORING

### What Must Be Logged
Every log entry must include: `timestamp`, `user_id`, `company_id`, `ip_address`, `action`.

| Event | Log Level | Notes |
|-------|-----------|-------|
| Successful login | INFO | user_id, IP |
| Failed login attempt | WARNING | email attempted, IP |
| Password reset requested | INFO | email, IP |
| Password reset completed | INFO | user_id |
| 403 authorization failure | WARNING | user_id, resource attempted |
| Rate limit triggered | WARNING | route, IP |
| AI action applied to estimate | INFO | user_id, project_id, action type |
| Admin action | INFO | admin user_id, target user_id, action |
| Account created | INFO | company_id, user_id |

### Log Storage
- Application logs via Gunicorn → systemd journal (`journalctl -u zenbid`).
- Do not log passwords, tokens, full API keys, or full estimate data content.
- Retain logs for 90 days minimum on-server; archive to DigitalOcean Spaces for longer retention.

### Alerting (Target State)
- Alert on: >10 failed logins in 5 minutes from one IP; 403 errors spiking; application errors spiking.
- Simple initial implementation: send email alert via Flask-Mail for critical security events.

---

## PART 9 — LEGAL & COMPLIANCE DOCUMENTS

These are prerequisites for any paying customer. Both are currently placeholder routes — **CRITICAL priority.**

### Privacy Policy (Must Cover)
- What personal data is collected (name, email, company name, usage data)
- Why it is collected (account management, service delivery, product improvement)
- How long it is retained
- Whether it is shared with third parties (list them: Anthropic for AI processing, SendGrid for email)
- User rights: access, correction, deletion
- **Explicit statement on AI training data use** (see Section 6)
- Contact information for privacy requests

### Terms of Service (Must Cover)
- Acceptable use policy
- Data ownership: customer data belongs to the customer
- Service availability / SLA expectations
- Account termination conditions
- Limitation of liability
- **Data processing agreement framework** (needed for any enterprise customer that asks)

### Recommended Implementation
Use a reputable SaaS Terms/Privacy template service (Termly, Iubenda, or a lawyer-reviewed template) and customize. Do not write these from scratch without legal review.

---

## PART 10 — AGENTIC WORKFLOW SECURITY

### Principles for AI-Assisted Development (Claude Code)
These rules govern how Claude Code is used to build Zenbid itself — separate from how the app's AI features work.

- Claude Code sessions must never be given production database credentials.
- Prompts to Claude Code must not include real customer data, even as examples.
- All Claude Code output must be reviewed before deployment. Never auto-deploy AI-generated code without human review.
- Claude Code generated migrations must be tested in local dev before running on production.
- The `CLAUDE.md` file must be kept current so Claude Code always has the correct security context.

### Principles for AgentX (In-App AI Features)
- AgentX may read project data to build context for responses.
- AgentX may propose changes via `write_proposal` JSON blocks.
- AgentX must never directly write to the database. All writes go through the `/ai/apply` route which validates company ownership before applying.
- The `allowed` fields whitelist in `/ai/apply` is a security control — it must be reviewed when new fields are added to models.
- AI-generated content inserted into estimates must be treated as user input for XSS purposes (escaped by Jinja, not rendered as HTML).

---

## PART 11 — CURRENT SECURITY GAPS & REMEDIATION BACKLOG

These are known issues pulled from the codebase audit. They are ordered by priority. Each must be resolved before the corresponding milestone.

### CRITICAL — Block on Beta Launch

| # | Issue | Location | Remediation |
|---|-------|----------|-------------|
| C-1 | No HTTPS / SSL certificate | Nginx config, DigitalOcean | Install Let's Encrypt cert via Certbot; configure Nginx HTTP→HTTPS redirect |
| C-2 | Privacy Policy route returns placeholder | `/privacy` route | Implement real Privacy Policy page before any paying user |
| C-3 | Terms of Service route returns placeholder | `/terms` route | Implement real Terms of Service page before any paying user |
| C-4 | `ANTHROPIC_API_KEY` not verified at startup | `app.py` | Add startup validation — fail fast with clear error if key is missing or default |

### HIGH — Resolve Before First Paying Customer

| # | Issue | Location | Remediation |
|---|-------|----------|-------------|
| H-1 | Proposal route not using `get_project_or_403()` | `/project/<id>/proposal` in `routes.py` | Replace direct `Project.query.get_or_404()` with `get_project_or_403(project_id)` |
| H-2 | Viewer role not enforced on write routes | All POST/PUT/DELETE routes | Implement `@viewer_readonly` decorator; apply to all write routes |
| H-3 | No Nginx security headers | Nginx config | Add full security header block (see Part 7) |
| H-4 | DigitalOcean account lacks MFA | Account settings | Enable authenticator app MFA + add backup email |
| H-5 | Rate limiter is in-memory only | `app.py` (Flask-Limiter) | Acceptable for single-worker MVP; add Redis migration to roadmap before multi-worker |
| H-6 | No AI prompt injection hardening | `/ai/chat` route | Wrap estimate context in labeled delimiters; strip token-manipulation characters from user input before prompt insertion |

### MEDIUM — Resolve Within First 30 Days of Paid Users

| # | Issue | Location | Remediation |
|---|-------|----------|-------------|
| M-1 | No security headers in Flask fallback | `app.py` | Add `flask-talisman` or manual `after_request` header injection as backup |
| M-2 | No audit log table | Database | Add `audit_log` table: `id`, `user_id`, `company_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `created_at` |
| M-3 | No `/forgot-password` CSRF protection | `forgot_password.html` | Add CSRF token to the public password reset form |
| M-4 | Session cookie flags not explicitly set | `app.py` config | Add `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`; add `SESSION_COOKIE_SECURE=True` after HTTPS is live |
| M-5 | No soft delete on projects | `Project` model | Add `deleted_at` column; implement soft delete + 30-day purge |
| M-6 | No account deletion route | Routes | Implement `/account/delete` that anonymizes PII (GDPR requirement) |
| M-7 | DNS cleanup (GoDaddy) | GoDaddy DNS panel | Remove unused Microsoft/Skype CNAME records (`email`, `lyncdiscover`, `sip`) |
| M-8 | No dependency vulnerability scanning | `requirements.txt` | Add `pip audit` to deploy checklist |

### LOW — Pre-Scale / Enterprise Readiness

| # | Issue | Location | Remediation |
|---|-------|----------|-------------|
| L-1 | No MFA for app users | User model | Implement TOTP MFA for admin role users |
| L-2 | Rate limiter needs Redis for multi-worker | Flask-Limiter config | Migrate to Redis storage when moving to multi-worker Gunicorn |
| L-3 | No structured application logging | `app.py` | Implement Python `logging` module with structured JSON output |
| L-4 | No data export for account portability | Routes | Implement `/account/export` that returns user's data as JSON/CSV |
| L-5 | AI training data opt-in mechanism | Database + UI | Design and build opt-in flow with clear consent before Cost Intelligence tier |
| L-6 | No penetration test | External | Commission a basic web app pentest before enterprise sales |

---

## PART 12 — SECURITY REVIEW CHECKLIST

Run this checklist for every Claude Code prompt that builds a new feature or modifies existing routes.

### Before Writing the Prompt
- [ ] Does this feature touch estimate/project data? → Multi-tenant isolation required.
- [ ] Does this feature accept user input? → Validation and sanitization required.
- [ ] Does this feature add a route? → Authentication and authorization required.
- [ ] Does this feature involve AI? → Prompt injection hardening and human-in-the-loop required.
- [ ] Does this feature store new data? → Data classification and retention policy required.

### After Claude Code Delivers Output
- [ ] Are all new routes decorated with `@login_required`?
- [ ] Are all write routes decorated with `@viewer_readonly`?
- [ ] Do all routes accessing tenant data use `_or_403()` helpers?
- [ ] Are all new HTML forms CSRF-protected?
- [ ] Is any user input inserted into SQL queries via ORM/parameterization (not f-strings)?
- [ ] Is any user input rendered in templates without escaping?
- [ ] Are any secrets hardcoded or logged?
- [ ] Are new database columns accounted for in the migration (ALTER TABLE ADD COLUMN IF NOT EXISTS)?
- [ ] Does the AI `allowed` whitelist need updating for new model fields?

---

## REVISION HISTORY

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-20 | Initial framework — full security audit, gap backlog, all principles documented |

---

*This document is owned by the Zenbid engineering function. It is reviewed and updated at every major feature milestone and whenever a security incident or near-miss occurs. It is referenced in `CLAUDE.md` and `Agent_MD.md` as a mandatory pre-build consultation document.*
