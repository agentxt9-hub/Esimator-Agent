# Estimator AgentX — Northstar Document
**Purpose:** Foundational philosophy and feature architecture. Every design decision, feature build, and UI choice should be evaluated against this document.

---

## PART 1: PHILOSOPHY & ARCHITECTURE FRAMEWORK

### Problem Statement

The construction estimating industry faces a generational divide. Experienced estimators possess deep domain knowledge but are locked into rigid Excel workflows and legacy software (Sage, Timberline, DESTINI) that enforce a single mental model. Newer estimators and less-seasoned staff lack institutional knowledge—they struggle to replicate complex templates, miss critical line items, and have no framework for thinking beyond the spreadsheet. Meanwhile, the industry's shift toward AI-native workflows creates an opportunity to serve both mindsets simultaneously.

### Strategic Positioning

AgentX bridges this gap by offering dual-natured estimating: a tool that is simultaneously rigid enough to feel familiar and flexible enough to accommodate different thinking styles, with an optional AI layer that augments human judgment rather than replacing it.

---

### Core Philosophy

**1. Flexibility Over Dogma**
Users should never feel constrained by the tool's structure. You want your assemblies grouped by floor? Group by floor. You want to reorganize the estimate by trade instead of CSI? Do it. You want to manually build line items one-by-one like an Excel sheet? That option exists. The tool adapts to the user's mental model, not the reverse.

**2. AI as Optional Augmentation, Not Required Intelligence**
The AI layer (Ollama + local LLM) is always available but never mandatory. A user should be able to build a complete, professional estimate without asking the AI a single question. But when they do ask—"How many sheets of drywall in this wall?" or "What's typical for painting costs in this region?"—the AI handles the research, calculation, and reasoning behind the scenes, transparently. No formulas to maintain. No breakage.

**3. Predictable Output, Unpredictable Process**
No matter how flexibly a user navigates the tool—whether they build rigid assemblies, freestyle line items, or hybrid approaches—the backend delivers consistent, professional reports. Material totals, labor hours, CSI-grouped summaries, assembly breakdowns. The rigor is in the output, not the input process.

**4. Institutional Knowledge at Your Fingertips**
Younger or less-seasoned estimators often don't know what they don't know. AI recommendations ("You've got drywall but no paint. Standard practice?") or intelligent line item suggestions ("Typical assemblies for this wall type include...") level the playing field without condescension. Over time, machine learning can learn from project patterns and offer increasingly smart suggestions.

**5. Generational Inclusivity**
The tool must work for the 60-year-old estimator who thinks in Excel and wants predictability, and the 28-year-old who thinks in AI-assisted workflows and values flexibility. Same tool, different interfaces, same solid output.

---

### Architectural Principles

**1. Modularity**
Assembly builder, estimate spreadsheet, line item library, reporting engine—each operates independently but flows seamlessly together.

**2. Non-Destructive Flexibility**
Users can reorganize, re-group, re-tag line items without losing source data or calculation integrity.

**3. Transparent AI**
When the AI provides an answer or recommendation, show the reasoning. "Paint recommendation: industry standard is 2 coats after drywall taping/finishing. Assuming 1 gallon per 350 SF."

**4. Offline-First**
Ollama runs locally. No API calls, no usage limits, no surprises. Data never leaves the machine unless the user explicitly exports.

**5. Report Generation Agnostic**
The same estimate data should feed multiple report formats—CSI-organized, assembly-organized, trade-organized, line-item detail, executive summary. The data is the source of truth.

---

### Implementation Mindset

> **The Test:** When building features, ask: *Could a rigid estimator use this comfortably? Could a flexible estimator use this expressively?* If the answer to either is "no," reconsider the design.

The tool should feel like it's made of clay, not concrete.

---

## PART 2: FEATURE VISION & SPECIFICATIONS

### Vision

Build a dual-workflow estimating system that supports both assembly-based estimation (fast, reusable) and traditional line-by-line estimation. The core innovation is the Assembly Builder—a tool that lets estimators compose complex building systems (walls, footings, roofs) by selecting line items across multiple CSI divisions, measure once, and flow all costs into a flexible estimate view that can be reorganized by assembly, CSI division, or trade.

---

### Phase 1: Line Item Library

A searchable, filterable database of line items separate from any specific project. Library items are reusable across projects; project line items are project-specific.

**Requirements:**
- Search and filter by description, CSI code, or trade/labor category
- Create new library items on the fly (description, CSI code, unit, production rate, default costs)
- Display in a clean card or table view
- Ability to pull a library item into a project assembly or directly into the estimate

**Database:** `line_item_library` table — separate from `LineItem` (which is project-specific)

---

### Phase 2: Assembly Builder Interface

A multi-step wizard where users compose assemblies by selecting line items, setting measurement parameters, and saving the result to a project.

