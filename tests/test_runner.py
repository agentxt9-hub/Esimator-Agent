"""
Agentic Testing Framework for Estimator AgentX
Powered by Claude API to autonomously test all features

Usage:
    python test_runner.py --all                    # Run all tests
    python test_runner.py --auth                   # Test authentication
    python test_runner.py --ai                     # Test AI features
    python test_runner.py --e2e                    # End-to-end workflows
    python test_runner.py --report                 # Generate HTML report
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://localhost:5000')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
TEST_USER_EMAIL = 'thomasheise@live.com'
TEST_USER_PASSWORD = 'password'

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in environment")
    sys.exit(1)

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Create reports directory
REPORTS_DIR = Path(__file__).parent / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────
# TEST RESULT STORAGE
# ─────────────────────────────────────────

test_results = []

class TestResult:
    def __init__(self, test_name, category):
        self.test_name = test_name
        self.category = category
        self.passed = False
        self.error_message = None
        self.duration = 0
        self.details = {}
        self.start_time = time.time()
    
    def pass_test(self, details=None):
        self.passed = True
        self.duration = time.time() - self.start_time
        if details:
            self.details = details
        test_results.append(self)
        print(f"✅ PASS: {self.test_name} ({self.duration:.2f}s)")
    
    def fail_test(self, error_message, details=None):
        self.passed = False
        self.error_message = error_message
        self.duration = time.time() - self.start_time
        if details:
            self.details = details
        test_results.append(self)
        print(f"❌ FAIL: {self.test_name} - {error_message} ({self.duration:.2f}s)")

# ─────────────────────────────────────────
# HELPER: SESSION MANAGER
# ─────────────────────────────────────────

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        self.user_id = None
        self.company_id = None
    
    def get_csrf_token(self):
        """Extract CSRF token from login page"""
        response = self.session.get(f"{BASE_URL}/login")
        # Simple extraction - adjust based on your actual HTML structure
        if 'csrf_token' in response.text:
            # This is a simplistic approach; you may need regex
            return "dummy-csrf-token"  # Replace with actual extraction
        return None
    
    def login(self, email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD):
        """Login and establish session"""
        self.csrf_token = self.get_csrf_token()
        response = self.session.post(
            f"{BASE_URL}/login",
            data={'email': email, 'password': password, 'csrf_token': self.csrf_token},
            allow_redirects=False
        )
        return response.status_code in [200, 302]
    
    def get(self, endpoint, **kwargs):
        return self.session.get(f"{BASE_URL}{endpoint}", **kwargs)
    
    def post(self, endpoint, **kwargs):
        return self.session.post(f"{BASE_URL}{endpoint}", **kwargs)
    
    def post_json(self, endpoint, data, **kwargs):
        return self.session.post(
            f"{BASE_URL}{endpoint}",
            json=data,
            headers={'Content-Type': 'application/json'},
            **kwargs
        )

# ─────────────────────────────────────────
# CLAUDE AGENT: TEST ANALYZER
# ─────────────────────────────────────────

def ask_claude_to_validate(test_name, context, expected_behavior, actual_result):
    """
    Use Claude to intelligently validate test results
    """
    prompt = f"""You are a QA test validator for a construction estimating SaaS application.

Test Name: {test_name}
Context: {context}
Expected Behavior: {expected_behavior}

Actual Result:
{json.dumps(actual_result, indent=2)}

Your task:
1. Analyze if the actual result matches the expected behavior
2. Identify any anomalies or red flags
3. Provide a pass/fail decision with reasoning

Respond in JSON format:
{{
    "passed": true/false,
    "confidence": "high/medium/low",
    "reasoning": "explanation of your decision",
    "issues_found": ["list of any issues"],
    "suggestions": ["optional improvement suggestions"]
}}
"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        # Strip markdown if present
        if result_text.strip().startswith("```json"):
            result_text = result_text.strip()[7:-3]
        
        return json.loads(result_text)
    
    except Exception as e:
        return {
            "passed": False,
            "confidence": "low",
            "reasoning": f"Claude validation failed: {str(e)}",
            "issues_found": [str(e)],
            "suggestions": []
        }

