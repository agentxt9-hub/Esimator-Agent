---
name: status
description: Get a one-paragraph current state report. Reads operating documents and recent commits, summarizes what shipped, what's in progress, what's blocked, and what's next.
---

# /status — Current state report

Read in this order:

1. `ORCHESTRATOR_TASK_PLAN.md`
2. `FEEDBACK_LOOP.md` (entries from last 24 hours)
3. `DECISION_QUEUE.md` (pending items)
4. `git log --oneline -10` (recent commits)
5. Any open `HANDOFF_TO_*.md` files at repo root

## Report format

Reply with one paragraph in this structure:

> **Sprint:** [name] · Day [N]/14 · [% complete estimate]
>
> **Shipped recently:** [1-2 most significant items from last 24h]
>
> **In progress:** [what you're actively working on]
>
> **Blocked:** [anything blocked, with what's blocking it; "nothing blocked" is fine]
>
> **Pending decisions:** [count of unresolved DEC items, with most-urgent named]
>
> **Next:** [the single next action you'll take]

Keep it tight. No preamble, no apology, no narration. Just the paragraph.

If the founder asks a follow-up question after status, answer it directly and continue executing.
