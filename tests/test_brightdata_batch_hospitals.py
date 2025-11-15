"""
Batch Test: BrightData 3-Step Pipeline for Multiple Hospitals
Processes all hospitals from HospitalAccountsAndIDs.csv
Outputs comprehensive CSV with all prospect data
"""

import asyncio
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService
from app.services.salesforce import SalesforceService


# State abbreviation mapping
STATE_ABBREV_MAP = {
    'MT': 'Montana',
    'ID': 'Idaho',
    'CA': 'California',
    'OR': 'Oregon',
    'WA': 'Washington',
    'NV': 'Nevada',
    'UT': 'Utah',
    'WY': 'Wyoming',
    'CO': 'Colorado',
    'AZ': 'Arizona',
    'NM': 'New Mexico'
}


async def process_hospital(service, hospital_data, csv_writer, csv_file, parent_account_name=None):
    """
    Process a single hospital through the full 3-step pipeline
    """
    company_name = hospital_data['Hospital']
    company_city = hospital_data['City']
    company_state_abbrev = hospital_data['State']
    account_id = hospital_data['Account ID']

    # Expand state abbreviation
    company_state = STATE_ABBREV_MAP.get(company_state_abbrev, company_state_abbrev)

    print(f"\n{'='*80}")
    print(f"🏥 PROCESSING: {company_name}")
    print(f"📍 Location: {company_city}, {company_state}")
    print(f"🆔 Account ID: {account_id}")
    if parent_account_name:
        print(f"👨‍👩‍👧‍👦 Parent Account: {parent_account_name}")
    print('='*80)

    result = {
        'hospital': company_name,
        'city': company_city,
        'state': company_state,
        'state_abbrev': company_state_abbrev,
        'account_id': account_id,
        'success': False,
        'error': None,
        'timing': {},
        'funnel': {},
        'qualified_prospects': []
    }

    try:
        pipeline_start = time.time()

        # Step 1: BrightData Filter with AI Normalization
        print(f"\n{'─'*80}")
        print(f"📊 STEP 1: BrightData Filtering with AI Company Normalization")
        print(f"{'─'*80}")
        print(f"⚙️  Generating AI company name variations...")
        print(f"⚙️  Filtering LinkedIn dataset via BrightData API...")
        step1_start = time.time()
        step1_result = await service.step1_brightdata_filter(
            company_name=company_name,
            parent_account_name=parent_account_name or company_name,  # Use parent if available, else company name
            company_city=company_city,
            company_state=company_state,
            min_connections=20,
            use_city_filter=False
        )
        step1_time = time.time() - step1_start

        if not step1_result.get('success'):
            result['error'] = f"Step 1 failed: {step1_result.get('error')}"
            print(f"❌ STEP 1 FAILED: {result['error']}")
            return result

        enriched = step1_result['enriched_prospects']
        print(f"✅ STEP 1 COMPLETE ({step1_time:.1f}s)")
        print(f"   📈 Found {len(enriched)} LinkedIn profiles")

        # Step 2: Company Validation Filter
        print(f"\n{'─'*80}")
        print(f"🔍 STEP 2: Company Validation Filtering")
        print(f"{'─'*80}")
        print(f"⚙️  Validating current employment at {company_name}...")
        print(f"⚙️  Checking company name variations and aliases...")
        step2_start = time.time()
        step2_result = await service.step2_filter_prospects(
            enriched_prospects=enriched,
            company_name=company_name,
            company_city=company_city,
            company_state=company_state
        )
        step2_time = time.time() - step2_start

        if not step2_result.get('success'):
            result['error'] = f"Step 2 failed: {step2_result.get('error')}"
            print(f"❌ STEP 2 FAILED: {result['error']}")
            return result

        filtered = step2_result['enriched_prospects']
        filtered_out = len(enriched) - len(filtered)
        print(f"✅ STEP 2 COMPLETE ({step2_time:.1f}s)")
        print(f"   📈 {len(filtered)} profiles passed validation")
        if filtered_out > 0:
            print(f"   ❌ {filtered_out} profiles filtered out ({filtered_out/len(enriched)*100:.1f}%)")

        # Step 3: AI Ranking
        print(f"\n{'─'*80}")
        print(f"🤖 STEP 3: AI Ranking and Qualification")
        print(f"{'─'*80}")
        print(f"⚙️  Analyzing {len(filtered)} profiles with AI...")
        print(f"⚙️  Scoring decision-making authority and relevance...")
        step3_start = time.time()
        step3_result = await service.step3_rank_prospects(
            enriched_prospects=filtered,
            company_name=company_name,
            min_score_threshold=65,
            max_prospects=120
        )
        step3_time = time.time() - step3_start

        if not step3_result.get('success'):
            result['error'] = f"Step 3 failed: {step3_result.get('error')}"
            print(f"❌ STEP 3 FAILED: {result['error']}")
            return result

        qualified = step3_result['qualified_prospects']
        print(f"✅ STEP 3 COMPLETE ({step3_time:.1f}s)")
        print(f"   📈 {len(qualified)} qualified prospects (score ≥65)")

        total_time = time.time() - pipeline_start

        # Build result
        result['success'] = True
        result['timing'] = {
            'step1': step1_time,
            'step2': step2_time,
            'step3': step3_time,
            'total': total_time
        }
        result['funnel'] = {
            'step1_profiles': len(enriched),
            'step2_filtered': len(filtered),
            'step3_qualified': len(qualified),
            'step2_pass_rate': f"{len(filtered)/len(enriched)*100:.1f}%" if enriched else "N/A",
            'step3_pass_rate': f"{len(qualified)/len(filtered)*100:.1f}%" if filtered else "N/A",
            'overall_conversion': f"{len(qualified)/len(enriched)*100:.1f}%" if enriched else "N/A"
        }
        result['qualified_prospects'] = qualified

        # Display and write qualified prospects to CSV
        if qualified:
            print(f"\n{'─'*80}")
            print(f"🏆 QUALIFIED PROSPECTS: {len(qualified)} found")
            print(f"{'─'*80}")
            for i, prospect in enumerate(qualified, 1):
                linkedin_data = prospect.get('linkedin_data', {})
                ai_ranking = prospect.get('ai_ranking', {})

                name = linkedin_data.get('name', 'Unknown')
                title = linkedin_data.get('job_title', 'Unknown')
                score = ai_ranking.get('ranking_score', 0)
                reasoning = ai_ranking.get('ranking_reasoning', '')

                print(f"   {i}. {name}")
                print(f"      Title: {title}")
                print(f"      Score: {score}/100")
                print(f"      URL: {prospect.get('linkedin_url', '')}")

                # Write to CSV
                csv_row = {
                    'Hospital_Name': company_name,
                    'Hospital_City': company_city,
                    'Hospital_State': company_state,
                    'Parent_Account': parent_account_name or company_name,  # Use parent if available
                    'Account_ID': account_id,
                    'Prospect_Name': name,
                    'First_Name': linkedin_data.get('first_name', ''),
                    'Last_Name': linkedin_data.get('last_name', ''),
                    'Job_Title': title,
                    'LinkedIn_URL': prospect.get('linkedin_url', ''),
                    'Location': linkedin_data.get('location', ''),
                    'City': linkedin_data.get('city', ''),
                    'State': linkedin_data.get('state', ''),
                    'Country': linkedin_data.get('country', ''),
                    'Company_Name': linkedin_data.get('company_name', ''),
                    'Headline': linkedin_data.get('headline', ''),
                    'About': linkedin_data.get('about', ''),
                    'Summary': linkedin_data.get('summary', ''),
                    'Connections': linkedin_data.get('connections', ''),
                    'Followers': linkedin_data.get('followers', ''),
                    'Profile_Completeness_Score': linkedin_data.get('profile_completeness_score', ''),
                    'Accessibility_Score': linkedin_data.get('accessibility_score', ''),
                    'Engagement_Score': linkedin_data.get('engagement_score', ''),
                    'AI_Ranking_Score': score,
                    'AI_Reasoning': reasoning,
                    'Data_Source': prospect.get('data_source', 'brightdata'),
                    'Discovery_Date': datetime.now().strftime('%Y-%m-%d'),
                    'Pipeline_Step1_Time': step1_time,
                    'Pipeline_Step2_Time': step2_time,
                    'Pipeline_Step3_Time': step3_time,
                    'Pipeline_Total_Time': total_time
                }
                csv_writer.writerow(csv_row)
                csv_file.flush()  # Ensure data is written immediately

            print(f"✅ {len(qualified)} prospects written to CSV")
        else:
            print(f"\n❌ No prospects qualified with score ≥65")

        return result

    except Exception as e:
        result['error'] = f"Exception: {str(e)}"
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return result


