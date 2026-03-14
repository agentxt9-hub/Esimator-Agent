# Estimator AgentX — Session Handoff
**Session Date:** 2026-03-10 (Session 5)
**Prepared by:** Claude (claude-sonnet-4-6)

---

## What Was Accomplished This Session

### CLAUDE.md Created ✅
Created `CLAUDE.md` at the project root — the standard onboarding file for Claude Code instances. Contains:
- How to run the app and the "do not re-run seed_csi.py" warning
- Architecture overview (single-file Flask, data flow chain, key models)
- Critical patterns that are easy to break (JSON-only summary route, cascade delete in Python, CSI dropdown pattern, JSON embedding, schema migration pattern)
- UI color rules and the `CSI_COLORS` sync requirement
- The NORTHSTAR design test in one sentence
- Known gaps

### Full App Audit ✅
Fetched and reviewed all pages at localhost:5000. Findings:

| Page | Status | Finding |
|------|--------|---------|
| `/` | 200 ✓ | Clean |
| `/library` | 200 ✓ | Clean |
| `/templates` | 200 ✓ | Clean — empty state correct (no templates yet) |
| `/project/new` | 200 ✓ | Clean |
| `/project/1` | 200 ✓ | Totals bar $0 in raw HTML (JS-populated, not a bug) |
| `/project/1/report` | **500 ✗ → fixed** | KeyError: 'total_total_cost' |
| `/project/1/estimate` | 200 ✓ | Clean |
| `/project/1/report/csi` | 200 ✓ | Clean (items show uncategorized — data issue) |
| `/project/1/assembly/builder` | 200 ✓ | Clean |

### Bug Fix: `KeyError: 'total_total_cost'` in `/project/<id>/report` ✅
**Root cause:** In `project_report()`, a loop iterated over keys including `'total_cost'`, then did `summary['total_' + key]` — creating `'total_total_cost'` which didn't exist in the summary dict.

**Fix in [app.py:290-292](app.py):**
```python
# Before (broken):
for key in ('material_cost', 'labor_cost', 'labor_hours', 'equipment_cost', 'equipment_hours', 'total_cost'):
    summary['total_' + key] += row[key]

# After (fixed):
for key in ('material_cost', 'labor_cost', 'labor_hours', 'equipment_cost', 'equipment_hours'):
    summary['total_' + key] += row[key]
summary['total_cost'] += row['total_cost']
```

### `datetime.utcnow()` Deprecation Fixed ✅
Python 3.14 warns that `datetime.utcnow()` is deprecated. Fixed throughout app.py:
- Import changed: `from datetime import datetime` → `from datetime import datetime, timezone`
- All `default=datetime.utcnow` model column defaults (10 occurrences) → `default=lambda: datetime.now(timezone.utc)`
- All `datetime.utcnow()` direct calls (3 occurrences: `update_assembly`, `update_line_item`, `csi_report`) → `datetime.now(timezone.utc)`

Zero deprecation warnings remain.

---

## Data Issues Noted (Not Code Bugs)
- Test project name: "Medical Office **Buidling**" (typo — user data)
- Test assembly name: "Drywall **Partion**" (typo — user data)
- All line items show as "Uncategorized" in CSI report — assemblies were never given a CSI division at creation time
- Only 1 library item — user hasn't populated it yet

---

## Current Codebase State

### File Structure
```
Estimator Agent/
├── app.py                      ✅ Complete — all routes working, warnings clean
├── seed_csi.py                 ✅ Run once — DO NOT re-run
├── CLAUDE.md                   ✅ New — Claude Code onboarding file
├── NORTHSTAR.md                ✅ Philosophy + architecture reference
├── Agent_MD_26.03.08v0.md      (Session 1)
├── Agent_MD_26.03.08v1.md      (Session 2)
├── Agent_MD_26.03.09v0.md      (Session 3)
├── Agent_MD_26.03.09v1.md      (Session 4)
├── Agent_MD_26.03.10v0.md      (this file)
└── Templates/
    ├── index.html              ✅
    ├── new_project.html        ✅
    ├── project.html            ✅
    ├── summary.html            ✅
    ├── estimate.html           ✅
    ├── library.html            ✅
    ├── assembly_builder.html   ✅
    ├── csi_report.html         ✅
    └── templates.html          ✅
```

### All HTTP Status (confirmed this session)
All 21 routes return correct responses. No 500 errors. No deprecation warnings.

---

## What's NOT Working / Known Issues

1. **No delete buttons in estimate.html** — must use project detail page. Low priority.
2. **No Edit Project UI** — project name/number/location can't be changed after creation.
3. **No authentication** — single-user local app. Fine for now.
4. **equipment_hours = labor_hours hardcoded** — known limitation.
5. **Template cost display is "at time of creation"** — not recalculated at browse time. Intentional.
6. **All line items uncategorized in CSI report** — because test assemblies have no CSI assigned. Not a bug.

---

## What's Next (Options)

**Polish / UX:**
- Add delete buttons to estimate.html rows (soft delete with confirmation)
- Add Edit Project route + UI (name, number, location, description)
- Better empty states, loading indicators

**New capabilities:**
- **Bid Proposal output** — formatted cover page + cost breakdown for clients
- **Project duplication** — clone entire project as a starting point
- **Assembly template tagging** — free-text tags to group templates by work type
- **Production rate standards table** — lookup library for standard rates by CSI/trade
- **Multi-project comparison** — side-by-side cost view for bid alternates

**AI enhancements:**
- Bulk AI review — queue all line items for suggestions at once
- AI narrative summary — generate a cost narrative paragraph for proposals

---

## Important Constraints (Do Not Change)

- `/project/<id>/summary` **must stay JSON** — project.html fetches it on load for the totals bar
- `seed_csi.py` **must NOT be re-run** — CSI data is already in the DB
- Dark navy/red color scheme: `#1a1a2e` bg, `#16213e` card, `#0f3460` panel, `#e94560` accent
- JSON data embedding: `<script id="..." type="application/json">{{ data | safe }}</script>`
- Cascade delete handled in Python, not DB schema
- Schema migrations: always extend `run_migrations()` with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- `datetime.now(timezone.utc)` — do NOT use `datetime.utcnow()` (deprecated in Python 3.14)

---

## Tech Stack

| Component | Tool | Notes |
|---|---|---|
| Database | PostgreSQL (local) | `postgresql://postgres:Builder@localhost:5432/estimator_db` |
| Backend | Python 3.14 / Flask | `python app.py` → localhost:5000 |
| ORM | Flask-SQLAlchemy | |
| Local AI | Ollama + llama3.2 | Optional; `ollama serve` to start |
| Frontend | HTML/CSS/Vanilla JS (Jinja) | No frameworks |
| Backup | Dropbox | Auto-syncing |

---

## Instructions for Claude (Next Session)

- **Read CLAUDE.md first** — it's the quick-start reference
- **Read this file** for session context, then NORTHSTAR.md for philosophy
- **All major roadmap phases are complete** — confirm with user what they want next
- **Always maintain the dark navy/red color scheme**
- **Never change the database schema** without flagging + extending `run_migrations()`
- **Flag any new pip dependencies** before generating code that requires them
- **Use `datetime.now(timezone.utc)`** — never `datetime.utcnow()`
