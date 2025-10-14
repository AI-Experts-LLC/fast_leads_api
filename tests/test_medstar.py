#!/usr/bin/env python3
"""
MedStar Health Prospect Discovery Test
Tests the improved prospect discovery pipeline for MedStar Health
"""

import requests
import json
import time
from datetime import datetime

# Local API Configuration
LOCAL_API_URL = "http://localhost:8000"

# MedStar Health Configuration
MEDSTAR_DATA = {
    "company_name": "MedStar Health",
    "company_city": "Columbia",
    "company_state": "Maryland",
    "salesforce_account_id": "0017V00001uZ2yjQAC"
}

def test_medstar_discovery():
    """Test improved prospect discovery for MedStar Health"""

    print("🏥 MedStar Health Prospect Discovery Test")
    print("=" * 60)
    print(f"Company: {MEDSTAR_DATA['company_name']}")
    print(f"Location: {MEDSTAR_DATA['company_city']}, {MEDSTAR_DATA['company_state']}")
    print(f"Salesforce ID: {MEDSTAR_DATA['salesforce_account_id']}")
    print()

    # Check API health
    print("🔍 Checking API status...")
    try:
        health = requests.get(f"{LOCAL_API_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ API is running")
        else:
            print(f"❌ API health check failed: {health.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure server is running: hypercorn main:app --reload")
        return

    # Run prospect discovery
    print("\n🔎 Starting improved prospect discovery...")
    print("⏰ This may take 3-5 minutes (searching, scraping, and ranking)...")
    start_time = time.time()

    try:
        response = requests.post(
            f"{LOCAL_API_URL}/discover-prospects-improved",
            json={
                "company_name": MEDSTAR_DATA["company_name"],
                "company_city": MEDSTAR_DATA["company_city"],
                "company_state": MEDSTAR_DATA["company_state"]
            },
            timeout=600  # 10 minutes max
        )

        end_time = time.time()
        elapsed = end_time - start_time

        print(f"\n✅ Response received in {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 'success':
                result = data.get('data', {})
                prospects = result.get('qualified_prospects', [])
                pipeline = result.get('pipeline_summary', {})
                costs = result.get('cost_estimates', {})

                print(f"\n🎯 RESULTS")
                print("=" * 60)
                print(f"Qualified Prospects: {len(prospects)}")
                print(f"\nPipeline:")
                print(f"  Search Results: {pipeline.get('search_results', 0)}")
                print(f"  After Basic Filter: {pipeline.get('after_basic_filter', 0)}")
                print(f"  After AI Company Filter: {pipeline.get('after_ai_filter', 0)}")
                print(f"  After LinkedIn Scraping: {pipeline.get('after_linkedin_scraping', 0)}")
                print(f"  Final Qualified (≥70 score): {len(prospects)}")

                print(f"\nCosts:")
                print(f"  Search: ${costs.get('search_api', 0):.2f}")
                print(f"  LinkedIn Scraping: ${costs.get('linkedin_scraping', 0):.2f}")
                print(f"  AI Processing: ${costs.get('ai_processing', 0):.2f}")
                print(f"  Total: ${costs.get('total_estimated', 0):.2f}")

                # Display prospects
                print(f"\n📋 QUALIFIED PROSPECTS (sorted by AI ranking)")
                print("=" * 60)

                if prospects:
                    for i, prospect in enumerate(prospects, 1):
                        print(f"\n{i}. {prospect.get('name', 'N/A')}")
                        print(f"   Score: {prospect.get('ai_ranking', {}).get('total_score', 0):.1f}/100")
                        print(f"   Title: {prospect.get('title', 'N/A')}")
                        print(f"   Company: {prospect.get('company', 'N/A')}")
                        print(f"   Location: {prospect.get('location', 'N/A')}")
                        print(f"   LinkedIn: {prospect.get('linkedin_url', 'N/A')}")

                        ranking = prospect.get('ai_ranking', {})
                        if ranking:
                            breakdown = ranking.get('breakdown', {})
                            print(f"   Breakdown:")
                            print(f"     • Job Title Relevance: {breakdown.get('job_title_score', 0):.1f}/40")
                            print(f"     • Decision Authority: {breakdown.get('decision_authority_score', 0):.1f}/25")
                            print(f"     • Employment Validation: {breakdown.get('employment_score', 0):.1f}/20")
                            print(f"     • Location Match: {breakdown.get('location_score', 0):.1f}/10")
                            print(f"     • Accessibility: {breakdown.get('accessibility_score', 0):.1f}/5")

                            reasoning = ranking.get('reasoning', '')
                            if reasoning:
                                print(f"   Reasoning: {reasoning[:150]}...")
                else:
                    print("No qualified prospects found (none scored ≥70 points)")

                # Save results to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"medstar_prospects_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n💾 Full results saved to: {filename}")

            else:
                print(f"❌ API Error: {data.get('detail', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {response.text}")

    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out (>10 minutes)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_medstar_discovery()