async def run_batch_test():
    """
    Run batch test on all hospitals from CSV
    """
    print("\n" + "="*80)
    print("🚀 BRIGHTDATA BATCH TEST - MULTIPLE HOSPITALS")
    print("="*80)

    # Read input CSV file
    input_csv_path = Path(__file__).parent.parent / 'docs' / 'archive' / 'HospitalAccountsAndIDs.csv'

    if not input_csv_path.exists():
        print(f"❌ Input CSV file not found: {input_csv_path}")
        return

    hospitals = []
    with open(input_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hospitals.append(row)

    print(f"\n📋 Loaded {len(hospitals)} hospitals from input CSV")
    print(f"   Input File: {input_csv_path}")

    # Connect to Salesforce to get parent account names
    print(f"\n🔗 Connecting to Salesforce to fetch parent account names...")
    sf_service = SalesforceService()
    sf_connected = await sf_service.connect()

    parent_account_map = {}
    if sf_connected:
        print(f"✅ Connected to Salesforce")
        print(f"📊 Fetching parent account names for {len(hospitals)} hospitals...")

        for hospital in hospitals:
            account_id = hospital['Account ID']
            try:
                # Query for parent account
                query = f"SELECT Name, ParentId, Parent.Name FROM Account WHERE Id = '{account_id}'"
                result = sf_service.sf.query(query)

                if result['totalSize'] > 0:
                    record = result['records'][0]
                    parent_id = record.get('ParentId')
                    parent_name = record.get('Parent', {}).get('Name') if record.get('Parent') else None

                    if parent_name:
                        parent_account_map[account_id] = parent_name
                        print(f"   ✅ {hospital['Hospital'][:40]:40s} → Parent: {parent_name}")
                    else:
                        print(f"   ⚠️  {hospital['Hospital'][:40]:40s} → No parent account")
                else:
                    print(f"   ❌ {hospital['Hospital'][:40]:40s} → Account not found in Salesforce")
            except Exception as e:
                print(f"   ❌ {hospital['Hospital'][:40]:40s} → Error: {str(e)}")

        print(f"✅ Found parent accounts for {len(parent_account_map)}/{len(hospitals)} hospitals")
    else:
        print(f"⚠️  Could not connect to Salesforce - proceeding without parent account names")
        print(f"   AI will only use hospital names for company variations")

    # Create output CSV files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv_path = f"brightdata_batch_prospects_{timestamp}.csv"
    failed_csv_path = f"brightdata_batch_failed_hospitals_{timestamp}.csv"

    # Define prospect CSV columns
    csv_columns = [
        'Hospital_Name', 'Hospital_City', 'Hospital_State', 'Parent_Account', 'Account_ID',
        'Prospect_Name', 'First_Name', 'Last_Name', 'Job_Title', 'LinkedIn_URL',
        'Location', 'City', 'State', 'Country', 'Company_Name',
        'Headline', 'About', 'Summary', 'Connections', 'Followers',
        'Profile_Completeness_Score', 'Accessibility_Score', 'Engagement_Score',
        'AI_Ranking_Score', 'AI_Reasoning', 'Data_Source', 'Discovery_Date',
        'Pipeline_Step1_Time', 'Pipeline_Step2_Time', 'Pipeline_Step3_Time', 'Pipeline_Total_Time'
    ]

    # Define failed hospitals CSV columns (same format as input CSV for easy re-processing)
    failed_csv_columns = ['Hospital', 'City', 'State', 'Account ID', 'Failure_Reason']

    print(f"\n📄 Output files:")
    print(f"   Prospects CSV: {output_csv_path}")
    print(f"   Failed hospitals CSV: {failed_csv_path}")
    print(f"   Columns: {len(csv_columns)} fields per prospect")

    # Initialize service
    service = BrightDataProspectDiscoveryService()

    # Open output CSV files
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csv_file, \
         open(failed_csv_path, 'w', newline='', encoding='utf-8') as failed_csv_file:

        csv_writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
        csv_writer.writeheader()
        csv_file.flush()

        failed_csv_writer = csv.DictWriter(failed_csv_file, fieldnames=failed_csv_columns)
        failed_csv_writer.writeheader()
        failed_csv_file.flush()

        print(f"\n✅ CSV files created with headers")

        # Process each hospital
        batch_start = time.time()
        results = []

        for i, hospital_data in enumerate(hospitals, 1):
            print(f"\n\n{'#'*80}")
            print(f"🏥 HOSPITAL {i} of {len(hospitals)}")
            print(f"{'#'*80}")

            # Get parent account name for this hospital
            account_id = hospital_data['Account ID']
            parent_account_name = parent_account_map.get(account_id)

            result = await process_hospital(service, hospital_data, csv_writer, csv_file, parent_account_name)
            results.append(result)

            # If hospital failed or returned 0 qualified prospects, add to failed CSV
            if not result['success'] or result['funnel'].get('step3_qualified', 0) == 0:
                failure_reason = result.get('error', 'No qualified prospects found')
                failed_csv_writer.writerow({
                    'Hospital': hospital_data['Hospital'],
                    'City': hospital_data['City'],
                    'State': hospital_data['State'],
                    'Account ID': hospital_data['Account ID'],
                    'Failure_Reason': failure_reason
                })
                failed_csv_file.flush()
                print(f"   ⚠️  Added to failed hospitals CSV for failover processing")

            # Small delay between hospitals
            if i < len(hospitals):
                print(f"\n⏸️  Waiting 2 seconds before next hospital...")
                await asyncio.sleep(2)

        batch_time = time.time() - batch_start

    # Calculate aggregate statistics
    print("\n\n" + "="*80)
    print("📊 BATCH TEST SUMMARY")
    print("="*80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    no_prospects = [r for r in results if r['success'] and r['funnel'].get('step3_qualified', 0) == 0]
    needs_failover = [r for r in results if not r['success'] or r['funnel'].get('step3_qualified', 0) == 0]

    total_profiles = sum(r['funnel'].get('step1_profiles', 0) for r in successful)
    total_filtered = sum(r['funnel'].get('step2_filtered', 0) for r in successful)
    total_qualified = sum(r['funnel'].get('step3_qualified', 0) for r in successful)

    print(f"\n🏥 HOSPITAL PROCESSING:")
    print(f"   Total Hospitals:             {len(hospitals)}")
    print(f"   ✅ Successful with prospects: {len(successful) - len(no_prospects)} ({(len(successful) - len(no_prospects))/len(hospitals)*100:.1f}%)")
    print(f"   ⚠️  Successful but no prospects: {len(no_prospects)} ({len(no_prospects)/len(hospitals)*100:.1f}%)")
    print(f"   ❌ Failed (errors):           {len(failed)} ({len(failed)/len(hospitals)*100:.1f}%)")
    print(f"   🔄 Need failover processing:  {len(needs_failover)} ({len(needs_failover)/len(hospitals)*100:.1f}%)")

    print(f"\n📈 AGGREGATE FUNNEL (All Hospitals Combined):")
    print(f"   Profiles Found (Step 1):    {total_profiles}")
    print(f"   Profiles Validated (Step 2): {total_filtered} ({total_filtered/total_profiles*100:.1f}% pass rate)" if total_profiles else "   Profiles Validated:         0")
    print(f"   Prospects Qualified (Step 3): {total_qualified} ({total_qualified/total_filtered*100:.1f}% of validated)" if total_filtered else "   Prospects Qualified:        0")
    print(f"   Overall Conversion Rate:    {total_qualified/total_profiles*100:.1f}% ({total_profiles} → {total_qualified})" if total_profiles else "   Overall Conversion:         N/A")

    print(f"\n⏱️  TIMING:")
    print(f"   Total Batch Time:       {batch_time:.1f}s ({batch_time/60:.1f} minutes)")
    print(f"   Average per Hospital:   {batch_time/len(hospitals):.1f}s")

    print(f"\n📄 OUTPUT FILES:")
    print(f"   ✅ Prospects CSV: {output_csv_path}")
    print(f"      Total prospects written: {total_qualified}")
    print(f"   ⚠️  Failed hospitals CSV: {failed_csv_path}")
    print(f"      Hospitals needing failover: {len(needs_failover)}")
    if len(needs_failover) > 0:
        print(f"      👉 Use this file as input for failover batch script")

    # Per-hospital breakdown
    print("\n" + "="*80)
    print("📋 PER-HOSPITAL BREAKDOWN")
    print("="*80)

    for i, result in enumerate(results, 1):
        status = "✅" if result['success'] else "❌"
        hospital = result['hospital']

        if result['success']:
            funnel = result['funnel']
            qualified = funnel['step3_qualified']
            print(f"\n{i:2d}. {status} {hospital}")
            print(f"      Location:  {result['city']}, {result['state']}")
            print(f"      Funnel:    {funnel['step1_profiles']} → {funnel['step2_filtered']} → {funnel['step3_qualified']}")
            print(f"      Time:      {result['timing']['total']:.1f}s")
            print(f"      Qualified: {qualified} prospects")
        else:
            print(f"\n{i:2d}. {status} {hospital}")
            print(f"      Location:  {result['city']}, {result['state']}")
            print(f"      Error:     {result['error']}")

    # Save detailed JSON results
    output_json = f"brightdata_batch_test_{timestamp}.json"

    with open(output_json, 'w') as f:
        json.dump({
            'test_info': {
                'timestamp': timestamp,
                'total_hospitals': len(hospitals),
                'input_csv': str(input_csv_path),
                'output_csv': output_csv_path
            },
            'summary': {
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': f"{len(successful)/len(hospitals)*100:.1f}%",
                'total_profiles': total_profiles,
                'total_filtered': total_filtered,
                'total_qualified': total_qualified,
                'overall_conversion': f"{total_qualified/total_profiles*100:.1f}%" if total_profiles else "N/A",
                'batch_time_seconds': batch_time,
                'avg_time_per_hospital': batch_time/len(hospitals)
            },
            'results': results
        }, f, indent=2)

    print(f"   ✅ JSON details: {output_json}")
    print("="*80)
    print(f"\n✅ BATCH TEST COMPLETE!")
    print(f"   Total qualified prospects: {total_qualified}")
    print(f"   Prospects CSV: {output_csv_path}")
    if len(needs_failover) > 0:
        print(f"\n⚠️  FAILOVER NEEDED:")
        print(f"   {len(needs_failover)} hospitals need to be processed with failover pipeline")
        print(f"   Failed hospitals CSV: {failed_csv_path}")
        print(f"   👉 Next step: Run failover batch script with this CSV as input")
    else:
        print(f"\n🎉 All hospitals successfully processed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_batch_test())
