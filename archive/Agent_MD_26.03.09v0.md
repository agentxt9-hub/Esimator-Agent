# Estimator AgentX — Session Handoff
**Session Date:** 2026-03-09 (Session 3)
**Prepared by:** Claude (claude-sonnet-4-6)

---

## What Was Accomplished This Session

### Architecture: NORTHSTAR.md Created
Added a permanent philosophy and architecture reference document at the project root. Every future build session should evaluate decisions against it.

**File:** `NORTHSTAR.md`
**Contents:**
- Part 1: Core philosophy (5 principles), architectural principles (5), implementation mindset test
- Part 2: Feature specifications for all planned phases (Line Item Library, Assembly Builder, Estimate Views, Templates, AI Layer)
- Part 3: Technical spec — build sequence, planned Flask routes, frontend guidance, data structure decisions, success criteria checklist

**The test to run on every feature:**
> *Could a rigid estimator use this comfortably? Could a flexible estimator use this expressively?* If either is "no," reconsider.

---

### Feature: Edit Assembly (Step 3) ✅

**What changed:**
- `app.py` — New route `POST /assembly/<id>/update` — accepts same fields as create, updates record in place
- `app.py` — `view_project` now also passes `assemblies_json` (array of all assembly data for the page)
- `project.html` — Assembly modal is now dual-mode: `<h2 id="assemblyModalTitle">`, `<input type="hidden" id="assemblyEditId">`, `<button id="assemblySubmitBtn">`
- `project.html` — Form `onsubmit` changed from `createAssembly()` → `saveAssembly()` which routes to `/new` or `/update` based on whether `assemblyEditId` is set
- `project.html` — Each assembly header has an **Edit** button that calls `openEditAssemblyModal(id)`, pre-fills all fields and CSI dropdowns, and switches modal to edit mode
- `project.html` — `openAssemblyModal()` resets everything to blank create mode

---

### Feature: Line Item Library (Phase 1) ✅

A global, reusable library of line items separate from any project.

**What changed:**
- `app.py` — New `LibraryItem` model (`library_items` table): description, csi_level_1_id, csi_level_2_id, unit, production_rate, production_unit, material_cost_per_unit, labor_cost_per_hour, equipment_cost_per_hour, notes
- `app.py` — 4 new routes: `GET /library`, `POST /library/item/new`, `POST /library/item/<id>/update`, `POST /library/item/<id>/delete`
- `Templates/library.html` — New full page with:
  - Stats bar (total items, showing count, CSI divisions covered)
  - Search input + CSI division filter (both client-side, no page reload)
  - Table: Description, CSI Division, CSI Section, Unit, Prod Rate, Mat $/Unit, Labor $/Hr, Equip $/Hr, Edit/Delete
  - Dual-mode Create/Edit modal (same JSON embedding pattern as assembly modal)
  - Delete confirm notes "will not affect existing project line items"
- `index.html` — "Line Item Library" button added next to "+ New Project"
- `project.html` — "Library" button added to project header nav
- `db.create_all()` creates the `library_items` table on first run

---

### Feature: Assembly Builder v2 (Phase 2) ✅

A dedicated multi-section builder page where estimators compose assemblies from library items with measurement-driven quantity formulas.

