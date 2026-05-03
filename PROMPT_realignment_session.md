# Zenbid Realignment Session — Pass 1 of 4

**Scope:** Documentation only. No application code changes. No migrations. No UI edits.
**Output:** Updated MD files that match repo reality as of today and encode the product direction below.
**Sessions that follow:** (2) 90-Second Confidence Study, (3) Bridge + Table Migration, (4) Tally Intelligence Wiring.

---

## ORIENT — read before writing anything

Read these in order. Do not edit yet.

1. `NORTHSTAR.md`
2. `Agent_MD.md`
3. `DECISIONS.md`
4. `TALLY_VISION.md`
5. `FEATURE_ROADMAP.md`
6. `SECURITY.md`
7. `CLAUDE.md`

Then scan the actual code to ground-truth the docs:

- `app/templates/project.html` (legacy estimate table surface)
- `app/static/js/estimate-*.js` (legacy table JS)
- `app/templates/estimate.html` or equivalent route for the new TanStack table
- `app/static/react/estimate-table/` (or wherever the TanStack build lives)
- `app/templates/takeoff.html` and `app/static/js/takeoff/` (Konva canvas)
- `app/models/` — specifically `LineItem`, `Measurement`, `Project`, any `AI*` or flywheel fields
- `app/routes/` — takeoff routes, estimate routes, measurement routes
- `tests/` — what's actually covered

**Before writing a single doc change, report:**

- Every contradiction between docs and code (doc says X exists, code says Y; code has Z, no doc mentions it).
- Every AgentX reference still live in code or UI (side tabs, model names, route names, labels).
- Current state of flywheel fields on `LineItem` — exist? populated? unused?
- Current state of flywheel fields on `Measurement` — likely absent; confirm.
- Any Tally UI surfaces present (banner, badge, button) and whether they wire to anything.

Only after that report is written, proceed to the edits below.

---

## PRODUCT DIRECTION — what the docs must now encode

These are the decisions driving this pass. They come from recent strategic conversations and supersede older framing anywhere the two conflict.

### 1. The user journey is Takeoff → Estimate → Proposal, and it must feel seamless.

Takeoff is now the first impression of Zenbid. The first 90 seconds — upload PDF, set scale, first measurement landed — is the confidence moment. Everything about that flow gets disproportionate attention. After those 90 seconds, Zenbid should diverge from zzTakeoff, not match it. The moat is what their architecture can't do: direct measurement→line item flow, Tally over the top, dual costing in one grid.

### 2. The estimator always owns the estimate. Tally is a collaborator.

Anti-replacement stance, stated plainly in NORTHSTAR as a product principle:

> Zenbid makes estimators more efficient and smarter about what's in a job. It builds confidence. It does not trigger AI fear. Tally handles labor so the estimator focuses on judgment. The estimator always owns the estimate — AI is optional, never mandatory, and never silent.

This is the message that converts seasoned estimators, who are the hardest conversion. It belongs high in NORTHSTAR, not buried.

### 3. Dual costing models are first-class. Both live in the same grid.

Two costing paradigms, equal weight:

- **Unit cost** — qty × unit_cost = line_total. For trades that bid flat unit prices (doors, frames, hardware, fixtures, specialty items).
- **Assembly build-up** — qty, production_rate, labor_rate, material_rate → computed unit_cost → line_total. For labor-heavy trades that think in production rates (drywall, framing, concrete, painting, flooring).

Not primary/secondary. Not a mode switch. Both render cleanly in the same table, line by line. The grid validates a line as complete if **either** path resolves to a line_total.

**UI pattern to adopt (pending small design spike in Session 3):** expandable row. Default row shows qty + unit_cost + line_total. A chevron expands to reveal the assembly build-up, which computes the unit_cost upward. No global mode toggle. Clean for unit-cost users, powerful for assembly users, no context switch.

