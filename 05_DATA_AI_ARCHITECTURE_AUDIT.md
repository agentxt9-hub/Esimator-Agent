# 05_DATA_AI_ARCHITECTURE_AUDIT.md — Zenbid Data and AI Architecture Audit

**Engagement:** Six-Agent Reconnaissance — Agent Five (Data and AI Architect)
**Date:** 2026-04-29
**Scope:** Full codebase read through a data and applied-AI lens. No application executed.
**Files read:** `app.py` (3,863 lines), `routes_takeoff.py`, `static/js/estimate_table.js`, `TALLY_VISION.md`, `NORTHSTAR.md`, `DECISIONS.md` (ADR-001 through ADR-027), `requirements.txt`.

---

## Orientation

**Database technology:** PostgreSQL via SQLAlchemy ORM. Schema managed through `run_migrations()` — a handwritten block of `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements executed at startup. No Alembic, no migration history, no rollback.

**Documentation files touching AI strategy:** `TALLY_VISION.md` (primary AI and flywheel specification), `NORTHSTAR.md` (product philosophy, flywheel architectural principles), `DECISIONS.md` (ADR-001 through ADR-027, including ADRs 021, 022, 024, 025, 026, 027 which are directly flywheel-relevant).

**Python modules invoking the AI provider:** All invocations are in `app.py`. The `anthropic` library is imported at the top (line 23). Five routes call `client.messages.create()`:
- `ai_chat()` at line 2717 — conversational + write proposal
- `ai_build_assembly()` at line 2988 — generative assembly from description
- `ai_scope_gap()` at line 3278 — scope gap analysis
- `ai_production_rate()` at line 3433 — production rate lookup
- `ai_validate_rate()` at line 3544 — production rate validation

**Fields or surfaces called out as flywheel-critical in documentation:** `ai_generated`, `estimator_action`, `edit_delta`, `ai_status`, `ai_confidence`, `ai_note` on `LineItem` (TALLY_VISION.md Section: Data Flywheel). `ai_generated`, `estimator_action`, `edit_delta` on `TakeoffMeasurement` (ADR-026 — deferred to Pass 3).

**Immediate surprises:**
- `ai_generated` is defined in the schema and documented as live. It is never set to `True` by any route in the codebase. Every LineItem in the database has `ai_generated=False` regardless of whether a human or the AI created it.
- `estimator_action='accepted'` is never written. The most important positive signal in the documented flywheel is structurally uncaptured.
- Five distinct AI routes make calls to the Anthropic API. Not one of them logs the call, the tokens used, the cost, the prompt, or the response.
- The `/ai/scope-gap` route returns gap analysis to the frontend but writes nothing back to the database — the AI's assessment of which items are gaps is not persisted anywhere.

---

## Documented Strategy

`TALLY_VISION.md` and `NORTHSTAR.md` together describe an AI layer called Tally that operates in three modes: Passive (always watching, surfaces observations without prompting), Reactive (on-demand Q&A and reports), and Generative (natural-language line item creation requiring explicit estimator review). The strategy is explicit that every Tally interaction is a training signal and must be captured from day one, passively, without requiring estimators to categorize their own work.

The data flywheel is defined precisely. When an estimator accepts an AI-generated row, that is a strong positive signal. When they edit it, the delta between AI output and human ground truth is the signal. When they reject it, that is a negative signal. When an estimate is marked won or lost, that outcome propagates backward to all contributing line items. The schema for capturing these signals is documented as live as of Session 22: `ai_generated`, `ai_confidence`, `estimator_action`, `edit_delta`, `ai_status`, `ai_note` are all on `LineItem`. The TALLY_VISION.md document states: "This data accumulates into a proprietary cost intelligence dataset. At sufficient volume, it becomes the foundation for fine-tuning an LLM on contractor-sourced cost data."

What the strategy requires the architecture to do today is straightforward: every time a row is written to the database, the system must correctly tag whether it was AI-generated or human-generated, and every time an estimator acts on an AI-generated row, the system must record the action and the delta. This is the minimum viable flywheel — the data that must be clean from day one because retroactive labeling is impossible. What the strategy requires the architecture to be ready for tomorrow is an evaluation and feedback loop that can tell the team whether Tally's outputs are improving or degrading over time, a retrieval layer that can ground AI responses in historical estimates, and an opt-in mechanism that can filter the corpus before any fine-tuning.

---

## Data Capture Map

**14 tables mapped. Flywheel-critical fields traced from schema definition through every write path.**

### `companies` (2 flywheel-relevant fields: none)
No flywheel fields. Acts as tenant root. No AI-relevant capture needed here.

### `users` (flywheel-relevant fields: none)
No flywheel fields. No per-user AI consent or opt-in flag. The absence of a consent flag is a future problem: the flywheel strategy describes an opt-in program for training data, and opt-in state will need to live somewhere per company or per user when that feature is built.

### `projects` (flywheel-relevant fields: 0 of 1 needed)
No flywheel fields on the `Project` model. The most critical missing field at the project level is `estimate_outcome` (won/lost/pending/abandoned). `TALLY_VISION.md` acknowledges this is not yet added. An estimate marked Won is described as "strong positive on all contributing line items" — but without a win/loss field on the project, that signal can never be captured, even in Pass 4.

### `assemblies` (flywheel-relevant fields: none)
No flywheel fields. `is_template` boolean is structural, not flywheel. `measurement_params` is a JSON blob for assembly measurements. No AI-generated flag at the assembly level, which is a gap: `/ai/build-assembly` generates complete assemblies but there is no way to tag an assembly as AI-generated vs. human-built.

### `line_items` (flywheel-relevant fields: 6 defined, 2 populated, 4 non-functional)

This is the core flywheel table. The six fields and their actual write paths:

**`ai_generated` (Boolean, default False)**
Defined at `app.py:224`. The only write paths in the entire codebase:
- `api_create_line_item()` (line 1314): explicitly sets `ai_generated=False`
- `_make_line_item_from_form()` (line 930): does not set the field; defaults to False
- `save_assembly_builder()` (line 1605-1616): creates LineItem objects; does not set the field; defaults to False
- `/ai/apply` (line 2857-2877): creates LineItem objects from AI proposals; does not set the field; defaults to False

**The field is never set to True by any code path.** The route that creates AI-generated line items (`/ai/apply`) silently defaults the discriminator to `False`. Every row in the production database has `ai_generated=False` regardless of its actual provenance. The flywheel's ability to distinguish AI output from human input is zero.

**`estimator_action` (String, nullable)**
Defined at `app.py:225`. Write paths:
- `api_patch_line_item()` (line 1369): sets `'edited'` when any field changes via TanStack PATCH
- `api_delete_line_item()` (line 1386): sets `'rejected'` when soft-deleted via TanStack DELETE
- `api_create_line_item()` (line 1299-1315): field not set; null on creation
- `/ai/apply` (line 2745-2880): field not set on any of the four action types (update, delete, bulk update, add)
- Legacy routes (`update_line_item`, `delete_line_item`, `new_line_item`): field not set

The value `'accepted'` — the most important positive signal in the documented flywheel — is never written anywhere in the codebase. The value `'ignored'` is never written. `'edited'` and `'rejected'` are only captured through the TanStack API, not through legacy routes or the `/ai/apply` route. This means estimator actions performed through the AI panel (the primary AI surface) are not captured as flywheel signals.

**`edit_delta` (Text/JSON, nullable)**
Defined at `app.py:226`. Write paths:
- `api_patch_line_item()` (lines 1341-1373): correctly captures before/after values as JSON for all PATCH fields via TanStack. Implementation is correct.
- All other write paths: field not set; remains null

The capture is technically correct for TanStack PATCH operations. However, since `ai_generated` is never True, the `edit_delta` field cannot serve its intended purpose — distinguishing an estimator's correction of an AI-generated value from a routine human edit. The data captured is structurally sound; its interpretation is broken by the `ai_generated` failure.

**`ai_status` (String, default 'verified')**
Defined at `app.py:219`. Write paths:
- `api_create_line_item()` (line 1311): hardcodes `'verified'`
- No other route updates `ai_status` after row creation
- `/ai/validate-rate()` (line 3462): validates a production rate and returns an assessment, but does not update `ai_status` on the item
- `/ai/scope-gap()` (line 3104): returns gap findings but does not update `ai_status` on any item

The four badge states (`verified`, `suggestion`, `gap`, `live-price`) are defined in `estimate_table.js` lines 42-47. The display code is live and renders correctly. The intelligence layer that would transition rows between states is not wired. All rows in the production database show `ai_status='verified'` at all times.

**`ai_confidence` (Integer, default 100)**
Defined at `app.py:220`. Write paths:
- `api_create_line_item()` (line 1312): hardcodes `100`
- No other route updates this field

The field is always 100. No AI route ever writes a non-100 value.

**`ai_note` (Text, nullable)**
Defined at `app.py:221`. Write paths: none. The field is defined, migrated, returned in API responses, and displayed in the `AiBadge` tooltip hover state in `estimate_table.js:147`. No route ever writes to it.

### `assembly_composition` (flywheel fields: none)
No flywheel fields. Records the formula-based composition of assemblies. No AI provenance tracking.

### `library_items` (flywheel fields: none)
Company-scoped reusable item library. No AI provenance. No usage tracking. Library items used via the assembly builder could contribute to flywheel data (which items are used most, which rates are edited after use) but this surface is not instrumented.

### `production_rate_standards` (flywheel fields: none)
Global reference rates, seeded at startup. Read-only by design. The `/ai/validate-rate` route uses these as reference data. When the AI's validation reveals that a rate is outside the database range, neither the database record nor the line item is updated to reflect the finding.

### `takeoff_plans`, `takeoff_pages` (flywheel fields: none)
No flywheel fields. `TakeoffPage.scale_method` contains `none|manual|ai` — a nascent tracking field for scale calibration method, but it is always set to `'none'` by the upload route (`routes_takeoff.py:155`) and no code path sets it to `'ai'`.

### `takeoff_items` (flywheel fields: none needed)
Tracks measurement tool definitions (type, color, width). No AI provenance needed here; the measurement itself is the flywheel data point.

### `takeoff_measurements` (flywheel fields: 0 of 3 planned)
`TakeoffMeasurement` contains: `id`, `item_id`, `page_id`, `points_json`, `calculated_value`, `calculated_secondary`, `measurement_type`, `created_at`. The three flywheel fields (`ai_generated`, `estimator_action`, `edit_delta`) are called out in ADR-026 and TALLY_VISION.md as deferred to Pass 3. They are correctly documented as not yet present. No gap here; this is an acknowledged future migration.

### `wbs_properties`, `wbs_values`, `line_item_wbs` (flywheel fields: none)
Work breakdown structure. Not flywheel-critical at this stage.

### `waitlist_entries`, `waitlist_surveys` (flywheel fields: N/A)
Marketing funnel data. Not product flywheel.

---

## AI Integration Architecture

Five routes call the Anthropic API. None share infrastructure, utility functions, client instances, logging, cost tracking, or evaluation hooks. The integration pattern is identical across all five and is as follows: retrieve API key from environment, instantiate a fresh `anthropic.Anthropic(api_key=api_key)` client, construct a system prompt (via f-string interpolation of database data), call `client.messages.create()`, handle the response, return to the caller. The implementation is scattered and structurally identical — not centralized, not abstracted, not swap-ready.

**`/ai/chat` (line 2513):** The most user-facing route. Builds a system prompt from the full project context (project metadata, all assemblies, all line items with cost data, production rate standards) when in `estimate` mode. Accepts a free-text user message. Returns a reply and an optional `write_proposal` JSON block extracted from the response via regex. The write proposal is then applied by the separate `/ai/apply` route. The route does not log the call, the prompt, the response, the user, the company, or the token count. The model is hardcoded as `claude-sonnet-4-20250514`.

**`/ai/apply` (line 2745):** Applies the write proposal from `/ai/chat`. Four action types: `update_line_item`, `update_assembly`, `delete_line_item`, `bulk_update`, and `add_line_items`. The `add_line_items` path creates LineItem records at lines 2857-2877 without setting `ai_generated=True`. No AI call is made within this route — it executes structured data from the previous `/ai/chat` response. This is the correct design pattern; the gap is only in the missing `ai_generated` flag.

**`/ai/build-assembly` (line 2883):** Accepts a scope description and returns a fully-computed assembly with line items. This route does not persist anything to the database — it returns the computed result for frontend review. The frontend (via the assembly builder UI) would then save the result through `save_assembly_builder()` at line 1547, which does not set `ai_generated=True`. The route does not log the call. The model is hardcoded.

**`/ai/scope-gap` (line 3104):** Sends the full project estimate to the model for scope gap analysis. Returns a JSON object with `summary`, `completeness_score`, `gaps`, `strengths`, and `review_notes`. The gaps are returned to the frontend for display. No gap is persisted to the database — neither as `ai_status='gap'` on an existing line item nor as a new record. The estimator sees the analysis; the system learns nothing from whether they acted on it. Model hardcoded.

**`/ai/production-rate` (line 3332):** Answers a natural-language production rate question using the `production_rate_standards` table as grounding data. Returns structured rate recommendations. Nothing is written back to the database. If the AI surfaces a rate that the estimator then uses, that usage is not captured. Model hardcoded.

**`/ai/validate-rate` (line 3462):** Validates a specific line item's production rate against database standards and the model's knowledge. Returns `is_reasonable`, `assessment`, `explanation`, `recommendation`. Does not update `ai_status`, `ai_confidence`, or `ai_note` on the validated line item. The validation result evaporates the moment the user closes the response. Model hardcoded.

**What is absent across all five routes:**
- No request logging (user_id, company_id, route, timestamp, token count)
- No response storage (prompt + response pairs are never persisted)
- No cost instrumentation (no way to know how much each company or each route is costing)
- No prompt versioning (prompts are constructed inline as f-strings; no template IDs, no version numbers)
- No model versioning beyond the hardcoded string (five separate hardcoded occurrences of `claude-sonnet-4-20250514`)
- No evaluation hooks (no mechanism to flag outputs as good or bad, correct or incorrect)
- No shared client instance (a new `anthropic.Anthropic()` is instantiated per request)

**Swap readiness:** The integration is not swap-ready. Replacing the model requires finding all five hardcoded strings in `app.py`. Versioning prompts requires extracting and parameterizing five inline f-strings. Adding evaluation requires adding hooks at five separate points. The work is not architecturally blocked — the routes are short and clear — but it is not centralized in any way that would make a model swap or evaluation addition a one-place change.

---

## Flywheel Readiness

The flywheel is not firing. Not partially. Not slowly. The primary discriminator field — `ai_generated` — has never been set to `True` by any route in the codebase. Every row produced by the AI has the same value on this field as every row entered manually by an estimator. The two are indistinguishable in the database. Any query today that attempts to compute flywheel metrics — "what fraction of AI-generated rows are edited?", "which AI-suggested production rates are consistently corrected by estimators?", "what is the accept/edit/reject distribution on AI output?" — would return meaningless results because the AI-generated label does not exist.

The secondary signals are also broken. `estimator_action='accepted'` is never written, meaning the most important positive feedback loop is never captured. When an estimator opens `/ai/apply` and approves an AI-generated assembly, the system records no event. The assembly appears in the database indistinguishable from one the estimator built by hand.

The fields that are correctly implemented are `edit_delta` (captured accurately for TanStack PATCH) and `estimator_action='edited'` and `estimator_action='rejected'` (captured for TanStack PATCH and soft-delete). These two are working correctly in isolation but are rendered strategically useless by the `ai_generated` failure — without knowing which rows were AI-generated, there is no way to interpret what the edits and rejections mean as flywheel signals.

The root cause is a single missing assignment in `/ai/apply` at line 2857-2877 and in `/ai/build-assembly`'s downstream save path. The fix is one line of code per insertion point. But the data lost since Session 22 — every AI-generated row created since the flywheel fields were introduced — is irrecoverable as labeled training data. Existing rows cannot be retroactively labeled as AI-generated because the information was never recorded.

---

## Fine-Tuning and Retrieval Readiness

**Fine-tuning readiness (18-month horizon):** The schema shape is correct. LineItem contains the fields needed to reconstruct a training example: description, quantity, unit, production rate, material cost, labor rate, CSI division, trade, project context via foreign key. The assembly structure provides grouping context. In principle, a corpus of "human-reviewed-and-approved" estimates is exactly what a fine-tuning dataset for a construction cost estimation model would look like.

What makes fine-tuning impossible from the current data: the `ai_generated` field is always False, meaning there is no way to construct a dataset of "AI output / human correction" pairs — the canonical input-output pairs for preference fine-tuning. What would be possible is building a dataset of "complete estimate structures" (for a completion-style fine-tune) or "project context + line items" (for a retrieval-grounding fine-tune). But both of these require being able to distinguish high-quality human estimates from AI-influenced ones, and that distinction does not exist in the current data.

The consent infrastructure for fine-tuning does not exist at all. No per-company opt-in flag, no consent event log, no way to filter a training corpus to only consenting customers. Building this before any customers have consented means the mechanism exists when it is needed rather than being retrofitted after growth makes it complex.

**RAG readiness (12-month horizon):** The data is structured in retrievable units. A LineItem with its assembly, project, and CSI context is a natural retrieval document. The schema supports retrieval without structural changes. What does not exist is any embedding infrastructure: no vector column on any table, no separate vector store, no embedding generation pipeline, no retrieval query pattern.

The current AI integration uses the full estimate as a context injection (stuffed directly into the system prompt). This works at small scale — a single estimate with dozens of line items is well within context window limits. At larger scale — cross-estimate retrieval ("what did we cost Division 03 at on similar commercial office projects last year?") — the current injection approach fails because the context window cannot hold thousands of historical line items. RAG is the natural solution, but no infrastructure for it exists. The minimum addition that locks in readiness is a `pgvector` extension on the PostgreSQL cluster and an `embedding` column on key tables (LineItem or Assembly), populated by a background job that calls an embedding API.

---

## Evaluation and Feedback Loop

There is no evaluation or feedback loop of any kind today. Nothing is captured that would tell the team whether AI output quality is improving or degrading over time.

**What is captured today that is evaluation-relevant:**
- `edit_delta` on TanStack PATCH operations: if `ai_generated` were True, these deltas would be exactly what an evaluation harness would ingest — the ground truth correction the estimator applied to the AI's output.
- `estimator_action='rejected'` on soft-delete: negative signal, correctly captured.
- `estimator_action='edited'`: partial signal, correctly captured.

**What is missing:**
- `ai_generated=True`: without this, the captured signals cannot be attributed to AI output.
- `estimator_action='accepted'`: the positive signal.
- Any logging of AI prompts and responses: there is no way to reconstruct what the model was asked or what it answered for any historical request.
- Any win/loss field on Project: the outcome signal that would allow correlation between estimate quality and bid results.
- Any mechanism to flag an AI response as helpful or not: the scope gap analysis, the production rate recommendation, and the rate validation all return results to the user with no feedback path.

**Minimum capture that would unlock evaluation without a backfill:**
1. Fix `ai_generated=True` in `/ai/apply` and in any downstream save path from `/ai/build-assembly`. This is one line of code per insertion point and unlocks all future interpretation of `edit_delta` and `estimator_action`.
2. Write `estimator_action='accepted'` when a user applies an AI proposal without modification. This would happen in `/ai/apply` — if the user invokes apply at all, that is acceptance of the proposal.
3. Add an `ai_call_log` table: `id`, `user_id`, `company_id`, `route`, `model`, `prompt_tokens`, `completion_tokens`, `created_at`. Populate it in every AI route. This enables cost attribution and provides the request-level anchors that would make prompt/response retrieval possible later.
4. Add `estimate_outcome` (enum: won/lost/pending/abandoned) to the `Project` model. This is the outcome signal the strategy describes as a strong positive.

These four changes are small, not architecturally disruptive, and must happen before any evaluation infrastructure can be meaningful.

---

## Phasing Recommendation

The sequencing logic here is governed by one constraint: flywheel data that is not captured at the moment of the action is lost permanently. A recommendation to "add logging in Phase 3" is a recommendation to write off all Phase 1 and Phase 2 interactions as irrecoverable from a training perspective. The cost of correct capture now is one to five lines of code. The cost of not capturing now is a permanently polluted corpus.

**Bake in now (before any AI routes serve real customers):**
The `ai_generated=True` fix. The `estimator_action='accepted'` write in `/ai/apply`. An `ai_call_log` table and a single shared logging function that all five AI routes call before returning. These are not architectural investments — they are bug fixes in the context of the documented strategy. The fact that `ai_generated` defaults to False and the apply route never overrides it is a bug, not a design decision.

**Defer with a defined trigger:**
Centralized prompt management and model configuration can wait until the team wants to run an A/B test on prompt variants or swap models. The trigger for this work is the first time the team wants to change a prompt and measure whether the change improved outcomes. Do not abstract before that trigger is clear.

RAG infrastructure should be deferred until there is enough data to retrieve from. Embedding ten line items from one project is not retrieval — it is context injection with extra steps. The trigger for RAG is either: (a) estimates grow large enough that context window injection becomes a bottleneck, or (b) cross-estimate historical retrieval becomes a feature the team wants to ship.

Fine-tuning infrastructure should be deferred until there are thousands of AI-generated rows with human corrections. The trigger is data volume, not time. But the consent mechanism (per-company opt-in flag) should be built before any customers exist — retrofitting consent collection after growth is legally and operationally expensive.

**Instrument so decisions can be made on data:**
Add the `estimate_outcome` field to `Project` now, even if the UI for marking won/lost is not built. The field costs nothing to add and a migration costs nothing at zero-customer scale. Add the `ai_call_log` table now, before the first paying customer, so the team knows what they are spending.

---

## Findings Worth Acting On

**F1 — `ai_generated` Is Never True: The Flywheel Discriminator Is Broken**
Severity: **Critical** | Effort: Small

The primary field that distinguishes AI-generated line items from human-generated line items is never set to `True` by any code path. The `/ai/apply` route at lines 2857-2877 creates LineItem records with all defaults, which sets `ai_generated=False`. The `save_assembly_builder()` route at lines 1605-1616 does the same. The `api_create_line_item()` route at line 1314 explicitly sets `ai_generated=False`. No route sets it True. Every row in the production database is identically labeled regardless of provenance. The documented flywheel requires this discriminator to interpret every other captured signal. Without it, `edit_delta`, `estimator_action`, `ai_confidence`, and `ai_status` cannot be attributed to AI output, and no future evaluation, fine-tuning corpus construction, or analytics query can distinguish human work from AI work. The fix is one assignment in `/ai/apply` and in the downstream save path for `/ai/build-assembly`. The data lost since Session 22 cannot be recovered.

File: `app.py:2857-2877` (add `ai_generated=True`), `app.py:1605-1616` (same)

**F2 — `estimator_action='accepted'` Is Never Written**
Severity: **Critical** | Effort: Small

The positive feedback signal — the most important signal in the documented flywheel — is never captured. When an estimator invokes `/ai/apply` to accept an AI proposal, `estimator_action` is not set on the created or modified items. The value `'accepted'` does not appear anywhere in `app.py`. The `estimator_action` field is only set to `'edited'` (TanStack PATCH) and `'rejected'` (TanStack DELETE). A flywheel with negative and correction signals but no positive signals cannot be used to train a model or evaluate quality. The fix is a single write in `/ai/apply` at the point of successful commit.

File: `app.py:2745-2880`

**F3 — Zero AI Calls Are Logged**
Severity: **Critical** | Effort: Small

Five routes invoke the Anthropic API. None log the call. There is no record anywhere in the system of: which user triggered an AI call, which company, which route, what the token count was, what the cost was, what the model responded, or whether the response was applied or discarded. The team has no way to know total AI spend, per-company AI spend, per-route token distribution, or anything about AI behavior over time. The minimum viable logging is one table (`ai_call_log`: user_id, company_id, route, model, input_tokens, output_tokens, created_at) and one shared function called before each route returns. Without this, cost runaway and quality degradation are invisible until they are problems large enough to feel without instrumentation.

File: `app.py:2717, 2988, 3278, 3433, 3544` (all five call sites)

**F4 — `/ai/scope-gap` Results Are Not Persisted**
Severity: **High** | Effort: Medium

The scope gap analysis route sends the full project to the model and receives a structured list of gaps, severities, and recommended actions. The response is returned to the frontend for display. Nothing is written to the database. The `ai_status` and `ai_note` fields on the relevant line items are not updated. The estimator either acts on the gaps or does not — the system records neither outcome. This means the scope gap feature generates no flywheel signal at all: the model cannot learn whether its gap detections are correct or false positives, and the estimator cannot see previous gap analyses on a project. The correct behavior is to write `ai_status='gap'` and `ai_note=<gap description>` to the affected items when the estimator confirms a gap.

File: `app.py:3104-3310`

**F5 — `/ai/validate-rate` Results Are Not Persisted**
Severity: **High** | Effort: Small

When the AI validates a production rate and finds it unreasonable, the assessment and recommendation are returned to the frontend. The line item's `ai_status`, `ai_confidence`, and `ai_note` are not updated. If the user closes the validation panel without taking action, the finding is gone. This is the exact use case `ai_note` was designed for — "Concrete — Footings, 8 LF/hr: above typical range of 15-40 LF/hr for this trade. Consider reviewing." The fix is to write the validation result back to the item record as part of the response.

File: `app.py:3462-3570`

**F6 — No Win/Loss Field on Project**
Severity: **High** | Effort: Small

`TALLY_VISION.md` identifies estimate outcome (won/lost/pending/abandoned) as a flywheel signal and explicitly notes `estimate_outcome` is "not yet added (future)." Every AI-assisted estimate that a contractor bids generates an outcome. That outcome, correlated back to AI-generated line items, is the richest signal in the entire flywheel — stronger than accept/edit/reject because it measures real-world correctness. Adding this field costs one migration statement and one route for the estimator to record the outcome. Not adding it means every estimate submitted before the field exists is permanently disconnected from its outcome.

File: `app.py` — Project model at line 115; `run_migrations()` at line 3676

**F7 — Model Version Is Hardcoded in Five Places with No Configuration**
Severity: **High** | Effort: Small

`claude-sonnet-4-20250514` appears at `app.py:2719, 2990, 3280, 3435, 3546`. ADR-001 documents `claude-sonnet-4-6` as the decision — the hardcoded string is a different model identifier from what the decision record says. Upgrading to a new model version, or running A/B tests between model versions, requires finding and modifying five separate strings with no single configuration point. The correct pattern is one `MODEL_ID = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')` at the module level, referenced from all call sites.

