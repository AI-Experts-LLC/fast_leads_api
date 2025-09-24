#!/usr/bin/env python3
"""
Test the prospect discovery API on multiple hospitals and save complete JSON responses
"""

import requests
import json
import time
import os
from datetime import datetime

API_BASE_URL = "https://fast-leads-api.up.railway.app"

# Target hospitals from the enhanced list (testing larger hospitals for more diversity)
TEST_HOSPITALS = [
    {
        "name": "CLEVELAND CLINIC", 
        "city": "CLEVELAND",
        "state": "OH",
        "beds": 1285,
        "type": "Large Academic Medical Center"
    }
]

TARGET_TITLES = [
    "Director of Facilities", "CFO", "Chief Financial Officer", 
    "Sustainability Manager", "Energy Manager", "Chief Operating Officer", "Facilities Manager"
]

def create_output_directory():
    """Create output directory for JSON responses"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"hospital_prospect_testing_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def test_api_health():
    """Test if API is responsive"""
    try:
        print("🔍 Testing API health...")
        response = requests.get(f"{API_BASE_URL}/health", timeout=60)
        if response.status_code == 200:
            print("✅ API is responsive")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API unreachable: {e}")
        return False

def test_hospital(hospital, output_dir):
    """Test prospect discovery for a single hospital"""
    print(f"\n🏥 Testing: {hospital['name']}")
    print(f"📍 Location: {hospital['city']}, {hospital['state']}")
    print(f"🛏️  Beds: {hospital['beds']} ({hospital['type']})")
    print("-" * 80)
    
    request_data = {
        "company_name": hospital["name"],
        "target_titles": TARGET_TITLES,
        "company_city": hospital["city"],
        "company_state": hospital["state"]
    }
    
    try:
        print(f"📤 Making API request...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/discover-prospects-improved",
            json=request_data,
            timeout=600  # 10 minutes timeout
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"📥 Response received in {response_time:.1f} seconds")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Save complete JSON response to file
            safe_name = hospital["name"].replace(" ", "_").replace("-", "_").replace("/", "_")
            filename = f"{output_dir}/{safe_name}_complete_response.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"💾 Complete JSON saved to: {filename}")
            
            # Extract and display key metrics
            if data.get('status') == 'success':
                result_data = data.get('data', {})
                prospects = result_data.get('qualified_prospects', [])
                pipeline = result_data.get('pipeline_summary', {})
                costs = result_data.get('cost_estimates', {})
                
                print(f"\n✅ SUCCESS!")
                print(f"   Prospects found: {len(prospects)}")
                print(f"   Pipeline: {pipeline.get('search_results_found', 0)} → {len(prospects)}")
                print(f"   Cost: ${costs.get('total_estimated', 0):.2f}")
                
                # Show top prospects
                if prospects:
                    print(f"\n🎯 Top Prospects:")
                    for i, prospect in enumerate(prospects[:3]):
                        linkedin_data = prospect.get('linkedin_data', {})
                        ai_ranking = prospect.get('ai_ranking', {})
                        
                        name = linkedin_data.get('name', 'N/A')
                        title = linkedin_data.get('job_title', 'N/A')
                        score = ai_ranking.get('ranking_score', 0)
                        persona = ai_ranking.get('persona_category', 'N/A')
                        
                        print(f"   {i+1}. {name} - {score}/100")
                        print(f"      Title: {title}")
                        print(f"      Persona: {persona}")
                
                return {
                    "success": True,
                    "hospital": hospital["name"],
                    "prospects_found": len(prospects),
                    "cost": costs.get('total_estimated', 0),
                    "response_time": response_time,
                    "json_file": filename
                }
            else:
                error_msg = data.get('detail', 'Unknown error')
                print(f"❌ API Error: {error_msg}")
                return {
                    "success": False,
                    "hospital": hospital["name"], 
                    "error": error_msg,
                    "response_time": response_time
                }
        else:
            error_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {error_text}")
            return {
                "success": False,
                "hospital": hospital["name"],
                "error": f"HTTP {response.status_code}: {error_text}",
                "response_time": response_time
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "success": False,
            "hospital": hospital["name"],
            "error": str(e),
            "response_time": 0
        }

def main():
    """Main testing function"""
    print("🧪 MULTI-HOSPITAL PROSPECT DISCOVERY TESTING")
    print("=" * 80)
    print(f"Testing {len(TEST_HOSPITALS)} hospitals")
    print(f"Target titles: {', '.join(TARGET_TITLES)}")
    print()
    
    # Test API health first
    if not test_api_health():
        print("❌ API not responsive - aborting tests")
        return
    
    # Create output directory
    output_dir = create_output_directory()
    print(f"📁 Output directory: {output_dir}")
    
    # Test each hospital
    results = []
    total_start_time = time.time()
    
    for i, hospital in enumerate(TEST_HOSPITALS):
        print(f"\n{'='*80}")
        print(f"TEST {i+1}/{len(TEST_HOSPITALS)}")
        result = test_hospital(hospital, output_dir)
        results.append(result)
        
        # Brief pause between requests
        if i < len(TEST_HOSPITALS) - 1:
            print(f"\n⏸️  Pausing 5 seconds before next test...")
            time.sleep(5)
    
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    
    # Generate summary report
    print(f"\n🎯 TESTING SUMMARY")
    print("=" * 80)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"Total tests: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success rate: {len(successful_tests)/len(results)*100:.1f}%")
    print(f"Total testing time: {total_time/60:.1f} minutes")
    
    if successful_tests:
        total_prospects = sum(r["prospects_found"] for r in successful_tests)
        total_cost = sum(r["cost"] for r in successful_tests)
        avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"Total prospects found: {total_prospects}")
        print(f"Average prospects per hospital: {total_prospects/len(successful_tests):.1f}")
        print(f"Total cost: ${total_cost:.2f}")
        print(f"Average cost per hospital: ${total_cost/len(successful_tests):.2f}")
        print(f"Average response time: {avg_response_time:.1f} seconds")
        
        print(f"\n📁 JSON FILES CREATED:")
        for result in successful_tests:
            if "json_file" in result:
                print(f"   {result['json_file']}")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for result in failed_tests:
            print(f"   {result['hospital']}: {result['error']}")
    
    # Save summary to file
    summary_file = f"{output_dir}/testing_summary.json"
    summary_data = {
        "test_timestamp": datetime.now().isoformat(),
        "total_hospitals_tested": len(results),
        "successful_tests": len(successful_tests),
        "failed_tests": len(failed_tests),
        "success_rate_percent": len(successful_tests)/len(results)*100,
        "total_testing_time_minutes": total_time/60,
        "results": results
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    print(f"\n💾 Summary saved to: {summary_file}")
    print(f"\n🚀 All testing complete! Check {output_dir}/ for detailed results.")

if __name__ == "__main__":
    main()
