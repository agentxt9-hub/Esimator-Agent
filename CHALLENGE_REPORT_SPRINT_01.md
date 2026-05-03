# Challenge Report — Sprint 01: Foundation Sprint

## Sprint summary

The Foundation Sprint set out to make the tool, infrastructure, and first-user surface "clean, coherent, and not clunky" before any outreach began. It shipped: staging environment (A.1), all 11 Sprint Zero security fixes (A.2), monitoring infrastructure (A.4), landing page refresh (B.1 on staging), full in-app copy brand alignment (B.2), welcome email (B.3), demo script (B.4), brand coherence checklist (B.5), Playwright E2E scaffolding 25/25 (C.1), and ai_call_log + log_ai_call() (D.1). Seven of the eight tracks have partial or full delivery. Four tracks (C, D, E, and the production-promotion step of B.1) closed with deferred items. The sprint ran two days against a 14-day window — velocity was high; scope completion was partial.

---

## Observations

### 1 — D.3 didn't ship, but it's a stated hard constraint — not a backlog item

CLAUDE.md Section "Hard constraints" explicitly says: *"AI prompts wrap user input in delimiters. `<project_name>`, `<description>`, `<line_item>`. Never bare interpolation."* D.3 (prompt construction discipline audit) was in Foundation Sprint scope and didn't ship. This means the product is currently operating in production with AI prompts that may have bare user-input interpolation. The risk is prompt injection — a user crafting a project name or description that escapes the intended prompt boundary and manipulates Tally's output. We do not know the current state of this because the audit was never done. This is the most uncomfortable finding in this report.

### 2 — C.2 never shipped — the most critical security property has no regression test

The Foundation Sprint exit criteria required API tests confirming 401/403 on unauth and 403 on cross-company access. C.1 (Playwright E2E scaffolding) shipped 25 tests, including one cross-company isolation guard. But those are UI-layer tests — they test what a browser sees, not what the API returns to a crafted request. The A.2 multi-tenancy fix closed a real breach in the admin panel. There is currently no automated test that would catch a regression in that fix at the API layer. If a future route is added without `get_project_or_403()`, no test fails. We shipped the fix; we didn't ship the safety net.

### 3 — No review artifacts were produced

The Engineering Challenger launch prompt expects `SECURITY_REVIEW_NN.md`, `DATA_AI_REVIEW_NN.md`, and `DESIGN_REVIEW_NN.md` to exist for relevant work. None were committed. The sprint closed 11 security fixes, a new data table with a helper wired into five production AI routes, and a new prompt construction pattern — without a formal review artifact for any of it. The work may be correct. The reviews may have happened informally. But there is no artifact. The next person who needs to understand "what security properties were verified for the A.2 fixes" has nowhere to look.

### 4 — A.4 notification path is unverified — the outreach gate claim is imprecise

ORCHESTRATOR_TASK_PLAN.md says "All 4 gate items in brand/COHERENCE_CHECKLIST.md Section 7 now met." One of those four is A.4. But A.4 has an explicit open gap: the Uptime Kuma notification channel is not wired, and the end-to-end alert path (staging goes down → notification reaches founder) has never been triggered. The code is verified; the alert is not. This distinction matters because the claim that outreach can begin is load-bearing on A.4 being complete. If outreach begins, strangers start arriving, staging goes down, and no one gets notified — the welcome-mat the sprint spent two days building becomes a dead end for the first users who try it.

### 5 — E.1 and E.2 (founder walkthrough) were never completed

The FOUNDATION_SPRINT.md exit criteria explicitly require: "Founder walkthrough complete, FEEDBACK_LOOP.md populated with discoveries." The Feedback Loop has founder observations from active development — it does not have a structured fresh-user walkthrough as defined in E.1. The founder has never signed up as a new user, received the welcome email from a clean state, built a project from scratch, used Tally on a real bid scenario, and logged every friction point. This is not a nice-to-have. It is the primary quality signal the Foundation Sprint was designed to produce. We are considering the sprint closed without it.

### 6 — B.1 (landing page) is in production staging, not production

The landing page changes were approved on staging and are not in production. Outreach is the primary Sprint One track. The first action of any outreach — Tier 1 warm-network DM — will direct contacts to `zenbid.io`. That URL currently serves the old copy (with or without the "AI-powered" language, fake dashboard, and removed stats). This is not a gap in the sprint plan; it is a founder action that was deferred. But it is worth naming explicitly: Sprint One cannot begin meaningful outreach until this single `update.sh` run happens.

---

## What is missing

1. **D.3 — Prompt construction discipline audit.** Not shipped. Violates a hard constraint. P0 for Sprint One.
2. **C.2 — API security tests.** Not shipped. The multi-tenancy fix has no regression coverage at the API layer. P1.
3. **Security review artifact for A.2.** 11 security fixes with no formal review doc. P2.
4. **E.1/E.2 — Founder walkthrough.** Exit criteria not met. Should happen before first beta users arrive. P1.
5. **A.3 — Mono-repo restructure.** Explicitly deferred as low urgency. Still on the backlog. P4.
6. **C.4 — Test documentation.** `tests/README.md` not updated. P3.
7. **D.2 — Flywheel field writes tests.** Tests confirming `ai_generated=True` and `estimator_action` populate correctly were not written. P2.

---

## Drift from plan

The original Foundation Sprint scope included four full test infrastructure tracks (C.1–C.4). Only C.1 shipped. The plan framed the test infrastructure as foundational to sprint close — it was not treated that way in execution. Similarly, D.2 and D.3 were in scope and neither shipped. Track E (founder onboarding) was in-scope and the exit criteria explicitly required it — it was not completed. The sprint also expected review artifacts to exist for the Engineering Challenger; none do.

The drift is understandable — the sprint ran two days at high velocity, survived a production incident, and shipped more core security and brand work than would be typical. But the test and review infrastructure trails are a real deficit.

---

## Recommendations for next sprint

1. **P0 — B.1 production promotion.** One `update.sh` run. Gate on all Tier 1 outreach. Do this before Sprint One opens.
2. **P0 — A.4 end-to-end alert verification.** Wire Uptime Kuma notification channel. Stop staging. Confirm alert fires. Then outreach gate is actually met.
3. **P0 — D.3 prompt construction discipline audit.** Violates a hard constraint currently in production. Audit all AI routes, wrap bare inputs in delimiters, document the pattern.
4. **P1 — C.2 API security tests.** Write auth/cross-tenant tests at the API layer before any new route work begins in Sprint One.
5. **P1 — E.1/E.2 founder walkthrough.** Fresh-user signup through proposal generation. Log every friction point before beta users arrive.
6. **P2 — D.2 flywheel field writes tests.** Confirm ai_generated and estimator_action populate correctly under test.
7. **P3 — Security review artifact for A.2 (retroactive).** Document what was verified, what wasn't, and what assumptions were made.
8. **P4 — A.3 mono-repo restructure.** Last. No user-visible impact.

---

## What this challenge is not

I considered raising: the SQLAlchemy LegacyAPIWarning (Query.get() deprecated) surfaced in pytest output. This is a real technical debt item — 72 warnings across the test suite — but it is not a correctness issue and does not affect the sprint's security or data properties. Deferred to a future sprint as a low-priority cleanup. Also considered: the test_login_only.py exclusion from the standard pytest suite — this is a known documented exclusion, not a new finding.