**Formula column is Mode 3.** Prototyped already, likely a premium tier feature. Lives as a cell-level option, not a row pattern. Session 3 must not foreclose it. Name it in DECISIONS as a future mode; do not design it now.

### 4. Pricing flexibility is a flywheel strategy, not a UX convenience.

The causal chain: flexibility → trade breadth → real market data → GC-grade cost intelligence competitive with RSMeans. Unit-cost-only strands half the trades. Assembly-only strands the other half. The Cost Intelligence layer requires both. Every architectural decision evaluates against: **does this narrow or expand the trade set?**

Secondary point worth recording: assembly build-up is sticky work. An estimator who builds a burden-loaded assembly in Zenbid is not going back to Excel. A user who only enters unit prices can leave anytime. Assembly is retention.

### 5. Takeoff ↔ Estimate link is one-way-plus-traceability, not live two-way bind.

Measurement is the source of truth. Measurement qty flows into line_item qty on link. Line_item qty can diverge (waste factor, rounding, estimator judgment). Editing line_item qty does **not** silently rewrite the measurement. The UI surfaces divergence so the estimator knows the grid and the drawing no longer match.

This semantics must be named explicitly so Session 3 does not accidentally implement a live bidirectional sync.

### 6. Tally wraps every surface. Hooks get designed in this pass, intelligence gets wired in Pass 4.

Tally is not a separate product. It is the intelligence layer of the product. Every surface gets Tally entry points designed in now, even if they stub:

- **Takeoff:** "Verify this scale" action next to the scale tool. Passive badge when a drawing has been open N minutes with no measurements. Tally button on each measurement tool for contextual help.
- **Estimate grid:** Three modes have visible entry points. Passive (scope gap badges on rows/groups). Reactive (Tally button in toolbar for Q&A, reporting). Generative (natural-language line item creation, accessed from an explicit action, never auto-triggered).
- **Proposal:** deferred, but named as a future Tally surface.

### 7. Flywheel data capture extends to measurements, not just line items.

Every measurement is flywheel data: which trade, which drawing type, scale used, edits from initial to final, whether AI assisted. The fields `ai_generated`, `estimator_action`, `edit_delta` need to exist on `Measurement` as well as `LineItem`. Non-AI users still contribute clean flywheel data — possibly cleaner ground truth than AI-assisted estimates.

Data capture must be passive. No form fields asking the estimator to categorize their own work.

### 8. The new TanStack table is canonical. The legacy project-page table is deprecated.

Name this directly in an ADR during this pass. The Session 3 work is migration + deprecation, not reconciliation. Reconciliation framing implies symmetry that does not exist.

Migration scope to capture (not execute) in FEATURE_ROADMAP:
- Port Prod Rate, Labor Hrs, Labor $, Material $ columns into the TanStack schema as the assembly-mode columns.
- Port Assembly grouping behavior.
- Remove AgentX side tab and all AgentX references from UI and code.
- Retire the legacy table route after the migration session lands.

---

## DOCUMENT-BY-DOCUMENT EDITS

### `NORTHSTAR.md`

Rewrite to reflect:
- The Takeoff → Estimate → Proposal journey as the organizing frame.
- The anti-replacement principle (section 2 above) as a top-level product principle, verbatim or close.
- The dual-costing thesis (sections 3 and 4) as a core product principle — "Pricing Flexibility as a Flywheel Strategy."
- The one-way-plus-traceability takeoff↔estimate semantics (section 5).
- Tally as the intelligence layer that wraps every surface, not a separate module.
- The flywheel extending to measurements (section 7).
- The 90-second confidence moment as the takeoff product standard.

Remove anything that contradicts the above. Remove any AgentX framing.

### `Agent_MD.md`

Update the session-opening protocol to match current reality. Confirm the read order: NORTHSTAR → Agent_MD → DECISIONS → TALLY_VISION → task refs. Flag (do not execute) the question of whether TALLY_VISION should fold into NORTHSTAR in a later pass — doc sprawl is becoming real and Tally is not separable from the product.

