# Zenbid — Northstar Document
**Purpose:** Foundational philosophy and feature architecture. Every design decision, feature build, and UI choice should be evaluated against this document.

**Last updated:** 2026-04-13

> Full AI intelligence specification: see `TALLY_VISION.md`.  
> Architecture decisions with rationale: see `DECISIONS.md`.

---

## PART 1: PHILOSOPHY & ARCHITECTURE FRAMEWORK

### Problem Statement

The construction estimating industry faces a generational divide. Experienced estimators possess deep domain knowledge but are locked into rigid Excel workflows and legacy software (Sage, Timberline, DESTINI) that enforce a single mental model. Newer estimators and less-seasoned staff lack institutional knowledge — they struggle to replicate complex templates, miss critical line items, and have no framework for thinking beyond the spreadsheet. Meanwhile, the industry's shift toward AI-native workflows creates an opportunity to serve both mindsets simultaneously.

### Strategic Positioning

Zenbid bridges this gap with a seamless **Takeoff → Estimate → Proposal** workflow. Takeoff is not a bolt-on module — it is the first impression. After the first 90 seconds on the canvas, Zenbid must diverge sharply from generic takeoff tools. The moat is direct measurement-to-line-item flow, Tally intelligence over the top, and dual costing in a single grid. No other construction estimating tool does this natively.

---

### Core Product Principles

**1. The Journey is Takeoff → Estimate → Proposal**
Every feature decision is evaluated against whether it makes this journey faster, more confident, or more seamless. No seams. No context switches. All three surfaces feel like one product.

**2. The 90-Second Confidence Moment**
Upload PDF, set scale, land first measurement. That is the product's first impression. Those 90 seconds must be flawless. After the first measurement lands, Zenbid diverges from zzTakeoff and similar tools — the moat is the direct measurement→estimate flow that their architectures cannot replicate.

**3. The Estimator Always Owns the Estimate — Tally is a Collaborator**
Zenbid makes estimators more efficient and smarter about what's in a job. It builds confidence. It does not trigger AI fear. Tally handles quantification labor so the estimator focuses on judgment. The estimator always owns the estimate — AI is optional, never mandatory, and never silent. This is the message that converts seasoned estimators, who are the hardest conversion.

**4. Pricing Flexibility Is a Flywheel Strategy**
Two costing paradigms are equal, and both live in the same grid:

- **Unit cost** — `qty × unit_cost = line_total`. For trades that bid flat unit prices (doors, frames, hardware, fixtures, specialty items).
- **Assembly build-up** — `qty + production_rate + labor_rate + material_rate → computed unit_cost → line_total`. For labor-heavy trades that think in production rates (drywall, framing, concrete, painting, flooring).

Not primary/secondary. Not a mode switch. Both render in the same table, line by line. The grid validates a line as complete if **either** path resolves to a `line_total`.

The causal chain: flexibility → trade breadth → real market data → GC-grade cost intelligence competitive with RSMeans. Unit-cost-only strands half the trades. Assembly-only strands the other half. Assembly build-up is also retention: an estimator who builds a burden-loaded assembly in Zenbid is not going back to Excel.

**5. Takeoff↔Estimate Link: One-Way Source-of-Truth with Traceability**
Measurement is the source of truth. Measurement qty flows into `line_item.qty` on link. `line_item.qty` can diverge (waste factor, rounding, estimator judgment). Editing a line item qty does **not** silently rewrite the measurement. The UI surfaces divergence so the estimator knows the grid and the drawing no longer match. No live bidirectional sync — ever.

**6. Tally Wraps Every Surface**
Tally is not a separate product. It is the intelligence layer of the product. Every surface — Takeoff, Estimate, Proposal — gets Tally entry points. Tally operates in three modes:
- **Passive** — always watching, surfaces observations without interrupting
- **Reactive** — on-demand Q&A and reports, scoped to current estimate data
- **Generative** — natural-language line item creation, accessed from an explicit user action, never auto-triggered

See `TALLY_VISION.md` for full specification. Every surface gets Tally stub hooks in Pass 3; intelligence is wired in Pass 4.

**7. Flexibility Over Dogma**
Users should never feel constrained by the tool's structure. Want assemblies grouped by floor? Fine. Reorganize by trade instead of CSI? Fine. Build line items one-by-one like an Excel sheet? That option always exists. The tool adapts to the user's mental model, not the reverse.

