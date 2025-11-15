#!/usr/bin/env python3
"""
Test the Bright Data 3-step prospect discovery service
Uses Bright Data LinkedIn Filter instead of Google Search as the starting point

Test Company: West Valley Medical Center, Caldwell, Idaho
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_summary(data, title):
    """Print a formatted summary"""
    print(f"\n{title}:")
    import json
    print(json.dumps(data, indent=2))


async def test_brightdata_three_step():
    """Run all three steps of the Bright Data prospect discovery pipeline"""

    # Initialize service
    try:
        service = BrightDataProspectDiscoveryService()
    except ValueError as e:
        print(f"❌ Failed to initialize Bright Data service: {e}")
        print("Make sure BRIGHTDATA_API_TOKEN is set in your .env file")
        return

    # Test configuration
    TEST_COMPANY = {
        "company_name": "West Valley Medical Center",
        "company_city": "Caldwell",
        "company_state": "Idaho",
        "account_id": "0017V00001SOG6LQAX"
    }

    print_section("BRIGHT DATA 3-STEP PROSPECT DISCOVERY TEST")
    print(f"Company: {TEST_COMPANY['company_name']}")
    print(f"Location: {TEST_COMPANY['company_city']}, {TEST_COMPANY['company_state']}")
    print(f"Account ID: {TEST_COMPANY['account_id']}")

    start_time = asyncio.get_event_loop().time()

    # ========== STEP 1: Bright Data Filter ==========
    print_section("STEP 1: Bright Data LinkedIn Filter")
    print(f"🔍 Filtering LinkedIn dataset for: {TEST_COMPANY['company_name']}")
    print(f"   Location: {TEST_COMPANY['company_city']}, {TEST_COMPANY['company_state']}")

    step1_start = asyncio.get_event_loop().time()

    step1_result = await service.step1_brightdata_filter(
        company_name=TEST_COMPANY["company_name"],
        company_city=TEST_COMPANY["company_city"],
        company_state=TEST_COMPANY["company_state"],
        min_connections=20
    )

    step1_elapsed = asyncio.get_event_loop().time() - step1_start

    print(f"\n⏱️  Step 1 completed in {step1_elapsed:.1f} seconds")

    if not step1_result.get("success"):
        print(f"\n❌ Step 1 FAILED: {step1_result.get('error')}")
        print_summary(step1_result, "Error Details")
        return

    print("\n✅ Step 1 SUCCESS!")
    summary = step1_result.get("summary", {})
    print_summary(summary, "Summary")

    enriched = step1_result.get("enriched_prospects", [])
    print(f"\n📊 Found {len(enriched)} enriched prospects from Bright Data (no scraping needed!):")
    for i, prospect in enumerate(enriched[:5], 1):
        linkedin_data = prospect.get("linkedin_data", {})
        print(f"   {i}. {linkedin_data.get('name', 'N/A')}")
        print(f"      Position: {linkedin_data.get('job_title', 'N/A')}")
        print(f"      Company: {linkedin_data.get('company', 'N/A')}")
        print(f"      Connections: {linkedin_data.get('connections', 'N/A')}")
        print(f"      URL: {prospect.get('linkedin_url', 'N/A')}")

    if len(enriched) > 5:
        print(f"   ... and {len(enriched) - 5} more")

    # ========== STEP 2: Filter Prospects (No Scraping!) ==========
    print_section("STEP 2: Filter Prospects (No Scraping!)")

    if not enriched:
        print("❌ No enriched prospects from Step 1")
        return

    print(f"🔍 Filtering {len(enriched)} Bright Data prospects...")
    print("   ✅ Skipping LinkedIn scraping - using Bright Data profiles directly!")

    step2_start = asyncio.get_event_loop().time()

    step2_result = await service.step2_filter_prospects(
        enriched_prospects=enriched,
        company_name=TEST_COMPANY["company_name"],
        company_city=TEST_COMPANY["company_city"],
        company_state=TEST_COMPANY["company_state"],
        location_filter_enabled=True
    )

    step2_elapsed = asyncio.get_event_loop().time() - step2_start

    print(f"\n⏱️  Step 2 completed in {step2_elapsed:.1f} seconds")

    if not step2_result.get("success"):
        print(f"\n❌ Step 2 FAILED: {step2_result.get('error')}")
        print_summary(step2_result, "Error Details")

        # Show filtering details if available
        filtering_details = step2_result.get("filtering_details", {})
        if filtering_details:
            print_summary(filtering_details, "Filtering Details")

        return

    print("\n✅ Step 2 SUCCESS!")
    summary = step2_result.get("summary", {})
    print_summary(summary, "Summary")

    filtering_details = step2_result.get("filtering_details", {})
    if filtering_details:
        print_summary(filtering_details, "Filtering Details")

    enriched = step2_result.get("enriched_prospects", [])
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

    # ========== STEP 3: AI Ranking ==========
    print_section("STEP 3: AI Ranking and Qualification")

    if not enriched:
        print("❌ No enriched prospects from Step 2")
        return

    print(f"🤖 Running AI ranking on {len(enriched)} prospects...")
    print(f"   Min score threshold: 65")
    print(f"   Max prospects: 10")

    step3_start = asyncio.get_event_loop().time()

    step3_result = await service.step3_rank_prospects(
        enriched_prospects=enriched,
        company_name=TEST_COMPANY["company_name"],
        min_score_threshold=65,
        max_prospects=10
    )

    step3_elapsed = asyncio.get_event_loop().time() - step3_start

    print(f"\n⏱️  Step 3 completed in {step3_elapsed:.1f} seconds")

    if not step3_result.get("success"):
        print(f"\n❌ Step 3 FAILED: {step3_result.get('error')}")
        print_summary(step3_result, "Error Details")
        return

    print("\n✅ Step 3 SUCCESS!")
    summary = step3_result.get("summary", {})
    print_summary(summary, "Summary")

    qualified_prospects = step3_result.get("qualified_prospects", [])
    print(f"\n🎯 TOP QUALIFIED PROSPECTS ({len(qualified_prospects)}):")
    print("\n" + "-"*80)

    for i, prospect in enumerate(qualified_prospects, 1):
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
            for line in reasoning.split('. '):
                if line.strip():
                    print(f"      • {line.strip()}")

        print("\n" + "-"*80)

    # ========== FINAL SUMMARY ==========
    total_elapsed = asyncio.get_event_loop().time() - start_time

    print_section("FINAL SUMMARY")
    print(f"⏱️  Total pipeline time: {total_elapsed:.1f} seconds ({total_elapsed/60:.1f} minutes)")
    print("\n✅ ALL STEPS COMPLETED SUCCESSFULLY!")

    step1_summary = step1_result.get("summary", {})
    step2_summary = step2_result.get("summary", {})
    step3_summary = step3_result.get("summary", {})

    print(f"\n📊 Pipeline Statistics:")
    print(f"   • Bright Data profiles found: {step1_summary.get('total_profiles_from_brightdata', 0)}")
    print(f"   • Profiles transformed: {step1_summary.get('profiles_transformed', 0)}")
    print(f"   • Scraping skipped: {step1_summary.get('scraping_skipped', False)} ✅")
    print(f"   • After advanced filter: {step2_summary.get('after_advanced_filter', 0)}")
    print(f"   • Prospects ranked: {step3_summary.get('prospects_ranked', 0)}")
    print(f"   • Above threshold (65+): {step3_summary.get('above_threshold', 0)}")
    print(f"   • Final qualified: {step3_summary.get('final_top_prospects', 0)}")

    print(f"\n💰 Estimated API Costs:")
    print(f"   • Bright Data (filter): ~$0.05 (snapshot creation)")
    print(f"   • Apify (scraping): $0.00 (SKIPPED - used Bright Data profiles!) ✅")
    print(f"   • OpenAI (AI ranking): ~${step3_summary.get('prospects_ranked', 0) * 0.03:.2f}")
    total_cost = 0.05 + (step3_summary.get('prospects_ranked', 0) * 0.03)
    print(f"   • TOTAL: ~${total_cost:.2f}")
    print(f"\n💵 Cost Savings: ~${step1_summary.get('total_profiles_from_brightdata', 0) * 0.0047:.2f} saved by skipping scraping!")

    print(f"\n🎉 Bright Data 3-Step Discovery Complete!")
    print(f"   Snapshot ID: {step1_summary.get('snapshot_id', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test_brightdata_three_step())
