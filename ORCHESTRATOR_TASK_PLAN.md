# Orchestrator Task Plan

*Last updated: 2026-05-02 — Foundation Sprint Day 1*

## Current sprint

**Foundation Sprint**
**Started:** 2026-05-02
**Target close:** 2026-05-16
**Scope summary:** Stand up staging environment, ship the eleven Sprint Zero items from `06_ENGAGEMENT_PLAN.md`, restructure the repo to mono-repo v2 layout, establish Playwright + monitoring infrastructure, lock brand coherence across landing/in-app/email surfaces, prepare the founder for first-beta-user testing.

Full scope detail lives in `FOUNDATION_SPRINT.md`.

## In flight (by role)

### Foundation Engineer

**Track A.2 — Sprint Zero items: SHIPPED 2026-05-02**
All eleven items shipped in one session:
- [x] Admin panel multi-tenancy: `admin_required` now enforces `SUPERADMIN_EMAIL` env var; self-service signup changed from `role='admin'` to `role='estimator'`. Active cross-company breach closed.
- [x] `/ai/apply` flywheel writes: `ai_generated=True`, `estimator_action='accepted'` set on all AI-created LineItems.
- [x] `save_assembly_builder()` flywheel writes: `ai_generated=True` set on AI-built line items.
- [x] `deploy/update.sh` branch fix: `master` → `main` + dirty-tree guard.
- [x] `SECRET_KEY` startup gate: refuses to start with default key in production.
- [x] `DATABASE_URL` startup gate: refuses to start without DATABASE_URL in production.
- [x] Open redirect fix: `next_page` validated to start with `/` before redirect.
- [x] Session cookie security flags: `HTTPONLY=True`, `SECURE=True` (production), `SAMESITE='Lax'`.
- [x] Exception leakage: all `str(e)` in AI route error responses replaced with generic messages + `app.logger.exception()`.
- [x] `requests>=2.31,<3.0` added to `requirements.txt`.
- [x] `routes.py` deleted.
- [x] Migration failure logging: `print(f"Migration failed: ...")` in except block.

**Track A.1 — Staging environment** — *scripts shipped; server provisioning pending founder action*
- [x] DEC-003 resolved: same-droplet staging (2026-05-02)
- [x] `deploy/staging-setup.sh` — one-time setup script for staging on the droplet
- [x] `deploy/staging-update.sh` — code deploy script for staging
- [x] `docs/STAGING.md` — full setup and ops documentation
- [x] `.env.staging.example` — staging env template with all new vars
- [x] `.env.example` updated with `SUPERADMIN_EMAIL`, `FLASK_ENV`, `REQUIRE_SECURE_CONFIG`
- [ ] **Founder action required:** Run `bash /var/www/zenbid/deploy/staging-setup.sh` on the droplet
- [ ] **Founder action required:** Edit `/var/www/zenbid-staging/.env` with staging secrets
- [ ] **Founder action required:** Add DNS A record for `staging.zenbid.io` → droplet IP
- [ ] **Founder action required:** `certbot --nginx -d staging.zenbid.io` for SSL
- [ ] **Founder action required:** `systemctl start zenbid-staging`
- [ ] Smoke-test after provisioning

**Track A.3 — Mono-repo restructure** — *pending: after staging is up*
**Track A.4 — Best-practices baseline** — *pending: after A.1*

### Frontend/Design Engineer
- Landing page audit and refresh — *pending*
- In-app copy audit and alignment — *pending*
- Welcome email refresh — *pending*
- Demo script lock — *pending*
- Brand coherence checklist (`brand/COHERENCE_CHECKLIST.md`) — *pending*

### QA / Test Automation Engineer
- Playwright setup — *pending*
- API test suite — *pending*
- Monitoring infrastructure (Sentry, Uptime Kuma) — *pending*
- Test documentation (`tests/README.md`) — *pending*

### Data/AI Engineer
- `ai_call_log` population on existing AI routes — *pending*
- Prompt construction discipline audit — *pending*
- Flywheel field writes review — *unblocked: Sprint Zero shipped*

### Product Engineer
- *Not active in Foundation Sprint. Activates Sprint One after Foundation closes.*

### Content Machine Operator
- *Not active in Foundation Sprint. Activates at Sprint One open.*

### Outreach Operator
- *Not active in Foundation Sprint. DEC-001 resolved: paid beta $29/mo, first 20 users. Activates at Sprint One open.*

### Founder (you)
- Walk through the user journey on staging once it's up — *pending Track A.1*
- Validate workflow correctness as a 25-year estimator — *pending walkthrough*
- DEC-001 resolved (2026-05-02): cheap paid beta, $29/mo, first 20 users for 6 months.

## Shipped today — 2026-05-02

- All 11 Sprint Zero security/data-integrity items (see Track A.2 above)
- Tests: 39/39 TanStack + API, 99/99 Takeoff — all green

## Blocked

*[none]*

## Next up

1. **Track A.1** — staging server provisioning (founder runs `staging-setup.sh` on the droplet; scripts are ready).
2. **Track C.1** — Playwright setup (starting now; writing tests against local env first, then re-run on staging).
3. **Track D.1** — `ai_call_log` table + `log_ai_call()` helper (starting now; pure code work, no staging dependency).
4. **Track B.1** — Landing page audit (starting now; works against current code).

## Coverage gaps

- `docs/00_FOUNDER_CONTEXT.md` referenced in multiple places but doesn't exist in `docs/` — file appears to be missing from the repo. Audits reference it as Section 5 (pricing intuitions) and Section 7 (brand voice). **Action needed**: if this file was never created, sections relevant to brand voice in `06_ENGAGEMENT_PLAN.md` and brand decisions in `FOUNDATION_SPRINT.md` cover the gaps adequately for now.
- `test_login_only.py` requires a live server — excluded from standard `pytest tests/` run. Should be moved to integration test suite once staging is up.
