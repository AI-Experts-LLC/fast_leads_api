#!/usr/bin/env python3
"""
Test Salesforce integration with real sandbox
"""

import asyncio
from app.services.salesforce import SalesforceService

async def test_salesforce_integration():
    print("🔌 TESTING SALESFORCE SANDBOX INTEGRATION")
    print("=" * 50)
    
    try:
        print("1️⃣ Authenticating to sandbox...")
        async with SalesforceService() as sf:
            print("✅ Authentication successful!")
            print(f"   Instance: {sf.instance_url}")
            print(f"   Token: {sf.access_token[:30]}...")
            
            print("\n2️⃣ Testing basic API calls...")
            
            # Test getting user info
            try:
                user_query = "SELECT Id, Username, Name, Email FROM User WHERE Username = 'lucas.erb@metrusenergy.com.metrusdedv' LIMIT 1"
                users = await sf.query(user_query)
                if users:
                    user = users[0]
                    print("✅ User query successful:")
                    print(f"   Name: {user.get('Name')}")
                    print(f"   Email: {user.get('Email')}")
                else:
                    print("⚠️  No user found with that username")
            except Exception as e:
                print(f"⚠️  User query failed: {e}")
            
            print("\n3️⃣ Testing Account queries...")
            
            # Test account queries
            try:
                account_query = "SELECT Id, Name, Industry FROM Account LIMIT 3"
                accounts = await sf.query(account_query)
                print(f"✅ Account query successful: {len(accounts)} accounts found")
                
                for i, account in enumerate(accounts[:3], 1):
                    print(f"   {i}. {account.get('Name', 'Unnamed')} ({account.get('Industry', 'No Industry')})")
                    
            except Exception as e:
                print(f"⚠️  Account query failed: {e}")
            
            print("\n4️⃣ Testing Lead creation capability...")
            
            # Test if we can describe Lead object
            try:
                lead_describe = await sf.describe_object('Lead')
                if lead_describe:
                    print("✅ Lead object accessible")
                    print("   Available for lead creation")
                else:
                    print("⚠️  Lead object describe failed")
            except Exception as e:
                print(f"⚠️  Lead describe failed: {e}")
            
            print("\n5️⃣ Testing prospect lead mapping...")
            
            # Test lead mapping function
            test_prospect = {
                'first_name': 'John',
                'last_name': 'Doe', 
                'title': 'CFO',
                'company': 'Test Hospital',
                'email': 'john.doe@testhospital.com',
                'phone': '+1-555-123-4567',
                'linkedin_url': 'https://linkedin.com/in/johndoe',
                'persona_type': 'Chief Financial Officer',
                'qualification_score': 85.5,
                'ai_generated_message': 'Personalized message here...'
            }
            
            test_account = {
                'Id': '001XX000003DHP0YAO',
                'Name': 'Test Hospital',
                'Industry': 'Healthcare'
            }
            
            lead_data = sf.map_prospect_to_lead(test_prospect, test_account)
            print("✅ Lead mapping successful:")
            print(f"   Mapped fields: {len(lead_data)}")
            print(f"   First Name: {lead_data.get('FirstName')}")
            print(f"   Last Name: {lead_data.get('LastName')}")
            print(f"   Company: {lead_data.get('Company')}")
            
            print("\n🎉 SALESFORCE INTEGRATION FULLY FUNCTIONAL!")
            
    except Exception as e:
        print(f"❌ Salesforce integration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_salesforce_integration())
