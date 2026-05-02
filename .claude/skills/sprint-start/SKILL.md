---
name: sprint-start
description: Open a new sprint with defined scope. Use after a sprint closes or to kick off the first sprint. Argument is the sprint name or theme. Drafts scope, surfaces to founder for confirmation, then opens the sprint.
argument-hint: [sprint-name]
---

# /sprint-start — Open a new sprint

Argument: `$ARGUMENTS` (sprint name or theme; e.g. "design-system-and-ai-identity" or "moat-component-pass-3")

## Step 1 — Determine scope

Read:
- `SPRINT_LOG.md` for what closed previously
- `FEEDBACK_LOOP.md` for signals informing what to prioritize
- `DECISION_QUEUE.md` for any DEC items that resolve into sprint scope (especially DEC-002 if at end of Foundation)
- `docs/06_ENGAGEMENT_PLAN.md` for the next sprint candidate from the engineering roadmap (Sprint Two: Design System Close + AI Identity, Sprint Three: Security Hardening, Sprint Four: Flywheel Instrumentation, Sprint Five: Pass 3 Bridge, Sprint Six: Cost Intelligence)

Draft a sprint scope with:
- Sprint name
- Sprint number
- Target duration (typically 2 weeks)
- Tracks (similar to Foundation Sprint structure: A=infrastructure, B=brand/UX, C=test, D=data/AI, etc., scaled to what's needed)
- Specific items per track
- Exit criteria

## Step 2 — Confirm with founder

Reply to the founder with:

> **Sprint [N+1]: [name] — proposed scope**
>
> [3-5 sentence summary of the sprint's intent]
>
> **Tracks:**
> - A: [items]
> - B: [items]
> - (etc.)
>
> **Exit criteria:**
> [bullet list]
>
> **Target duration:** [N] days
>
> Confirm to open, or push back with adjustments.

## Step 3 — On confirmation, open the sprint

Once founder confirms:

1. Create `SPRINT_NN_TASK_PLAN.md` at repo root with the locked scope (where NN is the sprint number)
2. Update `ORCHESTRATOR_TASK_PLAN.md`:
   - Current sprint = new sprint
   - Started = today
   - Target close = today + duration
   - Reset "In flight" sections to reflect new sprint's tracks
3. Commit with `sprint(NN): open — [name]`
4. Push
5. Begin executing Track A of the new sprint

## Step 4 — Report

Brief status: sprint opened, first track started, what to expect in the next 24 hours.
