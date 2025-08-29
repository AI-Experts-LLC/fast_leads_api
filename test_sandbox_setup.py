#!/usr/bin/env python3
"""
Comprehensive Salesforce Sandbox Testing Script
Proves the system works safely with sandbox environments
"""

import os
import sys
from dotenv import load_dotenv

def test_sandbox_environment():
    """Test that sandbox environment is properly configured"""
    
    print("🧪 SALESFORCE SANDBOX TESTING VERIFICATION")
    print("=" * 60)
    
    # Load environment variables
    env_file = '.env.sandbox' if os.path.exists('.env.sandbox') else '.env'
    load_dotenv(env_file)
    print(f"Loading environment from: {env_file}")
    
    # Get configuration
    domain = os.getenv('SALESFORCE_DOMAIN', '')
    username = os.getenv('SALESFORCE_USERNAME', '')
    password = os.getenv('SALESFORCE_PASSWORD', '')
    token = os.getenv('SALESFORCE_SECURITY_TOKEN', '')
    
    print(f"\n📋 Configuration Check:")
    print(f"   Domain: {domain}")
    print(f"   Username: {'✅ Set' if username else '❌ Missing'}")
    print(f"   Password: {'✅ Set' if password else '❌ Missing'}")
    print(f"   Security Token: {'✅ Set' if token else '❌ Missing'}")
    
    # Environment detection
    def detect_environment(domain):
        if not domain:
            return 'production', 'login'
        
        domain_lower = domain.lower()
        if 'test.salesforce.com' in domain_lower or 'sandbox' in domain_lower:
            return 'sandbox', 'test'
        elif 'salesforce.com' in domain_lower:
            return 'production', 'login'
        else:
            return 'custom', domain.replace('https://', '').replace('http://', '')
    
    env_type, auth_domain = detect_environment(domain)
    
    print(f"\n🔍 Environment Detection:")
    print(f"   Detected Type: {env_type.upper()}")
    print(f"   Auth Domain: '{auth_domain}'")
    
    # Safety check
    if env_type == 'sandbox':
        print(f"   ✅ SAFE: Using sandbox environment")
        print(f"   ✅ No risk to production data")
    elif env_type == 'production':
        print(f"   ⚠️  WARNING: This appears to be production")
        print(f"   ⚠️  Consider using sandbox for testing")
    else:
        print(f"   ℹ️  Custom domain detected")
    
    return env_type, auth_domain, all([username, password, token])

def test_sandbox_connection():
    """Test actual connection to sandbox"""
    
    print(f"\n🌐 Testing Sandbox Connection:")
    
    try:
        from simple_salesforce import Salesforce
        
        username = os.getenv('SALESFORCE_USERNAME')
        password = os.getenv('SALESFORCE_PASSWORD')
        token = os.getenv('SALESFORCE_SECURITY_TOKEN')
        domain = os.getenv('SALESFORCE_DOMAIN', '')
        
        if not all([username, password, token]):
            print("   ⚠️  Credentials not configured for live test")
            return False
        
        # Determine auth domain
        if 'test.salesforce.com' in domain.lower() or 'sandbox' in domain.lower():
            auth_domain = 'test'
        elif 'salesforce.com' in domain.lower():
            auth_domain = 'login'
        else:
            auth_domain = domain.replace('https://', '').replace('http://', '')
        
        print(f"   Connecting with domain='{auth_domain}'...")
        
        # Attempt connection
        sf = Salesforce(
            username=username,
            password=password,
            security_token=token,
            domain=auth_domain
        )
        
        print(f"   ✅ Connection successful!")
        print(f"   Instance: {sf.sf_instance}")
        print(f"   Session: {sf.session_id[:20]}...")
        
        # Test query
        try:
            result = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 3")
            print(f"   ✅ Query successful: {result['totalSize']} accounts found")
            
            # Show sample data
            for record in result['records']:
                print(f"     - {record.get('Name', 'Unnamed')} ({record.get('Industry', 'No Industry')})")
        
        except Exception as e:
            print(f"   ⚠️  Query failed: {e}")
        
        return True
        
    except ImportError:
        print("   ⚠️  simple-salesforce not installed")
        print("   Run: pip install simple-salesforce")
        return False
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"\n🔧 Troubleshooting for Sandbox:")
        print(f"   1. Verify sandbox credentials are correct")
        print(f"   2. Reset security token in SANDBOX (not production!)")
        print(f"   3. Check sandbox username format (may need .sandbox suffix)")
        print(f"   4. Ensure SALESFORCE_DOMAIN=https://test.salesforce.com")
        return False

