# Decision Queue

Decisions awaiting founder input. The Orchestrator surfaces decisions here. The founder reads, decides, resolves. Resolved decisions are crossed out (~~strikethrough~~) but kept for historical reference.

---

## Pending

### ~~DEC-001: Beta pricing and capture model~~

**Surfaced:** [program activation]
**Surfaced by:** Orchestrator (initial program setup)

**Original decision (2026-05-02):** Option 2 — Cheap paid beta ($29/mo for first 20 users for 6 months)

**Amended decision (2026-05-02):** 2-stage beta model.

- **Stage 1 (now):** Free reserved beta. Collect emails via `/waitlist`. Founder hand-curates first ~20 from warm network and inbound interest. Early users get free access during validation period in exchange for structured feedback. No charge.
- **Stage 2 (when product validated):** Paid beta at $29/mo. Existing stage 1 users get conversion offer with grandfathered/discount pricing. Open public funnel.

**Reasoning:** Selling $29/mo before the product is validated by real estimators on real bids burns trust faster than a careful free-then-paid sequence. Stage 1 generates validation signal. Stage 2 monetizes it.

**Implication for copy:** No $29/mo language on the landing page or in outreach until stage 2 launches. CTA language: "Reserve beta access." Transition criteria governed by DEC-005.

**Decided on:** 2026-05-02 (amended)

---

### ~~DEC-003: Staging environment location~~

**Surfaced:** 2026-05-02
**Surfaced by:** Orchestrator (Foundation Sprint Day 1)

**Context:** Track A.1 requires a staging environment. Three options were identified: (1) same DigitalOcean droplet as production with separate app directory, (2) separate droplet, (3) managed platform (Fly.io/Render).

**Options:**
1. Same droplet — separate `/var/www/zenbid-staging` dir, separate DB, separate systemd service, separate subdomain. Cheapest; acceptable for beta scale.
2. Separate droplet — full isolation; more expensive; better for production safety.
3. Managed platform (Fly.io/Render) — easiest to provision; some config divergence from production.

**Founder decision:** Option 1 — same-droplet staging
**Decided on:** 2026-05-02

---

### DEC-005: Stage 1 → Stage 2 transition criteria

**Surfaced:** 2026-05-02
**Surfaced by:** Founder (with DEC-001 amendment)

**Context:** DEC-001 establishes a 2-stage beta model. Stage 1 is a free validation period. Stage 2 is paid ($29/mo). The question is what signal triggers the transition — and who decides when it's hit.

**Options:**
1. **(a) Calendar trigger** — e.g., 60 days of stage 1, then evaluate regardless of outcome
2. **(b) Volume trigger** — 10 active stage 1 users using the product weekly
3. **(c) Feedback trigger** — 3+ stage 1 users explicitly say "I would pay for this" (unprompted or in structured feedback)
4. **(d) Founder discretion** — no fixed criteria; founder calls it when it feels right

**Recommended call (founder's):** Option (c) — feedback trigger. Ties the gate to actual validation signal, not arbitrary milestones. Prevents premature monetization. Prevents indefinite free access. The question to stage 1 users: "Would you pay $29/mo for this?" If 3 say yes, the gate opens.

**Founder decision:** *[to be confirmed]*
**Decided on:** *[to be filled]*

---

### DEC-002: Sprint One scope (drafted at Foundation closure)

**Surfaced:** *[Will be surfaced when Foundation Sprint closes]*
**Surfaced by:** Orchestrator (sprint closure)

**Context:** Foundation Sprint closes with `FEEDBACK_LOOP.md` populated by founder walkthrough. Sprint One scope draws from: (a) most-pressing items from founder feedback, (b) Sprint Two items from `docs/06_ENGAGEMENT_PLAN.md` (design system close, AI identity unification), (c) Content Machine + Outreach Operator activation if not blocked.

**Options:** *[to be drafted by Orchestrator at closure]*
**Founder decision:** *[to be filled]*
**Decided on:** *[to be filled]*

---

## Resolved

### ~~DEC-001: Beta pricing and capture model~~

**Final resolution:** 2-stage beta. Stage 1: free reserved access, founder-curated, validation in exchange for feedback. Stage 2: $29/mo paid beta when product validated. Transition criteria: DEC-005.
**Decided on:** 2026-05-02 (amended same day from original Option 2)
