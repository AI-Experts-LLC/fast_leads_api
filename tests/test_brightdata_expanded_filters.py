"""
Test BrightData with Expanded Filters
Tests the improved filter settings to see if we get better coverage
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


async def test_brightdata_expanded():
    """Test BrightData with expanded filters"""
    print("\n" + "="*80)
    print("BRIGHTDATA PIPELINE TEST - EXPANDED FILTERS")
    print("="*80)

    # Test company - same as comparison test
    company_name = "BENEFIS HOSPITALS INC"
    parent_account_name = "Benefis Health System"
    company_city = "Great Falls"
    company_state = "Montana"

    print(f"\nTest Company: {company_name}")
    print(f"Parent Account: {parent_account_name}")
    print(f"Location: {company_city}, {company_state}")

    service = BrightDataProspectDiscoveryService()

    # Display filter improvements
    print("\n" + "-"*80)
    print("FILTER IMPROVEMENTS:")
    print("-"*80)
    print("✅ Added 'Facilities Director' (was only 'Director of Facilities')")
    print("✅ Added 'Maintenance Manager' (was missing)")
    print("✅ Added 'Finance Manager' (to catch 'System Finance Manager')")
    print("✅ Added 'COO' abbreviation")
    print("✅ Lowered min_connections: 20 → 0 (disabled)")
    print("✅ Disabled city filter by default (too restrictive)")
    print(f"\nTotal title filters: {len(service.default_target_titles)} (max: 20)")
    print("-"*80)

    start_time = time.time()

    # Step 1: BrightData Filter (with expanded filters)
    print(f"\n[STEP 1] Filtering LinkedIn dataset via BrightData (EXPANDED FILTERS)...")
    step1_start = time.time()
    step1_result = await service.step1_brightdata_filter(
        company_name=company_name,
        parent_account_name=parent_account_name,
        company_city=company_city,
        company_state=company_state,
        min_connections=0,          # DISABLED
        use_city_filter=False       # DISABLED
    )
    step1_time = time.time() - step1_start

    if not step1_result.get('success'):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return

    enriched = step1_result['enriched_prospects']
    print(f"✅ Step 1 complete ({step1_time:.1f}s): {len(enriched)} profiles from BrightData")

    # Step 2: Filter (no scraping)
    print(f"\n[STEP 2] Filtering profiles (no scraping)...")
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
    print(f"✅ Step 2 complete ({step2_time:.1f}s): {len(filtered)} filtered profiles")

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
    ai_cost = len(filtered) * 0.03
    total_cost = brightdata_cost + ai_cost

    print(f"\n📊 BRIGHTDATA EXPANDED FILTERS SUMMARY:")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Step 1 (BrightData): {step1_time:.1f}s, ${brightdata_cost:.2f}")
    print(f"   Step 2 (Filter): {step2_time:.1f}s, $0.00")
    print(f"   Step 3 (AI): {step3_time:.1f}s, ${ai_cost:.2f}")
    print(f"   Total cost: ${total_cost:.2f}")
    print(f"   Profiles → Filtered → Qualified: {len(enriched)} → {len(filtered)} → {len(qualified)}")

    # Display prospects
    print("\n🏆 QUALIFIED PROSPECTS:")
    for i, prospect in enumerate(qualified, 1):
        name = prospect['linkedin_data'].get('name', 'Unknown')
        title = prospect['linkedin_data'].get('job_title', 'Unknown')
        score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
        url = prospect.get('linkedin_url', '')
        print(f"   {i}. {name}")
        print(f"      Title: {title}")
        print(f"      Score: {score}/100")
        print(f"      URL: {url}")
        print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"brightdata_expanded_test_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'test_company': {
                'name': company_name,
                'parent': parent_account_name,
                'city': company_city,
                'state': company_state
            },
            'filter_improvements': {
                'min_connections': '20 → 0 (disabled)',
                'city_filter': 'Enabled → Disabled',
                'titles_added': [
                    'Facilities Director',
                    'Maintenance Manager',
                    'Finance Manager',
                    'COO'
                ],
                'total_title_filters': len(service.default_target_titles)
            },
            'results': {
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
            },
            'timestamp': timestamp
        }, f, indent=2)

    print(f"✅ Results saved to: {output_file}")

    # Comparison with previous test
    print("\n" + "="*80)
    print("COMPARISON WITH PREVIOUS TEST:")
    print("="*80)
    print("BEFORE (Old Filters):")
    print("   - 20 title filters (included broad keywords)")
    print("   - Min connections: 20")
    print("   - City filter: ENABLED")
    print("   - Results: 1 profile → 1 qualified")
    print()
    print("AFTER (Expanded Filters):")
    print(f"   - {len(service.default_target_titles)} title filters (specific titles only)")
    print("   - Min connections: 0 (disabled)")
    print("   - City filter: DISABLED")
    print(f"   - Results: {len(enriched)} profiles → {len(qualified)} qualified")
    print()

    improvement = len(qualified) - 1  # Previous test had 1 qualified
    if improvement > 0:
        print(f"✅ IMPROVEMENT: +{improvement} qualified prospect(s)!")
    elif improvement == 0:
        print("⚠️  Same results as before")
    else:
        print("❌ Worse results than before")

    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_brightdata_expanded())
