---
name: review
description: Run a review pass on recent changes. Argument is the review type (security | design | ai | challenge). Reads recent commits, applies the relevant checklist, writes a verdict file.
argument-hint: [security|design|ai|challenge]
---

# /review — Run a review pass

Argument: `$ARGUMENTS` (one of: `security`, `design`, `ai`, `challenge`)

## Identify scope

Read:
- `HANDOFF_TO_*.md` files matching the review type (if exists)
- `git log --oneline` for recent commits
- The active sprint task plan

If a hand-off file exists for the review type, that defines scope. Otherwise, scope is the recent commits not yet reviewed.

## Wear the reviewer persona

### `security` — Security Reviewer
Reference: `docs/launch_prompts/06_SECURITY_REVIEWER.md`

Apply checklist:
- `get_project_or_403()` or equivalent on data-touching routes
- `current_user.company_id` matches resource `company_id` checks
- Admin panel scoped to current company or restricted to superadmin
- CSRF tokens on forms
- Generic user-facing error responses (no `str(e)`)
- Secrets from environment, not hardcoded
- Startup gates fail fast on weak/missing secrets
- Session cookies have `HTTPONLY`, `SECURE`, `SAMESITE`
- Open-redirect protection on `next_page`
- AI prompts use labeled delimiters for user input
- Rate limiting on auth-adjacent routes

Output: `SECURITY_REVIEW_NN.md` with verdict per change (Approved / Approved-with-note / Held).

### `design` — Design Reviewer
Reference: `docs/launch_prompts/02_FRONTEND_DESIGN_ENGINEER.md`

Apply checklist:
- CSS variables for all colors (no `#1a1a2e`, `#16213e`, `#0f3460`, `#e94560` — deprecated)
- Brand naming: `Zenbid` in prose, `ZENBID` in logos, `Tally` for AI
- No banned voice (`revolutionize`, `disrupt`, `seamless`, `cutting-edge`)
- Interactive elements have working backend or explicit "coming soon"
- Empty/loading/error states designed
- Focus states on interactive elements
- Semantic HTML

Output: `DESIGN_REVIEW_NN.md` with verdict per change.

### `ai` — Data/AI Engineer review
Reference: `docs/launch_prompts/04_DATA_AI_ENGINEER.md`

Apply checklist:
- `ai_generated=True` on every record AI created
- `estimator_action` set correctly on user actions
- `log_ai_call()` invoked with route, model, tokens, prompt version
- Prompt construction wraps user input in labeled delimiters
- User-review-before-database-write pattern preserved

Output: `DATA_AI_REVIEW_NN.md` with verdict per change.

### `challenge` — Engineering Challenger
Reference: `docs/launch_prompts/07_ENGINEERING_CHALLENGER.md`

Ask:
- What assumption is embedded that nobody named?
- What did exit criteria verify and what did they not?
- What adjacent surface might this affect that wasn't tested?
- What edge case in production data could behave differently than test data?
- What's missing that should have been here?
- Does what shipped match the original scope?

Output: `CHALLENGE_REPORT_NN.md` with observations, what's missing, drift from plan, recommendations for next sprint.

## Commit and report

Stage the review file. Commit with `review(type): NN`. Push.

Reply briefly:
- Number of changes reviewed
- Verdict counts (X approved, Y held)
- Single most important finding
- What the founder should know next (if anything held, route back to the implementing persona via `/build`)