# ─────────────────────────────────────────
# TEST SUITE: AUTHENTICATION
# ─────────────────────────────────────────

def test_auth_signup():
    """Test user signup flow"""
    test = TestResult("User Signup", "Authentication")
    
    try:
        session = TestSession()
        unique_email = f"test_{int(time.time())}@test.com"
        
        response = session.post('/signup', data={
            'company_name': 'Test Company',
            'username': f'testuser_{int(time.time())}',
            'email': unique_email,
            'password': TEST_USER_PASSWORD,
            'password_confirm': TEST_USER_PASSWORD
        })
        
        if response.status_code == 200 or response.status_code == 302:
            test.pass_test({'status_code': response.status_code})
        else:
            test.fail_test(f"Unexpected status code: {response.status_code}")
    
    except Exception as e:
        test.fail_test(str(e))

def test_auth_login():
    """Test user login flow"""
    test = TestResult("User Login", "Authentication")
    
    try:
        session = TestSession()
        success = session.login()
        
        if success:
            # Verify we can access dashboard
            response = session.get('/dashboard')
            if response.status_code == 200:
                test.pass_test({'redirected_to_dashboard': True})
            else:
                test.fail_test(f"Login succeeded but dashboard returned {response.status_code}")
        else:
            test.fail_test("Login failed")
    
    except Exception as e:
        test.fail_test(str(e))

def test_auth_logout():
    """Test user logout"""
    test = TestResult("User Logout", "Authentication")
    
    try:
        session = TestSession()
        session.login()
        
        response = session.get('/logout')
        
        # After logout, dashboard should redirect to login
        dashboard_response = session.get('/dashboard')
        if dashboard_response.status_code == 302:
            test.pass_test({'logout_successful': True})
        else:
            test.fail_test("Still authenticated after logout")
    
    except Exception as e:
        test.fail_test(str(e))

# ─────────────────────────────────────────
# TEST SUITE: PROJECT & ESTIMATE CRUD
# ─────────────────────────────────────────

def test_project_create():
    """Test project creation"""
    test = TestResult("Create Project", "Project Management")
    
    try:
        session = TestSession()
        session.login()
        
        # Use form data, not JSON (your API uses request.form)
        response = session.post('/project/new', data={
            'project_name': f'Test Project {int(time.time())}',
            'project_number': 'TEST-001',
            'description': 'Automated test project',
            'city': 'Houston',
            'state': 'TX',
            'zip_code': '77001'
        })
        
        data = response.json()
        
        claude_validation = ask_claude_to_validate(
            "Project Creation",
            "User attempts to create a new project via API",
            "API should return success=True and a project_id",
            data
        )
        
        if claude_validation['passed']:
            test.pass_test(data)
        else:
            test.fail_test(claude_validation['reasoning'])
    
    except Exception as e:
        test.fail_test(str(e))

def test_line_item_create():
    """Test adding line items to estimate"""
    test = TestResult("Create Line Item", "Estimating")
    
    try:
        session = TestSession()
        session.login()
        
        # First create a project (using form data)
        proj_response = session.post('/project/new', data={
            'project_name': f'Test Project {int(time.time())}',
            'project_number': 'TEST-002',
            'city': 'Houston',
            'state': 'TX'
        })
        
        project_id = proj_response.json()['project_id']
        
        # Add a line item (using form data)
        item_response = session.post(f'/project/{project_id}/estimate/add', data={
            'description': 'Test Concrete Pour',
            'quantity': '100',
            'unit': 'CY',
            'unit_cost': '150.00',
            'csi_level_1_id': '1',
            'csi_level_2_id': '1'
        })
        
        data = item_response.json()
        
        if data.get('success'):
            test.pass_test(data)
        else:
            test.fail_test(f"Line item creation failed: {data}")
    
    except Exception as e:
        test.fail_test(str(e))

# ─────────────────────────────────────────
# TEST SUITE: AI FEATURES
# ─────────────────────────────────────────

