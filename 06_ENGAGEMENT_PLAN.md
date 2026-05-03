# 06_ENGAGEMENT_PLAN.md — Operating Partner Synthesis and Engagement Plan

**Agent:** Six — Operating Partner (Synthesis)
**Engagement:** Six-Agent Reconnaissance — Zenbid Codebase
**Audits read:** `01_STRATEGIC_AUDIT.md`, `02_DESIGN_AUDIT.md`, `03_TECHNICAL_AUDIT.md`, `04_SECURITY_PRIVACY_AUDIT.md`, `05_DATA_AI_ARCHITECTURE_AUDIT.md`
**Date:** 2026-04-29

---

## Executive Diagnosis

The pattern connecting every meaningful finding across all five audits is this: **documentation has been used as a substitute for closure.** Zenbid's strategic documents are internally coherent, well-reasoned, and specific — they describe a flywheel discriminator live on LineItem, Tally intelligence woven into every surface, a three-surface moat established in the present tense, and a data strategy accumulating from day one. The code says something different. `ai_generated` is never True. Tally exists only as a rename in documents and a set of display constants in `estimate_table.js`. The moat's three components are multiple engineering passes away from existence. The production deploy script has been silently fetching the wrong branch since the repository was renamed from `master` to `main`, meaning the server may be running code that is weeks out of date. These are not minor drift items — they are structural divergences that cause irreversible harm or active security exposure right now.

The two realities coexist because the product development rhythm got out of sequence. Writing the vision before the build is correct practice. Not correcting the documentation when the build diverges from the vision is where the problem compounds: each subsequent session opens with a falsified picture of current state, which causes the next session to build on wrong assumptions about what already exists. The strategic documents became aspirational marketing copy for the codebase's own developers rather than accurate operational references.

The five lenses converge on five categories of risk. First, there is an **active security breach**: every self-service signup receives `role='admin'`, and the admin panel queries all companies and all users across the entire platform with no company scoping. Any Zenbid customer can see every other customer's account today. Second, there is an **irrecoverable data corruption window**: `ai_generated` is never set to True, meaning every AI-generated line item is labeled identically to every human-created one. The flywheel the strategy describes as spinning since Session 22 has never produced a labeled signal. Third, there is a **broken production pipeline**: the deploy script pulls `origin master`; the active branch is `main`; every documented deploy since the rename has silently failed to update the server. Fourth, there is a **legal posture incompatible with a paying customer**: the Privacy Policy and Terms of Service are placeholder strings, there is no disclosed data flow to Anthropic, and there is no consent mechanism for the flywheel's training data program. Fifth, there is a **strategic vacuum** at the market level: the product thesis has no pricing model, no named first customer, no switch story, and no competitive engagement with the counter-evidence that sits uncited in the same repository.

The good news is that the foundation is sound and the interventions are specific. The flywheel fix is one assignment in one route. The deploy fix is one word in a shell script. The admin panel fix is two route queries and a role assignment. None of these require a rewrite. The architecture can support what the documents describe — it simply has not been built to do so yet, and several of the gaps are actively corrupting data or exposing customers right now.

The hardest conversation ahead is not technical. It is the conversation about who pays for Zenbid, what they pay, and what story gets them to open their wallet. That question does not appear anywhere in five documents and six months of engineering work. Every other fix in this plan is executable. That one is not executable until the founder answers it.

---

## Divergence Map

Each divergence has a name, the audits that surfaced it, the underlying condition, and a severity. **High-conviction** designates findings surfaced independently by two or more audits.

---

**D1 — The Flywheel Discriminator Has Never Fired**
*Surfaced by:* Agent Three (Technical, R2 / F1), Agent Five (Data/AI, F1 / F2) **[High conviction — two audits]**
*Underlying condition:* `ai_generated` on LineItem defaults to False and is never overridden by `/ai/apply`, `save_assembly_builder()`, or any AI-facing route. Every row in the production database carries identical provenance metadata regardless of whether a human or the AI created it. `estimator_action='accepted'` is never written anywhere in the codebase — the most important positive flywheel signal is structurally absent. The data accumulated since Session 22 cannot be retroactively labeled. The flywheel described as the product's primary long-term competitive moat has been producing nothing interpretable since it was introduced.
*Severity:* **Critical** — data loss is ongoing and irreversible for each passing day of production AI usage.

---

**D2 — The Admin Panel Exposes All Customers to All Customers**
*Surfaced by:* Agent Four (Security, F1) **[Single audit, confirmed by code — effectively high conviction given zero exploitation sophistication required]**
*Underlying condition:* Self-service signup sets `role='admin'` for every user (`app.py:468`). The `/admin` panel queries `Company.query.all()` and `User.query.all()` without filtering by `current_user.company_id` (`app.py:488-494`). The `admin_new_user`, `admin_delete_user`, and `admin_edit_user` routes accept arbitrary user and company IDs without ownership validation. Any Zenbid customer can enumerate all other customers, modify any user's password, and delete any account. This is not a theoretical risk — it requires no exploitation sophistication.
*Severity:* **Critical** — active breach affecting every account in the system today.

---

**D3 — Production Deploy Has Been Silently Failing**
*Surfaced by:* Agent Three (Technical, R1 / F2), Agent Four (Security, F13) **[High conviction — two audits]**
*Underlying condition:* `deploy/update.sh` line 10 calls `git pull origin master`. The active branch is `main`. The git command exits 0 (success) while making no changes. Every deploy via the documented script since the branch rename has left the production server running stale code. The gap between the committed codebase and what is actually running in production is unknown.
*Severity:* **Critical** — the production server's actual state is unverified and all security fixes committed since the rename may not be live.

---

**D4 — The AI Identity Is "Tally" in Documents and "AgentX" in Every Line of Code**
*Surfaced by:* Agent Two (Design, Section 4c), Agent Three (Technical, D2) **[High conviction — two audits]**
*Underlying condition:* The Pass 1 realignment renamed the AI layer from AgentX to Tally across all strategic documents. Zero code was changed. The tab button reads `🤖 AgentX`. The welcome bubble reads "Hi! I'm AgentX." The mode labels are Estimate/Research/Chat, not Passive/Reactive/Generative. All CSS class prefixes are `ax-`. The TanStack grid defines `AI_STATUS` constants and column schema for Tally Passive but no data populates them. Tally exists only as a documentation event.
*Severity:* **High** — every user-facing AI interaction contradicts the documented product identity. The rename must precede any Tally intelligence wiring.

---

**D5 — The Moat Is Described as Present; None of Its Components Are Built**
*Surfaced by:* Agent One (Strategic, Contradiction 2), Agent Two (Design, Section 5), Agent Three (Technical, D2) **[High conviction — three audits from different angles]**
*Underlying condition:* NORTHSTAR's Strategic Positioning section states in present tense that the moat is "direct measurement-to-line-item flow, Tally intelligence over the top, and dual costing in a single grid." All three components are future work: the Takeoff→Estimate bridge is Pass 3 (Queued), Tally intelligence is Pass 4, and the dual-costing expandable row is a design spike. The present-tense moat claim does not survive contact with a technically informed counterparty.
*Severity:* **High** — strategic messaging risk; also means no planning document currently tracks the gap between "moat claimed" and "moat built."

