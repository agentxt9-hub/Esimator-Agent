# Architecture Decision Record (ADR) - Zenbid

> **Purpose:** Document important technical and product decisions with context and rationale.  
> **Format:** Following ADR best practices (used by engineering teams worldwide).  
> **How to use:** When you make a key decision, add an entry. Number them sequentially.

---

## ADR-001: Switched from Ollama/Llama to Claude API

**Date:** 2026-03-12 (Session 9)  
**Status:** Accepted

### Context
Initially built AI features with local Ollama + Llama 3.1 for cost savings and offline capability. Performance was too slow (5-10 second response times) and quality underwhelming for construction domain reasoning.

### Decision
Switch to Claude API (claude-sonnet-4-6) for all AI features.

### Rationale
- Fast responses critical for good UX (1-2 seconds vs 5-10 seconds)
- Higher quality reasoning for construction estimating
- No local GPU/hardware requirements
- Simpler deployment (no model hosting)
- API costs acceptable for beta/MVP stage (~$0.003 per request)

### Consequences
**Positive:**
- Much faster AI responses
- Better quality assistance (scope gap detection, rate validation)
- Easier deployment to DigitalOcean
- Can optimize costs later (caching, cheaper models for simple tasks)

**Negative:**
- Ongoing API costs (need to monitor usage)
- External service dependency (need error handling)
- Requires ANTHROPIC_API_KEY in server .env

**Neutral:**
- Built modular AI service layer, can swap models if needed

### Alternatives Considered
- **OpenAI GPT-4:** More expensive, similar quality
- **Google Gemini:** Not as strong for technical reasoning
- **Continue with Ollama:** Rejected due to speed issues