File: `app.py:2719, 2990, 3280, 3435, 3546`

**F8 — AI Prompts Are Not Versioned or Centralized**
Severity: **High** | Effort: Medium

Five routes construct system prompts via inline f-string interpolation with no template IDs, no version numbers, and no shared construction logic. If a prompt is modified in one route, there is no way to know which prompt version produced which rows in the database without inspecting git history. If the team wants to measure whether a prompt change improved AI output quality (the most basic evaluation question), they cannot answer it because the prompt version is not recorded anywhere alongside the output. The minimum viable approach is a constant or a module-level dictionary that maps route name to prompt version string, logged with each `ai_call_log` entry.

File: `app.py:2602, 2923, 3193, 3384, 3510` (five separate inline system prompt constructions)

**F9 — No Consent Infrastructure for Training Data Use**
Severity: **Medium** | Effort: Medium

The flywheel strategy describes a future opt-in program for training data use. No per-company consent flag exists. No consent event is recorded. When the team wants to build the Cost Intelligence tier using customer estimate data, there is no mechanism to filter the training corpus to consenting customers. This must be built before the first customer exists — not because the training is happening now, but because retrofitting consent collection after growth is legally and commercially expensive. The minimum addition is a `training_consent` boolean on `Company` (default False) and a UI in company settings to opt in. This one field is the gate on whether any future fine-tuning can legally use accumulated data.

