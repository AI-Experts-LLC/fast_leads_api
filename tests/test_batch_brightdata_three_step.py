#!/usr/bin/env python3
"""
Batch test for Bright Data 3-Step Prospect Discovery (No Scraping!)
Tests 3 hospitals from the same ones used in test_brightdata_with_salesforce.py

This version:
- Step 1: Bright Data Filter + Transform (no Serper)
- Step 2: Filter Only (no Apify scraping!)
- Step 3: AI Ranking (same as before)
"""
import asyncio
import sys
import os
import csv
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService
from app.services.salesforce import salesforce_service


# Test hospitals - same as test_brightdata_with_salesforce.py
TEST_HOSPITALS = [
    {
        "account_id": "001VR00000Vh74QYAR",
        "name": "Portneuf Health System",
        "city": "Pocatello",
        "state": "Idaho"
    },
    {
        "account_id": "001VR00000UhXwBYAV",
        "name": "BENEFIS HOSPITALS INC",
        "city": "Great Falls",
        "state": "Montana",
        "parent_account": "Benefis Health System"
    },
    {
        "account_id": "0017V00001YEA77QAH",
        "name": "Billings Clinic",
        "city": "Billings",
        "state": "Montana"
    }
]


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*100)
    print(f"  {title}")
    print("="*100 + "\n")


