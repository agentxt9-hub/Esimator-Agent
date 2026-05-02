---
name: decide
description: Resolve a decision from DECISION_QUEUE.md. Arguments are the decision number and the chosen option (or just the answer in plain English). Updates the queue, applies the decision, unblocks any work waiting on it.
argument-hint: [DEC-NNN] [option-or-answer]
---

# /decide — Resolve a decision

Argument: `$ARGUMENTS` (e.g., "DEC-001 option 1" or "DEC-002 sprint two scope is design system close + AI identity")

## Step 1 — Locate the decision

Read `DECISION_QUEUE.md`. Find the DEC-NNN named in `$ARGUMENTS` (or the most recent unresolved DEC if the founder didn't specify).

If multiple unresolved DECs exist and the argument is ambiguous, ask which one.

## Step 2 — Capture the resolution

Update the DEC in `DECISION_QUEUE.md`:
- Fill in "Founder decision:" with the chosen option or answer
- Fill in "Decided on:" with today's date
- Move the entire DEC entry from "Pending" to "Resolved" section
- Apply ~~strikethrough~~ formatting around the title for visual scan

## Step 3 — Apply the decision

For each well-known DEC, apply concretely:

### DEC-001: Beta pricing and capture model
- Update `gtm/01_EXECUTION_WORKFLOWS/outreach/PLAYBOOK.md` if it exists, with the locked model
- Update landing page CTA copy if needed (route to /build if so)
- If the locked model implies pricing fields, update product code accordingly

### DEC-002: Sprint One scope
- Use the resolution to invoke `/sprint-start` for the new sprint
- Or if the founder is using `/decide` standalone, draft the new sprint task plan and confirm

### Generic DEC
- Read the DEC's "Context" and "Options" sections
- Identify what files/work need to change based on the founder's choice
- Either execute the change directly (if small) or queue it as a `/build` task

## Step 4 — Unblock waiting work

Check `ORCHESTRATOR_TASK_PLAN.md` for any "Blocked" items waiting on this decision. Move them to "In flight" and resume execution.

## Step 5 — Commit and report

Stage `DECISION_QUEUE.md` and `ORCHESTRATOR_TASK_PLAN.md` plus any code changes. Commit with `decide(DEC-NNN): [resolution summary]`. Push.

Reply briefly:
- "Resolved DEC-NNN: [resolution]. [What unblocks]. [What you're doing next.]"
