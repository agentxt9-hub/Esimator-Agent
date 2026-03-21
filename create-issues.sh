#!/bin/bash

echo "Creating remaining GitHub issues..."

# Issue #3: Proposal Route Security
gh issue create \
  --title "[BUG] Proposal route not using get_project_or_403()" \
  --body "## 🐛 Bug Description

Security vulnerability: Any logged-in user can view any project's proposal by guessing the project_id. Route doesn't check company_id.

## 📍 Location
- **Page/Feature:** Proposal viewer
- **URL Path:** /project/<id>/proposal
- **Route:** GET /project/<int:project_id>/proposal

## 🔄 Steps to Reproduce
1. Login as User A (Company 1, project_id=5)
2. Manually navigate to /project/10/proposal (Company 2's project)
3. User A can see Company 2's proposal (should be 403)

## ✅ Expected Behavior
Should return 403 Forbidden if project belongs to different company

## ❌ Actual Behavior
Shows proposal to any authenticated user

## 🔥 Severity
- [X] 🟡 **High** - Security issue but requires knowing project_id

## 🔐 Auth/Tenant Context
- **Multi-tenant issue?** Yes - data isolation vulnerability
- Affects cross-company data access

## 📝 Additional Context
From Agent_MD.md Known Gaps:
\"Proposal route not using get_project_or_403() - High severity\"

**Fix:**
Change from: \`project = Project.query.get(project_id)\`
To: \`project = get_project_or_403(project_id)\`

## 🎯 Related Routes/Models
- **Model:** Project
- **Route:** /project/<int:project_id>/proposal (in app.py)
- **Template:** proposal.html" \
  --label "bug,high,multi-tenant,security,reporting" \
  --project "Zenbid Development Sprint"

echo "✓ Issue #3 created: Proposal route security"

# Issue #4: Viewer Role Enforcement
gh issue create \
  --title "[FEATURE] Enforce viewer role permissions on write routes" \
  --body "## 💡 Feature Description

Implement role-based access control to prevent viewers from creating/updating/deleting data.

## 🎯 User Story
**As a** company admin  
**I want** viewer-role users to be read-only  
**So that** they can't accidentally modify estimates

## ✨ Proposed Solution
- Add role check decorator: @viewer_readonly
- Apply to all POST/PUT/DELETE routes (except /admin which already checks)
- Return 403 if viewer attempts write operation
- Show helpful error message in UI

## 🔗 Dependencies
- [ ] None - User model already has role field (admin/estimator/viewer)

## 📊 Priority
- [X] **HIGH** - MVP for paying users (needed before team features)

## ⚖️ Effort Estimate
- [X] **Medium** - Half day (decorator + testing)

## 🎯 Related Components
- **Models:** User (role field: admin/estimator/viewer)
- **Routes:** All write routes (create/update/delete for projects/assemblies/line items)
- **Security:** Role-based access control

## 📝 Technical Notes
- Multi-tenant safe: Yes (already company_id isolated)
- CSRF protected: Yes (already implemented Session 12)

## ✅ Acceptance Criteria
- [ ] Viewer cannot create projects/assemblies/line items
- [ ] Viewer cannot update any data
- [ ] Viewer cannot delete any data
- [ ] Clear error message shown if viewer attempts write (403 response)
- [ ] Admin and estimator roles still have full write access
- [ ] Tested with all three roles (admin/estimator/viewer)" \
  --label "enhancement,HIGH-priority,multi-tenant,security,auth" \
  --project "Zenbid Development Sprint"

echo "✓ Issue #4 created: Viewer role enforcement"

# Issue #5: PDF Export for Proposals
gh issue create \
  --title "[FEATURE] Server-side PDF export for proposals" \
  --body "## 💡 Feature Description

Implement server-side PDF generation so users can download professional proposal PDFs (not just print-to-PDF from browser).

## 🎯 User Story
**As an** estimator  
**I want to** download a PDF proposal  
**So that** I can email it to clients or include in bid packages

## ✨ Proposed Solution
Use WeasyPrint (Python library, HTML → PDF)
- Simpler than headless Chrome
- No browser dependency
- Good support for CSS print styles
- Already have print-optimized proposal.html template

**Implementation:**
- Install weasyprint library
- Add to requirements.txt
- Create new route: /project/<id>/proposal/download
- Use existing proposal.html template
- Generate PDF server-side
- Stream as download with proper filename

## 🔗 Dependencies
- [ ] Install weasyprint library (\`pip install weasyprint\`)
- [ ] Add to requirements.txt
- [ ] May need system dependencies on server (Cairo, Pango)

## 📊 Priority
- [X] **HIGH** - MVP for paying users

## ⚖️ Effort Estimate
- [X] **Large** - 1-2 full days (library integration + testing)

## 🎯 Related Components
- **Routes:** New route - /project/<id>/proposal/download
- **Templates:** proposal.html (already has light theme + print styles)
- **Libraries:** weasyprint (new dependency)

## 📝 Technical Notes
- Must respect multi-tenant isolation (use get_project_or_403())
- CSRF protection on download route
- Consider async generation for large estimates (optional v2)

## ✅ Acceptance Criteria
- [ ] \"Download PDF\" button appears on proposal page
- [ ] PDF generated server-side (not client-side print)
- [ ] PDF matches print layout from proposal.html
- [ ] Company logo included in PDF
- [ ] File named properly: [Company]_[Project]_Proposal.pdf
- [ ] Works for estimates with 100+ line items (no timeout)
- [ ] Multi-tenant security verified (cannot download other company's PDFs)" \
  --label "enhancement,HIGH-priority,reporting" \
  --project "Zenbid Development Sprint"

echo "✓ Issue #5 created: PDF export for proposals"

echo ""
echo "🎉 All 3 issues created successfully!"
echo ""
echo "View your issues at: https://github.com/agentxt9-hub/Esimator-Agent/issues"
echo "View your project board at: https://github.com/agentxt9-hub/Esimator-Agent/projects"