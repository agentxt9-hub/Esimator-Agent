# Mono-Repo Restructure Plan

This document tells you how to restructure the existing `zenbid` repository (`github.com/agentxt9-hub/Esimator-Agent`) into the v2 mono-repo layout — without breaking production, without losing git history, and without disrupting the deployed app.

The current repo has product code at the root. The v2 layout moves product code into `product/` and adds parallel folders for `gtm/`, `brand/`, `tests/`, `deploy/`, `docs/`. We do this as a single, careful, reversible commit.

---

## Production safety first

The production server at `159.203.69.203` runs `/var/www/zenbid` with Gunicorn. Its `app.py` and templates are at the *root* of the deployed copy. Any restructure that moves `app.py` will break production until the deploy script is updated.

**Strategy:** Do the restructure on a feature branch. Update the deploy script in the same branch. Deploy the staging environment first to validate. Only after staging is green do we merge to main and deploy to production.

This means: **the Foundation Engineer provisions staging FIRST, before any restructure happens.** Staging gives us a safe place to test the new layout.

---

## Phase 1 — Foundation Engineer provisions staging (before restructure)

The Foundation Engineer's first task is to stand up a staging environment. This happens on `main` *before* any restructure — staging gets the current flat repo layout, just on a different droplet/database.

1. Provision staging droplet (or staging app on existing infrastructure with separate database).
2. Configure environment: separate database (managed Postgres logical DB `zenbid_staging`), separate domain (`staging.zenbid.io`), separate SSL.
3. Update `deploy/update.sh` (currently at root, will move) to support both `staging` and `production` targets.
4. Smoke-test staging deploy with current flat layout.
5. Document staging environment in `docs/STAGING.md`.

Once staging is live and matches production behavior, we restructure.

## Phase 2 — Branch and restructure

```bash
# From local clone of zenbid
git checkout main
git pull
git checkout -b restructure/mono-repo-v2

# Create new top-level directories
mkdir product gtm brand tests deploy docs

# Move existing files into new structure with git mv (preserves history)
# Product code → product/
git mv app.py product/
git mv routes_takeoff.py product/   # if exists
git mv models.py product/             # if exists
git mv templates product/
git mv static product/
git mv migrations product/            # if exists
git mv requirements.txt product/

# Tests → tests/
git mv test_*.py tests/               # if any at root
# (existing tests/ folder stays as tests/, just merged)

# Deployment → deploy/
git mv update.sh deploy/              # if exists at root
git mv docker-compose*.yml deploy/    # if exists
git mv Dockerfile deploy/             # if exists

# Documentation → docs/
git mv NORTHSTAR.md docs/
git mv DECISIONS.md docs/
git mv CLAUDE.md docs/
git mv SECURITY.md docs/
git mv Agent_MD.md docs/
git mv FEATURE_ROADMAP.md docs/
git mv 00_FOUNDER_CONTEXT.md docs/
git mv 01_STRATEGIC_AUDIT.md docs/
git mv 02_DESIGN_AUDIT.md docs/
git mv 03_TECHNICAL_AUDIT.md docs/
git mv 04_SECURITY_PRIVACY_AUDIT.md docs/
git mv 05_DATA_AI_ARCHITECTURE_AUDIT.md docs/
git mv 06_ENGAGEMENT_PLAN.md docs/
git mv 13_CONVERGENCE_PROTOCOL.md docs/v1_legacy/   # archive v1 design
git mv FOUNDER_ORCHESTRATOR.md docs/v1_legacy/      # archive v1 design

# Brand assets → brand/
# (currently brand assets are inside product/static — keep them there for now;
#  brand/ houses *guidance* and *templates*, not deployed assets)

# GTM → gtm/ (currently empty since GTM was a separate repo plan)
# Will be populated by Content Machine and Outreach Operators
echo "# GTM" > gtm/README.md

# Top-level operating documents
touch ORCHESTRATOR_TASK_PLAN.md
touch FEEDBACK_LOOP.md
touch DECISION_QUEUE.md
touch FOUNDATION_SPRINT.md
# (use templates from this package)
```

