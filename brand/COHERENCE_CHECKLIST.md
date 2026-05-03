# Brand Coherence Checklist

**Version:** 1.0 (Foundation Sprint lock)
**Mandatory for:** any surface shipped post-Foundation — landing page, email, social post, demo clip, outreach DM, in-app copy update.

Run every check before marking a surface as "ready." Fail = fix before ship.

---

## Section 1 — Naming conventions

- [ ] Product is called **Zenbid** (not ZenBid, not Zen Bid, not zenbid)
- [ ] AI assistant is called **Tally** (not AgentX, not "the AI", not "our assistant")
- [ ] Logo/mark uses **ZENBID** all-caps only (in logo SVG context)
- [ ] Domain references use `zenbid.io` (lowercase)
- [ ] No competitor names mentioned

---

## Section 2 — Banned phrases

None of these appear anywhere in the surface being reviewed:

- [ ] ~~AI-powered~~ → use "Tally reads the plan", "draft takeoff", "catch what you miss"
- [ ] ~~Seamless~~ → cut entirely or rephrase with a concrete action
- [ ] ~~Revolutionize / disrupt / game-changer~~ → cut
- [ ] ~~Smart / intelligent / cutting-edge / next-gen~~ → cut
- [ ] ~~Build Smarter Estimates, Faster~~ (or close variants) → generic SaaS, cut
- [ ] ~~AI-assisted / AI-driven / AI-enabled~~ → describe the behavior, not the category

---

## Section 3 — Claims and proof

- [ ] No unsubstantiated statistics (no "3x faster", "100% accuracy", "saves X hours" unless sourced from real data)
- [ ] No features mentioned that aren't live in production (no roadmap in outward-facing copy)
- [ ] No customer names or logos unless founder has written permission
- [ ] No fake/placeholder data shown in screenshots or demos ("Welcome back, Alex!", "$2.4M est value", "Medical Office Bldg Chicago" → all banned)

---

## Section 4 — Beta and pricing language

- [ ] **Stage 1 (active now):** CTA says "Reserve beta access" or "Early access — first estimators test free" — no price
- [ ] **No $29/mo language** anywhere until DEC-005 transition criteria are met (3+ users say "I'd pay for this") and founder declares stage 2
- [ ] No "free trial" language (it implies a paid tier that follows automatically)
- [ ] No "early bird pricing" language (implies urgency we haven't earned)
- [ ] If stage 2 is active: $29/mo is correct, "grandfathered" offer available to stage 1 users

---

## Section 5 — Voice and tone

- [ ] Written from the estimator's perspective, not the software's ("your numbers backed up" not "we help you estimate")
- [ ] Plain, specific language — no abstractions ("takeoff" not "project initiation", "line items" not "cost components")
- [ ] Short sentences dominate — max 2 clauses per sentence in hero/CTA copy
- [ ] No exclamation points in body copy (headers and CTAs may use one, never two)
- [ ] No passive voice in CTAs ("Reserve your spot" not "Your spot can be reserved")
- [ ] Founder's voice = direct, confident, trades-knowledgeable, not startup-hype

---

## Section 6 — Surface-specific checks

### Landing page
- [ ] H1 is not generic SaaS copy — it earns a reader who estimates for a living
- [ ] Subhead adds context the H1 doesn't repeat
- [ ] CTA primary button: "Reserve beta access" (stage 1) or "Start beta — $29/mo" (stage 2)
- [ ] No social proof (testimonials, logos, stats) until real data exists
- [ ] Hero visual shows real product UI — no mocks with fake customer data

### Email (welcome, outreach, transactional)
- [ ] Subject line: specific, no generic SaaS subject patterns ("Welcome to Zenbid!" is borderline — preferred: something that earns the open)
- [ ] First sentence does not begin with "I" or the company name
- [ ] Reply-to is a real inbox the founder monitors
- [ ] No unsubscribe friction for cold/warm outreach — include easy opt-out
- [ ] Signature: real name, real title (or none), no boilerplate legal footer in outreach emails

### Social (LinkedIn, TikTok, YouTube shorts)
- [ ] Hook line earns the scroll — one specific problem or moment, not a broad claim
- [ ] Demo clips: real data, real actions, no voiceover that contradicts what's on screen
- [ ] No hashtag spam (max 3 relevant hashtags on LinkedIn)
- [ ] Caption does not restate what the video shows — adds context or CTA

### In-app copy
- [ ] Empty states tell the user what to do, not that nothing is there
- [ ] Error messages describe what to try, not what went wrong in system terms
- [ ] No `str(e)` or stack trace fragments in user-facing strings
- [ ] Tally's responses stay in scope — no hallucinated features or roadmap promises

### Demo script / screen recording
- [ ] Follows `brand/demo_script.md` structure exactly, or departure is explicitly approved
- [ ] No placeholder/fake project data
- [ ] Features shown are live in production at time of recording
- [ ] No pricing mentioned

---

## Section 7 — QA gate before outreach activation

The following must all be checked before tier 1 outreach begins:

- [ ] A.4 monitoring fully verified: Sentry live, Uptime Kuma alerts wired and tested end-to-end
- [ ] B.3 welcome email live and voice-aligned
- [ ] B.4 demo script locked at `brand/demo_script.md`
- [ ] B.5 this checklist exists and is committed

**Outreach gate:** all four items above checked = tier 1 outreach can begin.

---

## How to use this checklist

1. Open a new surface (page, email, post, demo) and a copy of this checklist.
2. Work through every section. Check each item when it passes.
3. Any unchecked item = fix before ship. No exceptions.
4. If a check doesn't apply to the surface type (e.g., "hero visual" for an email) — mark N/A.
5. When all checks pass: ship.

This checklist evolves. If a new banned phrase gets identified, add it to Section 2 and commit. If beta stage transitions to stage 2, update Section 4. The checklist is the source of truth — not memory.
