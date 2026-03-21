# Estimator AgentX — Project README
### "What is everything, what does it do, and how does it all fit together"
**Last updated: Session 12 — 2026-03-15**

---

## First: The Big Picture in Plain English

Think of this project like a restaurant kitchen.

- **`app.py`** is the chef — it handles every request that comes in, does the work, and sends back a response
- **The Templates folder** is the dining room — it's what the customer (user) actually sees
- **PostgreSQL (the database)** is the walk-in fridge — all the data lives there permanently
- **The `.md` files** (CLAUDE.md, Agent_MD.md, etc.) are your recipe binders and operations manuals — they don't run anything, they're reference documents for you and Claude Code
- **The `.env` file** holds the secret keys (passwords, API keys) — like the safe in the back office
- **DigitalOcean** is the building itself — the server where everything runs live on the internet

---

## Part 1: File-by-File Inventory

### 🟢 ACTIVE — Core Application Files (touch these regularly)

---

#### `app.py` — The Heart of Everything
**What it is:** One big Python file (~3,450 lines) that is literally the entire backend of your app.

**What it does:**
- Defines every page your app has (called "routes") — like `/project/5` or `/login`
- Defines all your database tables (User, Project, Assembly, LineItem, etc.)
- Handles all the logic: saving data, calculating costs, calling the Claude AI API
- Runs the server

**Analogy:** If the app were a car, `app.py` is the engine, transmission, and steering system all in one.

**When Claude Code touches it:** Almost every feature build. New routes, new database columns, new AI features — all go here.

**⚠️ Risk level: HIGH** — This file does everything. A bad edit here breaks the whole app. Always ask Claude Code to "show me the change before applying it."

---

#### `Templates/` folder — All the Web Pages
**What it is:** Every HTML file the user sees in their browser. There are two "base" templates everything else inherits from, plus individual page templates.

**The two base templates (the foundation everything else builds on):**

| File | Theme | Used For |
|------|-------|----------|
| `app_base.html` | Dark (navy/blue) | Every page inside the app after login |
| `base.html` | Light (white) | Marketing site — landing, pricing, etc. |

**Think of them like:** Two different store layouts. Every app page uses the dark layout. Every public page uses the light layout.

**Individual page templates:**

| File | Route it serves | What the user sees |
|------|----------------|--------------------|
| `landing.html` | `/` | The public homepage / marketing page |
| `pricing.html` | `/pricing` | Pricing tiers |
| `login.html` | `/login` | Login form |
| `signup.html` | `/signup` | Sign up / create account |
| `forgot_password.html` | `/forgot-password` | "I forgot my password" form |
| `reset_password.html` | `/reset-password/<token>` | Set new password form |
| `index.html` | `/` (dashboard) | The dashboard after login — lists projects |
| `new_project.html` | `/project/new` | Create a new project form |
| `project.html` | `/project/<id>` | **THE main page** — inline estimate table, assemblies, line items, WBS |
| `estimate.html` | `/project/<id>/estimate` | Legacy full estimate view (still exists but mostly replaced by project.html) |
| `assembly_builder.html` | `/project/<id>/assembly/builder` | The wizard for building assemblies with measurements |
| `library.html` | `/library` | Company item library (reusable line items) |
| `templates.html` | `/templates` | Browse and load assembly templates |
| `production_rates.html` | `/production-rates` | View/edit production rate standards |
| `summary.html` | `/project/<id>/report` | Assembly summary report |
| `csi_report.html` | `/project/<id>/report/csi` | Cost grouped by CSI division |
| `proposal.html` | `/project/<id>/proposal` | Bid proposal (printable/exportable) |
| `settings.html` | `/settings` | Company settings, logo, properties |
| `profile.html` | `/profile` | User profile / change password |
| `admin.html` | `/admin` | Admin panel — manage companies and users |
| `nav.html` | (included in app_base) | The sidebar navigation |
| `agentx_panel.html` | (included in every app page) | The AI sliding panel on the right side |

