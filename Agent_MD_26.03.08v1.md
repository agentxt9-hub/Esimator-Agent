# Estimator AgentX — Session Handoff
**Session Date:** 2026-03-08 (Session 2)
**Prepared by:** Claude (claude-sonnet-4-6)

---

## What Was Accomplished This Session

### Feature: CSI Dropdown Selectors in Assembly Modal (Step 1)

Replaced missing CSI fields in the assembly modal with real, working dropdowns on both `project.html` and `estimate.html`.

**What changed:**
- `app.py` — `view_project` route now queries all CSI Level 1 and Level 2 records and passes them to `project.html` as: `csi1_list` (for Jinja loop), `csi2_json` (for JS filtering), `csi1_map` and `csi2_map` (dicts for displaying codes on assembly cards)
- `app.py` — `estimate_view` route now passes `csi1_json` and `csi2_json` to `estimate.html`
- `project.html` — Assembly modal has two new dropdowns: CSI Division (Level 1) and CSI Section (Level 2). Level 2 filters dynamically via JS when Level 1 is selected. Assembly cards now show the actual CSI code + title (e.g., "03 — Concrete") instead of raw integer IDs.
- `estimate.html` — Same CSI dropdowns added to the assembly modal. CSI1 options are populated by JS from embedded JSON at page load (same pattern as other data). Level 2 filters dynamically.
- Both modals reset their CSI dropdowns to blank each time they are opened.
- CSI seed data was confirmed in the database — `python .\seed_csi.py` was run successfully. 25 divisions and ~150 sections are now permanently stored in PostgreSQL.

### Feature: Delete Routes (Step 2)

Added delete capability for all three levels: line items, assemblies, and projects.

**What changed:**
- `app.py` — 3 new routes:
  - `POST /lineitem/<id>/delete` — deletes one line item
  - `POST /assembly/<id>/delete` — deletes all its line items first, then the assembly
  - `POST /project/<id>/delete` — deletes all line items → all assemblies → the project (Python-level cascade, no DB schema change)
- `project.html` — Each line item row has a small red **✕** button at the right end. Each assembly header has a **Delete Assembly** button next to "+ Add Line Item". Both show a `confirm()` dialog before proceeding.
- `index.html` — Each project card has a **Delete** button. Confirmation dialog warns that all assemblies and line items will be permanently removed.
- Added `.btn-danger` and `.btn-sm` CSS classes to both `project.html` and `index.html`.

---

## Current Codebase State

### File Structure
```
Estimator Agent/
├── app.py                    ✅ Complete — all routes working
├── seed_csi.py               ✅ Run once — CSI data is in DB, do not re-run
├── CLAUDE.md                 (original reference file)
├── Agent_MD_26.03.08v0.md    (previous session handoff)
├── Agent_MD_26.03.08v1.md    (this file)
└── Templates/
    ├── index.html             ✅ Working — live stats bar, delete buttons on cards
    ├── new_project.html       ✅ Working — unchanged
    ├── project.html           ✅ Working — CSI dropdowns, delete buttons on assemblies/items
    ├── summary.html           ✅ Working — HTML cost summary report
    └── estimate.html          ✅ Working — full estimate table, CSI dropdowns in assembly modal
```

### Routes in app.py
| Method | Route | Purpose | Status |
|--------|-------|---------|--------|
| GET | `/` | Dashboard — live project stats + cards | ✅ Working |
| GET/POST | `/project/new` | Create project | ✅ Working |
| GET | `/project/<id>` | Project detail with assemblies & line items | ✅ Working |
| POST | `/project/<id>/assembly/new` | Create assembly (now saves CSI IDs) | ✅ Working |
| POST | `/assembly/<id>/lineitem/new` | Create line item (calculates costs) | ✅ Working |
| GET | `/project/<id>/summary` | JSON cost rollup — used by project.html JS | ✅ Working |
| GET | `/project/<id>/report` | HTML cost summary page | ✅ Working |
| GET | `/project/<id>/estimate` | Airtable-style estimate table | ✅ Working |
| POST | `/lineitem/<id>/update` | Auto-save line item, recalculates costs | ✅ Working |
| POST | `/lineitem/<id>/delete` | Delete one line item | ✅ New |
| POST | `/assembly/<id>/delete` | Delete assembly + all its line items | ✅ New |
| POST | `/project/<id>/delete` | Delete project + all assemblies + all line items | ✅ New |

### ORM Models (app.py)
All models have correct `db.relationship()` defined:
- `CSILevel1.subcodes` → list of `CSILevel2`
- `Project.assemblies` → list of `Assembly`
- `Assembly.line_items` → list of `LineItem`

---

## What's NOT Working / Known Issues

1. **No Edit Assembly** — The "Edit Assembly" feature (Step 3) was not started this session. There is no way to change an assembly's label, name, CSI codes, qty, or unit after it is created. The plan is to reuse the assembly modal, pre-populate it with current values, and submit to a new `POST /assembly/<id>/update` route.