---

**D6 — The Privacy Policy Does Not Exist While Sensitive Data Flows to Anthropic**
*Surfaced by:* Agent One (Strategic, Silence 7), Agent Four (Security, F5 / F9) **[High conviction — two audits, one at Critical severity]**
*Underlying condition:* `/privacy` returns the string "Privacy Policy — coming soon." `/ai/chat` in estimate mode serializes the full estimate — project location, all assembly names, all line item descriptions, all cost data including material costs and labor rates — into the Anthropic API system prompt. Users are not told this happens. No consent mechanism exists. The flywheel strategy in NORTHSTAR and TALLY_VISION depends on an opt-in consent promise in SECURITY.md that cannot be fulfilled because the Privacy Policy does not exist. No paying customer in any jurisdiction can be onboarded legally in this state.
*Severity:* **Critical** — blocks the first paying customer; active privacy exposure for any current users.

---

**D7 — Zero AI Calls Are Logged Anywhere in the System**
*Surfaced by:* Agent Three (Technical, 3d / F10), Agent Five (Data/AI, F3) **[High conviction — two audits, one at Critical severity]**
*Underlying condition:* Five routes invoke the Anthropic API. None log the call, the user, the company, the token count, the model used, or the response. There is no way to know total AI spend, identify quality degradation, attribute costs by company, or reconstruct what the model was asked for any historical request. Cost runaway and quality degradation are invisible until they are large enough to feel without instrumentation.
*Severity:* **Critical** (AI architecture) / **High** (security and operations) — cost and quality are unobservable.

---

**D8 — Rate Limiting Is Effectively Broken in Multi-Worker Production**
*Surfaced by:* Agent Three (Technical, mentioned in rate limiting context), Agent Four (Security, F4) **[High conviction — two audits]**
*Underlying condition:* Flask-Limiter uses `storage_uri='memory://'`, which means each Gunicorn worker maintains its own independent counter. With `cpu_count() * 2 + 1` workers on a 2-vCPU droplet (5 workers), the effective brute-force limit on `/login` is 50/minute, not 10. `/signup` and `/forgot-password` have no rate limiting at all.
*Severity:* **High** — brute-force protection is fivefold weaker than configured; authentication surfaces are exposed.

---

**D9 — Prompt Injection: User Content Enters AI System Prompts Without Sanitization**
*Surfaced by:* Agent Three (Technical, 3h), Agent Four (Security, F11) **[High conviction — two audits]**
*Underlying condition:* Every AI route builds system prompts via f-string interpolation of user-controlled data — project name, description, assembly names, line item descriptions, and user-submitted chat messages — without sanitization or labeled delimiters. A malicious user can embed instruction-overriding content in these fields. The write path (`/ai/apply`) executes the AI's response as structured data against the database, making a successful injection capable of proposing estimate deletions.
*Severity:* **Medium** (SECURITY.md acknowledged this as H-6; no known exploitation in the wild).

---

**D10 — Hardcoded Credentials and Insecure Defaults Allow Session Forgery**
*Surfaced by:* Agent Three (Technical, noted startup behavior), Agent Four (Security, F7 / F8) **[High conviction — two audits]**
*Underlying condition:* `SECRET_KEY` falls back to `'dev-change-this-in-production-please'` — a known string that allows any party knowing it to forge valid Flask session cookies. `DATABASE_URL` falls back to `postgresql://postgres:Builder@localhost:5432/estimator_db` — committed credentials now public. Neither has a startup gate that fails fast if the environment variable is missing or matches the default.
*Severity:* **High** — session forgery possible if production `SECRET_KEY` is missing or matches default.

---

**D11 — The Document Set Claims One Current State; The Code Reflects Another**
*Surfaced by:* Agent One (Strategic, alignment analysis), Agent Two (Design, Section 7), Agent Three (Technical, Section 2) **[High conviction — three audits, fundamental pattern]**
*Underlying condition:* This is the meta-divergence that explains all others. SECURITY.md describes file upload security as "future" for features live since Session 18. TALLY_VISION.md describes flywheel fields as "✅ live" when `ai_generated` is never True. Agent_MD.md uses "AgentX" in its product vision section despite the realignment that was supposed to remove it. NORTHSTAR claims the moat exists. PROJECT_README.md predates Sessions 18-22 and does not mention Takeoff. The documents have been written to agree with each other but not updated to agree with the code.
*Severity:* **High** — every session that opens with inaccurate operational documentation builds on a false foundation.

---

**Note on Agent Two / Agent Three Disagreement — `index.html`:**
Agent Two (Design) identified `index.html` as "the first authenticated page a user sees" and its design-system mismatch as the audit's most severe finding. Agent Three (Technical) explicitly confirmed that `render_template('index.html', ...)` appears zero times in `app.py` — the live dashboard route renders `app_dashboard.html`, which extends `app_base.html` and uses the current design system. The Technical agent is correct: Agent Two read templates on disk without tracing routes. The dashboard design-system migration is already complete at the route level. `index.html` is a dead file; the correct action is deletion, not migration. The Design agent's urgency framing was based on a false premise about which file is served. This disagreement does not change the Design agent's other findings, which are independently valid.

---

## Triage

### Sprint Zero — Must address before any new feature work

**Admin panel multi-tenancy breach** (Sec F1) — A currently active cross-customer exposure; every new signup inherits admin access to all tenant data. Cannot defer.

**`ai_generated = True` in `/ai/apply` and `save_assembly_builder()`** (Tech F1, AI F1) — One line of code per insertion point. Each day without this fix destroys flywheel signal that cannot be recovered. Highest urgency in the technical set.

**`estimator_action = 'accepted'` write in `/ai/apply`** (AI F2) — The positive flywheel signal has never been captured; same window of irrecoverable data loss as `ai_generated`. Fix alongside the above.

**Production deploy script branch** (Tech F2, Sec F13) — One word change (`master` → `main`). Without it, every subsequent fix in this plan may not reach production.

**`SECRET_KEY` and `DATABASE_URL` startup gates** (Sec F7, F8) — The application should refuse to serve authenticated traffic on a known-weak secret. Three lines of code at startup.

**Open redirect in login `next` parameter** (Sec F2) — One-line fix; allows credential phishing via crafted Zenbid URLs.

**Session cookie security flags** (Sec F3) — Three Flask config lines. `HTTPONLY`, `SECURE`, `SAMESITE`. The application cannot be hardened without them.

**Exception details leaked in API responses** (Sec F6) — Replace `str(e)` with generic error messages and log the full exception server-side. Eight locations.

**`requests` added to requirements.txt** (Tech F3 / Sec note) — A missing declared dependency that fails silently at runtime on first waitlist signup.

**`routes.py` deleted** (Tech F4) — A dead shadow-auth file that would cause catastrophic duplicate route errors if imported. Its presence is a live hazard.

**Migration failure logging** (Tech F7) — Replace the silent `except` block with a single print statement. Failed migrations are currently invisible.

### Near-Term — Next two sprints after Sprint Zero

