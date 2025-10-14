#!/usr/bin/env python3
"""
Providence Medford Medical Center (Medford, Oregon) Prospect Discovery Test
Tests the improved filtering with centralized prompts
"""

import requests
import json
import time
from datetime import datetime

# Local API Configuration
LOCAL_API_URL = "http://localhost:8000"

# Providence Medford Medical Center Configuration
PROVIDENCE_DATA = {
    "company_name": "Providence Medford Medical Center",
    "company_city": "Medford",
    "company_state": "Oregon",
    "salesforce_account_id": "001VR00000UhXv8YAF"
}

def test_providence_discovery():
    """Test improved prospect discovery for Providence Medford Medical Center"""

    print("=" * 80)
    print("🏥 PROVIDENCE MEDFORD MEDICAL CENTER (MEDFORD, OR) - PROSPECT DISCOVERY TEST")
    print("=" * 80)
    print(f"Company: {PROVIDENCE_DATA['company_name']}")
    print(f"Location: {PROVIDENCE_DATA['company_city']}, {PROVIDENCE_DATA['company_state']}")
    print(f"Salesforce ID: {PROVIDENCE_DATA['salesforce_account_id']}")
    print()

    # Check API health
    print("🔍 Checking API status...")
    try:
        health = requests.get(f"{LOCAL_API_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ API is running\n")
        else:
            print(f"❌ API health check failed: {health.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure server is running: hypercorn main:app --reload")
        return

    # Run prospect discovery
    print("🔎 Starting improved prospect discovery with centralized prompts...")
    print("⏰ This may take 3-5 minutes...\n")
    start_time = time.time()

    try:
        response = requests.post(
            f"{LOCAL_API_URL}/discover-prospects-improved",
            json={
                "company_name": PROVIDENCE_DATA["company_name"],
                "company_city": PROVIDENCE_DATA["company_city"],
                "company_state": PROVIDENCE_DATA["company_state"]
            },
            timeout=600
        )

        end_time = time.time()
        elapsed = end_time - start_time

        print(f"✅ Response received in {elapsed/60:.1f} minutes\n")

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 'success':
                result = data.get('data', {})
                prospects = result.get('qualified_prospects', [])
                all_after_advanced = result.get('prospects_after_advanced_filter', [])
                pipeline = result.get('pipeline_summary', {})
                funnel = result.get('filtering_funnel', {})
                costs = result.get('cost_estimates', {})

                # Display Pipeline Summary
                print("=" * 80)
                print("📊 PIPELINE SUMMARY")
                print("=" * 80)
                print(f"Search Results Found: {pipeline.get('search_results_found', 0)}")
                print(f"After Basic Filter: {pipeline.get('prospects_after_basic_filter', 0)}")
                print(f"LinkedIn Profiles Scraped: {pipeline.get('linkedin_profiles_scraped', 0)}")
                print(f"After Advanced Filter (connections/company/location): {pipeline.get('prospects_after_advanced_filter', 0)}")
                print(f"After AI Ranking: {pipeline.get('prospects_after_ai_ranking', 0)}")
                print(f"Meeting Score Threshold (≥70): {pipeline.get('prospects_meeting_threshold', 0)}")
                print(f"Final Top Prospects (max 10): {pipeline.get('final_top_prospects', 0)}")

                # Display Filtering Funnel
                print(f"\n🔽 FILTERING FUNNEL")
                print("=" * 80)
                print(f"Total Filtered Out: {funnel.get('total_filtered_out', 0)}")
                print(f"\nFiltered by Stage:")
                for stage, count in funnel.get('filtered_out_by_stage', {}).items():
                    print(f"  • {stage}: {count} prospects")

                # Show some examples of filtered prospects
                print(f"\n📋 FILTERED OUT PROSPECTS (showing first 10):")
                print("-" * 80)
                filtered_details = funnel.get('detailed_filtered_prospects', [])
                for i, filtered in enumerate(filtered_details[:10], 1):
                    print(f"{i}. {filtered.get('name', 'Unknown')}")
                    print(f"   Stage: {filtered.get('stage', 'unknown')}")
                    print(f"   Reason: {filtered.get('reason', 'N/A')}")
                    if 'company_listed' in filtered:
                        print(f"   Company Listed: {filtered['company_listed']}")
                    if 'location_listed' in filtered:
                        print(f"   Location Listed: {filtered['location_listed']}")
                    print()

                if len(filtered_details) > 10:
                    print(f"   ... and {len(filtered_details) - 10} more\n")

                # Display ALL prospects after advanced filter
                print("=" * 80)
                print(f"📋 ALL PROSPECTS AFTER ADVANCED FILTER ({len(all_after_advanced)} total)")
                print("=" * 80)

                for i, prospect in enumerate(all_after_advanced, 1):
                    ld = prospect.get('linkedin_data', {})
                    ai_ranking = prospect.get('ai_ranking', {})

                    name = ld.get('name', 'N/A')
                    title = ld.get('job_title', ld.get('headline', 'N/A'))
                    company = ld.get('company_name', ld.get('company', 'N/A'))
                    connections = ld.get('connections', 'N/A')

                    if ai_ranking and ai_ranking.get('ranking_score'):
                        score = ai_ranking.get('ranking_score', 0)
                        status = "✅ QUALIFIED" if score >= 70 else f"⚠️  Score: {score}"
                    else:
                        status = "❌ AI ranking failed"

                    print(f"\n{i}. {name} - {status}")
                    print(f"   Title: {title}")
                    print(f"   Company: {company}")
                    print(f"   Connections: {connections}")

                # Display Final Qualified Prospects
                print(f"\n{'=' * 80}")
                print(f"🎯 FINAL QUALIFIED PROSPECTS ({len(prospects)} total)")
                print("=" * 80)

                if prospects:
                    for i, prospect in enumerate(prospects, 1):
                        ld = prospect.get('linkedin_data', {})
                        ai_ranking = prospect.get('ai_ranking', {})

                        print(f"\n{'-' * 80}")
                        print(f"{i}. {ld.get('name', 'N/A')}")
                        print(f"{'-' * 80}")
                        print(f"   AI Score: {ai_ranking.get('ranking_score', 0)}/100")
                        print(f"   Title: {ld.get('job_title', ld.get('headline', 'N/A'))}")
                        print(f"   Company: {ld.get('company_name', ld.get('company', 'N/A'))}")
                        print(f"   Location: {ld.get('location', 'N/A')}")
                        print(f"   Connections: {ld.get('connections', 'N/A')}")
                        print(f"   Current Role Duration: {ld.get('current_job_duration', 'N/A')}")
                        print(f"   LinkedIn: {prospect.get('linkedin_url', 'N/A')}")
                        print(f"   Scoring: {ai_ranking.get('ranking_reasoning', 'N/A')}")

                        # Show top skills
                        top_skills = ld.get('top_skills_by_endorsements', '')
                        if top_skills:
                            print(f"   Top Skills: {top_skills}")
                else:
                    print("\n⚠️  No prospects met the qualification criteria (score ≥70)")

                # Cost Summary
                print(f"\n{'=' * 80}")
                print(f"💰 COST SUMMARY")
                print(f"{'=' * 80}")
                print(f"Total Estimated Cost: ${costs.get('total_estimated', 0):.2f}")

                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"providence_medford_{timestamp}.json"
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
        print(f"⏰ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_providence_discovery()
