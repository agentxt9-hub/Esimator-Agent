# Claude Code Agentic Issue Management

This document defines how Claude Code should autonomously manage GitHub issues for Zenbid.

## Autonomous Behaviors

### 1. Auto-Create Issues from Roadmap Changes

**Trigger:** FEATURE_ROADMAP.md is modified and committed

**Action:**
```python
# Claude Code should automatically run:
python scripts/auto-create-issues.py --priority CRITICAL --dry-run

# If dry-run looks good, ask user:
# "I found X new CRITICAL items in FEATURE_ROADMAP.md. Create GitHub issues?"

# If user approves:
python scripts/auto-create-issues.py --priority CRITICAL
```

**Expected Frequency:** When FEATURE_ROADMAP.md changes

---

### 2. Auto-Create Issues from TODO Comments

**Trigger:** Code contains TODO/FIXME comments

**Detection Pattern:**
```python
# TODO: Fix proposal route security (HIGH priority)
# FIXME: Viewer role not enforced (closes #23)
# BUG: Race condition in assembly builder
```

**Action:**
```python
# Claude Code detects TODO in git diff
# Extracts: description, priority, type
# Creates issue automatically:

gh issue create \
  --title "[BUG] Fix proposal route security" \
  --body "Found in: app.py line 234\nPriority: HIGH\nReference: TODO comment" \
  --label "bug,high,security"
```

---

### 3. Auto-Close Issues from Commit Messages

**Trigger:** Commit message contains `closes #N`, `fixes #N`, `resolves #N`

**Action:**
```bash
# This is automatic via GitHub, but Claude Code should verify:
# - Issue was actually fixed
# - Tests pass
# - Update Agent_MD.md if architectural change
```

---

### 4. Auto-Update Issues from Code Changes

**Trigger:** File changed that's referenced in an issue

**Action:**
```python
# If issue #5 says "Edit proposal.html"
# And proposal.html is modified in commit
# Claude Code adds comment to issue #5:

gh issue comment 5 --body "Progress update: proposal.html modified in commit abc123"
```

---

## Prompts for Claude Code

### Prompt: "Check for new roadmap items"

```
Read FEATURE_ROADMAP.md and check for items marked as "❌ Open" 
in CRITICAL or HIGH priority sections.

For each open item:
1. Check if a GitHub issue already exists with similar title
2. If not, run: python scripts/auto-create-issues.py --dry-run --priority CRITICAL
3. Show me the preview
4. Ask: "Create these N issues?"
5. If I approve, run without --dry-run
```

---

### Prompt: "Sync roadmap with GitHub issues"

```
1. Fetch all open GitHub issues
2. Read FEATURE_ROADMAP.md
3. Identify discrepancies:
   - Items in roadmap but no issue exists
   - Issues exist but not in roadmap
4. Suggest:
   - Create missing issues
   - Update roadmap with issue numbers
   - Close stale issues
```

---

### Prompt: "Create issue from my description"

**User says:** "We need to add email notifications when estimates are shared"

**Claude Code should:**
```
1. Determine type: [FEATURE]
2. Determine priority: Ask user or infer from keywords
3. Determine labels: enhancement, HIGH-priority, estimates, reporting
4. Generate body with:
   - Description
   - User story
   - Acceptance criteria
5. Create issue via gh CLI
6. Add to project board
7. Update FEATURE_ROADMAP.md if CRITICAL/HIGH priority
```

---

## Smart Label Detection

Claude Code should intelligently detect labels based on content:

| Keywords in Title/Body | Labels to Add |
|------------------------|---------------|
| "AI", "AgentX", "Claude" | ai-integration, agentx-panel |
| "assembly", "builder" | assembly-builder |
| "estimate", "line item" | estimates |
| "WBS", "location", "phase" | wbs |
| "auth", "login", "password", "role" | auth, security |
| "company", "multi-tenant", "isolation" | multi-tenant, security |
| "proposal", "report", "PDF" | reporting |
| "deploy", "DigitalOcean", "server" | deployment |
| "security", "CSRF", "XSS" | security |
| "database", "schema", "migration" | database |
| "bug", "fix", "broken" | bug |
| "feature", "add", "implement" | enhancement |

