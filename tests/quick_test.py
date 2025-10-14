#!/usr/bin/env python3
"""
Quick LinkedIn Prospect Discovery Test - Real-time feedback
"""

import requests
import json
import time

def test_cleveland_clinic():
    """Quick test with Cleveland Clinic"""
    
    print("🧪 Quick LinkedIn Prospect Discovery Test")
    print("=" * 50)
    
    # Test data
    request_data = {
        "company_name": "Cleveland Clinic",
        "target_titles": [
            "Director of Facilities",
            "CFO", 
            "Energy Manager",
            "Facilities Manager",
            "Chief Financial Officer"
        ]
    }
    
    print(f"🏥 Testing: {request_data['company_name']}")
    print(f"🎯 Target Titles: {len(request_data['target_titles'])}")
    print()
    
    try:
        print("📤 Sending request to local API...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8001/discover-prospects",
            json=request_data,
            timeout=180
        )
        
        end_time = time.time()
        print(f"📥 Response received in {end_time - start_time:.1f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                result_data = data.get('data', {})
                prospects = result_data.get('qualified_prospects', [])
                pipeline = result_data.get('pipeline_summary', {})
                costs = result_data.get('cost_estimates', {})
                
                print(f"\n✅ SUCCESS!")
                print(f"   Prospects found: {len(prospects)}")
                print(f"   Pipeline: {pipeline.get('search_results_found', 0)} → {len(prospects)}")
                print(f"   Cost: ${costs.get('total_estimated', 0):.4f}")
                
                print(f"\n🎯 Prospects Found:")
                for i, prospect in enumerate(prospects[:5]):  # Show first 5
                    linkedin_summary = prospect.get('linkedin_summary', {})
                    print(f"   {i+1}. {linkedin_summary.get('name', 'N/A')} - {prospect.get('qualification_score', 0)}/100")
                    print(f"      Title: {linkedin_summary.get('job_title', 'N/A')}")
                    print(f"      Company: {linkedin_summary.get('company', 'N/A')}")
                    print(f"      LinkedIn: {prospect.get('linkedin_url', 'N/A')}")
                    print()
                
                return True
            else:
                print(f"❌ API Error: {data.get('detail', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local API")
        print("   Make sure server is running on http://localhost:8001")
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>3 minutes)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_cleveland_clinic()
    
    if success:
        print("🚀 Local LinkedIn prospect discovery is working perfectly!")
    else:
        print("⚠️  Test failed - check server and try again")
