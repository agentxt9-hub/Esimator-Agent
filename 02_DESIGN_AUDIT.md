# 02_DESIGN_AUDIT.md — Agent Two: Design Lead Audit

**Date:** 2026-04-29  
**Scope:** Front-end implementation vs. documented design intent. No backend code read. Agent One's audit not read.  
**Files read:** `NORTHSTAR.md`, `TALLY_VISION.md`, `FEATURE_ROADMAP.md`, `CLAUDE.md` (design sections), `Agent_MD.md` (architecture sections), all templates, `takeoff.css`, `estimate_table.css`, `estimate_table.js` (partial), `agentx_panel.html`

---

## 1. Documented Intent

The following design commitments appear explicitly in strategic and operating documentation:

**Three-surface product flow:** Takeoff → Estimate → Proposal. Each surface has a distinct job and a distinct design mode.

**Tally AI identity:** The intelligence layer is called "Tally." It operates in three modes — Passive (column annotations on the TanStack grid), Reactive (inline suggestions on demand), Generative (scope gap fill with approve/reject). No legacy AI name appears in any strategic document.

**Two base templates, strict separation:** `base.html` for the marketing/public surfaces (light theme), `app_base.html` for the authenticated app (dark theme). CSS variables flow from these two files; nothing else should define color tokens.

**No external font imports:** NORTHSTAR specifies "System UI font stack only." No calls to Google Fonts or CDN-hosted typeface files.

**No hardcoded hex values:** Only CSS variables from the base templates. Documented explicitly in CLAUDE.md UI Rules and reiterated as a comment in `takeoff.css`.

**No emoji as UI primitives:** Not stated verbatim but implied by "professional tool" positioning throughout NORTHSTAR. The NORTHSTAR design rule list says nothing about emoji icons.

**AI interaction model:** Tally Passive operates in-grid (column badges, confidence scores, action flags). Tally Reactive and Generative are triggered interactions. The prior chat-panel model is not described anywhere in current strategy documents.

---

## 2. Implementation Inventory

### Marketing Surface (public, light theme)
| Template | Base | Notes |
|---|---|---|
| `base.html` | — | Base itself; CSS vars, sticky nav, hamburger, footer |
| `landing.html` | `base.html` | Hero, stats bar, testimonials, CTA sections |
| `pricing.html` | `base.html` | Three-tier pricing cards with "Join Waitlist" CTAs |
| `waitlist.html` | `base.html` | Clean card form, CSS vars throughout |
| `signup.html` | `base.html` | Auth card with social buttons |
| `login.html` | `base.html` | Auth card with social buttons |

### App Surface — New Design System (dark theme)
| Template | Base | Notes |
|---|---|---|
| `app_base.html` | — | Base itself; full CSS var system, 260px sidebar, top bar |
| `project.html` | `app_base.html` | Legacy estimate table still live inline |
| `estimate_table.html` | `app_base.html` | TanStack v8 + React; introduces --zb-* vars; IBM Plex Sans |
| `takeoff/viewer.html` | `app_base.html` | Three-panel Konva canvas; 7 disabled toolbar buttons |

### App Surface — Old Design System (deprecated)
| Template | Base | Notes |
|---|---|---|
| `index.html` | **none** | Dashboard; hardcoded deprecated colors; "Construction Estimator" |
| `nav.html` | **none** | Old nav partial; deprecated colors; "Construction Estimator" |

### AI Panel
| File | Status |
|---|---|
| `agentx_panel.html` | Live; 1,860 lines; "AgentX" brand throughout; loaded by `index.html` |

### Static Assets
| File | Notes |
|---|---|
| `takeoff.css` | Well-organized; uses CSS vars throughout; minor hardcoded greens for semantic states |
| `estimate_table.css` | Mixed: CSS vars claimed in comment, hardcoded hex values used in scrollbars, borders, and tooltips |
| `estimate_table.js` | React/Babel; duplicates design tokens in `ZB` object; `AI_STATUS` constants defined; Tally fields stub only |

