"""
Test St. Joseph Regional Medical Center - Show All Profiles with AI Scores
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService
from app.services.salesforce import SalesforceService


async def test_stjoseph():
    """
    Test St. Joseph Regional Medical Center with full scoring details
    """
    print("\n" + "="*80)
    print("ST. JOSEPH REGIONAL MEDICAL CENTER - SINGLE HOSPITAL TEST")
    print("="*80)

    # St. Joseph data from batch run
    company_name = "St. Joseph Regional Medical Center"
    company_city = "Lewiston"
    company_state = "Idaho"
    account_id = "001VR00000UhY3oYAF"

    print(f"\n🏥 Hospital: {company_name}")
    print(f"📍 Location: {company_city}, {company_state}")
    print(f"🆔 Account ID: {account_id}")

    # Connect to Salesforce to get parent account
    print(f"\n🔗 Connecting to Salesforce...")
    sf_service = SalesforceService()
    sf_connected = await sf_service.connect()

    parent_account_name = None
    if sf_connected:
        print(f"✅ Connected to Salesforce")
        try:
            query = f"SELECT Name, ParentId, Parent.Name FROM Account WHERE Id = '{account_id}'"
            result = sf_service.sf.query(query)

            if result['totalSize'] > 0:
                record = result['records'][0]
                parent_name = record.get('Parent', {}).get('Name') if record.get('Parent') else None

                if parent_name:
                    parent_account_name = parent_name
                    print(f"👨‍👩‍👧‍👦 Parent Account: {parent_account_name}")
                else:
                    print(f"⚠️  No parent account found")
            else:
                print(f"❌ Account not found in Salesforce")
        except Exception as e:
            print(f"❌ Error querying Salesforce: {e}")
    else:
        print(f"⚠️  Could not connect to Salesforce")

    # Initialize service
    service = BrightDataProspectDiscoveryService()

    # Step 1: BrightData Filter
    print(f"\n{'─'*80}")
    print(f"📊 STEP 1: BrightData Filtering with AI Company Normalization")
    print(f"{'─'*80}")

    step1_result = await service.step1_brightdata_filter(
        company_name=company_name,
        parent_account_name=parent_account_name or company_name,
        company_city=company_city,
        company_state=company_state,
        min_connections=0,
        use_city_filter=False
    )

    if not step1_result.get('success'):
        print(f"❌ Step 1 failed: {step1_result.get('error')}")
        return

    enriched = step1_result['enriched_prospects']
    print(f"✅ Step 1 complete: {len(enriched)} profiles found")

    # Show all profiles found
    if enriched:
        print(f"\n📋 All profiles found:")
        for i, prospect in enumerate(enriched, 1):
            name = prospect['linkedin_data'].get('name', 'Unknown')
            title = prospect['linkedin_data'].get('job_title', 'Unknown')
            company = prospect['linkedin_data'].get('company_name', 'Unknown')
            print(f"   {i}. {name} - {title} at {company}")

    # Step 2: Filter
    print(f"\n{'─'*80}")
    print(f"🔍 STEP 2: Company Validation Filtering")
    print(f"{'─'*80}")

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
    filtered_out = len(enriched) - len(filtered)
    print(f"✅ Step 2 complete: {len(filtered)} profiles passed validation")
    if filtered_out > 0:
        print(f"   ❌ {filtered_out} profiles filtered out ({filtered_out/len(enriched)*100:.1f}%)")

    # Step 3: AI Rank - GET ALL PROFILES WITH SCORES (no threshold)
    print(f"\n{'─'*80}")
    print(f"🤖 STEP 3: AI Ranking ALL {len(filtered)} profiles (no threshold)")
    print(f"{'─'*80}")

    step3_result = await service.step3_rank_prospects(
        enriched_prospects=filtered,
        company_name=company_name,
        min_score_threshold=0,  # Get ALL profiles with scores
        max_prospects=100
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

    print(f"✅ AI ranking complete")
    print(f"   🏆 {len(qualified)} profiles scored ≥65 (qualified)")
    print(f"   ❌ {len(non_qualified)} profiles scored <65 (not qualified)")

    # Display ALL profiles with scores
    print(f"\n{'='*80}")
    print(f"ALL {len(all_ranked)} PROFILES WITH AI SCORES (Sorted by Score)")
    print(f"{'='*80}")

    if qualified:
        print(f"\n🏆 QUALIFIED PROSPECTS (Score ≥65): {len(qualified)} profiles")
        print("-"*80)
        for i, prospect in enumerate(qualified, 1):
            name = prospect['linkedin_data'].get('name', 'Unknown')
            title = prospect['linkedin_data'].get('job_title', 'Unknown')
            company = prospect['linkedin_data'].get('company_name', 'Unknown')
            location = prospect['linkedin_data'].get('location', 'Unknown')
            score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
            reasoning = prospect.get('ai_ranking', {}).get('ranking_reasoning', 'No reasoning provided')
            url = prospect.get('linkedin_url', '')

            print(f"\n{i}. {name}")
            print(f"   Title:     {title}")
            print(f"   Company:   {company}")
            print(f"   Location:  {location}")
            print(f"   Score:     ✅ {score}/100")
            print(f"   Reasoning: {reasoning}")
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
            reasoning = prospect.get('ai_ranking', {}).get('ranking_reasoning', 'No reasoning provided')
            url = prospect.get('linkedin_url', '')

            print(f"\n{i}. {name}")
            print(f"   Title:     {title}")
            print(f"   Company:   {company}")
            print(f"   Location:  {location}")
            print(f"   Score:     ❌ {score}/100")
            print(f"   Reasoning: {reasoning}")
            print(f"   URL:       {url}")

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total profiles found:    {len(enriched)}")
    print(f"Passed validation:       {len(filtered)}")
    print(f"Qualified (≥65):         {len(qualified)}")
    print(f"Not qualified (<65):     {len(non_qualified)}")
    if all_ranked:
        avg_score = sum(p.get('ai_ranking', {}).get('ranking_score', 0) for p in all_ranked) / len(all_ranked)
        print(f"Average score:           {avg_score:.1f}/100")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_stjoseph())
