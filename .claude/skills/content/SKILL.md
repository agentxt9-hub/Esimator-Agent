---
name: content
description: Generate brand-aligned content. Argument is the type (linkedin | tiktok | youtube | email | landing) optionally followed by a topic or trigger. Pulls from brand voice and recent product changes, generates the content, queues for human review.
argument-hint: [linkedin|tiktok|youtube|email|landing] [optional topic]
---

# /content — Generate brand-aligned content

Argument: `$ARGUMENTS` (type and optional topic; e.g., "linkedin scope-gap-detection" or "tiktok new-feature" or "email weekly-digest")

## Step 1 — Read brand source of truth

Read in order:
1. `brand/COHERENCE_CHECKLIST.md` (locked voice rules) — if not yet built, read `docs/00_FOUNDER_CONTEXT.md` Section 7
2. `brand/demo_script.md` (locked feature framing) — if not yet built, derive from current product state
3. Recent product commits via `git log -10 product/` — for "what shipped" context if no topic specified
4. `gtm/01_EXECUTION_WORKFLOWS/content_generation/[type]_generator.prompt.md` (template, if exists)

## Step 2 — Wear the Content Machine Operator persona

Reference: `docs/launch_prompts/08_CONTENT_MACHINE_OPERATOR.md`

Apply discipline:
- Voice locked to brand
- Never `revolutionize`, `disrupt`, `seamless`, `cutting-edge AI`
- Estimator-native language (`quantities`, `assemblies`, `scope`, `catch what you miss`)
- `Tally` for AI, `Zenbid` in prose, `ZENBID` in logos
- Reference only shipped features, not roadmap claims

## Step 3 — Generate

### `linkedin`
3-5 paragraph post. Hook → pain or insight → demonstration → soft CTA. Voice = founder-coded, not corporate. End with one line of relevant context (e.g., "Building Zenbid in public.").

### `tiktok`
30-60 second video script with:
- Opening hook (first 2 seconds)
- Problem framing
- Demo of the feature in action
- Quick verdict
- Caption + hashtags

### `youtube`
60-90 second short script in same structure as TikTok, plus a slightly longer-form alternate (3-5 min) for the channel.

### `email`
Subject line + body. Voice matches landing. Personalization tokens for first name. CTA matches current funnel state (waitlist / beta / paid).

### `landing`
Specific landing page section refresh (hero / features / CTA / footer). Markdown for the founder to drop into the template.

## Step 4 — Output

Write the generated content to:
- `gtm/02_CONTENT/drafts/[type]_[YYYYMMDD]_[topic-slug].md`

Include at the top:
- Date generated
- Topic / trigger
- Voice constraints applied
- Suggested publish time (or "draft for human review")

## Step 5 — Commit and report

Stage. Commit with `content: [type] — [topic]`. Push.

Reply briefly:
- Content type generated, topic
- File path
- One-line preview (first sentence or hook)
- Suggested next step (publish / iterate / hold)

Continue executing other work unless the founder wants to iterate.
