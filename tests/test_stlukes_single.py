"""
Test St. Luke's Regional Medical Center with Parent Account
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


async def test_stlukes():
    """
    Test St. Luke's Regional Medical Center
    """
    print("\n" + "="*80)
    print("ST. LUKE'S BOISE MEDICAL CENTER - SINGLE HOSPITAL TEST")
    print("="*80)

    # St. Luke's data from CSV
    company_name = "St. Luke's Boise Medical Center"
    company_city = "Boise"
    company_state = "Idaho"
    account_id = "001VR00000XQCPYYA5"

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

    # Show sample profiles
    if enriched:
        print(f"\n📋 Sample profiles found (first 5):")
        for i, prospect in enumerate(enriched[:5], 1):
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

    # Step 3: AI Ranking
    print(f"\n{'─'*80}")
    print(f"🤖 STEP 3: AI Ranking and Qualification")
    print(f"{'─'*80}")

    step3_result = await service.step3_rank_prospects(
        enriched_prospects=filtered,
        company_name=company_name,
        min_score_threshold=65,
        max_prospects=10
    )

    if not step3_result.get('success'):
        print(f"❌ Step 3 failed: {step3_result.get('error')}")
        return

    qualified = step3_result['qualified_prospects']
    print(f"✅ Step 3 complete: {len(qualified)} qualified prospects (score ≥65)")

    # Display results
    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"Funnel: {len(enriched)} → {len(filtered)} → {len(qualified)}")
    print(f"Conversion: {len(qualified)/len(enriched)*100:.1f}%" if enriched else "N/A")

    if qualified:
        print(f"\n🏆 QUALIFIED PROSPECTS:")
        for i, prospect in enumerate(qualified, 1):
            name = prospect['linkedin_data'].get('name', 'Unknown')
            title = prospect['linkedin_data'].get('job_title', 'Unknown')
            score = prospect.get('ai_ranking', {}).get('ranking_score', 0)
            reasoning = prospect.get('ai_ranking', {}).get('ranking_reasoning', '')
            url = prospect.get('linkedin_url', '')

            print(f"\n{i}. {name}")
            print(f"   Title:     {title}")
            print(f"   Score:     {score}/100")
            print(f"   Reasoning: {reasoning[:150]}..." if len(reasoning) > 150 else f"   Reasoning: {reasoning}")
            print(f"   URL:       {url}")
    else:
        print(f"\n❌ No prospects qualified with score ≥65")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_stlukes())
