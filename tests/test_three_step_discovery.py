"""
Test the 3-step prospect discovery API for West Valley Medical Center
Caldwell, Idaho (Account ID: 0017V00001SOG6LQAX)
"""
import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_COMPANY = {
    "company_name": "West Valley Medical Center",
    "company_city": "Caldwell",
    "company_state": "Idaho",
    "account_id": "0017V00001SOG6LQAX"
}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_summary(data, title):
    """Print a formatted summary"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))

def save_results(step_name, data):
    """Save step results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{step_name}_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Results saved to: {filename}")

def test_step1():
    """
    STEP 1: Search and Filter
    Expected time: 30-50 seconds
    """
    print_section("STEP 1: Search and Filter LinkedIn Profiles")

    payload = {
        "company_name": TEST_COMPANY["company_name"],
        "company_city": TEST_COMPANY["company_city"],
        "company_state": TEST_COMPANY["company_state"]
    }

    print(f"🔍 Searching for prospects at: {TEST_COMPANY['company_name']}")
    print(f"   Location: {TEST_COMPANY['company_city']}, {TEST_COMPANY['company_state']}")
    print(f"   Account ID: {TEST_COMPANY['account_id']}")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step1",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        elapsed = time.time() - start_time
        print(f"\n⏱️  Step 1 completed in {elapsed:.1f} seconds")

        if response.status_code == 200:
            response_data = response.json()
            # Handle wrapped response format
            result = response_data.get("data", response_data)

            if result.get("success"):
                summary = result.get("summary", {})
                qualified = result.get("qualified_prospects", [])

                print("\n✅ Step 1 SUCCESS!")
                print_summary(summary, "Summary")

                print(f"\n📊 Found {len(qualified)} qualified prospects for scraping:")
                for i, prospect in enumerate(qualified[:5], 1):
                    print(f"   {i}. {prospect.get('search_title', 'N/A')}")
                    print(f"      URL: {prospect.get('linkedin_url', 'N/A')}")
                    print(f"      AI Title Score: {prospect.get('ai_title_score', 'N/A')}")

                if len(qualified) > 5:
                    print(f"   ... and {len(qualified) - 5} more")

                save_results("step1", result)
                return result
            else:
                print(f"\n❌ Step 1 FAILED: {result.get('error')}")
                print_summary(result, "Error Details")
                return None
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"\n❌ Exception in Step 1: {str(e)}")
        return None

def test_step2(step1_result):
    """
    STEP 2: Scrape LinkedIn Profiles
    Expected time: 50-90 seconds
    """
    if not step1_result or not step1_result.get("success"):
        print("\n⚠️  Skipping Step 2 - Step 1 failed")
        return None

    print_section("STEP 2: Scrape LinkedIn Profiles")

    qualified_prospects = step1_result.get("qualified_prospects", [])
    linkedin_urls = [p.get("linkedin_url") for p in qualified_prospects if p.get("linkedin_url")]

    if not linkedin_urls:
        print("❌ No LinkedIn URLs from Step 1")
        return None

    payload = {
        "linkedin_urls": linkedin_urls,
        "company_name": TEST_COMPANY["company_name"],
        "company_city": TEST_COMPANY["company_city"],
        "company_state": TEST_COMPANY["company_state"],
        "location_filter_enabled": True
    }

    print(f"🔍 Scraping {len(linkedin_urls)} LinkedIn profiles...")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step2",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180
        )

        elapsed = time.time() - start_time
        print(f"\n⏱️  Step 2 completed in {elapsed:.1f} seconds")

        if response.status_code == 200:
            response_data = response.json()
            # Handle wrapped response format
            result = response_data.get("data", response_data)

            if result.get("success"):
                summary = result.get("summary", {})
                enriched = result.get("enriched_prospects", [])
                filtering = result.get("filtering_details", {})

                print("\n✅ Step 2 SUCCESS!")
                print_summary(summary, "Summary")

                if filtering:
                    print_summary(filtering, "Filtering Details")

                print(f"\n📊 Successfully enriched {len(enriched)} prospects:")
                for i, prospect in enumerate(enriched[:5], 1):
                    linkedin_data = prospect.get("linkedin_data", {})
                    print(f"   {i}. {linkedin_data.get('name', 'N/A')}")
                    print(f"      Title: {linkedin_data.get('job_title', 'N/A')}")
                    print(f"      Company: {linkedin_data.get('company', 'N/A')}")
                    print(f"      Location: {linkedin_data.get('location', 'N/A')}")
                    print(f"      Connections: {linkedin_data.get('connections', 'N/A')}")

                if len(enriched) > 5:
                    print(f"   ... and {len(enriched) - 5} more")

                save_results("step2", result)
                return result
            else:
                print(f"\n❌ Step 2 FAILED: {result.get('error')}")
                print_summary(result, "Error Details")
                return None
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"\n❌ Exception in Step 2: {str(e)}")
        return None