**8. Institutional Knowledge at Your Fingertips**
Junior or less-seasoned estimators often don't know what they don't know. Tally's Passive mode surfaces scope gaps, production rate deviations, and pricing drift automatically — without condescension. Over time, the flywheel accumulates real market data that becomes the foundation for a Cost Intelligence tier comparable to RSMeans but continuously updated.

**9. Predictable Output, Unpredictable Process**
No matter how flexibly a user navigates the tool — assembly builder, freestyle line items, or hybrid — the backend delivers consistent, professional reports: material totals, labor hours, CSI-grouped summaries, assembly breakdowns. The rigor is in the output, not the input process.

**10. Generational Inclusivity**
Works for the 60-year-old estimator who thinks in Excel and wants predictability, and the 28-year-old who thinks in AI-assisted workflows and values flexibility. Same tool, different interfaces, same solid output.

---

### Architectural Principles

**1. Modularity**
Assembly builder, estimate grid, takeoff canvas, reporting engine — each operates independently but flows seamlessly together.

**2. Non-Destructive Flexibility**
Users can reorganize, re-group, re-tag line items without losing source data or calculation integrity.

**3. Transparent AI**
When Tally provides an answer or recommendation, show the reasoning. No magic numbers. No black boxes. Every generated row shows confidence and can be reviewed, edited, or rejected.

**4. Data Flywheel by Design**
Every interaction — accept, edit, reject, ignore — is a training signal captured from day one. Flywheel fields (`ai_generated`, `estimator_action`, `edit_delta`) are live on `LineItem`. The same fields will be added to `TakeoffMeasurement` (ADR-026), so non-AI users still contribute clean ground-truth data. Passive capture only — no forms asking estimators to categorize their own work.

**5. Report Generation Agnostic**
The same estimate data feeds multiple report formats: CSI-organized, assembly-organized, trade-organized, line-item detail, executive summary. The data is the source of truth.

---

### Implementation Mindset

> **The Test:** When building features, ask: *Could a rigid estimator use this comfortably? Could a flexible estimator use this expressively?* If the answer to either is "no," reconsider the design.

The tool should feel like it's made of clay, not concrete.

---

## PART 2: THE THREE SURFACES

### Current Architecture (2026-04)

The product has three core surfaces. All three must feel like one product — no seams, no context switches.

| Surface | Implementation | Status |
|---|---|---|
| **Takeoff** (measure) | Konva.js canvas, PDF.js, multi-page | ✅ LIVE — Session 21 complete, 99/99 tests |
| **Estimate** (price) | TanStack Table v8, React, Flask API | ✅ LIVE — Session 22 complete, 29/29 tests |
| **Proposal** (deliver) | Jinja template, print-to-PDF | ⚠️ Existing — pre-TanStack, pending integration |

**Core user journey:**
```
Takeoff (measure) → Estimate (price) → Proposal (deliver)
```

The **Takeoff → Estimate bridge** (Pass 3) is the next architectural priority: measurements from the Konva canvas flow directly into LineItem rows. This is the core product moat — no other construction estimating tool does this natively.

---

### The Takeoff Surface

Konva.js 3-layer canvas (`pdfLayer`, `measureLayer`, `uiLayer`) with PDF.js for all PDF rendering. Supports:

- PDF plan upload (instant; PyMuPDF for page count only; no server-side pixel work)
- Client-side thumbnails via PDF.js at `scale: 0.15`
- Scale calibration (architectural ratio display: 1/4″=1′ etc.)
- Linear, Linear with Width, Area, and Count measurement tools
- Ortho mode (45° snap), close-polygon green indicator, status bar coordinates
- Properties panel, project-level totals per item across all pages

The **90-second confidence moment** is the takeoff product standard: upload → scale → first measurement landed. This flow gets disproportionate attention in all polish and UX decisions.

Tally stub hooks planned for Pass 3: "Verify this scale" action, passive idle-drawing badge, measurement-tool contextual help button.

---

### The Estimate Surface

TanStack Table v8 (headless, React via CDN + Babel Standalone) is the **canonical estimate surface**. The legacy project-page inline estimate table is deprecated — see ADR-024.

**Dual costing in one grid:** every row resolves to a `line_total` via either the unit-cost or assembly build-up path (ADR-022). Both coexist line by line. The expandable row is the chosen UI direction for surfacing assembly detail without cluttering unit-cost rows — design spike in Pass 3.

