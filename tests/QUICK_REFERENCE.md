# 🚀 Estimator AgentX Testing - Quick Reference Card

## 📍 Project Location
```
C:\Users\Tknig\Dropbox\Estimator Agent\tests\
```

---

## ⚡ Most Common Commands

### Quick Test Everything
```bash
cd tests
python quickstart_test.py
```
✅ One command does it all!

### Run All Tests (No Dashboard)
```bash
python test_runner.py --all
```
⏱️ Takes ~5 minutes

### Run with Live Dashboard
```bash
python run_tests.py --all --watch
```
📊 Open http://localhost:5001 to watch

### Test Just AI Features
```bash
python test_runner.py --ai
```
🧠 Tests Chat, Assembly Builder, Scope Gap, Production Rates

### Test Just Authentication
```bash
python test_runner.py --auth
```
🔐 Tests Signup, Login, Logout

### Test Just CRUD Operations
```bash
python test_runner.py
```
📝 Tests Projects and Line Items (default, fastest)

---

## 📂 File Structure

```
Estimator Agent/
├── app.py                    ← Your main Flask app
├── .env                      ← API keys and config
│
└── tests/                    ← Testing system
    ├── test_runner.py        ← Core test framework
    ├── run_tests.py          ← Runner with dashboard
    ├── quickstart_test.py    ← One-click testing
    ├── test_dashboard.py     ← Live monitoring
    ├── README_TESTING.md     ← Documentation
    └── reports/              ← Auto-generated reports
        └── test_report_*.html
```

---

## 🔧 Before Running Tests

### 1. Start Flask App (Terminal 1)
```bash
cd C:\Users\Tknig\Dropbox\Estimator Agent
python app.py
```
⚠️ Keep this running!

### 2. Run Tests (Terminal 2)
```bash
cd C:\Users\Tknig\Dropbox\Estimator Agent\tests
python test_runner.py --all
```

---

## 📊 Understanding Results

### Terminal Output
```
✅ PASS: Create Project (1.2s)
❌ FAIL: AI Chat - API key invalid
```

### HTML Report
Location: `tests/test_report_YYYYMMDD_HHMMSS.html`
- Open in browser for detailed view
- Shows pass/fail breakdown
- Includes Claude's reasoning
- Execution times per test

### Live Dashboard
URL: `http://localhost:5001`
- Real-time test progress
- Animated status updates
- Statistics and charts

---

## 🎯 What Gets Tested

| Category | Tests | What It Checks |
|----------|-------|----------------|
| **Auth** | 3 | Signup, Login, Logout |
| **CRUD** | 2 | Projects, Line Items |
| **AI Chat** | 1 | Conversational assistant |
| **Assembly Builder** | 1 | AI breaks down work |
| **Scope Gap** | 1 | AI finds missing items |
| **Production Rates** | 1 | AI lookup crew sizes |
| **E2E** | 1 | Complete workflows |

---

## 🐛 Quick Troubleshooting

### "Connection Refused"
➡️ Flask app not running
```bash
python app.py
```

### "ANTHROPIC_API_KEY not found"
➡️ Check .env file
```bash
# Add to .env:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### "Module not found: anthropic"
➡️ Install dependencies
```bash
pip install anthropic python-dotenv requests
```

### "Database error"
➡️ Check PostgreSQL running
```bash
# Windows: Check Services
# Or start: pg_ctl start
```

### Tests failing but app works
➡️ Check test database
```bash
# Tests use real database
# May need to reset test data
```

---

## 🎓 Test Flags Reference

```bash
--all       # Run everything (~5 min)
--auth      # Just authentication tests
--ai        # Just AI feature tests
--e2e       # Just end-to-end workflows
--watch     # Enable live dashboard
--report    # Generate HTML report only
```

### Examples:
```bash
python test_runner.py --ai --watch
python run_tests.py --all --watch
python quickstart_test.py  # No flags needed
```

---

## 📈 CI/CD (GitHub Actions)

### Setup
1. Copy `github_workflow_tests.yml` to `.github/workflows/tests.yml`
2. Add `ANTHROPIC_API_KEY` to GitHub Secrets
3. Push to GitHub
4. Tests run automatically on every push

### Check Status
- GitHub repo → Actions tab
- See test results for each commit
- Download HTML reports from artifacts

---

## 🔐 Environment Variables

Required in `.env`:
```bash
# Your app
DATABASE_URL=postgresql://postgres:Builder@localhost:5432/estimator_db
ANTHROPIC_API_KEY=sk-ant-xxxxx
SECRET_KEY=your-secret-key

# Testing
TEST_BASE_URL=http://localhost:5000
TEST_USER_EMAIL=test@estimatoragentx.com
TEST_USER_PASSWORD=TestPassword123!
```

---

## 🎯 Success Criteria

✅ All tests passing = Good to deploy  
⚠️ AI tests failing = Check API key/quota  
❌ Auth tests failing = Database issue  
❌ CRUD tests failing = App logic issue  

---

## 📞 Getting Help

1. **Check docs:**
   - `README_TESTING.md` - Overview
   - `TESTING_GUIDE.md` - Detailed guide

2. **Review test output:**
   - Terminal shows errors
   - HTML report has details
   - Claude provides reasoning

3. **Debug with dashboard:**
   ```bash
   python run_tests.py --watch
   # Watch tests execute live
   ```

---

## ⏱️ Typical Run Times

| Command | Time | Use Case |
|---------|------|----------|
| `python test_runner.py` | 30s | Quick smoke test |
| `python test_runner.py --auth` | 1m | Auth check |
| `python test_runner.py --ai` | 3m | AI features |
| `python test_runner.py --all` | 5m | Full suite |
| `python quickstart_test.py` | 6m | Everything + setup |

---

## 💡 Pro Tips

1. **Run tests before deploying**
   ```bash
   python test_runner.py --all
   # If pass rate > 95%, you're good!
   ```

2. **Use dashboard during development**
   ```bash
   python run_tests.py --watch
   # Keep browser open, re-run as you code
   ```

3. **Check reports for patterns**
   - Same test failing repeatedly? Real bug!
   - Intermittent failures? Network/DB issue
   - Claude validation failing? Response format changed

4. **Test after every feature**
   - Add feature
   - Write test
   - Run: `python test_runner.py --all`
   - Ensure nothing broke

---

## 📅 Recommended Testing Schedule

### During Development
- After each feature: Run relevant test suite
- Before each commit: Run `--all`
- Before PR: Full suite + review report

### Pre-Deployment
- Full test suite
- Review HTML report
- Ensure pass rate > 95%
- Check Claude's validation reasoning

### Production Monitoring
- GitHub Actions on every push
- Daily automated runs (via cron)
- Monitor for regressions

---

**🎉 You're all set! Happy testing!**

**Last Updated:** March 2025  
**Version:** 1.0  
**For:** Estimator AgentX
