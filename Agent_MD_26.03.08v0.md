# Estimator AgentX — Session Handoff
**Session Date:** 2026-03-08
**Prepared by:** Claude (claude-sonnet-4-6)

---

## What Was Accomplished This Session

All 5 known bugs from the pre-session CLAUDE.md were resolved. The primary new feature (Estimate table view) was fully built. Here is the complete list:

### Bug Fixes

1. **`project.html` was truncated/broken** — FIXED
   - File was cut off at line ~140 mid-tag, leaving all modals and JS missing
   - Rewrote the complete file: assembly modal, line item modal, all JS functions, totals bar fetch
   - Added "Estimate" button linking to `/project/<id>/estimate`

2. **Missing `db.relationship()` on models** — FIXED
   - `Assembly.line_items` was referenced in templates but didn't exist as an ORM relationship
   - Added `db.relationship()` to all three models: `CSILevel1.subcodes`, `Project.assemblies`, `Assembly.line_items`

3. **Summary page was JSON-only** — FIXED
   - Created `Templates/summary.html` — full HTML cost summary report
   - Added `/project/<id>/report` route that renders it
   - **Important:** kept `/project/<id>/summary` as a JSON endpoint — `project.html` fetches it on load to populate the live totals bar. Do NOT convert it to HTML or that will break.

4. **CSI tables were empty** — FIXED
   - Created `seed_csi.py` — standalone script, run once with `python .\seed_csi.py`
   - Seeds 25 Level 1 divisions (00–34) and ~150 Level 2 sections for the most-used divisions
   - Idempotent: safe to re-run, checks before inserting

5. **Totals bar showed $0** — FIXED
   - The JS in `project.html` fetches `/project/<id>/summary` and populates the 4 cost cards on page load
   - `index.html` stats bar updated from hardcoded zeros to live Jinja: `total_value` and `active_count`
   - Both values come from real DB queries in the `index` route

### New Feature: Estimate Table View

Built the primary estimating interface — the core of the product.

- **Route:** `/project/<id>/estimate` → renders `Templates/estimate.html`
- **Route:** `/lineitem/<id>/update` (POST, JSON) → auto-save endpoint

**What the estimate table does:**
- 15-column scrollable table with sticky header
- All line items for the project in one view
- Group by: Assembly / CSI Division / CSI Section / Flat — toggle with button group, no reload
- Collapsible groups — click header to expand/collapse
- Roll-up totals shown in each group header row
- Project Total pinned at bottom
- Sortable columns — click any column header to sort asc/desc, ▲▼ indicator shows active sort
- **Inline editing** — click any editable cell (description, qty, unit, prod rate, mat$/unit, labor$/hr, equip$/hr) to get an input field; blur or Enter to save
- **Calculated cells** (labor hrs, material$, labor$, equip$, total$) shown in a dimmer color and update automatically — not directly editable
- **Auto-save** — blur/Enter triggers `fetch POST /lineitem/<id>/update`; optimistic local recalc runs immediately without waiting for server response
- **Live totals bar** (4 cards) updates on every edit
- Assembly modal and Line item modal work same as `project.html`
- "+" button in each group header pre-selects that assembly in the line item modal

---

## Current Codebase State

### File Structure
```
Estimator Agent/
├── app.py                    ✅ Complete — all routes working
├── seed_csi.py               ✅ New — run once to seed CSI data
├── CLAUDE.md                 (pre-session reference file)
├── Agent_MD_26.03.08v0.md    (this file)
└── Templates/
    ├── index.html             ✅ Working — live stats bar
    ├── new_project.html       ✅ Working — unchanged
    ├── project.html           ✅ Fixed — complete with modals & JS
    ├── summary.html           ✅ New — HTML cost summary report
    └── estimate.html          ✅ New — full Airtable-style estimate table
```