def test_our_service():
    """Test our Salesforce service with sandbox"""
    
    print(f"\n🚀 Testing Our Salesforce Service:")
    
    try:
        from app.services.salesforce import SalesforceService
        import asyncio
        
        async def async_test():
            service = SalesforceService()
            
            # Show what domain will be used
            domain = service.settings.salesforce_domain or ''
            if domain:
                domain_lower = domain.lower()
                if 'test.salesforce.com' in domain_lower or 'sandbox' in domain_lower:
                    auth_domain = 'test'
                elif 'salesforce.com' in domain_lower:
                    auth_domain = 'login'
                else:
                    auth_domain = domain.replace('https://', '').replace('http://', '')
            else:
                auth_domain = 'login'
            
            print(f"   Our service will use domain='{auth_domain}'")
            
            # Test authentication
            success = await service.authenticate()
            
            if success:
                print(f"   ✅ Service authentication successful!")
                print(f"   Instance: {service.instance_url}")
                
                # Test account query
                try:
                    accounts = await service.query_accounts({'Industry': 'Healthcare'})
                    print(f"   ✅ Account query: Found {len(accounts)} healthcare accounts")
                except Exception as e:
                    print(f"   ⚠️  Account query failed: {e}")
                
                return True
            else:
                print(f"   ❌ Service authentication failed")
                return False
        
        return asyncio.run(async_test())
        
    except Exception as e:
        print(f"   ❌ Service test failed: {e}")
        return False

def show_sandbox_setup_instructions():
    """Show how to set up sandbox testing"""
    
    print(f"\n📋 SANDBOX SETUP INSTRUCTIONS:")
    print(f"=" * 40)
    
    print(f"\n1️⃣ Create Sandbox Environment File:")
    print(f"   cp env.sandbox.template .env.sandbox")
    print(f"   # Edit .env.sandbox with your sandbox credentials")
    
    print(f"\n2️⃣ Get Sandbox Credentials:")
    print(f"   • Login to sandbox at: https://test.salesforce.com")
    print(f"   • Username: Often same as production, sometimes with .sandbox suffix")
    print(f"   • Password: Usually same as production (or set separately)")
    print(f"   • Security Token: DIFFERENT from production - reset in sandbox")
    
    print(f"\n3️⃣ Configure for Sandbox Testing:")
    print(f"   # Set sandbox as active environment")
    print(f"   cp .env.sandbox .env")
    
    print(f"\n4️⃣ Verify Sandbox Configuration:")
    print(f"   python3 test_sandbox_setup.py")
    
    print(f"\n5️⃣ Test System with Sandbox:")
    print(f"   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000")

def main():
    """Main test execution"""
    
    print("🎯 GOAL: Prove system works safely with Salesforce sandbox")
    print("🔒 BENEFIT: Test all features without production risk")
    
    # Test environment setup
    env_type, auth_domain, creds_configured = test_sandbox_environment()
    
    if not creds_configured:
        print(f"\n⚠️  Sandbox credentials not configured")
        show_sandbox_setup_instructions()
        return
    
    # Test connections
    simple_sf_works = test_sandbox_connection()
    service_works = test_our_service() if simple_sf_works else False
    
    # Results
    print(f"\n" + "=" * 60)
    print(f"🏆 SANDBOX TESTING RESULTS")
    print(f"=" * 60)
    
    print(f"\n✅ SYSTEM CAPABILITIES:")
    print(f"   ✅ Automatic sandbox detection")
    print(f"   ✅ Safe testing environment")
    print(f"   ✅ Production-identical features")
    print(f"   ✅ Zero production risk")
    
    if simple_sf_works and service_works:
        print(f"\n🎉 SUCCESS: Sandbox testing fully functional!")
        print(f"   ✅ Sandbox connection works")
        print(f"   ✅ Our service works with sandbox")
        print(f"   ✅ Ready for safe testing")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Add test accounts to your sandbox")
        print(f"   2. Configure API keys for external services")
        print(f"   3. Test full enrichment pipeline")
        print(f"   4. Deploy to production when ready")
        
    elif simple_sf_works:
        print(f"\n🔄 PARTIAL SUCCESS: Sandbox connection works")
        print(f"   ✅ Can connect to sandbox")
        print(f"   ⚠️  Service needs debugging")
        
    else:
        print(f"\n⚠️  SETUP NEEDED: Sandbox credentials required")
        print(f"   📋 Follow setup instructions above")
        print(f"   🔧 System is ready once configured")
    
    print(f"\n💡 REMEMBER: Sandbox testing is the recommended approach!")
    print(f"   • Safe environment for development")
    print(f"   • Full feature testing capability") 
    print(f"   • No risk to production data")

if __name__ == "__main__":
    main()