**5-Step Workflow:**
1. **Label & Name** — Set assembly label (A100, Wall-East) and name
2. **Select Line Items** — Search/filter the line item library; checkbox or drag-and-drop to add items; color-coded by CSI division
3. **Set Measurements** — Define assembly-level dimensions (e.g., LF + height for walls; LF + depth for footings). Multiple parameters allowed.
4. **Review** — See all composed line items with calculated quantities in real time as measurements are adjusted
5. **Save** — Save to project; optional "Save as Template" checkbox

**Assembly Measurement Logic (User-Configurable, Not Hardcoded):**

For each line item in the assembly, the user defines how its quantity derives from assembly measurements. The interface should allow expressions like:
- "quantity = LF × height" → insulation (SF)
- "quantity = (LF × height) ÷ 32" → drywall (sheets, 4×8 = 32 SF each)
- "quantity = LF × depth × [density factor]" → rebar (lbs)
- "quantity = LF" → top/bottom plate (linear feet)

This logic is stored with the assembly composition so it recalculates if measurements change.

**Assembly Builder Examples:**

*Exterior Wall Assembly* — 500 LF × 12 ft high
| Component | CSI | Quantity Formula | Result |
|-----------|-----|-----------------|--------|
| Drywall | 09 | (LF × H) ÷ 32 | 187.5 sheets |
| Paint | 09 | LF × H (SF) | 6,000 SF |
| Insulation | 07 | LF × H (SF) | 6,000 SF |
| Studs/Framing | 06 | LF | 500 LF |
| Top/Bottom Plate | 06 | LF × 2 | 1,000 LF |
| Sheathing | 07 | LF × H (SF) | 6,000 SF |
| Weather Barrier | 07 | LF × H (SF) | 6,000 SF |
| Exterior Finish | 04 | LF × H (SF) | 6,000 SF |

*Concrete Footing Assembly* — 50 LF × 2 ft deep
| Component | CSI | Quantity Formula | Result |
|-----------|-----|-----------------|--------|
| Excavation | 31 | LF × D (CY) | ~3.7 CY |
| Concrete | 03 | LF × D (CY) | ~3.7 CY |
| Rebar | 03 | LF × D × factor (lbs) | variable |
| Formwork | 03 | LF × D (SF) | 100 SF |

**UI Specifics:**
- Wizard-style or tabbed flow
- Drag-and-drop or checkbox line item selection
- Real-time quantity preview updates as measurements change
- Color-coded rows by CSI division
- Save button with confirmation message

---

### Phase 3: Estimate Spreadsheet View

A flexible, reorganizable spreadsheet-like view of the entire project estimate. Functions like DESTINI or Ediphi — data stays the same, presentation changes based on user's needs.

**Columns:** Description | CSI Code | Qty | Unit | Labor Hours | Material Cost | Labor Cost | Equipment Cost | Total Cost

**View Toggle (Critical):**
- **Assembly View** — Group by assembly label (A100, B200); subtotals per assembly; overall total
- **CSI View** — Group by CSI division (03, 04, 06...); subtotals per division; overall total
- **Trade View** — Group by trade/labor category (framing, concrete, electrical...); subtotals per trade; overall total

Three-button toggle at top of page. Data is identical; only grouping and presentation changes.

**Flexibility Features (Non-Negotiable):**
- Manual inline editing of qty, costs, notes — auto-save on change
- Delete any line item without affecting assembly integrity
- Add ad-hoc line items directly to the estimate without using the assembly builder (traditional workflow)
- Drag-reorder line items within a view (optional but valuable)
- Collapsible groups (expand/collapse assembly or CSI section)

**UI Specifics:**
- Sticky table header + sticky footer showing live totals (always visible while scrolling)
- Color-coded rows by CSI division for visual clarity
- Print-friendly styling (so users can print the estimate directly from browser)
- Export to CSV or PDF — design for this now, build later
- Sortable columns (click to sort by description, cost, hours, etc.)
- Maintain dark navy/red color scheme with light borders for table structure

---

### Phase 4: Assembly Templates

Save assemblies as reusable templates and load them into any new project.

**Saving:**
- "Save as Template" checkbox on the Assembly Builder save step
- Templates are global (not project-specific)

**Browsing & Loading:**
- Browse templates page or modal showing: template name, last used date, project count
- One-click load: auto-populates composition, measurement parameters, and default costs into a new assembly
- Duplication with modifications: load a template and edit before saving to project

**Database:** `Assembly.is_template = True` flag + template scope global; or separate `AssemblyTemplate` table — decide at build time.

---

### Traditional Line Item Entry (Always Available)

The existing modal for manual line-by-line entry is never removed. Users who prefer Excel-style direct input can skip the assembly builder entirely and add line items one by one. This is not a workaround — it is a supported workflow.

---

### AI-Assisted Recommendations (Design Now, Build in Phase 7)

The architecture must accommodate AI injection at multiple points without breaking existing workflows:
- **Completeness checks:** "You've added drywall but no paint. Standard practice?"
- **Quantity suggestions:** "For 500 LF wall at 12 ft, typical drywall is ~188 sheets."
- **Pricing research:** "Market rate for 5/8" Type X drywall in your region: $X/sheet."

