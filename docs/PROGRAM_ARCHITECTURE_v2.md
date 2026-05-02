# Zenbid Program Architecture v2

This is the operating manual for the Zenbid program. The model: a single mono-repo, a single agentic Orchestrator, eight focused roles, and continuous velocity instead of sprint-cadence convergence. Built for AI-speed execution where engineering ships features in days and content ships same-day.

---

## The mono-repo

Single repository at `github.com/agentxt9-hub/Esimator-Agent` (existing repo, restructured). All work happens here — product, GTM, brand, tests, docs, deployment.

```
zenbid/
├── product/                      Flask app, models, routes, templates, static
├── gtm/                          n8n workflows, content templates, outreach scripts
├── brand/                        design tokens, copy guidelines, demo script
├── tests/                        unit, integration, Playwright E2E, API tests
├── deploy/                       staging + production scripts, docker-compose, CI/CD
├── docs/                         architecture, source material, launch prompts
│
├── ORCHESTRATOR_TASK_PLAN.md     live state of all work (Orchestrator updates daily)
├── FEEDBACK_LOOP.md              user signals, bugs, content performance
├── DECISION_QUEUE.md             decisions awaiting founder input
├── SPRINT_LOG.md                 sprint closure summaries
├── FOUNDATION_SPRINT.md          first-sprint scope (active until closure)
└── README.md                     program overview, repo structure, getting started
```

The reconnaissance audits (`01_STRATEGIC_AUDIT.md` through `06_ENGAGEMENT_PLAN.md`) and `00_FOUNDER_CONTEXT.md` live in `docs/` as primary source material the Orchestrator and roles read.

---

## The eight working roles

### 1. Orchestrator (agentic Claude, daily)

The coordination layer. Runs daily. Reads the entire `zenbid/` tree. Updates `ORCHESTRATOR_TASK_PLAN.md`, `FEEDBACK_LOOP.md`, `DECISION_QUEUE.md`. Surfaces conflicts. Routes work. Drafts sprint closures.

Not a human role. A daily-running Claude session. Eventually wired up as a true cron-driven agent; until then, manually launched daily.

### 2. Foundation Engineer

Owns infrastructure debt, staging environment, deployment safety, best practices. Ships the Foundation Sprint scope: staging env, the eleven Sprint Zero items from `06_ENGAGEMENT_PLAN.md`, mono-repo restructure, logging baseline.

This role activates first and the Foundation Sprint must close before everything else accelerates.

### 3. Product Engineer

Owns feature work post-Foundation. Builds Assembly Builder polish, AI co-estimator improvements, scope gap detection, dual-costing grid. Writes Python, Flask routes, models, business logic. Hands off to Data/AI Engineer for AI-touching code, to Frontend/Design Engineer for UI changes.

### 4. Frontend/Design Engineer

Owns UI, UX, brand coherence. Templates, CSS, JS, design tokens. Ensures landing page, onboarding, in-app copy, demo, email all tell the same story. Uses Claude as design auditor against tokens and brand voice.

This role owns the **brand coherence layer** — the cross-surface continuity that was flagged as a current gap. Landing page promise must match in-app reality.

### 5. Data/AI Engineer

Owns AI routes, Claude prompts, flywheel logging. Reviews any code calling the Anthropic API. Implements `log_ai_call()`, sets `ai_generated`, captures `estimator_action`. Gates AI work before QA.

### 6. QA / Test Automation Engineer

Owns automated testing, monitoring, ticketing. Sets up Playwright for E2E browser tests. Sets up API tests. Sets up Sentry/Uptime Kuma. Maintains and expands the test suite. Catches technical breakage automatically so the founder's feedback can focus on workflow validation.

### 7. Content Machine Operator (GTM, post-Foundation)

Sets up n8n + Claude workflows that watch GitHub commits and generate TikTok scripts, LinkedIn posts, YouTube shorts, email copy, landing page updates. Same-day content shipping. Brand voice locked into prompt templates.

### 8. Outreach Operator (GTM, post-Foundation)

Runs warm-network outreach. Distributes content. Captures beta users. Watches what users actually do. Surfaces signal to FEEDBACK_LOOP.md.

### Plus: Founder (you)

First beta user. Domain expert. Strategic decision-maker. Use the product as a real estimator, log feedback on workflow correctness, resolve decisions from the queue.

### And: on-demand strategic roles

When the Orchestrator detects a need, it invokes one-shot strategic prompts — Market Analyst, Positioning Lead, Pricing Strategist, Brand Messaging Lead, Engineering Challenger, Security Reviewer. These aren't standing roles; they activate when the feedback loop says it's time.

