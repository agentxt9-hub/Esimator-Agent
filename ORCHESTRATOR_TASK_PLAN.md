# Orchestrator Task Plan

*Last updated: 2026-05-02 — reconciled against git log*

## Current sprint

**Foundation Sprint**
**Started:** 2026-05-02
**Target close:** 2026-05-16
**Scope summary:** Stand up staging environment, ship the eleven Sprint Zero items, restructure the repo to mono-repo v2 layout, establish Playwright + monitoring infrastructure, lock brand coherence across landing/in-app/email surfaces, prepare the founder for first-beta-user testing.

Full scope detail lives in `FOUNDATION_SPRINT.md`.

---

## Track A — Infrastructure (Foundation Engineer)

### A.1 — Staging environment: COMPLETE ✓
*Commit: `abf105b`. Staging confirmed live by founder 2026-05-02.*
- [x] DEC-003 resolved: same-droplet staging
- [x] `deploy/staging-setup.sh` — one-time setup script
- [x] `deploy/staging-update.sh` — code deploy script
- [x] `docs/STAGING.md` — full ops documentation
- [x] `.env.staging.example` — staging env template
- [x] `.env.example` updated with new env vars
- [x] Server provisioned: `staging.zenbid.io` live, SSL, separate DB, port 8001

### A.2 — Sprint Zero (11 items): COMPLETE ✓
*Commit: `5bbe8da`. Tests: 39/39, 99/99.*
- [x] Admin panel multi-tenancy breach closed (`SUPERADMIN_EMAIL` gate)
- [x] Self-service signup: `role='admin'` → `role='estimator'`
- [x] `/ai/apply` flywheel writes: `ai_generated=True`, `estimator_action='accepted'`
- [x] `save_assembly_builder()` flywheel write: `ai_generated=True`
- [x] `deploy/update.sh`: `master` → `main` + dirty-tree guard
- [x] `SECRET_KEY` startup gate
- [x] `DATABASE_URL` startup gate
- [x] Open redirect fix on `next_page`
- [x] Session cookie flags: `HTTPONLY`, `SECURE` (production), `SAMESITE=Lax`
- [x] Exception leakage: all `str(e)` replaced + `app.logger.exception()`
- [x] `requests>=2.31,<3.0` added to `requirements.txt`
- [x] `routes.py` deleted
- [x] Migration failure logging

### A.3 — Mono-repo restructure: pending
*Depends on: A.1 complete (now unblocked).*

### A.4 — Monitoring + structured logging: CODE VERIFIED — notification gap pending closure
*Commit: `6c060d9`. Most of A.4 verified. One gap remaining.*
- [x] Sentry SDK verified via log: "Sentry is attempting to send 2 pending events" + "Waiting up to 2 seconds". Founder to confirm issue appears in sentry.io dashboard.
- [x] Uptime Kuma at status.zenbid.io — both monitors green, 60s checks
- [x] Structured logging active — journalctl + /var/log/zenbid/app.log
- [x] Auth events, admin access, 5xx handlers, `/_health` all wired
- [ ] **GAP: Uptime Kuma notification channel not wired.** 30+ min staging outage went unnoticed. Founder to: wire Discord/email webhook in Uptime Kuma → stop staging → confirm alert fires end-to-end → mark A.4 COMPLETE.
- [ ] **Founder action: rotate SENTRY_DSN** — exposed in session log. Update both server .env files, restart both services.

---

## Track B — Brand Coherence (Frontend/Design Engineer)

### B.1 — Landing page: APPROVED ON STAGING ✓ — pending production promotion
*Commits: `e25db7b`, `ff373a6`. Founder verified in browser 2026-05-02.*
- [x] H1 rewritten: estimator-native ("Measure. Price. Catch what you missed.")
- [x] Subhead: "AI-powered" removed, estimator-native language
- [x] Fake mock dashboard removed, replaced with honest feature checklist
- [x] Unsubstantiated stats ("3x", "100%") removed
- [x] All `$29/mo` references removed (2-stage beta, DEC-001 amended)
- [x] CTA everywhere: "Reserve beta access"
- [x] Banner: "Early access is open — first estimators test free."
- [x] Footer tagline and page title updated
- [ ] **Production promotion needed** — founder approved; run `bash /var/www/zenbid/deploy/update.sh` on production server

### B.2 — In-app copy audit and alignment: pending
### B.3 — Welcome email refresh: pending
### B.4 — Demo script lock: pending
### B.5 — Brand coherence checklist (`brand/COHERENCE_CHECKLIST.md`): pending

---

## Track C — Test Infrastructure (QA / Test Automation Engineer)

