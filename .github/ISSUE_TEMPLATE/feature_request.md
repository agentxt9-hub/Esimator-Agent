---
name: Feature Request
about: Suggest a new feature or enhancement for Zenbid
title: '[FEATURE] '
labels: enhancement
assignees: ''

---

## 💡 Feature Description
<!-- What do you want to build? -->

## 🎯 User Story
<!-- Who is this for and why do they need it? -->
**As a** [admin / estimator / viewer / company owner]  
**I want** [goal/desire]  
**So that** [benefit/value]

## ✨ Proposed Solution
<!-- How should this work? What's your vision? -->

## 🔄 User Flow
<!-- Optional: Describe the step-by-step interaction -->
1. User navigates to...
2. User clicks/enters...
3. System does...
4. Result displayed...

## 🎨 Design/UI Notes
<!-- Any specific design requirements or mockups? -->
- Fits in existing page: [project.html / index.html / settings.html / etc.]
- New page needed?
- Modal/panel/inline?
- Dark theme compatible?

## 🔗 Dependencies
<!-- Does this require other work to be done first? -->
- [ ] Database schema changes needed
- [ ] New models/tables required
- [ ] AI integration (Claude API)
- [ ] Email/external service integration
- [ ] Depends on: [other feature/issue]

## 📊 Priority
<!-- How important is this? Reference Agent_MD.md roadmap -->
- [ ] **CRITICAL** - Must resolve before beta users (Privacy/Terms, Security)
- [ ] **HIGH** - MVP for paying users (Billing, PDF export, Onboarding)
- [ ] **MEDIUM** - Core SaaS features (Audit logging, Mobile responsive)
- [ ] **FUTURE** - Post-launch (Takeoff import, Public API, Streaming AI)

## ⚖️ Effort Estimate
<!-- How big is this feature? -->
- [ ] **Small** - 1-2 hours (config change, minor UI tweak)
- [ ] **Medium** - Half day (new route + template + basic logic)
- [ ] **Large** - 1-2 full days (complex feature with DB changes)
- [ ] **XL** - Multiple days (major feature like WBS overhaul)

## 🤔 Alternatives Considered
<!-- Are there other ways to solve this problem? -->

## 🎯 Related Components
<!-- Which parts of the codebase will this touch? -->
- **Models:** [e.g., Project, Assembly, LineItem, User, WBSProperty]
- **Routes:** [e.g., /project/<id>, /ai/chat, /settings]
- **Templates:** [e.g., project.html, agentx_panel.html, settings.html]
- **AI Features:** [AgentX panel, Scope Gap, Rate Lookup, Assembly Auto-Builder]

## 📝 Technical Notes
<!-- For implementer reference -->
- Requires migration? [Yes/No]
- Multi-tenant safe? [Must respect company_id isolation]
- CSRF protected? [All forms need csrf_token]
- Rate limited? [AI routes already rate-limited]

## ✅ Acceptance Criteria
<!-- How will we know this is done? -->
- [ ] Feature works as described
- [ ] Tested in both admin and estimator roles
- [ ] Multi-tenant data isolation verified
- [ ] Mobile-responsive (if UI change)
- [ ] No console errors
- [ ] Documented in Agent_MD.md if architectural change

## 🔮 Future Enhancements
<!-- Optional: What could we add later to make this even better? -->
