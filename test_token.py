#!/usr/bin/env python3
"""
Quick test for your new sandbox security token
"""

import os
from dotenv import load_dotenv

def test_sandbox_token():
    """Test the new sandbox security token"""
    
    print("🧪 TESTING SANDBOX SECURITY TOKEN")
    print("=" * 40)
    
    # Load environment
    load_dotenv()
    
    username = os.getenv('SALESFORCE_USERNAME')
    password = os.getenv('SALESFORCE_PASSWORD') 
    token = os.getenv('SALESFORCE_SECURITY_TOKEN')
    domain = os.getenv('SALESFORCE_DOMAIN', '')
    
    print(f"📋 Configuration:")
    print(f"   Domain: {domain}")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password) if password else 'Missing'}")
    print(f"   Token: {'*' * len(token) if token else 'Missing'}")
    print()
    
    if not all([username, password, token]):
        print("❌ Missing credentials in .env file")
        print()
        print("📝 Create .env file with:")
        print("   SALESFORCE_DOMAIN=https://test.salesforce.com")
        print("   SALESFORCE_USERNAME=lucas.erb@metrusenergy.com.metrusdedv")
        print("   SALESFORCE_PASSWORD=your_password")
        print("   SALESFORCE_SECURITY_TOKEN=YourNewTokenFromEmail")
        return False
    
    # Test connection
    try:
        from simple_salesforce import Salesforce
        
        print("🔌 Testing sandbox connection...")
        
        sf = Salesforce(
            username=username,
            password=password,
            security_token=token,
            domain='test'  # Sandbox domain
        )
        
        print("✅ Connection successful!")
        print(f"   Instance: {sf.sf_instance}")
        print(f"   Session ID: {sf.session_id[:20]}...")
        
        # Test query
        try:
            result = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 3")
            print(f"✅ Query test: Found {result['totalSize']} accounts")
            
            if result['records']:
                print("   Sample accounts:")
                for record in result['records'][:3]:
                    name = record.get('Name', 'Unnamed')
                    industry = record.get('Industry', 'No Industry')
                    print(f"     - {name} ({industry})")
        
        except Exception as e:
            print(f"⚠️  Query failed: {e}")
        
        print()
        print("🎉 SUCCESS: Sandbox connection working!")
        print("🚀 Ready to test the Metrus Account Enrichment System")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Verify the security token is correct")
        print("   2. Make sure you copied the full token from email")
        print("   3. Check password is correct")
        print("   4. Ensure no extra spaces in .env file")
        return False

if __name__ == "__main__":
    test_sandbox_token()