**Privacy Policy and Terms of Service** (Sec F9, Strat Silence 7) — Required before the first paying customer. Requires legal content, not engineering alone; start immediately alongside Sprint Zero. Not a code change — a content and legal work stream.

**AI call logging table** (AI F3) — An `ai_call_log` table and one shared logging function called by all five AI routes. Adds cost visibility and provides the audit anchor for all future evaluation work. Must exist before the first paying customer generates AI costs.

**Rate limiting Redis backend** (Sec F4) — Replace `memory://` with a Redis-backed store so rate limits apply across the full worker pool. Add limits to `/signup` and `/forgot-password`.

**Gunicorn bind to `127.0.0.1`** (Sec F10) — One config change; closes direct application access that bypasses Nginx security headers.

**Viewer role enforcement** (Tech F12, Sec F15) — The `@viewer_readonly` decorator is documented but does not exist. Implement and apply to all write routes.

**AgentX → Tally rename in user-facing strings** (Des 4c, Tech D2) — Tab button, welcome bubble, mode labels, toast messages. The CSS class prefix `ax-` is internal and can stay.

**Social auth buttons removed or disabled** (Des F3) — The buttons route to 404 errors. Remove them until the routes exist; add a "coming soon" note if desired.

**Landing CTA copy fixed** (Des F2) — "Start your free trial today. No credit card required. Full access to all features for 14 days." linked to `/waitlist` is factually incorrect. The copy should describe the waitlist state.

**`company_id` population in legacy line item routes** (Tech F8) — Items created via legacy routes have `company_id = NULL`. One assignment per route.

**Unify delete semantics** (Tech F5) — The legacy `/lineitem/<id>/delete` route hard-deletes; the TanStack API soft-deletes. Align to soft-delete across all paths or remove the legacy route as part of Pass 3.

**Database indexes** (Tech F6) — `CREATE INDEX IF NOT EXISTS` on `assemblies.project_id`, `line_items.assembly_id`, `users.email`, and `production_rate_standards.trade`. Added to `run_migrations()`. Low effort; large scale-up payoff.

**Model name constant** (AI F7) — Replace the five hardcoded `claude-sonnet-4-20250514` strings with a module-level `AI_MODEL` constant configurable via environment variable.

### Opportunistic — Address within the flow of feature work

**IBM Plex Sans import removed from `estimate_table.html`** (Des F6) — A documented prohibition. Delete the `<link>` tag; no other change needed.

**Disabled Takeoff toolbar buttons** (Des F7) — Hide them or add a hover tooltip. They read as broken features. Address during the next Takeoff work pass.

**Non-functional search and notification bell in top bar** (Des F8) — Remove them or implement them. Placeholder interactive elements train users to ignore controls.

**Design token consolidation** (Des F9) — Three simultaneous token definitions (CSS vars, `ZB` JS object, hardcoded hex in CSS). Address during the next estimate table work pass.

**`company_profile` unique constraint** (Tech F11) — One migration statement. Address in the next migration pass.

**Deprecated `Query.get()` patterns** (Tech 3g) — Low urgency; Flask-SQLAlchemy 3.x still supports them. Migrate to `db.session.get()` during any future session touching those routes.

**Centralized AI client singleton** (Tech F9, AI note) — Move `anthropic.Anthropic()` instantiation to a module-level function. Address in the same pass as the model name constant.

**Scope gap results persistence** (AI F4) — When the estimator confirms a gap, write `ai_status='gap'` and `ai_note=<description>` to the affected items. Address when Tally Passive is wired.

**Validate-rate results persistence** (AI F5) — Write validation findings back to `ai_status`, `ai_confidence`, and `ai_note` on the validated item. Address when Tally Passive is wired.

**`estimate_outcome` field on Project** (AI F6) — One migration statement (`enum won/lost/pending/abandoned`). The UI for marking outcomes can come later; the field should exist before it is needed.

**Consent infrastructure for training data** (AI F9) — A `training_consent` boolean on `Company` (default False) and a UI in company settings. The field must exist before the first customer so the corpus can be legally filtered for fine-tuning.

**Logo upload MIME type validation** (Sec F12) — Low risk in current deployment; add `python-magic` validation during the next file-handling work pass.

**Account deletion route** (Sec F14) — Required for GDPR Article 17; needed before EU customers. Build alongside the Privacy Policy work stream.

**`TakeoffMeasurement` flywheel fields** (AI F12) — Correctly deferred in ADR-026 to Pass 3. This is the hard deadline; not before Pass 3, not after.

**`win/loss` UI for Project outcome** (AI F6 downstream) — A simple estimator-facing UI to mark estimates won/lost. The field (added in Opportunistic above) can sit empty until this UI is built.

**`estimate_table.html` dead file deletion** (Tech 3a) — `estimate.html` (orphaned), `nav.html`, `index.html`, `migration.sql`, root `konva.min.js`. Clean up in Pass 3's legacy retirement sprint.

**Prompt versioning** (AI F8) — A route-to-prompt-version mapping logged with each `ai_call_log` entry. Address when the team wants to run its first A/B prompt test; not before.

### Acceptable / Intentional — Not recommending action

**Monolithic `app.py` at 3,863 lines** (Tech R6) — Single-author codebase; the organizational benefit of refactoring into multiple modules does not exceed the cost at current team size. Revisit only when the team grows beyond two developers working simultaneously. The Takeoff Blueprint is the right precedent — extract new surfaces, not existing routes.

**Synchronous AI calls blocking Gunicorn workers** (Tech Section 5) — At current concurrency levels, synchronous AI responses are acceptable. The 300-second timeout is set for PDF upload, not AI. Revisit when concurrent user load becomes measurable and AI route latency causes observable queuing.

**TakeoffMeasurement flywheel fields deferred** (AI F12, ADR-026) — Correctly acknowledged and deferred. This position is accepted.

**`thumbnail_path` column always NULL on `takeoff_pages`** (Tech D3) — The column exists for future server-side thumbnails. Client-side PDF.js rendering is the correct current approach. The null column costs nothing.

**RAG and vector embedding infrastructure** (AI F10) — No retrieval use case exists with current data volume. The trigger is either context window overflow (a single estimate will not cause this) or cross-estimate historical retrieval becoming a product feature. Do not build before the trigger is clear.

**Fine-tuning infrastructure** (AI note) — Data volume is zero labeled training examples. Consent infrastructure does not exist. Both must precede any fine-tuning investment.

**No TypeScript or build step** (Tech Section 1) — Acceptable at current scale. The CDN + Babel Standalone pattern for the TanStack grid is a technical debt item but not a correctness or security risk. Introduce a build step only when the JavaScript surface complexity justifies it.

**`migration.sql` at repository root** (Tech 3a note) — Historical artifact; harmless. Can be deleted in a cleanup pass but does not warrant its own sprint.

**Social auth implementation** (Des F3 resolution) — Removing the buttons is the right Sprint Zero action. Implementing Google/Microsoft OAuth is a distraction from the primary conversion path (waitlist → first paying customer). Defer OAuth indefinitely until the pricing model and first customer segment are defined.

