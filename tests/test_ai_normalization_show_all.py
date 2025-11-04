"""
Test AI Company Normalization - Show All Profiles Including Non-Qualified
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


async def test_show_all_profiles():
    """
    Run full 3-step pipeline and show ALL profiles with their AI scores
    """
    print("\n" + "="*80)
    print("AI NORMALIZATION - ALL PROFILES WITH SCORES")
    print("="*80)

    company_name = "BENEFIS HOSPITALS INC"
    parent_account_name = "Benefis Health System"
    company_city = "Great Falls"
    company_state = "Montana"

    print(f"\nTest Company: {company_name}")
    print(f"Parent Account: {parent_account_name}")
    print(f"Location: {company_city}, {company_state}")

    service = BrightDataProspectDiscoveryService()

    # Step 1: BrightData Filter
    print(f"\n[STEP 1] BrightData filtering with AI normalization...")
    step1_result = await service.step1_brightdata_filter(
        company_name=company_name,
        parent_account_name=parent_account_name,
        company_city=company_city,
        company_state=company_state,
        min_connections=0,
        use_city_filter=False
    )

    if not step1_result.get('success'):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return

    enriched = step1_result['enriched_prospects']
    print(f"✅ Found {len(enriched)} profiles")

    # Step 2: Filter
    print(f"\n[STEP 2] Company validation filtering...")
    step2_result = await service.step2_filter_prospects(
        enriched_prospects=enriched,
        company_name=company_name,
        company_city=company_city,
        company_state=company_state
    )

    if not step2_result.get('success'):
        print(f"❌ Step 2 failed: {step2_result.get('error')}")
        return

    filtered = step2_result['enriched_prospects']
    print(f"✅ {len(filtered)} profiles passed validation")

    # Step 3: AI Rank - BUT GET ALL PROFILES WITH SCORES
    print(f"\n[STEP 3] AI ranking all {len(filtered)} profiles...")

    # Call step3 with min_score_threshold=0 to get ALL profiles with scores
    step3_result = await service.step3_rank_prospects(
        enriched_prospects=filtered,
        company_name=company_name,
        min_score_threshold=0,  # Get ALL profiles
        max_prospects=100  # No limit
    )

    if not step3_result.get('success'):
        print(f"❌ Step 3 failed: {step3_result.get('error')}")
        return

    all_ranked = step3_result['qualified_prospects']

    # Sort by score descending
    all_ranked.sort(key=lambda x: x.get('ai_ranking', {}).get('ranking_score', 0), reverse=True)

    # Separate into qualified (≥65) and non-qualified (<65)
    qualified = [p for p in all_ranked if p.get('ai_ranking', {}).get('ranking_score', 0) >= 65]
    non_qualified = [p for p in all_ranked if p.get('ai_ranking', {}).get('ranking_score', 0) < 65]

    print(f"✅ AI ranking complete: {len(qualified)} qualified (≥65), {len(non_qualified)} below threshold")

    # Display ALL profiles
    print("\n" + "="*80)
    print(f"ALL {len(all_ranked)} PROFILES WITH AI SCORES (Sorted by Score)")
    print("="*80)

    if qualified:
        print(f"\n🏆 QUALIFIED PROSPECTS (Score ≥65): {len(qualified)} profiles")
        print("-"*80)
        for i, prospect in enumerate(qualified, 1):
            name = prospect['linkedin_data'].get('name', 'Unknown')
            title = prospect['linkedin_data'].get('job_title', 'Unknown')
            company = prospect['linkedin_data'].get('company_name', 'Unknown')
            location = prospect['linkedin_data'].get('location', 'Unknown')
            score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
            reasoning = prospect.get('ai_ranking', {}).get('reasoning', 'No reasoning provided')
            url = prospect.get('linkedin_url', '')

            print(f"\n{i}. {name}")
            print(f"   Title:     {title}")
            print(f"   Company:   {company}")
            print(f"   Location:  {location}")
            print(f"   Score:     ✅ {score}/100")
            print(f"   Reasoning: {reasoning[:150]}..." if len(reasoning) > 150 else f"   Reasoning: {reasoning}")
            print(f"   URL:       {url}")

    if non_qualified:
        print(f"\n\n❌ NON-QUALIFIED PROFILES (Score <65): {len(non_qualified)} profiles")
        print("-"*80)
        for i, prospect in enumerate(non_qualified, 1):
            name = prospect['linkedin_data'].get('name', 'Unknown')
            title = prospect['linkedin_data'].get('job_title', 'Unknown')
            company = prospect['linkedin_data'].get('company_name', 'Unknown')
            location = prospect['linkedin_data'].get('location', 'Unknown')
            score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
            reasoning = prospect.get('ai_ranking', {}).get('reasoning', 'No reasoning provided')
            url = prospect.get('linkedin_url', '')

            print(f"\n{i}. {name}")
            print(f"   Title:     {title}")
            print(f"   Company:   {company}")
            print(f"   Location:  {location}")
            print(f"   Score:     ❌ {score}/100")
            print(f"   Reasoning: {reasoning[:150]}..." if len(reasoning) > 150 else f"   Reasoning: {reasoning}")
            print(f"   URL:       {url}")

    # Summary
    print("\n" + "="*80)
    print("SCORE DISTRIBUTION")
    print("="*80)

    score_ranges = {
        '80-100': 0,
        '70-79': 0,
        '65-69': 0,
        '60-64': 0,
        '50-59': 0,
        '<50': 0
    }

    for prospect in all_ranked:
        score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
        if score >= 80:
            score_ranges['80-100'] += 1
        elif score >= 70:
            score_ranges['70-79'] += 1
        elif score >= 65:
            score_ranges['65-69'] += 1
        elif score >= 60:
            score_ranges['60-64'] += 1
        elif score >= 50:
            score_ranges['50-59'] += 1
        else:
            score_ranges['<50'] += 1

    print(f"80-100 (Excellent):  {score_ranges['80-100']:2d} profiles")
    print(f"70-79  (Good):       {score_ranges['70-79']:2d} profiles")
    print(f"65-69  (Qualified):  {score_ranges['65-69']:2d} profiles")
    print(f"60-64  (Close):      {score_ranges['60-64']:2d} profiles")
    print(f"50-59  (Marginal):   {score_ranges['50-59']:2d} profiles")
    print(f"<50    (Poor fit):   {score_ranges['<50']:2d} profiles")
    print("-"*80)
    print(f"Total:               {len(all_ranked):2d} profiles")
    print(f"Qualified (≥65):     {len(qualified):2d} profiles ({len(qualified)/len(all_ranked)*100:.1f}%)")
    print("="*80)

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"ai_normalization_all_profiles_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'test_company': {
                'name': company_name,
                'parent': parent_account_name,
                'city': company_city,
                'state': company_state
            },
            'summary': {
                'total_profiles': len(all_ranked),
                'qualified': len(qualified),
                'non_qualified': len(non_qualified),
                'qualification_rate': f"{len(qualified)/len(all_ranked)*100:.1f}%"
            },
            'score_distribution': score_ranges,
            'qualified_profiles': qualified,
            'non_qualified_profiles': non_qualified,
            'timestamp': timestamp
        }, f, indent=2)

    print(f"\n✅ Detailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(test_show_all_profiles())