File: `app.py` — Company model at line 68; `run_migrations()` at line 3676

**F10 — No Embedding or Vector Infrastructure**
Severity: **Medium** | Effort: Large

The documented strategy implies cross-estimate intelligence: "What did we cost this scope on similar projects?" This requires retrieval, which requires embeddings, which requires a vector store. None exists. The current AI integration injects full estimate context into the system prompt — effective for a single estimate but architecturally incapable of cross-estimate retrieval. The minimum preparation is enabling `pgvector` on the PostgreSQL instance and adding a nullable `embedding vector(1536)` column to `line_items` or `assemblies`, populated asynchronously by a background job. The column can sit empty until the retrieval feature is needed; having the column means the first retrieval feature ships without a schema migration on a large table.

File: No file — infrastructure change

**F11 — `edit_delta` Is Only Captured for TanStack PATCH**
Severity: **Medium** | Effort: Small

`edit_delta` is correctly captured in `api_patch_line_item()` at lines 1341-1373. The legacy `update_line_item()` route at line 1173 does not capture it. The `/ai/apply` update path does not capture it. Since the legacy route is deprecated (ADR-024) and will be retired in Pass 3, this is partially self-correcting. However, until Pass 3, any edits made through the legacy surface are missing deltas.

File: `app.py:1173-1205`