### C.1 — Playwright E2E + API scaffolding: COMPLETE ✓
*Commit: `784e6f1`. 25/25 E2E tests passing locally. 39/39 pytest + 99/99 takeoff still green.*
### C.2 — API test suite: pending
### C.3 — Monitoring infrastructure: pending
### C.4 — Test documentation: pending

---

## Track D — Data & AI Foundation (Data/AI Engineer)

### D.1 — `ai_call_log` table + `log_ai_call()`: COMPLETE ✓
*Commit: `d85be43`. AICallLog model, migration, helper wired into all 5 AI routes.*
### D.2 — Flywheel field writes review: unblocked (A.2 shipped)
### D.3 — Prompt construction discipline audit: pending

---

## Outreach Operator
*Not active in Foundation Sprint. Activates at Sprint One open. DEC-001 amended: 2-stage beta — stage 1 free reserved access now; stage 2 $29/mo when 3+ stage 1 users say they'd pay (DEC-005). No $29/mo in outreach until stage 2.*

## Founder
- [x] DEC-001 resolved and amended (2-stage beta model)
- [x] DEC-003 resolved (same-droplet staging)
- [x] DEC-005 resolved (feedback trigger for stage 1→2)
- [ ] Walk through user journey on staging as a real estimator (Track E.1)
- [ ] Validate workflow correctness as 25-year estimator (Track E.2)
- [ ] Run `bash /var/www/zenbid/deploy/update.sh` on production server to promote landing page changes

---

## Shipped (2026-05-02)

| Commit | What |
|---|---|
| `5bbe8da` | All 11 Sprint Zero security + data integrity fixes |
| `abf105b` | DEC-003: staging environment scripts and docs |
| `e25db7b` | Brand B.1: landing page coherence — 5 issues fixed |
| `ff373a6` | Brand B.1: 2-stage beta — remove $29/mo from all copy |
| `db14ebf` | DEC-005: stage 1→2 feedback trigger locked |
| `50cfde5` | ops: deploy script hardening — SECRET_KEY guard + systemd restart rate limits |
| `d85be43` | data: D.1 — ai_call_log + log_ai_call() wired into all 5 AI routes |
| `6c060d9` | ops: A.4 — Sentry + structured logging + auth event logging + error handlers |
| `784e6f1` | test: C.1 — Playwright E2E scaffolding — 25/25 passing |

## Blocked

*Nothing blocked.*

## Next up

1. **Track B.2** — In-app copy audit (brand coherence across authenticated surfaces)
2. **Track C.2** — API test suite expansion (widen Playwright coverage to assembly builder, AI routes with mocked API key)
3. **Track A.3** — Mono-repo restructure (unblocked)

## Backlog

- `deploy/staging-setup.sh` bugs: no postgres detection before createdb; nginx server block issues. Fix before next staging rebuild.
- Growth-hub admin recovery runbook: NPM password recovery wasted 30+ min. Document container names, DB locations, bcrypt reset SQL in `docs/GROWTH_HUB_RECOVERY.md`.
- Notification channels: Uptime Kuma + Sentry email sufficient now. Discord/Slack/SMS deferred to Sprint One+.
- SENTRY_DSN: DSN was exposed in session log. Founder to rotate via Sentry dashboard, update both server .env files, restart both services.

### P1 — Sprint One (from 2026-05-02 production 502 post-incident)

1. **Startup gate + key rotation atomicity** — Document the required ops sequence: rotate `SECRET_KEY` first, verify strong key in `.env`, THEN enable the startup gate and restart. Never ship the gate without rotating. Add to `docs/OPERATIONS.md` runbook before Sprint One opens.

2. **systemd restart rate limit on live production service** — `deploy/setup.sh` and `deploy/staging-setup.sh` now have `StartLimitBurst=3 / StartLimitInterval=60s / Restart=on-failure / RestartSec=5` in the service template, but the **live production `/etc/systemd/system/zenbid.service`** needs these values applied manually. Founder action: SSH to production, edit the service file, run `systemctl daemon-reload`.

3. ~~**Sentry + Uptime Kuma before any beta users**~~ — DONE: A.4 verified 2026-05-02.

4. **CI/CD pipeline** — Code merged to main but neither prod nor staging auto-deployed; had to manually run update.sh. GitHub Actions workflow on push-to-main needed for Sprint One.

## Coverage gaps

- `docs/00_FOUNDER_CONTEXT.md` missing from repo. Brand voice guidance covered by `06_ENGAGEMENT_PLAN.md` Section 7 for now.
- `test_login_only.py` requires live server — excluded from standard `pytest tests/` run.