**What changed:**
- `app.py` — `Assembly` model gets 2 new columns: `is_template` (Boolean), `measurement_params` (Text/JSON)
- `app.py` — New `AssemblyComposition` model (`assembly_composition` table): assembly_id FK, library_item_id FK (nullable), description, unit, qty_formula, qty_divisor, qty_manual, production_rate, material/labor/equipment costs, sort_order
- `app.py` — `calculate_qty(formula, params, divisor, manual_qty)` helper function — maps formula keys to calculated values
- `app.py` — `run_migrations()` function — uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` to safely add the two new Assembly columns to the existing DB table without losing data
- `app.py` — 2 new routes:
  - `GET /project/<id>/assembly/builder` — renders builder page with library JSON
  - `POST /project/<id>/assembly/builder/save` — atomic save: Assembly + AssemblyComposition records + LineItem records in one transaction
- `app.py` — `__main__` now calls `run_migrations()` after `db.create_all()`
- `Templates/assembly_builder.html` — New dedicated page with:
  - Assembly Info section (label, name, description, template checkbox)
  - Measurements section (LF, Height, Depth, Width) with live derived display (SF, Vol)
  - Two-panel builder: left 320px library search panel, right composition table
  - Library panel: real-time text filter, click to add item, "+ Add Custom Item" button
  - Composition table: per row — editable description, formula dropdown, live qty display, unit, cost inputs, remove button
  - Formula types: Fixed Qty, = LF, = LF×2, = Area SF (LF×H), = Area SF÷N, = LF×Depth, = Volume CY
  - When formula changes or measurements update, all quantities recalculate instantly
  - Preview totals (Material, Labor, Equipment, Total) update live
  - Save serializes everything to JSON, POSTs to Flask, redirects to project on success
- `project.html` — "+ Assembly Builder" (red, links to builder page) + "+ Quick Assembly" (secondary, opens existing modal) — both available, user chooses workflow

**Formula keys stored in AssemblyComposition.qty_formula:**
| Key | Calculation |
|-----|-------------|
| `fixed` | `qty_manual` value |
| `lf` | LF |
| `lf_x_2` | LF × 2 |
| `sf` | LF × Height |
| `sf_div` | (LF × Height) ÷ qty_divisor |
| `depth` | LF × Depth |
| `volume_cy` | LF × Width × Depth ÷ 27 |

---

## Current Codebase State

### File Structure
```
Estimator Agent/
├── app.py                      ✅ Complete — all routes working
├── seed_csi.py                 ✅ Run once — do NOT re-run
├── NORTHSTAR.md                ✅ New — philosophy + architecture reference
├── Agent_MD_26.03.08v0.md      (Session 1 handoff)
├── Agent_MD_26.03.08v1.md      (Session 2 handoff)
├── Agent_MD_26.03.09v0.md      (this file)
└── Templates/
    ├── index.html              ✅ Library button added
    ├── new_project.html        ✅ Unchanged
    ├── project.html            ✅ Edit Assembly, Library nav, Builder button
    ├── summary.html            ✅ Unchanged
    ├── estimate.html           ✅ Unchanged (toggle views not yet built)
    ├── library.html            ✅ New — full library CRUD page
    └── assembly_builder.html   ✅ New — multi-section builder page