## Phase 3 — Update import paths

After moving `app.py` and friends into `product/`, the deploy script and Gunicorn invocation must update.

```bash
# In deploy/update.sh, change:
#   gunicorn app:app
# to:
#   cd product && gunicorn app:app
# OR set PYTHONPATH and stay flat:
#   PYTHONPATH=/var/www/zenbid/product gunicorn app:app

# Also update systemd unit file (zenbid.service) to point at new working directory
```

Update `requirements.txt` location reference in any CI/CD. Confirm the Flask app still finds its templates (they're in `product/templates/` now, which is the default Flask location relative to `product/app.py`).

## Phase 4 — Test on staging

Push the `restructure/mono-repo-v2` branch. SSH to staging server. Pull the branch. Run the updated deploy script. Hit the staging URL and run through the critical paths manually:

- Landing page loads
- Signup works
- Login works
- Project creation works
- AI routes work
- Database connection works

If any of these fail, debug *on the branch* before merging. The branch is the safe space.

## Phase 5 — Merge and deploy to production

Once staging is green:

```bash
git checkout main
git merge restructure/mono-repo-v2
git push origin main

# SSH to production
ssh root@159.203.69.203
cd /var/www/zenbid
git pull
# Run the new deploy script (which is now at deploy/update.sh)
bash deploy/update.sh
systemctl restart zenbid
```

Monitor production for 30 minutes after deploy. If anything breaks, the rollback is `git revert` of the merge commit and re-deploy.

## Phase 6 — Final mono-repo state

After restructure, the repo looks like:

```
zenbid/
├── product/
│   ├── app.py
│   ├── routes_takeoff.py
│   ├── models.py
│   ├── templates/
│   ├── static/
│   ├── migrations/
│   └── requirements.txt
├── gtm/
│   └── README.md (placeholder)
├── brand/
│   └── (will be populated by Frontend/Design Engineer)
├── tests/
│   ├── test_*.py (existing 29 + 99 tests)
│   ├── e2e/ (Playwright, populated by QA)
│   └── api/ (API tests, populated by QA)
├── deploy/
│   ├── update.sh
│   ├── docker-compose*.yml
│   └── Dockerfile
├── docs/
│   ├── PROGRAM_ARCHITECTURE_v2.md
│   ├── NORTHSTAR.md
│   ├── DECISIONS.md
│   ├── CLAUDE.md
│   ├── SECURITY.md
│   ├── Agent_MD.md
│   ├── 00_FOUNDER_CONTEXT.md
│   ├── 01_STRATEGIC_AUDIT.md ... 06_ENGAGEMENT_PLAN.md
│   └── v1_legacy/
│       ├── 13_CONVERGENCE_PROTOCOL.md
│       └── FOUNDER_ORCHESTRATOR.md
├── ORCHESTRATOR_TASK_PLAN.md
├── FEEDBACK_LOOP.md
├── DECISION_QUEUE.md
├── FOUNDATION_SPRINT.md
├── SPRINT_LOG.md (created at first sprint close)
└── README.md (updated to reflect mono-repo)
```

## Rollback plan

If anything goes sideways during or after the restructure:

```bash
# On production:
cd /var/www/zenbid
git revert <merge-commit-sha>
git push origin main
bash deploy/update.sh   # using old structure
# OR if revert is messy:
git checkout <pre-restructure-sha>
# manually deploy
```

Document any rollback in `docs/DECISIONS.md` as an ADR so the team learns.

## Restructure timing

This restructure is **part of the Foundation Sprint, not before it**. The sequence is:

1. Foundation Engineer stands up staging (Day 1–3 of Foundation Sprint)
2. Foundation Engineer ships the eleven Sprint Zero items on the current flat layout (Day 4–10)
3. Foundation Engineer does the mono-repo restructure on a branch (Day 11–14)
4. Test on staging, merge to main, deploy to production (Day 14)
5. The rest of the team starts using the new structure for all subsequent work

This sequencing keeps the high-priority bug fixes from waiting on the restructure, and keeps the restructure from happening on a fragile codebase.
