#!/usr/bin/env python3
"""
Direct API test for St. Vincent Healthcare
"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/discover-prospects-improved"

payload = {
    "company_name": "St. Vincent Healthcare",
    "company_city": "Billings",
    "company_state": "Montana"
}

print("="*80)
print("Testing St. Vincent Healthcare Prospect Discovery")
print("="*80)
print(f"Request: {json.dumps(payload, indent=2)}")
print("\nCalling API (this may take 5-10 minutes)...")
print("="*80)

start_time = time.time()

try:
    response = requests.post(
        API_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=600  # 10 minute timeout
    )

    elapsed = time.time() - start_time
    print(f"\n✓ Response received in {elapsed:.1f} seconds")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()

        # Save full response
        with open("st_vincent_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n✓ Full response saved to: st_vincent_response.json")

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        data = result.get("data", {})
        pipeline = data.get("pipeline_summary", {})
        prospects = data.get("qualified_prospects", [])

        print(f"Search Results: {pipeline.get('search_results_found', 0)}")
        print(f"After Basic Filter: {pipeline.get('prospects_after_basic_filter', 0)}")
        print(f"After AI Title Filter: {pipeline.get('prospects_after_ai_title_filter', 0)}")
        print(f"LinkedIn Profiles Scraped: {pipeline.get('linkedin_profiles_scraped', 0)}")
        print(f"After Advanced Filter: {pipeline.get('prospects_after_advanced_filter', 0)}")
        print(f"After AI Ranking: {pipeline.get('prospects_after_ai_ranking', 0)}")
        print(f"Final Top Prospects: {len(prospects)}")

        if prospects:
            print("\n" + "="*80)
            print("TOP PROSPECTS")
            print("="*80)
            for i, prospect in enumerate(prospects[:5], 1):
                linkedin_data = prospect.get("linkedin_data", {})
                ai_ranking = prospect.get("ai_ranking", {})
                print(f"\n{i}. {linkedin_data.get('name', 'Unknown')}")
                print(f"   Title: {linkedin_data.get('job_title', 'N/A')}")
                print(f"   Company: {linkedin_data.get('company', 'N/A')}")
                print(f"   AI Score: {ai_ranking.get('ranking_score', 0)}/100")
                print(f"   LinkedIn: {prospect.get('linkedin_url', 'N/A')}")

    else:
        print(f"\n✗ Error: {response.status_code}")
        print(response.text[:500])

except requests.Timeout:
    print(f"\n✗ Request timed out after {time.time() - start_time:.1f} seconds")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")

print("\n" + "="*80)
