# Foundation Sprint — Scope Document

This is the first sprint. Everything else waits on it. The Foundation Sprint must close before the program shifts to continuous velocity. It exists to make sure the tool, the infrastructure, and the surface presented to the first beta user (the founder) is clean, coherent, and not clunky.

**Target duration:** 2 weeks. Strictly scoped — no scope creep.

**Exit criteria:** All items below shipped, all existing tests passing, Playwright E2E suite running against staging, brand coherence verified across landing/in-app/email surfaces, mono-repo restructure complete, founder can use the product end-to-end without hitting clunkiness.

---

## Track A — Infrastructure (Foundation Engineer)

These are the items that protect the rest of the team and the founder from clunkiness, broken deploys, and lost data.

### A.1 — Staging environment
- Provision staging droplet (or staging app on existing infrastructure)
- Separate staging database (managed Postgres logical DB `zenbid_staging`)
- Separate staging domain (`staging.zenbid.io`) with SSL
- Update deploy script to support both `staging` and `production` targets
- Document in `docs/STAGING.md`
- Smoke-test staging deploy

### A.2 — Eleven Sprint Zero items from `06_ENGAGEMENT_PLAN.md`
1. Admin panel multi-tenancy fix (queries scoped to current company or restricted to superadmin)
2. `/ai/apply` route flywheel writes (`ai_generated=True`, `estimator_action='accepted'`)
3. `save_assembly_builder()` flywheel writes
4. `deploy/update.sh` branch reference fix (`master` → `main`)
5. `SECRET_KEY` startup gate (fail fast on weak/missing)
6. `DATABASE_URL` startup gate (fail fast on missing)
7. Open redirect fix on `next_page` parameter
8. Session cookie security flags (`HTTPONLY`, `SECURE`, `SAMESITE`)
9. Exception leakage fix (no `str(e)` in user-facing responses)
10. Add `requests` to `requirements.txt`
11. Delete unused `routes.py` if present
12. Migration logging baseline

### A.3 — Mono-repo restructure
Per `MONO_REPO_RESTRUCTURE.md`. Branch, restructure, test on staging, merge.

### A.4 — Best-practices baseline
- Centralized logging configuration (Flask app logs to file in production, stdout in development)
- Sentry (or equivalent) error capture wired into Flask app
- `.env.example` file at repo root with all required environment variables documented (no secrets)
- README.md updated to reflect new structure and setup instructions

---

## Track B — Brand Coherence (Frontend/Design Engineer)

This is the founder-flagged gap: the landing page, the in-app experience, the welcome email, and the demo script don't all tell the same story. By the end of Foundation, they do.

### B.1 — Landing page audit and refresh
- Read current `zenbid.io` landing page copy
- Audit against brand voice guidelines (currently in `00_FOUNDER_CONTEXT.md` Section 7)
- Refresh hero, subhead, CTA copy
- Replace any "Free Trial" CTA with accurate waitlist or beta-capture language
- Update visuals to match what the product actually shows in-app
- Verify the promise on landing matches the experience after signup

### B.2 — In-app copy audit and alignment
- Audit empty states, loading states, error states across all major pages
- Verify naming consistency: `Tally` for the AI (never `AgentX`), `Zenbid` for the product (never `ZenBid`, `Zen Bid`)
- Verify CSS uses design tokens (no deprecated `#1a1a2e`, `#16213e`, `#0f3460`, `#e94560`)
- Remove or replace social auth buttons per brand decision (likely remove until OAuth is wired)
- Verify all interactive elements have working backend or explicit "coming soon" states

### B.3 — Welcome email refresh
- Audit current n8n-generated welcome email template
- Refresh prompt template to enforce locked brand voice
- Verify subject line, body, signature all match landing page promise
- Test by signing up a fresh waitlist entry and reviewing the generated email

### B.4 — Demo script lock
- Write a 90-second demo script the founder uses for warm outreach
- Script should reference real product features, not roadmap claims
- Voice should match landing page and in-app copy exactly
- Script committed to `brand/demo_script.md`

### B.5 — Brand coherence checklist
- Create `brand/COHERENCE_CHECKLIST.md` — a single-page audit tool that any role can use to verify a new surface (page, email, post, demo) matches the locked voice and named-feature claims
- Checklist becomes mandatory for any GTM content shipped post-Foundation

---

## Track C — Test Infrastructure (QA / Test Automation Engineer)

The tool can't be clunky for the founder if breakage isn't caught automatically. QA stands up Playwright and monitoring in parallel with Tracks A and B.

