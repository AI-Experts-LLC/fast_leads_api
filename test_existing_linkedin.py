#!/usr/bin/env python3
"""
Test LinkedIn functionality using existing deployed API endpoints
Since the new LinkedIn endpoints aren't deployed yet, we'll use the prospect discovery
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "https://fast-leads-api.up.railway.app"

def test_prospect_discovery_with_company():
    """Test LinkedIn functionality through prospect discovery endpoint"""
    print("🔍 Testing LinkedIn functionality via prospect discovery...")
    
    # Use a company that should have LinkedIn profiles
    request_data = {
        "company_name": "Apple Inc",
        "target_titles": ["Software Engineer", "Product Manager"]
    }
    
    try:
        print(f"   Testing with company: {request_data['company_name']}")
        print(f"   Target titles: {request_data['target_titles']}")
        
        response = requests.post(
            f"{API_BASE_URL}/discover-prospects",
            json=request_data,
            timeout=120  # Longer timeout for full pipeline
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Prospect discovery successful!")
            
            # Check if LinkedIn functionality worked
            if 'data' in data:
                pipeline_data = data['data']
                print(f"   Search results found: {pipeline_data.get('pipeline_summary', {}).get('search_results_found', 0)}")
                print(f"   Prospects qualified: {pipeline_data.get('pipeline_summary', {}).get('prospects_qualified', 0)}")
                print(f"   LinkedIn profiles scraped: {pipeline_data.get('pipeline_summary', {}).get('linkedin_profiles_scraped', 0)}")
                
                # Show qualified prospects
                prospects = pipeline_data.get('qualified_prospects', [])
                if prospects:
                    print(f"\n   📋 Found {len(prospects)} qualified prospects:")
                    for i, prospect in enumerate(prospects[:2]):  # Show first 2
                        print(f"      {i+1}. {prospect.get('linkedin_data', {}).get('name', 'N/A')}")
                        print(f"         Title: {prospect.get('linkedin_data', {}).get('headline', 'N/A')}")
                        print(f"         Score: {prospect.get('qualification_score', 'N/A')}")
                        print(f"         LinkedIn: {prospect.get('linkedin_url', 'N/A')}")
                
                return True
            else:
                print("⚠️  No data in response")
                return False
        else:
            error_data = response.json() if response.content else {}
            print(f"❌ Request failed: {error_data.get('detail', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_environment_variables():
    """Check if required environment variables are configured"""
    print("\n🔧 Checking environment configuration...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/debug/environment", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            env_vars = data.get('environment_variables', {})
            
            print("   Environment status:")
            print(f"      SALESFORCE_USERNAME: {'✅' if env_vars.get('SALESFORCE_USERNAME') else '❌'}")
            print(f"      EDFX_USERNAME: {'✅' if env_vars.get('EDFX_USERNAME') else '❌'}")
            print(f"      Total env vars: {env_vars.get('total_env_vars', 0)}")
            
            # Note: We can't see APIFY_API_TOKEN directly for security, but it would be needed
            print(f"      Note: APIFY_API_TOKEN status not visible for security")
            
            return True
        else:
            print(f"   ❌ Environment check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Environment check error: {e}")
        return False

def main():
    """Main testing function"""
    print("🔗 Testing LinkedIn Functionality - Existing API")
    print("=" * 55)
    
    # Test 1: Basic API connection
    print("\n1️⃣ Testing API Connection...")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accessible - {data.get('service')}")
        else:
            print(f"❌ API not accessible: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Test 2: Environment check
    test_environment_variables()
    
    # Test 3: LinkedIn via prospect discovery
    print("\n2️⃣ Testing LinkedIn via Prospect Discovery...")
    linkedin_works = test_prospect_discovery_with_company()
    
    # Summary and next steps
    print(f"\n📊 Test Results:")
    print(f"   API Status: ✅ Accessible")
    print(f"   LinkedIn Functionality: {'✅ Working' if linkedin_works else '❌ Issues detected'}")
    
    print(f"\n🚀 To test your specific LinkedIn profiles:")
    print(f"   1. Deploy the updated API with new LinkedIn endpoints")
    print(f"   2. Ensure APIFY_API_TOKEN is set in Railway environment")
    print(f"   3. Use the new /linkedin/scrape-profiles endpoint")
    
    print(f"\n📋 Test URLs ready for deployment:")
    print(f"   • https://www.linkedin.com/in/lucaserb/")
    print(f"   • https://www.linkedin.com/in/emollick/")

if __name__ == "__main__":
    main()
