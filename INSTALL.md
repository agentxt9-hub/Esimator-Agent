# Zenbid Skills Package — Install

## What this is

Claude Code Skills package. Drop in. Launch Claude Code in your repo. Type slash commands. Team executes.

## What's in here

```
.
├── CLAUDE.md                          ← operating brain (auto-loads every session)
└── .claude/
    └── skills/
        ├── kickoff/SKILL.md           ← /kickoff
        ├── status/SKILL.md            ← /status
        ├── sprint-start/SKILL.md      ← /sprint-start
        ├── sprint-close/SKILL.md      ← /sprint-close
        ├── build/SKILL.md             ← /build
        ├── review/SKILL.md            ← /review
        ├── deploy/SKILL.md            ← /deploy
        ├── feedback/SKILL.md          ← /feedback
        ├── decide/SKILL.md            ← /decide
        ├── content/SKILL.md           ← /content
        └── outreach/SKILL.md          ← /outreach
```

## Install (3 minutes)

```powershell
cd "C:\Users\Tknig\Dropbox\ZenBid\Estimator Agent"

# Back up existing CLAUDE.md (it has UI rules etc. you may want to preserve)
Copy-Item CLAUDE.md CLAUDE_legacy.md

# Extract the skills package
tar -xzf zenbid_skills_package.tar.gz --strip-components=1

# Verify the skills landed
ls .claude\skills\
# Should show: build, content, decide, deploy, feedback, kickoff, outreach, review, sprint-close, sprint-start, status

# Verify CLAUDE.md is the new operating brain
# (the legacy version is preserved as CLAUDE_legacy.md — merge UI rules back in later if desired)

# Commit
git add .
git commit -m "init: zenbid skills package — slash commands operational"
git push
```

## Use

Launch Claude Code in the repo:

```powershell
claude --dangerously-skip-permissions
```

Then type:

```
/kickoff
```

That's it. The team starts running.

## The full slash command set

| Command | What it does |
|---|---|
| `/kickoff` | First-time activation. Reads everything, plans, starts Foundation Sprint. |
| `/status` | One-paragraph current state report. |
| `/sprint-start [name]` | Open a new sprint with scope. Founder confirms. |
| `/sprint-close` | Close active sprint with closure ritual + challenge pass. |
| `/build [description]` | Workhorse. Implement a feature, fix, infra, anything end-to-end. |
| `/review [security\|design\|ai\|challenge]` | Run a review pass on recent changes. |
| `/deploy [staging\|production]` | Deploy with pre-flight checks and verification. |
| `/feedback [observation]` | Log founder observation. Triages severity, routes or queues. |
| `/decide [DEC-NNN] [option]` | Resolve a decision from the queue. Unblocks waiting work. |
| `/content [type] [topic]` | Generate brand-aligned LinkedIn / TikTok / YouTube / email / landing copy. |
| `/outreach [optional action]` | Manage outreach playbook and warm-network sequences. |

## How conversation flows

You don't paste prompts. You don't manage sessions. You launch Claude Code, type a slash command, talk to the team.

**Example session:**

```
> /kickoff
[Claude reads everything, gives you a 4-paragraph status, starts working on Track A.1]

> /status
[Claude gives one-paragraph update]

> /feedback the landing page CTA still says "free trial" but we're waitlist-only
[Claude triages → high severity → fixes it → reports back]

> /build add scope gap detection summary to project dashboard
[Claude wears Product Engineer + Frontend persona, implements, tests, commits, pushes, reports]

> /review security
[Claude wears Security Reviewer, audits recent changes, writes verdict file]

> /sprint-close
[Claude verifies exit criteria, runs challenge pass, drafts closure, surfaces next-sprint scope]
```

The team executes. You direct. Period.

## When things go wrong

- **A skill fails or hangs:** kill the Claude Code session, `git pull`, relaunch, type `/status` to re-orient
- **A skill produced something wrong:** `/feedback [what's wrong]` — Claude will triage and fix
- **You want to add a new skill:** create `.claude/skills/<name>/SKILL.md` with frontmatter (`name`, `description`) + body. Restart Claude Code. New skill is live.

## CLAUDE.md merge note

The new `CLAUDE.md` is the v2 operating brain. Your existing one (now `CLAUDE_legacy.md`) likely had UI design rules and other useful constraints. After install, look through `CLAUDE_legacy.md` and merge anything still relevant into the new `CLAUDE.md` (UI rules, design tokens, brand specifics not yet captured). Most of it is probably already covered in the new brain or in `docs/00_FOUNDER_CONTEXT.md`, but a quick read-through is worthwhile.
