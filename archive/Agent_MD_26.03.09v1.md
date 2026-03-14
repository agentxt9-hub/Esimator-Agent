# Estimator AgentX — Session Handoff
**Session Date:** 2026-03-09 (Session 4)
**Prepared by:** Claude (claude-sonnet-4-6)

---

## What Was Accomplished This Session

### Step 6: Estimate Toggle Views ✅ (discovered already built)
Already fully implemented in `estimate.html` before session start:
- Assembly / CSI Division / CSI Section / Trade / Flat grouping buttons
- Collapsible group header rows with subtotals
- Color-coded left borders per CSI division (`CSI_COLORS` lookup)
- Trade column (hidden by default, revealed in Trade View via `.show-trade` class)
- Sort by any column (click header)

### Step 7: Ollama / AI Layer ✅ (discovered already built)
Already fully implemented before session start:
- `POST /agent/suggest` — proxies to `http://localhost:11434/api/generate` with llama3.2
- Slide-in AI panel in estimate.html — shows reasoning text, comparison table (current vs suggested)
- "Apply Suggestions" button — user must click to accept; never auto-fills
- Handles Ollama not running gracefully (error message in panel)

### Step 8: Export / Reporting ✅ (built this session)

#### CSV Export
- `GET /project/<id>/estimate/csv` — new route in app.py
- Python stdlib `csv` + `io.StringIO` — no new pip dependencies
- Returns `Response` with `Content-Disposition: attachment` header
- Filename sanitized from project name + number via `re.sub`
- Columns: Assembly, Assembly Name, CSI Division, CSI Section, Description, Trade, Qty, Unit, Prod Rate, Labor Hrs, Mat $/Unit, Material $, Labor $/Hr, Labor $, Equip $/Hr, Equipment $, Total $, Notes

#### CSI Report
- `GET /project/<id>/report/csi` — new route in app.py
- Server-side grouping: division → section → line items; subtotals at each level
- `CSI_COLORS` dict at module level (keyed by 2-digit code prefix) used by both server and client
- `Templates/csi_report.html` — new template:
  - 5 grand total cards (Material, Labor, Equipment, Labor Hours, Total)
  - Per-division color-coded blocks (`border-left: 5px solid {color}`)
  - Per-section tables with 14 columns of line item detail
  - Section subtotals, division totals, project grand total
  - "No CSI Division Assigned" block for uncategorized items
  - `@media print` — light background, hidden nav, static headers

#### Print Buttons + Nav Links
- `estimate.html` — added CSI Report, Export CSV, Print buttons to header btn-row; added `@media print` CSS
- `summary.html` — added Estimate, CSI Report, Export CSV, Print buttons

### Phase 4: Assembly Templates Browse ✅ (built this session)

#### New Routes in app.py
- `GET /templates` — queries `Assembly.is_template=True`, builds template card data (measurements, composition preview, cost total), passes all projects for the load modal
- `POST /project/<id>/assembly/load-template/<template_id>` — clones template assembly + all `AssemblyComposition` records + all `LineItem` records into target project; sets `is_template=False` on the clone

#### Assembly Builder Template Pre-load
- `GET /project/<id>/assembly/builder` now accepts `?from_template=<id>` query param
- Queries the template assembly, serializes its composition + measurements as `template_json`
- In `assembly_builder.html` JS init: if `templatePreload` is not null, pre-fills all form fields and composition array, then recalculates quantities live from the loaded measurements

