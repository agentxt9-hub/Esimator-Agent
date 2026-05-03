---
name: build
description: Implement a feature, fix, or unit of work end-to-end. Argument is a description of what to build. You wear whichever persona fits (Foundation/Product/Frontend/Data-AI/QA), execute, test, commit, push, and report.
argument-hint: [description of what to build]
---

# /build — Execute a unit of work

Argument: `$ARGUMENTS` (description of what to build, fix, or implement)

## Step 1 — Understand the request

Parse `$ARGUMENTS`. Identify:
- **What** is being built (feature, bug fix, infrastructure, content, etc.)
- **Which persona** fits (Foundation Engineer, Product Engineer, Frontend/Design, Data/AI, QA Automation)
- **Which surface** is touched (`product/`, `gtm/`, `brand/`, `tests/`, `deploy/`)
- **What hard constraints apply** (multi-tenant isolation, flywheel writes, brand voice, etc.)

If the request is ambiguous in a way that materially changes the implementation, ask one focused clarifying question. Otherwise, proceed with reasonable defaults.

## Step 2 — Plan briefly

Internally outline:
- Files you'll modify
- Tests you'll add or update
- Hand-offs the work generates (Security review? Data/AI review? Design review?)
- Estimated scope (small=under 30 min, medium=1-3 hours, large=needs to be broken up)

If the work is large, break it into shippable units and execute one at a time with commits between.

## Step 3 — Wear the persona

Ground yourself in the relevant persona's discipline. Reference notes:
- Foundation Engineer → `docs/launch_prompts/01_FOUNDATION_ENGINEER.md`
- Frontend/Design → `docs/launch_prompts/02_FRONTEND_DESIGN_ENGINEER.md`
- QA Automation → `docs/launch_prompts/03_QA_TEST_AUTOMATION.md`
- Data/AI → `docs/launch_prompts/04_DATA_AI_ENGINEER.md`
- Product Engineer → `docs/launch_prompts/05_PRODUCT_ENGINEER.md`

Pull in their constraints. The persona is a tool you wear, not a separate session.

## Step 4 — Execute

Implement the work. Surgical scope. No drive-by improvements unless they're necessary for the change. Use design tokens, not hardcoded hex. CSRF on forms. Isolation helpers on data-touching routes. Flywheel writes on AI paths.

## Step 5 — Test

Run relevant tests:
- `pytest tests/` for backend changes
- `python test_takeoff.py` for takeoff-related changes
- `npx playwright test` for UI changes touching the user journey
- Smoke-test on staging if the change affects deployed behavior

If tests fail, fix the code (not the test) unless the test was wrong.

## Step 6 — Hand-offs

Write hand-off files at repo root if review is needed:
- `HANDOFF_TO_DATAAI.md` for AI-route changes (founder can invoke `/review ai`)
- `HANDOFF_TO_SECURITY.md` for auth/isolation/secrets changes (founder can invoke `/review security`)
- `HANDOFF_TO_DESIGN.md` for UI changes (founder can invoke `/review design`)

If the review is straightforward and you can apply the checklist yourself with confidence, do it inline rather than creating the hand-off — but document what you verified in the commit message.

## Step 7 — Commit and push

Stage changes. Commit with descriptive message: `[scope]: [persona] — [what shipped]`. Examples:
- `foundation: backend — admin panel multi-tenancy fix`
- `sprint(2): frontend — landing page brand refresh`
- `gtm: content — linkedin pain-point post template`

Push.

## Step 8 — Report

One paragraph to founder:
- What you shipped
- Tests passing
- Any review pending
- What's next on your queue (the next thing you'd naturally do without further direction)

Then continue executing the next thing unless the founder steps in.