### Routes in app.py
| Method | Route | Purpose | Status |
|--------|-------|---------|--------|
| GET | `/` | Dashboard — live project stats + cards | ✅ Working |
| GET/POST | `/project/new` | Create project | ✅ Working |
| GET | `/project/<id>` | Project detail with assemblies & line items | ✅ Working |
| POST | `/project/<id>/assembly/new` | Create assembly | ✅ Working |
| POST | `/assembly/<id>/lineitem/new` | Create line item (calculates costs) | ✅ Working |
| GET | `/project/<id>/summary` | JSON cost rollup — used by project.html JS | ✅ Working |
| GET | `/project/<id>/report` | HTML cost summary page | ✅ New |
| GET | `/project/<id>/estimate` | Airtable-style estimate table | ✅ New |
| POST | `/lineitem/<id>/update` | Auto-save line item, recalculates costs | ✅ New |

### ORM Models (app.py)
All models have correct `db.relationship()` defined:
- `CSILevel1.subcodes` → list of `CSILevel2`
- `Project.assemblies` → list of `Assembly`
- `Assembly.line_items` → list of `LineItem`

---

## What's NOT Working / Known Issues

1. **CSI dropdowns in assembly modal** — The modal has no CSI fields yet. User has to enter CSI codes manually (or skip them). Need to add a Level 1 `<select>` and a dependent Level 2 `<select>` that filters based on the Level 1 choice. Requires either passing all CSI data to the template or a `/api/csi` JSON endpoint.

2. **No edit or delete** — There are no routes or UI for editing/deleting projects, assemblies, or line items (except inline edits in the estimate table). No delete buttons anywhere.

3. **Ollama / Llama not wired in** — Ollama is installed locally but has no connection to Flask. The AI agent features are 0% built.

4. **No authentication** — Single-user local app only. Fine for now.

5. **Equipment hours = labor hours hardcoded** — In both `new_line_item` and `update_line_item`, `equipment_hours = labor_hours`. This is fine as a default but some items will need separate equipment hour inputs.

6. **`production_rate_standards` table not created** — Referenced in CLAUDE.md as a lookup table, but the schema was never migrated. The `seed_csi.py` script only covers CSI data. This table doesn't exist in the DB yet.

---

## Exact Next Steps

Work through these in order. Test each one before starting the next.

### Step 1: CSI Dropdown Selectors in Assembly Modal (Highest Priority)
**What:** Replace the missing CSI fields in the assembly modal with real dropdowns.
- Pass CSI data to the project template: `csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()`
- Add a `<select>` for Level 1 in the modal
- Add a second `<select>` for Level 2 that reloads/filters when Level 1 changes (JS-driven, using embedded JSON of all CSI2 data, filter client-side)
- Same dropdowns needed in the estimate.html assembly modal

**Why this matters:** Currently assemblies can only be created with no CSI tagging, which breaks the "Group by CSI Division" and "Group by CSI Section" views in the estimate table.

### Step 2: Delete Routes
**What:** Add delete buttons + confirmation dialogs + routes for:
- Delete line item: `DELETE /lineitem/<id>` (or `POST /lineitem/<id>/delete`)
- Delete assembly: `DELETE /assembly/<id>` (cascade deletes its line items)
- Delete project: `DELETE /project/<id>` (cascade deletes everything)

**Note on cascade:** Make sure PostgreSQL cascade delete is configured or handle it in Python.

### Step 3: Edit Assembly
**What:** Allow editing assembly label, name, CSI codes, qty, and unit after creation.
- Add an "Edit" button on each assembly card in `project.html`
- Reuse the assembly modal form, pre-populated with current values
- Add `PUT /assembly/<id>` or `POST /assembly/<id>/update` route

### Step 4: Ollama / Llama Integration
**What:** Wire up the local LLM for AI-assisted estimating.
- Start with a simple "research pricing" tool: user clicks a line item → AI suggests material cost based on item description and location
- Use Ollama's REST API (`http://localhost:11434/api/generate`)
- Add a Flask proxy route `/agent/suggest` that sends the line item description + project location to Ollama and returns a suggested price
- In the estimate table, add a small "AI ✨" button on each editable row

### Step 5: Export / Reporting
**What:** Generate printable/exportable outputs from the estimate.
- PDF version of `summary.html` — use `weasyprint` or `pdfkit` (flag as a new pip dependency)
- CSI-structured detailed report: line items grouped and subtotaled by CSI Division
- Bid proposal template: project info header + cost summary + optional markup/contingency fields