**zzTakeoff competitive engagement** (Strat Contradiction 4) — The Strategic agent correctly surfaced that the moat claim "No other construction estimating tool does this natively" is made without engaging the zzTakeoff counter-evidence in the same repository. This is a strategic research task, not a code task. The founder should engage it before the moat claim is used in external-facing materials.

---

## Proposed North Star v2

Zenbid is a construction estimating platform designed to run the full estimating workflow — from plan measurement through priced estimate to contractor proposal — inside a single continuous interface. It serves construction estimators: people who currently jump between a takeoff tool, a spreadsheet, and a Word document to complete a single bid. The architectural bet is that eliminating that workflow seam is worth more to estimators than any individual feature improvement inside the three tools they currently use.

The moat that makes this defensible at scale has three components. First, direct measurement-to-line-item flow: a measurement drawn on a plan in the Takeoff surface becomes a quantity in the estimate grid automatically, without copy-paste, unit conversion, or tool switching. Second, dual costing in a single grid: unit-cost entry and assembly build-up coexist line by line without a mode switch, which means a single product can serve electrical estimators who price by unit and concrete estimators who price by crew-day productivity in the same session. Third, a data flywheel: every estimator interaction — accepting an AI-generated row, editing it, rejecting it, marking an estimate won or lost — is a labeled training signal that accumulates into a proprietary cost intelligence dataset no competitor without the same user base can replicate. The flywheel is the long-term moat; the first two components are the conversion argument.

None of the three moat components are fully built. The measurement-to-estimate bridge is Pass 3 work. The dual-costing expandable row is a Pass 3 design spike. The flywheel discriminator has never been set correctly. This plan sequences the work to build all three in order.

**The choices the documents currently dodge, which the founder must make before this plan can be executed against a specific market:**

*First customer:* Who specifically writes the first check — not "construction estimators" as a category, but a named trade, firm size, project type, and current workflow. This choice determines which moat component matters most in the sales conversation, what the pricing structure looks like, and what the first marketing message says. The zzTakeoff Clone Context Doc — filed in this repository and clearly used as an engineering blueprint for the Takeoff module — documents a drywall takeoff workflow in detail. This may indicate where the competitive research was grounded, but it has never been named as a deliberate market entry choice. The founder should name it as such or name something else.

*Pricing model:* What does Zenbid charge, and how does a waitlist signup become a paying customer? Per seat? Per project? Monthly flat? Freemium floor with a paid tier? The answer determines what the trial looks like, what the conversion gate is, and what the unit economics of the flywheel are. Without it, the FEATURE_ROADMAP milestone "first paying customer" has no defined path.

*AI data use disclosure and consent:* The flywheel strategy requires opt-in consent from estimators before their interaction data can be used for training. SECURITY.md states this clearly. The Privacy Policy does not exist. Before these two facts can coexist with a paying customer, the consent mechanism must be designed and the disclosure must be written. This is partly a legal task, partly a product design task, and wholly a strategic commitment: the flywheel only works if estimators opt in, which means the value proposition for opting in must be compelling enough to earn their consent.

*Competitive moat validation:* The claim "No other construction estimating tool does this natively" regarding measurement-to-estimate flow is asserted in NORTHSTAR without engaging zzTakeoff's own measurement-to-cost linkage, documented in the zzTakeoff Clone Context Doc in this repository. The moat may be defensible — Zenbid's architecture may be materially superior — but the claim has not been tested against the counter-evidence. The founder should read Section 18 of the zzTakeoff Clone Context Doc and decide whether the moat claim can stand, needs to be refined, or needs to be argued differently.

---

## Documentation Architecture

The current document set has accumulated across 22 sessions of development without a retirement policy. Nine documents of varying authority and age are cited as mandatory reading in various combinations. The maintenance burden of keeping nine documents consistent is unsustainable and is a root cause of the divergence pattern identified in this audit. The minimum viable set going forward is five documents.

**Documents to keep, with defined scope:**

`CLAUDE.md` — Operating instructions for Claude Code sessions. Contains: stack quick-start, security pre-build checklist, architecture summary, UI rules, known gaps, and the link to `Agent_MD.md` for full reference. This document should be updated only when the architecture changes in a way that affects how sessions open. It is not a sprint log. The session history section is retired — that role moves to `SPRINT_LOG.md`.

`Agent_MD.md` — Master operational reference. Contains: every route, every model, every helper function, and the database schema at its current state. Updated only when routes are added, removed, or changed; when models are added or changed; and when the deployment process changes. Not updated at sprint close for its own sake. The session history section in `Agent_MD.md` is also retired — `SPRINT_LOG.md` takes this role.

`DECISIONS.md` — Architecture Decision Records only. Each ADR documents a choice made, the context, the options considered, and the rationale. ADRs are added when a new architectural decision is made; existing ADRs are never edited except to add a "superseded by ADR-NNN" note. No other content belongs in this file.

`NORTHSTAR.md` — Product philosophy, strategy, and design principles. Absorbs `TALLY_VISION.md` (the merge was already flagged in that document itself). The merged document is the source of truth for: what Zenbid is, who it serves, why it wins, the Tally AI model, the flywheel strategy, surface design rules. Updated only when a strategic direction changes — not as a sprint close ritual. The North Star v2 section of this engagement plan is the basis for the next revision.

`SPRINT_LOG.md` — The new sprint closure surface. One entry per sprint. Fixed format (see Sprint Closure Ritual below). This file absorbs the session history functions of both `CLAUDE.md` and `Agent_MD.md`. It is the only document touched at sprint close in the normal case.

**Documents to retire:**

`TALLY_VISION.md` — Merged into `NORTHSTAR.md`. The document itself flagged this merge as appropriate. Retire after the merge is complete.

`PROJECT_README.md` — Last updated Session 12, predating Sessions 18-22 (Takeoff module, TanStack table, flywheel fields). It is substantially incorrect about the current product. The information it contains that remains accurate belongs in `Agent_MD.md`. Retire without replacement.

`TALLY_VISION.md` (already named), `archive/CLAUDE.md` — Archive files accumulate noise. If a document is superseded, delete it rather than archiving it. Git history preserves superseded content.

**The rule for when a new document is allowed to come into existence:**

A new document is justified only when it covers a scope that none of the five maintained documents own. If the content fits in any of the five documents, it goes there. The only categories that would justify a new document are: a compliance artifact required by an external party (a DPA, a security questionnaire response, an enterprise SOC 2 report); a specification for a component complex enough that the technical detail would distort its host document (a detailed API specification, an LLM evaluation framework); or an engagement artifact for a specific external engagement (such as this document). Operational notes, decision logs, and session histories belong in the five maintained documents. The burden of proof for a new document is high.

---

## Sprint Roadmap

Six sprints plus Sprint Zero. Each sprint is scoped for a focused session or short series of sessions. Exit criteria are binary — the sprint is either complete or it is not.

---

### Sprint Zero — Security and Data Integrity

**Goal:** Stop the active breach, stop the irreversible data loss, make production deployable, and add the startup gates that prevent silent misconfiguration from reaching users.