---

## The cadence

### Phase 1 — Foundation Sprint (~2 weeks)

Foundation Engineer ships staging env, fixes bugs, restructures repo. QA Automation Engineer stands up Playwright and monitoring in parallel. Frontend/Design Engineer ships brand coherence layer. Data/AI Engineer wires `ai_call_log` and flywheel writes.

Outcome: clean staging, clean tool, brand-coherent surface, tests passing, monitoring live. Product is ready for founder beta-user testing and the next ten beta users.

### Phase 2 — Continuous velocity (post-Foundation, ongoing)

- Product Engineer ships features, daily commits
- Frontend/Design Engineer ships UI in lockstep
- Data/AI Engineer reviews and ships AI changes
- QA Automation Engineer expands test coverage as features ship
- Content Machine Operator generates content same-day a feature ships
- Outreach Operator distributes content, brings in beta users, captures feedback
- Founder uses product as real estimator, logs feedback
- QA catches bugs automatically and routes tickets
- Orchestrator reads everything daily, updates task plan, routes work, surfaces decisions

The loop runs continuously. Sprints become a soft framing — every ~2 weeks the Orchestrator drafts a closure summary so progress is legible — but they're not gates. Work doesn't pause for sprint boundaries.

### Phase 3 — Beta capture and feedback (starts at end of Foundation)

Outreach Operator opens a low-friction beta gate. Beta users come in. They use the product. QA captures technical signals. Founder validates workflow. Content keeps shipping. Loop tightens.

---

## Decision authority

| Decision | Who decides |
|---|---|
| Daily task routing within a role | Role itself, guided by ORCHESTRATOR_TASK_PLAN.md |
| Cross-role coordination | Orchestrator (reads tree, surfaces conflicts) |
| Sprint closure (every ~2 weeks) | Orchestrator drafts, founder confirms |
| Strategic decisions (pricing, customer pivot, feature priority) | Founder (via DECISION_QUEUE.md) |
| Foundation Sprint scope | Locked in `FOUNDATION_SPRINT.md` |
| Content voice and brand consistency | Frontend/Design Engineer (Claude-audited) |
| AI prompt changes | Data/AI Engineer |
| Test coverage targets | QA Automation Engineer |
| Beta pricing and gating | Founder, surfaced by Orchestrator (DEC-001) |

---

## The founder's role

Time commitment: ~1–2 hours/day during Foundation Sprint, dropping to ~30–60 minutes/day in steady state.

Daily:
- Read `FEEDBACK_LOOP.md` for new signals
- Resolve items in `DECISION_QUEUE.md`
- Use the product (after staging is up); log feedback
- Run the Orchestrator's daily session if not yet automated

Per-sprint:
- Confirm sprint closure drafts
- Approve next sprint scope

Strategic:
- Final voice on brand and product direction
- Pricing decisions, customer pivots, founder-reveal timing

You are the first beta user, not a coordinator standing above streams. The Orchestrator handles coordination. You handle decisions and product validation.

---

## Operating principles

1. **One source of truth.** Everything lives in the mono-repo. Coordination flows through the Orchestrator and the four operating documents.

2. **Roles do role work.** Specialists ship. Orchestrator coordinates. Founder decides. Nobody overlaps.

3. **The flywheel is non-negotiable.** Every AI route writes flywheel signals. Every estimator action is captured. The data network effect is the moat.

4. **Brand coherence before content velocity.** Foundation Sprint locks the cross-surface continuity. Content Machine doesn't activate until brand is coherent.

5. **Continuous velocity, soft sprints.** Work doesn't pause for sprint boundaries. Sprints are observability, not gates.

6. **Founder is first beta user.** The system supports you using the product as a real estimator; QA catches the technical breakage so your feedback can focus on workflow correctness.

---

## When things go wrong

**A specialist's session fails or hangs:** kill terminal, `git pull`, relaunch. Work is checkpointed in commits.

**Production breaks:** revert per `MONO_REPO_RESTRUCTURE.md` rollback plan or `git revert` the offending commit.

**Specialists conflict:** Orchestrator's daily run surfaces to `DECISION_QUEUE.md`. Read, decide, continue.

**Founder feels overwhelmed:** the program is designed for ~1 hour/day in steady state. If it's taking more, the cadence is wrong — flag it to the Orchestrator and the next daily run will adjust.

The teams are agentic. The roles are best-in-class. The operating model is built for AI-speed.
