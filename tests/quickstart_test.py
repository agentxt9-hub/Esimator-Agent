#!/usr/bin/env python3
"""
Quick-Start Test Script
One command to rule them all

This script:
1. Checks your environment setup
2. Seeds test data if needed
3. Starts the app (if not running)
4. Runs the full test suite with live dashboard
5. Opens the report in your browser
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_environment():
    """Verify all requirements are met"""
    print_header("🔍 Environment Check")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 7):
        issues.append("Python 3.7+ required")
    else:
        print("✅ Python version OK")
    
    # Check .env file
    if not Path('.env').exists():
        issues.append(".env file not found")
    else:
        print("✅ .env file found")
    
    # Check required packages
    try:
        import anthropic
        print("✅ anthropic package installed")
    except ImportError:
        issues.append("anthropic package not installed (pip install anthropic)")
    
    try:
        import requests
        print("✅ requests package installed")
    except ImportError:
        issues.append("requests package not installed (pip install requests)")
    
    try:
        import flask
        print("✅ flask package installed")
    except ImportError:
        issues.append("flask package not installed (pip install flask)")
    
    # Check ANTHROPIC_API_KEY
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.environ.get('ANTHROPIC_API_KEY'):
        issues.append("ANTHROPIC_API_KEY not set in .env")
    else:
        print("✅ ANTHROPIC_API_KEY configured")
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("\n✅ All checks passed!")
    return True

def check_app_running():
    """Check if Flask app is running"""
    import requests
    try:
        response = requests.get('http://localhost:5000/', timeout=2)
        return True
    except:
        return False

def start_app():
    """Start the Flask app in background"""
    print_header("🚀 Starting Flask App")
    
    if check_app_running():
        print("✅ App already running on http://localhost:5000")
        return None
    
    print("Starting app in background...")
    
    # Start app in subprocess
    process = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for app to be ready
    print("Waiting for app to start", end="")
    for i in range(10):
        time.sleep(1)
        print(".", end="", flush=True)
        if check_app_running():
            print(" ✅")
            print("App is ready!")
            return process
    
    print(" ❌")
    print("App failed to start. Check logs.")
    return None

def seed_test_data():
    """Optionally seed test data"""
    print_header("🌱 Test Data")
    
    response = input("Seed test data? (y/n): ").lower().strip()
    
    if response == 'y':
        print("Seeding CSI codes...")
        subprocess.run([sys.executable, 'seed_csi.py'])
        print("✅ Test data seeded")
    else:
        print("⏭️  Skipped")

def run_tests():
    """Run the test suite with live dashboard"""
    print_header("🧪 Running Tests")
    
    print("\n🎯 Opening live dashboard...")
    time.sleep(1)
    webbrowser.open('http://localhost:5001')
    time.sleep(2)
    
    print("\n🤖 Starting agentic test suite...")
    
    # Run tests with live monitoring
    result = subprocess.run([
        sys.executable,
        'run_tests.py',
        '--all',
        '--watch'
    ])
    
    return result.returncode == 0

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🤖 Estimator AgentX - Agentic Testing System           ║
║                                                           ║
║   Powered by Claude API for intelligent test validation  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Environment check
    if not check_environment():
        print("\n❌ Please fix the issues above and try again.")
        sys.exit(1)
    
    # Step 2: Start app
    app_process = start_app()
    
    # Step 3: Seed data (optional)
    seed_test_data()
    
    # Step 4: Run tests
    try:
        success = run_tests()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 All tests passed!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ Some tests failed. Check the report for details.")
            print("=" * 60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    
    finally:
        # Cleanup
        if app_process:
            print("\n🧹 Cleaning up...")
            app_process.terminate()
            app_process.wait()
            print("✅ App stopped")
    
    print("\n👋 Done!\n")

if __name__ == '__main__':
    main()