### Step 6: Production Rate Library
**What:** Let users pick from standard production rates rather than typing from memory.
- Create the `production_rate_standards` table in DB (need migration or `db.create_all()`)
- Seed with common rates (excavation, concrete, framing, drywall, etc.)
- Add a searchable modal in the estimate table: "Browse Rates" → filter by trade/keyword → click to apply to current line item

---

## Important Decisions & Context (Why We Did It This Way)

### Two endpoints for summary
Kept `/project/<id>/summary` as a JSON endpoint and created a separate `/project/<id>/report` for the HTML view. The JS in `project.html` fetches the JSON endpoint on every page load to populate the live totals bar. If that endpoint had been converted to HTML, it would have silently broken the totals display. Any future changes to the summary page should maintain this split.

### JSON data embedding in estimate.html
Used `<script id="itemsData" type="application/json">{{ items_json | safe }}</script>` to pass the line item data to the JS. This is safer than directly assigning to a JS variable with `| safe` (which can allow XSS if the data contains `</script>`). JS reads it with `JSON.parse(document.getElementById('itemsData').textContent)`.

### Optimistic updates in estimate table
When a cell is saved, the JS recalculates all derived fields locally immediately, without waiting for the server response. The server response then confirms or corrects the values. This makes the table feel instant even on a local server. If the server ever returns different values (e.g., rounding differences), the UI corrects itself after the fetch completes.

### Grouping and sorting are client-side only
All grouping, sorting, and roll-up calculations in the estimate table happen in JavaScript using the initial data payload. No page reloads needed when switching group mode or sort column. This keeps the UX fast and keeps the server simple. The tradeoff: if two users were editing the same estimate simultaneously, they wouldn't see each other's changes without a page reload. Acceptable for a single-user local tool.

### Equipment hours tied to labor hours
In the calculation logic, `equipment_hours = labor_hours` by default. This is correct for most items (one piece of equipment runs as long as the crew is working). Items where equipment is rented separately (e.g., a crane on-site for one day, labor for a week) will need a separate equipment hours input. This is a known limitation noted for future enhancement.

---

## UI Design Rules — DO NOT CHANGE

| Element | Value |
|---|---|
| Page background | `#1a1a2e` |
| Card/container background | `#16213e` |
| Panel/input background | `#0f3460` |
| Deep panel background | `#0d1b2a` |
| Primary accent (buttons, labels, headers) | `#e94560` |
| Primary accent hover | `#c73652` |
| Secondary button | `#0f3460` |
| Body text | `#eee` |
| Muted text | `#888` or `#aaa` |
| Table header background | `#0f3460` |
| Table row hover | `#1a2a3a` |
| Border color | `#0f3460` |
| Border radius | `8px` or `4px` |
| Font | `Arial, sans-serif` |

---

## Tech Stack

| Component | Tool | Status |
|---|---|---|
| Database | PostgreSQL (local) | ✅ Running |
| Backend | Python Flask | ✅ Running at localhost:5000 |
| ORM | Flask-SQLAlchemy | ✅ Working |
| Code Editor | Visual Studio Code | ✅ Installed |
| Local AI Model | Ollama + Llama | ✅ Installed, NOT yet wired in |
| Frontend | HTML/CSS/JS (Jinja templates) | ✅ All templates working |
| Backup | Dropbox | ✅ Auto-syncing |

**Start app:** `python .\app.py` from VS Code terminal
**URL:** `http://localhost:5000`
**Seed CSI data (run once):** `python .\seed_csi.py`

**Project folder:** `C:\Users\Tknig\Dropbox\Estimator Agent`
**Database:** `estimator_db` on port 5432, user `postgres`

---

## Instructions for Claude (Next Session)

- **Always generate complete, copy-pasteable code.** No partial snippets unless asked.
- **Always maintain the dark navy/red color scheme** defined above.
- **Explain what each piece of code does** in plain English — the owner is not a developer.
- **Give step-by-step terminal commands** when installation or setup is needed. Assume Windows + VS Code terminal.
- **Never change the database schema** without flagging it and explaining the impact.
- **Flag any new pip dependencies** before generating code that requires them.
- **Do not convert `/project/<id>/summary` to HTML** — it is a JSON endpoint used by `project.html` JS.
- **Build incrementally** — one feature at a time, confirm before moving on.
