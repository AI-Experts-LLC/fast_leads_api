#!/usr/bin/env python3
"""
Test LinkedIn scraping functionality using the fast_leads_api public API

This script tests LinkedIn profile scraping for:
- linkedin.com/in/lucaserb
- https://www.linkedin.com/in/emollick/

Uses the public API at: https://fast-leads-api.up.railway.app/
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any

# API Configuration
API_BASE_URL = "https://fast-leads-api.up.railway.app"

def test_api_connection() -> bool:
    """Test if the API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ API Connection Successful")
        print(f"   Service: {data.get('service')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Timestamp: {data.get('timestamp')}")
        return True
        
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        return False

def test_health_check() -> bool:
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Health Check Successful")
        print(f"   Status: {data.get('status')}")
        print(f"   Environment: {data.get('environment')}")
        return True
        
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_linkedin_service() -> Dict[str, Any]:
    """Test LinkedIn service status"""
    try:
        print(f"\n🔍 Testing LinkedIn Service Status...")
        
        response = requests.get(f"{API_BASE_URL}/linkedin/test", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ LinkedIn Service Test Response:")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
        
        if data.get('error'):
            print(f"   Error: {data.get('error')}")
        
        return data
        
    except Exception as e:
        print(f"❌ LinkedIn Service Test Failed: {e}")
        return {"success": False, "error": str(e)}

def test_linkedin_scraping(linkedin_urls: list, profile_names: list) -> Dict[str, Any]:
    """
    Test LinkedIn scraping with the new direct endpoint
    """
    try:
        print(f"\n🔍 Testing LinkedIn Scraping...")
        print(f"   Profiles: {', '.join(profile_names)}")
        print(f"   URLs: {linkedin_urls}")
        
        # Prepare the request
        request_data = {
            "linkedin_urls": linkedin_urls,
            "include_detailed_data": True
        }
        
        # Make the API call
        response = requests.post(
            f"{API_BASE_URL}/linkedin/scrape-profiles",
            json=request_data,
            timeout=60  # LinkedIn scraping can take time
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ LinkedIn Scraping Response:")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
        
        # Parse the response data
        if 'data' in data and data['data'].get('success'):
            scraping_data = data['data']
            print(f"   Profiles Requested: {scraping_data.get('profiles_requested', 0)}")
            print(f"   Profiles Scraped: {scraping_data.get('profiles_scraped', 0)}")
            print(f"   Cost Estimate: ${scraping_data.get('cost_estimate', 0):.2f}")
            
            # Show profile summaries
            profiles = scraping_data.get('profiles', [])
            for i, profile in enumerate(profiles):
                print(f"\n   📋 Profile {i+1}:")
                print(f"      Name: {profile.get('name', 'N/A')}")
                print(f"      Headline: {profile.get('headline', 'N/A')}")
                print(f"      Company: {profile.get('company', 'N/A')}")
                print(f"      Location: {profile.get('location', 'N/A')}")
                print(f"      Experience Count: {profile.get('experience_count', 0)}")
                print(f"      Skills Count: {profile.get('skills_count', 0)}")
                
        return data
        
    except Exception as e:
        print(f"❌ LinkedIn Scraping Failed: {e}")
        return {"success": False, "error": str(e)}

def create_direct_linkedin_test_request(linkedin_urls: list) -> Dict[str, Any]:
    """
    Create a mock request to test LinkedIn functionality directly
    This would require adding an endpoint to the API
    """
    print(f"\n📋 Direct LinkedIn Test Request (for API enhancement)")
    print(f"   URLs to test: {linkedin_urls}")
    
    # This is what the request would look like if we had a direct endpoint
    mock_request = {
        "endpoint": "POST /linkedin/scrape-profiles",
        "request_body": {
            "linkedin_urls": linkedin_urls,
            "include_detailed_data": True
        },
        "expected_response": {
            "success": True,
            "profiles_requested": len(linkedin_urls),
            "profiles_scraped": "number",
            "profiles": [
                {
                    "url": "profile_url",
                    "name": "full_name",
                    "headline": "professional_headline",
                    "company": "current_company",
                    "location": "location",
                    "summary": "about_section",
                    "experience": [],
                    "education": [],
                    "skills": []
                }
            ]
        }
    }
    
    print(f"   Mock Request Structure:")
    print(json.dumps(mock_request, indent=2))
    
    return mock_request

def suggest_api_enhancement() -> None:
    """Suggest how to add LinkedIn endpoint to the API"""
    print(f"\n💡 API Enhancement Suggestion:")
    print(f"   To enable direct LinkedIn testing, add this endpoint to main.py:")
    print(f"""
@app.post("/linkedin/scrape-profiles")
async def scrape_linkedin_profiles(request: dict):
    '''Scrape LinkedIn profiles directly'''
    try:
        linkedin_urls = request.get("linkedin_urls", [])
        if not linkedin_urls:
            raise HTTPException(
                status_code=400,
                detail="linkedin_urls is required"
            )
        
        result = await linkedin_service.scrape_profiles(linkedin_urls)
        
        if result.get("success"):
            return {{
                "status": "success",
                "message": "LinkedIn profiles scraped successfully",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"LinkedIn scraping failed: {{result.get('error', 'Unknown error')}}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping LinkedIn profiles: {{str(e)}}"
        )
    """)

def main():
    """Main testing function"""
    print("🚀 LinkedIn Scraping Test - Fast Leads API")
    print("=" * 50)
    
    # Test profiles
    test_profiles = [
        {
            "url": "https://www.linkedin.com/in/lucaserb/",
            "name": "Lucas Erb"
        },
        {
            "url": "https://www.linkedin.com/in/emollick/",
            "name": "Ethan Mollick"
        }
    ]
    
    # Step 1: Test API connection
    print("\n1️⃣ Testing API Connection...")
    if not test_api_connection():
        print("❌ Cannot proceed - API not accessible")
        sys.exit(1)
    
    # Step 2: Test health check
    print("\n2️⃣ Testing Health Check...")
    test_health_check()
    
    # Step 3: Test LinkedIn service
    print("\n3️⃣ Testing LinkedIn Service...")
    linkedin_service_result = test_linkedin_service()
    
    # Step 4: Test LinkedIn scraping functionality
    print("\n4️⃣ Testing LinkedIn Scraping...")
    linkedin_urls = [profile["url"] for profile in test_profiles]
    profile_names = [profile["name"] for profile in test_profiles]
    
    scraping_result = test_linkedin_scraping(linkedin_urls, profile_names)
    
    # Step 5: Analyze results
    print("\n5️⃣ Results Analysis...")
    if scraping_result.get('status') == 'success':
        print("✅ LinkedIn scraping completed successfully!")
        
        # Check if we got profile data
        data = scraping_result.get('data', {})
        if data.get('success'):
            profiles = data.get('profiles', [])
            print(f"   Successfully scraped {len(profiles)} profiles")
            
            # Show detailed results for each profile
            for i, profile in enumerate(profiles):
                print(f"\n   🎯 Detailed Profile {i+1} Results:")
                print(f"      URL: {profile.get('url', 'N/A')}")
                print(f"      Full Name: {profile.get('name', 'N/A')}")
                print(f"      First Name: {profile.get('first_name', 'N/A')}")
                print(f"      Last Name: {profile.get('last_name', 'N/A')}")
                print(f"      Headline: {profile.get('headline', 'N/A')}")
                print(f"      Current Company: {profile.get('company', 'N/A')}")
                print(f"      Job Title: {profile.get('job_title', 'N/A')}")
                print(f"      Location: {profile.get('location', 'N/A')}")
                print(f"      Connections: {profile.get('connections', 'N/A')}")
                print(f"      Followers: {profile.get('followers', 'N/A')}")
                print(f"      Top Skills: {profile.get('top_skills_by_endorsements', 'N/A')}")
                
                # Show experience summary
                experience = profile.get('experience', [])
                if experience:
                    print(f"      Recent Experience:")
                    for exp in experience[:3]:  # Show top 3
                        print(f"        • {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
                
                # Show education summary
                education = profile.get('education', [])
                if education:
                    print(f"      Education:")
                    for edu in education[:2]:  # Show top 2
                        print(f"        • {edu.get('degree', 'N/A')} from {edu.get('school', 'N/A')}")
        else:
            print(f"⚠️  Scraping completed but with issues: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ LinkedIn scraping failed: {scraping_result.get('error', 'Unknown error')}")
    
    # Step 6: Show comparison
    print("\n6️⃣ Profile Comparison...")
    if scraping_result.get('status') == 'success':
        data = scraping_result.get('data', {})
        profiles = data.get('profiles', [])
        
        if len(profiles) >= 2:
            print("   Comparing the two profiles:")
            print(f"   Profile 1 ({profiles[0].get('name', 'Unknown')}):")
            print(f"     Company: {profiles[0].get('company', 'N/A')}")
            print(f"     Title: {profiles[0].get('job_title', 'N/A')}")
            print(f"     Connections: {profiles[0].get('connections', 'N/A')}")
            
            print(f"   Profile 2 ({profiles[1].get('name', 'Unknown')}):")
            print(f"     Company: {profiles[1].get('company', 'N/A')}")
            print(f"     Title: {profiles[1].get('job_title', 'N/A')}")
            print(f"     Connections: {profiles[1].get('connections', 'N/A')}")
        else:
            print("   Not enough profiles for comparison")
    
    print(f"\n📊 Test Summary:")
    print(f"   API Status: ✅ Accessible")
    print(f"   LinkedIn Service: {linkedin_service_result.get('status', 'Unknown')}")
    if scraping_result.get('status') == 'success':
        data = scraping_result.get('data', {})
        print(f"   LinkedIn Scraping: ✅ Successful")
        print(f"   Profiles Scraped: {data.get('profiles_scraped', 0)}/{data.get('profiles_requested', 0)}")
        print(f"   Cost Estimate: ${data.get('cost_estimate', 0):.2f}")
    else:
        print(f"   LinkedIn Scraping: ❌ Failed")
        print(f"   Error: {scraping_result.get('error', 'Unknown')}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Ensure APIFY_API_TOKEN is set in Railway environment")
    print(f"   2. Test individual profiles if batch scraping fails")
    print(f"   3. Check Apify actor limits and billing")
    print(f"   4. Use scraped data for lead qualification")

if __name__ == "__main__":
    main()
