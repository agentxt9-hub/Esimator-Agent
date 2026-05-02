# ROLLOUT — Day 1 Activation Guide

Step-by-step. Follow in order. Day 1 takes about 2 hours of your time, mostly waiting on parallel sessions.

---

## Step 0 — Extract the package (5 min)

You have `zenbid_v2_package.tar.gz`. Extract it into the root of your local mono-repo.

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"

# Extract the tar (adjust path to where you downloaded it)
tar -xzf "C:\path\to\zenbid_v2_package.tar.gz" --strip-components=1

# Verify the files landed
ls
ls docs/
ls docs/launch_prompts/
```

You should now see:

- `README_PACKAGE.md`, `ROLLOUT.md`, `FOUNDATION_SPRINT.md`, `ORCHESTRATOR_TASK_PLAN.md`, `FEEDBACK_LOOP.md`, `DECISION_QUEUE.md`, `SPRINT_LOG.md` at the repo root
- `docs/PROGRAM_ARCHITECTURE_v2.md` and `docs/MONO_REPO_RESTRUCTURE.md`
- 10 launch prompts in `docs/launch_prompts/`

---

## Step 1 — Commit the package (5 min)

```powershell
git status              # confirm only the new package files are staged
git add .
git commit -m "init: v2 program architecture and Foundation Sprint scope"
git push
```

That's it. Nothing else changes in the repo right now. The mono-repo restructure happens later, on a branch, by the Foundation Engineer.

---

## Step 2 — Resolve DEC-001 (10 min)

Open `DECISION_QUEUE.md`. DEC-001 (beta pricing and capture model) is waiting. Read the three options and pick one.

Edit the file: append your decision under "Founder decision" and "Decided on". Save. Commit.

```powershell
notepad DECISION_QUEUE.md
# decide, save
git add DECISION_QUEUE.md
git commit -m "decide: DEC-001 beta pricing model"
git push
```

This unblocks the Outreach Operator activation later in Foundation Sprint.

---

## Step 3 — Launch Foundation Engineer (Track A) — 5 min setup, 2-3 hour run

Open Terminal #1.

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"
git pull
claude --dangerously-skip-permissions
```

Open `docs/launch_prompts/01_FOUNDATION_ENGINEER.md`. Find the section between `## PROMPT BODY — paste from here` and `## END PROMPT BODY`. Copy that body. Paste into the Claude Code session.

Let it run. It'll take 2–3 hours. You don't have to babysit. Check in occasionally.

---

## Step 4 — Launch QA / Test Automation (Track C) — 5 min setup

Open Terminal #2 (parallel to Terminal #1).

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"
claude --dangerously-skip-permissions
```

Open `docs/launch_prompts/03_QA_TEST_AUTOMATION.md`. Copy the prompt body. Paste.

QA can begin Playwright setup, API test scaffolding, and monitoring infrastructure in parallel — they don't fully depend on Foundation Engineer's staging being live. The full E2E suite waits on staging, but everything else can start now.

---

## Step 5 — Launch Frontend/Design Engineer (Track B) — 5 min setup

Open Terminal #3.

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"
claude --dangerously-skip-permissions
```

Open `docs/launch_prompts/02_FRONTEND_DESIGN_ENGINEER.md`. Copy the prompt body. Paste.

This session works against the current codebase (pre-restructure). Brand coherence work doesn't require staging — landing page, copy audit, demo script can all happen against the current production codebase.

---

## Step 6 — Launch Data/AI Engineer (Track D) — 5 min setup

Open Terminal #4.

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"
claude --dangerously-skip-permissions
```

Open `docs/launch_prompts/04_DATA_AI_ENGINEER.md`. Copy the prompt body. Paste.

D.1 (`ai_call_log` population) and D.3 (prompt construction audit) can start immediately. D.2 (flywheel review) is blocked on Foundation Engineer's Sprint Zero items — that part defers.

---

## Step 7 — Run the Orchestrator's first daily session (10 min)

Wait until the four specialist sessions have at least started producing commits (~30–60 min after launch). Then:

Open Terminal #5.

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"
git pull              # pull whatever the four specialists have committed
claude --dangerously-skip-permissions
```

Open `docs/launch_prompts/00_ORCHESTRATOR_DAILY.md`. Copy the prompt body. Paste.

The Orchestrator reads the tree, populates `ORCHESTRATOR_TASK_PLAN.md` with the actual current state, identifies any conflicts, and posts any decisions to `DECISION_QUEUE.md`.

---

## Step 8 — Read the Orchestrator's output (10 min)

```powershell
git pull
notepad ORCHESTRATOR_TASK_PLAN.md
notepad FEEDBACK_LOOP.md
notepad DECISION_QUEUE.md
```

Read each. The task plan now reflects real state. The decision queue may have new items from cross-role observations.