**⚠️ Special rule for `agentx_panel.html`:** This file must never contain Jinja template tags (`{% %}` or `{{ }}`). It's a plain HTML/JS file. This caused a crash before — do not forget this rule.

---

#### `.env` — Secret Keys (Never Share This File)
**What it is:** A plain text file with sensitive credentials.

**What's in it:**
```
SECRET_KEY          ← Encrypts user sessions (like a master lock)
DATABASE_URL        ← How to connect to PostgreSQL
ANTHROPIC_API_KEY   ← Your Claude AI API key (costs money per use)
FLASK_DEBUG         ← true locally, MUST be false on the live server
MAIL_PASSWORD       ← SendGrid API key for sending password reset emails
```

**⚠️ This file is gitignored** — it never goes to GitHub. If someone else got this file, they could access your database and rack up AI API charges. Guard it.

---

### 🔵 DEPLOYMENT — Files That Run the Live Server

---

#### `Procfile`
**What it is:** One line that tells DigitalOcean how to start your app.
**Contents:** `web: gunicorn app:app`
**Analogy:** The ignition key. It just tells the server "start the engine."

#### `gunicorn_conf.py`
**What it is:** Configuration for Gunicorn (the production web server).
**What it does:** Runs database migrations and seeds data automatically every time the server starts. This means you never have to manually update the live database — it happens automatically on deploy.
**Analogy:** The car's startup checklist — check oil, check tire pressure — before the engine fully turns over.

#### `migration.sql`
**What it is:** A record of database structure changes (adding columns, etc.).
**What it does:** Not run directly — the migration logic lives in `app.py` in a function called `run_migrations()`. This `.sql` file is a reference/backup of those changes.
**When to update:** Any time Claude Code adds a new column to a database table, that change should also be reflected here.

#### `requirements.txt`
**What it is:** The list of Python packages your app depends on.
**What it does:** When you run `pip install -r requirements.txt`, Python installs everything the app needs to run.
**Analogy:** A grocery list. The app can't cook without these ingredients.
**When to update:** Any time Claude Code adds a new Python library to `app.py`.

#### `seed_csi.py`
**What it is:** A one-time script that populated the CSI division data in your database.
**⚠️ DO NOT RUN THIS AGAIN.** The data is already in the database. Running it again creates duplicates. This file exists as a reference only.

---

### 📋 DOCUMENTATION — Reference Files (For You and Claude Code)

These files don't run. They don't affect the app. They exist to keep you and Claude Code on the same page.

---

#### `CLAUDE.md` — Claude Code's Quick-Start Card
**Audience:** Claude Code reads this first at the start of every session.
**What's in it:** The absolute minimum Claude Code needs to know — how to run the app, the hard rules it must never break, active blockers, top priority gaps.
**Analogy:** The laminated card on the wall of a kitchen that says "allergens, emergency contacts, health code rules."
**Keep it:** Short, current, and focused on constraints. Point to Agent_MD.md for everything else.

#### `Agent_MD.md` — The Master Reference (27KB)
**Audience:** You and Claude Code. The most important documentation file.
**What's in it:** Everything — full architecture, all database models, every route, the AI panel details, UI rules, deployment steps, full roadmap, session history.
**Analogy:** The complete operations manual for the restaurant.
**Keep it:** Updated at the end of every session. When something changes in the app, it should change here too.

#### `NORTHSTAR.md` — The Why (17KB)
**Audience:** Primarily you. Strategy and philosophy.
**What's in it:** The product vision, the problem you're solving, the core principles (AI as optional, generational inclusivity, etc.), the long-term roadmap thinking.
**Analogy:** The founder's manifesto. Doesn't change often, but anchors every decision.
**When to reference:** When you're deciding whether a feature belongs in the product at all.