```

### Routes in app.py
| Method | Route | Purpose | Status |
|--------|-------|---------|--------|
| GET | `/` | Dashboard | ✅ |
| GET/POST | `/project/new` | Create project | ✅ |
| GET | `/project/<id>` | Project detail | ✅ |
| POST | `/project/<id>/assembly/new` | Quick create assembly | ✅ |
| POST | `/assembly/<id>/update` | Edit assembly | ✅ New |
| POST | `/assembly/<id>/lineitem/new` | Create line item | ✅ |
| GET | `/project/<id>/summary` | JSON cost rollup | ✅ |
| GET | `/project/<id>/report` | HTML cost summary | ✅ |
| GET | `/project/<id>/estimate` | Estimate table | ✅ |
| GET | `/project/<id>/assembly/builder` | Assembly builder page | ✅ New |
| POST | `/project/<id>/assembly/builder/save` | Save builder assembly | ✅ New |
| POST | `/lineitem/<id>/update` | Auto-save line item | ✅ |
| POST | `/lineitem/<id>/delete` | Delete line item | ✅ |
| POST | `/assembly/<id>/delete` | Delete assembly | ✅ |
| POST | `/project/<id>/delete` | Delete project | ✅ |
| GET | `/library` | Library browse page | ✅ New |
| POST | `/library/item/new` | Create library item | ✅ New |
| POST | `/library/item/<id>/update` | Edit library item | ✅ New |
| POST | `/library/item/<id>/delete` | Delete library item | ✅ New |

### ORM Models
| Model | Table | Status |
|-------|-------|--------|
| `CSILevel1` | `csi_level_1` | ✅ Seeded, unchanged |
| `CSILevel2` | `csi_level_2` | ✅ Seeded, unchanged |
| `Project` | `projects` | ✅ Unchanged |
| `Assembly` | `assemblies` | ✅ + `is_template`, `measurement_params` via migration |
| `AssemblyComposition` | `assembly_composition` | ✅ New — created by `db.create_all()` |
| `LibraryItem` | `library_items` | ✅ New — created by `db.create_all()` |
| `LineItem` | `line_items` | ✅ Unchanged |

---

## What's NOT Working / Known Issues

1. **Estimate view toggle not built** — `estimate.html` has toggle button structure (`Assembly | CSI | Trade`) but the CSI and Trade groupings are not yet implemented. Currently only Assembly View renders correctly. This is Step 6.

2. **No delete/edit in estimate.html** — The estimate table supports inline editing (auto-save) but has no delete buttons. Must go to project detail page to delete line items or assemblies.

3. **Trade/labor_category field missing from LineItem** — The Trade View in estimate.html needs a `trade` or `labor_category` field on line items. This DB column doesn't exist yet. Required for Step 6 Trade View toggle.

4. **LineItem has no direct CSI FK** — Currently CSI comes through the Assembly FK. For CSI grouping in estimate view (Step 6), `LineItem.csi_level_1_id` needs to be added as a direct column (migration required).

5. **Assembly Builder doesn't set Assembly CSI** — Assemblies created via the builder have `csi_level_1_id = NULL` and `csi_level_2_id = NULL`. The builder currently omits CSI dropdowns for simplicity. Line items created through the builder inherit no CSI directly. For Step 6 CSI grouping, line items need a CSI reference. Options: (a) add CSI dropdowns back to builder, or (b) derive CSI from the most common library item in the composition on save.

6. **Template Browse page not built** — Templates can be saved (the `is_template` flag works), but there's no page to browse and load saved templates. That's Phase 4.

7. **No authentication** — Single-user local app. Fine for now.

8. **equipment_hours = labor_hours hardcoded** — Known limitation.

---

## Exact Next Steps

### Step 6: Estimate Toggle Views (Next Up)

**What:** Add Assembly / CSI / Trade grouping to `estimate.html`. The JS toggle buttons already exist. The data (`items_json`) already carries CSI codes. Trade grouping needs a new DB field.

**Implementation plan:**

**Part A — CSI View (no DB changes needed):**
- `items_json` already includes `csi_level_1_code`, `csi_level_1_title`, `csi_level_2_code` (inherited from assembly)
- In `estimate.html` JS, add a `groupBy('csi')` render path that groups rows by `csi_level_1_code`
- Each group shows a colored header row with the division name + subtotals
- Wire the "CSI" toggle button to call this render path

**Part B — Trade View (requires DB migration):**
- Add `trade` column to `line_items` table via `run_migrations()` (ALTER TABLE ... ADD COLUMN IF NOT EXISTS)
- Add `trade` field to `LineItem` model in app.py
- Add `trade` to the `items` dict in `estimate_view` route
- In `estimate.html`: add a "Trade" column to the table (hidden by default, shown in Trade View); add a trade input to the Add Line Item modal; wire the "Trade" toggle button
- The trade field is a free-text string (e.g., "Concrete", "Framing", "Drywall") — no dropdown needed, users type it

**Part C — Color coding + collapsible groups:**
- Assign a color per CSI division (use a JS lookup table mapping division code → hex color)
- Group header rows get that color as a left border or background tint
- Click group header to collapse/expand its rows
- Subtotals per group shown in the group header row

**Part D — Fix CSI inheritance:**
- In `save_assembly_builder`, set `Assembly.csi_level_1_id` from the first library item's CSI (or leave null — acceptable tradeoff)
- In `estimate_view` route, when building `items`, if line item has no direct CSI, fall back to assembly's CSI — already done this way

### Step 7: Ollama / AI Layer
**What:** Wire local Ollama to Flask. Design as opt-in assistant.
- New route `POST /agent/suggest` — takes line item description + project location, sends to Ollama `http://localhost:11434/api/generate`, returns suggested pricing with reasoning
- In estimate table: "AI ✨" button on each row that opens a suggestion panel
- Show reasoning transparently: "Recommendation based on: [model's explanation]"
- Never auto-fill — user must click "Apply" to accept any AI suggestion