AI suggestions are always opt-in, always shown with reasoning, never required. Design hooks into the Assembly Builder and Estimate View for future AI panel or inline suggestion system.

---

### Design Rules (All New Interfaces)

- Dark navy (`#1a1a2e`) page bg, `#16213e` card bg, `#0f3460` panel/input, `#e94560` accent red — no exceptions
- All templates consistent with existing `project.html` styling
- Production rate calculations flow through automatically from assembly measurements
- Cost and hours rollups update in real-time as items are added or changed
- Users can always manually override, re-tag, or reorganize without losing data integrity

---

### Database Additions (Flag Before Implementing Any)

| Addition | Purpose | Phase |
|----------|---------|-------|
| `line_item_library` table | Reusable library items separate from project LineItems | 1 |
| `LineItem.csi_level_1_id` / `csi_level_2_id` | Direct CSI FK on line items (needed for CSI view grouping) | 3 |
| `LineItem.trade` / `labor_category` field | Trade grouping for Trade View | 3 |
| `Assembly.is_template` (bool) | Mark assemblies as reusable templates | 4 |
| `Assembly.measurement_params` (JSON) | Store assembly-level dimensions | 2 |
| `Assembly.composition` (JSON) or `assembly_composition` junction table | Which library items + quantity formulas | 2 |
| `production_rate_standards` table | Standard rate lookup library | Future |

**Rule:** Never alter schema without flagging impact. Use `db.create_all()` for new tables.

---

## PART 3: TECHNICAL SPEC & BUILD SEQUENCE

### Build Sequence

Build phases in order. Test each phase before starting the next. Each phase output must feed the next phase's input — no orphaned features.

```
Phase 1: Line Item Library       → feeds Phase 2 (library items selected in builder)
Phase 2: Assembly Builder        → feeds Phase 3 (assemblies appear in estimate)
Phase 3: Estimate Spreadsheet    → feeds Phase 4 (templates load into estimate)
Phase 4: Assembly Templates      → completes the loop
```

---

### New Flask Routes (Planned)

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/library` | Line item library browse page |
| POST | `/library/item/new` | Create new library item |
| POST | `/library/item/<id>/update` | Edit library item |
| POST | `/library/item/<id>/delete` | Delete library item |
| GET | `/project/<id>/estimate/data` | JSON data payload for dynamic view reorganization |
| POST | `/project/<id>/assembly/save-template` | Save assembly as reusable template |
| GET | `/templates` | Browse saved assembly templates |
| POST | `/project/<id>/assembly/load-template/<template_id>` | Load template into new assembly |

Existing routes unchanged. `/project/<id>/estimate` stays but gets enhanced with view toggle.

---

### Frontend Guidance

- **Default: Vanilla JS + fetch()** — consistent with existing codebase pattern
- **Alpine.js:** Consider if reactive state management becomes complex (flag before adding any new JS dependency)
- **View toggle logic:** JS-only, no page reload — fetch `/estimate/data` once, render client-side by grouping key
- **Sorting/collapsing:** Client-side JS
- **Inline editing:** Existing auto-save pattern reused (fetch POST on blur)

---

### Calculation Logic Chain

The full chain from assembly input to report output:

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

Existing `labor_hours = quantity ÷ production_rate` logic is preserved and extended, not replaced.

---

### Data Structure Decisions (Defer to Build Time)

**Assembly composition storage:**
- Option A: JSON column on `Assembly` — simpler, flexible, less queryable
- Option B: `assembly_composition` junction table (assembly_id, library_item_id, qty_formula) — queryable, supports library item references
- Recommendation: flag at Phase 2 build time; lean toward junction table if library integration is needed

**Line item CSI for grouping:**
- Currently line items inherit CSI through their assembly FK
- CSI View requires direct `csi_level_1_id` on `LineItem` — add this column in Phase 3 DB migration

**Trade grouping:**
- `LineItem.trade` or `labor_category` text field — add in Phase 3 DB migration alongside CSI field

---

### Success Criteria

The build phases are complete when all of the following are true:

- [ ] Users can search, filter, and create line items in a global library
- [ ] Users can compose assemblies via a multi-step builder with user-configurable measurement logic
- [ ] Real-time quantity preview updates as assembly measurements change
- [ ] Estimate view toggles between Assembly, CSI, and Trade groupings with live subtotals
- [ ] Users can manually edit, add, or delete line items in the estimate without breaking calculations
- [ ] Users can add ad-hoc line items directly to the estimate (no assembly builder required)
- [ ] Users can save assemblies as templates and load them into new projects
- [ ] Output reports (material totals, labor hours, CSI summaries) are consistent regardless of input method
- [ ] UI is accessible to both rigid (Excel-minded) and flexible (AI-native) estimators
- [ ] Codebase architecture accommodates AI injection in Phase 7 without structural changes

---

*Last updated: 2026-03-09 — Session 3*