**Scope:**
- Admin panel: Change self-service signup to assign `role='estimator'`; add a superadmin flag (single internal email or env-configured token) for the admin panel; scope all admin panel queries to `current_user.company_id` or restrict to superadmin entirely.
- `/ai/apply`: Add `ai_generated=True` to every `LineItem` created in the `add_line_items` branch. Add `estimator_action='accepted'` to every item created or updated by the apply route.
- `save_assembly_builder()`: Add `ai_generated=True` to every `LineItem` created by the AI assembly builder save path.
- `deploy/update.sh`: Change `master` to `main` on line 10. Add a `git status` check after the pull that fails the deploy if the working tree is dirty.
- Startup gates: If `SECRET_KEY` equals the default string or is shorter than 32 characters, refuse to start. If `DATABASE_URL` is not set in the environment, refuse to start.
- Open redirect: Validate `next_page` starts with `/` before redirecting. One line.
- Session cookies: Add `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_SAMESITE = 'Lax'` to the Flask config block. Confirm TLS is active before enabling Secure.
- Exception leakage: Replace all `str(e)` in AI route error responses with generic messages; log the full exception server-side (even a `print()` to Gunicorn stdout is sufficient as an interim).
- `requests` in requirements.txt: Add `requests>=2.31,<3.0`.
- Delete `routes.py` from the repository root.
- Migration logging: In `run_migrations()`, add `print(f"Migration failed: {sql[:80]!r} — {e}")` in the `except` block.

**Exit criteria:** Tests pass (29/29 TanStack, 99/99 Takeoff). No authenticated route assigns `role='admin'` on signup. A new user's session cannot reach the admin panel. `ai_generated=True` is set on a test line item created via `/ai/apply`. `estimator_action='accepted'` appears in the database after an apply call. Deploy script succeeds with `git pull origin main`. Application refuses to start on the default `SECRET_KEY`. `routes.py` is gone.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint Zero. No ADRs expected — these are corrections, not architectural decisions.

**Findings addressed:** D1 (ai_generated fix), D2 (admin panel), D3 (deploy script), D10 (startup gates), Sec F2 (open redirect), Sec F3 (session cookies), Sec F6 (exception leakage), Tech F3 (requests), Tech F4 (routes.py), Tech F7 (migration logging).

---

### Sprint One — Legal Foundation

**Goal:** Create the legal foundation that makes it possible to onboard the first paying customer.

**Note:** This sprint has significant non-engineering content (legal copy, privacy policy drafting, DPA review). The engineering scope is small; the content scope is substantial and requires founder input and legal review. Begin alongside Sprint Zero, not after it.

**Scope:**
- Privacy Policy: A real page at `/privacy` that discloses: what personal data is collected, how it is used, that estimate data is processed by Anthropic under their API terms, that data is not used for AI training without explicit opt-in consent, how users can request deletion of their data, and the contact address for data requests. Requires legal review before publication.
- Terms of Service: A real page at `/terms` that covers: acceptable use, limitations of liability, what happens to data on account termination, and the AI assistance disclaimer (AI outputs require estimator review before reliance). Requires legal review.
- AI data flow disclosure: A one-sentence disclosure at the point where AI is first invoked, informing the user that their estimate data will be sent to the Anthropic API. A dismissible banner or a consent checkbox before the first AI call is activated. This is the minimum disclosure; it does not replace the Privacy Policy.
- Consent infrastructure: Add `training_consent` boolean (default False) to the `Company` model. Add a toggle in company settings for "Participate in AI cost intelligence improvement program." No training data is used before this is live.
- Account deletion route: A route at `/account/delete` that anonymizes or purges user PII in `users` and `waitlist_entries` and deletes session tokens. Projects are the customer's data — document the retention policy for project data separately.

**Exit criteria:** `/privacy` and `/terms` return real page content. The signup flow links to both and they resolve. A company-level `training_consent` field exists in the database. A first AI call in a new session displays a disclosure. An account deletion request can be submitted and processed.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint One. ADR if the consent mechanism design introduces an architectural decision.

**Findings addressed:** D6 (privacy / AI disclosure), Sec F5 (Anthropic data flow disclosure), Sec F9 (Privacy Policy / Terms), Sec F14 (account deletion), AI F9 (consent infrastructure).

---

### Sprint Two — Design System Close and AI Identity

**Goal:** Resolve the two-AI-identity problem, fix the false affordances that train users to ignore controls, and close the remaining design system divergences.

**Scope (informed by the disagreement resolution on `index.html`):**
- Confirm `app_dashboard.html` extends `app_base.html` and uses CSS variables correctly. If any deprecated design tokens (`#1a1a2e`, `#e94560`, `#0f3460`) remain in it, correct them.
- Delete dead files: `index.html`, `estimate.html`, `nav.html` (if not used by any live route after verification), `migration.sql` (repository root), root `konva.min.js`.
- AgentX → Tally rename in all user-facing strings: tab button (`🤖 AgentX` → `📐 Tally` or text-only `Tally`), welcome bubble, mode labels (Estimate/Research/Chat → the documented Reactive mode names), toast messages. CSS class prefix `ax-` is internal and does not need to change.
- Social auth buttons: Remove Google and Microsoft auth buttons from login and signup pages. These produce 404 errors. Replace with a note "Additional sign-in options coming soon" if the visual space needs to be filled, or remove entirely.
- Landing CTA copy: Change the "Start your free trial today. No credit card required. Full access to all features for 14 days." copy block so it accurately describes the waitlist state.
- IBM Plex Sans import: Remove the Google Fonts `<link>` tag from `estimate_table.html`. No other change needed — the system UI stack is sufficient.
- Non-functional search and notification bell: Remove from the top bar or implement. The bar should contain only functional elements.
- Disabled Takeoff toolbar buttons: Add a tooltip on hover for each disabled button ("Available after Takeoff→Estimate bridge — Pass 3"). This reads as a planned feature rather than a broken one.

**Exit criteria:** No user-facing string says "AgentX." The tab button, welcome message, and mode labels all reflect the Tally identity. Social auth buttons are gone. Landing CTA is accurate. `index.html`, `estimate.html`, `nav.html` (if confirmed dead), root `konva.min.js`, `migration.sql` are deleted. IBM Plex Sans import is gone from `estimate_table.html`. `app_dashboard.html` uses no deprecated color tokens.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint Two. No ADRs expected — these are corrections.

**Findings addressed:** D4 (AI identity), Des F2 (landing CTA), Des F3 (social auth), Des F6 (font import), Des F7 (disabled buttons), Des F8 (non-functional controls), D11 (documentation/reality divergence — partially).

---

### Sprint Three — Security Hardening

**Goal:** Close the remaining High-severity security findings that do not require architectural work: rate limiting backend, Gunicorn binding, viewer role enforcement.

