# Feature Roadmap — Zenbid

> **Purpose:** Strategic planning and feature prioritization.
> **Last Updated:** 2026-04-13 (Pass 1 — Realignment)
> **Source of architectural decisions:** `DECISIONS.md`
> **Bugs and QA tasks:** tracked in GitHub Issues

---

## The Four-Pass Sequence

The next four sessions follow a deliberate sequence. Each pass has a clear scope that feeds the next.

| Pass | Session | Scope | Status |
|------|---------|-------|--------|
| **Pass 1** | Current | Realignment — docs only. Contradiction report + doc updates to match repo reality and encode product direction. No code. | ✅ In progress |
| **Pass 2** | Next | 90-Second Confidence Study — scoped Playwright/manual walkthrough of zzTakeoff, produce a punch list for the upload→scale→first-measurement flow only. Diverge after that. No code changes. | ⏳ Queued |
| **Pass 3** | Session 23+ | Bridge + Table Migration — combined. TanStack becomes canonical, legacy table retired, AgentX purged. Measurement→line_item link implemented with one-way+traceability semantics (ADR-025). Dual-costing expandable row designed and built (ADR-022). Tally stub hooks placed on both surfaces (ADR-027). Flywheel fields added to TakeoffMeasurement (ADR-026). | ⏳ Queued |
| **Pass 4** | Session 24+ | Tally Intelligence Wiring — backend for Passive/Reactive/Generative modes against the hooks Pass 3 placed. | ⏳ Queued |

---

## Pass 3 — Bridge + Table Migration (Detailed Scope)

This is the most complex session. Scope is fixed here so it does not grow.

### TanStack Migration
- [ ] Port Prod Rate, Labor Hrs, Labor $, Material $ columns into TanStack API response as assembly-mode columns
- [ ] Port Assembly grouping behavior from legacy table
- [ ] Retire legacy inline estimate table from `project.html`
- [ ] Delete or archive orphaned `estimate.html`

### AgentX Retirement
- [ ] Remove AgentX side tab button and panel from all live templates
- [ ] Remove or rename `agentx_panel.html`
- [ ] Keep `/ai/chat`, `/ai/apply` etc. routes but remove the UI entry point that calls them "AgentX"

### Takeoff → Estimate Bridge
- [ ] `POST /api/projects/<id>/line_items` — accept measurement_id parameter to create a linked line item
- [ ] Store measurement linkage on LineItem (new FK column: `measurement_id` nullable)
- [ ] Divergence tracking: detect when `line_item.qty ≠ measurement.calculated_value` and surface in UI
- [ ] Flywheel fields added to TakeoffMeasurement (`ai_generated`, `estimator_action`, `edit_delta`)

### Dual Costing Expandable Row
- [ ] Design spike: expandable row interaction pattern (chevron → reveal assembly build-up fields)
- [ ] Implement in `estimate_table.js`

### Tally Stub Hooks
- [ ] Estimate: wire Reactive Q&A stub panel to the Tally footer "Review All" button
- [ ] Estimate: add Generative mode "Ask Tally" explicit entry point button
- [ ] Takeoff: "Verify scale" stub button in status bar
- [ ] Takeoff: Tally icon on measurement toolbar tools

---

## 🚨 CRITICAL — Must Resolve Before Beta Users

| Feature | Status | Notes |
|---------|--------|-------|
| **Privacy Policy page** | ❌ Open | `/privacy` returns placeholder text — need real legal page |
| **Terms of Service page** | ❌ Open | `/terms` returns placeholder text — need real legal page |
| **ANTHROPIC_API_KEY startup validation** | ❌ Open | No startup check; app starts silently with missing key |
| **SSL certificate** | ⚠️ Unconfirmed | Site operational but HTTPS status not confirmed post-deployment |

---

## 🎯 HIGH PRIORITY — Pre-First-Paying-User

| Feature | Status | Effort | Notes |
|---------|--------|--------|-------|
| **Edit Project Fields UI** | ⚠️ Partial | Small | Route exists; modal missing city/state/zip/type/sector fields |
| **Welcome Email on Signup** | ❌ Open | Small | Flask-Mail wired; just needs `mail.send()` in `/signup` |
| **Proposal Route Isolation** | ❌ Open | Small | `GET /project/<id>/proposal` uses bare `Project.query.get_or_404()` — security gap |
| **Viewer Role Enforcement** | ❌ Open | Medium | Role checked only for `/admin`; viewers can currently write data |
| **Contact Page** | ❌ Open | Small | Placeholder |

---

## ✅ RECENTLY COMPLETED

