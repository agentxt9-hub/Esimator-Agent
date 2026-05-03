# Zenbid v2 Program Package

This package contains everything needed to activate the Zenbid v2 program. It is structured to drop directly into the root of the `zenbid` mono-repo.

## What's in here

```
.
├── README_PACKAGE.md              ← you are here
├── ROLLOUT.md                     ← step-by-step Day 1 activation guide
├── FOUNDATION_SPRINT.md           ← the active first-sprint scope
├── ORCHESTRATOR_TASK_PLAN.md      ← live state of all work (Orchestrator updates daily)
├── FEEDBACK_LOOP.md               ← user signals, bugs, content performance
├── DECISION_QUEUE.md              ← decisions awaiting founder input (starts with DEC-001)
├── SPRINT_LOG.md                  ← sprint closure summaries (empty until first close)
└── docs/
    ├── PROGRAM_ARCHITECTURE_v2.md ← master operating manual
    ├── MONO_REPO_RESTRUCTURE.md   ← how to reorganize repo safely
    └── launch_prompts/
        ├── 00_ORCHESTRATOR_DAILY.md           ← runs every day
        ├── 01_FOUNDATION_ENGINEER.md          ← Foundation Sprint Track A
        ├── 02_FRONTEND_DESIGN_ENGINEER.md     ← Foundation Sprint Track B
        ├── 03_QA_TEST_AUTOMATION.md           ← Foundation Sprint Track C
        ├── 04_DATA_AI_ENGINEER.md             ← Foundation Sprint Track D
        ├── 05_PRODUCT_ENGINEER.md             ← activates Sprint One+
        ├── 06_SECURITY_REVIEWER.md            ← ad-hoc auth/secrets/isolation review
        ├── 07_ENGINEERING_CHALLENGER.md       ← runs at sprint close
        ├── 08_CONTENT_MACHINE_OPERATOR.md     ← activates post-Foundation
        └── 09_OUTREACH_OPERATOR.md            ← activates post-Foundation
```

## How to use this package

1. Read `ROLLOUT.md` first — it tells you exactly what to do.
2. Extract the package into the root of your local `zenbid` mono-repo.
3. Commit the new files.
4. Follow the activation sequence in `ROLLOUT.md`.

That's it. Every launch prompt is self-contained — no editing required, no orientation notes to add. Open the file, copy the body between the `## PROMPT BODY — paste from here` markers, paste into a fresh Claude Code session, let it run.

## Quick reference: the eight working roles

1. **Foundation Engineer** — staging env, infrastructure, Sprint Zero items
2. **Product Engineer** — feature work (Sprint One+)
3. **Frontend/Design Engineer** — UI, brand coherence
4. **Data/AI Engineer** — AI routes, flywheel logging
5. **QA / Test Automation Engineer** — Playwright, monitoring, ticketing
6. **Content Machine Operator** — agentic content generation (post-Foundation)
7. **Outreach Operator** — beta capture, warm-network distribution (post-Foundation)
8. **Orchestrator** — daily agentic coordination across all of the above

Plus you, the founder — first beta user, strategic decision-maker.

## Quick reference: the on-demand strategic roles

When the Orchestrator detects a need (positioning drift, pricing question from beta data, brand voice audit, sprint-close challenge), it surfaces a launch prompt to `DECISION_QUEUE.md`. The on-demand prompts live in `docs/launch_prompts/` alongside the standing roles. They are not standing roles — they activate when the feedback loop says it's time.

The v1 strategic GTM prompts (Market Analyst, Positioning Lead, Pricing Strategist, Brand Messaging Lead, GTM Challenger) are kept available but archived to `docs/v1_legacy/` if you have the v1 outputs. They can be invoked the same way.

## What this package does NOT do

- It does not modify your existing product code.
- It does not delete or move your existing files (the mono-repo restructure happens in a separate, careful step on a branch — see `docs/MONO_REPO_RESTRUCTURE.md`).
- It does not fire any sessions. You fire them when you're ready.

This is a staged drop-in. Add it to the repo. Read the rollout. Fire the team when you're ready.
