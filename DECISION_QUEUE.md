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

### ~~DEC-005: Stage 1 → Stage 2 transition criteria~~

**Surfaced:** 2026-05-02
**Surfaced by:** Founder (with DEC-001 amendment)

**Options:**
1. **(a)** Calendar trigger — 60 days, then evaluate
2. **(b)** Volume trigger — 10 active weekly users
3. **(c)** Feedback trigger — 3+ stage 1 users say "I would pay for this"
4. **(d)** Founder discretion — no fixed criteria

**Founder decision:** Option (c) — Feedback trigger. Gate opens when 3+ stage 1 users explicitly say "I would pay for this" (unprompted or via structured check-in). Founder calls the transition.
**Decided on:** 2026-05-02

---

### DEC-002: Sprint One scope

**Surfaced:** 2026-05-02
**Surfaced by:** Founder (pre-close direction)

**Context:** Foundation Sprint is closing. Real bottleneck is awareness, not conversion — waitlist funnel mechanics are healthy but zero organic signups. Sprint One must activate outreach. All welcome-mat work (B.3–B.5, A.4 alerts) must land first so strangers have something coherent to land on.

**Proposed Sprint One scope (founder-directed):**

**Track F — Outreach Playbook v1 (Outreach Operator)**
- F.1: Tier 1 playbook — 20–30 warm-network contacts (LinkedIn construction/estimating), personal DM template with demo clip. Gate: B.3 + B.4 + B.5 + A.4 alerts all locked first.
- F.2: Tier 2 content — targeted LinkedIn public posts, faceless brand voice, demo clips of product features actually working. Content Machine Operator.
- F.3: Tier 3 (forum/subreddit/Discord) — explicitly deferred. Too unfocused for stage 1.
- Target: 5+ stage 1 active users by Sprint One close. Transition criteria (DEC-005): 3+ say "I would pay for this."

**Remaining Foundation Sprint carry-over into Sprint One:**
- A.4 notification gap (Uptime Kuma alert end-to-end) — founder action, close first
- B.3 welcome email refresh — in progress
- B.4 demo script lock — pending
- B.5 brand coherence checklist — pending
- A.3 mono-repo restructure — last (low urgency, no user-visible impact)
- C.2 Playwright coverage expansion — parallel
- CI/CD GitHub Actions pipeline — P1 backlog item

**Founder decision:** Confirmed at Foundation Sprint closure (2026-05-03). Sprint One opens with Track F (Outreach Playbook v1) as the primary track. Carry-over items from Foundation Sprint added to Sprint One scope per Challenge Report findings: D.3 (prompt discipline audit, P0), A.4 alert verification (founder action gate), B.1 production promotion (founder action gate), C.2 API security tests (P1), E.1/E.2 founder walkthrough (P1). B.3, B.4, B.5 are shipped; they drop from carry-over. Outreach gate: A.4 alerts verified + B.1 in production + D.3 audited + E.1 walkthrough complete.

**Decided on:** 2026-05-03

---

## Resolved

### ~~DEC-005: Stage 1 → Stage 2 transition criteria~~

**Decision:** Option (c) — Feedback trigger. 3+ stage 1 users say "I would pay for this." Founder calls the transition. $29/mo language returns to landing page and outreach at that point.
**Decided on:** 2026-05-02

---

### ~~DEC-001: Beta pricing and capture model~~

**Final resolution:** 2-stage beta. Stage 1: free reserved access, founder-curated, validation in exchange for feedback. Stage 2: $29/mo paid beta when product validated. Transition criteria: DEC-005.
**Decided on:** 2026-05-02 (amended same day from original Option 2)
