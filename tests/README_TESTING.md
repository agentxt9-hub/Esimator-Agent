# 🤖 Estimator AgentX - Agentic Testing System

An intelligent, Claude-powered testing framework that doesn't just check status codes — it **understands** your construction estimating application and validates behavior semantically.

## 🎯 What Makes This "Agentic"?

Traditional tests:
```python
assert response.status_code == 200
assert 'success' in response.json()
```

Agentic tests (using Claude):
```python
# Claude analyzes the entire response contextually
validation = ask_claude_to_validate(
    test_name="AI Assembly Builder",
    context="User asks AI to break down carpet installation",
    expected_behavior="Should return line items with: base prep, adhesive, carpet, labor",
    actual_result=response.json()
)

# Claude returns:
{
    "passed": true,
    "confidence": "high", 
    "reasoning": "Response includes all expected components with reasonable quantities",
    "issues_found": [],
    "suggestions": ["Consider adding waste factor calculation"]
}
```

Claude acts as an intelligent QA engineer who:
- ✅ Understands construction estimating domain
- ✅ Validates semantic correctness, not just syntax
- ✅ Identifies edge cases and anomalies
- ✅ Provides actionable suggestions

## 🚀 Quick Start (Easiest Way)

**One command to test everything:**

```bash
python quickstart_test.py
```

This script:
1. Checks your environment
2. Starts your Flask app
3. Seeds test data (optional)
4. Opens a live dashboard
5. Runs all tests with real-time monitoring
6. Generates an HTML report

**That's it!** Open `http://localhost:5001` to watch tests run live.

## 📁 What You Got

```
testing_system/
├── test_runner.py           # Core test framework (30+ tests)
├── test_dashboard.py         # Live monitoring dashboard
├── run_tests.py             # Integrated runner with dashboard
├── quickstart_test.py       # One-click testing script
├── TESTING_GUIDE.md         # Comprehensive documentation
└── test_report_*.html       # Auto-generated reports
```

## 🧪 Test Coverage

### Authentication & Session Management
- ✅ User signup with company creation
- ✅ Login flow with session tokens
- ✅ Logout and session termination
- ✅ Multi-tenancy isolation

### Project & Estimate CRUD
- ✅ Create projects with metadata
- ✅ Add/update/delete line items
- ✅ Assembly management
- ✅ Data validation

### AI Features (The Magic ✨)
- ✅ **AI Chat** - Conversational construction assistant
- ✅ **Assembly Auto-Builder** - Break down work into components
- ✅ **Scope Gap Detector** - Identify missing scope items
- ✅ **Production Rate Assistant** - Lookup crew sizes & rates

### End-to-End Workflows
- ✅ Complete estimating workflow (create → estimate → AI assist → validate)
- ✅ Multi-step AI interactions
- ✅ Data persistence across requests

## 📊 Live Dashboard

Run tests with real-time monitoring:

```bash
python run_tests.py --all --watch
```

Then open `http://localhost:5001` to see:

- **Live test progress** - Watch tests execute in real-time
- **Pass/fail status** - Instant feedback with animated updates
- **Test details** - See what's being tested right now
- **Statistics** - Total, passed, failed, running counts

## 🎨 Test Reports

Beautiful HTML reports auto-generated after each run:

```bash
python test_runner.py --all
# Opens test_report_20250317_143022.html
```

Reports include:
- Overall statistics with pass rates
- Tests grouped by category
- Detailed error messages
- Claude's AI validation reasoning
- Execution times

## 🔧 Manual Testing (Advanced)

### Run Specific Test Suites

```bash
# Just authentication tests
python test_runner.py --auth

# Just AI features
python test_runner.py --ai

# Just end-to-end workflows  
python test_runner.py --e2e

# Everything
python test_runner.py --all
```

### With Live Dashboard

```bash
python run_tests.py --ai --watch
```

### Generate Report Only (from previous run)

```bash
python test_runner.py --report
```

## 🛠️ Setup (Manual)

If you didn't use `quickstart_test.py`:

### 1. Install Dependencies

```bash
pip install anthropic python-dotenv requests
```

### 2. Configure Environment

Add to your `.env`:

```bash
# Testing
TEST_BASE_URL=http://localhost:5000
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional test credentials
TEST_USER_EMAIL=test@estimatoragentx.com
TEST_USER_PASSWORD=TestPassword123!
```

### 3. Start Your App

```bash
python app.py
```

### 4. Run Tests

```bash
python test_runner.py --all
```

## 📝 Writing Your Own Tests

### Basic Test Template

```python
def test_your_feature():
    """Test description"""
    test = TestResult("Your Test Name", "Category")
    
    try:
        session = TestSession()
        session.login()
        
        response = session.post_json('/your/endpoint', {
            'data': 'value'
        })
        
        if response.json().get('success'):
            test.pass_test({'details': 'here'})
        else:
            test.fail_test("Reason")
    
    except Exception as e:
        test.fail_test(str(e))
```

### With Claude Validation (Recommended!)