#### templates.html — New Page
- Client-side search (name, label, CSI, description)
- Template cards showing: label badge, name, CSI, measurement chips (LF/H/D/W), first 4 composition items with formula tags, estimated total cost
- "Use Template" button → modal with:
  - Target project dropdown (all projects)
  - Label override field (pre-filled with template's label)
  - "Load Directly" — POSTs to load-template route, redirects to project
  - "Customize in Builder" — redirects to builder with `?from_template=<id>` param
- Empty state when no templates exist yet (explains how to create one)

#### Nav Links
- `index.html` — "Assembly Templates" button added next to Library
- `project.html` — "Templates" button added to header nav

---

## Current Codebase State

### File Structure
```
Estimator Agent/
├── app.py                      ✅ Complete — all routes working
├── seed_csi.py                 ✅ Run once — do NOT re-run
├── NORTHSTAR.md                ✅ Philosophy + architecture reference
├── Agent_MD_26.03.08v0.md      (Session 1)
├── Agent_MD_26.03.08v1.md      (Session 2)
├── Agent_MD_26.03.09v0.md      (Session 3)
├── Agent_MD_26.03.09v1.md      (this file)
└── Templates/
    ├── index.html              ✅ Library + Templates nav buttons
    ├── new_project.html        ✅ Unchanged
    ├── project.html            ✅ Templates nav button added
    ├── summary.html            ✅ Estimate + CSI Report + CSV + Print buttons
    ├── estimate.html           ✅ Full estimate — grouping, AI, CSV, CSI Report, Print
    ├── library.html            ✅ Full library CRUD
    ├── assembly_builder.html   ✅ Builder + template pre-load support
    ├── csi_report.html         ✅ New — CSI-grouped report with print
    └── templates.html          ✅ New — template browse + load/builder launch
```

### All Routes in app.py
| Method | Route | Purpose | Status |
|--------|-------|---------|--------|
| GET | `/` | Dashboard | ✅ |
| GET/POST | `/project/new` | Create project | ✅ |
| GET | `/project/<id>` | Project detail | ✅ |
| POST | `/project/<id>/assembly/new` | Quick create assembly | ✅ |
| POST | `/assembly/<id>/update` | Edit assembly | ✅ |
| POST | `/assembly/<id>/lineitem/new` | Create line item | ✅ |
| GET | `/project/<id>/summary` | **JSON only** — live totals for project.html | ✅ |
| GET | `/project/<id>/report` | HTML assembly summary | ✅ |
| GET | `/project/<id>/estimate` | Estimate table (grouping, AI, inline edit) | ✅ |
| GET | `/project/<id>/estimate/csv` | CSV download | ✅ |
| GET | `/project/<id>/report/csi` | CSI-structured HTML report | ✅ |
| GET | `/project/<id>/assembly/builder` | Assembly Builder (`?from_template=<id>` supported) | ✅ |
| POST | `/project/<id>/assembly/builder/save` | Save builder assembly | ✅ |
| GET | `/templates` | Browse all templates | ✅ |
| POST | `/project/<id>/assembly/load-template/<tid>` | Clone template into project | ✅ |
| POST | `/lineitem/<id>/update` | Auto-save + recalculate line item | ✅ |
| POST | `/lineitem/<id>/delete` | Delete line item | ✅ |
| POST | `/assembly/<id>/delete` | Delete assembly + children | ✅ |
| POST | `/project/<id>/delete` | Delete project + children | ✅ |
| GET | `/library` | Library browse page | ✅ |
| POST | `/library/item/new` | Create library item | ✅ |
| POST | `/library/item/<id>/update` | Edit library item | ✅ |
| POST | `/library/item/<id>/delete` | Delete library item | ✅ |
| POST | `/agent/suggest` | Ollama AI suggestion | ✅ |

### ORM Models
| Model | Table | Status |
|-------|-------|--------|
| `CSILevel1` | `csi_level_1` | ✅ Seeded |
| `CSILevel2` | `csi_level_2` | ✅ Seeded |
| `Project` | `projects` | ✅ |
| `Assembly` | `assemblies` | ✅ incl. `is_template`, `measurement_params` |
| `AssemblyComposition` | `assembly_composition` | ✅ |
| `LibraryItem` | `library_items` | ✅ |
| `LineItem` | `line_items` | ✅ incl. `trade` |

---

## What's NOT Working / Known Issues

1. **No delete buttons in estimate.html** — inline editing works but no delete. Must go to project detail page to delete line items or assemblies. Low priority.

2. **No authentication** — single-user local app. Fine for now.

3. **equipment_hours = labor_hours hardcoded** — known limitation; separate equipment tracking is a future concern.

4. **Template cost display is "at time of creation"** — the total shown on template cards is the cost from when the template was saved, not recalculated at browse time. If rates change, template preview won't reflect that. Acceptable tradeoff.

5. **Templates page shows "Estimated total" using saved costs** — when loaded via "Load Directly", the cloned line items use stored costs (no recalculation). This is intentional: predictable behavior. "Customize in Builder" is the path for adjusting measurements/costs.

6. **Template must have `AssemblyComposition` records to be useful in Builder** — assemblies created via "Quick Assembly" (modal, not builder) have no composition records. Loading them into the builder via `?from_template` will show an empty composition. Non-blocking: user can still add items.

7. **No PDF export** — Print-to-PDF via browser is the current workaround. `weasyprint`/`pdfkit` would add a pip dependency; flag before adding.

---

## What's Next

### All major roadmap phases complete. Options for future sessions:

**Polish / UX improvements (no new features):**
- Add delete buttons to estimate.html rows (soft delete with confirmation)
- Edit project details (name, number, location) — currently no edit route exists for Project model
- Better empty states and loading indicators
- Keyboard shortcut to close modals (Escape key in estimate modal)

**New capabilities:**
- **Bid Proposal output** — formatted cover page + cost breakdown, more professional than the current summary. Good candidate for a new template.
- **Project duplication** — clone an entire project (all assemblies + line items) as a starting point
- **Assembly template tagging / categories** — free-text tags on templates to group by work type
- **Production rate standards table** — lookup table for standard production rates by trade/CSI, integrated into library items and assembly builder
- **Multi-project comparison** — side-by-side cost comparison across projects (useful for bid alternates)

**AI / Ollama enhancements:**
- Bulk AI review — button to get suggestions for all line items at once (queue-based)
- AI summary narrative — generate a project cost narrative paragraph for proposals

---

## Key Decisions Made This Session

### Why "Load Directly" clones stored costs instead of recalculating
When a template is loaded directly, the estimator expects the saved costs (with all their context — rates at a specific point in time, for a specific job type). Recalculating would require new measurements, which is what "Customize in Builder" is for. The two paths serve different needs: speed (Load Directly) vs. precision (Builder).

### Why template_json passes null instead of omitting the script tag
Jinja `{{ template_json | safe }}` always emits the tag whether or not there's a template. When no template is requested, `template_data = None` → `json.dumps(None)` → the JSON literal `null`. The JS reads `JSON.parse(...) === null` and skips the pre-fill block. No conditional template logic needed.

### Why CSI_COLORS is defined at module level in app.py
Both the `csi_report` route (server-side coloring) and `estimate.html` (client-side JS) need the same color mapping. Defining it once in app.py keeps it DRY on the server side. The JS copy in estimate.html is a second source of truth — acceptable because colors don't change.

---

## Important Constraints (Do Not Change)

- `/project/<id>/summary` **must stay JSON** — `project.html` fetches it on load for the live totals bar
- `seed_csi.py` **must NOT be re-run** — CSI data is already in the DB
- Dark navy/red color scheme: `#1a1a2e` bg, `#16213e` card, `#0f3460` panel, `#e94560` accent
- JSON data embedding: `<script id="..." type="application/json">{{ data | safe }}</script>`
- Cascade delete in Python (not DB schema)
- `run_migrations()` uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — extend this pattern for any new columns

---

## Tech Stack

| Component | Tool | Status |
|---|---|---|
| Database | PostgreSQL (local) | ✅ Running |
| Backend | Python Flask | ✅ Running at localhost:5000 |
| ORM | Flask-SQLAlchemy | ✅ Working |
| Local AI | Ollama + llama3.2 | ✅ Wired in |
| Frontend | HTML/CSS/Vanilla JS (Jinja templates) | ✅ All templates working |
| Backup | Dropbox | ✅ Auto-syncing |

**Start app:** `python .\app.py` from VS Code terminal
**URL:** `http://localhost:5000`

---

## Instructions for Claude (Next Session)

- **Read this file first**, then `NORTHSTAR.md` for philosophy context
- **All major roadmap phases are complete** — confirm with user what they want next before building
- **Always generate complete, copy-pasteable code** — no partial snippets
- **Always maintain the dark navy/red color scheme**
- **Never change the database schema** without flagging it explicitly and adding to `run_migrations()`
- **Flag any new pip dependencies** before generating code that requires them
- **Do not convert `/project/<id>/summary` to HTML**
- **Build incrementally** — one feature at a time, confirm it works before moving on