---

## 3. Experience Walkthrough

### Path A: Visitor → Waitlist

**Landing:** Hero section (`landing.html`) contains a fabricated app mockup with hardcoded data ("Alex", "$2.4M", "47 AI Assists"). The stats bar cites "3x Faster," "100% CSI," "AI" — these are aspirational copy with no qualifier. Three testimonials have fabricated names and companies with no attribution marker.

**CTA mismatch — critical:** The CTA section body reads: *"Start your free trial today. No credit card required. Full access to all features for 14 days."* The button below this copy links to `/waitlist`. The product is in waitlist mode; the copy describes a launched SaaS with a trial. These are contradictory on the same screen.

**Waitlist form:** Clean. CSS variables used correctly. Post-submit micro-survey not walkable from the template alone but is non-blocking per implementation notes.

### Path B: New Account via Social Auth

**Login / Signup:** Both pages display Google and Microsoft social auth buttons with functional-looking SVG logos and direct `<a href>` links to `/auth/google` and `/auth/microsoft`. These routes are not listed in any documented route table. Clicking them produces a 404 or routing error. The social buttons are interactive false affordances on both the login and signup screens.

**Signup terms:** The signup form links to `/terms` and `/privacy` — both listed as CRITICAL gaps in CLAUDE.md (placeholder routes). A user cannot complete the consent flow without encountering broken or absent pages.

### Path C: Authenticated User → Dashboard

**Index.html — the session's most severe finding:** After login, users land on `index.html`. This template does not extend `app_base.html`. It defines its own inline styles using an entirely different design system:

```css
body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; }
.container { background: #16213e; }
h1 { color: #e94560; }
.btn { background: #e94560; }
.project-card { background: #0f3460; }
```

The colors `#1a1a2e`, `#16213e`, `#0f3460`, and `#e94560` are explicitly named "do not use" in CLAUDE.md. The product name on this page is "Construction Estimator." The AgentX panel tab (`🤖 AgentX`) is visible on the right edge. This is the first authenticated page a user sees. It is designed as if no rebrand or design system migration ever happened.

**Project page:** Navigating into a project (`project.html`) correctly extends `app_base.html` and uses CSS variables. The design system snaps back to the intended state. Users experience a visible discontinuity — old theme on the dashboard, new theme inside a project.

### Path D: Takeoff → Estimate (the product's core flow)

**Takeoff viewer:** Three-panel layout (sheets sidebar, Konva canvas, takeoffs sidebar) is well-executed. The toolbar contains 7 tool buttons marked `.disabled` via the `disabled` HTML attribute and `.opacity: 0.3` via CSS: Cloud, Highlight, Note, Arrow, Callout, Overlay, Link. These buttons are rendered at full visual size with icons and labels. Users can see them, hover over them (cursor changes to `not-allowed`), but cannot use them. There is no tooltip explaining when they will become available. They read as broken features, not planned features.

Scale badge and Snap/Ortho toggle are functional and well-styled. Empty state with 📐 emoji is present.

**Estimate table:** The TanStack table (`estimate_table.html`) imports IBM Plex Sans from `fonts.googleapis.com`. This is a documented prohibition. The `estimate_table.css` comment on line 1 says "All colors use Zenbid design tokens" but the file uses `#0F1419`, `#2A3040`, `#1A1F26`, and `#2D5BFF` as hardcoded hex values in scrollbar, border, and tooltip rules.

The TanStack grid defines `AI_STATUS` constants and a Tally footer banner stub but no live AI surface interaction is wired. The Tally column in the grid exists as a schema field, not an active UI element.

**Proposal:** Not directly read; not reachable from the estimate table in the current implementation.

---

## 4. Consistency Findings

### 4a. Two Parallel Design Systems

The application simultaneously runs two design systems:

