# Sprint Log

Closure summaries for each sprint. The Orchestrator drafts; the founder confirms.

---

## Sprint 01: Foundation Sprint — Closed 2026-05-03

### Scope
- Track A — Infrastructure: staging env, 11 Sprint Zero security fixes, monitoring baseline, mono-repo restructure
- Track B — Brand Coherence: landing page, in-app copy, welcome email, demo script, brand checklist
- Track C — Test Infrastructure: Playwright E2E, API tests, monitoring infra, test docs
- Track D — Data & AI: ai_call_log table + log_ai_call(), flywheel field writes review, prompt construction audit
- Track E — Founder Onboarding: fresh-user walkthrough and workflow validation

### Shipped
- `5bbe8da` — A.2: All 11 Sprint Zero security + data integrity fixes
- `abf105b` — A.1: Staging environment (staging.zenbid.io live, SSL, separate DB, port 8001)
- `e25db7b` — B.1: Landing page coherence — 5 issues fixed (staging; not yet in production)
- `ff373a6` — B.1: 2-stage beta — remove $29/mo from all landing copy
- `db14ebf` — DEC-005: Stage 1→2 feedback trigger locked
- `50cfde5` — Ops: deploy script hardening — SECRET_KEY guard + systemd restart rate limits
- `d85be43` — D.1: ai_call_log table + log_ai_call() wired into all 5 AI routes
- `6c060d9` — A.4: Sentry + structured logging + auth event logging + error handlers
- `784e6f1` — C.1: Playwright E2E scaffolding — 25/25 passing on staging
- `e60a5f4` — B.3: Welcome email on signup (brand-aligned, Tally named, reply-to founder)
- `59b29f7` — B.2: AgentX → Tally rename across all user-facing in-app copy + banned phrases removed
- `e8a0b96` — B.4+B.5: Demo script lock + brand coherence checklist

### Deferred
- **A.3 — Mono-repo restructure:** Deferred explicitly. Low urgency; no user-visible impact. Sprint One backlog P4.
- **A.4 — Uptime Kuma notification channel:** Code verified; end-to-end alert path not verified. Founder action required (wire webhook + smoke test). Gate on outreach.
- **B.1 — Production promotion:** Landing page approved on staging; `update.sh` not run on production. Founder action required before outreach begins.
- **C.2 — API security tests:** Auth/cross-tenant API layer tests not written. Sprint One P1.
- **C.3 — GitHub issue automation from CI:** Partial; Sentry + Uptime Kuma wired but no GitHub Actions CI pipeline. Sprint One P2.
- **C.4 — Test documentation:** `tests/README.md` not updated. Sprint One P3.
- **D.2 — Flywheel field writes tests:** ai_generated + estimator_action behavioral tests not written. Sprint One P2.
- **D.3 — Prompt construction discipline audit:** Not shipped. Violates CLAUDE.md hard constraint (bare user-input interpolation may exist in production). Sprint One P0.
- **E.1/E.2 — Founder walkthrough + workflow validation:** Exit criteria not met. Required before first beta users arrive. Sprint One P1.
- **SENTRY_DSN rotation:** DSN exposed in session log. Founder to rotate via Sentry dashboard + update both server .env files. Not a code change.
- **systemd restart rate limits on live production service:** Applied to deploy scripts; production service file not yet updated manually. Founder SSH action required.

### Test status
- pytest tests/ (excl. test_login_only.py): **39/39 passed**
- test_takeoff.py: **99/99 passed**
- Playwright E2E: **25/25 passed** (run on staging.zenbid.io)
- API security tests (C.2): **not written**
- CI pipeline: **not wired** (manual deploy only)

### Findings (from Engineering Challenger pass)
1. **D.3 gap violates a hard constraint.** CLAUDE.md requires delimiter-wrapped user inputs in AI prompts. The audit confirming compliance (or finding violations) was never run. This is a prompt injection risk in production.
2. **No API-layer regression test for multi-tenancy.** A.2 fixed the breach; C.2 didn't write the guard. A future route without `get_project_or_403()` would pass all current tests.
3. **A.4 notification path is unverified — outreach gate claim is imprecise.** The "gate met" claim in the task plan is code-verified, not end-to-end verified. Alert must fire before outreach.
4. **Founder walkthrough not completed.** The product has never been exercised by the founder as a fresh user. We don't know what the first beta user's experience will actually be.
5. **No review artifacts produced.** 11 security fixes and a new data layer shipped without committed review docs.

### Next sprint candidate scope
Sprint One: Outreach Activation (founder-directed). Tier 1 warm-network DMs + Tier 2 LinkedIn content. Gate: B.1 in production + A.4 alerts verified + D.3 prompt audit + E.1 founder walkthrough. Target: 5+ stage 1 active users. See DEC-002 (resolved below).