2. **No Edit Project** — Project name, number, location, description cannot be changed after creation. Not yet planned.

3. **Ollama / Llama not wired in** — Ollama is installed locally but has no connection to Flask. AI agent features are 0% built.

4. **No authentication** — Single-user local app only. Fine for now.

5. **Equipment hours = labor hours hardcoded** — `equipment_hours = labor_hours` by default in both create and update routes. Known limitation.

6. **`production_rate_standards` table not created** — Referenced in original CLAUDE.md as a lookup table. The schema was never migrated. Does not exist in the DB yet.

7. **No edit/delete in estimate.html** — The estimate table has inline editing for line item values (auto-save), but no delete button for line items, and no assembly management buttons. If a user wants to delete or edit assemblies they must go to the project detail page.

---

## Exact Next Steps

Work through these in order. Test each before starting the next.

### Step 3: Edit Assembly (Next Up)
**What:** Allow editing assembly label, name, CSI codes, qty, and unit after creation.

**Implementation plan:**
- Add `POST /assembly/<id>/update` route in `app.py` — accepts same form fields as `new_assembly`, updates the record in place
- Reuse the existing assembly modal in `project.html` — set a hidden field `assembly_edit_id` that is empty for "create" mode and holds the assembly ID for "edit" mode
- Change the form's `onsubmit` to call `saveAssembly(event, projectId)` which checks whether `assembly_edit_id` is set and sends to either `/project/<id>/assembly/new` or `/assembly/<id>/update`
- Change the modal title between "Add Assembly" and "Edit Assembly" based on mode
- Add an **Edit** button to each assembly header (next to the existing "+ Add Line Item" and "Delete Assembly" buttons)
- The Edit button calls `openEditAssemblyModal(assemblyData)` — a JS function that pre-fills all fields, sets the CSI dropdowns (including filtering Level 2 for the current Level 1 selection), and opens the modal in edit mode
- Assembly data for edit pre-population needs to be embedded in the page as JSON (same pattern as other data) since Jinja doesn't run on button click
- After successful update, reload the page

**Why reuse the modal instead of a separate one:** Keeps the HTML smaller and ensures CSI dropdown behavior is identical between create and edit.

### Step 4: Ollama / Llama Integration
**What:** Wire up the local LLM for AI-assisted estimating.
- Start with a simple "research pricing" tool: user clicks a line item → AI suggests material cost based on item description and location
- Use Ollama's REST API (`http://localhost:11434/api/generate`)
- Add a Flask proxy route `/agent/suggest` that sends the line item description + project location to Ollama and returns a suggested price
- In the estimate table, add a small "AI ✨" button on each editable row

### Step 5: Export / Reporting
**What:** Generate printable/exportable outputs from the estimate.
- PDF version of `summary.html` — use `weasyprint` or `pdfkit` (new pip dependency, flag before implementing)
- CSI-structured detailed report: line items grouped and subtotaled by CSI Division
- Bid proposal template: project info header + cost summary + optional markup/contingency fields

### Step 6: Production Rate Library
**What:** Let users pick from standard production rates rather than typing from memory.
- Create the `production_rate_standards` table in DB (need migration or `db.create_all()`)
- Seed with common rates (excavation, concrete, framing, drywall, etc.)
- Add a searchable modal in the estimate table

---

## Important Decisions & Context

### Cascade delete handled in Python, not PostgreSQL
We delete child records in Python before deleting the parent (e.g., delete all LineItems before deleting Assembly). This avoids needing to alter foreign key constraints or add `ON DELETE CASCADE` to the DB schema. The tradeoff: if the Python loop were interrupted mid-delete, orphaned records could remain. Acceptable for a single-user local app with no concurrent access.

### CSI dropdowns: Level 1 server-rendered, Level 2 JS-rendered
Level 1 options are rendered by Jinja in the HTML at page load (simple, no JS needed). Level 2 options are generated by JS filtering a JSON payload, because they depend on the user's Level 1 selection at runtime. This avoids a round-trip API call on every Level 1 change.

### Two endpoints for summary (unchanged from v0)
`/project/<id>/summary` remains a JSON endpoint — `project.html` fetches it on every page load to populate the live totals bar. `/project/<id>/report` is the HTML version. **Do not convert the JSON endpoint to HTML.**

### JSON data embedding pattern
All data passed to JS uses `<script id="..." type="application/json">{{ data | safe }}</script>` with `JSON.parse(document.getElementById('...').textContent)` in JS. This is XSS-safe because the browser treats `type="application/json"` as non-executable.

### Optimistic updates in estimate table (unchanged from v0)
When a cell is saved in the estimate table, JS recalculates all derived fields locally immediately, without waiting for the server response. The server response then confirms or corrects. Makes the table feel instant.

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
| Danger button background | `#3a0a12` |
| Danger button text | `#e94560` |
| Danger button hover | `#e94560` bg, white text |
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
**Seed CSI data:** Already done — do NOT run `seed_csi.py` again

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
- **Next task is Step 3: Edit Assembly** — see the detailed implementation plan above.
