#!/usr/bin/env python3
"""
Quick Sandbox Token Helper
Helps you get your security token easily
"""

import webbrowser
import time

def open_sandbox_token_page():
    """Open the sandbox security token reset page directly"""
    
    print("🔑 QUICK SANDBOX TOKEN RESET")
    print("=" * 40)
    
    print("\n📋 Your sandbox credentials detected:")
    print("   Username: lucas.erb@metrusenergy.com.metrusdedv")
    print("   Environment: Metrus Energy Sandbox")
    print()
    
    print("🚀 Opening sandbox login page...")
    
    # Open sandbox login
    webbrowser.open("https://test.salesforce.com")
    
    time.sleep(2)
    
    print("\n📋 STEPS TO GET YOUR TOKEN:")
    print("=" * 40)
    print("1. ✅ Login to the sandbox with your credentials")
    print("2. 📸 Click your profile picture (top right)")
    print("3. ⚙️  Click 'Settings'")
    print("4. 👤 Click 'My Personal Information' (left sidebar)")
    print("5. 🔑 Click 'Reset My Security Token'")
    print("6. 🔄 Click 'Reset Security Token' button")
    print("7. 📧 Check your email for the new token")
    print("8. 📋 Copy the token to your .env file")
    
    print("\n📧 EMAIL WILL LOOK LIKE:")
    print("   From: Salesforce <noreply@salesforce.com>")
    print("   Subject: Your new Salesforce security token")
    print("   Body: Your new security token is: AbCdEfGhIjKlMnOpQrStUv")
    
    print("\n💾 UPDATE YOUR .env FILE:")
    print("   SALESFORCE_DOMAIN=https://test.salesforce.com")
    print("   SALESFORCE_USERNAME=lucas.erb@metrusenergy.com.metrusdedv")
    print("   SALESFORCE_PASSWORD=your_password")
    print("   SALESFORCE_SECURITY_TOKEN=NewTokenFromEmail")
    
    print("\n🧪 TEST YOUR CONNECTION:")
    print("   python3 test_sandbox_setup.py")
    
    print("\n⏱️  Expected time: 2-3 minutes total")
    print("🎯 Result: Working sandbox connection for safe testing!")

if __name__ == "__main__":
    open_sandbox_token_page()
