"""
Quick diagnostic - Test just the login
Save as test_login_only.py in tests folder
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = 'http://localhost:5000'
TEST_USER_EMAIL = os.environ.get('TEST_USER_EMAIL', 'thomasheise@live.com')
TEST_USER_PASSWORD = os.environ.get('TEST_USER_PASSWORD', 'password')

print("🔍 Testing Login Flow")
print("=" * 60)

# Step 1: Get login page
session = requests.Session()
response = session.get(f"{BASE_URL}/login")
print(f"✅ Login page loaded: {response.status_code}")

# Step 2: Attempt login
print(f"\nAttempting login with: {TEST_USER_EMAIL}")
login_response = session.post(
    f"{BASE_URL}/login",
    data={
        'email': TEST_USER_EMAIL,
        'password': TEST_USER_PASSWORD
    },
    allow_redirects=False
)

print(f"Login response status: {login_response.status_code}")
print(f"Location header: {login_response.headers.get('Location', 'None')}")

# Step 3: Try to access dashboard
dashboard_response = session.get(f"{BASE_URL}/dashboard")
print(f"\nDashboard access: {dashboard_response.status_code}")

if dashboard_response.status_code == 200:
    print("✅ LOGIN SUCCESSFUL!")
    print("\nSession cookies:")
    for cookie in session.cookies:
        print(f"  {cookie.name} = {cookie.value[:20]}...")
else:
    print("❌ LOGIN FAILED")
    print("\nResponse preview:")
    print(dashboard_response.text[:500])

# Step 4: Test project creation with form data
if dashboard_response.status_code == 200:
    print("\n" + "=" * 60)
    print("Testing project creation...")
    
    import time
    proj_response = session.post(
        f"{BASE_URL}/project/new",
        data={
            'project_name': f'Test {int(time.time())}',
            'city': 'Houston',
            'state': 'TX'
        }
    )
    
    print(f"Project creation status: {proj_response.status_code}")
    print(f"Response preview: {proj_response.text[:200]}")
    
    try:
        result = proj_response.json()
        print(f"✅ JSON response: {result}")
    except:
        print("❌ Not JSON - returned HTML")