| Feature | Session | Notes |
|---------|---------|-------|
| **Estimate Table — TanStack Table v8** | 22 | Full grid: inline edit, grouping, sort, column reorder/resize/show-hide, CSV+Excel export, AI badges, Tally footer, Add Item panel, flywheel fields |
| **Takeoff — Drawing Tools (Session 2)** | 21 | Scale, linear, area, count, ortho, properties panel, totals; 99/99 tests |
| **Takeoff — Foundation + Konva migration** | 18–19 | PDF upload, 3-layer canvas, multi-page, thumbnails; Blueprint architecture |
| **Password Reset via Email** | 12 | flask-mail, /forgot-password, /reset-password |
| **CSRF + Rate Limiting** | 12 | flask-wtf, fetch monkey-patch, flask-limiter |
| **Auth + Multi-Tenancy** | 7 | Flask-Login, Company/User models, company_id isolation |
| **Waitlist Flow + Micro-Survey** | 15–16 | WaitlistEntry + WaitlistSurvey models, n8n webhook integration |
| **Marketing Site + Production Deploy** | 11c–13 | zenbid.io live, Gunicorn+Nginx+systemd, SendGrid, Concept C logo |

---

## 📊 MEDIUM PRIORITY — Post-MVP

| Feature | Effort | Notes |
|---------|--------|-------|
| **Subscription / Billing** | XL | Stripe Checkout + webhook |
| **Free Trial Gate** | Medium | Limit projects/features for new signups |
| **In-App Onboarding** | Large | Empty state CTAs, first-time user guide |
| **Proposal PDF Export** | Large | Print-to-PDF works; server-side needs weasyprint or headless Chrome |
| **Audit Logging** | Large | Enterprise compliance; `edit_delta` flywheel field already captured |
| **Mobile-Responsive Estimate View** | Large | Currently desktop-only |
| **About / Blog / Careers / Contact Pages** | Small | Footer links currently plain text |
| **Delete Button in Estimate Grid** | Small | Soft-delete API built (Session 22); needs UI button |

---

## 🔮 LATER — Post-Launch / Innovation

These items are real but do not fit in the four-pass sequence. Labeled honestly.

| Feature | Notes |
|---------|-------|
| **Tally Reactive Mode** | On-demand Q&A and division summaries — intelligence wired in Pass 4 |
| **Tally Generative Mode** | Natural-language line item creation — intelligence wired in Pass 4 |
| **Regional Cost Intelligence** | Flywheel data → regional pricing benchmarks; requires sufficient data volume |
| **AI Conversation Memory** | Multi-turn context across sessions (currently stateless per request) |
| **Subcontractor Bid Requests** | Send line items to subs, receive quotes, compare in-app |
| **Public API** | REST/webhook for firm integrations (Procore, Autodesk) |
| **Streaming AI Responses** | Token-by-token output via SSE |
| **Bulk Import for Production Rates** | CSV upload to populate `production_rate_standards` table |
| **Multi-Page Scale Inheritance** | Copy scale from page 1 to all pages in a plan set |
| **Snap-to-Vertex** | Functional vertex snapping (currently visual toggle only) |
| **Undo/Redo for Drawing Steps** | Ctrl+Z / Ctrl+Y on the Takeoff canvas |
| **Zoom-to-Measurement** | Click item in sidebar → canvas zooms to first measurement |
| **Cost Intelligence Fine-Tuned Model** | LLM fine-tuned on proprietary flywheel dataset; premium tier |
| **MFA for App Users** | TOTP for admin role; required for enterprise sales |
| **Account Deletion Route** | `/account/delete` for GDPR compliance |

---

## 🗑️ NOT BUILDING

| Feature | Why Rejected |
|---------|-------------|
| **Real-Time Collaboration (Google Docs style)** | Too complex for MVP; most estimators work solo |
| **Mobile App First** | Web-first faster to ship; field estimating is niche |
| **Offline-First / Local Ollama** | Claude API superior (speed + quality); ADR-001 |

---

## 📊 SUCCESS METRICS

**Pre-revenue (current focus):**
- [ ] All CRITICAL security items resolved
- [ ] First paying customer onboarded
- [ ] Four-pass sequence complete

**Post-launch:**
- [ ] 50 active users
- [ ] 500 estimates created
- [ ] Regional pricing intelligence beta
- [ ] $5K MRR

---

## 📖 REFERENCES

- `Agent_MD.md` — Master reference, current state, session history
- `NORTHSTAR.md` — Product philosophy and product principles
- `DECISIONS.md` — Architecture Decision Records
- `TALLY_VISION.md` — Tally AI layer specification
- `SECURITY.md` — Security framework and gap backlog
- `CLAUDE.md` — Claude Code project instructions