def test_ai_chat():
    """Test AI chat endpoint"""
    test = TestResult("AI Chat", "AI Features")
    
    try:
        session = TestSession()
        session.login()
        
        # Create project first (using form data)
        proj_response = session.post('/project/new', data={
            'project_name': f'AI Test Project {int(time.time())}',
            'city': 'Houston',
            'state': 'TX'
        })
        
        project_id = proj_response.json()['project_id']
        
        # Test AI chat (likely uses JSON for AI endpoints)
        chat_response = session.post_json('/api/ai/chat', {
            'message': 'What are the main CSI divisions for a commercial office building?',
            'project_id': project_id
        })
        
        data = chat_response.json()
        
        claude_validation = ask_claude_to_validate(
            "AI Chat Response",
            "User asks about CSI divisions for commercial office",
            "AI should provide a relevant response about construction divisions",
            data
        )
        
        if claude_validation['passed'] and data.get('response'):
            test.pass_test({'response_length': len(data.get('response', '')), 'validation': claude_validation})
        else:
            test.fail_test(claude_validation.get('reasoning', 'No response from AI'))
    
    except Exception as e:
        test.fail_test(str(e))

def test_ai_assembly_builder():
    """Test AI Assembly Auto-Builder"""
    test = TestResult("AI Assembly Builder", "AI Features")
    
    try:
        session = TestSession()
        session.login()
        
        proj_response = session.post("/project/new", data={
            'project_name': f'Assembly Test {int(time.time())}',
            'city': 'Houston',
            'state': 'TX'
        })
        
        project_id = proj_response.json()['project_id']
        
        # Test assembly builder
        response = session.post_json('/api/ai/build-assembly', {
            'project_id': project_id,
            'description': 'Install 100 SF of carpet tile in office space, including base prep and adhesive'
        })
        
        data = response.json()
        
        claude_validation = ask_claude_to_validate(
            "AI Assembly Builder",
            "User requests AI to build carpet installation assembly",
            "AI should break down the work into component line items with quantities and costs",
            data
        )
        
        if claude_validation['passed']:
            test.pass_test({'items_generated': len(data.get('items', [])), 'validation': claude_validation})
        else:
            test.fail_test(claude_validation['reasoning'])
    
    except Exception as e:
        test.fail_test(str(e))

def test_ai_scope_gap_detector():
    """Test AI Scope Gap Detector"""
    test = TestResult("AI Scope Gap Detector", "AI Features")
    
    try:
        session = TestSession()
        session.login()
        
        # Create project with some line items
        proj_response = session.post("/project/new", data={
            'project_name': f'Scope Gap Test {int(time.time())}',
            'description': 'New office building with reception area, conference rooms, and private offices',
            'city': 'Houston',
            'state': 'TX'
        })
        
        project_id = proj_response.json()['project_id']
        
        # Add a basic item (intentionally incomplete scope)
        session.post(f"/project/{project_id}/estimate/add", data={
            'description': 'Framing',
            'quantity': 1000,
            'unit': 'SF',
            'unit_cost': 8.50
        })
        
        # Run scope gap analysis
        response = session.post_json('/api/ai/scope-gap', {
            'project_id': project_id
        })
        
        data = response.json()
        
        claude_validation = ask_claude_to_validate(
            "AI Scope Gap Detection",
            "Analyze an incomplete estimate (only has framing for an office building)",
            "AI should identify missing scope items like electrical, HVAC, finishes, etc.",
            data
        )
        
        if claude_validation['passed']:
            test.pass_test({
                'gaps_found': len(data.get('gaps', [])),
                'validation': claude_validation
            })
        else:
            test.fail_test(claude_validation['reasoning'])
    
    except Exception as e:
        test.fail_test(str(e))

