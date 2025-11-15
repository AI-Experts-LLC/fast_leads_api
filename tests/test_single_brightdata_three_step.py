#!/usr/bin/env python3
"""
Single test of Bright Data 3-Step Prospect Discovery (No Scraping!)
Tests Mayo Clinic which has data in Bright Data dataset
"""
import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService


async def main():
    """Test single hospital through all 3 steps"""
    print("\n" + "="*80)
    print("BRIGHT DATA 3-STEP TEST - Mayo Clinic")
    print("="*80 + "\n")

    # Initialize service
    try:
        service = BrightDataProspectDiscoveryService()
        print("✅ Bright Data service initialized\n")
    except ValueError as e:
        print(f"❌ Failed to initialize: {e}")
        return

    # Test Mayo Clinic (known to have data in BD dataset)
    company_name = "Mayo Clinic"
    city = "Rochester"
    state = "Minnesota"

    print(f"Company: {company_name}")
    print(f"Location: {city}, {state}\n")

    # Step 1: Bright Data Filter + Transform
    print("="*80)
    print("STEP 1: Bright Data Filter + Transform")
    print("="*80 + "\n")

    step1_result = await service.step1_brightdata_filter(
        company_name=company_name,
        company_city=city,
        company_state=state,
        min_connections=20
    )

    if not step1_result.get("success"):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return

    print("✅ Step 1 Success!")
    summary = step1_result.get("summary", {})
    print(f"   Profiles found: {summary.get('total_profiles_from_brightdata', 0)}")
    print(f"   Profiles transformed: {summary.get('profiles_transformed', 0)}")
    print(f"   Scraping skipped: {summary.get('scraping_skipped', False)}\n")

    enriched_prospects = step1_result.get("enriched_prospects", [])

    if not enriched_prospects:
        print("⚠️  No profiles found")
        return

    # Show first 3 prospects
    print(f"First 3 prospects:")
    for i, prospect in enumerate(enriched_prospects[:3], 1):
        linkedin_data = prospect.get("linkedin_data", {})
        print(f"   {i}. {linkedin_data.get('name', 'N/A')}")
        print(f"      Title: {linkedin_data.get('job_title', 'N/A')}")
        print(f"      Connections: {linkedin_data.get('connections', 'N/A')}\n")

    # Step 2: Filter Prospects (No Scraping!)
    print("="*80)
    print("STEP 2: Filter Prospects (No Scraping!)")
    print("="*80 + "\n")

    step2_result = await service.step2_filter_prospects(
        enriched_prospects=enriched_prospects,
        company_name=company_name,
        company_city=city,
        company_state=state,
        location_filter_enabled=True
    )

    if not step2_result.get("success"):
        print(f"❌ Step 2 failed: {step2_result.get('error')}")
        return

    print("✅ Step 2 Success!")
    summary = step2_result.get("summary", {})
    print(f"   After filter: {summary.get('after_advanced_filter', 0)}\n")

    filtered_prospects = step2_result.get("enriched_prospects", [])

    if not filtered_prospects:
        print("⚠️  No prospects passed filtering")
        return

    # Step 3: AI Ranking
    print("="*80)
    print("STEP 3: AI Ranking")
    print("="*80 + "\n")

    step3_result = await service.step3_rank_prospects(
        enriched_prospects=filtered_prospects,
        company_name=company_name,
        min_score_threshold=65,
        max_prospects=10
    )

    if not step3_result.get("success"):
        print(f"❌ Step 3 failed: {step3_result.get('error')}")
        return

    print("✅ Step 3 Success!")
    summary = step3_result.get("summary", {})
    print(f"   Prospects ranked: {summary.get('prospects_ranked', 0)}")
    print(f"   Final qualified: {summary.get('final_top_prospects', 0)}\n")

    qualified_prospects = step3_result.get("qualified_prospects", [])

    # Show top 3 prospects
    print("="*80)
    print("TOP QUALIFIED PROSPECTS")
    print("="*80 + "\n")

    for i, prospect in enumerate(qualified_prospects[:3], 1):
        linkedin_data = prospect.get("linkedin_data", {})
        ai_ranking = prospect.get("ai_ranking", {})

        print(f"#{i} - Score: {ai_ranking.get('ranking_score', 'N/A')}/100")
        print(f"   Name: {linkedin_data.get('name', 'N/A')}")
        print(f"   Title: {linkedin_data.get('job_title', 'N/A')}")
        print(f"   Company: {linkedin_data.get('company', 'N/A')}")
        print(f"   Location: {linkedin_data.get('location', 'N/A')}")
        print(f"   Connections: {linkedin_data.get('connections', 'N/A')}\n")

    print("🎉 Test Complete!")


if __name__ == "__main__":
    asyncio.run(main())