#### `DECISIONS.md` — Architecture Decision Log (17KB)
**Audience:** You and Claude Code. Historical record.
**What's in it:** Every major technical decision documented — why you switched from Ollama to Claude API, why Flask over Django, why PostgreSQL over SQLite, etc. Each entry has context, rationale, and consequences.
**Analogy:** The "why did we do it this way?" file. Prevents re-litigating old decisions.
**When to update:** Any time you make a significant technical choice that future-you might question.

#### `FEATURE_ROADMAP.md` — What's Next (9KB)
**Audience:** You. Product planning.
**What's in it:** Prioritized list of features — Critical / High / Medium / Future — with status, effort estimate, and GitHub issue links.
**Analogy:** The construction schedule. What's being built, in what order, and what's blocked.
**When to update:** At the start/end of each session, as features get completed or priorities shift.

#### `INTEGRATION_GUIDE.md` — One-Time Setup Record
**Audience:** Historical reference only.
**What's in it:** The step-by-step guide for integrating the marketing site into the app (done during Session 11c).
**Status:** ✅ Already completed. This file is a record of work that's done.
**Recommendation:** Move to `archive/` folder — it's no longer actionable.

---

### 🟡 SCRIPTS & AUTOMATION

#### `create-issues.sh`
**What it is:** A shell script that creates pre-written GitHub Issues automatically.
**What it does:** Runs `gh issue create` commands to populate your GitHub repo with bug reports and feature requests that were identified during development.
**How to use:** Run once from terminal: `bash create-issues.sh`
**Status:** May already have been run. Check your GitHub Issues before running again.

#### `scripts/` folder (visible in your file explorer)
**What's in it:** Likely helper scripts from development (the project files here don't show contents). Worth opening in VS Code to see what's there — if it's empty or has old one-off scripts, it can be archived.

---

### 🗄️ ARCHIVE & BACKUP

#### `archive/` folder
For files that are done/historical but you don't want to delete. Suggested candidates:
- `INTEGRATION_GUIDE.md` (work is done)
- `routes.py` (see below)

#### `backup/` folder
Snapshots of `app.py` and templates before major changes. Good habit — keep it.

#### `routes.py` — ⚠️ STALE FILE
**What it is:** An old separate routes file from an earlier session that was meant to be merged into `app.py`.
**Current status:** All routes now live in `app.py`. This file is outdated — it references an older pre-Flask-Login auth system.
**Recommendation:** Move to `archive/` immediately. If Claude Code ever reads this file, it will get confused about how auth works.

---

### 📊 OTHER FILES

#### `Zenbid_Market_Analysis_v3.xlsx`
Your market research spreadsheet. Not part of the app — just lives here for convenience.
Consider moving to a `business/` or `research/` folder to keep it separate from code.

#### `_env`, `_env.example`, `_gitignore`
These have underscore prefixes because they represent the `.env`, `.env.example`, and `.gitignore` files (which start with a dot and are hidden on Mac/Linux). In the project here they're prefixed with underscore so they're visible. Your actual project folder has the real dotfiles.

---

## Part 2: How the Files Flow Together

### The Request-Response Flow (What happens when a user loads a page)

```
User opens browser → types zenbid.io/project/5
        ↓
DigitalOcean server receives the request
        ↓
Nginx (web server) forwards it to Gunicorn
        ↓
Gunicorn runs app.py
        ↓
app.py finds the matching route: def project_detail(project_id=5)
        ↓
app.py queries PostgreSQL: "give me project #5 and all its assemblies/line items"
        ↓
app.py renders project.html, injecting the data
        ↓
project.html builds the page using app_base.html as its frame
        ↓
The HTML page is sent back to the user's browser
        ↓
User sees their estimate table
```

---

### The AI Flow (What happens when a user asks AgentX something)

```
User types a question in the AgentX panel → hits Send
        ↓
agentx_panel.html sends a fetch() POST to /ai/chat
        ↓
app.py receives it, builds context (project data + line items + production rates)
        ↓
app.py calls the Anthropic Claude API with that context
        ↓
Claude API responds (costs ~$0.003)
        ↓
app.py sends the response back as JSON
        ↓
agentx_panel.html displays it in the chat window
        ↓
If Claude proposed estimate changes → user clicks Apply
        ↓
agentx_panel.html sends another fetch() to /ai/apply
        ↓
app.py writes new line items to PostgreSQL
        ↓
The estimate table refreshes with new data
```

