# Feature Roadmap - Zenbid

> **Purpose:** High-level strategic planning and feature prioritization.  
> **Last Updated:** Session 12 (2026-03-15)  
> **Source:** Agent_MD.md Strategic Roadmap section

> **Note:** Bugs and QA tasks are tracked in GitHub Issues. This file is for features and strategic planning only.

---

## 🚨 CURRENT BLOCKER

**DigitalOcean / zenbid.io is unreachable**
- Domain is down, droplet access locked
- Support ticket open with DigitalOcean
- All Session 12 work code-complete locally but not deployed
- No new deployments possible until resolved

**GitHub Issue:** #[create issue with label: bug, critical, deployment]

---

## 🔥 CRITICAL PRIORITY
**Must Resolve Before Beta Users**

| Feature | Status | GitHub Issue | Notes |
|---------|--------|--------------|-------|
| **Password Reset** | ✅ Done | - | Session 12; needs MAIL_PASSWORD on server to send emails |
| **CSRF Protection** | ✅ Done | - | Session 12; all forms + fetch monkey-patch |
| **Rate Limiting** | ✅ Done | - | Session 12; AI routes + login; in-memory (fine for now) |
| **Privacy Policy & Terms** | ❌ Open | #[create] | Placeholder routes return plain text; need real legal docs |
| **ANTHROPIC_API_KEY on server** | ⚠️ Config | - | Needs verification after DigitalOcean is back up |

---

## 🎯 HIGH PRIORITY
**MVP for Paying Users - Ship Within 4 Weeks**

| Feature | Status | Effort | GitHub Issue | Notes |
|---------|--------|--------|--------------|-------|
| **Edit Project Fields UI** | ⚠️ Partial | Small | #[create] | Route exists (`POST /project/<id>/update`); Edit Project modal missing city/state/zip/type/sector fields |
| **Welcome Email on Signup** | ❌ Open | Small | #[create] | Flask-Mail wired; just add `mail.send()` in `/signup` route |
| **Contact Page** | ❌ Open | Small | #[create] | Currently placeholder |
| **Viewer Role Enforcement** | ❌ Open | Medium | #[create] | Role checked only for `/admin`; viewers can currently write data |
| **Proposal PDF Export** | ❌ Open | Large | #[create] | Print-to-PDF works; server-side PDF needs weasyprint or headless Chrome |
| **Proposal Route Isolation** | ❌ Open | Small | #[create] | `GET /project/<id>/proposal` uses bare `Project.query.get()` not `get_project_or_403()` - security issue |
| **Subscription / Billing** | ❌ Open | XL | #[create] | Stripe Checkout + webhook integration |

---

## 📊 MEDIUM PRIORITY
**Core SaaS Features - Post-MVP**

| Feature | Effort | GitHub Issue | Notes |
|---------|--------|--------------|-------|
| **Free Trial Gate** | Medium | #[create] | Limit projects/features for new signups |
| **In-App Onboarding** | Large | #[create] | Empty state CTAs, first-time user guide |
| **About / Blog / Careers Pages** | Small | #[create] | Footer links currently return plain text |
| **Delete Buttons in Estimate Table** | Small | #[create] | Currently must go to project page to delete line items |
| **Audit Logging** | Large | #[create] | Enterprise compliance, debug support, track all CRUD operations |
| **Mobile-Responsive Estimate View** | Large | #[create] | Currently desktop-only; need tablet/mobile breakpoints |

---

## 🔮 FUTURE PRIORITY
**Post-Launch - Innovation & Scale**

| Feature | Category | Notes |
|---------|----------|-------|
| **Subcontractor Bid Requests** | Workflow | Send line items to subs, receive quotes, compare in-app |
| **Takeoff File Import** | AI/Automation | PDF/DWG → auto-populate assemblies via AI parsing |
| **Public API** | Integration | Webhook / REST for firm integrations, Procore/Autodesk sync |
| **Streaming AI Responses** | Performance | Token-by-token output via SSE (Server-Sent Events) |
| **AgentX Conversation Memory** | AI Enhancement | `axHistory[]` array; multi-turn context across sessions |
| **Quick-Action Chips** | UX | Zero-backend prompt shortcuts in AgentX panel |
| **Bulk Import for Production Rates** | Data | CSV upload to populate production_rate_standards table |
| **Regional Cost Intelligence** | Strategic | Use accumulated estimate data for regional pricing insights |

---

## ✅ SHIPPED (Recent Sessions)

### Session 12 (2026-03-15)
- ✅ CSRF protection (flask-wtf, meta tag, fetch monkey-patch)
- ✅ Rate limiting (flask-limiter on login + 5 AI routes)
- ✅ Password reset via email (flask-mail, /forgot-password, /reset-password/<token>)

