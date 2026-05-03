---
name: feedback
description: Log founder feedback or product observation to the FEEDBACK_LOOP. Argument is the observation. Triages severity and routes to a track or queues for next sprint.
argument-hint: [observation]
---

# /feedback — Log founder observation

Argument: `$ARGUMENTS` (the observation, in plain English)

## Step 1 — Capture

Append to `FEEDBACK_LOOP.md` under today's section, "From founder":

```markdown
- [timestamp] $ARGUMENTS
```

If today's date doesn't have a section yet, add one.

## Step 2 — Triage

Decide severity:

- **Blocker** (production broken, data integrity risk, security issue, founder unable to use product) → fix NOW, before continuing other work
- **High** (UX friction that makes the next beta user fail, broken brand promise, copy mismatch) → route into current sprint
- **Medium** (refinement, small feature gap, polish) → queue for next sprint via DECISION_QUEUE.md
- **Low** (nice-to-have, future consideration) → log only, no routing

## Step 3 — Route or queue

### If blocker:
Drop other work. Wear the persona that fits, fix it directly via `/build`-style flow. Push the fix. Report to founder: "fixed [observation], commit [hash], back to previous work."

### If high:
Add to `ORCHESTRATOR_TASK_PLAN.md` under the relevant role's "In flight" section. Pick it up in the current sprint cadence.

### If medium:
Add to `DECISION_QUEUE.md` as a candidate for next-sprint scope (or append to existing DEC-NNN: Sprint [N+1] scope if open).

### If low:
No routing. The log entry is the action.

## Step 4 — Report

One line to founder:
- "Logged. [Severity]. [What happens next]."

Examples:
- "Logged. Blocker — fixing now."
- "Logged. High — added to current sprint Track B."
- "Logged. Medium — queued for next sprint scope."
- "Logged. Low — captured."

Continue executing whatever you were doing before, unless severity required interrupt.
