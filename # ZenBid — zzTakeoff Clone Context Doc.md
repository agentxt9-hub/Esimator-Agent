# ZenBid — zzTakeoff Clone Context Document

> Comprehensive UI/UX specification, data models, interaction patterns, and architecture reference derived from hands-on review of zzTakeoff (www.zztakeoff.com). This document is intended to serve as a blueprint for building the ZenBid construction takeoff application.

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [Technology Stack (zzTakeoff Reference)](#2-technology-stack)
3. [Application Architecture & Navigation](#3-application-architecture--navigation)
4. [Layout System — Three-Panel Design](#4-layout-system--three-panel-design)
5. [Left Sidebar — Pages & Bookmarks](#5-left-sidebar--pages--bookmarks)
6. [Center Panel — Plan Viewer (PDF Canvas)](#6-center-panel--plan-viewer)
7. [Top Toolbar — Drawing & Measurement Tools](#7-top-toolbar--drawing--measurement-tools)
8. [Right Sidebar — Takeoffs, Templates, Lists](#8-right-sidebar--takeoffs-templates-lists)
9. [Takeoff Data Model](#9-takeoff-data-model)
10. [Properties Dialogs — Full Field Specifications](#10-properties-dialogs)
11. [On-Plan Data Table (Floating Summary)](#11-on-plan-data-table)
12. [Status Bar](#12-status-bar)
13. [Reports View](#13-reports-view)
14. [Scale System](#14-scale-system)
15. [Project & File Structure](#15-project--file-structure)
16. [Contextual Toolbar Behavior](#16-contextual-toolbar-behavior)
17. [Annotation Tools](#17-annotation-tools)
18. [Templates & Lists Systems](#18-templates--lists-systems)
19. [Keyboard Shortcuts / Hotkeys](#19-keyboard-shortcuts--hotkeys)
20. [Observed Takeoff Examples (Drywall Project)](#20-observed-takeoff-examples)
21. [Key Differences Between Pages](#21-key-differences-between-pages)
22. [Feature Priority Matrix for ZenBid MVP](#22-feature-priority-matrix)

---

## 1. Application Overview

zzTakeoff is a web-based construction takeoff and estimating tool that allows contractors, estimators, and project managers to:

- Upload architectural/engineering PDF plan sets
- Scale drawings to real-world dimensions
- Measure linear distances, areas, counts, and segments directly on plans
- Organize takeoffs by type with color-coded overlays
- Attach material/labor items and assembly notes to each takeoff
- Generate reports grouped by various criteria
- Use templates and product lists for standardized takeoff workflows

The application operates as a single-page application (SPA) with real-time updates.

---

## 2. Technology Stack

**zzTakeoff observed stack (for reference only — ZenBid will use its own):**

- **Framework:** Meteor.js (full-stack JavaScript)
- **Frontend:** Vue.js components
- **PDF Rendering:** Custom canvas-based PDF viewer with overlay system
- **Data Grid:** AG Grid (for Reports view)
- **Real-time:** Meteor's DDP (Distributed Data Protocol) for live updates
- **Deployment:** Web-hosted SPA

---

## 3. Application Architecture & Navigation

### Top-Level Navigation Tabs

Located in the top navigation bar, these are the primary sections:

| Tab | Purpose |
|-----|---------|
| **Plans** | Upload, manage, and view PDF plan pages |
| **Takeoff** | Primary workspace — plan viewer + measurement tools + takeoff panel |
| **Reports** | AG Grid-based data tables with grouping/filtering of all takeoff data |
| **Community** | Documentation, help articles, shared resources |

### Global Header Elements

- **Company name** (top-left): e.g., "Life Science Health"
- **Project selector**: Dropdown to switch between projects
- **Search** (magnifying glass icon, top-right)
- **Share** button
- **View mode** selector: "Default" dropdown
- **User avatar / account menu** (far top-right)

---

## 4. Layout System — Three-Panel Design

The Takeoff view uses a responsive three-panel layout:

```
+------------------+--------------------------------+------------------+
|   LEFT SIDEBAR   |        CENTER PANEL            |  RIGHT SIDEBAR   |
|   (~240px)       |     (flexible, fills space)     |   (~280px)       |
|                  |                                  |                  |
|  Pages           |  PDF Plan Viewer Canvas          |  Takeoffs        |
|  Bookmarks       |  with Takeoff Overlays           |  Templates       |
|                  |                                  |  Lists           |
+------------------+--------------------------------+------------------+
|                        STATUS BAR                                     |
+-----------------------------------------------------------------------+
```

- Left and right sidebars are collapsible (arrow toggles visible)
- Center panel handles zoom, pan, and all drawing interactions
- Status bar spans full width at bottom

---

## 5. Left Sidebar — Pages & Bookmarks

### Pages Panel

- **Search box** at top for filtering pages
- **Tree list** of all drawing sheets in the project, organized by drawing number
- Each entry shows: `[Drawing Number] - [Sheet Name]`
- Active page is highlighted (bold, colored background)
- **"+" icon** next to expandable page groups (e.g., A1.0 > A1.1)
- Pages with sub-pages have expand/collapse chevrons

**Observed page hierarchy from the drywall project:**

```
A0.0 - Cover Sheet
A0.1 - Site Plan
LS1.0 - Life Safety Plan
D1.0 - Demolition Floor Plan
D1.1 - Demolition Ceiling Plan
A1.0 - Floor Plan          ← Page 1 reviewed
  A1.1 - Reflected Ceiling Plan  ← Page 2 reviewed
A2.0 - Finish Plan
A3.0 - Enlarged Plan & Interior Elevations
A3.1 - Wall Types and Details
A3.2 - Door & Material Schedules
A3.3 - Restroom Enlarged Plans and Elevations
A4.0 - Accessible Guidelines
A5.0 - Specifications
A5.1 - Specifications
A5.2 - Specifications
M1.0 - Mechanical Legends, Schedules, & De...
MD1.0 - Mechanical Demolition Plan
M2.0 - Mechanical Plan
M3.0 - Mechanical Specifications
P1.0 - Plumbing Schedules, Details, & Isometr...
P2.0 - Plumbing Plan
P2.1 - Gas Piping Plan
P3.0 - Plumbing Specifications
E1.0 - Electrical Legends, Schedules & Details
```

### Bookmarks Panel

- Located below Pages
- Has its own **Search box**
- **Action icons** (4 small icons): Add, Refresh, Expand All, More Options
- Shows "No Bookmarks" when empty
- Purpose: User-created bookmarks for quick navigation to specific plan locations

---

## 6. Center Panel — Plan Viewer

### Core Features

- **PDF rendering** on an HTML5 Canvas
- **Pan & zoom** (mouse wheel for zoom, click-drag for pan)
- **Takeoff overlays** rendered on top of the PDF as semi-transparent colored shapes
- **Selection handles** appear when a takeoff item is clicked (blue squares at vertices/control points)
- **Drawing number badge** in bottom-right corner of the plan (e.g., "A1.1")

### Overlay Rendering

Takeoff overlays are drawn with:
- **Fill color** matching the takeoff item's assigned color
- **Opacity** controlled per-item (slider in properties)
- **Stroke/outline** matching the color for linear items
- **Width rendering** for "Linear with Width" items (the line has visual width on the plan)
- **Selection state**: When selected, vertices show blue square handles; the item border becomes more prominent

### Zoom Controls

- **"+" and "-" buttons** in bottom-right corner
- **Zoom to Fit** button in toolbar
- **Mouse wheel zoom** (standard behavior)
- Current zoom percentage shown in status bar (e.g., "24%")

---

## 7. Top Toolbar — Drawing & Measurement Tools

The toolbar runs horizontally across the top, below the navigation tabs. It contains two states:

### Default State (no item selected)

| Icon | Tool | Description |
|------|------|-------------|
| 🖨️ | **Print** | Print/export current view (has dropdown arrow) |
| 🔍 | **Zoom to Fit** | Fits entire plan in viewport |
| 📏 | **Scale** | Set/change the scale for the current page (has dropdown) |
| 📐 | **Dimension** | Measure a distance without creating a takeoff |
| ⬜ | **Area** | Draw area (polygon) takeoff |
| 📏 | **Linear** | Draw linear (line) takeoff |
| 🔗 | **Segment** | Draw segmented line takeoff |
| 🔢 | **Count** | Place count markers |
| ☁️ | **Cloud** | Draw revision cloud markup |
| 🖍️ | **Highlighter** | Freehand highlight tool |
| 📝 | **Note** | Place text note on plan |
| ➡️ | **Arrow** | Draw arrow annotation |
| 💬 | **Callout** | Place callout with text |
| 🔲 | **Overlay** | Add image/shape overlay |
| 🔗 | **Hyperlink** | Add hyperlink to plan |

### Contextual State (takeoff item selected)

When a takeoff item is selected on the plan, the toolbar changes to show these **additional** buttons appended after Hyperlink:

| Button | Action |
|--------|--------|
| **Properties** | Opens the Properties dialog for the selected item |
| **Start** | Begins drawing/extending the selected takeoff |
| **Merge Ar...** | Merge Area (for area-type takeoffs — merges overlapping areas) |
| **Delete** | Deletes the selected takeoff from the plan |

---

## 8. Right Sidebar — Takeoffs, Templates, Lists

### Tab Navigation

Three tabs at the top of the right sidebar:

| Tab | Content |
|-----|---------|
| **Takeoffs** | List of all takeoff items for the current page |
| **Templates** | Company-saved takeoff templates |
| **Lists** | Company product/material lists |

### Takeoffs Tab

- **Search box** at top
- **Action icons** (top-right): Create new, Sort, Filter, Settings, Expand/Collapse
- **Takeoff item rows**, each showing:
  - **Icon** indicating type (linear icon for linear, area icon for area)
  - **Name** (e.g., "WT-B", "CT-ACT-1")
  - **Measurement value** (right-aligned, colored in blue/green)
  - **Unit** abbreviation (FT, SF)
  - **Color swatch** (small square showing the assigned overlay color)

**Example takeoff list from the drywall project (Page 2 - Ceiling Plan):**

| Icon | Name | Value | Unit | Color |
|------|------|-------|------|-------|
| Linear | WT-B | 456.10 | FT | Blue |
| Linear | WT-B2 | 254.29 | FT | Magenta |
| Linear | WT-B3 | 26.88 | FT | Orange |
| Linear | WT-D3 | 86.82 | FT | Green |
| Area | CT-ACT-1 | 4,525.60 | SF | Red |
| Area | CT-GYP-1 | 114.25 | SF | Cyan |
| Linear | CT-Bulk Head-1 | 41.41 | FT | Blue |
| Linear | CT-Bulk Head-2 | 193.31 | FT | Purple |

### Templates Tab

- Shows "Company Templates" header
- "No Templates" when empty
- Purpose: Pre-configured takeoff item templates (name, color, type, notes) that can be applied to new projects

### Lists Tab

- Shows "Company Products" header
- "No Products" when empty
- Purpose: Product/material catalog that can be linked to takeoff items via Materials & Labor

---

## 9. Takeoff Data Model

### Takeoff Item Entity

Each takeoff item has the following data structure:

```
TakeoffItem {
  id: String (unique identifier)
  name: String (user-defined, e.g., "WT-B", "CT-ACT-1")
  projectId: String (parent project)
  pageId: String (which drawing page this takeoff belongs to)

  // Type & Appearance
  measurementType: Enum [
    "Linear with Width",
    "Flat Area",
    "Segment",
    "Count",
    "Cloud"
  ]
  color: Color (hex/RGB)
  opacity: Float (0.0 - 1.0, controlled by slider)

  // Linear-specific fields
  width: {
    feet: Number,
    inches: Number,
    numerator: Number,
    denominator: Number
  }
  scaled: Boolean (whether width scales with zoom)
  sideOfLine: Enum ["Center", "Left", "Right"]

  // Geometry (stored as coordinate arrays)
  points: Array<{x: Number, y: Number}> // vertices in plan coordinates

  // Measurements (auto-calculated from geometry + scale)
  measurements: Array<{
    index: Number (1, 2, 3...)
    type: Enum ["Linear", "Area", "Linear / Perimeter", "Count"]
    value: Number
    unit: Enum ["FT", "SF", "EA", "LF", "SY", "IN"]
  }>

  // Materials & Labor
  materials: Array<{
    productId: String,
    name: String,
    quantity: Number,
    unit: String,
    costPer: Number
  }>

  // Organization
  workBreakdownStructure: {
    division: String (e.g., CSI MasterFormat division)
  }

  // Custom Properties
  customProperties: {
    assemblyNotes: String (free text, e.g., construction spec)
    // extensible — more custom fields possible
  }
}
```

### Measurement Types — Detailed Behavior

| Type | Icon | Primary Measurement | Secondary Measurement | Drawing Method |
|------|------|--------------------|-----------------------|----------------|
| **Linear with Width** | Line icon | Linear FT | — | Click-to-click polyline, renders with visible width |
| **Flat Area** | Polygon icon | Area SF | Linear/Perimeter FT | Click-to-click polygon, closed shape |
| **Segment** | Segmented line icon | Linear FT | — | Similar to linear but for non-continuous segments |
| **Count** | Count icon | Count EA | — | Click to place individual markers |
| **Cloud** | Cloud icon | — | — | Freeform cloud shape (markup, not measurement) |

### Multi-Measurement Support

Area-type takeoffs automatically provide two measurements:
- **Measurement 1**: Area (SF) — the enclosed area
- **Measurement 2**: Linear / Perimeter (FT) — the perimeter length

Linear-type takeoffs provide one measurement:
- **Measurement 1**: Linear (FT) — total line length

A "More" dropdown and "+" button exist in the Measurements section, suggesting users can add additional derived measurements.

---

## 10. Properties Dialogs

### Linear Properties Dialog

**Header:** "Linear Properties" with icon, settings gear, and close (X) button

**Fields (in order):**

1. **Name** — Text input (e.g., "WT-B", "CT-Bulk Head-2")
2. **Measurement Type** — Dropdown: "Linear with Width"
3. **Color** — Color picker swatch
4. **Width** — Compound input:
   - Feet field (number)
   - Inches field (number, e.g., "4")
   - Fraction: Numerator / Denominator fields
   - Format: `[Feet]' [Inches]" [Num]/[Den]"`
5. **Scaled** — Checkbox (checked = width scales proportionally on screen)
   - Has info tooltip icon (?)
6. **Side of Line** — Dropdown: Center | Left | Right
   - Has info tooltip icon (?)
7. **Opacity** — Horizontal slider (continuous range)

**Collapsible Sections:**

8. **Measurements** (expandable with chevron)
   - Measurement 1: [value in green/blue] | Type dropdown (Linear) | Units dropdown (FT)
   - "+ More" button to add additional measurements

9. **Materials & Labor** (expandable)
   - Shows "No Items." when empty
   - "+" button to add items

10. **Work Breakdown Structure** (expandable)
    - Division: Dropdown "Choose Division..." (CSI MasterFormat divisions)

11. **Custom Properties** (expandable)
    - Assembly Notes: Multi-line textarea

**Footer:**
- Two small icons (bottom-left): Share/Copy icon, Bookmark icon
- **Save** button (blue, primary)
- **Cancel** button (secondary)

### Area Properties Dialog

**Header:** "Area Properties" with polygon icon

**Fields (same structure as Linear, minus linear-specific fields):**

1. **Name** — Text input (e.g., "CT-ACT-1", "CT-GYP-1")
2. **Measurement Type** — Dropdown: "Flat Area"
3. **Color** — Color picker swatch
4. **Opacity** — Horizontal slider
5. *(No Width, Scaled, or Side of Line fields)*

**Measurements Section:**
- **Measurement 1**: Area | [value] | SF
- **Measurement 2**: Linear / Perimeter | [value] | FT
- "+ More" button

**Remaining sections identical to Linear Properties:**
- Materials & Labor
- Work Breakdown Structure (Division)
- Custom Properties (Assembly Notes)
- Save / Cancel footer

---

## 11. On-Plan Data Table (Floating Summary)

A floating table appears on the plan canvas showing a summary of page-specific takeoff items. This table is rendered as an overlay on the drawing.

**Structure:**

| Column | Description |
|--------|-------------|
| Color icon | Small swatch matching takeoff color |
| Takeoff Name | Name of the takeoff item |
| Measurement 1 | Primary measurement with units |

**Example from Page 2 (Ceiling Plan):**

| | Takeoff Name | Measurement 1 |
|-|-------------|---------------|
| 🟥 | CT-ACT-1 | 4,525.60 SF |
| 🟦 | CT-GYP-1 | 114.25 SF |
| 🔵 | CT-Bulk Head-1 | 41.41 FT |
| 🟣 | CT-Bulk Head-2 | 193.31 FT |

**Behavior:**
- Shows only ceiling/area takeoff items relevant to the current page view
- Wall types (WT-*) from Page 1 appeared in a similar table with their measurements
- Table is draggable/repositionable on the canvas
- Appears to filter based on what's visible in the current viewport or by takeoff category

---

## 12. Status Bar

The status bar spans the full width at the bottom of the application.

**Left side:**
```
X: 0.0, Y: 0.0
```
Real-time cursor coordinates in plan space.

**Center-left:**
```
24%
```
Current zoom percentage.

**Center:**
```
A1.1 - Reflected Ceiling Plan
```
Current page name / drawing title.

**Center-right:**
```
Scale: 1/4"=1'
```
Current scale setting for the active page.

**Right side (tool status indicators):**
```
PDF Snap: Off | Snap: Off | Ortho: On | Auto Scroll: On
```
Toggle states for precision drawing aids:
- **PDF Snap**: Snaps to PDF geometry (lines, intersections)
- **Snap**: Grid/point snapping
- **Ortho**: Constrains drawing to orthogonal (90-degree) angles
- **Auto Scroll**: Auto-scrolls the viewport when drawing near edges

---

## 13. Reports View

### Layout

The Reports view replaces the Center Panel with an AG Grid data table. The right sidebar changes to show report navigation categories.

### Data Grid

- **AG Grid** implementation with full-featured data table
- Column headers with sort indicators
- Row grouping with expand/collapse
- Cell-level data including takeoff names, measurements, materials, etc.
- Supports filtering, sorting, grouping by multiple fields

### Reports Sidebar Categories

```
Team Reports
  (expandable)

My Reports
  (expandable)

Default Reports
  ├── Takeoff Tree Reports
  │   ├── Measurements Grouped by Takeoff
  │   ├── Measurements Grouped by Page
  │   ├── Measurements Grouped by Division & Page
  │   └── Measurements Grouped by Division & Takeoff
  │
  └── Advanced Takeoff / Item Reports
      ├── Item Costs by Page
      ├── Item Costs Grouped by Division
      ├── Item Costs Grouped by Division & Page
      └── (potentially more...)
```

### Report URL Structure
```
/app/reports?projectId={id}&reportViewId={viewId}&pageId={pageId}
```

The `reportViewId` parameter controls which report grouping is active (e.g., `defaultMeasurementsGroupedByTakeoff`).

---

## 14. Scale System

### Scale Format
```
[numerator]"=[denominator]'
```
Example: `1/4"=1'` means 1/4 inch on the drawing equals 1 foot in real life.

### Scale Methods

1. **AI-Powered Automatic Scaling**
   - Draw a selection window around a scale indicator on the drawing
   - Right-click context menu > "Scale"
   - AI detects standard architectural/engineering scales
   - Sets scale automatically

2. **Manual Scaling**
   - Click Scale tool in toolbar
   - Enter known real-world dimension
   - Click two points on the drawing that correspond to that dimension
   - Scale is calculated from the pixel distance vs. entered value

### Scale Verification
- Scale indicator appears in the status bar
- Cross-hair indicator appears on the left side when scale is set
- Recommended to verify both horizontal and vertical dimensions

### Scale Per Page
Each page in the project can have its own independent scale setting.

---

## 15. Project & File Structure

### URL Structure
```
Base: https://www.zztakeoff.com/app/

Takeoff View:
/takeoff?projectId={projectId}&reportViewId={reportViewId}&pageId={pageId}

Reports View:
/reports?projectId={projectId}&reportViewId={reportViewId}&pageId={pageId}

Plans View:
/plans?projectId={projectId}

Community:
/community/documentation
```

### Project Entity
```
Project {
  id: String
  name: String (e.g., "Life Science Health")
  company: String
  measurementSystem: Enum ["Imperial", "Metric"]
  pages: Array<Page>
  createdAt: DateTime
  updatedAt: DateTime
}
```

### Page Entity
```
Page {
  id: String
  projectId: String
  drawingNumber: String (e.g., "A1.1")
  name: String (e.g., "Reflected Ceiling Plan")
  pdfFile: Binary/URL
  scale: String (e.g., "1/4\"=1'")
  sortOrder: Number
  parentPageId: String? (for hierarchical grouping)
  takeoffs: Array<TakeoffItem>
}
```

### Supported File Formats
- PDF (primary)
- PNG
- JPG
- TIFF

---

## 16. Contextual Toolbar Behavior

The toolbar dynamically changes based on application state:

### State 1: No Selection (Default)
Full drawing tool palette is shown: Print, Zoom to Fit, Scale, Dimension, Area, Linear, Segment, Count, Cloud, Highlighter, Note, Arrow, Callout, Overlay, Hyperlink

### State 2: Takeoff Item Selected
All default tools remain, plus these are **appended**:
- **Properties** — Opens the selected item's property editor
- **Start** — Begins/resumes drawing on the selected takeoff
- **Merge Ar...** (Merge Area) — For area types, merges adjacent/overlapping regions
- **Delete** — Removes the selected takeoff item

### State 3: Active Drawing
When actively drawing (placing points for a new takeoff), the cursor changes and click behavior is overridden to add vertices. Press Escape or double-click to finish.

---

## 17. Annotation Tools

In addition to measurement takeoffs, the toolbar provides non-measurement annotation tools:

| Tool | Type | Purpose |
|------|------|---------|
| **Highlighter** | Freehand | Mark up areas with transparent color |
| **Note** | Text | Place text notes directly on the plan |
| **Arrow** | Line | Draw directional arrows for callouts |
| **Callout** | Text + Shape | Place framed text callouts with leader lines |
| **Cloud** | Shape | Draw revision clouds around areas of interest |
| **Overlay** | Image/Shape | Add overlay images or shapes |
| **Hyperlink** | Link | Attach clickable hyperlinks to plan locations |
| **Dimension** | Measurement | Quick-measure a distance without creating a permanent takeoff |

---

## 18. Templates & Lists Systems

### Company Templates

- Stored at the company/workspace level (shared across projects)
- Pre-configured takeoff items with:
  - Name pattern
  - Measurement Type
  - Color
  - Default width (for linear)
  - Assembly Notes
  - Materials & Labor associations
- Users can apply templates to quickly create standardized takeoff items

### Company Products (Lists)

- Product/material catalog at the company level
- Each product has: name, unit, cost information
- Products are linked to takeoff items via the "Materials & Labor" section
- Enables cost estimation when products are assigned to takeoffs

### Integration Flow
```
Template → Create Takeoff Item → Link Products (Materials & Labor) → Report with Costs
```

---

## 19. Keyboard Shortcuts / Hotkeys

From zzTakeoff documentation:

| Shortcut | Action |
|----------|--------|
| Escape | Cancel current operation / deselect |
| Delete | Delete selected item |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+C | Copy |
| Ctrl+V | Paste |
| Space (hold) | Pan mode |
| Mouse Wheel | Zoom in/out |
| Double-click | Finish current drawing operation |
| F | Zoom to fit |

---

## 20. Observed Takeoff Examples (Drywall Project)

### Project: Life Science Health

This section documents the actual takeoff data observed during the UI review, providing real-world context for data types and naming conventions used in drywall estimating.

### Page 1: A1.0 — Floor Plan

**Takeoff items (8 total):**

| Name | Type | Measurement | Color | Assembly Notes |
|------|------|-------------|-------|----------------|
| WT-B | Linear w/ Width | 456.10 FT | Blue | 3-5/8" 20ga Framing at 16" OC, 12" Above Ceiling, Braced to Deck 48" OC, 5/8" Type X Drywall Each Side, 3" Mineral Wool Insulation |
| WT-B2 | Linear w/ Width | 254.29 FT | Magenta | (wall type variant) |
| WT-B3 | Linear w/ Width | 26.88 FT | Orange | (wall type variant) |
| WT-D3 | Linear w/ Width | 86.82 FT | Green | (wall type variant) |
| CT-ACT-1 | Flat Area | 4,525.60 SF + 1,745.20 FT perimeter | Red | 2x4 Armstrong Ultima Tegular Tile with 9/16" Suprafine Grid |
| CT-GYP-1 | Flat Area | 114.25 SF | Cyan | (gypsum ceiling type) |
| CT-Bulk Head-1 | Linear w/ Width | 41.41 FT | Blue | (bulkhead framing) |
| CT-Bulk Head-2 | Linear w/ Width | 193.31 FT | Purple | 6" 20ga "I" Style Fur Down, Assume 8' Framing with 2' Finished Drywall Face |

**Naming Convention:**
- `WT-` prefix = Wall Type
- `CT-` prefix = Ceiling Type
- Suffix letter/number = Variant identifier (B, B2, B3, D3, ACT-1, GYP-1)
- "Bulk Head" = Ceiling bulkhead/soffit

### Page 2: A1.1 — Reflected Ceiling Plan

**Same 8 takeoff items** visible (shared across pages within the same project scope). The ceiling plan shows:

- Large red-shaded areas = CT-ACT-1 (acoustic ceiling tile coverage, ~4,525 SF)
- Small cyan areas = CT-GYP-1 (gypsum board ceiling, ~114 SF, vestibule/small rooms)
- Purple linear lines around perimeter = CT-Bulk Head-2 (bulkhead soffits, ~193 FT)
- Blue linear lines at transitions = CT-Bulk Head-1 (shorter bulkheads, ~41 FT)
- Wall type lines (WT-B, WT-B2, etc.) also visible as they extend floor-to-ceiling

**Ceiling Plan-Specific Drawing Information:**
- Site Information table (heights: 13'-07" AFF varies for bottom of deck, 11'-07" AFF varies for bottom of structure)
- Lay-In Ceiling Type schedule (ACT-1: Ultima Tegular Ceiling Tile w/ 9/16" Suprafine White Grid 24"x48"; ACT-3: similar with 8"x48")
- Decorative Light Schedule
- Ceiling Plan Coded Notes (16 numbered notes describing ceiling conditions)
- Key Plan (small location reference)
- Section Detail references

### CT-GYP-1 Properties (Captured in Detail)

```
Name: CT-GYP-1
Measurement Type: Flat Area
Color: Cyan
Opacity: ~30%
Measurement 1: 114.25 SF (Area)
Measurement 2: 76.54 FT (Linear / Perimeter)
Materials & Labor: No Items
Division: (not set)
Assembly Notes: "Suspended Drywall Grid Framing System with 1 Layer of 5/8" Type X"
```

### CT-Bulk Head-2 Properties (Captured in Detail)

```
Name: CT-Bulk Head-2
Measurement Type: Linear with Width
Color: Purple
Width: 4"
Scaled: Yes
Side of Line: Center
Opacity: ~55%
Measurement 1: 193.31 FT (Linear)
Materials & Labor: No Items
Division: (not set)
Assembly Notes: "6" 20ga "I" Style Fur Down, Assume 8' Framing with 2' Finished Drywall Face"
```

---

## 21. Key Differences Between Pages

| Aspect | Page 1 (A1.0 Floor Plan) | Page 2 (A1.1 Reflected Ceiling Plan) |
|--------|--------------------------|--------------------------------------|
| Drawing content | Floor plan with room layouts, doors, walls | Reflected ceiling plan with ceiling grid, lights, soffits |
| Primary takeoffs | Wall types (WT-*) dominant | Ceiling types (CT-*) dominant |
| Area overlays | CT-ACT-1 visible but less prominent | CT-ACT-1 covers majority of the plan (large red fill) |
| Reference tables | Wall type schedule, door schedule | Ceiling coded notes (16 items), lay-in ceiling types, decorative light schedule |
| Takeoff list | Same 8 items in right sidebar | Same 8 items (takeoffs span across pages) |
| On-plan data table | Shows WT-B through WT-D3 measurements | Shows CT-ACT-1 through CT-Bulk Head-2 measurements |
| Scale | 1/4"=1' | 1/4"=1' (same) |

**Key insight:** Takeoff items exist at the project level and can span multiple pages. The same WT-B takeoff has measurements drawn on both the floor plan and ceiling plan. The on-plan data table filters to show relevant items for the current page context.

---

## 22. Feature Priority Matrix for ZenBid MVP

### P0 — Must Have (Core)

- [ ] PDF plan viewer with pan/zoom on HTML5 Canvas
- [ ] Page sidebar with sheet navigation
- [ ] Scale system (manual at minimum, AI stretch goal)
- [ ] Linear measurement tool (click-to-click polyline)
- [ ] Area measurement tool (click-to-click polygon)
- [ ] Count tool (click to place markers)
- [ ] Takeoff item management (create, name, color, delete)
- [ ] Properties dialog (name, type, color, measurements)
- [ ] Overlay rendering (colored fills/strokes on canvas)
- [ ] On-plan data table (floating measurement summary)
- [ ] Status bar (coordinates, zoom, page name, scale)
- [ ] Project creation with PDF upload
- [ ] Basic reports view (data table with takeoff measurements)

### P1 — Should Have (Full Product)

- [ ] Segment tool
- [ ] Width property for linear items (with visual rendering)
- [ ] Side of Line option (Center/Left/Right)
- [ ] Opacity control per takeoff
- [ ] Assembly Notes / Custom Properties
- [ ] Materials & Labor linking
- [ ] Work Breakdown Structure (CSI Division)
- [ ] Company Templates system
- [ ] Company Products/Lists system
- [ ] Report grouping (by takeoff, page, division, etc.)
- [ ] Bookmarks system
- [ ] Multi-measurement support per takeoff (area + perimeter)
- [ ] Contextual toolbar (changes when item selected)
- [ ] Ortho / Snap / PDF Snap precision aids

### P2 — Nice to Have (Polish)

- [ ] AI-powered auto-scaling
- [ ] Cloud / Highlighter / Note / Arrow / Callout annotations
- [ ] Overlay tool (image overlays)
- [ ] Hyperlink tool
- [ ] Print/Export functionality
- [ ] Real-time collaboration (multi-user)
- [ ] Dimension tool (quick measure)
- [ ] Team Reports / My Reports (saved report views)
- [ ] PlanSwift migration/import
- [ ] Formula system for computed measurements
- [ ] True/False conditional expressions for takeoff items

---

## Appendix: Screenshot Reference Index

The following screenshots were captured during the UI review and saved to disk. They provide visual reference for each component documented above.

| Screenshot ID | Description |
|---------------|-------------|
| ss_6556fdr4x | Page 1 (A1.0) full overview — all panels, overlays, toolbar |
| ss_4003e3zrc | WT-B Linear Properties dialog (full form) |
| ss_5248uazjd | CT-ACT-1 Area Properties dialog |
| ss_0320qr85o | Templates tab (Company Templates, empty state) |
| ss_249002y48 | Lists tab (Company Products, empty state) |
| ss_3122xggmn | Reports view — full AG Grid data table |
| ss_6604k7coo | Page 2 (A1.1) full overview — ceiling plan with overlays |
| ss_9193c8tes | Page 2 with CT-GYP-1 selected (contextual toolbar visible) |
| ss_9808tfse8 | CT-GYP-1 Area Properties dialog |
| ss_5566hseq6 | CT-Bulk Head-2 selected on ceiling plan |
| ss_6631dhs1h | CT-Bulk Head-2 Linear Properties dialog |

Additional zoomed captures document: toolbar details, takeoff list items, page tree, status bar indicators, on-plan data tables, ceiling plan coded notes, site information tables, and drawing detail views.

---

*Document compiled from hands-on review of zzTakeoff application, April 2026.*
*Intended as reference specification for ZenBid construction takeoff application.*