### Session 11c (2026-03-14)
- ✅ Marketing site + dark theme re-skin (CSS vars)
- ✅ Production deployment to zenbid.io (Gunicorn+Nginx+systemd)
- ✅ Login via email support
- ✅ /signup route

### Session 11b (2026-03-14)
- ✅ WBS value inline editing + drag-to-reorder
- ✅ AI rate lookup panel
- ✅ Validate rate feature (right-click context menu)
- ✅ requirements.txt generated

### Session 11 (2026-03-13)
- ✅ project.html inline table overhaul
- ✅ Inline cell editing
- ✅ Multi-select Group By
- ✅ WBS in Edit Project modal
- ✅ Location 1/2/3 (renamed from Area)

### Session 10 (2026-03-12)
- ✅ AgentX extracted to partial (agentx_panel.html)
- ✅ Context-aware mode init (Estimate mode only on /project/<id>)
- ✅ Fixed Jinja recursion bug

### Session 9 (2026-03-12)
- ✅ AgentX AI panel (Claude API integration)
- ✅ /ai/chat + /ai/apply routes
- ✅ Voice input (Web Speech API)
- ✅ Removed Ollama dependency

### Session 8 (2026-03-11)
- ✅ Bid Proposal template
- ✅ Production Rate Standards CRUD + lookup modal

### Session 7 (2026-03-11)
- ✅ Authentication + Multi-Tenancy (Flask-Login)
- ✅ Company/User models
- ✅ Full data isolation by company_id

---

## 🗑️ NOT BUILDING

### Real-Time Collaboration (Google Docs style)
- **Why Rejected:** Too complex for MVP; most estimators work solo
- **Revisit:** If users explicitly request it after launch

### Mobile App First
- **Why Rejected:** Web-first faster to ship; field estimating is niche use case
- **Revisit:** After web traction proven (500+ active users)

### Offline-First / Local Ollama
- **Why Rejected:** Claude API vastly superior (speed + quality)
- **Decision Date:** Session 9 (2026-03-12)
- **Reference:** Agent_MD.md Session History, ADR in DECISIONS.md

---

## 📊 SUCCESS METRICS (Post-Launch)

**By End of Q2 2025:**
- [ ] 50 active users
- [ ] 500 estimates created
- [ ] DigitalOcean deployment stable
- [ ] All CRITICAL priority items resolved
- [ ] All HIGH priority items shipped

**By End of 2025:**
- [ ] 500 active users
- [ ] 5,000 estimates (training data for future ML features)
- [ ] Regional pricing intelligence beta
- [ ] Revenue: $5K MRR
- [ ] Cost Intelligence Database concept validated

---

## 🔄 WORKFLOW

### Weekly Planning (Monday)
1. Review this roadmap
2. Create GitHub issues for sprint features
3. Add labels: `enhancement` + priority label + feature area
4. Assign to milestone if using milestones

### Feature Kickoff
1. Create GitHub issue (use Feature Request template)
2. Reference issue in Claude Code prompt
3. Build incrementally, test locally
4. Deploy when ready

### Feature Complete
1. Test thoroughly (create QA issue if needed)
2. Deploy to production
3. Close GitHub issue
4. Move to SHIPPED section in this file
5. Update Agent_MD.md if architectural change

---

## 💡 DECISION CRITERIA

**CRITICAL Priority:**
- Blocks beta launch
- Security/legal requirement
- Data integrity risk

**HIGH Priority:**
- Needed for first 50 paying customers
- High ROI / low effort
- Competitive parity feature

**MEDIUM Priority:**
- Nice to have for growth
- Improves retention
- Standard SaaS feature

**FUTURE Priority:**
- Innovation / differentiation
- Needs validation first
- Resource-intensive

---

## 🎯 NORTH STAR GOALS

From NORTHSTAR.md philosophy:

1. **Flexibility Over Dogma** - Tool adapts to user's mental model
2. **AI as Optional Augmentation** - Never mandatory, always available
3. **Predictable Output, Unpredictable Process** - Professional reports regardless of workflow
4. **Institutional Knowledge at Your Fingertips** - Level the playing field for junior estimators
5. **Generational Inclusivity** - Works for 60yo Excel estimator AND 28yo AI-native

**The Test:**
> *Could a rigid (Excel-minded) estimator use this comfortably? Could a flexible (AI-native) estimator use this expressively?* If either answer is "no," reconsider the design.

---

## 📖 REFERENCES

- **Agent_MD.md** - Master reference document, current state, session history
- **NORTHSTAR.md** - Product philosophy and architectural principles
- **CLAUDE.md** - Claude Code project instructions
- **GitHub Issues** - Individual features, bugs, and QA tasks
- **DECISIONS.md** - Architecture Decision Record (ADR)
