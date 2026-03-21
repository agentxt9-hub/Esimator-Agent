# Agentic GitHub Issue Management for Zenbid

Automated and semi-automated tools for managing GitHub issues via Claude Code.

---

## 🚀 Quick Start

### Level 1: Generate Commands (Manual Review)

**Preview what issues would be created:**

```bash
python scripts/generate-issue-commands.py
```

**Output:** PowerShell commands ready to copy/paste

---

### Level 2: Auto-Create Issues (One Command)

**Dry run (preview only):**

```bash
python scripts/auto-create-issues.py --dry-run
```

**Create all open CRITICAL issues:**

```bash
python scripts/auto-create-issues.py --priority CRITICAL
```

**Create ALL open issues from roadmap:**

```bash
python scripts/auto-create-issues.py
```

---

### Level 3: Claude Code Autonomous

**Add to your Claude Code prompts:**

```
"Check FEATURE_ROADMAP.md for new items and create GitHub issues 
for any CRITICAL priority items that don't have issues yet."
```

**Claude Code will:**
1. Read FEATURE_ROADMAP.md
2. Check existing GitHub issues
3. Show you what it would create
4. Ask for approval
5. Create issues automatically

---

## 📁 Files

| File | Purpose |
|------|---------|
| `scripts/generate-issue-commands.py` | Generates `gh` commands for manual run |
| `scripts/auto-create-issues.py` | Fully automated issue creation |
| `CLAUDE_CODE_AGENTIC_ISSUES.md` | Prompt templates for Claude Code |

---

## 🎯 Use Cases

### Use Case 1: Weekly Roadmap Sync

```bash
# Every Monday, sync roadmap with GitHub
python scripts/auto-create-issues.py --dry-run --priority CRITICAL

# Review output, then run:
python scripts/auto-create-issues.py --priority CRITICAL
```

---

### Use Case 2: Plan Next Sprint

```bash
# Create all HIGH priority issues for sprint planning
python scripts/auto-create-issues.py --priority HIGH
```

---

### Use Case 3: Claude Code Creates Issues On-Demand

**You:** "We need to add two-factor authentication"

**Claude Code:**
1. Determines this is a CRITICAL security feature
2. Creates GitHub issue with proper labels
3. Adds to project board
4. Updates FEATURE_ROADMAP.md
5. Confirms: "Issue #27 created. Ready to implement?"

---

## 🤖 How It Works

### Smart Label Detection

The scripts automatically detect appropriate labels based on keywords:

| Keywords | Labels Applied |
|----------|----------------|
| "AI", "AgentX" | `ai-integration`, `agentx-panel` |
| "assembly" | `assembly-builder` |
| "estimate", "line item" | `estimates` |
| "auth", "login", "role" | `auth`, `security` |
| "proposal", "PDF" | `reporting` |
| "deploy", "DigitalOcean" | `deployment` |

### Priority Mapping

| Roadmap Section | Issue Priority |
|-----------------|----------------|
| 🔥 CRITICAL PRIORITY | `CRITICAL-priority` |
| 🎯 HIGH PRIORITY | `HIGH-priority` |
| 📊 MEDIUM PRIORITY | `MEDIUM-priority` |
| 🔮 FUTURE PRIORITY | `FUTURE-priority` |

---

## 🔧 Requirements

- **Python 3.7+** (already installed)
- **GitHub CLI (`gh`)** (already installed and authenticated)
- **FEATURE_ROADMAP.md** in project root

---

## 📖 Examples

### Example 1: Preview Issues

```powershell
PS> python scripts/generate-issue-commands.py

# GitHub Issue Creation Commands
# Generated from FEATURE_ROADMAP.md

# 1. Edit Project Fields UI (🎯 HIGH PRIORITY)
gh issue create --title "[FEATURE] Edit Project Fields UI" --body "..." --label "enhancement,HIGH-priority,ui-ux"

# 2. Welcome Email on Signup (🎯 HIGH PRIORITY)
gh issue create --title "[FEATURE] Welcome Email on Signup" --body "..." --label "enhancement,HIGH-priority,auth"

# Total: 2 issues to create
```

---

### Example 2: Auto-Create with Dry Run

```powershell
PS> python scripts/auto-create-issues.py --dry-run --priority CRITICAL

============================================================
  DRY RUN: 2 issues from FEATURE_ROADMAP.md
============================================================

[1/2] Edit Project Fields UI...
  ✅ Would create

[2/2] Welcome Email on Signup...
  ✅ Would create

============================================================
  SUMMARY
============================================================
✅ Successfully created: 2
❌ Failed: 0

# Looks good? Run without --dry-run to create for real
```

---

### Example 3: Claude Code Autonomous

**In CLAUDE.md, add:**

```markdown
## Issue Management Automation

When user mentions a new feature or bug:
1. Check if GitHub issue exists
2. If not, create issue with proper labels
3. Ask: "Created issue #N. Add to sprint?"
4. If yes, add to project board

Available commands:
- python scripts/auto-create-issues.py --priority CRITICAL
- gh issue create --title "..." --body "..." --label "..."
```

**Then prompt Claude Code:**

```
"Sync FEATURE_ROADMAP.md with GitHub issues. Create any missing 
CRITICAL priority issues."
```

---

## 🎓 Tips

### Tip 1: Always Dry Run First

```bash
# See what would be created
python scripts/auto-create-issues.py --dry-run

# If it looks good, run for real
python scripts/auto-create-issues.py
```

### Tip 2: Create Issues by Priority

```bash
# Only create CRITICAL issues (for immediate attention)
python scripts/auto-create-issues.py --priority CRITICAL

# Create HIGH priority issues (for sprint planning)
python scripts/auto-create-issues.py --priority HIGH
```

### Tip 3: Check Existing Issues First

```bash
# Before creating, check what's already there
gh issue list --label "CRITICAL-priority"
```

---

## 🚨 Troubleshooting

**Error: "gh: command not found"**
- Install GitHub CLI: https://cli.github.com/

**Error: "FEATURE_ROADMAP.md not found"**
- Run script from project root: `cd "C:\Users\Tknig\Dropbox\Estimator Agent"`

**Error: "authentication token is missing required scopes"**
- Refresh auth: `gh auth refresh -s project`

---

## 🎉 Next Steps

1. **Test Level 1:** `python scripts/generate-issue-commands.py`
2. **Test Level 2:** `python scripts/auto-create-issues.py --dry-run`
3. **Integrate with Claude Code:** Add prompts from CLAUDE_CODE_AGENTIC_ISSUES.md
4. **Enjoy automated issue management!** 🤖

---

## 📚 Learn More

- See `CLAUDE_CODE_AGENTIC_ISSUES.md` for full autonomous capabilities
- See `GITHUB_SETUP_GUIDE.md` for manual issue creation workflows
- See `FEATURE_ROADMAP.md` for roadmap format
