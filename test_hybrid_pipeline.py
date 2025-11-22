"""
Test script for Hybrid Prospect Discovery Pipeline
Tests the 4-step pipeline locally: Parallel Search → Deduplicate → Rank → Queue

Usage:
    python test_hybrid_pipeline.py
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
BASE_URL = "http://127.0.0.1:8000"

# Test Company
TEST_COMPANY = {
    "company_name": "Portneuf Medical Center",
    "company_city": "Pocatello",
    "company_state": "Idaho"
}


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_step(step_num, text):
    """Print formatted step"""
    print(f"\n🔹 STEP {step_num}: {text}")
    print("-" * 80)


def print_result(data, title="Result"):
    """Print formatted JSON result"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))


def test_hybrid_pipeline():
    """Test the full hybrid prospect discovery pipeline"""

    print_header("🆕 HYBRID PROSPECT DISCOVERY PIPELINE TEST")
    print(f"Test Company: {TEST_COMPANY['company_name']}")
    print(f"Location: {TEST_COMPANY['company_city']}, {TEST_COMPANY['company_state']}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # =========================================================================
    # STEP 1: Parallel Search (Serper + Bright Data)
    # =========================================================================
    print_step(1, "Parallel Search (Serper + Bright Data)")

    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/discover-leads-step1",
            json=TEST_COMPANY,
            timeout=360  # 6 minutes for parallel search
        )

        step1_duration = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ Step 1 failed: HTTP {response.status_code}")
            print(response.text)
            return

        step1_result = response.json()
        print(f"✅ Step 1 completed in {step1_duration:.1f}s")

        # Extract data for next step
        step1_data = step1_result.get("data", {})
        serper_prospects = step1_data.get("serper_prospects", [])
        brightdata_prospects = step1_data.get("brightdata_prospects", [])
        summary = step1_data.get("summary", {})

        print(f"   → Serper: {summary.get('serper_count', 0)} prospects")
        print(f"   → Bright Data: {summary.get('brightdata_count', 0)} prospects")

        if not serper_prospects and not brightdata_prospects:
            print("❌ No prospects found from either source. Aborting.")
            return

    except Exception as e:
        print(f"❌ Step 1 failed with exception: {str(e)}")
        return

    # =========================================================================
    # STEP 2: Deduplicate + Enrich
    # =========================================================================
    print_step(2, "Deduplicate + Enrich")

    start_time = time.time()

    try:
        step2_payload = {
            "serper_prospects": serper_prospects,
            "brightdata_prospects": brightdata_prospects,
            "company_name": TEST_COMPANY["company_name"],
            "company_city": TEST_COMPANY["company_city"],
            "company_state": TEST_COMPANY["company_state"]
        }

        response = requests.post(
            f"{BASE_URL}/discover-leads-step2",
            json=step2_payload,
            timeout=360  # 6 minutes for scraping
        )

        step2_duration = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ Step 2 failed: HTTP {response.status_code}")
            print(response.text)
            return

        step2_result = response.json()
        print(f"✅ Step 2 completed in {step2_duration:.1f}s")

        # Extract data for next step
        step2_data = step2_result.get("data", {})
        enriched_prospects = step2_data.get("enriched_prospects", [])
        summary = step2_data.get("summary", {})

        print(f"   → Bright Data: {summary.get('brightdata_count', 0)} prospects")
        print(f"   → Serper (enriched): {summary.get('serper_enriched_count', 0)} prospects")
        print(f"   → Duplicates skipped: {summary.get('duplicates_skipped', 0)} prospects")
        print(f"   → Total enriched: {summary.get('total_enriched', 0)} prospects")

        if not enriched_prospects:
            print("❌ No enriched prospects. Aborting.")
            return

    except Exception as e:
        print(f"❌ Step 2 failed with exception: {str(e)}")
        return

    # =========================================================================
    # STEP 3: AI Ranking & Qualification
    # =========================================================================
    print_step(3, "AI Ranking & Qualification")

    start_time = time.time()

    try:
        step3_payload = {
            "enriched_prospects": enriched_prospects,
            "company_name": TEST_COMPANY["company_name"],
            "min_score_threshold": 65,
            "max_prospects": 10
        }

        response = requests.post(
            f"{BASE_URL}/discover-leads-step3",
            json=step3_payload,
            timeout=360  # 6 minutes for AI ranking
        )

        step3_duration = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ Step 3 failed: HTTP {response.status_code}")
            print(response.text)
            return

        step3_result = response.json()
        print(f"✅ Step 3 completed in {step3_duration:.1f}s")

        # Extract data for next step
        step3_data = step3_result.get("data", {})
        qualified_prospects = step3_data.get("qualified_prospects", [])
        summary = step3_data.get("summary", {})

        print(f"   → Qualified prospects (≥65 score): {len(qualified_prospects)}")

        if qualified_prospects:
            print("\n   📋 Top Qualified Prospects:")
            for i, prospect in enumerate(qualified_prospects[:5], 1):
                linkedin_data = prospect.get("linkedin_data", {})
                ai_ranking = prospect.get("ai_ranking", {})
                name = linkedin_data.get("name", "Unknown")
                title = linkedin_data.get("job_title", "Unknown")
                score = ai_ranking.get("ranking_score", 0)
                print(f"      {i}. {name} - {title} (Score: {score})")
        else:
            print("❌ No qualified prospects. Aborting.")
            return

    except Exception as e:
        print(f"❌ Step 3 failed with exception: {str(e)}")
        return

    # =========================================================================
    # STEP 4: Queue to Pending Updates
    # =========================================================================
    print_step(4, "Queue Leads for Approval")

    start_time = time.time()

    try:
        step4_payload = {
            "qualified_prospects": qualified_prospects,
            "company_name": TEST_COMPANY["company_name"]
        }

        response = requests.post(
            f"{BASE_URL}/discover-leads-step4",
            json=step4_payload,
            timeout=360  # 6 minutes for queuing leads
        )

        step4_duration = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ Step 4 failed: HTTP {response.status_code}")
            print(response.text)
            return

        step4_result = response.json()
        print(f"✅ Step 4 completed in {step4_duration:.1f}s")

        # Extract data
        data = step4_result.get("data", {})

        print(f"   → Queued: {data.get('queued', 0)} leads")
        print(f"   → Failed: {data.get('failed', 0)} leads")
        print(f"   → Total: {data.get('total', 0)} leads")

    except Exception as e:
        print(f"❌ Step 4 failed with exception: {str(e)}")
        return

    # =========================================================================
    # SUMMARY
    # =========================================================================
    total_duration = step1_duration + step2_duration + step3_duration + step4_duration

    print_header("🎉 PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Total Time: {total_duration:.1f}s")
    print(f"  → Step 1 (Parallel Search): {step1_duration:.1f}s")
    print(f"  → Step 2 (Deduplicate + Enrich): {step2_duration:.1f}s")
    print(f"  → Step 3 (AI Ranking): {step3_duration:.1f}s")
    print(f"  → Step 4 (Queue Leads): {step4_duration:.1f}s")
    print(f"\n✅ {data.get('queued', 0)} leads queued for approval")
    print(f"📊 View at: {BASE_URL}/dashboard")
    print(f"📋 View pending updates at: {BASE_URL}/pending-updates?record_type=Lead")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  🆕 HYBRID PROSPECT DISCOVERY PIPELINE TEST".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    test_hybrid_pipeline()

    print("\n" + "=" * 80)
    print("Test complete! 🚀")
    print("=" * 80 + "\n")
