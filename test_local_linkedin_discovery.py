#!/usr/bin/env python3
"""
Local LinkedIn Prospect Discovery Test
Tests the prospect discovery API running locally
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Local API Configuration
LOCAL_API_URL = "http://localhost:8001"

# Test hospitals for prospect discovery
TEST_HOSPITALS = [
    {
        "name": "Cleveland Clinic",
        "description": "Large prestigious hospital system"
    },
    {
        "name": "Johns Hopkins Hospital",
        "description": "Top-tier academic medical center"
    },
    {
        "name": "Mayo Clinic Rochester",
        "description": "World-renowned medical facility"
    }
]

# Target titles for healthcare decision makers
TARGET_TITLES = [
    "Director of Facilities",
    "CFO", 
    "COO",
    "VP Operations",
    "Energy Manager",
    "Facilities Manager",
    "Chief Financial Officer",
    "Director of Engineering",
    "Plant Operations",
    "Maintenance Manager"
]

class LocalLinkedInTest:
    """Test the local prospect discovery API"""
    
    def __init__(self):
        self.api_url = LOCAL_API_URL
        self.results = []
        
    def check_api_health(self) -> bool:
        """Check if the local API is running"""
        try:
            print("🔍 Checking local API health...")
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                print("✅ Local API is running and healthy")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to local API - is it running?")
            print("   Start with: uvicorn main:app --reload")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_single_hospital(self, hospital: Dict[str, Any]) -> Dict[str, Any]:
        """Test prospect discovery for a single hospital"""
        
        hospital_name = hospital["name"]
        print(f"\n🏥 Testing: {hospital_name}")
        print(f"   Description: {hospital['description']}")
        print(f"   Target Titles: {len(TARGET_TITLES)}")
        
        request_data = {
            "company_name": hospital_name,
            "target_titles": TARGET_TITLES
        }
        
        try:
            print("   ⏰ Starting prospect discovery...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/discover-prospects",
                json=request_data,
                timeout=120  # 2 minutes
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"   📥 Response received in {response_time:.1f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    result_data = data.get('data', {})
                    prospects = result_data.get('qualified_prospects', [])
                    pipeline = result_data.get('pipeline_summary', {})
                    costs = result_data.get('cost_estimates', {})
                    
                    print(f"   ✅ SUCCESS!")
                    print(f"      Prospects found: {len(prospects)}")
                    print(f"      Pipeline: {pipeline.get('search_results_found', 0)} → {len(prospects)}")
                    print(f"      Cost: ${costs.get('total_estimated', 0):.4f}")
                    
                    # Show prospect details
                    print(f"   🎯 Prospects:")
                    for i, prospect in enumerate(prospects):
                        linkedin_summary = prospect.get('linkedin_summary', {})
                        linkedin_data = prospect.get('linkedin_data', {})
                        
                        print(f"      {i+1}. {linkedin_summary.get('name', 'N/A')} - {prospect.get('qualification_score', 0)}/100")
                        print(f"         Role: {prospect.get('persona_match', 'N/A')}")
                        print(f"         Company: {linkedin_summary.get('company', 'N/A')}")
                        print(f"         Authority: {prospect.get('decision_authority', 'N/A')}")
                        print(f"         LinkedIn URL: {prospect.get('linkedin_url', 'N/A')}")
                        print(f"         LinkedIn Data Fields: {len(linkedin_data)}")
                        
                        # Show key LinkedIn intelligence
                        if linkedin_summary:
                            print(f"         Intelligence:")
                            print(f"           • Experience: {linkedin_summary.get('total_experience_years', 'N/A')} years")
                            print(f"           • Authority Score: {linkedin_summary.get('professional_authority_score', 'N/A')}")
                            print(f"           • Connections: {linkedin_summary.get('connections', 'N/A')}")
                            print(f"           • Education: {linkedin_summary.get('highest_degree', 'N/A')}")
                        print()
                    
                    return {
                        "success": True,
                        "hospital": hospital_name,
                        "prospects_count": len(prospects),
                        "response_time": response_time,
                        "cost": costs.get('total_estimated', 0),
                        "pipeline": pipeline,
                        "prospects": prospects
                    }
                    
                else:
                    print(f"   ❌ API Error: {data.get('detail', 'Unknown error')}")
                    return {"success": False, "error": data.get('detail', 'Unknown error')}
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"      Error: {error_data}")
                except:
                    print(f"      Error: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out (>2 minutes)")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run tests on all hospitals"""
        
        print("🧪 Local LinkedIn Prospect Discovery Test")
        print("=" * 50)
        print(f"API URL: {self.api_url}")
        print(f"Hospitals to test: {len(TEST_HOSPITALS)}")
        print()
        
        # Check API health first
        if not self.check_api_health():
            print("\n💡 To start the local API:")
            print("   cd /Users/lucaserb/Documents/MetrusEnergy/fast_leads_api")
            print("   uvicorn main:app --reload")
            return
        
        successful_tests = 0
        total_prospects = 0
        total_cost = 0
        
        for i, hospital in enumerate(TEST_HOSPITALS, 1):
            print(f"\n📋 Test {i}/{len(TEST_HOSPITALS)}")
            
            result = self.test_single_hospital(hospital)
            self.results.append(result)
            
            if result.get("success"):
                successful_tests += 1
                total_prospects += result.get("prospects_count", 0)
                total_cost += result.get("cost", 0)
            
            # Brief pause between tests
            if i < len(TEST_HOSPITALS):
                print("   ⏳ Waiting 5 seconds before next test...")
                time.sleep(5)
        
        print(f"\n🎯 LOCAL TEST RESULTS")
        print("=" * 30)
        print(f"✅ Successful tests: {successful_tests}/{len(TEST_HOSPITALS)}")
        print(f"📊 Total prospects found: {total_prospects}")
        print(f"💰 Total cost: ${total_cost:.4f}")
        if successful_tests > 0:
            print(f"📈 Average prospects per hospital: {total_prospects/successful_tests:.1f}")
        
        # Show detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.results:
            if result.get("success"):
                hospital = result.get("hospital")
                prospects = result.get("prospects_count", 0)
                cost = result.get("cost", 0)
                time_taken = result.get("response_time", 0)
                
                print(f"   {hospital}: {prospects} prospects, ${cost:.4f}, {time_taken:.1f}s")
            else:
                hospital = result.get("hospital", "Unknown")
                error = result.get("error", "Unknown error")
                print(f"   {hospital}: FAILED - {error}")
        
        if successful_tests > 0:
            print(f"\n🚀 Local prospect discovery system is working!")
            print(f"   Ready for production use or further testing")
        else:
            print(f"\n⚠️  All tests failed - check API configuration")

def main():
    """Main test execution"""
    tester = LocalLinkedInTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
