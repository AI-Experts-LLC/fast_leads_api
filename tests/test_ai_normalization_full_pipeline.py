"""
Test AI Company Normalization - Full 3-Step Pipeline
Shows how many prospects from AI normalization pass through all filtering stages
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root FIRST before any imports
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService


async def test_full_pipeline():
    """
    Run full 3-step pipeline with AI normalization to see filtering results
    """
    print("\n" + "="*80)
    print("AI NORMALIZATION - FULL 3-STEP PIPELINE TEST")
    print("="*80)

    # Test company - same as before
    company_name = "BENEFIS HOSPITALS INC"
    parent_account_name = "Benefis Health System"
    company_city = "Great Falls"
    company_state = "Montana"

    print(f"\nTest Company: {company_name}")
    print(f"Parent Account: {parent_account_name}")
    print(f"Location: {company_city}, {company_state}")

    service = BrightDataProspectDiscoveryService()

    start_time = time.time()

    # Step 1: BrightData Filter (with AI normalization)
    print(f"\n[STEP 1] Filtering LinkedIn dataset via BrightData (AI-POWERED NORMALIZATION)...")
    step1_start = time.time()
    step1_result = await service.step1_brightdata_filter(
        company_name=company_name,
        parent_account_name=parent_account_name,
        company_city=company_city,
        company_state=company_state,
        min_connections=0,
        use_city_filter=False
    )
    step1_time = time.time() - step1_start

    if not step1_result.get('success'):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return

    enriched = step1_result['enriched_prospects']
    print(f"✅ Step 1 complete ({step1_time:.1f}s): {len(enriched)} profiles from BrightData")

    # Step 2: Filter (company validation, no scraping)
    print(f"\n[STEP 2] Filtering profiles (company validation)...")
    step2_start = time.time()
    step2_result = await service.step2_filter_prospects(
        enriched_prospects=enriched,
        company_name=company_name,
        company_city=company_city,
        company_state=company_state
    )
    step2_time = time.time() - step2_start

    if not step2_result.get('success'):
        print(f"❌ Step 2 failed: {step2_result.get('error')}")
        return

    filtered = step2_result['enriched_prospects']
    print(f"✅ Step 2 complete ({step2_time:.1f}s): {len(filtered)} profiles passed validation")

    # Show what was filtered out
    filtered_out = len(enriched) - len(filtered)
    if filtered_out > 0:
        print(f"   → Filtered out {filtered_out} profiles ({filtered_out/len(enriched)*100:.1f}%)")

    # Step 3: AI Rank
    print(f"\n[STEP 3] AI ranking and qualification...")
    step3_start = time.time()
    step3_result = await service.step3_rank_prospects(
        enriched_prospects=filtered,
        company_name=company_name,
        min_score_threshold=65,
        max_prospects=10
    )
    step3_time = time.time() - step3_start

    if not step3_result.get('success'):
        print(f"❌ Step 3 failed: {step3_result.get('error')}")
        return

    qualified = step3_result['qualified_prospects']
    print(f"✅ Step 3 complete ({step3_time:.1f}s): {len(qualified)} qualified prospects")

    total_time = time.time() - start_time

    # Calculate costs
    brightdata_cost = 0.05
    ai_normalization_cost = 0.001
    ai_ranking_cost = len(filtered) * 0.03
    total_cost = brightdata_cost + ai_normalization_cost + ai_ranking_cost

    # DETAILED FUNNEL ANALYSIS
    print("\n" + "="*80)
    print("FILTERING FUNNEL WITH AI NORMALIZATION")
    print("="*80)
    print(f"Step 1 (BrightData + AI):  {len(enriched):3d} profiles found")
    print(f"Step 2 (Company Validation): {len(filtered):3d} profiles passed ({len(filtered)/len(enriched)*100:.1f}% pass rate)")
    print(f"Step 3 (AI Qualification):   {len(qualified):3d} qualified ({len(qualified)/len(filtered)*100:.1f}% of validated)")
    print(f"\n📊 OVERALL CONVERSION: {len(enriched)} → {len(filtered)} → {len(qualified)} ({len(qualified)/len(enriched)*100:.1f}% end-to-end)")

    print(f"\n⏱️  TIMING:")
    print(f"   Step 1 (BrightData):     {step1_time:6.1f}s")
    print(f"   Step 2 (Filter):         {step2_time:6.1f}s")
    print(f"   Step 3 (AI Ranking):     {step3_time:6.1f}s")
    print(f"   Total:                   {total_time:6.1f}s")

    print(f"\n💰 COST BREAKDOWN:")
    print(f"   BrightData:              ${brightdata_cost:.3f}")
    print(f"   AI Normalization:        ${ai_normalization_cost:.3f}")
    print(f"   AI Ranking:              ${ai_ranking_cost:.3f}")
    print(f"   Total:                   ${total_cost:.3f}")

    # Display qualified prospects
    if qualified:
        print("\n" + "="*80)
        print("QUALIFIED PROSPECTS (Score ≥65)")
        print("="*80)
        for i, prospect in enumerate(qualified, 1):
            name = prospect['linkedin_data'].get('name', 'Unknown')
            title = prospect['linkedin_data'].get('job_title', 'Unknown')
            company = prospect['linkedin_data'].get('company_name', 'Unknown')
            score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
            url = prospect.get('linkedin_url', '')

            print(f"\n{i}. {name}")
            print(f"   Title:   {title}")
            print(f"   Company: {company}")
            print(f"   Score:   {score}/100")
            print(f"   URL:     {url}")
    else:
        print("\n❌ No prospects qualified with score ≥65")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"ai_normalization_full_pipeline_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'test_company': {
                'name': company_name,
                'parent': parent_account_name,
                'city': company_city,
                'state': company_state
            },
            'pipeline_version': 'BrightData with AI Company Normalization',
            'funnel': {
                'step1_profiles': len(enriched),
                'step2_filtered': len(filtered),
                'step3_qualified': len(qualified),
                'step2_pass_rate': f"{len(filtered)/len(enriched)*100:.1f}%",
                'step3_pass_rate': f"{len(qualified)/len(filtered)*100:.1f}%" if filtered else "N/A",
                'overall_conversion': f"{len(qualified)/len(enriched)*100:.1f}%"
            },
            'timing': {
                'step1': step1_time,
                'step2': step2_time,
                'step3': step3_time,
                'total': total_time
            },
            'costs': {
                'brightdata': brightdata_cost,
                'ai_normalization': ai_normalization_cost,
                'ai_ranking': ai_ranking_cost,
                'total': total_cost
            },
            'qualified_prospects': qualified,
            'timestamp': timestamp
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