**F12 — `TakeoffMeasurement` Has No Flywheel Fields (Acknowledged, Tracking)**
Severity: **Medium** | Effort: Small

ADR-026 defers the addition of `ai_generated`, `estimator_action`, and `edit_delta` to `TakeoffMeasurement` to Pass 3. This is correctly documented. The finding is noted here because every measurement made before these fields are added is permanently unlabeled as human-drawn ground truth — the highest-quality flywheel signal per TALLY_VISION.md. The longer the delay, the more ground-truth data is accumulated without labels. Pass 3 should be treated as the hard deadline for this migration.

File: `app.py:362-371` (TakeoffMeasurement model); `run_migrations()` at line 3676

**F13 — `ai_build_assembly` Returns Data for Review Without Flywheel Capture**
Severity: **Medium** | Effort: Small

The `/ai/build-assembly` route at line 2883 generates a complete assembly and returns it for review. When the estimator accepts and saves the result, it flows through `save_assembly_builder()` at line 1547 — which creates LineItem records without setting `ai_generated=True`. The review-and-accept flow is the correct design pattern (ADR-005). The gap is that the acceptance event is not captured as a flywheel signal at the save step. The estimator's decision to accept the AI-generated assembly is the highest-value positive signal the generative mode can produce, and it is currently invisible to the system.

File: `app.py:1547-1617`

---

## Verdict

The architecture is not supporting the AI and data strategy the documents claim. The documentation is precise, correct, and specific about what the flywheel requires — and the implementation diverges from it on the single most important point: the field that identifies AI-generated content from human-generated content has never been set correctly since it was introduced. The strategy describes a flywheel that has been spinning since Session 22. The data says every row looks the same. The most important single issue the team needs to confront is that the flywheel's discriminator field is broken, every AI interaction since Session 22 has been recorded without a label, and no retroactive fix exists — the only choice is to fix it now, accept the loss of unlabeled historical data, and start accumulating clean signal from this point forward.