### Step 8: Export / Reporting
**What:** Printable/exportable outputs.
- PDF version of summary report — flag `weasyprint` or `pdfkit` before implementing (new pip dependency)
- CSV export of estimate table — no new dependencies
- CSI-structured detailed report as a new HTML template

---

## Key Decisions Made This Session

### Why `calculate_qty()` uses a dict dispatch instead of if/elif
Cleaner and easier to extend. Adding a new formula type = adding one line to the dict. The dict lookup pattern also mirrors the JS `switch` statement in the builder, making the backend and frontend behavior easier to verify side-by-side.

### Why Assembly Builder is a dedicated page, not a modal
The 5-section layout (info + measurements + library search + composition table + totals) is too complex for a modal. A dedicated page also allows the browser back button to work naturally. The existing "+ Quick Assembly" modal stays for traditional single-click assembly creation.

### Why the builder uses JSON serialization via hidden inputs
The composition array (variable length, nested data) can't be sent as standard HTML form fields. Serializing to JSON and sending in a hidden input is the cleanest approach that works without adding JavaScript frameworks. The server parses the JSON with `json.loads()`.

### Why run_migrations() instead of Flask-Migrate
Flask-Migrate (Alembic) adds a new dependency and requires migration files to be tracked. For a local single-user app, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in a startup function achieves the same result with zero new dependencies and no migration file management.

### Why library items and project line items are separate tables
A library item is a reusable template. A project line item is a cost record with a specific quantity, calculated costs, and an assembly parent. They serve different purposes. Mixing them would require nullable foreign keys and complex null-handling everywhere. The separation also means deleting a library item never affects existing project estimates.

---

## Important Constraints (Do Not Change)

- `/project/<id>/summary` **must stay JSON** — `project.html` fetches it on load for the totals bar
- `seed_csi.py` **must NOT be re-run** — CSI data is already in the DB
- Dark navy/red color scheme: `#1a1a2e` bg, `#16213e` card, `#0f3460` panel, `#e94560` accent
- JSON data embedding pattern: `<script id="..." type="application/json">` — do not use inline `var x = {{ data }}`
- Cascade delete handled in Python, not DB schema — do not add `ON DELETE CASCADE` to FK constraints

---

## Tech Stack

| Component | Tool | Status |
|---|---|---|
| Database | PostgreSQL (local) | ✅ Running |
| Backend | Python Flask | ✅ Running at localhost:5000 |
| ORM | Flask-SQLAlchemy | ✅ Working |
| Local AI Model | Ollama + Llama | ✅ Installed, NOT yet wired in |
| Frontend | HTML/CSS/Vanilla JS (Jinja templates) | ✅ All templates working |
| Backup | Dropbox | ✅ Auto-syncing |

**Start app:** `python .\app.py` from VS Code terminal
**URL:** `http://localhost:5000`

---

## Instructions for Claude (Next Session)

- **Read this file first**, then read `NORTHSTAR.md` for philosophy context before building anything
- **Step 6 is next** — Estimate Toggle Views. Start with CSI View (no DB changes), then add Trade field to LineItem (migration needed), then wire Trade View
- **Always generate complete, copy-pasteable code** — no partial snippets
- **Always maintain the dark navy/red color scheme**
- **Never change the database schema** without flagging it explicitly
- **Flag any new pip dependencies** before generating code that requires them
- **Do not convert `/project/<id>/summary` to HTML**
- **Build incrementally** — one feature at a time