Update any stale tool/stack references against what the code actually uses today.

### `DECISIONS.md`

Add the following ADRs. Number them in sequence after the existing last ADR.

- **ADR-XXX — Dual Costing Models as First-Class Paradigms.** Unit cost and assembly build-up are equal. Both render in the same grid. Flywheel rationale, trade-breadth rationale, retention rationale (assembly stickiness). Expandable row as the chosen UI pattern pending design spike.
- **ADR-XXX — Formula Column as Mode 3 (Future).** Prototyped, deferred to premium tier. Cell-level option, not row-level. Reserved so the dual-costing ADR does not foreclose it.
- **ADR-XXX — TanStack Table as Canonical Estimate Surface.** Legacy project-page table deprecated. Migration scope named. AgentX references retired.
- **ADR-XXX — Takeoff↔Estimate Link Semantics.** One-way source-of-truth from measurement to line_item. Line_item qty may diverge. UI surfaces divergence. No live bidirectional bind.
- **ADR-XXX — Flywheel Fields on Measurements.** `ai_generated`, `estimator_action`, `edit_delta` added to the Measurement model concept. Passive capture only.
- **ADR-XXX — Tally Hooks Designed In, Intelligence Wired Later.** Every surface gets stubbed Tally entry points in Pass 3. Pass 4 wires the intelligence layer. Prevents retrofit.

### `TALLY_VISION.md`

Update to:
- Map each of the three modes (Passive, Reactive, Generative) to concrete surfaces on Takeoff and Estimate.
- Name the stub hooks each surface will get in Pass 3.
- Reaffirm the anti-replacement stance — Tally is collaborative, optional, never silent.
- Name the flywheel contribution of each mode.

### `FEATURE_ROADMAP.md`

Reorganize around the four-pass sequence:

1. **Pass 1 (this session):** Realignment — docs only.
2. **Pass 2:** 90-Second Confidence Study — scoped Playwright/manual walkthrough of zzTakeoff, punch list for the upload→scale→first-measurement flow only. Diverge after that.
3. **Pass 3:** Bridge + Table Migration — combined. TanStack becomes canonical. Legacy table retired. AgentX purged. Measurement→line_item link implemented with one-way+traceability semantics. Dual-costing expandable row designed and built. Tally stub hooks placed on both surfaces.
4. **Pass 4:** Tally Intelligence Wiring — backend for Passive/Reactive/Generative modes against the hooks Pass 3 placed.

Move any items that don't fit into a "Later" section with honest labeling.

### `SECURITY.md`

No scope change in this pass. Confirm the four Critical items (SSL cert, Privacy Policy, ToS, API key startup validation) are still listed. Flag if any have been resolved.

### `CLAUDE.md`

Confirm it still reflects the working session protocol. Update the repo structure section if the code scan revealed drift.

---

## ACCEPTANCE CRITERIA FOR THIS SESSION

- Contradiction report written before any edits.
- Every MD above reflects repo reality, not aspirational state.
- Every product direction in sections 1–8 is encoded in at least one doc, with the key ones (anti-replacement, dual costing, one-way link semantics) in NORTHSTAR.
- No AgentX references left in NORTHSTAR, Agent_MD, DECISIONS, FEATURE_ROADMAP, or TALLY_VISION.
- New ADRs recorded with full rationale, not one-liners.
- No application code changed. No model changes. No migrations. No route changes.
- Session closes with a commit containing only MD changes and a commit message summarizing the realignment.

---

## WHAT THIS SESSION IS NOT

- Not a build session. No code.
- Not a design session. Expandable row is named as the direction; the interaction spike happens in Pass 3.
- Not a Tally wiring session. Hooks are described in docs; implementation is Pass 3 (stubs) and Pass 4 (intelligence).
- Not a zzTakeoff study. That is Pass 2.
