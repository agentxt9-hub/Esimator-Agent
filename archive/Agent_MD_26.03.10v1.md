# Session Handoff — Construction Estimating Tool
**Date:** 2026-03-10 | **Session:** 7 (v1)

---

## What Was Accomplished This Session

### 1. UX Polish — Estimate Delete Buttons
- Added ✕ delete buttons to every line item row in `estimate.html`
- Event delegation on tbody → confirm → POST `/lineitem/<id>/delete` → remove row + `updateTotals()`
- Print CSS hides the delete column (`@media print`)

### 2. Edit Project UI
- Added `POST /project/<id>/update` route to `app.py`
- Added "Edit Project" button + modal to `project.html` with 4 fields: name, project number, location, description
- Modal pre-fills from embedded JSON; saves via fetch, reloads on success

### 3. Major Redesign — Global Properties System
- **New DB models:** `GlobalProperty` (category: trade/project_type/market_sector) and `CompanyProfile`
- **New `/settings` page:** Company profile form (name, address, city, state, zip, phone, email, logo upload) + editable lists for Trades, Project Types, Market Sectors. Each list has inline "Add New" + delete.
- **Seeded defaults:** Trades (Concrete, Drywall, Steel, Framing, Masonry, Electrical, Plumbing, Mechanical), Project Types (Ground Up, Interior Fit-Out, Renovation), Market Sectors (Retail, Multi-Family, Mixed-Use, Single Family, Higher-Ed)
- Settings nav button added to `index.html`

### 4. Project Fields — Location Split + Classification
- `Project` model: added `city`, `state`, `zip_code`, `project_type_id`, `market_sector_id`
- `new_project.html`: replaced single `location` field with City / State / Zip (3 fields) + Project Type dropdown + Market Sector dropdown
- Both dropdowns include "➕ Add New…" inline flow that POSTs to `/settings/property/new` and auto-selects the result
- Edit Project modal updated with same split fields + dropdowns
- Legacy `location` column kept in DB (not dropped) for backward compat

### 5. Line Item Cost Logic Overhaul
- New `calculate_item_costs()` helper in `app.py`
- **Equipment items:** `equipment_cost = qty × equipment_cost_per_unit`, no labor
- **Labor & Materials + Prod Base ON:** `labor_hours = qty / production_rate`, `labor_cost = labor_hours × labor_cost_per_hour`
- **Labor & Materials + Prod Base OFF:** `labor_cost = qty × labor_cost_per_unit`, no labor hours
- Client-side `recalcItem()` in `estimate.html` mirrors this exactly
- New columns on `line_items`: `item_type`, `prod_base`, `labor_cost_per_unit`, `equipment_cost_per_unit`
- New columns on `library_items`: same four columns
- `assembly_id` on `line_items` made **NULLABLE** — line items can now exist without an assembly

### 6. Estimate.html — Full Redesign of Add Line Item
- **Quick Assembly button removed** entirely
- New **2-step modal:**
  - Step 1: Search library by description or CSI code (real-time filter). "➕ Create New Library Item" option at bottom.
  - Step 2: Item form — item type toggle (Labor & Materials / Equipment), prod base checkbox (conditional fields), trade dropdown from GlobalProps (with "Add New…"), CSI Division + CSI Section dropdowns
- **Library item selection pre-fills** all Step 2 fields including CSI
- Submits to `POST /project/<id>/lineitem/new` as JSON, returns full item dict, client pushes to `items[]` and calls `render()` — no page reload
- **Trade inline editing** upgraded: `startEdit()` renders a `<select>` for trade field, populated from GlobalProps, with "Add New…" option
- **Direct Items grouping:** `assembly_id === null` items show under "Direct Items" group in Assembly view

### 7. Library.html — New Fields
- Item type toggle (Labor & Materials / Equipment) in add/edit form
- Prod Base checkbox with conditional fields (shows prod rate + labor $/hr when ON; labor $/unit when OFF)
- Table updated with Type column (L&M / Equipment badge)
- Edit modal pre-fills all new fields

### 8. Assembly Builder Cleanup
- "Add Custom Line Item" button replaced with "➕ Create New Library Item" mini-modal
- Mini-modal POSTs to `/library/item/new`, then immediately calls `addFromLibrary()` to add to composition

### 9. CSI on Direct Line Items (end-of-session addition)
- `LineItem` model: added `csi_level_1_id` + `csi_level_2_id` FK columns
- `run_migrations()` adds these columns on startup
- `item_dict()` now reads CSI from the item itself when `assembly_id` is null
- `new_direct_line_item` and `update_line_item` accept and save CSI IDs
- Step 2 modal in estimate.html has CSI Division + Section dropdowns, pre-filled from library selection
- **Confirmed working by user**

