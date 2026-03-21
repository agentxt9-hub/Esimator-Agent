# Agentic Testing System for Estimator AgentX

## Overview

This testing framework uses **Claude API** to autonomously test your entire application, including AI features. Claude acts as an intelligent QA agent that can:

- Validate API responses semantically (not just status codes)
- Identify edge cases and anomalies
- Test complex AI interactions (chat, assembly builder, scope gap detection)
- Generate detailed test reports with insights

## Setup

### 1. Install Dependencies

```bash
pip install anthropic python-dotenv requests
```

### 2. Environment Variables

Add to your `.env` file:

```bash
# Testing Configuration
TEST_BASE_URL=http://localhost:5000
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Test User Credentials (will be created if doesn't exist)
TEST_USER_EMAIL=test@estimatoragentx.com
TEST_USER_PASSWORD=TestPassword123!
```

### 3. Ensure Your App is Running

```bash
python app.py
```

The app should be running on `http://localhost:5000` (or your configured URL).

## Running Tests

### Run All Tests
```bash
python test_runner.py --all
```

### Run Specific Test Suites
```bash
python test_runner.py --auth     # Authentication tests only
python test_runner.py --ai       # AI feature tests only  
python test_runner.py --e2e      # End-to-end workflows only
```

### Default (Quick Smoke Test)
```bash
python test_runner.py            # Runs basic CRUD tests
```

### Generate Report from Previous Run
```bash
python test_runner.py --report
```

## Test Coverage

### Authentication Tests
- ✅ User signup with company creation
- ✅ User login with session management
- ✅ User logout and session termination

### Project & Estimate CRUD
- ✅ Create new project
- ✅ Add line items to estimate
- ✅ Update line items
- ✅ Delete line items

### AI Feature Tests (The Cool Stuff!)
- ✅ **AI Chat** - Tests conversational AI with construction context
- ✅ **Assembly Auto-Builder** - Tests AI breaking down work into components
- ✅ **Scope Gap Detector** - Tests AI identifying missing scope
- ✅ **Production Rate Assistant** - Tests AI production rate lookups

### End-to-End Workflows
- ✅ Complete estimate workflow (create → add items → AI assist → export)

## How Claude Validates Tests

Instead of simple `assert status_code == 200` checks, this framework uses Claude to:

1. **Understand Context** - Claude knows what the test is trying to accomplish
2. **Analyze Response** - Claude reviews the actual API response
3. **Semantic Validation** - Claude determines if the response makes sense for construction estimating
4. **Identify Issues** - Claude spots anomalies that regex/status codes would miss

Example validation:

```python
claude_validation = ask_claude_to_validate(
    test_name="AI Assembly Builder",
    context="User requests AI to build carpet installation assembly",
    expected_behavior="AI should break down work into component line items with quantities and costs",
    actual_result=api_response_data
)
```

Claude returns:
```json
{
    "passed": true,
    "confidence": "high",
    "reasoning": "Response includes appropriate line items for carpet installation: base prep, adhesive, carpet tile, and labor. Quantities and costs are reasonable for the scope.",
    "issues_found": [],
    "suggestions": ["Consider adding waste factor calculation"]
}
```

## Understanding Test Reports

After running tests, an HTML report is auto-generated in `/mnt/user-data/outputs/`:

```
test_report_20250317_143022.html
```

The report includes:
- **Overall Statistics** - Pass rate, total tests, execution time
- **Test Results by Category** - Grouped by test type
- **Detailed Failures** - Error messages and stack traces
- **Claude's Reasoning** - When Claude validation is used, see AI's analysis

## Advanced: Adding Your Own Tests

### Basic Test Template

```python
def test_your_feature():
    """Test description"""
    test = TestResult("Your Test Name", "Category")
    
    try:
        session = TestSession()
        session.login()
        
        # Your test logic here
        response = session.post_json('/your/endpoint', {'data': 'value'})
        
        if response.json().get('success'):
            test.pass_test({'your': 'details'})
        else:
            test.fail_test("Reason for failure")
    
    except Exception as e:
        test.fail_test(str(e))
```

### Using Claude Validation

```python
def test_with_ai_validation():
    test = TestResult("AI-Validated Test", "Category")
    
    try:
        session = TestSession()
        session.login()
        
        response = session.post_json('/api/endpoint', {'query': 'test'})
        data = response.json()
        
        # Let Claude validate the response
        validation = ask_claude_to_validate(
            test_name="Your Test",
            context="What the test is doing",
            expected_behavior="What should happen",
            actual_result=data
        )
        
        if validation['passed']:
            test.pass_test({'ai_reasoning': validation['reasoning']})
        else:
            test.fail_test(validation['reasoning'])
    
    except Exception as e:
        test.fail_test(str(e))
```

## Continuous Integration Ready

This test runner is designed for CI/CD pipelines:

- **Exit Codes**: Returns 0 on success, 1 on any failure
- **JSON Output**: Can be extended to output machine-readable results
- **Parallel Execution**: Tests are independent and can be parallelized
- **Environment Aware**: Uses env vars for configuration

### Example GitHub Actions Workflow

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install anthropic python-dotenv requests
      
      - name: Run migrations
        run: python app.py init-db
        
      - name: Start Flask app
        run: python app.py &
        
      - name: Run tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TEST_BASE_URL: http://localhost:5000
        run: python test_runner.py --all
```

## Troubleshooting

### Tests Fail to Connect
- Ensure Flask app is running: `python app.py`
- Check `TEST_BASE_URL` in `.env` matches your app
- Verify no firewall blocking localhost:5000

### Claude Validation Errors
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API quota/rate limits
- Review Claude's error message in test output

### Authentication Failures
- Test user may not exist - run signup test first
- Check database connection
- Verify password requirements match your app

### Database Conflicts
- Tests create real data - use a test database
- Consider adding `@before_all` cleanup
- Or use transactions with rollback

## Performance Tips

- Tests run sequentially by default (safer for database)
- For speed, use test database with faster I/O
- Claude validation adds ~1-2s per test (worth it!)
- Consider caching session tokens between tests

## Future Enhancements

Planned features:
- [ ] Load testing with concurrent users
- [ ] Performance benchmarking
- [ ] Screenshot capture on failures
- [ ] Test data fixtures/factories
- [ ] Mutation testing (intentionally break code, verify tests catch it)
- [ ] Claude-generated test cases (have AI write new tests!)

## Questions?

This testing system was built specifically for Estimator AgentX. The agentic approach means Claude understands your domain (construction estimating) and can provide intelligent validation beyond simple assertions.

Happy testing! 🧪
