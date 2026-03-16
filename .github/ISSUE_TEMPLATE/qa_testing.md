---
name: QA/Testing Task
about: Track manual testing and quality assurance work for Zenbid
title: '[QA] '
labels: testing, qa
assignees: ''

---

## 🧪 Test Scope
<!-- What are we testing? -->
- **Feature/Area:** [e.g., WBS inline editing, Password reset, AgentX panel]
- **Session:** [e.g., Session 12, Post-deployment]
- **Environment:** [Local dev / Production zenbid.io]
- **Testing Date:** 

## ✅ Test Checklist
<!-- Mark items as you test them -->

### Functionality
- [ ] Feature works as expected
- [ ] All user flows complete successfully
- [ ] Edge cases handled properly
- [ ] Error messages are clear
- [ ] Multi-tenant data isolation working (users only see their company's data)

### UI/UX
- [ ] UI renders correctly (dark theme, CSS variables)
- [ ] Responsive on different screen sizes
- [ ] No visual bugs or overflow
- [ ] Loading states work (spinners, disabled buttons)
- [ ] Tooltips/help text clear

### Performance
- [ ] Page loads in < 2 seconds
- [ ] No console errors (check browser DevTools)
- [ ] No network errors (check Network tab)
- [ ] AI responses under 5 seconds (for typical queries)
- [ ] Estimate table recalculates quickly

### Security/Auth
- [ ] CSRF token present on forms
- [ ] Rate limiting working (for AI routes, login)
- [ ] Login redirects work correctly
- [ ] Role permissions enforced (admin vs estimator vs viewer)
- [ ] No cross-company data leaks

### Data Integrity
- [ ] Data saves correctly to PostgreSQL
- [ ] Calculations accurate (line item totals, assembly totals, project totals)
- [ ] Inline editing updates database
- [ ] Delete operations work with cascading deletes
- [ ] No orphaned records

## 🐛 Bugs Found
<!-- Link to any bug issues created during testing -->
- #[issue number] - [brief description]
- #[issue number] - [brief description]

## 📊 Test Results
<!-- Overall status -->
- [ ] ✅ **PASS** - Ready to ship / deploy
- [ ] ⚠️ **PASS WITH ISSUES** - Works but has non-critical bugs (list in Bugs Found)
- [ ] ❌ **FAIL** - Blocking issues found, needs fixes before deployment

## 🖼️ Screenshots/Evidence
<!-- Optional: Attach screenshots of test results, console logs, etc. -->

## 📝 Testing Notes
<!-- Any observations, concerns, or recommendations -->

## 🔄 Regression Testing
<!-- Did this change break anything else? Check critical paths -->
- [ ] Login/logout still works
- [ ] Project creation still works
- [ ] Assembly builder still works
- [ ] Line item creation/editing still works
- [ ] AgentX AI panel still works
- [ ] Estimate table calculations still accurate
- [ ] WBS panel still works (if applicable)
- [ ] Reports still generate correctly

## 🌐 Browser Compatibility (if UI change)
- [ ] Chrome (primary)
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## 📱 Screen Sizes Tested (if UI change)
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768px) - should degrade gracefully
- [ ] Mobile (375px) - may not be fully supported yet

## 🎯 Specific Test Cases
<!-- Add specific test scenarios relevant to this feature -->

### Example: Password Reset Flow
- [ ] Request reset email (valid email)
- [ ] Request reset email (invalid email) - no error exposed
- [ ] Click reset link in email
- [ ] Token valid: reset form loads
- [ ] Token expired: error message shown
- [ ] New password meets requirements
- [ ] Login with new password works

### Example: AgentX AI Panel
- [ ] Panel opens/closes
- [ ] All 3 modes accessible (Estimate/Research/Chat)
- [ ] Estimate mode shows project context
- [ ] Rate lookup returns data
- [ ] Scope gap check generates report
- [ ] Write proposals create assemblies
- [ ] Voice input works (if applicable)

### Example: Multi-Tenant Isolation
- [ ] User A (Company 1) logs in
- [ ] Create project/assembly/line items
- [ ] Log out, log in as User B (Company 2)
- [ ] Cannot see User A's data anywhere
- [ ] Create own data, verify separation
- [ ] Check database: all records have correct company_id