**Scope:**
- Rate limiting backend: Replace `storage_uri='memory://'` with a Redis-backed URI (`redis://localhost:6379/0` or equivalent). Add `redis` to `requirements.txt`. Add rate limits to `/signup` (`5/minute`) and `/forgot-password` (`3/minute`).
- Gunicorn bind: Change `bind = "0.0.0.0:8000"` to `bind = "127.0.0.1:8000"` in `gunicorn.conf.py`. Verify that `ufw` is active on the server and blocks external access to port 8000.
- Viewer role enforcement: Implement the `@viewer_readonly` decorator (the pattern is specified in SECURITY.md). Apply to all write routes: assembly create/update/delete, line item create/update/delete, library item create/update/delete, all WBS write routes, project update/delete.
- Prompt injection: Wrap user-sourced content in labeled delimiters in all AI system prompts — `<project_name>`, `<description>`, `<line_item_description>` — and strip known control-token patterns from user input before interpolation. This is the fix described in SECURITY.md Part 6.
- Logo MIME validation: Add content-type check on logo uploads using extension allowlist and `imghdr` or `python-magic`.

**Exit criteria:** A viewer-role user receives 403 on all write routes. Rate limits apply across all workers (verify with Redis backend active and multiple workers). Gunicorn is not reachable on port 8000 from an external address. Logo upload rejects a non-image file.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint Three. ADR if the Redis dependency introduces a deployment decision.

**Findings addressed:** Sec F4 (rate limiting), Sec F10 (Gunicorn bind), Sec F11 (prompt injection), Sec F12 (logo MIME), Tech F12 (viewer role).

---

### Sprint Four — Flywheel Instrumentation

**Goal:** Complete the minimum flywheel capture architecture so the system is actually accumulating interpretable training-quality data from every AI interaction.

**Scope:**
- `ai_call_log` table: Add a new model `AICallLog` with fields `user_id`, `company_id`, `route`, `model`, `input_tokens`, `output_tokens`, `created_at`, `prompt_version`. Add to `run_migrations()`. Create a shared helper function `log_ai_call(route, response, user, company, prompt_version)` that writes to this table. Call it in all five AI routes before returning.
- Scope gap persistence: After the estimator confirms a scope gap (when they click "Fix it" or acknowledge a gap), write `ai_status='gap'` and `ai_note=<gap description>` to the affected line items. If the estimator dismisses a gap, write `ai_status='verified'` with no note change (neutral signal).
- Validate-rate persistence: Write the validation result back to `ai_status`, `ai_confidence`, and `ai_note` on the validated line item when `/ai/validate-rate` completes.
- `estimate_outcome` on Project: Add `estimate_outcome` (enum: won/lost/pending/abandoned, nullable) to the `Project` model and `run_migrations()`. Add a UI element in the project header or project settings for the estimator to mark outcome.
- Model name constant: Add `AI_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')` at module level. Replace all five hardcoded strings.
- Centralized AI client: Wrap `anthropic.Anthropic(api_key=api_key)` in a cached module-level getter. The client should be instantiated once, not per request.
- `TakeoffMeasurement` flywheel fields (ADR-026 delivery): Add `ai_generated`, `estimator_action`, and `edit_delta` to `TakeoffMeasurement` via `run_migrations()`. This is the hard deadline for ADR-026.
- `edit_delta` in legacy update route: Add `edit_delta` capture to `update_line_item()` (legacy route) — or confirm that the legacy route is scheduled for retirement in Sprint Five and document the gap.

**Exit criteria:** An AI call creates an `ai_call_log` entry with correct user, company, route, token count, and prompt version. `scope-gap` confirmation writes `ai_status='gap'` to the affected item. `validate-rate` writes to `ai_status` and `ai_note`. `Project` model has `estimate_outcome`. Five AI routes all use `AI_MODEL` constant. `TakeoffMeasurement` has `ai_generated`, `estimator_action`, `edit_delta`. A `training_consent=True` company filters correctly in a simulated corpus query.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint Four. New ADR if the `ai_call_log` table introduces a data retention decision.

**Findings addressed:** AI F3 (call logging), AI F4 (scope gap persistence), AI F5 (validate-rate persistence), AI F6 (estimate outcome), AI F7 (model name constant), AI F8 (prompt versioning foundation), AI F11 (edit_delta in legacy route), AI F12 (TakeoffMeasurement flywheel fields), AI F13 (ai_build_assembly flywheel capture), Tech F9 (centralized client).

---

### Sprint Five — Takeoff → Estimate Bridge (Pass 3)

**Goal:** Connect the two primary product surfaces and retire the legacy estimate infrastructure. This is the sprint that builds the first component of the documented moat.

**Scope:**
The Pass 3 scope is substantial and is defined in FEATURE_ROADMAP.md. Sprint Five executes the following sub-set in priority order:
- Measurement link: A TakeoffMeasurement can be linked to a LineItem (or creates one on commit) — the direct measurement-to-estimate flow that defines the product's core value proposition.
- TanStack table as canonical: Remove the legacy estimate table from `project.html`. The TanStack route (`/project/<id>/estimate`) becomes the only estimate surface accessible via project navigation.
- AgentX panel retirement: Remove `agentx_panel.html` and all `{% include 'agentx_panel.html' %}` references. The AI surface moves to the TanStack grid's Tally stub hooks (see Sprint Six).
- Dual-costing expandable row: Design and implement the expandable row for assembly build-up within the TanStack grid. This is ADR-022's delivery.
- Tally stub hooks on Estimate surface: Place the "Ask Tally" toolbar button (stubs to a coming-soon panel), the Reactive Q&A stub panel (example output only), the Generative entry point button (no intelligence — placement only). These are the wiring anchors for Sprint Seven.
- Legacy route cleanup: Delete or formally deprecate the legacy estimate routes that have been superseded by the TanStack API. Update `Agent_MD.md` route table accordingly.

**Exit criteria:** A measurement drawn in Takeoff appears as a quantity in the estimate grid without copy-paste. The legacy estimate table is no longer served to users. `agentx_panel.html` is deleted. The TanStack grid has a "Tally" toolbar button. Dual-costing expandable rows render correctly. 29/29 TanStack tests pass; 99/99 Takeoff tests pass. New tests for the measurement link are written and pass.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint Five. ADR for the measurement link schema and the legacy route retirement decision.

**Findings addressed:** D5 (moat component one — measurement-to-estimate flow), D4 downstream (Tally surface placement), Des F4 (Tally stub hooks), ADR-025 delivery (Takeoff→Estimate link semantics), ADR-027 delivery (Pass 3 stub hooks).

---

### Sprint Six — Tally Passive Intelligence (Pass 4)

**Goal:** Wire the first live Tally mode — Passive scope gap analysis — so that `ai_status` badges in the estimate grid render with real data for the first time.

**Scope:**
- Backend scope gap analysis: A background or on-demand analysis routine that reads a project's line items, identifies structural gaps (implied assemblies with missing members, division completeness checks), and writes `ai_status='gap'` and `ai_note=<description>` to the affected items.
- Frontend badge rendering: The `AI_STATUS` constants in `estimate_table.js` are already wired to display logic. This sprint populates them with real data from the backend. Badge states `verified`, `suggestion`, `gap`, `live-price` should all render with real data.
- Tally footer banner: Wire the "Review All" button in the Tally banner to the scope gap summary. The banner count should reflect live data.
- Reactive Q&A foundation: Wire the stub Reactive panel from Sprint Five to a real backend endpoint that answers questions scoped to the current estimate. Minimum scope: "What is my total labor exposure on Division X?" answered from project data, not from the LLM. LLM-powered answers in Pass 4 Phase 2.
- Production rate deviation badges: Add `ai_status='suggestion'` when a line item's production rate deviates from the `production_rate_standards` reference by more than a configurable threshold. This is the second Passive mode signal.