def save_results_to_csv(results, output_dir):
    """Save batch results to CSV"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    filepath = output_path / "batch_summary.csv"

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Hospital Name', 'City', 'State', 'Parent Account', 'Account ID',
            'Step 1 Status', 'Step 2 Status', 'Step 3 Status',
            'BD Profiles Found', 'Profiles Transformed', 'After Filter',
            'Prospects Ranked', 'Final Qualified', 'Total Time (s)',
            'Step 1 Time (s)', 'Step 2 Time (s)', 'Step 3 Time (s)',
            'Scraping Skipped', 'Scraping Cost Saved',
            'Top Prospect Name', 'Top Prospect Title', 'Top Prospect Score',
            'Top Prospect LinkedIn', 'Top Prospect Email', 'Error Message'
        ])

        # Data rows
        for result in results:
            hospital = result['hospital']
            step1 = result.get('step1_summary', {})
            step2 = result.get('step2_summary', {})
            step3 = result.get('step3_summary', {})
            top_prospect = result.get('top_prospect', {})
            timing = result.get('timing', {})

            bd_profiles = step1.get('total_profiles_from_brightdata', 0)
            scraping_saved = bd_profiles * 0.0047

            writer.writerow([
                hospital['name'],
                hospital['city'],
                hospital['state'],
                hospital.get('parent_account', ''),
                hospital['account_id'],
                result.get('step1_status', 'Failed'),
                result.get('step2_status', 'Failed'),
                result.get('step3_status', 'Failed'),
                bd_profiles,
                step1.get('profiles_transformed', 0),
                step2.get('after_advanced_filter', 0),
                step3.get('prospects_ranked', 0),
                step3.get('final_top_prospects', 0),
                result.get('total_time', 0),
                timing.get('step1', 0),
                timing.get('step2', 0),
                timing.get('step3', 0),
                step1.get('scraping_skipped', False),
                f"${scraping_saved:.2f}",
                top_prospect.get('name', ''),
                top_prospect.get('title', ''),
                top_prospect.get('score', ''),
                top_prospect.get('linkedin_url', ''),
                top_prospect.get('email', ''),
                result.get('error_message', '')
            ])

    print(f"✅ Summary CSV saved to: {filepath}")
    return str(filepath)


async def process_hospital(service, hospital, index, total):
    """Process a single hospital through all 3 steps"""
    print_section(f"Hospital {index}/{total}: {hospital['name']} - {hospital['city']}, {hospital['state']}")

    result = {
        'hospital': hospital,
        'step1_status': 'Not Started',
        'step2_status': 'Not Started',
        'step3_status': 'Not Started',
        'total_time': 0,
        'timing': {},
        'error_message': ''
    }

    start_time = time.time()

    # ========== STEP 1: Bright Data Filter + Transform ==========
    print(f"\n🔍 Step 1: Bright Data Filter + Transform")
    print(f"   Company: {hospital['name']}")
    print(f"   Location: {hospital['city']}, {hospital['state']}")
    if hospital.get('parent_account'):
        print(f"   Parent: {hospital['parent_account']}")

    step1_start = time.time()

    try:
        step1_result = await service.step1_brightdata_filter(
            company_name=hospital['name'],
            parent_account_name=hospital.get('parent_account'),
            company_city=hospital['city'],
            company_state=hospital['state'],
            min_connections=20
        )

        step1_time = time.time() - step1_start
        result['timing']['step1'] = step1_time

        if step1_result.get('success'):
            result['step1_status'] = 'Success'
            result['step1_summary'] = step1_result.get('summary', {})
            enriched_prospects = step1_result.get('enriched_prospects', [])

            print(f"✅ Step 1 completed in {step1_time:.1f}s")
            print(f"   Profiles found: {result['step1_summary'].get('total_profiles_from_brightdata', 0)}")
            print(f"   Profiles transformed: {result['step1_summary'].get('profiles_transformed', 0)}")
            print(f"   ✅ Scraping skipped: {result['step1_summary'].get('scraping_skipped', False)}")

            if not enriched_prospects:
                result['step1_status'] = 'No Results'
                result['error_message'] = 'No profiles found in Bright Data'
                print(f"⚠️  No profiles found")
                result['total_time'] = time.time() - start_time
                return result

            # ========== STEP 2: Filter Prospects (No Scraping!) ==========
            print(f"\n🔍 Step 2: Filter Prospects (No Scraping!)")
            print(f"   Filtering {len(enriched_prospects)} prospects...")

            step2_start = time.time()

            step2_result = await service.step2_filter_prospects(
                enriched_prospects=enriched_prospects,
                company_name=hospital['name'],
                company_city=hospital['city'],
                company_state=hospital['state'],
                location_filter_enabled=True
            )

            step2_time = time.time() - step2_start
            result['timing']['step2'] = step2_time

            if step2_result.get('success'):
                result['step2_status'] = 'Success'
                result['step2_summary'] = step2_result.get('summary', {})
                filtered_prospects = step2_result.get('enriched_prospects', [])

                print(f"✅ Step 2 completed in {step2_time:.1f}s")
                print(f"   After advanced filter: {result['step2_summary'].get('after_advanced_filter', 0)}")
                print(f"   💰 Scraping cost saved: ${len(enriched_prospects) * 0.0047:.2f}")

                if not filtered_prospects:
                    result['step2_status'] = 'No Results'
                    result['error_message'] = 'No prospects passed filtering'
                    print(f"⚠️  No prospects passed filtering")
                    result['total_time'] = time.time() - start_time
                    return result

                # ========== STEP 3: AI Ranking ==========
                print(f"\n🤖 Step 3: AI Ranking")
                print(f"   Ranking {len(filtered_prospects)} prospects...")

                step3_start = time.time()

                step3_result = await service.step3_rank_prospects(
                    enriched_prospects=filtered_prospects,
                    company_name=hospital['name'],
                    min_score_threshold=65,
                    max_prospects=10
                )

                step3_time = time.time() - step3_start
                result['timing']['step3'] = step3_time

                if step3_result.get('success'):
                    result['step3_status'] = 'Success'
                    result['step3_summary'] = step3_result.get('summary', {})
                    qualified_prospects = step3_result.get('qualified_prospects', [])

                    print(f"✅ Step 3 completed in {step3_time:.1f}s")
                    print(f"   Final qualified: {result['step3_summary'].get('final_top_prospects', 0)}")

                    # Extract top prospect
                    if qualified_prospects:
                        top = qualified_prospects[0]
                        linkedin_data = top.get('linkedin_data', {})
                        ai_ranking = top.get('ai_ranking', {})

                        result['top_prospect'] = {
                            'name': linkedin_data.get('name', ''),
                            'title': linkedin_data.get('job_title', ''),
                            'score': ai_ranking.get('ranking_score', 0),
                            'linkedin_url': linkedin_data.get('url', ''),
                            'email': linkedin_data.get('email', ''),
                            'phone': linkedin_data.get('mobile_number', '')
                        }

                        print(f"\n🎯 Top Prospect: {result['top_prospect']['name']}")
                        print(f"   Title: {result['top_prospect']['title']}")
                        print(f"   Score: {result['top_prospect']['score']}/100")
                else:
                    result['step3_status'] = 'Failed'
                    result['error_message'] = step3_result.get('error', 'Unknown error')
                    print(f"❌ Step 3 failed: {result['error_message']}")
            else:
                result['step2_status'] = 'Failed'
                result['error_message'] = step2_result.get('error', 'Unknown error')
                print(f"❌ Step 2 failed: {result['error_message']}")
        else:
            result['step1_status'] = 'Failed'
            result['error_message'] = step1_result.get('error', 'Unknown error')
            print(f"❌ Step 1 failed: {result['error_message']}")

    except Exception as e:
        result['error_message'] = str(e)
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    result['total_time'] = time.time() - start_time
    print(f"\n⏱️  Total time for {hospital['name']}: {result['total_time']:.1f}s")

    return result


async def main():
    """Main batch processing function"""
    print_section("BRIGHT DATA 3-STEP BATCH TEST (NO SCRAPING!)")
    print(f"Testing {len(TEST_HOSPITALS)} hospitals")
    print(f"Output directory: batch_brightdata_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # Initialize service
    try:
        service = BrightDataProspectDiscoveryService()
        print("✅ Bright Data service initialized")
    except ValueError as e:
        print(f"❌ Failed to initialize Bright Data service: {e}")
        print("Make sure BRIGHTDATA_API_TOKEN is set in your .env file")
        return

    # Connect to Salesforce (if needed for parent account lookup)
    try:
        success = await salesforce_service.connect()
        if success:
            print("✅ Connected to Salesforce")
    except Exception as e:
        print(f"⚠️  Salesforce connection failed: {e}")
        print("   Continuing without Salesforce (parent account lookup may fail)")

    # Process each hospital
    batch_start = time.time()
    results = []

    for i, hospital in enumerate(TEST_HOSPITALS, 1):
        result = await process_hospital(service, hospital, i, len(TEST_HOSPITALS))
        results.append(result)

        # Pause between hospitals
        if i < len(TEST_HOSPITALS):
            print(f"\n⏳ Waiting 5 seconds before next hospital...")
            await asyncio.sleep(5)

    batch_elapsed = time.time() - batch_start

    # ========== BATCH SUMMARY ==========
    print_section("BATCH SUMMARY")
    print(f"Total batch time: {batch_elapsed:.1f}s ({batch_elapsed/60:.1f} minutes)")
    print(f"Average time per hospital: {batch_elapsed/len(TEST_HOSPITALS):.1f}s")

    # Count successes
    successful = sum(1 for r in results if r['step3_status'] == 'Success')
    print(f"\n✅ Successfully processed: {successful}/{len(results)} hospitals")

    # Calculate cost savings
    total_profiles = sum(r.get('step1_summary', {}).get('total_profiles_from_brightdata', 0) for r in results)
    scraping_cost_saved = total_profiles * 0.0047
    print(f"\n💰 Cost Analysis:")
    print(f"   Total Bright Data profiles: {total_profiles}")
    print(f"   Scraping cost saved: ${scraping_cost_saved:.2f}")
    print(f"   Bright Data filter cost: ${len(results) * 0.05:.2f}")

    total_ranked = sum(r.get('step3_summary', {}).get('prospects_ranked', 0) for r in results)
    ai_cost = total_ranked * 0.03
    print(f"   AI ranking cost: ${ai_cost:.2f}")
    print(f"   Total cost: ${(len(results) * 0.05) + ai_cost:.2f}")
    print(f"   ✅ Saved ${scraping_cost_saved:.2f} by skipping scraping!")

    # Save results to CSV
    output_dir = f"batch_brightdata_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    csv_path = save_results_to_csv(results, output_dir)

    # Print top prospects summary
    print(f"\n🎯 TOP PROSPECTS SUMMARY:")
    print("-" * 100)
    for result in results:
        hospital = result['hospital']
        if 'top_prospect' in result:
            tp = result['top_prospect']
            print(f"\n{hospital['name']} ({hospital['city']}, {hospital['state']})")
            print(f"  → {tp['name']} - {tp['title']}")
            print(f"  → Score: {tp['score']}/100 | Email: {tp.get('email', 'N/A')}")
            print(f"  → LinkedIn: {tp['linkedin_url']}")
        else:
            print(f"\n{hospital['name']} ({hospital['city']}, {hospital['state']})")
            print(f"  → ❌ {result.get('error_message', 'No qualified prospects found')}")

    print(f"\n🎉 Batch processing complete!")
    print(f"   Results saved to: {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
