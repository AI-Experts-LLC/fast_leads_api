#!/usr/bin/env python3
"""
Get Salesforce Sandbox Security Token Programmatically
Multiple methods to retrieve your sandbox security token via command line
"""

import os
import sys
import requests
import json
from typing import Optional

def method1_reset_token_api(username: str, password: str, login_url: str = "https://test.salesforce.com") -> bool:
    """
    Method 1: Reset security token using Salesforce REST API
    This will trigger an email with the new token
    """
    print("🔄 Method 1: Reset Token via REST API")
    print("-" * 40)
    
    try:
        # Step 1: Get session ID
        login_data = {
            'grant_type': 'password',
            'client_id': '3MVG9YDQS5WtC11paU2WcQjBB3L5w4gz52uriT8ksZ3nUVjKvrfQMrU4uvZohTpD',  # Connected App
            'client_secret': 'secret',
            'username': username,
            'password': password
        }
        
        auth_url = f"{login_url}/services/oauth2/token"
        print(f"   Authenticating to: {auth_url}")
        
        # This approach requires a Connected App, which is complex for token reset
        print("   ⚠️  This method requires Connected App setup")
        print("   💡 Recommendation: Use Method 2 or 3 instead")
        return False
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def method2_sfdx_cli(username: str, password: str) -> bool:
    """
    Method 2: Use Salesforce CLI (sfdx) to reset security token
    """
    print("\n🛠️  Method 2: Salesforce CLI (sfdx)")
    print("-" * 40)
    
    try:
        import subprocess
        
        # Check if sfdx is installed
        result = subprocess.run(['sfdx', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("   ❌ Salesforce CLI not installed")
            print("   📥 Install: npm install -g sfdx-cli")
            return False
        
        print(f"   ✅ SFDX Version: {result.stdout.strip()}")
        
        # Authenticate to sandbox
        auth_cmd = [
            'sfdx', 'auth:web:login',
            '--instanceurl', 'https://test.salesforce.com',
            '--setalias', 'sandbox'
        ]
        
        print("   🔐 Authenticating to sandbox...")
        print("   💡 This will open a browser window for login")
        
        # Note: This is interactive, but shows the approach
        print(f"   Command: {' '.join(auth_cmd)}")
        print("   📋 After auth, you can reset token with:")
        print("       sfdx force:user:password:generate --targetusername sandbox")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def method3_python_script(username: str, password: str, current_token: str = "") -> bool:
    """
    Method 3: Use simple-salesforce to trigger token reset
    """
    print("\n🐍 Method 3: Python Script (simple-salesforce)")
    print("-" * 50)
    
    try:
        from simple_salesforce import Salesforce
        
        print("   🔑 Attempting to connect to sandbox...")
        
        # Try to connect first
        try:
            sf = Salesforce(
                username=username,
                password=password,
                security_token=current_token,
                domain='test'  # Sandbox
            )
            print("   ✅ Connected successfully!")
            print(f"   Instance: {sf.sf_instance}")
            
            # Use Salesforce API to reset token
            # Note: This requires special permissions and setup
            print("   💡 Connected - you can now use web interface to reset token")
            print("   🌐 Go to: Setup → My Personal Information → Reset Security Token")
            
            return True
            
        except Exception as connect_error:
            print(f"   ⚠️  Connection failed: {connect_error}")
            print("   💡 You may need to reset token manually first")
            return False
        
    except ImportError:
        print("   ❌ simple-salesforce not installed")
        print("   📥 Install: pip install simple-salesforce")
        return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def method4_curl_command(username: str, password: str) -> bool:
    """
    Method 4: Generate curl command for manual execution
    """
    print("\n🌐 Method 4: Curl Command (Manual)")
    print("-" * 40)
    
    # This is a template - actual implementation would need Connected App
    curl_template = f"""
# Curl command to reset security token (requires Connected App):

curl -X POST https://test.salesforce.com/services/oauth2/token \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "grant_type=password" \\
  -d "client_id=YOUR_CONNECTED_APP_CLIENT_ID" \\
  -d "client_secret=YOUR_CONNECTED_APP_SECRET" \\
  -d "username={username}" \\
  -d "password={password}YOUR_CURRENT_TOKEN"

# Then use the access token to call reset API
curl -X POST https://test.salesforce.com/services/data/v58.0/sobjects/User/resetSecurityToken \\
  -H "Authorization: Bearer ACCESS_TOKEN" \\
  -H "Content-Type: application/json"
"""
    
    print(curl_template)
    print("   ⚠️  Requires Connected App setup")
    print("   💡 Easier to use web interface for now")
    
    return True

def method5_web_automation() -> bool:
    """
    Method 5: Web automation with Selenium
    """
    print("\n🤖 Method 5: Web Automation (Selenium)")
    print("-" * 40)
    
    try:
        # Check if selenium is available
        import selenium
        print("   ✅ Selenium available")
        
        automation_script = '''
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def reset_token_selenium(username, password):
    driver = webdriver.Chrome()  # Requires chromedriver
    
    try:
        # Login to sandbox
        driver.get("https://test.salesforce.com")
        
        # Fill login form
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "Login").click()
        
        # Navigate to settings
        wait = WebDriverWait(driver, 10)
        
        # Click profile menu
        profile_menu = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "slds-avatar")))
        profile_menu.click()
        
        # Click Settings
        settings_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Settings")))
        settings_link.click()
        
        # Navigate to security token
        # ... continue navigation to reset token
        
        print("✅ Token reset initiated - check email!")
        
    finally:
        driver.quit()
'''
        
        print("   💡 Selenium script template available")
        print("   📥 Requires: pip install selenium")
        print("   📥 Requires: chromedriver")
        print("   ⚠️  Complex setup - manual method easier")
        
        return True
        
    except ImportError:
        print("   ❌ Selenium not installed")
        print("   📥 Install: pip install selenium")
        return False

def get_credentials_from_env():
    """Get credentials from environment or prompt"""
    username = os.getenv('SALESFORCE_USERNAME')
    password = os.getenv('SALESFORCE_PASSWORD')
    token = os.getenv('SALESFORCE_SECURITY_TOKEN', '')
    
    if not username:
        username = input("Sandbox Username: ")
    if not password:
        password = input("Sandbox Password: ")
    
    return username, password, token

def main():
    """Main function to test all methods"""
    
    print("🔑 SANDBOX SECURITY TOKEN RETRIEVAL METHODS")
    print("=" * 60)
    print("💡 Multiple ways to get your sandbox security token programmatically")
    
    # Get credentials
    username, password, current_token = get_credentials_from_env()
    
    if not username or not password:
        print("\n⚠️  Credentials needed for testing")
        print("   Set environment variables or run interactively")
        print("   SALESFORCE_USERNAME=your@email.com")
        print("   SALESFORCE_PASSWORD=yourpassword")
        return
    
    print(f"\n📋 Testing with username: {username}")
    print(f"   Password: {'*' * len(password)}")
    print(f"   Current token: {'*' * len(current_token) if current_token else 'None'}")
    
    # Test methods
    results = []
    
    results.append(("REST API", method1_reset_token_api(username, password)))
    results.append(("SFDX CLI", method2_sfdx_cli(username, password)))
    results.append(("Python Script", method3_python_script(username, password, current_token)))
    results.append(("Curl Command", method4_curl_command(username, password)))
    results.append(("Web Automation", method5_web_automation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    for method, success in results:
        status = "✅ Available" if success else "❌ Not Ready"
        print(f"   {method}: {status}")
    
    print("\n💡 RECOMMENDATIONS:")
    print("   🥇 Best: Manual web interface (fastest, most reliable)")
    print("   🥈 Good: Salesforce CLI (if you have it installed)")
    print("   🥉 Advanced: Python automation (for bulk operations)")
    
    print("\n🚀 QUICK MANUAL METHOD:")
    print("   1. Go to: https://test.salesforce.com")
    print("   2. Login with your sandbox credentials")
    print("   3. Profile → Settings → My Personal Information")
    print("   4. Click 'Reset My Security Token'")
    print("   5. Check email for new token")

if __name__ == "__main__":
    main()
