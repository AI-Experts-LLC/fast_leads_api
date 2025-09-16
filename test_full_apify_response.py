#!/usr/bin/env python3
"""
Test script to show the complete raw Apify response data
This will help us understand if we're missing data in our parsing
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "https://fast-leads-api.up.railway.app"

def test_linkedin_with_full_response():
    """Test LinkedIn scraping and show complete raw response"""
    
    test_profiles = [
        "https://www.linkedin.com/in/lucaserb/",
        "https://www.linkedin.com/in/emollick/"
    ]
    
    print("🔍 Testing LinkedIn Scraping with Full Response Data")
    print("=" * 60)
    print(f"Profiles to test: {test_profiles}")
    
    try:
        # Prepare the request
        request_data = {
            "linkedin_urls": test_profiles,
            "include_detailed_data": True
        }
        
        print(f"\n📤 Request being sent:")
        print(json.dumps(request_data, indent=2))
        
        # Make the API call
        response = requests.post(
            f"{API_BASE_URL}/linkedin/scrape-profiles",
            json=request_data,
            timeout=90
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 High-Level Response Structure:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            
            # Show the full response structure
            print(f"\n🗂️  Full Response JSON:")
            print("=" * 50)
            print(json.dumps(data, indent=2, default=str))
            print("=" * 50)
            
            # Now let's dive into the profiles data specifically
            if 'data' in data and data['data'].get('profiles'):
                profiles = data['data']['profiles']
                
                print(f"\n🔍 Detailed Profile Analysis:")
                print(f"Found {len(profiles)} profiles")
                
                for i, profile in enumerate(profiles):
                    print(f"\n📋 Profile {i+1} - Complete Raw Data:")
                    print("-" * 40)
                    
                    # Show all top-level keys first
                    print(f"Available fields: {list(profile.keys())}")
                    
                    # Show each field with its value
                    for key, value in profile.items():
                        if key == 'raw_data':
                            print(f"\n🔴 RAW_DATA SECTION (This contains the original Apify data):")
                            if value:
                                print(json.dumps(value, indent=4, default=str))
                            else:
                                print("   No raw_data found")
                        elif isinstance(value, (list, dict)):
                            print(f"\n{key}: {json.dumps(value, indent=2, default=str)}")
                        else:
                            print(f"{key}: {value}")
                    
                    print("-" * 40)
            
            # Check if there's additional data we might be missing
            if 'data' in data:
                scraping_data = data['data']
                print(f"\n🔧 Scraping Metadata:")
                print(f"   Success: {scraping_data.get('success')}")
                print(f"   Profiles Requested: {scraping_data.get('profiles_requested')}")
                print(f"   Profiles Scraped: {scraping_data.get('profiles_scraped')}")
                print(f"   Run ID: {scraping_data.get('run_id')}")
                print(f"   Cost Estimate: ${scraping_data.get('cost_estimate', 0):.2f}")
                
                # Check for any error messages
                if scraping_data.get('error'):
                    print(f"   Error: {scraping_data['error']}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response (raw): {response.text}")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

def test_single_profile(url):
    """Test a single profile to see if that gives more data"""
    print(f"\n🎯 Testing Single Profile: {url}")
    print("-" * 50)
    
    try:
        request_data = {
            "linkedin_urls": [url],
            "include_detailed_data": True
        }
        
        response = requests.post(
            f"{API_BASE_URL}/linkedin/scrape-profiles",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data'].get('profiles'):
                profile = data['data']['profiles'][0]
                
                print(f"📊 Single Profile Results for {url}:")
                print(f"   Name: {profile.get('name', 'N/A')}")
                print(f"   Headline: {profile.get('headline', 'N/A')}")
                print(f"   Company: {profile.get('company', 'N/A')}")
                print(f"   Location: {profile.get('location', 'N/A')}")
                print(f"   Summary length: {len(profile.get('summary', '') or '')}")
                print(f"   Experience entries: {len(profile.get('experience', []))}")
                print(f"   Education entries: {len(profile.get('education', []))}")
                print(f"   Skills entries: {len(profile.get('skills', []))}")
                
                # Show if raw_data has more information
                raw_data = profile.get('raw_data', {})
                if raw_data:
                    print(f"   Raw data keys: {list(raw_data.keys())}")
                    print(f"   Raw fullName: {raw_data.get('fullName')}")
                    print(f"   Raw about: {raw_data.get('about', 'N/A')[:100]}...")
                
                return profile
            else:
                print(f"❌ No profile data returned")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Single profile test failed: {e}")
    
    return None

def main():
    """Main function to run full response analysis"""
    print("🔬 Full Apify Response Analysis")
    print("=" * 60)
    
    # Test 1: Full batch request with complete response
    test_linkedin_with_full_response()
    
    # Test 2: Individual profiles to compare
    print(f"\n" + "="*60)
    print("🎯 INDIVIDUAL PROFILE TESTS")
    print("="*60)
    
    lucaserb_profile = test_single_profile("https://www.linkedin.com/in/lucaserb/")
    emollick_profile = test_single_profile("https://www.linkedin.com/in/emollick/")
    
    # Test 3: Summary analysis
    print(f"\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"This analysis will show:")
    print(f"1. The complete JSON structure returned by our API")
    print(f"2. All raw Apify data that's being captured")
    print(f"3. Whether our parsing is missing any available data")
    print(f"4. Differences between batch vs individual requests")
    
    print(f"\n💡 If the data still seems sparse, possible causes:")
    print(f"   • LinkedIn privacy settings limiting data access")
    print(f"   • Apify actor rate limiting or anti-scraping measures")
    print(f"   • Profile-specific restrictions")
    print(f"   • Our parsing logic missing some fields")

if __name__ == "__main__":
    main()