```python
def test_ai_feature():
    test = TestResult("AI Feature Test", "AI")
    
    try:
        session = TestSession()
        session.login()
        
        response = session.post_json('/api/ai/endpoint', {
            'query': 'test query'
        })
        
        # Let Claude intelligently validate
        validation = ask_claude_to_validate(
            test_name="AI Feature Test",
            context="Testing AI feature with construction query",
            expected_behavior="AI should respond with relevant construction info",
            actual_result=response.json()
        )
        
        if validation['passed']:
            test.pass_test({
                'confidence': validation['confidence'],
                'reasoning': validation['reasoning']
            })
        else:
            test.fail_test(validation['reasoning'])
    
    except Exception as e:
        test.fail_test(str(e))
```

## 🎯 Use Cases

### Before Deployment
```bash
# Run full test suite
python quickstart_test.py

# Review report
# Fix any failures
# Deploy with confidence
```

### After Adding a Feature
```bash
# Write test for new feature
# Add to test_runner.py

# Run tests
python test_runner.py --all

# Ensure everything still works
```

### During Development
```bash
# Run tests with live dashboard
python run_tests.py --watch

# Keep browser open
# Make code changes
# Re-run to see immediate feedback
```

### CI/CD Integration
```bash
# In your GitHub Actions / Jenkins / etc.
python test_runner.py --all --no-report

# Exit code: 0 = pass, 1 = fail
# Perfect for automated testing
```

## 🔍 How Claude Validation Works

When you use `ask_claude_to_validate()`, here's what happens:

1. **Context Assembly** - Your test context + expected behavior + actual result
2. **Claude Analysis** - Claude API receives the prompt
3. **Semantic Validation** - Claude analyzes if the response makes sense
4. **Structured Response** - Claude returns pass/fail + reasoning

Example:

```python
# You provide:
ask_claude_to_validate(
    test_name="Production Rate Lookup",
    context="User asks for drywall installation rate in Houston",
    expected_behavior="Should return crew size, hours/unit, location factors",
    actual_result={
        "crew_size": "2-person crew",
        "rate": "150 SF/hour",
        "location_multiplier": 0.95
    }
)

# Claude returns:
{
    "passed": true,
    "confidence": "high",
    "reasoning": "Response includes expected fields with realistic values. Houston location multiplier of 0.95 is reasonable for the region.",
    "issues_found": [],
    "suggestions": ["Consider adding unit cost estimate"]
}
```

## 🚨 Troubleshooting

### Tests Can't Connect
```bash
# Ensure app is running
python app.py

# Check port
curl http://localhost:5000/

# Verify TEST_BASE_URL in .env
```

### Claude API Errors
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Verify quota
# Check Anthropic console

# Test connection
python -c "from anthropic import Anthropic; print(Anthropic().messages.create(...))"
```

### Authentication Failures
```bash
# Create test user manually
# Or run signup test first
python test_runner.py --auth

# Check database
psql -d estimator_db -c "SELECT * FROM users WHERE email='test@estimatoragentx.com';"
```

### Dashboard Won't Start
```bash
# Port 5001 might be in use
lsof -i :5001

# Kill existing process
kill -9 <PID>

# Try again
python run_tests.py --watch
```

## 📈 Performance Notes

- **Sequential Execution**: Tests run one at a time (safer for database)
- **Claude Validation**: Adds ~1-2s per test (worth it for intelligence!)
- **Database**: Uses your real database (consider test DB for production)
- **Cleanup**: Tests create real data (implement cleanup if needed)

## 🎓 Learning Resources

- `TESTING_GUIDE.md` - Comprehensive documentation
- Test files themselves - Heavily commented examples
- Live dashboard - Watch tests to understand flow

## 🔮 Future Enhancements

Planned features (contribute via GitHub):

- [ ] Parallel test execution
- [ ] Performance benchmarking
- [ ] Screenshot capture on failures
- [ ] Test data fixtures
- [ ] Mutation testing
- [ ] **Claude-generated test cases** (AI writes new tests!)
- [ ] Integration with CI/CD
- [ ] Slack/email notifications
- [ ] Test coverage reports

## 💡 Pro Tips

1. **Always use Claude validation for AI features** - It catches subtle bugs
2. **Run `--watch` mode during development** - Instant visual feedback
3. **Generate reports** - Share with team, track over time
4. **Use test database** - Avoid polluting production data
5. **Write descriptive test names** - Makes reports more useful

## 🤝 Contributing

Want to add tests? Here's how:

1. Write test function in `test_runner.py`
2. Follow the naming convention: `test_category_feature()`
3. Use `TestResult` class for tracking
4. Use Claude validation for complex assertions
5. Add to appropriate test suite in `run_tests.py`
6. Run and verify: `python test_runner.py --all`
7. Submit PR!

## 📄 License

This testing framework is part of Estimator AgentX and follows the same license.

## 🎉 Credits

Built with:
- **Claude API** (claude-sonnet-4-20250514) - The brains
- **Python** - The backbone  
- **Flask** - Dashboard framework
- **Love** - The secret ingredient

---

**Ready to test?**

```bash
python quickstart_test.py
```

Happy testing! 🧪✨