**Exit criteria:** A project with a structural scope gap shows `ai_status='gap'` badges in the estimate grid without manual intervention. The Tally footer banner shows a live count of unreviewed gaps. A production rate outside the reference range shows `ai_status='suggestion'`. The "What is my total labor for Division X?" Reactive question returns a correct answer from project data. `ai_status='gap'` writes create `ai_call_log` entries.

**Artifact produced:** `SPRINT_LOG.md` entry for Sprint Six. ADR for the Passive mode analysis architecture (on-demand vs. background job).

**Findings addressed:** D4 fully (Tally intelligence wired, not just renamed), D1 partially (flywheel signals from badge interactions), Des F4 (Tally badges live), AI F4 downstream (scope gap writes), ADR-027 delivery (Pass 4 intelligence wiring).

---

## Sprint Closure Ritual

The goal of the closure ritual is one commit, two files touched in the normal case, and a clean handoff to the next sprint. It must be invocable as a skill at the end of any sprint without variation.

**Step 1 — Run tests.** Every sprint closes on green tests. No exceptions. Run `pytest tests/` (29 tests for the TanStack API) and `python test_takeoff.py` (99 assertions). If either suite has failures, the sprint is not closed — the failures are the sprint's remaining work. Do not commit a sprint closure with failing tests.

**Step 2 — Update `SPRINT_LOG.md`.** Add one entry at the top of the file using this exact format:

```
## Sprint N — [Sprint Name]
**Closed:** YYYY-MM-DD
**Tests:** 29/29 TanStack, 99/99 Takeoff
**Summary:** [One to three sentences. What shipped. What was deferred to the next sprint and why.]
**ADRs added:** [ADR-NNN: title, or "None"]
**Findings addressed:** [Comma-separated list of finding codes from this engagement plan]
```

No other structure. No paragraph explanations. No link to prior documents. The sprint log accumulates entries at the top.

**Step 3 — Update `DECISIONS.md` if and only if an architectural decision was made this sprint.** A new ADR is a decision about how something is built that will constrain future work: which data store, which schema shape, which API design, which third-party dependency. A code correction (changing `master` to `main`, fixing a bug) is not an ADR. Renaming a string is not an ADR. When in doubt, it is not an ADR.

**Step 4 — Update `Agent_MD.md` if and only if routes or models changed.** Only the route table and model list sections. Not the session history section — that role belongs to `SPRINT_LOG.md`.

**Step 5 — Commit with the format `sprint(N): [sprint name] close`.** No other files in the commit. If `Agent_MD.md` or `DECISIONS.md` were updated, they are included. If they were not updated, only `SPRINT_LOG.md` is in the commit.

**Step 6 — Push.** Confirm the push succeeded. The sprint is not closed until the commit is on the remote.

**What is NOT part of the closure ritual:**
- Updating `NORTHSTAR.md` — this changes only when strategic direction changes, not at sprint close.
- Updating `CLAUDE.md` — this changes only when the architecture or operating instructions change, not at sprint close.
- Adding session history to `CLAUDE.md` or `Agent_MD.md` — retired; `SPRINT_LOG.md` owns this.
- Updating `FEATURE_ROADMAP.md` — retired as a sprint-by-sprint tracking document; the Sprint Roadmap in this engagement plan is the reference for sprint sequence; `SPRINT_LOG.md` is the completion record.
- Updating `SECURITY.md` — this changes only when the security architecture changes, not at sprint close.
- Writing a new document — no new document is created at sprint close unless a new scope genuinely has no home in the five maintained documents (see Documentation Architecture section).

The ritual is designed to be quiet because documentation churn at sprint close signals that the documentation is carrying work that should stay in the code or in the `SPRINT_LOG.md` entry. If a sprint close feels like it requires updating many documents, the correct response is to question whether those documents are tracking the right things — not to update them all.

---

## Dev Team Charter

Seven roles. Each is defined by a charge (what it does), a boundary (what it does not do), and a handoff protocol (what it produces and to whom). The charter is intended to be precise enough that the founder can write a launch prompt for any role from this section alone.

---

**Orchestrator**

*Charge:* Reads the engagement plan and the active sprint specification. Breaks the sprint into a sequenced task list with file-level specificity: which file, which function, which behavior to change, which exit criterion it satisfies. Manages the task sequence, identifies dependencies between tasks, and ensures no task is attempted before its prerequisites are complete. Confirms sprint exit criteria are met before closing.

*Boundary:* Does not write code. Does not make architectural decisions — those go to an ADR via DECISIONS.md. Does not override a Security Reviewer hold or a Challenger challenge without naming the reasoning explicitly. Does not re-open findings from prior audits as new tasks.

*Handoff:* Produces a task list in priority order with file paths, function names, and expected behavior changes. Passes to Backend Engineer or Frontend Engineer depending on task scope. After sprint close, produces the `SPRINT_LOG.md` entry draft.

---

**Backend Engineer**

*Charge:* Implements Python-layer tasks in `app.py` and `routes_takeoff.py`: routes, models, migrations, helpers, AI route modifications, flywheel field writes. Owns correctness of business logic, isolation helper usage, and database integrity.

*Boundary:* Does not touch templates or CSS except for Jinja data-passing patterns. Does not make new architectural decisions without surfacing them to the Orchestrator for an ADR. Does not skip calling `get_project_or_403()` or equivalent isolation helpers on any route that touches project data.

*Handoff:* Produces working route code and migration statements. For any route that returns JSON to the frontend: documents the response shape (field names, types, nullable fields) for the Frontend Engineer. Passes AI route changes to the Data/AI Engineer for review before the Security Reviewer sees them. Passes any new write routes to the Security Reviewer for isolation and CSRF review.

---

**Frontend Engineer**

*Charge:* Implements template and JavaScript tasks: Jinja2 templates, vanilla JS `fetch()` interactions, TanStack table modifications, CSS changes. Owns correctness of design token usage, XSS-safe data embedding patterns, and form CSRF token inclusion.

*Boundary:* Does not hardcode hex color values — CSS variables only. Does not import external fonts without explicit approval. Does not add interactive elements (buttons, inputs, links) without confirmed backend routes or confirmed "coming soon" stub behavior. Does not modify `app.py` except to correct template data passed via `render_template()`.

*Handoff:* Produces template and JS changes for Design Reviewer approval before merge. For any new form or fetch POST: confirms CSRF token is correctly included.

---

**Security Reviewer**

*Charge:* Reviews any work that touches: authentication or session handling; isolation helpers or multi-tenancy boundaries; AI prompt construction or user data flowing to external APIs; file uploads; new write routes; rate limiting; environment variable handling. Applies the pre-build security checklist from `CLAUDE.md` to every change in scope. Signals explicit approval or holds work with a specific finding.

