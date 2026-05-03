---
name: sprint-close
description: Close the active sprint. Verifies exit criteria, runs the Engineering Challenger pass mentally, drafts the closure entry, surfaces next-sprint scope to the queue, asks founder to confirm.
---

# /sprint-close — Close the active sprint

## Step 1 — Verify exit criteria

Read the active sprint's task plan (`FOUNDATION_SPRINT.md` if Foundation, otherwise `SPRINT_NN_TASK_PLAN.md`). For each item in the sprint scope, confirm:
- It shipped (find the commit) OR was explicitly deferred (with reason)
- Tests pass: run `pytest tests/`, `python test_takeoff.py`, and Playwright suite if applicable
- Reviews complete: `SECURITY_REVIEW_*.md`, `DATA_AI_REVIEW_*.md`, `DESIGN_REVIEW_*.md` files exist for relevant work

If exit criteria are NOT met:
- Report to founder: which items aren't done, what's needed to close, estimated time
- Do NOT close the sprint
- Continue execution on incomplete items

## Step 2 — Run the Engineering Challenger pass (mentally)

Wear the Engineering Challenger persona (see `docs/launch_prompts/07_ENGINEERING_CHALLENGER.md` for character notes). For the work shipped this sprint, ask:

- What assumption is embedded in this work that nobody named?
- What did exit criteria verify and what did they not verify?
- What adjacent surface might this affect that wasn't tested?
- What edge case in production data could behave differently than test data?
- What's missing from this sprint that should have been here?
- Does what shipped match the sprint's original scope, or did it drift?

Capture observations as `CHALLENGE_REPORT_SPRINT_NN.md` at repo root.

## Step 3 — Draft closure entry

Append to `SPRINT_LOG.md`:

```markdown
## Sprint [N]: [name] — Closed [date]

### Scope
[bullet list]

### Shipped
[bullet list with commit hashes]

### Deferred
[anything in scope that didn't ship, with reason]

### Test status
[pytest pass count, Playwright pass count, any failures]

### Findings (from challenge pass)
[3-5 most important observations]

### Next sprint candidate scope
[What FEEDBACK_LOOP and challenge findings suggest]
```

## Step 4 — Surface next sprint to DECISION_QUEUE.md

Add `DEC-NNN: Sprint [N+1] scope` with:
- Context: what closed, what FEEDBACK_LOOP suggests
- Options (typically 2-3 for next sprint focus)
- Recommended call

## Step 5 — Notify founder

Reply with:

> **Sprint [N]: [name] — closed.**
>
> [2-3 sentence summary of what shipped, the most important finding from challenge, the next-sprint recommendation]
>
> Closure entry in `SPRINT_LOG.md`. Challenge report in `CHALLENGE_REPORT_SPRINT_NN.md`. DEC-NNN added for next-sprint scope confirmation.
>
> Confirm closure to commit, or push back with rework needed.

## Step 6 — On confirmation, commit and push

Stage `SPRINT_LOG.md`, `CHALLENGE_REPORT_SPRINT_NN.md`, `DECISION_QUEUE.md`, `ORCHESTRATOR_TASK_PLAN.md` (cleared "in flight" sections). Commit with `sprint(N): close — [name]`. Push.

The sprint is closed. Wait for founder to invoke `/sprint-start` for the next one.