**Related Files:** app.py (all /ai/* routes), agentx_panel.html

---

## ADR-002: Flask + PostgreSQL over Django

**Date:** 2026-03-08 (Session 1)  
**Status:** Accepted

### Context
Starting new SaaS product. Needed to choose web framework and database. Non-technical founder relying on Claude Code for all development.

### Decision
Use Flask + PostgreSQL (not Django + SQLite).

### Rationale
- Flask lightweight, easier for AI code generation
- PostgreSQL production-ready from day one
- Don't need Django's admin panel or ORM complexity for MVP
- Simpler for non-technical founder to understand
- Claude generates cleaner, more understandable Flask code

### Consequences
**Positive:**
- Less boilerplate to manage
- Production database from start (no migration pain later)
- Faster iteration (minimal magic, explicit code)
- Can add features incrementally

**Negative:**
- Had to build auth from scratch (vs Django's built-in)
- No built-in admin panel (created custom /admin route)
- More manual SQL/schema management via migrations

**Neutral:**
- Could add Django admin interface later if needed (as separate service)

**Related Files:** app.py (all routes + models), requirements.txt

---

## ADR-003: Multi-Tenancy with Company-Based Isolation

**Date:** 2026-03-11 (Session 7)  
**Status:** Accepted

### Context
Need multiple users to share the app. How to handle data separation for different construction companies?

### Decision
Companies table as tenant root. Every record has company_id foreign key. Users belong to one company. Data isolated by company_id in all queries.

### Rationale
- Most contractors work in companies (GC firms, subs)
- Team collaboration within company needed
- Strict data isolation for security/privacy
- Standard SaaS multi-tenancy pattern
- Enables future enterprise features

### Consequences
**Positive:**
- Clean data separation (Company A can't see Company B's data)
- Team features built-in from day one
- Scales to enterprise clients
- Industry-standard approach (easier to explain/sell)

**Negative:**
- Every query must filter by company_id (risk of data leaks if forgotten)
- More complex testing (need to verify multi-tenant scenarios)
- Migration complexity for adding company_id to existing tables

**Neutral:**
- Could add cross-company sharing later (for GC-sub workflows)

**Related Models:** Company, User, Project, Assembly, LineItem, LibraryItem, GlobalProperty, CompanyProfile

**Security Pattern:**
```python
def get_project_or_403(project_id):
    project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first()
    if not project:
        abort(403)
    return project
```

---

## ADR-004: AI Optional, Not Mandatory (Dual-Natured Tool)

**Date:** 2026-03-09 (Session 3, codified in NORTHSTAR.md)  
**Status:** Accepted

### Context
Defining core product philosophy. Who is this for and how should it work?

### Decision
Build a tool that serves BOTH experienced estimators (prefer rigid Excel-like workflows) AND newer estimators (benefit from AI guidance). AI layer always optional, never mandatory.

### Rationale
- Experienced estimators skeptical of AI
- Forcing AI reduces addressable market
- Want adoption from traditional firms (large potential market)
- Users should be able to build complete professional estimate without touching AI once
- AI becomes competitive advantage, not gatekeeper

### Consequences
**Positive:**
- Wider market appeal (both generations of estimators)
- Can sell to conservative/traditional firms
- AI becomes upsell feature, not barrier to entry
- Builds trust with skeptical users ("try it when you're ready")

**Negative:**
- More complex to build (support two workflows)
- Marketing must address both personas
- Feature priority conflicts (Excel power vs AI magic)

**Neutral:**
- Some users will never use AI features (that's okay, they're paying customers)

**Product Test:**
> *Could a rigid (Excel-minded) estimator use this comfortably? Could a flexible (AI-native) estimator use this expressively?* If either answer is "no," reconsider the design.

**Related Files:** NORTHSTAR.md, agentx_panel.html (optional sliding panel)

---

## ADR-005: Permission-Gated AI Writes

**Date:** 2026-03-12 (Session 9)  
**Status:** Accepted

### Context
Designing AI panel interactions. Should AI auto-save changes or require user confirmation?

### Decision
AI must ALWAYS get user confirmation before writing to database.

### Rationale
- Estimating is high-stakes (bids = money, wrong number = lost profit)
- Trust built through transparency
- Users need to review AI suggestions before committing
- Prevents accidental data corruption or bad estimates

### Consequences
**Positive:**
- Builds user trust ("I'm in control")
- Prevents costly errors
- Users learn from reviewing AI suggestions
- Clear audit trail (user explicitly approved each change)

**Negative:**
- Extra click for every AI action (slightly slower workflow)
- Power users may find it annoying
- Can't fully automate estimate generation

**Neutral:**
- Could add "auto-approve trusted operations" later as premium feature

**Implementation:** All AI write proposals return JSON; frontend renders proposal card with "Apply" button; Apply button calls /ai/apply route.

**Related Files:** agentx_panel.html (proposal rendering), app.py (/ai/apply route)

---

## ADR-006: Single-File Flask App (No Blueprints)

**Date:** 2026-03-08 (Session 1)  
**Status:** Accepted (may revisit at 5000+ lines)

### Context
How to structure Flask application? Blueprints vs single file?

### Decision
Keep everything in single app.py file (~3450 lines as of Session 12).

### Rationale
- Simpler for AI code generation (Claude can see entire app)
- Easier for non-technical founder to understand
- Faster iteration (no import management)
- No premature abstraction
- Can refactor to blueprints later if needed

### Consequences
**Positive:**
- Fast development velocity
- Easy to search/navigate (Ctrl+F finds anything)
- No circular import issues
- Claude Code works better with single file

**Negative:**
- Large file getting harder to navigate (~3450 lines)
- Merge conflicts if collaborating (not an issue yet - solo founder)
- IDE performance may degrade (not yet an issue)

**Neutral:**
- Can split into blueprints when file hits 5000 lines or when adding second developer

**Revisit Trigger:** File size > 5000 lines OR adding second developer

---

## ADR-007: Dark Theme as Default (No Light Mode)

**Date:** 2026-03-14 (Session 11c)  
**Status:** Accepted

### Context
Redesigning app UI. Light theme vs dark theme vs both?

### Decision
Dark theme only. No light mode toggle.

### Rationale
- Professional construction software aesthetic
- Reduces eye strain for estimators (long sessions)
- Differentiates from Excel/legacy tools
- Simpler to maintain (one theme, no toggle logic)
- Modern SaaS aesthetic

### Consequences
**Positive:**
- Consistent brand identity
- Professional appearance
- Less CSS complexity (no theme switching)
- Battery savings on OLED displays

**Negative:**
- Some users may prefer light mode
- Print/PDF views need light theme (solved: proposal.html uses light theme)

**Technical Implementation:**
- CSS variables in app_base.html
- Dark navy (#1a1a2e) + red (#e63946) color scheme
- Proposal template uses light theme for printing

**Related Files:** Templates/app_base.html (CSS vars), Templates/base.html (marketing light theme), Templates/proposal.html (light theme for print)

---

## ADR-008: Flask-Login for Auth (Not JWT)

**Date:** 2026-03-11 (Session 7)  
**Status:** Accepted

### Context
Need user authentication. Flask-Login vs JWT vs custom session auth?

### Decision
Use Flask-Login with server-side sessions.

### Rationale
- Simpler for traditional web app (not API-first)
- Works seamlessly with Jinja templates
- No token expiry complexity
- Session revocation built-in (logout = instant)
- Industry standard for Flask apps

### Consequences
**Positive:**
- Easy to implement (`@login_required` decorator)
- Works with existing Jinja templates
- Secure session management
- Easy logout/session revocation

**Negative:**
- Server-side sessions (need sticky sessions for multi-server)
- Can't easily share auth with mobile app (not needed yet)
- Not ideal for pure API usage (not needed yet)

**Neutral:**
- Can add JWT for API later if needed (separate /api/* routes)

**Related Files:** app.py (User model, Flask-Login setup, login/logout routes)

---

## ADR-009: DigitalOcean for Hosting

**Date:** 2026-03-14 (Session 11c)  
**Status:** Accepted

### Context
Need production hosting. Considered AWS, Heroku, DigitalOcean, Vercel.

### Decision
DigitalOcean Droplet + managed PostgreSQL (~$21/month).

### Rationale
- Simple pricing, no surprise bills
- Managed Postgres easy to set up
- Full control over server (SSH access)
- Good performance for price
- Less complex than AWS
- Predictable costs

### Consequences
**Positive:**
- Predictable monthly costs
- Fast setup (deployed in Session 11c)
- Good performance
- Easy to manage (SSH + systemd service)

**Negative:**
- Manual server management vs Heroku PaaS
- Need to handle deployments ourselves (solved: deploy/update.sh script)
- Limited auto-scaling (fine for MVP)

**Current Status:** zenbid.io fully operational (restored Session 13, 2026-03-17)

**Deployment Process:**
1. SSH into droplet
2. `bash /var/www/zenbid/deploy/update.sh`
3. Systemd service restarts automatically
4. Gunicorn runs migrations on startup

**Alternatives Considered:**
- **AWS:** Too complex for solo founder; unpredictable costs
- **Heroku:** Expensive for Postgres ($50+/month)
- **Vercel:** Great for Next.js, not ideal for Flask

**Related Files:** deploy/setup.sh, deploy/update.sh, gunicorn_conf.py, Procfile

---

## ADR-010: CSRF Protection via Flask-WTF

**Date:** 2026-03-15 (Session 12)  
**Status:** Accepted

### Context
Security audit before beta launch. How to protect against CSRF attacks?

### Decision
Use Flask-WTF CSRFProtect with meta tag + fetch monkey-patch.

### Rationale
- Industry standard for Flask
- Easy to implement
- Works with both forms and AJAX
- Minimal performance impact

### Consequences
**Positive:**
- Protected against CSRF attacks
- Works seamlessly with existing code
- Fetch monkey-patch auto-injects token into all AJAX requests

**Negative:**
- Need to add `{{ csrf_token() }}` to all new HTML forms
- Token in meta tag (minor exposure, but standard practice)

**Technical Implementation:**
```python
# app.py
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# app_base.html
<meta name="csrf-token" content="{{ csrf_token() }}">
<script>
  // Monkey-patch fetch to include CSRF token
  const originalFetch = window.fetch;
  window.fetch = function(...args) {
    if (args[1] && (args[1].method === 'POST' || args[1].method === 'PUT' || args[1].method === 'DELETE')) {
      args[1].headers = args[1].headers || {};
      args[1].headers['X-CSRFToken'] = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    return originalFetch.apply(this, args);
  };
</script>
```

**Related Files:** app.py (CSRFProtect), Templates/app_base.html (meta tag + monkey-patch)

---

## ADR-011: Rate Limiting via Flask-Limiter (In-Memory)

**Date:** 2026-03-15 (Session 12)  
**Status:** Accepted (Provisional - may migrate to Redis)

### Context
Need to protect AI routes and login from abuse. How to implement rate limiting?

### Decision
Use Flask-Limiter with in-memory storage.

### Rationale
- Simple to implement
- No external dependencies (Redis) for MVP
- Sufficient for single-server deployment
- Can migrate to Redis later for multi-server

### Consequences
**Positive:**
- Protection against brute-force login
- Protection against AI API abuse (costly)
- Easy to implement (decorators)

**Negative:**
- In-memory storage = resets on server restart
- Won't work across multiple servers (need Redis for that)

**Neutral:**
- Acceptable trade-off for MVP
- Will migrate to Redis when scaling to multiple servers

**Current Limits:**
- `/login`: 5 requests per minute
- All `/ai/*` routes: 20 requests per minute

**Migration Path:** When scaling, change to `storage_uri='redis://localhost:6379'`

**Related Files:** app.py (Flask-Limiter setup, @limiter.limit decorators)

---

## ADR-012: Password Reset via Email Tokens

**Date:** 2026-03-15 (Session 12)  
**Status:** Accepted

### Context
Users need to reset forgotten passwords. How to implement securely?

### Decision
Time-limited tokens (1 hour) sent via email, stored in User model.

### Rationale
- Standard pattern (Django, Rails all use this)
- Secure (random tokens, time-limited)
- Simple to implement with Flask-Mail
- No third-party service needed

### Consequences
**Positive:**
- Secure password reset flow
- Tokens expire after 1 hour
- Email delivery via SendGrid (reliable)

**Negative:**
- Requires MAIL_PASSWORD env var on server
- Relies on email delivery (could fail)

**Technical Implementation:**
- User model: `reset_token`, `reset_token_expires` columns
- Route: `/forgot-password` generates token, sends email
- Route: `/reset-password/<token>` validates token, resets password
- Token: `secrets.token_urlsafe(32)`, expires in 1 hour

**Related Files:** app.py (/forgot-password, /reset-password routes), Templates/forgot_password.html, Templates/reset_password.html

---

## ADR-013: Separate Growth Hub Server from Zenbid App Server

**Date:** 2026-03-19 (Session 17)
**Status:** Accepted

### Context
Need agentic growth marketing infrastructure (n8n workflows, Flowise AI agents, monitoring). Decision: run on the same droplet as Zenbid, or a dedicated server?

### Decision
Provision a second DigitalOcean droplet (45.55.33.136) exclusively for growth/agentic tooling. All services run via Docker Compose in `/opt/agentx-hub/`.

### Rationale
- Keeps agentic workflows completely isolated from customer-facing app
- Growth Hub can be restarted, updated, or broken without any risk to zenbid.io
- Independent scaling — Hub can be resized without touching the app server
- Docker Compose on Hub vs systemd on App — different deployment patterns, cleaner separation
- Easier to reason about each server's purpose

### Consequences
**Positive:**
- Zero blast radius from Hub failures on customer-facing app
- Can experiment freely with n8n/Flowise workflows without production risk
- Clear separation of concerns: app server = revenue, hub = growth
- Independent cost control (can spin down Hub if unused)

**Negative:**
- Two servers to maintain instead of one
- Slightly higher monthly cost (~$12-18/month extra)
- Cross-server communication via HTTP webhooks (not in-process)

**Neutral:**
- Webhook pattern (app → Hub) is loosely coupled and easy to extend

**Services on Hub:** n8n (flows.zenbid.io), Flowise (agents.zenbid.io), Dashy (hub.zenbid.io), Portainer (docker.zenbid.io), Uptime Kuma (status.zenbid.io), Nginx Proxy Manager (proxy.zenbid.io)

**Related Files:** `/opt/agentx-hub/docker-compose.yml` (on Growth Hub droplet)

---

## ADR-014: Client-Side PDF Thumbnails via PDF.js

**Date:** 2026-04-06 (Session 18)
**Status:** Accepted

### Context
Server-side thumbnail generation (pdf2image at 72 DPI, one page at a time) OOM-killed the 1 GB DigitalOcean droplet on large commercial drawing sets (50+ pages). Even page-by-page processing held all PIL Image objects in memory simultaneously before the first `del` could fire.

### Decision
All thumbnail rendering happens in the browser using PDF.js at `scale: 0.15`. Server stores `thumbnail_path=None` for every page record. No image data ever touches the server.

### Rationale
- Zero server memory for thumbnails regardless of PDF size
- Upload is instant (page count via `fitz.open` only)
- PDF.js is already loaded for the main canvas — no extra dependency
- Thumbnails regenerate each session (acceptable for MVP)
- Scales to any PDF size on any server hardware

### Consequences
**Positive:**
- No OOM risk on upload
- Instant upload response (just page count + DB records)
- Works on the smallest DO droplet

**Negative:**
- Thumbnails visible ~1–3 seconds after page load while PDF.js renders them
- Thumbnails re-render each session (no caching)
- Requires JavaScript (no fallback for bots/crawlers — not relevant for app)

**Neutral:**
- `pdf2image` and `Pillow` removed from requirements.txt

**Related Files:** routes_takeoff.py (upload route), static/js/takeoff.js (generateThumbnails), requirements.txt

---

## ADR-015: CSS Transform Pan/Zoom with Offscreen Canvas Re-render

**Date:** 2026-04-06 (Session 18)
**Status:** Superseded by ADR-017

### Context
Re-rendering the PDF via PDF.js on every mouse event (wheel, mousemove) caused visibly laggy, jumpy pan/zoom — PDF decode is expensive even at modest zoom levels. The old approach called `page.render()` on every wheel tick.

### Decision
All pan and zoom manipulates CSS `transform` on a `#canvas-inner` wrapper div. PDF.js decodes the page only on zoom end (600 ms debounce). The quality re-render renders to an offscreen canvas first, then swaps atomically via `requestAnimationFrame`. Pan updates are also RAF-batched.

### Rationale
- CSS `transform` is GPU-accelerated — zero CPU/decode cost during interaction
- Offscreen render + RAF swap eliminates visible canvas resize or blank flash
- 600 ms debounce means quality re-render fires only once per zoom gesture
- `Math.pow(0.999, e.deltaY)` gives continuous wheel factor — smooth on trackpads
- `baseRenderScale: 2.0` delivers retina-quality output after re-render

### Consequences
**Positive:**
- Smooth 60fps pan/zoom at any zoom level
- No jank during interaction
- Clean coordinate system for Session 19 hit testing (wrap→canvas→PDF math)

**Negative:**
- Slight quality delay (up to 600ms) after zoom end — imperceptible in practice
- Slightly higher initial render cost (2.0× scale vs 1.0×) — ~100ms extra on first load

**Neutral:**
- `#canvas-inner` wrapper is the only HTML change — rest of DOM untouched

**Related Files:** static/js/takeoff.js (rerenderAtCurrentZoom, _onWheel, _schedulePanUpdate), templates/takeoff/viewer.html (#canvas-inner), static/css/takeoff.css (#canvas-inner styles)

---

## ADR-017: Konva.js Canvas Architecture (Supersedes ADR-015)

**Date:** 2026-04-07 (Session 19)
**Status:** Accepted

### Context
The CSS transform + dual raw canvas approach (ADR-015) solved Session 18's pan/zoom performance problem but left two architectural gaps heading into Session 19 measurement tools:
1. **Hit detection** — raw canvas has no built-in object graph; Session 19 needs to know which measurement shape the user clicked
2. **Layer management** — PDF rendering, measurement overlays, and selection handles on a single z-stacked pair of canvases is fragile and will require complex manual compositing

### Decision
Replace `#canvas-inner` / `#pdf-canvas` / `#overlay-canvas` with a Konva.js stage containing three explicit layers:
- `pdfLayer` — one `Konva.Image` wrapping a PDF.js-rendered offscreen canvas
- `measureLayer` — `Konva.Shape` objects for each measurement (Session 2)
- `uiLayer` — selection handles, vertex dots, labels

PDF.js still does all PDF decoding. Konva handles everything visual after that.

### Rationale
- **Native pan/zoom** — `stage.draggable: true` + wheel scale handler; buttery smooth, no custom RAF/debounce loop
- **Built-in hit detection** — `shape.on('click')` fires without any manual bounding-box math; Session 2 measurement selection is trivial
- **Layer isolation** — PDF and overlays are composited by the GPU in separate Konva layers; no manual canvas clearing/redraw ordering
- **Tween API** — `Konva.Tween` gives smooth animated zoom-to-fit and button zooms with a single call
- **Coordinate system** — `state.screenToPDF(x, y)` converts stage pointer → PDF-space; single source of truth for all Session 2 geometry

### Consequences
**Positive:**
- Session 2 measurement tools reduce to: add Konva shape to measureLayer, store PDF-space coords
- No debounce timer or offscreen canvas swap logic (simpler code, fewer edge cases)
- `Konva.Stage` resizes cleanly on window/sidebar resize
- Pinch zoom works via direct `stage.scale()` calls in the touch handler

**Negative:**
- Konva adds ~150 KB CDN script (loaded before takeoff.js)
- PDF.js render still happens at 2× RENDER_SCALE for retina quality; no progressive re-render on zoom (acceptable — image scales via GPU)

**Neutral:**
- `generateThumbnails()` is unchanged — still uses PDF.js small-scale canvas renders
- All 31 integration tests continue to pass (they test server routes, not canvas internals)

**Alternatives Considered:**
- **Fabric.js:** Similar to Konva but heavier, less maintained
- **Continue with raw canvas:** Hit detection for Session 2 would require manual bounding-box math per shape type — rejected

**Related Files:** static/js/takeoff.js (initStage, renderPDFPage, zoomToFit, zoom), templates/takeoff/viewer.html (#konva-container), static/css/takeoff.css (#konva-container)

---

## ADR-016: PyMuPDF for Page Count Only

**Date:** 2026-04-06 (Session 18)
**Status:** Accepted

### Context
Need to know how many pages a PDF has immediately on upload, so the server can create the correct number of `TakeoffPage` records. Options: pdf2image + pdfinfo, pypdf, PyMuPDF. All of these can count pages; the question is what else they pull into the process.

### Decision
`fitz.open(pdf_path)` → `total_pages = len(doc)` → `doc.close()`. No pixel data, no image extraction, no rendering. PyMuPDF is the only PDF library in production.

### Rationale
- PyMuPDF is fast and reliable for page count even on corrupt/unusual PDFs
- `len(doc)` returns immediately without decoding any page content
- Single library rather than pdf2image + poppler dependency chain
- Makes the server-side contract explicit: count only, render never

### Consequences
**Positive:**
- Upload is O(1) in memory regardless of page count
- No poppler binary dependency on the server
- Clean separation: server = metadata, browser = rendering

**Negative:**
- PyMuPDF (~40 MB) is a heavier install than pypdf (~1 MB) for just page count
- If PyMuPDF import fails, fallback is `total_pages = 1` (graceful but wrong)

**Neutral:**
- `try/except` wraps the `fitz.open` call — fallback ensures upload never hard-fails

**Related Files:** routes_takeoff.py (upload_pdf route), requirements.txt

---

## ADR-018: Vendor Critical JS Dependencies Locally

**Date:** 2026-04-07 (Session 19)
**Status:** Accepted

### Context
After migrating to Konva.js, the CDN URL (`cdnjs.cloudflare.com`) proved unreliable when loaded from the DigitalOcean droplet in production — the script failed to load, causing "Konva is not defined" errors. PDF.js loads fine because browsers (not the server) fetch it; Konva was previously loaded server-side during SSR testing and also blocked in certain network paths.

### Decision
Vendor Konva.js locally at `static/js/konva.min.js`. Load it with a direct `<script src="/static/js/konva.min.js">` tag. PDF.js remains on CDN because it is always fetched by the browser, not the server.

### Rationale
- CDN unreliability from DigitalOcean is a known issue (certain outbound HTTP blocked)
- Local serving is 100% reliable regardless of CDN availability or network path
- File size (~171 KB) is acceptable for a single vendored dependency
- Browser still loads PDF.js from CDN — zero server-side fetch involved

### Consequences
**Positive:**
- Konva loads reliably on every page visit regardless of CDN status
- No dependency on third-party CDN availability for core canvas functionality
- Can pin exact version without CDN cache surprises

**Negative:**
- Repo is ~171 KB larger
- Must manually update `konva.min.js` when upgrading Konva version

**Neutral:**
- PDF.js still via CDN (browser fetch — not affected by server network restrictions)
- `static/uploads/` gitignored separately; only `static/js/` vendored files are committed

**Related Files:** `static/js/konva.min.js`, `templates/takeoff/viewer.html`

---

## ADR-019: Ortho Mode Constrains to 45° Increments

**Date:** 2026-04-07 (Session 21)
**Status:** Accepted

### Context
During polygon/polyline drawing, construction estimators frequently need perfectly horizontal, vertical, or 45° diagonal lines (wall runs, roof ridges, etc.). Without a constraint mode, hand-drawn lines are slightly off-axis, making takeoffs look imprecise.

### Decision
Ortho mode uses `Math.atan2(dy, dx)` → rounds to nearest `Math.PI / 4` increment → reconstructs endpoint at original distance. Applied to both click-commit points and the live preview line while cursor moves.

### Rationale
- `π/4` increments give 8 directions: 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°
- Preserves cursor distance (no shortening) — only snaps direction
- Same formula applied to preview = user sees snapped line before committing
- Toggle via status bar click or keyboard (future) — non-destructive, off by default

### Consequences
**Positive:**
- Precise horizontal/vertical/diagonal measurements with one toggle
- Preview snapping gives immediate visual feedback

**Negative:**
- 45° increments only (no arbitrary angle lock); acceptable for construction takeoff
- Cursor visually "jumps" direction — expected behavior in CAD tools

**Neutral:**
- State stored in `state.orthoMode` boolean; no DB changes

**Related Files:** `static/js/takeoff.js` (`_orthoConstrain()`, `_drawToolClick()`, `_updateDrawPreview()`), `templates/takeoff/viewer.html` (`#tk-status-ortho`)

---

## ADR-020: Project-Level Measurement Totals via Relationship Traversal

**Date:** 2026-04-07 (Session 21)
**Status:** Accepted

### Context
Each `TakeoffMeasurement` belongs to a specific page (FK→`takeoff_pages.id`). The `GET /items` endpoint initially returned only the list of items without any aggregate quantities. Users need to see total LF / SF / EA for an item summed across all pages in the project.

### Decision
`list_items` iterates `item.measurements` (SQLAlchemy relationship, no page filter) and sums `calculated_value` for each item. This cross-page total is returned as `item['total']` in the JSON response. No separate aggregation route needed.

### Rationale
- The SQLAlchemy `TakeoffItem.measurements` relationship already returns all measurements across all pages for that item
- No `GROUP BY` query needed — Python-side sum over the ORM relationship is clean and readable
- Single endpoint (`GET /items`) returns both item definitions and totals — fewer round trips

### Consequences
**Positive:**
- Zero extra code beyond what was already written — just use the relationship
- Single API call populates both item list and totals sidebar

**Negative:**
- For items with thousands of measurements this could be slow — not a concern at MVP scale

**Neutral:**
- `calculated_secondary` (perimeter) is not aggregated here — intentional; perimeter per-measurement is the correct unit

**Related Files:** `routes_takeoff.py` (`list_items`), `static/js/takeoff.js` (right-sidebar total render)

---

## ADR-021: TanStack Table v8 for Estimate Grid

**Date:** 2026-04-07 (Session 22)
**Status:** Accepted

### Context
Zenbid's estimate table is the core product surface. The existing `estimate.html` used a plain `<table>` with vanilla JS — functional but with a feature ceiling: no column reorder, no resize, no grouping, no inline row selection, no export. Evaluating AG Grid Enterprise vs. building on a headless library.

### Decision
Use **TanStack Table v8** (headless, MIT license) + custom React UI layer for the estimate grid. SheetJS for Excel/CSV export. Delivered via CDN script tags + Babel Standalone (no build pipeline added to repo).

### Rationale
- No vendor license ceiling — AG Grid Enterprise gates column panel, row grouping UI behind $1,500/dev/year
- TanStack Table v8 is headless: provides row models, sorting, filtering, column state — we own all the UI
- React via CDN + Babel Standalone fits the Flask+Jinja architecture (no npm required)
- SheetJS (MIT) handles Excel formatting including currency column styles

### Consequences

**Positive:**
- Full design system control — every pixel matches Zenbid design tokens
- No feature gating from a vendor
- Column reorder, resize, show/hide, grouping, inline edit, AI badges, export — all built and owned
- Data flywheel fields (ai_generated, estimator_action, edit_delta) captured from day one per TALLY_VISION.md

**Negative:**
- Babel Standalone adds ~300 KB CDN load and transpiles JSX in-browser (one-time ~1s hit on first page load)
- TanStack Table v8 UMD build (~50 KB) must be loaded from unpkg CDN
- Future complex features (virtual scroll for 10,000+ rows) require additional work

**Neutral:**
- estimate.html preserved as fallback — route now serves estimate_table.html
- 29 pytest tests cover all API endpoints (GET/POST/PATCH/DELETE), company isolation, CSRF, and data flywheel fields

### Alternatives Considered
- **AG Grid Community:** Free but missing grouping, column panel, Excel export without Enterprise
- **AG Grid Enterprise:** Full-featured but $1,500/dev/year + React dependency + vendor lock-in
- **Vanilla JS table (extend existing):** Rejecting — hit complexity ceiling; drag-reorder and column state alone would be 400+ lines of brittle custom code

**Related Files:** `templates/estimate_table.html`, `static/js/estimate_table.js`, `static/css/estimate_table.css`, `tests/test_estimate_table.py`, `app.py` (API routes + LineItem model additions)

---

## ADR-022: Dual Costing Models as First-Class Paradigms

**Date:** 2026-04-13 (Pass 1 — Realignment)
**Status:** Accepted

### Context
The legacy estimate surface was built around the assembly build-up model: qty → production_rate → labor_hours → labor_cost → total. This works well for labor-heavy trades (drywall, framing, concrete, painting). But half the trades that estimators actually use bid flat unit prices — doors, hardware, fixtures, specialty items. Those estimators have no good home in an assembly-only tool.

### Decision
Unit cost (`qty × unit_cost = line_total`) and assembly build-up (`qty + production_rate + labor_rate + material_rate → computed unit_cost → line_total`) are equal, co-resident paradigms. Both render in the same TanStack grid, line by line. No global mode toggle. The grid validates a line as complete if **either** path resolves to a `line_total`.

**UI pattern:** Expandable row. Default row shows qty + unit_cost + line_total. A chevron expands to reveal the assembly build-up fields, which compute unit_cost upward. No context switch, no separate view. Design spike in Pass 3.

### Rationale
- **Trade breadth:** unit-cost-only strands half the trades; assembly-only strands the other half; both are required for the Cost Intelligence flywheel to accumulate real market data across all trade sectors
- **Retention:** estimators who define burden-loaded assemblies in Zenbid don't go back to Excel; unit-cost-only users can leave anytime; assembly is stickiness
- **Flywheel:** both paths contribute to the same data structure; the cost intelligence layer requires both to reach GC-grade breadth competitive with RSMeans

### Consequences

**Positive:**
- Addresses the full market (all trade sectors, not just labor-heavy ones)
- Assembly build-up is a retention mechanism; unit cost is an acquisition mechanism
- Single grid; no UI fragmentation

**Negative:**
- More complex column schema on LineItem (must support both paths)
- Expandable row adds UI complexity (design spike required before Pass 3 build)

**Neutral:**
- Formula column (Mode 3) is a distinct future capability — see ADR-023

### Alternatives Considered
- **Primary/secondary model:** unit cost as default, assembly as "advanced mode" — rejected; creates a hierarchy that strands assembly-thinking trades
- **Mode toggle:** switch the whole grid between modes — rejected; forces a single mental model on all rows simultaneously

**Related Files:** `templates/estimate_table.html`, `static/js/estimate_table.js`, `app.py` (LineItem model)

---

## ADR-023: Formula Column as Mode 3 (Future)

**Date:** 2026-04-13 (Pass 1 — Realignment)
**Status:** Accepted (Deferred)

### Context
A formula column — where a cell value is computed from an arbitrary expression referencing other row fields — was prototyped in an early session. It is distinct from both unit cost and assembly build-up.

### Decision
Formula column is **Mode 3**. It is deferred to a premium tier feature. When implemented, it will be a cell-level option (the formula lives in a specific cell, not as a row pattern). It is named now so ADR-022 does not foreclose it.

### Rationale
- Too complex to design and test safely alongside the dual-costing migration in Pass 3
- Power-user feature with a natural premium tier price point
- Cell-level scope avoids polluting the row model that ADR-022 defines

### Consequences

**Positive:**
- Clearly reserved — no other ADR will accidentally design over this space

**Negative:**
- Power users who need formula cells have to wait
- Must ensure Pass 3 row schema doesn't make formula cells architecturally impossible

**Neutral:**
- Premium tier positioning means it can be gated behind a billing feature flag

**Related Files:** Future `app.py` LineItem schema; `static/js/estimate_table.js`

---

## ADR-024: TanStack Table as Canonical Estimate Surface

**Date:** 2026-04-13 (Pass 1 — Realignment)
**Status:** Accepted

### Context
Session 22 delivered `estimate_table.html` + `estimate_table.js` as a new estimate surface (TanStack Table v8, React via CDN). The `/project/<id>/estimate` route was immediately pointed at the new surface. The legacy `project.html` inline estimate table still exists on the project page. `estimate.html` (the old full-page estimate) is now an orphaned template with no route.

There are therefore two live estimate UIs:
1. `estimate_table.html` — TanStack, full-featured, canonical
2. `project.html` inline estimate table — legacy, narrower column set, no grouping/sort/flywheel

### Decision
TanStack (`estimate_table.html`) is the canonical estimate surface. The legacy project-page inline estimate is deprecated. The Session 3 work (Pass 3) is migration and deprecation, not reconciliation.

Migration scope (to be executed in Pass 3, not now):
- Port Prod Rate, Labor Hrs, Labor $, Material $ columns into the TanStack API response as assembly-mode columns
- Port Assembly grouping behavior
- Remove the AgentX side tab and all AgentX references from UI and code
- Retire the legacy estimate table from `project.html` after migration lands
- Delete or archive `estimate.html` (currently orphaned)

### Rationale
- Feature ceiling was reached on the legacy table (no column reorder, no resize, no grouping, no flywheel fields)
- TanStack owns all the features needed for the full product vision
- Running two estimate UIs simultaneously creates user confusion and maintenance burden
- "Reconciliation framing implies symmetry that does not exist" — the two surfaces are not equal

### Consequences

**Positive:**
- Single estimate surface, single data path
- Full flywheel fields captured from day one on all writes
- AgentX panel retirement clears UI debt

**Negative:**
- Migration work required in Pass 3 (column schema merging, assembly grouping port)
- AgentX panel retirement requires careful removal to avoid breaking admin.html (which still includes it)

**Neutral:**
- `estimate.html` stays in the repo as a reference until Pass 3 explicitly deletes it

### Alternatives Considered
- **Keep both surfaces indefinitely:** rejected; creates two competing UIs with diverging features
- **Upgrade the legacy table instead:** rejected; hit complexity ceiling; drag-reorder + column state alone would be 400+ lines of brittle custom code

**Related Files:** `templates/estimate_table.html`, `static/js/estimate_table.js`, `templates/project.html` (legacy inline table), `templates/estimate.html` (orphaned), `templates/agentx_panel.html` (to be retired in Pass 3)

---

## ADR-025: Takeoff↔Estimate Link Semantics (One-Way + Traceability)

**Date:** 2026-04-13 (Pass 1 — Realignment)
**Status:** Accepted

### Context
Pass 3 will implement the direct link from Takeoff measurements to Estimate line items. Before building, the semantics must be defined explicitly to prevent a live bidirectional sync from being built accidentally.

### Decision
The link is **one-way with traceability**. Measurement is the source of truth. On link creation, measurement qty flows into `line_item.qty`. After that:
- `line_item.qty` can diverge (waste factor, rounding, estimator judgment)
- Editing `line_item.qty` does **not** write back to the measurement
- The UI surfaces divergence — the estimator can see when the grid no longer matches the drawing

### Rationale
- Preserves estimator judgment: the drawing says 1,000 LF, but the estimator knows to add 10% waste; the line item should say 1,100 LF
- Prevents silent data corruption: a bidirectional bind means a typo in the grid could corrupt the takeoff record
- Traceability is more valuable than automation: the estimator wants to know "this came from my takeoff" and also "I deliberately changed this number"

### Consequences

**Positive:**
- Clean audit trail: measurement = drawing truth, line_item = priced truth
- Estimator judgment is preserved and visible
- No risk of a grid edit silently corrupting takeoff data

**Negative:**
- UI must surface divergence clearly (divergence indicator on line_item rows that are linked but have been manually overridden)
- Slightly more implementation work than a simple bidirectional bind

**Neutral:**
- Divergence indicators are Pass 3 UI work, not Pass 1

### Alternatives Considered
- **Live bidirectional sync:** rejected; silently overwrites estimator judgment; risks data corruption on typo
- **Lock line_item qty after link:** rejected; removes estimator's ability to apply waste factors, conversions, or judgment adjustments

**Related Files:** `app.py` (LineItem model, POST /api/projects/<id>/line_items), `routes_takeoff.py` (measurement routes)

---

## ADR-026: Flywheel Fields on TakeoffMeasurement

**Date:** 2026-04-13 (Pass 1 — Realignment)
**Status:** Accepted (Deferred to Pass 3 migration)

### Context
Flywheel fields (`ai_generated`, `estimator_action`, `edit_delta`) are live on `LineItem` as of Session 22. `TakeoffMeasurement` currently has none of these fields. Per NORTHSTAR.md and TALLY_VISION.md, every measurement is also flywheel data.

### Decision
Add `ai_generated` (Boolean), `estimator_action` (String: accepted/edited/rejected/ignored), and `edit_delta` (JSONB text) to `TakeoffMeasurement`. Add via `run_migrations()` in the Pass 3 migration session. Populate passively — no form fields asking the estimator to categorize their own work.

### Rationale
- Non-AI users still contribute clean ground truth: a human-drawn polygon at the correct scale with no AI assistance is possibly the highest-quality flywheel data point
- Measurement-level data enriches the flywheel: which trade, which drawing type, scale used, edits from initial to final, whether AI assisted
- Collecting from day one is essential: retroactive flywheel collection is impossible; sparse early data is worse than consistent data
- Passive capture only: the estimator should never see these fields in the UI; they accumulate invisibly

### Consequences

**Positive:**
- Takeoff and Estimate flywheel data align on the same schema
- Non-AI users become contributors to the cost intelligence dataset, not just AI users
- Foundation for future measurement-accuracy analysis (did the estimator edit their polygon significantly before committing?)

**Negative:**
- Small schema migration required (3 new nullable columns on `takeoff_measurements`)
- Populating `edit_delta` requires comparing pre- and post-edit measurement points (modest implementation work)

**Neutral:**
- Fields are nullable with sensible defaults; existing records are unaffected

### Alternatives Considered
- **Only track AI-assisted measurements:** rejected; eliminates the non-AI ground-truth signal, which is cleaner than AI-assisted estimates
- **Track at the TakeoffItem level instead:** rejected; item-level is too coarse; measurement-level captures the geometry edit history

**Related Files:** `app.py` (TakeoffMeasurement model), `routes_takeoff.py` (measurement POST/DELETE routes), `run_migrations()` in `app.py`

---

## ADR-027: Tally Hooks Designed In Pass 3, Intelligence Wired in Pass 4

**Date:** 2026-04-13 (Pass 1 — Realignment)
**Status:** Accepted

### Context
Tally intelligence (Passive scope gap detection, Reactive Q&A, Generative line item creation) requires entry points on every product surface. Building the intelligence first and retrofitting the UI hooks later is the wrong order — it produces awkward UI that was never designed for the feature.

### Decision
**Pass 3** places stub Tally hooks on both the Takeoff and Estimate surfaces — visible UI elements that have the correct position, label, and interaction pattern, but call a stub backend or show a "Coming soon" state. **Pass 4** wires the actual intelligence layer behind the hooks.

Stub hooks to be designed and placed in Pass 3:

**Takeoff surface:**
- "Verify this scale" action next to the scale tool — calls stub, eventually Tally reviews scale against drawing context
- Passive badge when a drawing has been open N minutes with no measurements — stub, eventually Tally prompts contextual help
- Tally button on each measurement tool — stub, eventually surfaces contextual help for that measurement type

**Estimate surface:**
- Passive scope gap badges on rows/groups (framework is live; intelligence layer is the Pass 4 wire)
- Tally toolbar button for Reactive Q&A (currently wired to `href="#"` in the Tally footer banner)
- Generative mode entry point — explicit action button, never auto-triggered

### Rationale
- Prevents retrofit: surfaces built without Tally hooks are harder to integrate later without visual awkwardness
- Every surface needs Tally DNA from day one, even if it stubs
- Separating hook design (Pass 3) from intelligence wiring (Pass 4) allows each to be done cleanly without mixing UI work with AI backend work

### Consequences

**Positive:**
- Every surface is Tally-aware at launch, even before intelligence is live
- Pass 4 is a wiring exercise, not a UI design exercise — faster and cleaner
- User expectations are set: they see Tally entry points before the feature is live, reducing surprise when it activates

**Negative:**
- Stub hooks require care: a stub that looks broken erodes trust faster than no hook at all
- Two separate passes means Tally is partially visible but non-functional for a period

**Neutral:**
- "Coming soon" states are acceptable for stub hooks if they are intentional and polished

**Related Files:** `templates/takeoff/viewer.html`, `static/js/takeoff.js`, `templates/estimate_table.html`, `static/js/estimate_table.js`, `TALLY_VISION.md`

---

## 📝 ADR Template

Use this template for new decisions:

```markdown
## ADR-XXX: [Decision Title]

**Date:** YYYY-MM-DD (Session X)  
**Status:** Proposed | Accepted | Deprecated | Superseded

### Context
[What situation led to this decision? What problem are we solving?]

### Decision
[What are we doing?]

### Rationale
[Why did we choose this path? What factors influenced the decision?]

### Consequences

**Positive:**
- [Benefit]
- [Benefit]

**Negative:**
- [Trade-off]
- [Trade-off]

**Neutral:**
- [Side effect]

### Alternatives Considered
- **Option A:** [Why rejected]
- **Option B:** [Why rejected]

### Revisit
[Optional: When should we reconsider this decision?]

**Related Files:** [app.py, Templates/*.html, etc.]
```

---

## 🔍 How to Use This ADR

1. **Making a decision?** Add a new ADR entry (increment number)
2. **Changed your mind?** Mark old ADR as "Superseded" by ADR-XXX and create new one
3. **Onboarding teammate?** Share this file for context on "why we built it this way"
4. **Talking to investors?** Reference ADRs to show thoughtful decision-making

**What deserves an ADR:**
- Technology choices (frameworks, databases, APIs)
- Architecture patterns (multi-tenancy, data modeling)
- Product philosophy (AI optional vs mandatory)
- Third-party services (hosting, payments, email)
- Major feature directions (what to build vs cut)
- Security decisions (auth, CSRF, rate limiting)

**What doesn't need an ADR:**
- Minor UI tweaks
- Bug fixes
- Small refactors
- Temporary workarounds

---

## 📚 REFERENCES

- **Agent_MD.md** - Master reference, current state, session history
- **NORTHSTAR.md** - Product philosophy and design principles
- **CLAUDE.md** - Claude Code project instructions
- **FEATURE_ROADMAP.md** - Strategic roadmap and priorities