*Boundary:* Does not write code. Does not approve work with unresolved isolation gaps, missing CSRF tokens, or `str(e)` in error responses. Does not re-audit prior agents' findings — works only from the current sprint's changes.

*Handoff:* Produces a signed-off list of reviewed changes with approval notes, or a hold with a specific finding and the required fix. Passes approved work to the Challenger. Passes held work back to the Backend Engineer with the specific issue identified.

---

**Data/AI Engineer**

*Charge:* Writes and reviews all code that invokes the Anthropic API, writes to flywheel fields (`ai_generated`, `estimator_action`, `edit_delta`, `ai_status`, `ai_confidence`, `ai_note`), or reads from `ai_call_log`. Ensures `log_ai_call()` is called in every AI route. Ensures `ai_generated=True` is set in every path where the AI creates a LineItem. Ensures `estimator_action` is written correctly for each user action type.

*Boundary:* Does not build AI features that auto-commit without explicit estimator review. Does not prompt the model with user-controlled input that has not passed through the prompt injection sanitization pattern. Does not access cross-company data in AI context construction.

*Handoff:* Reviews Backend Engineer's AI route changes before they reach the Security Reviewer. Produces flywheel capture changes with explicit confirmation of which `estimator_action` value is written in which branch. Passes to Security Reviewer for prompt injection and data flow review.

---

**Design Reviewer**

*Charge:* Reviews any change to templates (`templates/`) or CSS (`static/css/`) against the UI rules in `CLAUDE.md`. Checks for: hardcoded hex colors that should be CSS variables, external font imports, interactive elements without confirmed behavior, brand name variants (only "ZENBID" in logos, "Zenbid" in prose), disabled elements without explanation. Signals explicit approval or flags a specific violation.

*Boundary:* Does not write templates or CSS. Does not approve visual changes that introduce deprecated design tokens (`#1a1a2e`, `#16213e`, `#0f3460`, `#e94560`). Does not expand scope to review non-visual changes.

*Handoff:* Produces an approved or flagged status for each template or CSS change in scope, with the specific rule cited for any flag. Passes approved changes to the Challenger.

---

**Challenger**

*Charge:* Reads the sprint's completed output — code changes, test results, sprint log entry — and asks: what did we miss? What assumption embedded in this work is wrong? What exit criterion is technically met but strategically hollow? What adjacent risk did the work introduce that no one was looking for? Produces a short challenge report with specific observations.

*Boundary:* Does not write code. Does not re-litigate the sprint scope — the sprint is what it is. Does not raise findings from prior audits unless they are directly relevant to something the current sprint changed. Does not block the sprint close — the Challenger's report is an input to the next sprint's scope, not a veto on the current one.

*Handoff:* Produces a challenge report with specific observations. Observations that require action roll into the next sprint's task list via the Orchestrator. Observations that are out of scope for the engagement are flagged for the founder's awareness but not actioned in the sprint sequence.

---

## What We Are Not Doing

The following findings from the five prior audits are explicitly not recommended for action in this engagement plan. Each placement is justified.

**Rewriting `app.py` as a multi-module package** (Tech R6) — The monolith is a single-developer architecture that works correctly and is internally readable. The marginal developer-experience benefit of splitting it does not exceed the migration cost and risk at current team size. The Takeoff Blueprint (`routes_takeoff.py`) is the right precedent: extract new surfaces as they are built, not existing routes.

**Async AI calls and background workers** (Tech Section 5) — Synchronous Gunicorn workers are appropriate at current concurrency levels. No measurement of AI route blocking impact on real users exists yet. The correct trigger for async AI is observable user-facing latency degradation, not architectural preference.

**RAG and vector embedding infrastructure** (AI F10) — No retrieval use case exists with the current data volume. The cost of building embedding infrastructure before the retrieval use case is clear exceeds the cost of adding it when needed. The trigger: estimates grow large enough that context window injection becomes a bottleneck, or cross-estimate historical retrieval becomes a product feature with a named user.

**Fine-tuning model infrastructure** (AI architecture) — Zero labeled training examples exist. Consent infrastructure must be built first. The data does not yet justify the investment. Revisit after six months of flywheel data with training consent active.

**Social auth (Google/Microsoft OAuth)** (Des F3 resolution) — Removing the non-functional buttons is Sprint Two work. Implementing OAuth is a distraction from the primary conversion path. OAuth is a nice-to-have that belongs after the first paying customer, not before.

**TypeScript and build step** (Tech Section 1) — The CDN + Babel Standalone pattern for TanStack is a technical debt item, not a correctness or security risk. The overhead of introducing a Node.js build pipeline is not justified by the current JavaScript surface area.

**Proposal surface Tally intelligence** (TALLY_VISION surface mapping) — Correctly deferred in the documents. The Proposal surface is not designed for Tally in the current roadmap. No sprint in this plan addresses it.

**Production rate deviations via live market data** (Tally Vision, "Live Price" badge state) — The `live-price` badge state is defined in the frontend constants but has no data source. Connecting to live material pricing APIs is a post-launch feature that requires vendor relationships and a pricing strategy. Not in scope for this plan.

**Cross-estimate intelligence and variance analysis** (TALLY_VISION "Future" items) — Named as future in the strategic documents and correctly deferred. This requires flywheel data volume that does not yet exist.

**Named competitive response planning** (Strat Silence 4) — The Strategic agent correctly surfaced the absence of competitive contingency thinking. This is a founder-facing strategic task, not an engineering task. It belongs in a founder-facing business planning session, not in a development sprint.

**Waitlist survey analysis** (Strat Silence 3, Q3) — The survey results appear in no document. Analyzing them is the highest-priority non-engineering task the founder has. It is not a sprint task — it is a founder task that should precede any go-to-market work.

---

## Verdict

Zenbid is closer to a launchable product than the distance between its documented vision and its implemented code would suggest. The foundation is genuinely sound: the multi-tenancy isolation is correctly designed, the schema is right, the dual-costing model is a real architectural insight, and the flywheel field design is precisely correct — just broken on the one most important line. The fixes that matter most are not architectural. They are specific and small: one assignment sets `ai_generated=True`, one word changes `master` to `main`, two route queries get a company filter, and a privacy policy gets written. These are Sprint Zero. They can be done in a single focused session and they eliminate the most severe risks the engagement surfaced.

What the founder needs to confront before Sprint Zero begins is not technical. It is this: the moat described in NORTHSTAR is a roadmap, not a current reality. The flywheel described in TALLY_VISION has been accumulating since Session 22 — but without the discriminator that makes it interpretable, it has been accumulating noise. The product works, but it does not yet do what the documents say it does. That gap is closeable in this engagement plan — the six sprints above will build the moat, wire the flywheel, clean the legal foundation, and connect the surfaces. What the plan cannot close is the strategic vacuum: no pricing model, no named first customer, no switch story. The engineering work can proceed in parallel with the strategic work, but the go-to-market milestone — first paying customer — cannot be hit until the founder can answer who pays, what they pay, and why they stop using what they currently use. That answer does not live in any document in this repository. Writing it is the most important thing the founder can do before Sprint Zero begins.

---

*Agent Six — Operating Partner. File: `06_ENGAGEMENT_PLAN.md`.*