---

### The Data Hierarchy (How your data is structured)

```
Company (tenant — one per construction firm)
  └── Users (admin / estimator / viewer)
  └── Projects (one estimate job)
        └── Assemblies (a group of related work, e.g. "Exterior Wall")
              └── Line Items (individual cost rows, e.g. "Framing lumber")
                    └── WBS Tags (location/phase labels, e.g. "Level 1 / Phase 2")
        └── Library Items (reusable item definitions, scoped to company)
  └── GlobalProperties (custom trade/type/sector lists)
  └── CompanyProfile (name, logo, address)

ProductionRateStandards (global — not company-scoped)
CSI Level 1 / Level 2 (global — division codes, never edited)
```

**Key rule:** Every piece of data is isolated by `company_id`. Company A can never see Company B's projects, even if they're in the same database. This is called multi-tenancy.

---

### The Cost Calculation Flow (How a line item gets its dollar value)

```
User enters quantity (e.g., 500 SF of drywall)
        ↓
app.py runs calculate_item_costs()
        ↓
IF item has a production rate:
   labor_hours = quantity ÷ production_rate
   labor_cost = hours × labor_cost_per_hour
ELSE:
   labor_cost = quantity × labor_cost_per_unit
        ↓
material_cost = quantity × material_cost_per_unit
equipment_cost = quantity × equipment_cost_per_unit
        ↓
total = material + labor + equipment
        ↓
Saved to PostgreSQL
        ↓
project.html fetches /project/<id>/summary → updates the totals bar live
```

**⚠️ Important:** The JavaScript in `estimate.html` (function `recalcItem()`) mirrors this same math on the frontend so the numbers update instantly before the server confirms. Both must always be kept in sync.

---

## Part 3: Folder Structure — What Should Be Where

### Current State vs. Recommended

```
Estimator Agent/                    CURRENT STATE
├── .github/                        ← GitHub Actions config (fine here)
├── __pycache__/                    ← Auto-generated Python cache (never touch)
├── archive/                        ← Good — use it more
├── backup/                         ← Good — keep snapshots here
├── deploy/                         ← Good — deployment scripts
├── scripts/                        ← Review contents; archive if empty/stale
├── static/                         ← CSS, images, uploaded logos (fine here)
├── Templates/                      ← All HTML files (fine here)
├── app.py                          ← Core app (fine at root)
├── CLAUDE.md                       ← ✅ Fine at root (Claude Code reads it here)
├── Agent_MD.md                     ← ✅ Fine at root
├── NORTHSTAR.md                    ← ✅ Fine at root
├── DECISIONS.md                    ← ✅ Fine at root
├── FEATURE_ROADMAP.md              ← ✅ Fine at root
├── INTEGRATION_GUIDE.md            ← ⚠️ Move to archive/ (work is done)
├── routes.py                       ← 🚨 Move to archive/ (stale — confuses Claude Code)
├── create-issues.sh                ← ⚠️ Move to scripts/ after confirming it's been run
├── migration.sql                   ← ✅ Fine at root
├── seed_csi.py                     ← ⚠️ Consider moving to archive/ (already run)
├── gunicorn_conf.py                ← ✅ Fine at root
├── requirements.txt                ← ✅ Fine at root
├── Procfile                        ← ✅ Fine at root
├── .env                            ← ✅ Fine at root (gitignored)
├── .env.example                    ← ✅ Fine at root
├── .gitignore                      ← ✅ Fine at root
└── Zenbid_Market_Analysis_v3.xlsx  ← ⚠️ Move to a business/ or research/ folder
```

### Three Actions to Take Right Now

