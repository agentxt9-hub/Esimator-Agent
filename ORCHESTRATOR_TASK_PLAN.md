# Orchestrator Task Plan

*Last updated: 2026-05-03 — Foundation Sprint closed, Sprint One open*

## Current sprint

**Sprint One: Outreach Activation**
**Started:** 2026-05-03
**Target close:** 2026-05-17
**Scope summary:** Activate Tier 1 warm-network outreach (Track F). Clear the four founder-action gates first. Carry over deferred Foundation Sprint technical items in parallel. Target: 5+ stage 1 active users by close.

---

## Pre-outreach gates (founder actions — must clear before F.1 begins)

- [ ] **Gate 1 — B.1 production promotion:** Run `bash /var/www/zenbid/deploy/update.sh` on production server. Landing page must be live at zenbid.io.
- [ ] **Gate 2 — A.4 alert verification:** Wire Discord/email webhook in Uptime Kuma → stop staging → confirm alert fires → mark A.4 fully complete.
- [ ] **Gate 3 — SENTRY_DSN rotation:** Rotate via Sentry dashboard. Update both server `.env` files. Restart both services.
- [ ] **Gate 4 — systemd restart rate limits on production service:** SSH to production, edit `/etc/systemd/system/zenbid.service` to add `StartLimitBurst=3`, `StartLimitInterval=60s`, `Restart=on-failure`, `RestartSec=5`. Run `systemctl daemon-reload`.

---

## Track F — Outreach Playbook v1 (Outreach Operator)

*Activates after all 4 gates above are cleared.*

### F.1 — Tier 1 warm-network outreach: pending
- [ ] Build contact list: 20–30 LinkedIn construction/estimating contacts
- [ ] Personal DM template with demo clip
- [ ] Track responses in FEEDBACK_LOOP.md

### F.2 — Tier 2 LinkedIn content: pending
- [ ] Targeted public posts, faceless brand voice
- [ ] Demo clips of product features actually working

### F.3 — Tier 3 (forum/subreddit/Discord): EXPLICITLY DEFERRED
*Too unfocused for stage 1. Re-evaluate at Sprint Two.*

---

## Track D — Data & AI (Data/AI Engineer)

### D.3 — Prompt injection audit: P0 — GATE ON OUTREACH
*CLAUDE.md hard constraint: AI prompts must wrap user input in delimiters. Bare interpolation = prompt injection risk. Must close before F.1 outreach begins.*
- [ ] Audit `/ai/chat` — identify every user-supplied variable interpolated into the prompt; wrap in delimiters
- [ ] Audit `/ai/build-assembly` — same
- [ ] Audit `/ai/scope-gap` — same
- [ ] Audit `/ai/production-rate` — same
- [ ] Audit `/ai/validate-rate` — same
- [ ] Fix all violations in place (no refactor; surgical delimiter wraps)
- [ ] Document the pattern in `docs/AI_PROMPT_PATTERNS.md` (what delimiters, why, how to add a new AI route)
- [ ] Commit + tests still green

### D.2 — Flywheel field writes tests: P2
- [ ] Tests confirming `ai_generated=True` sets when AI creates data
- [ ] Tests confirming `estimator_action` captures correctly

---

## Track E — Founder Onboarding (Founder)

### E.1/E.2 — Walkthrough + workflow validation: P1 — before beta users arrive
*Foundation Sprint exit criteria not met.*
- [ ] Fresh-user signup on staging
- [ ] Receive and review welcome email from clean state
- [ ] Build a project, add line items, use Tally, use Assembly Builder
- [ ] Log every friction point to FEEDBACK_LOOP.md
- [ ] Validate workflow as 25-year estimator — document gaps

---

## Track C — Test Infrastructure (QA Engineer)

### C.2 — API security tests: P1
- [ ] Auth/cross-tenant tests at the API layer (401/403 on unauth, 403 on cross-company)
- [ ] Regression coverage for A.2 multi-tenancy fix

### C.3 — CI/CD GitHub Actions pipeline: P2
- [ ] Workflow on push-to-main: run pytest + test_takeoff.py + Playwright
- [ ] Auto-deploy to staging on merge to main

### C.4 — Test documentation: P3
- [ ] `tests/README.md` updated with structure, run instructions, how to add a test

---

## Track A — Infrastructure (Foundation Engineer)

### A.3 — Mono-repo restructure: P4 (last)
*Low urgency. No user-visible impact.*

---

## Foundation Sprint — CLOSED 2026-05-03

*See SPRINT_LOG.md for full closure entry and CHALLENGE_REPORT_SPRINT_01.md for findings.*

### Shipped (Foundation Sprint)

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
| `e60a5f4` | sprint(B.3): welcome email on signup |
| `59b29f7` | brand: B.2 — rename AgentX → Tally + banned phrases removed |
| `e8a0b96` | sprint(B.4+B.5): demo script lock + brand coherence checklist |

---

## Backlog / Persistent

- `deploy/staging-setup.sh` bugs: no postgres detection before createdb; nginx server block issues. Fix before next staging rebuild.
- Growth-hub admin recovery runbook: NPM password recovery wasted 30+ min. Document container names, DB locations, bcrypt reset SQL in `docs/GROWTH_HUB_RECOVERY.md`.
- Startup gate + key rotation atomicity: document required ops sequence in `docs/OPERATIONS.md`.
- `docs/00_FOUNDER_CONTEXT.md` missing from repo. Brand voice covered by `06_ENGAGEMENT_PLAN.md` Section 7 for now.
- `test_login_only.py` requires live server — excluded from standard `pytest tests/` run.
- SQLAlchemy LegacyAPIWarning (Query.get() deprecated) — 72 warnings in test suite; low-priority cleanup.