def test_ai_production_rate_assistant():
    """Test AI Production Rate & Pricing Assistant"""
    test = TestResult("AI Production Rate Assistant", "AI Features")
    
    try:
        session = TestSession()
        session.login()
        
        # Create project
        proj_response = session.post("/project/new", data={
            'project_name': f'Production Rate Test {int(time.time())}',
            'city': 'Houston',
            'state': 'TX'
        })
        
        project_id = proj_response.json()['project_id']
        
        # Test production rate lookup
        response = session.post_json('/api/ai/production-rate', {
            'project_id': project_id,
            'description': 'Install drywall on metal studs',
            'location': 'Houston, TX'
        })
        
        data = response.json()
        
        claude_validation = ask_claude_to_validate(
            "AI Production Rate Assistant",
            "User requests production rate for drywall installation in Houston",
            "AI should provide crew size, hours per unit, and regional pricing factors",
            data
        )
        
        if claude_validation['passed']:
            test.pass_test({'validation': claude_validation})
        else:
            test.fail_test(claude_validation['reasoning'])
    
    except Exception as e:
        test.fail_test(str(e))

# ─────────────────────────────────────────
# TEST SUITE: END-TO-END WORKFLOWS
# ─────────────────────────────────────────

def test_e2e_complete_estimate_workflow():
    """End-to-end: Create project, add items, use AI, export"""
    test = TestResult("E2E Complete Estimate Workflow", "Integration")
    
    try:
        session = TestSession()
        session.login()
        
        workflow_log = []
        
        # Step 1: Create project
        proj_response = session.post("/project/new", data={
            'project_name': f'E2E Test {int(time.time())}',
            'project_number': 'E2E-001',
            'description': 'Small office renovation - 2000 SF',
            'city': 'Houston',
            'state': 'TX',
            'zip_code': '77001'
        })
        project_id = proj_response.json()['project_id']
        workflow_log.append(f"✓ Created project {project_id}")
        
        # Step 2: Add manual line items
        session.post(f"/project/{project_id}/estimate/add", data={
            'description': 'Demolition',
            'quantity': 2000,
            'unit': 'SF',
            'unit_cost': 3.50
        })
        workflow_log.append("✓ Added demolition line item")
        
        # Step 3: Use AI to build assembly
        assembly_response = session.post_json('/api/ai/build-assembly', {
            'project_id': project_id,
            'description': 'Paint 2000 SF office space with two coats'
        })
        workflow_log.append(f"✓ AI generated {len(assembly_response.json().get('items', []))} painting items")
        
        # Step 4: Run scope gap analysis
        gap_response = session.post_json('/api/ai/scope-gap', {
            'project_id': project_id
        })
        gaps_found = len(gap_response.json().get('gaps', []))
        workflow_log.append(f"✓ Scope gap analysis found {gaps_found} potential gaps")
        
        # Step 5: Verify estimate exists
        estimate_response = session.get(f'/project/{project_id}/estimate')
        workflow_log.append("✓ Retrieved full estimate")
        
        # Final validation
        if estimate_response.status_code == 200:
            test.pass_test({
                'project_id': project_id,
                'workflow_steps': workflow_log
            })
        else:
            test.fail_test("Estimate retrieval failed")
    
    except Exception as e:
        test.fail_test(str(e))

# ─────────────────────────────────────────
# REPORT GENERATION
# ─────────────────────────────────────────