If anything urgent surfaced, address it. Otherwise, you're done with Day 1.

---

## Day 2–14 — Foundation Sprint runs (1 hour/day from you)

### Each morning (~30 min):

1. `git pull`
2. Read `ORCHESTRATOR_TASK_PLAN.md` — what's in flight, what shipped yesterday, what's blocked
3. Read new entries in `FEEDBACK_LOOP.md`
4. Resolve any pending items in `DECISION_QUEUE.md`
5. Run the Orchestrator's daily session (Step 7 above)

### Each afternoon (~15 min):

1. Check in on each specialist session's status
2. If a specialist ended with a hand-off file (`HANDOFF_TO_*`), launch the next role:
   - `HANDOFF_TO_DATAAI.md` exists → launch Data/AI Engineer for review
   - `HANDOFF_TO_SECURITY.md` exists → launch Security Reviewer (`docs/launch_prompts/06_SECURITY_REVIEWER.md`)
3. Address blockers the Orchestrator flagged

### As soon as staging is up (Day 3–5):

Walk through the product as a fresh user on `staging.zenbid.io`. Log every clunk, friction point, copy mismatch, missing feature into `FEEDBACK_LOOP.md`. The next Orchestrator run picks it up and routes to the right role.

### As tracks complete:

When Foundation Engineer signals A.2 (Sprint Zero items) is complete and tests are green, relaunch Data/AI Engineer to do D.2 (flywheel review).

When Foundation Engineer signals readiness for the mono-repo restructure (Track A.3), launch a fresh Foundation Engineer session pointing them at `docs/MONO_REPO_RESTRUCTURE.md`. That session does the restructure on a branch, tests on staging, merges.

---

## Foundation Sprint Closure (~Day 14)

When all five Foundation tracks have shipped:

1. Launch Engineering Challenger:
   ```powershell
   claude --dangerously-skip-permissions
   # paste docs/launch_prompts/07_ENGINEERING_CHALLENGER.md body
   ```

2. Run the Orchestrator's daily session — it drafts the Foundation Sprint closure entry in `SPRINT_LOG.md`.

3. Read the closure draft. Confirm or push back. If approved, the Orchestrator commits.

4. The Orchestrator surfaces Sprint One scope to `DECISION_QUEUE.md` (DEC-002). You decide what's in scope for the next two weeks.

---

## Post-Foundation: Continuous Velocity (Day 14+)

After Foundation closes, activate the GTM operators and the Product Engineer:

### Activate Content Machine Operator
```powershell
claude --dangerously-skip-permissions
# paste docs/launch_prompts/08_CONTENT_MACHINE_OPERATOR.md body
```

### Activate Outreach Operator
```powershell
claude --dangerously-skip-permissions
# paste docs/launch_prompts/09_OUTREACH_OPERATOR.md body
```

### Activate Product Engineer (Sprint One)
```powershell
claude --dangerously-skip-permissions
# paste docs/launch_prompts/05_PRODUCT_ENGINEER.md body
```

### Daily rhythm shifts:

- Orchestrator runs every morning (10 min)
- Specialist sessions launched as the Orchestrator routes work to them
- Founder reads `FEEDBACK_LOOP.md` and `DECISION_QUEUE.md` daily
- Founder uses the product daily, logs feedback
- Sprint closes every ~2 weeks (soft framing, not hard gate)

---

## What Day 14 looks like if everything works

- `staging.zenbid.io` running cleanly, matching production behavior
- All eleven Sprint Zero items shipped to production
- Mono-repo restructure deployed without incident
- Playwright E2E suite running, monitoring catching errors automatically
- Landing page, in-app copy, welcome email all tell the same story (brand coherence locked)
- Founder has used the product end-to-end as a real estimator and logged friction
- All four operating documents populated with real state
- DEC-001 resolved; beta capture funnel ready
- Sprint One scope drafted and ready for founder approval (DEC-002)
- Content Machine workflows scoped and ready to deploy
- Outreach Playbook drafted and ready to fire

Then continuous velocity begins. Content ships daily. Beta users come in. The feedback loop runs.

---

## When things go wrong

- **Sessions hang or fail:** kill terminal, `git pull`, relaunch. Work is checkpointed in commits.
- **Production breaks during restructure:** revert the merge per `docs/MONO_REPO_RESTRUCTURE.md` rollback plan.
- **Specialists conflict:** Orchestrator's daily run will surface to `DECISION_QUEUE.md`. Read, decide, continue.
- **Founder feels overwhelmed:** the program is designed for ~1 hour/day in steady state. If it's taking more, flag it to the Orchestrator and the next daily run will adjust.

The teams are agentic. The roles are best-in-class. The operating model is built for AI-speed. You're the founder, the first beta user, and the strategic decision-maker. The system runs.

🚀 Time to fire it up.
