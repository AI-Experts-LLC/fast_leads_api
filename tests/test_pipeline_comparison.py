"""
Pipeline Comparison Test
Compares Original Three-Step Pipeline vs. BrightData Pipeline on the same company
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

from app.services.three_step_prospect_discovery import ThreeStepProspectDiscoveryService
from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService


async def test_original_pipeline(company_name: str, company_city: str, company_state: str):
    """Test the original three-step pipeline (Serper + Apify + AI)"""
    print("\n" + "="*80)
    print("ORIGINAL THREE-STEP PIPELINE (Serper + Apify + AI)")
    print("="*80)

    service = ThreeStepProspectDiscoveryService()

    # Step 1: Search
    print(f"\n[STEP 1] Searching LinkedIn via Serper...")
    start_time = time.time()
    step1_result = await service.step1_search_and_filter(
        company_name=company_name,
        company_city=company_city,
        company_state=company_state
    )
    step1_time = time.time() - start_time

    if not step1_result.get('success'):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return None

    linkedin_urls = [p['linkedin_url'] for p in step1_result['qualified_prospects']]
    print(f"✅ Step 1 complete ({step1_time:.1f}s): {len(linkedin_urls)} LinkedIn URLs found")

    # Step 2: Scrape
    print(f"\n[STEP 2] Scraping LinkedIn profiles via Apify...")
    start_time = time.time()
    step2_result = await service.step2_scrape_profiles(
        linkedin_urls=linkedin_urls,
        company_name=company_name,
        company_city=company_city,
        company_state=company_state
    )
    step2_time = time.time() - start_time

    if not step2_result.get('success'):
        print(f"❌ Step 2 failed: {step2_result.get('error')}")
        return None

    enriched = step2_result['enriched_prospects']
    print(f"✅ Step 2 complete ({step2_time:.1f}s): {len(enriched)} enriched profiles")

    # Step 3: Rank
    print(f"\n[STEP 3] AI ranking and qualification...")
    start_time = time.time()
    step3_result = await service.step3_rank_prospects(
        enriched_prospects=enriched,
        company_name=company_name,
        min_score_threshold=65,
        max_prospects=10
    )
    step3_time = time.time() - start_time

    if not step3_result.get('success'):
        print(f"❌ Step 3 failed: {step3_result.get('error')}")
        return None

    qualified = step3_result['qualified_prospects']
    print(f"✅ Step 3 complete ({step3_time:.1f}s): {len(qualified)} qualified prospects")

    total_time = step1_time + step2_time + step3_time

    # Calculate costs
    serper_cost = 0.05  # Approximate
    apify_cost = len(linkedin_urls) * 0.0047
    ai_cost = len(enriched) * 0.03
    total_cost = serper_cost + apify_cost + ai_cost

    print(f"\n📊 ORIGINAL PIPELINE SUMMARY:")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Step 1 (Serper): {step1_time:.1f}s, ${serper_cost:.2f}")
    print(f"   Step 2 (Apify): {step2_time:.1f}s, ${apify_cost:.2f}")
    print(f"   Step 3 (AI): {step3_time:.1f}s, ${ai_cost:.2f}")
    print(f"   Total cost: ${total_cost:.2f}")
    print(f"   URLs found → Enriched → Qualified: {len(linkedin_urls)} → {len(enriched)} → {len(qualified)}")

    return {
        'pipeline': 'original',
        'success': True,
        'total_time': total_time,
        'step_times': {
            'step1': step1_time,
            'step2': step2_time,
            'step3': step3_time
        },
        'costs': {
            'serper': serper_cost,
            'apify': apify_cost,
            'ai': ai_cost,
            'total': total_cost
        },
        'funnel': {
            'urls_found': len(linkedin_urls),
            'enriched': len(enriched),
            'qualified': len(qualified)
        },
        'prospects': qualified
    }


async def test_brightdata_pipeline(company_name: str, company_city: str, company_state: str, parent_account_name: str = None):
    """Test the BrightData pipeline (BrightData Filter + Filter + AI)"""
    print("\n" + "="*80)
    print("BRIGHTDATA PIPELINE (BrightData Filter + Filter + AI)")
    print("="*80)

    service = BrightDataProspectDiscoveryService()

    # Step 1: BrightData Filter
    print(f"\n[STEP 1] Filtering LinkedIn dataset via BrightData...")
    start_time = time.time()
    step1_result = await service.step1_brightdata_filter(
        company_name=company_name,
        parent_account_name=parent_account_name,
        company_city=company_city,
        company_state=company_state,
        min_connections=20
    )
    step1_time = time.time() - start_time

    if not step1_result.get('success'):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return None

    enriched = step1_result['enriched_prospects']
    print(f"✅ Step 1 complete ({step1_time:.1f}s): {len(enriched)} profiles from BrightData")

    # Step 2: Filter (no scraping)
    print(f"\n[STEP 2] Filtering profiles (no scraping)...")
    start_time = time.time()
    step2_result = await service.step2_filter_prospects(
        enriched_prospects=enriched,
        company_name=company_name,
        company_city=company_city,
        company_state=company_state
    )
    step2_time = time.time() - start_time

    if not step2_result.get('success'):
        print(f"❌ Step 2 failed: {step2_result.get('error')}")
        return None

    filtered = step2_result['enriched_prospects']
    print(f"✅ Step 2 complete ({step2_time:.1f}s): {len(filtered)} filtered profiles")

    # Step 3: Rank
    print(f"\n[STEP 3] AI ranking and qualification...")
    start_time = time.time()
    step3_result = await service.step3_rank_prospects(
        enriched_prospects=filtered,
        company_name=company_name,
        min_score_threshold=65,
        max_prospects=10
    )
    step3_time = time.time() - start_time

    if not step3_result.get('success'):
        print(f"❌ Step 3 failed: {step3_result.get('error')}")
        return None

    qualified = step3_result['qualified_prospects']
    print(f"✅ Step 3 complete ({step3_time:.1f}s): {len(qualified)} qualified prospects")

    total_time = step1_time + step2_time + step3_time

    # Calculate costs
    brightdata_cost = 0.05  # Approximate
    ai_cost = len(filtered) * 0.03
    total_cost = brightdata_cost + ai_cost

    print(f"\n📊 BRIGHTDATA PIPELINE SUMMARY:")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Step 1 (BrightData): {step1_time:.1f}s, ${brightdata_cost:.2f}")
    print(f"   Step 2 (Filter): {step2_time:.1f}s, $0.00")
    print(f"   Step 3 (AI): {step3_time:.1f}s, ${ai_cost:.2f}")
    print(f"   Total cost: ${total_cost:.2f}")
    print(f"   Profiles → Filtered → Qualified: {len(enriched)} → {len(filtered)} → {len(qualified)}")

    return {
        'pipeline': 'brightdata',
        'success': True,
        'total_time': total_time,
        'step_times': {
            'step1': step1_time,
            'step2': step2_time,
            'step3': step3_time
        },
        'costs': {
            'brightdata': brightdata_cost,
            'filter': 0.0,
            'ai': ai_cost,
            'total': total_cost
        },
        'funnel': {
            'profiles_found': len(enriched),
            'filtered': len(filtered),
            'qualified': len(qualified)
        },
        'prospects': qualified
    }


def compare_results(original_result, brightdata_result):
    """Compare the results from both pipelines"""
    print("\n" + "="*80)
    print("COMPARISON ANALYSIS")
    print("="*80)

    if not original_result:
        print("\n❌ Original pipeline failed - no comparison available")
        if brightdata_result:
            print("✅ BrightData pipeline succeeded")
        return

    if not brightdata_result:
        print("\n✅ Original pipeline succeeded")
        print("❌ BrightData pipeline failed - no comparison available")
        return

    # Time comparison
    print("\n⏱️  TIMING COMPARISON:")
    print(f"   Original: {original_result['total_time']:.1f}s")
    print(f"   BrightData: {brightdata_result['total_time']:.1f}s")
    time_diff = original_result['total_time'] - brightdata_result['total_time']
    if time_diff > 0:
        print(f"   → BrightData is {time_diff:.1f}s FASTER")
    else:
        print(f"   → Original is {abs(time_diff):.1f}s FASTER")

    # Cost comparison
    print("\n💰 COST COMPARISON:")
    print(f"   Original: ${original_result['costs']['total']:.2f}")
    print(f"   BrightData: ${brightdata_result['costs']['total']:.2f}")
    cost_savings = original_result['costs']['total'] - brightdata_result['costs']['total']
    if cost_savings > 0:
        savings_pct = (cost_savings / original_result['costs']['total']) * 100
        print(f"   → BrightData saves ${cost_savings:.2f} ({savings_pct:.1f}%)")
    else:
        print(f"   → Original is ${abs(cost_savings):.2f} cheaper")

    # Quality comparison
    print("\n📊 QUALITY COMPARISON:")
    print(f"   Original qualified: {original_result['funnel']['qualified']}")
    print(f"   BrightData qualified: {brightdata_result['funnel']['qualified']}")

    # Funnel comparison
    print("\n🔍 FUNNEL COMPARISON:")
    print(f"   Original: {original_result['funnel']['urls_found']} URLs → {original_result['funnel']['enriched']} enriched → {original_result['funnel']['qualified']} qualified")
    print(f"   BrightData: {brightdata_result['funnel']['profiles_found']} profiles → {brightdata_result['funnel']['filtered']} filtered → {brightdata_result['funnel']['qualified']} qualified")

    # Top prospects comparison
    print("\n🏆 TOP 3 PROSPECTS COMPARISON:")

    print("\n   ORIGINAL PIPELINE:")
    for i, prospect in enumerate(original_result['prospects'][:3], 1):
        name = prospect['linkedin_data'].get('name', 'Unknown')
        title = prospect['linkedin_data'].get('job_title', 'Unknown')
        score = prospect.get('ai_ranking', {}).get('overall_score', 0)
        print(f"   {i}. {name} - {title} (Score: {score}/100)")

    print("\n   BRIGHTDATA PIPELINE:")
    for i, prospect in enumerate(brightdata_result['prospects'][:3], 1):
        name = prospect['linkedin_data'].get('name', 'Unknown')
        title = prospect['linkedin_data'].get('job_title', 'Unknown')
        score = prospect.get('ai_ranking', {}).get('overall_score', 0)
        print(f"   {i}. {name} - {title} (Score: {score}/100)")

    # Overlap analysis
    print("\n🔄 PROSPECT OVERLAP:")
    original_urls = {p['linkedin_url'] for p in original_result['prospects']}
    brightdata_urls = {p['linkedin_url'] for p in brightdata_result['prospects']}

    overlap = original_urls & brightdata_urls
    original_only = original_urls - brightdata_urls
    brightdata_only = brightdata_urls - original_urls

    print(f"   Prospects in BOTH: {len(overlap)}")
    print(f"   Original ONLY: {len(original_only)}")
    print(f"   BrightData ONLY: {len(brightdata_only)}")

    if overlap:
        print("\n   Shared prospects:")
        for url in list(overlap)[:5]:
            orig_prospect = next(p for p in original_result['prospects'] if p['linkedin_url'] == url)
            bd_prospect = next(p for p in brightdata_result['prospects'] if p['linkedin_url'] == url)
            name = orig_prospect['linkedin_data'].get('name', 'Unknown')
            orig_score = orig_prospect.get('ai_ranking', {}).get('overall_score', 0)
            bd_score = bd_prospect.get('ai_ranking', {}).get('overall_score', 0)
            print(f"      - {name}: Original={orig_score}, BrightData={bd_score}")


async def main():
    """Run comparison test"""
    print("\n" + "="*80)
    print("PIPELINE COMPARISON TEST")
    print("="*80)

    # Test company - use a hospital that worked in BrightData tests
    company_name = "BENEFIS HOSPITALS INC"
    parent_account_name = "Benefis Health System"
    company_city = "Great Falls"
    company_state = "Montana"

    print(f"\nTest Company: {company_name}")
    print(f"Parent Account: {parent_account_name}")
    print(f"Location: {company_city}, {company_state}")

    # Run original pipeline
    original_result = await test_original_pipeline(
        company_name=company_name,
        company_city=company_city,
        company_state=company_state
    )

    # Run BrightData pipeline
    brightdata_result = await test_brightdata_pipeline(
        company_name=company_name,
        parent_account_name=parent_account_name,
        company_city=company_city,
        company_state=company_state
    )

    # Compare results
    compare_results(original_result, brightdata_result)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pipeline_comparison_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'test_company': {
                'name': company_name,
                'parent': parent_account_name,
                'city': company_city,
                'state': company_state
            },
            'original_pipeline': original_result,
            'brightdata_pipeline': brightdata_result,
            'timestamp': timestamp
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
