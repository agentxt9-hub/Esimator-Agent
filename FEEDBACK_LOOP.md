# Feedback Loop

This document captures continuous signal from users (founder + beta), QA automation, content performance, and routing decisions. The Orchestrator appends to this daily. Roles read it to inform their work.

## How this document works

- **Founder feedback** is logged when the founder uses the product or notices anything in chat with the Orchestrator
- **Beta user feedback** is logged when Outreach Operator captures signal from real users (post-Sprint One)
- **QA signals** are logged when Playwright tests fail, Sentry catches errors, Uptime Kuma alerts
- **Content performance** is logged weekly by the Content Machine Operator (post-Sprint One)
- **Routing decisions** are logged by the Orchestrator when feedback gets routed to a specific role/sprint

Entries are timestamped. Old entries are not deleted — they're a historical record.

---

## 2026-05-02 — Foundation Sprint Day 1

### From founder (workflow validation)

- [2026-05-02] Staging confirmed live at https://staging.zenbid.io — separate DB, user pool, SSL, port 8001. Smoke-test passed.

- [2026-05-02] **HIGH — Landing page brand-coherence failures (5 specific items). Blocks outreach activation.**
  1. Hero CTA says "early access is open" + "join the waitlist" — must say "Start beta — $29/mo" (DEC-001 locked paid beta)
  2. Subhead "AI-powered construction estimating" — banned phrase (Section 7 voice rules). Needs estimator-native language ("catch what you miss", "your numbers backed up", etc.)
  3. H1 "Build Smarter Estimates, Faster" — generic SaaS copy. Needs locked voice.
  4. Mock dashboard shows fake customer data ("Welcome back, Alex!", "$2.4M est value", "Medical Office Bldg Chicago") — dishonest on a beta-launch page. Remove or replace with real screenshots.
  5. "3x" and "100%" stats — unsubstantiated. Remove until real metrics exist.
  → Founder: "this MUST ship before any outreach activates. do all changes against staging first, then promote to prod once founder approves."

- [2026-05-02] **LOW — Backlog: deploy/staging-setup.sh has bugs (no postgres detection, nginx server block issues). Not urgent — fix before next staging rebuild.**

### From beta users
*[empty — populates after Sprint One opens beta capture]*

### From QA automation
- 39/39 TanStack + API tests passing
- 99/99 Takeoff tests passing
- `test_login_only.py` requires live server — not part of standard suite; deferred to staging

### From content performance
*[empty — populates after Content Machine activates post-Foundation]*

### Routing decisions made today
- Sprint Zero items (all 11) routed to Foundation Engineer → shipped in single session
- DEC-001 already resolved by founder (paid beta, $29/mo); no routing action needed
- `docs/00_FOUNDER_CONTEXT.md` missing from repo — noted as coverage gap, not blocking Foundation Sprint