**Action 1 — Move to `archive/`:**
- `routes.py` (stale auth system, will confuse Claude Code)
- `INTEGRATION_GUIDE.md` (completed work, no longer actionable)
- `seed_csi.py` (already run, dangerous to re-run)

**Action 2 — Move to `scripts/`:**
- `create-issues.sh` (once you confirm it's been run)

**Action 3 — Create a `business/` folder:**
- Move `Zenbid_Market_Analysis_v3.xlsx` there
- This keeps business/research files visually separate from code

---

## Part 4: The "If It's Broken, Start Here" Diagnosis Guide

### App won't start at all
1. Is PostgreSQL running? Check with: `pg_ctl status`
2. Is `.env` file present with all required keys?
3. Check `app.py` for a Python syntax error (red underline in VS Code)

### Page loads but shows an error
1. Look at the terminal where `python app.py` is running — the error is printed there
2. The error message will name a file and line number — that's where the problem is
3. Common cause: a recent edit to `app.py` introduced a bug

### AI panel isn't responding
1. Is `ANTHROPIC_API_KEY` in `.env`?
2. Are you over the rate limit? (20 requests/minute max)
3. Check the browser console (F12 → Console tab) for a red error

### Data isn't saving
1. Is PostgreSQL running?
2. Did you add a new column without adding it to `run_migrations()` in `app.py`?
3. Is CSRF protection blocking the POST? Check the browser console for a 400 error

### Styles look wrong / colors are off
1. Search the changed template for hardcoded hex colors (like `#1a1a2e`) — replace with CSS variables
2. Make sure the template extends the right base: `{% extends 'app_base.html' %}` for app pages, `{% extends 'base.html' %}` for marketing pages

---

## Part 5: The One-Page Cheat Sheet

```
┌─────────────────────────────────────────────────────────────┐
│                    WHAT DOES WHAT                           │
├──────────────────────┬──────────────────────────────────────┤
│ app.py               │ The entire backend. Routes, models,  │
│                      │ logic, AI calls. Don't edit blindly. │
├──────────────────────┼──────────────────────────────────────┤
│ Templates/*.html     │ What users see. Each file = one page.│
├──────────────────────┼──────────────────────────────────────┤
│ app_base.html        │ Dark theme shell. All app pages      │
│                      │ extend this.                         │
├──────────────────────┼──────────────────────────────────────┤
│ base.html            │ Light theme shell. Marketing pages   │
│                      │ extend this.                         │
├──────────────────────┼──────────────────────────────────────┤
│ agentx_panel.html    │ The AI sliding panel. No Jinja tags. │
├──────────────────────┼──────────────────────────────────────┤
│ .env                 │ Secret keys. Never share or commit.  │
├──────────────────────┼──────────────────────────────────────┤
│ CLAUDE.md            │ Claude Code's quick-start card.      │
├──────────────────────┼──────────────────────────────────────┤
│ Agent_MD.md          │ Full reference. Source of truth.     │
├──────────────────────┼──────────────────────────────────────┤
│ NORTHSTAR.md         │ Product vision and philosophy.       │
├──────────────────────┼──────────────────────────────────────┤
│ DECISIONS.md         │ Why we built it this way.            │
├──────────────────────┼──────────────────────────────────────┤
│ FEATURE_ROADMAP.md   │ What's next and in what order.       │
├──────────────────────┼──────────────────────────────────────┤
│ requirements.txt     │ Python packages needed to run.       │
├──────────────────────┼──────────────────────────────────────┤
│ Procfile             │ Tells server how to start the app.   │
├──────────────────────┼──────────────────────────────────────┤
│ gunicorn_conf.py     │ Runs DB migrations on server start.  │
├──────────────────────┼──────────────────────────────────────┤
│ routes.py            │ 🚨 STALE — move to archive/          │
├──────────────────────┼──────────────────────────────────────┤
│ seed_csi.py          │ ⚠️ Already run — move to archive/    │
└──────────────────────┴──────────────────────────────────────┘
```