| Attribute | New (intended) | Old (deprecated) |
|---|---|---|
| Base template | `app_base.html` | none / inline |
| Colors | CSS vars (`--app-bg`, `--accent-coral`, etc.) | `#1a1a2e`, `#e94560`, `#0f3460` |
| Font | System UI stack | `Arial, sans-serif` |
| Brand name | ZENBID / Zenbid | Construction Estimator |
| AI panel | Tally (documented) / AgentX (present) | AgentX |
| Navigation | app_base.html sidebar | nav.html partial |

Users experience the old system on `index.html` (the dashboard) and `nav.html`. They experience the new system on `project.html`, `estimate_table.html`, and `takeoff/viewer.html`. The seam is directly at login.

### 4b. Three Simultaneous Design Token Definitions

Design tokens are defined in three places with no single source of truth:

1. **CSS variables** in `app_base.html` — `--app-bg: #0F1419`, `--primary-brand: #2D5BFF`, etc. (canonical per documentation)
2. **JavaScript object** `ZB` in `estimate_table.js` — `bg: '#0F1419'`, `blue: '#2D5BFF'`, etc. (duplicate for React context)
3. **Hardcoded hex** in `estimate_table.css` — `#0F1419`, `#2D5BFF`, etc. (diverged; the comment claims they don't exist)

A change to a color token requires coordinated edits in three files. There is no mechanism to enforce consistency.

### 4c. Two AI Identities

Strategic documents use "Tally" exclusively. The implementation uses "AgentX" exclusively. The tab button reads `🤖 AgentX`. The welcome bubble reads `"Hi! I'm AgentX."` The mode buttons are labeled "Estimate / Research / Chat" — not the Tally Passive/Reactive/Generative model. The AI panel's CSS file (`agentx_panel.html`) uses `ax-` class prefixes throughout.

If the renaming to Tally is intended (it is, per every strategic document written since Pass 1), nothing in the front-end reflects it.

### 4d. Two Estimate Table Implementations

The legacy estimate table renders inline in `project.html` (the project detail page). The new TanStack table renders in `estimate_table.html` (a separate route). Both are accessible. The legacy table is listed in CLAUDE.md as "deprecated, retire in Pass 3" but is currently the table users see on the project page, since `project.html` does not link to `estimate_table.html`. The TanStack route exists in isolation; the normal project navigation does not surface it.

### 4e. Product Name Fragmentation

The product name appears in four forms across the templates:
- `ZENBID` — wordmark in logos (correct per CLAUDE.md)
- `Zenbid` — page titles, nav links, copy text (standard prose form)
- `ZenBid` — appears in CSS comment headers and some file references
- `Construction Estimator` — `index.html` h1, `nav.html` brand link, AgentX welcome bubble context

### 4f. Font Stack Violations

Three different font contexts exist:
1. System UI stack — declared in `app_base.html` and `base.html` body rules (intended)
2. IBM Plex Sans via Google Fonts CDN — imported in `estimate_table.html` head
3. `Arial, sans-serif` — used inline in `agentx_panel.html` for the chat textarea and builder textarea

---

## 5. AI Surface Assessment

### Current State

The only functional AI surface is `agentx_panel.html`: a right-edge slide-out panel with a coral tab trigger. It contains:
- Three modes: Estimate, Research, Chat (chat-centric model)
- Rate Lookup sub-panel (production rate database query)
- Assembly Auto-Builder sub-panel (describe work → generate assembly proposal)
- Scope Gap Detector (analyze estimate → gap report with fix-it button)
- Voice input (Web Speech API; hides button if API unavailable)
- Write permission checkbox (explicit opt-in before AI can mutate estimate)

This panel is technically functional and reasonably well-built. The CSS is 866 lines; the JavaScript is ~900 lines. It loads on `index.html` and legacy pages. On `project.html` it is included via `{% include 'agentx_panel.html' %}`. It does not appear on `estimate_table.html` or `takeoff/viewer.html`.

### Documented Target (Tally)

Per NORTHSTAR and TALLY_VISION, Tally should operate in three modes:
- **Passive:** AI annotations appear as columns in the TanStack grid (confidence, ai_status, ai_note). No panel, no interaction required.
- **Reactive:** User triggers a suggestion on a specific row or cell. Tally responds inline.
- **Generative:** Tally proposes scope additions; user approves or rejects in the grid.

The TanStack grid (`estimate_table.js`) defines the schema for Passive mode: `AI_STATUS` constants (`verified`, `suggestion`, `gap`, `live-price`) with color and icon configurations, and the `ai_status` / `ai_confidence` / `ai_note` / `estimator_action` fields exist in the LineItem model. The Tally footer banner is rendered as a static HTML stub in the grid.

**Gap:** Zero Tally interactions are wired. The `AI_STATUS` constants in `estimate_table.js` are display definitions only — no data flows into them from the backend. The Passive column badges never render with real data. The Tally footer banner is static HTML. Tally Reactive and Generative have no UI components at all.

### Assessment

The product has two AI personalities simultaneously: a functioning legacy one (AgentX, panel-based, chat-centric, works today) and a documented future one (Tally, grid-native, works nowhere). Users see AgentX. The documents describe Tally. The TanStack grid has scaffolding for Tally Passive but no live wiring. The flywheel (every accept/edit/reject captured as training data) cannot run until Tally Passive is wired, because the AgentX panel does not write to the `estimator_action` / `edit_delta` fields.

---

## 6. Accessibility and Foundations

### False Affordances

Three categories of visible-but-inert UI elements exist across the product:

1. **7 disabled tool buttons in Takeoff toolbar** — Cloud, Highlight, Note, Arrow, Callout, Overlay, Link. Full visual weight, no tooltip explaining absence. Read as broken.

2. **Non-functional search in app top bar** — `<input>` element with a search icon. No form wrapper, no `onsubmit`, no `oninput` handler. Pressing Enter does nothing.

3. **Non-functional notification bell** — Bell emoji in the top bar. No click handler, no badge. Reads as a dormant feature stub.

Social auth buttons on login/signup constitute a fourth category — they are fully functional as links, but they route to 404 errors.

### Emoji as UI Primitives

The sidebar navigation uses emoji as the primary icon system: an emoji precedes each nav label. The AgentX tab is `🤖 AgentX`. The Takeoff empty state is `📐`. Toolbar empty state is `📋`. These are not accessible to screen readers without explicit `aria-label` attributes. None were observed.

### Mobile

`base.html` has a responsive hamburger menu (confirmed in prior reading). `app_base.html` has no visible mobile breakpoints in the CSS variable section; the 260px fixed sidebar does not collapse. Takeoff (`viewer.html`) is a canvas-based layout; no mobile adaptation is expected or documented.

### Keyboard and Focus

No keyboard shortcut documentation observed for the authenticated app. The Takeoff module has Snap/Ortho toggles via status bar buttons, not keyboard shortcuts (though keyboard handling for canvas tools may exist in `takeoff.js`, not read). The TanStack grid supports click-to-edit cells but tab-to-next-cell behavior was not confirmed.

---

## 7. Legacy and Parallel Surfaces

| Surface | Status | Risk |
|---|---|---|
| `index.html` (dashboard) | Active — deprecated design system | First authenticated screen; severe discontinuity |
| `nav.html` (old nav partial) | Active — used by legacy pages | "Construction Estimator" brand visible to users |
| `agentx_panel.html` | Active — included by `index.html` and `project.html` | AgentX identity contradicts Tally strategy; 1,860-line maintenance burden |
| Legacy estimate table in `project.html` | Active — inline in project detail page | Parallel to TanStack table; users see legacy table, not new one |
| `estimate.html` (orphaned) | Route disabled per ADR-024 | Not a user-facing risk; maintenance artifact |
| `estimate_table.html` | Active but unreachable via normal nav | TanStack table exists but no link from project page |

The most consequential legacy surface is `index.html`. It is the first page every authenticated user sees. It has not been migrated to `app_base.html`. Every session starts with the wrong design system, the wrong brand name, and the legacy AI panel.

---

## 8. Findings Worth Acting On

Ranked by user impact:

**1. index.html must extend app_base.html (critical)**  
The authenticated dashboard uses the deprecated design system. Every user sees it immediately after login. The fix is a migration to `app_base.html` with CSS variables. This is not a cosmetic issue — the brand name displayed is wrong.

**2. Landing CTA copy must match product state (critical)**  
The body text below the CTA says "14-day free trial, no credit card required, full access." The button links to `/waitlist`. These contradict each other. Anyone who reads the copy before clicking receives false product information.

**3. Social auth buttons must be removed or routes must exist (high)**  
Google and Microsoft auth buttons on login and signup produce routing errors. They should either be removed until the routes exist or clearly labeled as "coming soon" and disabled.

**4. Tally footer banner and Passive column badges need data wiring (high)**  
The scaffolding exists in `estimate_table.js` — `AI_STATUS` constants, `ai_status` and `ai_confidence` column definitions, the static Tally banner. Wiring the backend to populate these fields would activate Tally Passive without new UI work. This is the first Tally milestone.

**5. AgentX must be renamed Tally in all user-facing strings (high)**  
The tab button, welcome bubble, toast messages, mode labels, and panel title all say "AgentX." The CSS class prefix `ax-` is internal and can stay. The user-facing strings can be changed with low risk.

**6. IBM Plex Sans import must be removed from estimate_table.html (medium)**  
A documented prohibition is violated. The system UI font stack is sufficient. Remove the Google Fonts `<link>` tag; no other change needed.

**7. Disabled Takeoff tool buttons should be hidden or explained (medium)**  
Rendering 7 buttons at full opacity with a `not-allowed` cursor communicates broken features. Either hide them until implemented, or add a tooltip ("Coming in Pass 3") that appears on hover.

**8. Non-functional search and bell in top bar (medium)**  
Both are rendered as interactive elements with no behavior. Remove them or implement them. Placeholder UI in the top bar trains users to ignore controls.

**9. Design token duplication should be resolved (low, architectural)**  
Three simultaneous token definitions (CSS vars, `ZB` JS object, hardcoded hex in CSS) will drift. The `ZB` object in `estimate_table.js` and the hardcoded values in `estimate_table.css` should reference CSS variables via `getComputedStyle` or be replaced with the variable names directly where CSS-in-JS is not required.

**10. Signup Terms/Privacy links must resolve (low, but legal risk)**  
The signup consent checkbox links to `/terms` and `/privacy`. These are CRITICAL gaps in CLAUDE.md. A user cannot give informed consent through broken links.

---

## 9. Verdict

The marketing surface is clean and mostly consistent. The app surface is not.

The product has two competing design systems, two competing AI identities, two competing estimate table implementations, and a product name that appears in four different forms. The authenticated entry point (`index.html`) is the clearest evidence of the split: it renders the old system in full, before any new surface is visible.

The strategic documents describe a coherent, unified product. The implementation describes two products in the same repository — one from before the rebrand and one from after it — with no wall between them. Users experience both in a single session.

The highest-leverage single action is migrating `index.html` to `app_base.html`. Everything else a logged-in user encounters is on the new system. The dashboard is the only holdout, and it is the first thing they see.

Tally is visible nowhere. AgentX works, but its future is not in the documents. The TanStack grid has the scaffolding for Tally Passive mode. The path from here to a live Tally interaction is shorter than it looks from the documentation — the database fields exist, the column definitions exist, the status badge rendering exists. What is missing is the backend populating them and the frontend rendering real values instead of stubs.

---

**Docs read:** 6 strategic docs + CLAUDE.md design sections  
**Templates walked:** 14 (base.html, app_base.html, landing, login, signup, waitlist, pricing, index, nav, project, estimate_table, takeoff/viewer, agentx_panel, estimate_table.css, takeoff.css, estimate_table.js)  
**Verdict:** Two products in one repo. The seam is the login page.  
**File committed:** `02_DESIGN_AUDIT.md`
