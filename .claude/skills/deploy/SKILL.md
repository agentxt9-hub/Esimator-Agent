---
name: deploy
description: Deploy to staging or production. Argument is the target. Runs the deploy script, verifies health, reports status.
argument-hint: [staging|production]
---

# /deploy — Deploy to a target environment

Argument: `$ARGUMENTS` (one of: `staging`, `production`)

## Pre-flight

1. `git status` — confirm clean working tree
2. `git log origin/main..HEAD` — confirm everything is pushed
3. Tests passing — run `pytest tests/` and confirm green
4. If deploying production: confirm staging is currently green and matching production behavior

If any pre-flight check fails, STOP. Report the failure to the founder. Do not proceed with deploy.

## Deploy

### `staging`

SSH to the staging server (or run the staging deploy script if it exists at `deploy/staging.sh` or similar):

```bash
ssh root@<staging-ip>
cd /var/www/zenbid-staging
git pull origin main
bash deploy/update.sh staging
systemctl restart zenbid-staging
```

Wait 30 seconds. Hit the staging URL (`https://staging.zenbid.io` or whatever is configured) and verify it returns 200.

Run smoke tests against staging:
- Landing page loads
- Health endpoint returns 200
- Login page loads
- (If Playwright is configured against staging) `npx playwright test --project=staging`

### `production`

This is high-blast-radius. Confirm with founder before proceeding if not in an established release cadence:

> About to deploy commit [hash] to production. Last staging verification: [time]. Proceed?

On confirmation:

```bash
ssh root@159.203.69.203
cd /var/www/zenbid
git pull origin main
bash deploy/update.sh production
systemctl restart zenbid
```

Wait 60 seconds. Hit `https://zenbid.io`, verify 200. Check Sentry dashboard for fresh errors. Hit health endpoint.

If anything fails: roll back immediately.

```bash
git revert HEAD
git push origin main
ssh root@<server>
cd /var/www/zenbid
git pull
bash deploy/update.sh <target>
systemctl restart zenbid
```

## Report

One paragraph to founder:
- Target deployed (staging or production)
- Commit deployed (hash + title)
- Smoke test results
- Any anomalies observed
- If rolled back: what happened and what was reverted

Update `ORCHESTRATOR_TASK_PLAN.md` with the deploy timestamp.
