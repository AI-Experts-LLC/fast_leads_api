#!/usr/bin/env python3
"""
Test the batch prospect discovery with just one hospital first
"""

import requests
import json
import time

API_BASE_URL = "https://fast-leads-api.up.railway.app"

TARGET_TITLES = [
    "Director of Facilities", "CFO", "COO", "VP Operations",
    "Energy Manager", "Facilities Manager", "Chief Financial Officer", 
    "Director of Engineering", "Plant Operations", "Maintenance Manager"
]

def test_api_health():
    """Test if API is responsive"""
    try:
        print("🔍 Testing API health...")
        response = requests.get(f"{API_BASE_URL}/health", timeout=60)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ API is responsive")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API unreachable: {e}")
        return False

def test_single_hospital():
    """Test with one hospital first"""
    
    test_hospital = {
        "name": "MAYO CLINIC HOSPITAL",
        "city": "PHOENIX",
        "state": "AZ",
        "beds": 280
    }
    
    print("🧪 Testing Batch Process with Single Hospital")
    print("=" * 50)
    print(f"Hospital: {test_hospital['name']}")
    print(f"Target Titles: {len(TARGET_TITLES)}")
    print()
    
    # Test API health first
    if not test_api_health():
        return False
    
    request_data = {
        "company_name": test_hospital["name"],
        "target_titles": TARGET_TITLES[:3]  # Use fewer titles for faster testing
    }
    
    # Try the improved endpoint first (it's more reliable)
    endpoint = "/discover-prospects-improved"
    
    try:
        print(f"\n📤 Testing endpoint: {endpoint}")
        print(f"🔍 Searching for: {', '.join(request_data['target_titles'])}")
        print(f"⏱️  This may take 5-15 minutes (LinkedIn search + scraping + AI qualification)")
        print(f"📊 Progress will be shown as the process runs...")
        
        start_time = time.time()
        
        # Much longer timeout for the full process
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=request_data,
            timeout=900  # 15 minutes timeout
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n📥 Response received in {response_time/60:.1f} minutes ({response_time:.1f} seconds)")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print the COMPLETE JSON response for analysis
            print(f"\n🔍 COMPLETE API RESPONSE JSON:")
            print("=" * 100)
            full_json = json.dumps(data, indent=2, default=str)
            if len(full_json) > 4000:
                print(full_json[:4000])
                print(f"\n... [Response truncated - showing first 4000 chars of {len(full_json)} total]")
                print("=" * 100)
            else:
                print(full_json)
                print("=" * 100)
            
            if data.get('status') == 'success':
                result_data = data.get('data', {})
                prospects = result_data.get('qualified_prospects', [])
                pipeline = result_data.get('pipeline_summary', {})
                costs = result_data.get('cost_estimates', {})
                
                print(f"\n✅ SUCCESS with {endpoint}!")
                print(f"   Prospects found: {len(prospects)}")
                print(f"   Pipeline: {pipeline.get('search_results_found', 0)} → {len(prospects)}")
                print(f"   Cost: ${costs.get('total_estimated', 0):.4f}")
                
                print(f"\n🎯 Prospects Preview:")
                for i, prospect in enumerate(prospects[:3]):  # Show top 3
                    linkedin_data = prospect.get('linkedin_data', {})
                    ai_ranking = prospect.get('ai_ranking', {})
                    # Check both formats for compatibility
                    linkedin_summary = prospect.get('linkedin_summary', {})
                    
                    name = linkedin_data.get('name') or linkedin_summary.get('name', 'N/A')
                    score = ai_ranking.get('ranking_score') or prospect.get('qualification_score', 0)
                    persona = ai_ranking.get('persona_category') or prospect.get('persona_match', 'N/A')
                    company = linkedin_data.get('company') or linkedin_summary.get('company', 'N/A')
                    
                    print(f"   {i+1}. {name} - {score}/100")
                    print(f"      Role: {persona}")
                    print(f"      Company: {company}")
                
                print(f"\n📊 Sample CSV Data Structure:")
                if prospects:
                    sample_prospect = prospects[0]
                    linkedin_data = sample_prospect.get('linkedin_data', {})
                    ai_ranking = sample_prospect.get('ai_ranking', {})
                    linkedin_summary = sample_prospect.get('linkedin_summary', {})
                    
                    name = linkedin_data.get('name') or linkedin_summary.get('name', 'N/A')
                    title = linkedin_data.get('job_title') or linkedin_summary.get('job_title', 'N/A')
                    score = ai_ranking.get('ranking_score') or sample_prospect.get('qualification_score', 0)
                    
                    print(f"   Hospital: {test_hospital['name']}")
                    print(f"   Location: {test_hospital['city']}, {test_hospital['state']}")
                    print(f"   Name: {name}")
                    print(f"   Title: {title}")
                    print(f"   Score: {score}")
                    print(f"   LinkedIn Data Fields: {len(sample_prospect.get('linkedin_data', {}))}")
                    print(f"   AI Ranking Fields: {len(sample_prospect.get('ai_ranking', {}))}")
                
                print(f"\n🚀 {endpoint} endpoint working!")
                return True
                
            else:
                print(f"❌ API Error from {endpoint}: {data.get('detail', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error from {endpoint}: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error with {endpoint}: {e}")
        return False

def main():
    """Main test"""
    success = test_single_hospital()
    
    if success:
        print(f"\n🎯 Test successful! Ready to run full batch:")
        print(f"   python batch_hospital_prospect_discovery.py")
    else:
        print(f"\n⚠️  Test failed - check API before running full batch")

if __name__ == "__main__":
    main()
