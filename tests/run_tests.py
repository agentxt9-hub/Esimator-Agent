"""
Integrated Test Runner with Live Dashboard
Run this to execute tests with real-time visual monitoring

Usage:
    python run_tests.py --all --watch
"""

import sys
import time
import subprocess
import threading
from test_dashboard import start_dashboard_server, publish_test_event

# Import all test functions
from test_runner import (
    test_auth_signup,
    test_auth_login,
    test_auth_logout,
    test_project_create,
    test_line_item_create,
    test_ai_chat,
    test_ai_assembly_builder,
    test_ai_scope_gap_detector,
    test_ai_production_rate_assistant,
    test_e2e_complete_estimate_workflow,
    test_results,
    generate_html_report
)

def run_with_monitoring(test_func, test_name, category):
    """Run a test function with dashboard monitoring"""
    
    # Publish start event
    publish_test_event(test_name, category, 'started')
    
    try:
        # Run the actual test
        test_func()
        
        # Find the result
        result = next((r for r in test_results if r.test_name == test_name), None)
        
        if result and result.passed:
            publish_test_event(
                test_name, 
                category, 
                'passed',
                f'Completed in {result.duration:.2f}s'
            )
        else:
            error_msg = result.error_message if result else 'Unknown error'
            publish_test_event(
                test_name,
                category,
                'failed',
                error_msg
            )
    
    except Exception as e:
        publish_test_event(test_name, category, 'failed', str(e))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests with live monitoring')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--auth', action='store_true', help='Run auth tests')
    parser.add_argument('--ai', action='store_true', help='Run AI tests')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests')
    parser.add_argument('--watch', action='store_true', help='Enable live dashboard')
    parser.add_argument('--no-report', action='store_true', help='Skip HTML report generation')
    
    args = parser.parse_args()
    
    # Start dashboard if watch mode enabled
    if args.watch:
        dashboard_thread = start_dashboard_server()
        time.sleep(2)  # Give dashboard time to start
        print("\n🎯 Open http://localhost:5001 to watch tests live!\n")
        time.sleep(3)  # Give user time to open browser
    
    print("🤖 Estimator AgentX - Agentic Test Runner")
    print("=" * 60)
    print()
    
    # Define test suites
    auth_tests = [
        (test_auth_signup, "User Signup", "Authentication"),
        (test_auth_login, "User Login", "Authentication"),
        (test_auth_logout, "User Logout", "Authentication"),
    ]
    
    crud_tests = [
        (test_project_create, "Create Project", "Project Management"),
        (test_line_item_create, "Create Line Item", "Estimating"),
    ]
    
    ai_tests = [
        (test_ai_chat, "AI Chat", "AI Features"),
        (test_ai_assembly_builder, "AI Assembly Builder", "AI Features"),
        (test_ai_scope_gap_detector, "AI Scope Gap Detector", "AI Features"),
        (test_ai_production_rate_assistant, "AI Production Rate Assistant", "AI Features"),
    ]
    
    e2e_tests = [
        (test_e2e_complete_estimate_workflow, "E2E Complete Workflow", "Integration"),
    ]
    
    # Run selected tests
    tests_to_run = []
    
    if args.all:
        tests_to_run = auth_tests + crud_tests + ai_tests + e2e_tests
    else:
        if args.auth:
            tests_to_run.extend(auth_tests)
        if args.ai:
            tests_to_run.extend(ai_tests)
        if args.e2e:
            tests_to_run.extend(e2e_tests)
        if not any([args.auth, args.ai, args.e2e]):
            tests_to_run = crud_tests  # Default
    
    # Execute tests
    for test_func, test_name, category in tests_to_run:
        if args.watch:
            run_with_monitoring(test_func, test_name, category)
        else:
            test_func()
        
        time.sleep(0.5)  # Small delay between tests for readability
    
    # Summary
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
    
    # Generate report
    if not args.no_report:
        report_path = generate_html_report()
        print(f"\n📊 HTML Report: {report_path}")
    
    if args.watch:
        print("\n💡 Dashboard will remain open. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
    
    # Exit with proper code
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
