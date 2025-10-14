#!/usr/bin/env python3
"""
Test 3-step prospect discovery pipeline using Railway deployment
Target: Bozeman Health Deaconess Regional Medical Center
Location: 915 Highland Blvd, Bozeman, MT 59715
"""

import requests
import json
import time
import csv
from datetime import datetime
from typing import Dict, Any, List

# Railway deployment URL
BASE_URL = "https://fast-leads-api.up.railway.app"

# Test hospital details
HOSPITAL = {
    "company_name": "Bozeman Health Deaconess Regional Medical Center",
    "company_city": "Bozeman",
    "company_state": "Montana",
    "address": "915 Highland Blvd, Bozeman, MT 59715"
}


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def step1_search_and_filter() -> Dict[str, Any]:
    """
    STEP 1: Search LinkedIn and filter to qualified prospects
    """
    print_section("STEP 1: Search & Filter")

    url = f"{BASE_URL}/discover-prospects-step1"
    payload = {
        "company_name": HOSPITAL["company_name"],
        "company_city": HOSPITAL["company_city"],
        "company_state": HOSPITAL["company_state"]
    }

    print(f"📍 Target: {HOSPITAL['company_name']}")
    print(f"📍 Location: {HOSPITAL['address']}")
    print(f"\n⏳ Sending request to: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")

    start_time = time.time()
    response = requests.post(url, json=payload, timeout=180)
    elapsed = time.time() - start_time

    print(f"\n✅ Response received in {elapsed:.2f} seconds")
    print(f"   Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return None

    response_data = response.json()

    # Handle Railway API wrapper format {status, message, data}
    if "data" in response_data:
        result = response_data["data"]
    else:
        result = response_data

    if not result.get("success"):
        print(f"❌ Step 1 failed: {result.get('error')}")
        print(f"\n🔍 Full response:")
        print(json.dumps(result, indent=2))
        return None

    # Print summary
    summary = result.get("summary", {})
    print(f"\n📊 Step 1 Results:")
    print(f"   • Total search results: {summary.get('total_search_results')}")
    print(f"   • After basic filter: {summary.get('after_basic_filter')}")
    print(f"   • After AI basic filter: {summary.get('after_ai_basic_filter')}")
    print(f"   • After title filter: {summary.get('after_title_filter')}")
    print(f"   • ✅ Qualified for scraping: {summary.get('qualified_for_scraping')}")

    # Show sample prospects
    qualified = result.get("qualified_prospects", [])
    if qualified:
        print(f"\n📋 Sample Qualified Prospects (showing first 3):")
        for i, prospect in enumerate(qualified[:3], 1):
            print(f"\n   {i}. {prospect.get('search_title', 'Unknown')}")
            print(f"      LinkedIn: {prospect.get('linkedin_url', 'N/A')}")
            print(f"      AI Score: {prospect.get('ai_title_score', 'N/A')}/100")

    return result


def step2_scrape_profiles(step1_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    STEP 2: Scrape LinkedIn profiles and apply advanced filters
    """
    print_section("STEP 2: Scrape & Advanced Filter")

    url = f"{BASE_URL}/discover-prospects-step2"

    # Extract LinkedIn URLs from step 1
    qualified_prospects = step1_result.get("qualified_prospects", [])
    linkedin_urls = [p.get("linkedin_url") for p in qualified_prospects if p.get("linkedin_url")]

    payload = {
        "linkedin_urls": linkedin_urls,
        "company_name": HOSPITAL["company_name"],
        "company_city": HOSPITAL["company_city"],
        "company_state": HOSPITAL["company_state"]
    }

    print(f"⏳ Scraping {len(linkedin_urls)} LinkedIn profiles...")
    print(f"   Sending request to: {url}")

    start_time = time.time()
    response = requests.post(url, json=payload, timeout=300)
    elapsed = time.time() - start_time

    print(f"\n✅ Response received in {elapsed:.2f} seconds")
    print(f"   Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return None

    response_data = response.json()

    # Handle Railway API wrapper format {status, message, data}
    if "data" in response_data:
        result = response_data["data"]
    else:
        result = response_data

    if not result.get("success"):
        print(f"❌ Step 2 failed: {result.get('error')}")
        # Show filtered reasons if available
        filtered = result.get("filtered_reasons", [])
        if filtered:
            print(f"\n📋 Filtering Details:")
            for item in filtered[:5]:
                print(f"   • {item.get('name')}: {item.get('reason')}")
        return None

    # Print summary
    summary = result.get("summary", {})
    print(f"\n📊 Step 2 Results:")
    print(f"   • Profiles scraped: {summary.get('profiles_scraped')}")
    print(f"   • After advanced filter: {summary.get('after_advanced_filter')}")
    print(f"   • ✅ Ready for ranking: {summary.get('ready_for_ranking')}")

    # Show filtering details
    filtering = result.get("filtering_details", {})
    if filtering.get("filtered_out_count", 0) > 0:
        print(f"\n🔍 Advanced Filtering:")
        print(f"   • Filtered out: {filtering.get('filtered_out_count')}")
        filtered_out = filtering.get("filtered_out", [])
        for item in filtered_out[:3]:
            print(f"      - {item.get('name')}: {item.get('reason')}")

    return result


def step3_rank_prospects(step2_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    STEP 3: AI ranking and final selection
    """
    print_section("STEP 3: AI Ranking & Final Selection")

    url = f"{BASE_URL}/discover-prospects-step3"

    enriched_prospects = step2_result.get("enriched_prospects", [])

    payload = {
        "enriched_prospects": enriched_prospects,
        "company_name": HOSPITAL["company_name"],
        "min_score_threshold": 70,
        "max_prospects": 10
    }

    print(f"⏳ Ranking {len(enriched_prospects)} prospects with AI...")
    print(f"   Sending request to: {url}")
    print(f"   Min Score Threshold: 70")
    print(f"   Max Prospects: 10")

    start_time = time.time()
    response = requests.post(url, json=payload, timeout=300)
    elapsed = time.time() - start_time

    print(f"\n✅ Response received in {elapsed:.2f} seconds")
    print(f"   Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return None

    response_data = response.json()

    # Handle Railway API wrapper format {status, message, data}
    if "data" in response_data:
        result = response_data["data"]
    else:
        result = response_data

    if not result.get("success"):
        print(f"❌ Step 3 failed: {result.get('error')}")
        return None

    # Print summary
    summary = result.get("summary", {})
    print(f"\n📊 Step 3 Results:")
    print(f"   • Prospects ranked: {summary.get('prospects_ranked')}")
    print(f"   • Above threshold (≥70): {summary.get('above_threshold')}")
    print(f"   • ✅ Final top prospects: {summary.get('final_top_prospects')}")

    # Show final qualified prospects
    qualified = result.get("qualified_prospects", [])
    if qualified:
        print(f"\n🎯 FINAL QUALIFIED PROSPECTS:")
        print(f"   ({len(qualified)} prospects scoring ≥70)")
        print()

        for i, prospect in enumerate(qualified, 1):
            linkedin_data = prospect.get("linkedin_data", {})
            ai_ranking = prospect.get("ai_ranking", {})

            print(f"   {i}. {linkedin_data.get('name', 'Unknown')}")
            print(f"      Title: {linkedin_data.get('job_title', 'N/A')}")
            print(f"      Company: {linkedin_data.get('company', 'N/A')}")
            print(f"      Location: {linkedin_data.get('location', 'N/A')}")
            print(f"      Connections: {linkedin_data.get('connections', 'N/A')}")
            print(f"      📊 AI Score: {ai_ranking.get('ranking_score', 'N/A')}/100")
            print(f"      💡 Reasoning: {ai_ranking.get('reasoning', 'N/A')[:100]}...")
            print()
    else:
        print("\n⚠️  No prospects scored above threshold")

    return result


def save_to_csv(qualified_prospects: List[Dict[str, Any]], filename: str):
    """
    Save qualified prospects to CSV file
    """
    if not qualified_prospects:
        print("\n⚠️  No prospects to save")
        return

    fieldnames = [
        'rank',
        'name',
        'job_title',
        'company',
        'location',
        'connections',
        'email',
        'mobile_number',
        'ai_score',
        'ai_reasoning',
        'linkedin_url',
        'headline',
        'summary',
        'total_experience_years',
        'professional_authority_score',
        'skills_count',
        'top_skills'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, prospect in enumerate(qualified_prospects, 1):
            linkedin_data = prospect.get("linkedin_data", {})
            ai_ranking = prospect.get("ai_ranking", {})

            # Get summary/about text safely
            summary_text = linkedin_data.get('summary') or linkedin_data.get('about') or ''
            summary_truncated = summary_text[:500] if summary_text else ''

            row = {
                'rank': i,
                'name': linkedin_data.get('name', ''),
                'job_title': linkedin_data.get('job_title', ''),
                'company': linkedin_data.get('company', ''),
                'location': linkedin_data.get('location', ''),
                'connections': linkedin_data.get('connections', ''),
                'email': linkedin_data.get('email', ''),
                'mobile_number': linkedin_data.get('mobile_number', ''),
                'ai_score': ai_ranking.get('ranking_score', ''),
                'ai_reasoning': ai_ranking.get('reasoning', ''),
                'linkedin_url': linkedin_data.get('url', ''),
                'headline': linkedin_data.get('headline', ''),
                'summary': summary_truncated,
                'total_experience_years': linkedin_data.get('total_experience_years', ''),
                'professional_authority_score': linkedin_data.get('professional_authority_score', ''),
                'skills_count': linkedin_data.get('skills_count', ''),
                'top_skills': linkedin_data.get('top_skills_by_endorsements', '')
            }

            writer.writerow(row)

    print(f"\n💾 Results saved to: {filename}")
    print(f"   {len(qualified_prospects)} prospects exported")


def main():
    """
    Run complete 3-step prospect discovery pipeline
    """
    print_section("🏥 BOZEMAN HEALTH - 3-STEP PROSPECT DISCOVERY TEST")
    print(f"\n🚀 Testing Railway Deployment: {BASE_URL}")
    print(f"🎯 Target: {HOSPITAL['company_name']}")
    print(f"📍 Location: {HOSPITAL['address']}")

    overall_start = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Search and Filter
    step1_result = step1_search_and_filter()
    if not step1_result:
        print("\n❌ Pipeline failed at Step 1")
        return

    time.sleep(2)  # Brief pause between steps

    # Step 2: Scrape and Advanced Filter
    step2_result = step2_scrape_profiles(step1_result)
    if not step2_result:
        print("\n❌ Pipeline failed at Step 2")
        return

    time.sleep(2)  # Brief pause between steps

    # Step 3: AI Ranking
    step3_result = step3_rank_prospects(step2_result)
    if not step3_result:
        print("\n❌ Pipeline failed at Step 3")
        return

    overall_elapsed = time.time() - overall_start

    # Save results to CSV
    qualified_prospects = step3_result.get("qualified_prospects", [])
    csv_filename = f"bozeman_health_prospects_{timestamp}.csv"
    save_to_csv(qualified_prospects, csv_filename)

    # Save full JSON output
    json_filename = f"bozeman_health_full_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "step1": step1_result,
            "step2": step2_result,
            "step3": step3_result
        }, f, indent=2)
    print(f"💾 Full JSON saved to: {json_filename}")

    # Final summary
    print_section("✅ PIPELINE COMPLETE")
    print(f"\n⏱️  Total Time: {overall_elapsed:.2f} seconds ({overall_elapsed/60:.2f} minutes)")

    # Show final stats
    step1_summary = step1_result.get("summary", {})
    step2_summary = step2_result.get("summary", {})
    step3_summary = step3_result.get("summary", {})

    print(f"\n📊 Pipeline Statistics:")
    print(f"   • Initial search results: {step1_summary.get('total_search_results', 0)}")
    print(f"   • After all Step 1 filters: {step1_summary.get('qualified_for_scraping', 0)}")
    print(f"   • After LinkedIn scraping: {step2_summary.get('profiles_scraped', 0)}")
    print(f"   • After advanced filtering: {step2_summary.get('after_advanced_filter', 0)}")
    print(f"   • After AI ranking: {step3_summary.get('prospects_ranked', 0)}")
    print(f"   • 🎯 Final qualified (≥70): {step3_summary.get('final_top_prospects', 0)}")

    # Calculate conversion rate
    initial = step1_summary.get('total_search_results', 0)
    final = step3_summary.get('final_top_prospects', 0)
    if initial > 0:
        conversion_rate = (final / initial) * 100
        print(f"\n📈 Conversion Rate: {conversion_rate:.1f}% ({final}/{initial})")

    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
