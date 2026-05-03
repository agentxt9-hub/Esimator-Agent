---
name: kickoff
description: First-time activation of the Zenbid program. Reads all source material, grounds in current state, plans next 2-4 hours, and begins executing Foundation Sprint. Use this once at the start of the program.
---

# /kickoff — Activate the program

You are activating the Zenbid program for the first time. Execute this in order:

## Step 1 — Read the eight inputs

Read these files in this order:

1. `docs/PROGRAM_ARCHITECTURE_v2.md` — your operating manual
2. `FOUNDATION_SPRINT.md` — your current sprint scope (Tracks A, B, C, D, E)
3. `docs/00_FOUNDER_CONTEXT.md` — founder's domain expertise and constraints
4. `docs/06_ENGAGEMENT_PLAN.md` — engineering scope, especially Sprint Zero (eleven items)
5. `DECISION_QUEUE.md` — DEC-001 resolution and any pending items
6. `ORCHESTRATOR_TASK_PLAN.md` — current task state
7. `FEEDBACK_LOOP.md` — current signal state
8. Recent commits via `git log -20 --oneline` — what's already been done

Skim `docs/launch_prompts/` to internalize the personas you'll wear.

## Step 2 — Confirm critical state

Check `DECISION_QUEUE.md` for DEC-001 (beta pricing model). If unresolved, note it but proceed — you can run Foundation Sprint without DEC-001 resolved (it only blocks Outreach activation, which is post-Foundation).

Check `git status`. Confirm clean working tree.

## Step 3 — Update ORCHESTRATOR_TASK_PLAN.md

Refresh the live state to reflect:
- Current sprint = Foundation Sprint
- Started date = today
- Target close = today + 14 days
- Each track's status across all eight roles

## Step 4 — Plan the next 2-4 hours

Identify what you start first. Default order:
- **Track A.1** (provision staging environment) — start immediately
- **Track C.1** (Playwright scaffolding) — can run in parallel since it doesn't fully depend on staging
- **Track B.1** (landing page audit) — can run in parallel; works against current code
- **Track D.1** (`ai_call_log` population) — can run in parallel; doesn't depend on staging

Track A.2 (the eleven Sprint Zero items) requires staging to verify safely, so sequence those after A.1 completes.

## Step 5 — Report to the founder

Tell the founder, in 3-5 short paragraphs:
- What you read and your understanding of current state
- What you're starting with right now (the parallel tracks above)
- What you'll surface and when
- Anything that requires their input before you proceed (likely just confirming DEC-001 timing if unresolved)

## Step 6 — Begin executing

Start with Track A.1. Provision staging. Commit and push as you go. When Track A.1 is shippable, move to Track A.2 while the parallel tracks (B, C, D) continue in the same session.

Keep going until you hit a natural pause point or the founder steps in. When you pause, report status and queue the next action.
