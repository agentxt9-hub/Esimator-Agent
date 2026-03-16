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

**Current Status:** zenbid.io deployed but currently DOWN (blocked, support ticket open)

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
