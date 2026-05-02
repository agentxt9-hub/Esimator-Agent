---
name: outreach
description: Manage the outreach playbook and warm-network sequences. With no argument, reports outreach state and next actions. With argument, executes that specific outreach action.
argument-hint: [optional: status|playbook|tier-1|tier-2|cold|sequences]
---

# /outreach — Outreach playbook and sequences

Argument: `$ARGUMENTS` (optional: `status`, `playbook`, `tier-1`, `tier-2`, `cold`, `sequences`)

## With no argument — report outreach state

Read:
- `gtm/01_EXECUTION_WORKFLOWS/outreach/PLAYBOOK.md` (if exists)
- `FEEDBACK_LOOP.md` for recent beta sign-up signals
- `DECISION_QUEUE.md` for DEC-001 resolution (beta pricing model is a precondition)

Report to founder:
- Playbook status (drafted / live / blocked on DEC-001)
- Outreach activity this week (DMs sent, sign-ups, conversion rate)
- Next actions (today's Tier-1 sends, this week's content)
- Anything blocking momentum

## With `status`

Same as no argument — outreach state report.

## With `playbook`

Wear the Outreach Operator persona (reference: `docs/launch_prompts/09_OUTREACH_OPERATOR.md`).

Build or refresh the outreach playbook at `gtm/01_EXECUTION_WORKFLOWS/outreach/PLAYBOOK.md` with sections:
1. Beta capture funnel (per DEC-001 resolution)
2. Warm network sequence (Tier 1, 2, 3)
3. Content distribution cadence
4. Beta user activation flow
5. Feedback loop closure
6. Peer referral mechanism
7. Phase 2 expansion plan

Stage, commit `gtm: outreach — playbook updated`, push, report.

## With `tier-1`

Generate today's Tier-1 outreach batch:
- Read `PLAYBOOK.md` for Tier-1 message template and target count
- Generate 5 personalized DM drafts ready for the founder to send (or queue for sending via the Content Machine workflow if automated)
- Output to `gtm/02_CONTENT/drafts/outreach_tier-1_[YYYYMMDD].md`
- Report: drafts ready, founder to review and send

## With `tier-2`

Same pattern, Tier-2 (LinkedIn DM, broader industry contacts), 10 drafts.

## With `cold`

Cold outreach segmentation and templating. Activates only after Tier-1 and Tier-2 are exhausted (per playbook Phase 2). If invoked early, ask founder to confirm.

## With `sequences`

Update the multi-touch sequences for warm leads who didn't respond to first touch. Standard pattern: Day 0 first DM → Day 4 follow-up with content → Day 10 final touch with specific question.

Output to `gtm/01_EXECUTION_WORKFLOWS/outreach/sequences.md`.

## Always

- Brand voice locked per `brand/COHERENCE_CHECKLIST.md` and `docs/00_FOUNDER_CONTEXT.md` Section 7
- Output is drafts for founder review unless founder has explicitly authorized auto-send
- Beta capture model from DEC-001 is the source of truth for pricing/funnel mentions
- Update `FEEDBACK_LOOP.md` with any sign-up signals captured

## Report

Brief one-paragraph status to founder per the action taken.
