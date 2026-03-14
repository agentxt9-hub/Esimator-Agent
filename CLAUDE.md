# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install dependencies
pip install flask psycopg2-binary sqlalchemy flask-sqlalchemy

# Start the Flask dev server
python app.py
```

App runs at `http://localhost:5000`. Requires PostgreSQL at `localhost:5432/estimator_db` (user: `postgres`, password: `Builder`).

**Do not run `seed_csi.py`** — CSI data is already seeded in the database.

## Architecture

Single-file Flask app (`app.py`) with Jinja2 templates in `Templates/`. No frontend framework — vanilla JS + `fetch()` throughout. No test suite.

**Data flow:**
```
Assembly measurements (user input)
    → qty_formula per composition item → derived quantities
    → production_rate → labor/equipment hours
    → cost rates → line item costs
    → grouped/summed → project totals
```

**Key models** (all in `app.py`):
- `CSILevel1` / `CSILevel2` — read-only CSI hierarchy (seeded, never alter)
- `Project` → `Assembly` → `LineItem` — core estimating hierarchy
- `Assembly` also holds `AssemblyComposition` rows (FK → `LibraryItem`) when built via the Assembly Builder
- `LibraryItem` — global reusable item definitions, independent of any project
- `Assembly.is_template = True` marks assemblies as global templates (no separate template table)

**Schema migrations:** Always extend `run_migrations()` in `app.py` using `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Never drop/recreate tables. Never run `db.create_all()` on existing tables.

## Critical Patterns

**`/project/<id>/summary` must return JSON** — `project.html` fetches it on load for the live totals bar. Do not change its response type.

**CSI dropdowns:** Level 1 rendered by Jinja; Level 2 populated by JS filtering a JSON blob embedded in the page. No API round-trip needed.

**JSON data embedding in templates:**
```html
<script id="my-data" type="application/json">{{ data | tojson | safe }}</script>
```
Parsed in JS with `JSON.parse(document.getElementById('my-data').textContent)`. Use this pattern — it's XSS-safe.

**Cascade delete:** Handled in Python (delete children before parent). No `ON DELETE CASCADE` in the DB.

**Template pre-load:** `assembly_builder.html` accepts `?from_template=<id>`. When no template, pass `json.dumps(None)` from the route → JS reads `null` → skips pre-fill.

## UI Rules

Dark theme — no exceptions:
- Page bg: `#1a1a2e` | Card bg: `#16213e` | Panel/input: `#0f3460` | Accent: `#e94560`
- Danger buttons: `#3a0a12` bg, `#e94560` text/border; hover → full red bg
- CSS classes: `.btn`, `.btn-secondary`, `.btn-danger`, `.btn-sm`
- `CSI_COLORS` dict is defined at module level in `app.py` **and** duplicated in `estimate.html` JS — keep both in sync when editing.

## Design Philosophy (from NORTHSTAR.md)

**Core test for every feature:** *Could a rigid (Excel-minded) estimator use this comfortably? Could a flexible (AI-native) estimator use this expressively?* If either answer is "no," reconsider.

- AI (`/agent/suggest` → Ollama llama3.2) is always opt-in, never required
- Traditional line-by-line entry is a supported first-class workflow — never remove it
- Offline-first: data never leaves the machine

## Known Gaps

- No edit UI for Project fields after creation
- No delete buttons in `estimate.html` (use project detail page)
- `equipment_hours` always equals `labor_hours` (hardcoded assumption)
- No authentication