def generate_html_report():
    """Generate beautiful HTML test report"""
    
    total_tests = len(test_results)
    passed_tests = sum(1 for t in test_results if t.passed)
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estimator AgentX - Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a1628;
            color: #e2e8f0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #991b1b 100%);
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .header .timestamp {{
            opacity: 0.8;
            font-size: 14px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}
        .stat-card.passed {{ border-left-color: #10b981; }}
        .stat-card.failed {{ border-left-color: #ef4444; }}
        .stat-card .label {{
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.7;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .test-results {{
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
        }}
        .test-category {{
            background: #0f172a;
            padding: 15px 20px;
            font-weight: 600;
            border-bottom: 1px solid #334155;
        }}
        .test-item {{
            padding: 20px;
            border-bottom: 1px solid #334155;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-icon {{
            font-size: 24px;
            flex-shrink: 0;
        }}
        .test-content {{
            flex-grow: 1;
        }}
        .test-name {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .test-error {{
            color: #ef4444;
            font-size: 14px;
            margin-top: 8px;
        }}
        .test-duration {{
            font-size: 12px;
            opacity: 0.6;
        }}
        .test-details {{
            background: #0f172a;
            padding: 12px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 12px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Estimator AgentX Test Report</h1>
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="label">Total Tests</div>
                <div class="value">{total_tests}</div>
            </div>
            <div class="stat-card passed">
                <div class="label">Passed</div>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="stat-card failed">
                <div class="label">Failed</div>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="stat-card">
                <div class="label">Pass Rate</div>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="test-results">
"""
    
    # Group tests by category
    categories = {}
    for test in test_results:
        if test.category not in categories:
            categories[test.category] = []
        categories[test.category].append(test)
    
    for category, tests in categories.items():
        html += f"""
            <div class="test-category">{category}</div>
"""
        for test in tests:
            icon = "✅" if test.passed else "❌"
            details_html = ""
            
            if test.error_message:
                details_html = f'<div class="test-error">Error: {test.error_message}</div>'
            
            if test.details:
                details_html += f'<div class="test-details">{json.dumps(test.details, indent=2)}</div>'
            
            html += f"""
            <div class="test-item">
                <div class="test-icon">{icon}</div>
                <div class="test-content">
                    <div class="test-name">{test.test_name}</div>
                    <div class="test-duration">{test.duration:.2f}s</div>
                    {details_html}
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = REPORTS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return str(filepath)

def generate_json_report():
    """Generate JSON report for GitHub Actions"""
    total = len(test_results)
    passed = sum(1 for t in test_results if t.passed)
    failed = total - passed
    
    failures = []
    for test in test_results:
        if not test.passed:
            failure_data = {
                'name': test.test_name,
                'category': test.category,
                'error': test.error_message or 'Unknown error',
                'duration': test.duration
            }
            # Include Claude reasoning if available
            if test.details and 'validation' in test.details:
                validation = test.details['validation']
                failure_data['claude_reasoning'] = validation.get('reasoning', '')
                failure_data['suggestions'] = validation.get('suggestions', [])
            failures.append(failure_data)
    
    json_data = {
        'total': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': round((passed/total*100), 1) if total > 0 else 0,
        'failures': failures,
        'timestamp': datetime.now().isoformat()
    }
    
    json_path = Path(__file__).parent / 'test_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    return str(json_path)

# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Agentic Testing Framework for Estimator AgentX')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--auth', action='store_true', help='Run authentication tests')
    parser.add_argument('--ai', action='store_true', help='Run AI feature tests')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests')
    parser.add_argument('--report', action='store_true', help='Generate HTML report only')
    parser.add_argument('--json-output', action='store_true', help='Generate JSON output for CI/CD')
    
    args = parser.parse_args()
    
    if args.report and test_results:
        report_path = generate_html_report()
        print(f"\n📊 Report generated: {report_path}")
        return
    
    print("🤖 Estimator AgentX Agentic Test Runner")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"AI Model: claude-sonnet-4-20250514")
    print("=" * 60)
    print()
    
    if args.all or args.auth:
        print("\n🔐 Running Authentication Tests...")
        test_auth_signup()
        test_auth_login()
        test_auth_logout()
    
    if args.all or args.ai:
        print("\n🧠 Running AI Feature Tests...")
        test_ai_chat()
        test_ai_assembly_builder()
        test_ai_scope_gap_detector()
        test_ai_production_rate_assistant()
    
    if args.all or args.e2e:
        print("\n🔄 Running End-to-End Tests...")
        test_e2e_complete_estimate_workflow()
    
    if not any([args.all, args.auth, args.ai, args.e2e]):
        print("\n📋 Running Project CRUD Tests...")
        test_project_create()
        test_line_item_create()
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total = len(test_results)
    passed = sum(1 for t in test_results if t.passed)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
    
    # Generate HTML report
    report_path = generate_html_report()
    print(f"\n📊 HTML Report: {report_path}")
    
    # Generate JSON report for CI/CD if requested
    if args.json_output:
        json_path = generate_json_report()
        print(f"📄 JSON Report: {json_path}")
    
    # Exit with proper code
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