### C.1 — Playwright setup
- Install Playwright in repo
- Configure for staging environment
- Write the 10 E2E test cases from the QA Engineer launch prompt
- All tests passing on staging

### C.2 — API test suite
- Write API tests for every authenticated route
- Confirm 401/403 on unauth, 403 on cross-company access, 200 on valid request
- All tests passing

### C.3 — Monitoring infrastructure
- Sentry configured (or equivalent error capture)
- Uptime Kuma monitoring staging and production endpoints
- GitHub issue automation: failing CI tests → automatic issue creation

### C.4 — Test documentation
- `tests/README.md` updated with structure, how to run, how CI works, how to add a test

---

## Track D — Data & AI Foundation (Data/AI Engineer)

The flywheel only works if the data layer captures the right signals. Foundation establishes the capture; later sprints expand it.

### D.1 — `ai_call_log` table and population
- Confirm schema is in place (per `06_ENGAGEMENT_PLAN.md` Sprint Four)
- Add `log_ai_call()` invocation to every existing AI route
- Capture: route name, model identifier, prompt version, token counts, response time, user/company IDs

### D.2 — Flywheel field writes review
- Verify Foundation Engineer's flywheel writes (Track A.2 items 2 and 3) are correct
- Add tests that confirm `ai_generated=True` is set when AI creates data
- Add tests that confirm `estimator_action` captures user action correctly

### D.3 — Prompt construction discipline
- Audit all existing AI routes for user-input interpolation
- Wrap user inputs in labeled delimiters (`<project_name>`, `<description>`, `<line_item>`)
- Document the prompt construction pattern in `docs/AI_PROMPT_PATTERNS.md`

---

## Track E — Founder Onboarding (You)

You're the first beta user. Foundation Sprint also prepares you to actually use the tool effectively.

### E.1 — Walk through the user journey
- Once staging is up and Tracks A, B, C, D are done, do a full walkthrough as a fresh user
- Sign up via the new waitlist/beta capture flow
- Receive welcome email — verify voice and clarity
- Log in, create a project, manually add line items, save
- Use Tally (AI co-estimator) — accept some suggestions, edit some, reject some
- Use Assembly Builder — build a custom assembly
- Run scope gap detection (if shipped)
- Generate a proposal
- Log every clunk, friction point, missing feature, confusion, copy mismatch into `FEEDBACK_LOOP.md`

### E.2 — Validate workflow correctness
- As a 25-year construction estimator, validate: does this workflow make sense for how I'd actually estimate a job?
- If no, document the workflow gaps for next sprint planning

---

## Tracks NOT in Foundation Sprint

These are deferred to Sprint One and beyond:

- New feature work (Pass 3 measurement-to-estimate bridge, dual-costing grid, etc.)
- GTM content machine activation (Content Machine Operator launches at Sprint One open)
- Outreach operations (Outreach Operator launches at Sprint One open, or earlier if brand coherence is ready and beta-capture funnel is operational)
- Strategic GTM artifacts (Market Map, Positioning, Pricing model, Brand Messaging guide) — invoked on-demand by the Orchestrator when needed
- Documentation rewrites (NORTHSTAR.md update, etc.) — incremental, not Foundation scope

---

## Foundation Sprint closure ritual

When all tracks are complete:

1. All tests passing locally and on CI (existing 29 + 99, plus new Playwright E2E, plus new API tests).
2. Staging environment matches production behavior end-to-end.
3. Mono-repo restructure deployed to production without incident.
4. Brand coherence checklist run against landing/in-app/email — all aligned.
5. Founder walkthrough complete, FEEDBACK_LOOP.md populated with discoveries.
6. Orchestrator drafts Foundation Sprint closure entry in `SPRINT_LOG.md`.
7. Founder confirms closure.
8. Sprint One scope is set based on Foundation Sprint findings + the next-most-important item from `06_ENGAGEMENT_PLAN.md`.

After closure, the program shifts to continuous velocity. Content Machine and Outreach Operators activate. Beta capture funnel opens. Real users come in. The feedback loop runs.

---

## Roles assigned to Foundation Sprint

- **Foundation Engineer** — Track A
- **Frontend/Design Engineer** — Track B
- **QA / Test Automation Engineer** — Track C
- **Data/AI Engineer** — Track D
- **Founder** — Track E
- **Product Engineer** — not active in Foundation; activates Sprint One
- **Content Machine Operator** — not active in Foundation; activates Sprint One open
- **Outreach Operator** — not active in Foundation; activates Sprint One open
- **Orchestrator** — running daily from Day 1 of Foundation; coordinates all tracks