---

## Current State of Codebase

### What Is Working (user-confirmed)
- All 21+ routes returning clean responses
- Delete buttons in estimate rows ✅
- Edit Project modal ✅
- Settings page — Trades, Project Types, Market Sectors ✅
- New project with city/state/zip + type/sector ✅
- Add Line Item 2-step modal with library search ✅
- CSI classification on direct line items ✅
- Library CRUD with new item_type + prod_base fields ✅

### Known Gaps / Not Yet Tested
- Assembly Builder "Create New Library Item" mini-modal → `addFromLibrary()` flow needs live test
- Company logo upload (`/settings/company/update` with file) — untested
- `/uploads/logo/<filename>` serve route — untested
- Edit Project modal CSI dropdowns for legacy projects with empty city/state/zip (display only, not a bug)
- `equipment_hours` field still exists on LineItem but always set to 0 (deprecated, harmless)

---

## Exact Next Steps

### Immediate — Bug Fixes & Polish
1. **Test Assembly Builder mini-modal** — open builder, click "Create New Library Item", fill form, confirm item appears in composition. Fix `addFromLibrary()` call if it doesn't.
2. **Test logo upload** — go to `/settings`, upload an image, confirm it saves and displays on page reload.
3. **Verify prod_base calculations live** — add a line item with prod_base ON, confirm labor hours appear in estimate. Add one with prod_base OFF, confirm labor cost = qty × labor_cost_per_unit.

### Backlog (prioritized order from user)
| Priority | Item |
|----------|------|
| High | **Bid Proposal output** — client-facing PDF cover page + cost summary (uses CompanyProfile logo/address) |
| High | **Project duplication** — clone entire project (assemblies + line items) as a starting point |
| Medium | **Assembly template tagging** — group templates by work type / trade |
| Medium | **Production rate standards lookup library** — reference table for prod rates by task |
| Medium | **Multi-project comparison** — side-by-side bid alternates view |
| Low | **Bulk AI review** — queue all line items for AI review at once |
| Low | **AI narrative summary paragraph** for proposals |

### Next Session Should Start With
```
Read CLAUDE.md (or Agent_MD_26.03.10v1.md) and confirm app starts cleanly with python app.py.
Then run the Assembly Builder mini-modal test and logo upload test before starting new features.
```

---

## Important Decisions & Context

- **Why CSI lives on LineItem, not just Assembly:** Direct line items (assembly_id = null) need their own CSI so they appear correctly in CSI report view and are searchable by division.
- **Why assembly_id is nullable:** User confirmed assemblies are grouping shortcuts — the estimate can be built with standalone line items only. "Direct Items" is the group label for null-assembly items.
- **Why location column was kept:** Backward compat for existing projects. New city/state/zip fields are additive. Do NOT drop location column.
- **Why Quick Assembly was removed:** User explicitly requested it. All assembly creation now goes through Assembly Builder.
- **Library-first Add Line Item:** Every line item should trace back to a library entry for consistency. "Create New" in the modal creates the library item first, then pulls it into the estimate — enforces the library as the catalog of record.
- **GlobalProperty "Add New…" pattern:** Appears in every dropdown (trade, project type, market sector). POSTs to `/settings/property/new` inline without leaving the page. Keeps the global list updated without requiring a separate settings visit.

---

## Key File Locations
```
C:\Users\Tknig\Dropbox\Estimator Agent\
├── app.py                          ← ~1200+ lines; all routes + models
├── NORTHSTAR.md                    ← Philosophy reference — read before any major decision
└── Templates\
    ├── index.html                  ← Dashboard + Settings nav
    ├── new_project.html            ← City/State/Zip + Type/Sector dropdowns
    ├── project.html                ← Edit modal; NO Quick Assembly
    ├── settings.html               ← Company profile + GlobalProperty lists
    ├── estimate.html               ← 2-step Add Line Item; CSI on direct items
    ├── library.html                ← Full CRUD + item_type + prod_base
    ├── assembly_builder.html       ← "Create New Library Item" mini-modal
    ├── summary.html
    ├── csi_report.html
    └── templates.html
```

## DB Connection
`postgresql://postgres:Builder@localhost:5432/estimator_db`

## Run Command
`python app.py` — migrations run automatically on startup via `run_migrations()`