**Formula column (Mode 3):** prototyped, deferred to premium tier as a cell-level option (ADR-023).

**Tally integration:** flywheel fields (`ai_generated`, `estimator_action`, `edit_delta`, `ai_status`, `ai_confidence`, `ai_note`) are live on all LineItem writes. The Tally footer banner and AI status badges render in the grid. Intelligence layer wired in Pass 4.

---

### The Proposal Surface

Jinja template with print-to-PDF (light theme for printing). Pre-TanStack design — pending integration with the new estimate data model.

---

## PART 3: FEATURE DETAIL

### Assembly Builder

Multi-step wizard (Label → Select Line Items → Set Measurements → Review → Save). User-configurable quantity formulas per line item (e.g., `LF × height`, `(LF × H) ÷ 32`). "Save as Template" for reuse across projects.

Assembly build-up is the **assembly-mode costing path** — computes `unit_cost` upward from `labor_rate`, `production_rate`, `material_rate`. This path makes assembly work sticky: users who define burden-loaded assemblies are not going back to Excel.

---

### Line Item Library

Searchable, filterable database of reusable line items. Company-scoped. Separate from project-specific `LineItem` records.

---

### Traditional Line Item Entry (Always Available)

Manual line-by-line entry via modal is never removed. Skip the assembly builder entirely and add line items one by one. This is a supported first-class workflow, not a workaround.

---

### Key Database Models

| Model | Notes |
|-------|-------|
| `LineItem` | assembly_id NULLABLE; all flywheel fields; unit-cost and assembly-build-up fields |
| `Assembly` | is_template; measurement_params JSON; qty formulas per composition item |
| `TakeoffMeasurement` | flywheel fields **to be added in Pass 3** (ADR-026): ai_generated, estimator_action, edit_delta |
| `TakeoffItem` | assembly_notes; bridge to Estimate is Pass 3 priority |

**Schema rule:** Always extend `run_migrations()` with `ALTER TABLE … ADD COLUMN IF NOT EXISTS`. Never drop/recreate tables.

---

### Calculation Logic Chain

```
Assembly measurements (LF, height, depth)
    ↓ user-defined quantity formulas
Derived line item quantities
    ↓ production_rate
Labor hours = quantity ÷ production_rate
    ↓ cost per unit / cost per hour
Material cost, Labor cost, Equipment cost
    ↓ sum
Line item total_cost
    ↓ group and sum
Assembly subtotals → CSI subtotals → Trade subtotals → Project grand total
```

---

## PART 4: DESIGN RULES

### App (dark theme) — CSS variables in `app_base.html`

Use CSS variables — **never hardcode hex values**. The old palette (`#1a1a2e`, `#16213e`, `#0f3460`, `#e94560`) is deprecated.

| Token | Hex | Use |
|-------|-----|-----|
| `--app-bg` | `#0F1419` | Page background |
| `--app-card` | `#1A1F26` | Card / panel background |
| `--app-sidebar` | `#16181D` | Sidebar background |
| `--app-input` | `#252B33` | Input field background |
| `--primary-brand` | `#2D5BFF` | Buttons, links, active states |
| `--accent-coral` | `#FF6B35` | CTAs, highlights, stat numbers |
| `--error-bg` | `#3a0a12` | Error state background |
| `--error` | `#EF4444` | Error text / destructive |

### Marketing (light theme) — CSS variables in `base.html`
- `--primary-brand: #2D5BFF` | `--accent-coral: #FF6B35` | `--marketing-bg: #FFFFFF`

### CSI Division Colors
Defined in `CSI_COLORS` dict in `app.py` AND duplicated in `estimate_table.js` — keep both in sync.

### Typography
System UI stack only: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif`. No external font imports.

---

## PART 5: SUCCESS CRITERIA (Current)

The three surfaces are complete when:

- [ ] Upload → scale → first measurement lands in under 90 seconds for a new user
- [ ] Measurement qty flows directly into a LineItem row via the bridge (Pass 3)
- [ ] Unit-cost and assembly build-up coexist in the same grid row by row
- [ ] Expandable row reveals assembly detail without a mode switch (Pass 3)
- [ ] Tally stub hooks are present on both Takeoff and Estimate (Pass 3)
- [ ] Tally Passive/Reactive/Generative intelligence is wired (Pass 4)
- [ ] Proposal integrates with TanStack estimate data model
- [ ] Output reports are consistent regardless of which costing path was used

---

*Last updated: 2026-04-13*