def test_step3(step2_result):
    """
    STEP 3: AI Ranking and Qualification
    Expected time: 15-25 seconds
    """
    if not step2_result or not step2_result.get("success"):
        print("\n⚠️  Skipping Step 3 - Step 2 failed")
        return None

    print_section("STEP 3: AI Ranking and Qualification")

    enriched_prospects = step2_result.get("enriched_prospects", [])

    if not enriched_prospects:
        print("❌ No enriched prospects from Step 2")
        return None

    payload = {
        "enriched_prospects": enriched_prospects,
        "company_name": TEST_COMPANY["company_name"],
        "min_score_threshold": 65,
        "max_prospects": 10
    }

    print(f"🤖 Running AI ranking on {len(enriched_prospects)} prospects...")
    print(f"   Min score threshold: 65")
    print(f"   Max prospects: 10")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step3",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        elapsed = time.time() - start_time
        print(f"\n⏱️  Step 3 completed in {elapsed:.1f} seconds")

        if response.status_code == 200:
            response_data = response.json()
            # Handle wrapped response format
            result = response_data.get("data", response_data)

            if result.get("success"):
                summary = result.get("summary", {})
                qualified = result.get("qualified_prospects", [])

                print("\n✅ Step 3 SUCCESS!")
                print_summary(summary, "Summary")

                print(f"\n🎯 TOP QUALIFIED PROSPECTS ({len(qualified)}):")
                print("\n" + "-"*80)

                for i, prospect in enumerate(qualified, 1):
                    linkedin_data = prospect.get("linkedin_data", {})
                    ai_ranking = prospect.get("ai_ranking", {})

                    print(f"\n#{i} - Score: {ai_ranking.get('ranking_score', 'N/A')}/100")
                    print(f"   Name: {linkedin_data.get('name', 'N/A')}")
                    print(f"   Title: {linkedin_data.get('job_title', 'N/A')}")
                    print(f"   Company: {linkedin_data.get('company', 'N/A')}")
                    print(f"   Location: {linkedin_data.get('location', 'N/A')}")
                    print(f"   Connections: {linkedin_data.get('connections', 'N/A')}")
                    print(f"   LinkedIn: {prospect.get('linkedin_url', 'N/A')}")

                    # Show AI reasoning
                    reasoning = ai_ranking.get("reasoning", "")
                    if reasoning:
                        print(f"\n   AI Reasoning:")
                        # Split reasoning into lines for better readability
                        for line in reasoning.split('. '):
                            if line.strip():
                                print(f"      • {line.strip()}")

                    print("\n" + "-"*80)

                save_results("step3_final", result)
                return result
            else:
                print(f"\n❌ Step 3 FAILED: {result.get('error')}")
                print_summary(result, "Error Details")
                return None
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"\n❌ Exception in Step 3: {str(e)}")
        return None

def main():
    """Run all three steps of the prospect discovery pipeline"""
    print("\n" + "="*80)
    print("  3-STEP PROSPECT DISCOVERY TEST")
    print("  West Valley Medical Center - Caldwell, Idaho")
    print("="*80)

    overall_start = time.time()

    # Step 1: Search and Filter
    step1_result = test_step1()

    if not step1_result:
        print("\n❌ Test aborted - Step 1 failed")
        return

    # Step 2: Scrape Profiles
    step2_result = test_step2(step1_result)

    if not step2_result:
        print("\n❌ Test aborted - Step 2 failed")
        return

    # Step 3: AI Ranking
    step3_result = test_step3(step2_result)

    overall_elapsed = time.time() - overall_start

    # Final Summary
    print_section("FINAL SUMMARY")
    print(f"⏱️  Total pipeline time: {overall_elapsed:.1f} seconds ({overall_elapsed/60:.1f} minutes)")

    if step3_result and step3_result.get("success"):
        print("\n✅ ALL STEPS COMPLETED SUCCESSFULLY!")

        step1_summary = step1_result.get("summary", {})
        step2_summary = step2_result.get("summary", {})
        step3_summary = step3_result.get("summary", {})

        print(f"\n📊 Pipeline Statistics:")
        print(f"   • Initial search results: {step1_summary.get('total_search_results', 0)}")
        print(f"   • After basic filter: {step1_summary.get('after_basic_filter', 0)}")
        print(f"   • After AI title filter: {step1_summary.get('after_title_filter', 0)}")
        print(f"   • Profiles scraped: {step2_summary.get('profiles_scraped', 0)}")
        print(f"   • After advanced filter: {step2_summary.get('after_advanced_filter', 0)}")
        print(f"   • Prospects ranked: {step3_summary.get('prospects_ranked', 0)}")
        print(f"   • Above threshold (65+): {step3_summary.get('above_threshold', 0)}")
        print(f"   • Final qualified: {step3_summary.get('final_top_prospects', 0)}")

        print(f"\n💰 Estimated API Costs:")
        print(f"   • Serper (search): ~$0.05")
        print(f"   • Apify (scraping): ~${step2_summary.get('profiles_scraped', 0) * 0.0047:.2f}")
        print(f"   • OpenAI (AI ranking): ~${step3_summary.get('prospects_ranked', 0) * 0.03:.2f}")
        print(f"   • TOTAL: ~${0.05 + (step2_summary.get('profiles_scraped', 0) * 0.0047) + (step3_summary.get('prospects_ranked', 0) * 0.03):.2f}")
    else:
        print("\n⚠️  Pipeline completed with errors")

if __name__ == "__main__":
    main()
