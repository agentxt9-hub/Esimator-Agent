#!/usr/bin/env python3
"""
Agentic Testing System Deployment Script
Run this in your project directory: C:\\Users\\Tknig\\Dropbox\\Estimator Agent

This script will:
1. Check your environment
2. Copy all testing files to the right locations
3. Update your .env file
4. Install dependencies
5. Verify everything works
6. Run a sample test
"""

import os
import sys
import shutil
from pathlib import Path

# Color codes for Windows terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step_num, total, message):
    print(f"\n{Colors.BLUE}[Step {step_num}/{total}]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def check_prerequisites():
    """Check if we're in the right directory and have required files"""
    print_step(1, 7, "Checking prerequisites...")
    
    issues = []
    
    # Check if app.py exists
    if not Path('app.py').exists():
        issues.append("app.py not found. Are you in the project directory?")
    else:
        print_success("Found app.py")
    
    # Check if .env exists
    if not Path('.env').exists():
        issues.append(".env file not found. Please create it first.")
    else:
        print_success("Found .env file")
    
    # Check Python version
    if sys.version_info < (3, 7):
        issues.append(f"Python 3.7+ required. You have {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} OK")
    
    if issues:
        print_error("Prerequisites check failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True

def create_testing_directory():
    """Create a tests/ directory for all testing files"""
    print_step(2, 7, "Creating testing directory structure...")
    
    tests_dir = Path('tests')
    tests_dir.mkdir(exist_ok=True)
    print_success(f"Created {tests_dir}/")
    
    # Create subdirectories
    (tests_dir / 'reports').mkdir(exist_ok=True)
    print_success(f"Created {tests_dir}/reports/")
    
    return tests_dir

def copy_testing_files(tests_dir):
    """Copy all testing files from outputs to project"""
    print_step(3, 7, "Copying testing framework files...")
    
    # These files should be in your project root/tests directory
    files_to_copy = [
        'test_runner.py',
        'test_dashboard.py',
        'run_tests.py',
        'quickstart_test.py',
        'TESTING_GUIDE.md',
        'README_TESTING.md'
    ]
    
    # Simulated source (in real deployment, these would be from the outputs folder)
    print(f"\n{Colors.YELLOW}📝 Manual Step Required:{Colors.END}")
    print("Copy these files to your project directory:")
    print(f"\nFrom: The files I just created")
    print(f"To:   C:\\Users\\Tknig\\Dropbox\\Estimator Agent\\tests\\")
    print("\nFiles to copy:")
    for file in files_to_copy:
        print(f"  - {file}")
    
    input("\nPress Enter once you've copied the files...")
    
    # Verify files were copied
    missing = []
    for file in files_to_copy:
        if not (tests_dir / file).exists():
            missing.append(file)
    
    if missing:
        print_warning(f"Some files not found: {', '.join(missing)}")
        print("You can copy them later, but tests won't work until you do.")
    else:
        print_success("All testing files copied successfully!")
    
    return len(missing) == 0

def update_env_file():
    """Update .env file with testing configuration"""
    print_step(4, 7, "Updating .env configuration...")
    
    env_path = Path('.env')
    
    # Read current .env
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Check if testing config already exists
    if 'TEST_BASE_URL' in env_content:
        print_warning("Testing configuration already exists in .env")
        return
    
    # Add testing configuration
    testing_config = """
# ─────────────────────────────────────────
# AGENTIC TESTING CONFIGURATION
# ─────────────────────────────────────────

# Base URL for testing (your Flask app)
TEST_BASE_URL=http://localhost:5000

# Test user credentials (will be created automatically)
TEST_USER_EMAIL=test@estimatoragentx.com
TEST_USER_PASSWORD=TestPassword123!

# NOTE: Make sure ANTHROPIC_API_KEY is set above
"""
    
    # Append to .env
    with open(env_path, 'a') as f:
        f.write(testing_config)
    
    print_success("Updated .env with testing configuration")
    
    # Verify ANTHROPIC_API_KEY exists
    if 'ANTHROPIC_API_KEY' not in env_content:
        print_warning("ANTHROPIC_API_KEY not found in .env")
        print("\nPlease add this line to your .env file:")
        print("ANTHROPIC_API_KEY=sk-ant-your-key-here")

def install_dependencies():
    """Install required Python packages"""
    print_step(5, 7, "Installing dependencies...")
    
    packages = ['anthropic', 'python-dotenv', 'requests']
    
    print(f"\nInstalling: {', '.join(packages)}")
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + packages,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("All dependencies installed successfully!")
        else:
            print_error("Installation failed. Please run manually:")
            print(f"pip install {' '.join(packages)}")
    
    except Exception as e:
        print_error(f"Error installing dependencies: {e}")
        print("\nPlease run manually:")
        print(f"pip install {' '.join(packages)}")

def create_github_workflow():
    """Create GitHub Actions workflow (optional)"""
    print_step(6, 7, "Setting up CI/CD (optional)...")
    
    response = input("\nDo you want to set up GitHub Actions for automated testing? (y/n): ").lower()
    
    if response == 'y':
        # Create .github/workflows directory
        workflows_dir = Path('.github/workflows')
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n📝 Manual Step Required:")
        print(f"Copy 'github_workflow_tests.yml' to:")
        print(f"{workflows_dir}/tests.yml")
        
        input("\nPress Enter once copied...")
        
        if (workflows_dir / 'tests.yml').exists():
            print_success("GitHub Actions workflow configured!")
            print("\nRemember to add ANTHROPIC_API_KEY to GitHub Secrets:")
            print("GitHub Repo → Settings → Secrets → Actions → New repository secret")
        else:
            print_warning("Workflow file not found. You can add it later.")
    else:
        print("Skipped CI/CD setup. You can add it later if needed.")

def verify_installation():
    """Verify everything is set up correctly"""
    print_step(7, 7, "Verifying installation...")
    
    checks = []
    
    # Check files exist
    tests_dir = Path('tests')
    if (tests_dir / 'test_runner.py').exists():
        checks.append(('Test Runner', True))
    else:
        checks.append(('Test Runner', False))
    
    # Check .env has testing config
    with open('.env', 'r') as f:
        env_content = f.read()
    
    if 'TEST_BASE_URL' in env_content:
        checks.append(('Environment Config', True))
    else:
        checks.append(('Environment Config', False))
    
    if 'ANTHROPIC_API_KEY' in env_content:
        checks.append(('Claude API Key', True))
    else:
        checks.append(('Claude API Key', False))
    
    # Check dependencies
    try:
        import anthropic
        checks.append(('Anthropic Package', True))
    except ImportError:
        checks.append(('Anthropic Package', False))
    
    try:
        import dotenv
        checks.append(('DotEnv Package', True))
    except ImportError:
        checks.append(('DotEnv Package', False))
    
    # Print results
    print("\n" + "="*50)
    print("INSTALLATION VERIFICATION")
    print("="*50)
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(f"{check_name}: OK")
        else:
            print_error(f"{check_name}: FAILED")
            all_passed = False
    
    print("="*50 + "\n")
    
    return all_passed

def print_next_steps():
    """Print what to do next"""
    print("\n" + "="*60)
    print(f"{Colors.GREEN}🎉 DEPLOYMENT COMPLETE!{Colors.END}")
    print("="*60)
    
    print(f"\n{Colors.BLUE}📚 Quick Start Guide:{Colors.END}\n")
    
    print("1️⃣  Start your Flask app:")
    print("   python app.py")
    
    print("\n2️⃣  Run the quickstart test:")
    print("   cd tests")
    print("   python quickstart_test.py")
    
    print("\n3️⃣  Or run specific tests:")
    print("   python test_runner.py --all       # All tests")
    print("   python test_runner.py --ai        # Just AI features")
    print("   python test_runner.py --auth      # Just authentication")
    
    print("\n4️⃣  Watch tests live:")
    print("   python run_tests.py --all --watch")
    print("   Then open: http://localhost:5001")
    
    print(f"\n{Colors.BLUE}📖 Documentation:{Colors.END}")
    print("   tests/README_TESTING.md    - Full guide")
    print("   tests/TESTING_GUIDE.md     - Detailed docs")
    
    print(f"\n{Colors.YELLOW}⚠️  Important:{Colors.END}")
    print("   - Make sure your .env has ANTHROPIC_API_KEY")
    print("   - Your app must be running on localhost:5000")
    print("   - Tests will create real data in your database")
    
    print("\n" + "="*60 + "\n")

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🤖 Estimator AgentX - Agentic Testing Deployment      ║
║                                                          ║
║   This will set up intelligent testing powered by       ║
║   Claude API for your construction estimating app       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\nThis script will guide you through deploying the testing system.")
    print("Make sure you're in your project directory:")
    print("C:\\Users\\Tknig\\Dropbox\\Estimator Agent\n")
    
    response = input("Ready to begin? (y/n): ").lower()
    if response != 'y':
        print("Deployment cancelled.")
        sys.exit(0)
    
    # Run deployment steps
    if not check_prerequisites():
        sys.exit(1)
    
    tests_dir = create_testing_directory()
    copy_testing_files(tests_dir)
    update_env_file()
    install_dependencies()
    create_github_workflow()
    
    if verify_installation():
        print_next_steps()
    else:
        print_error("\nSome checks failed. Please fix the issues above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