---

## Workflow Integration

### When User Says: "I'm working on the PDF export feature"

**Claude Code should:**
```
1. Search GitHub issues for "PDF export"
2. Find issue #5
3. Automatically:
   - Assign issue to user
   - Move to "In Progress" on project board
   - Comment: "Work started by Claude Code session"
4. When generating code, include in commits:
   git commit -m "Add WeasyPrint PDF generation (refs #5)"
```

---

### When User Says: "This is done, ship it"

**Claude Code should:**
```
1. Check what issue we're working on (e.g., #5)
2. Verify:
   - Code was committed
   - Tests pass (if applicable)
   - Meets acceptance criteria from issue
3. Update commit message if needed:
   git commit --amend -m "Add PDF export feature (closes #5)"
4. Move issue to "Done" on project board
5. Update FEATURE_ROADMAP.md (move to SHIPPED section)
```

---

## Safety Rules

Claude Code should NEVER:
- ❌ Auto-create issues without showing user preview first (except in fully autonomous mode)
- ❌ Auto-close issues without verifying fix was committed
- ❌ Delete issues (can close, but never delete)
- ❌ Modify issue labels without user understanding why

Claude Code should ALWAYS:
- ✅ Ask before creating CRITICAL priority issues
- ✅ Verify gh CLI is installed before running commands
- ✅ Show dry-run preview for bulk operations
- ✅ Link issues to commits with proper references

---

## Example: Full Agentic Workflow

**User:** "Add email notifications for shared estimates"

**Claude Code:**
```
1. [Understands this is a new feature]
   
2. [Creates GitHub issue]
   gh issue create \
     --title "[FEATURE] Email notifications for shared estimates" \
     --body "User story: As an estimator, I want to receive email when 
             someone shares an estimate with me.
             
             Acceptance criteria:
             - [ ] Email sent when estimate shared
             - [ ] Email contains estimate link
             - [ ] Email uses company branding
             - [ ] Notification preferences in settings" \
     --label "enhancement,HIGH-priority,estimates,auth"
   
3. [Adds to project board]
   gh project item-add 1 --url [issue-url]
   
4. [Updates FEATURE_ROADMAP.md]
   Adds line: "| **Email notifications** | ❌ Open | Medium | #23 | For shared estimates |"
   
5. [Confirms with user]
   "✅ Created issue #23 and added to roadmap. Ready to start implementation?"
   
6. [If user says yes, starts coding]
   - Generates email template
   - Adds route for email sending
   - Updates settings page
   - Commits with: "Add email notifications (refs #23)"
   
7. [When done]
   "Feature complete! Run tests and commit with 'closes #23' to auto-close the issue."
```

---

## Scripts Available

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/generate-issue-commands.py` | Preview issues to create | `python scripts/generate-issue-commands.py` |
| `scripts/auto-create-issues.py` | Auto-create from roadmap | `python scripts/auto-create-issues.py --dry-run` |

---

## Configuration for Claude Code

Add this to your Claude Code project settings (CLAUDE.md):

```markdown
## Autonomous Issue Management

Claude Code can autonomously manage GitHub issues using:
- `scripts/auto-create-issues.py` - Create issues from FEATURE_ROADMAP.md
- `gh issue create` - Create ad-hoc issues from user requests
- `gh issue comment` - Update issue progress
- Reference issues in commits with #N or closes #N

Before creating issues, always:
1. Show dry-run preview
2. Ask for user approval
3. Verify issue doesn't already exist
```

---

This enables Claude Code to be a true "project manager" that keeps your GitHub issues, roadmap, and codebase synchronized automatically!
