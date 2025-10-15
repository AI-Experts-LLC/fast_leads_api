"""
Batch test for Account ID-based prospect discovery
Tests the new /discover-prospects-by-account-id endpoint with real hospitals
"""

import asyncio
import httpx
import json
import csv
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hospital data with Account IDs
HOSPITALS = [
    {
        "name": "St. Joseph Regional Medical Center",
        "city": "Lewiston",
        "state": "ID",
        "health_system": "RCCH HealthCare Partners (formerly Ascension)",
        "account_id": "001VR00000UhY3oYAF"
    },
    {
        "name": "St. Patrick Hospital",
        "city": "Missoula",
        "state": "MT",
        "health_system": "Providence Health & Services (Providence Montana)",
        "account_id": "001VR00000UhY4hYAF"
    },
    {
        "name": "St. Vincent Healthcare",
        "city": "Billings",
        "state": "MT",
        "health_system": "Intermountain Health (formerly SCL Health)",
        "account_id": "001VR00000UhXv2YAF"
    },
    {
        "name": "Community Medical Center",
        "city": "Missoula",
        "state": "MT",
        "health_system": "Community Medical Center (Providence affiliated)",
        "account_id": "001VR00000VhCFNYA3"
    },
    {
        "name": "West Valley Medical Center",
        "city": "Caldwell",
        "state": "ID",
        "health_system": "HCA Healthcare",
        "account_id": "0017V00001SOG6LQAX"
    },
    {
        "name": "St. Luke's Magic Valley RMC",
        "city": "Twin Falls",
        "state": "ID",
        "health_system": "St. Luke's Health System",
        "account_id": "001VR00000VhECLYA3"
    },
    {
        "name": "Saint Alphonsus Regional Medical Center",
        "city": "Boise",
        "state": "ID",
        "health_system": "Saint Alphonsus Health System",
        "account_id": "001VR00000UhY7xYAF"
    },
    {
        "name": "Benefis Hospitals Inc",
        "city": "Great Falls",
        "state": "MT",
        "health_system": "Benefis Health System",
        "account_id": "001VR00000UhXwBYAV"
    },
    {
        "name": "Bozeman Health Deaconess Regional Medical Center",
        "city": "Bozeman",
        "state": "MT",
        "health_system": "Bozeman Health",
        "account_id": "0017V00001aggoqQAA"
    },
    {
        "name": "Billings Clinic Hospital",
        "city": "Billings",
        "state": "MT",
        "health_system": "Billings Clinic (Independent)",
        "account_id": "0017V00001YEA77QAH"
    },
    {
        "name": "Logan Health Medical Center",
        "city": "Kalispell",
        "state": "MT",
        "health_system": "Logan Health (formerly Kalispell Regional Healthcare)",
        "account_id": "001VR00000VhD3NYAV"
    },
    {
        "name": "Portneuf Medical Center",
        "city": "Pocatello",
        "state": "ID",
        "health_system": "Portneuf Health System",
        "account_id": "001VR00000Vh74QYAR"
    },
    {
        "name": "St. Luke's Regional Medical Center",
        "city": "Boise",
        "state": "ID",
        "health_system": "St. Luke's Health System",
        "account_id": "001VR00000UhY5JYAV"
    }
]

BASE_URL = "http://127.0.0.1:8000"


async def discover_prospects_for_hospital(client: httpx.AsyncClient, hospital: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Step 1 prospect discovery for a single hospital using Account ID
    """
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {hospital['name']} ({hospital['city']}, {hospital['state']})")
        logger.info(f"Account ID: {hospital['account_id']}")
        logger.info(f"{'='*80}")

        start_time = datetime.now()

        # Call the new account ID-based endpoint
        response = await client.post(
            f"{BASE_URL}/discover-prospects-by-account-id",
            json={"account_id": hospital['account_id']},
            timeout=180.0
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if response.status_code == 200:
            result = response.json()

            # Extract key metrics
            data = result.get('data', {})
            summary = data.get('summary', {})
            salesforce_account = result.get('salesforce_account', {})

            logger.info(f"✅ SUCCESS ({elapsed:.1f}s)")
            logger.info(f"  → SF Account Name: {salesforce_account.get('account_name')}")
            logger.info(f"  → Parent Name: {salesforce_account.get('parent_name') or 'None'}")
            logger.info(f"  → Total search results: {summary.get('total_search_results', 0)}")
            logger.info(f"  → After basic filter: {summary.get('after_basic_filter', 0)}")
            logger.info(f"  → After AI filter: {summary.get('after_ai_basic_filter', 0)}")
            logger.info(f"  → After title filter: {summary.get('after_title_filter', 0)}")
            logger.info(f"  → Qualified prospects: {summary.get('qualified_for_scraping', 0)}")
            logger.info(f"  → Searched with parent: {summary.get('searched_with_parent_account', False)}")

            return {
                "hospital": hospital['name'],
                "city": hospital['city'],
                "state": hospital['state'],
                "account_id": hospital['account_id'],
                "status": "success",
                "elapsed_seconds": elapsed,
                "salesforce_account_name": salesforce_account.get('account_name'),
                "parent_name": salesforce_account.get('parent_name'),
                "searched_with_parent": summary.get('searched_with_parent_account', False),
                "total_search_results": summary.get('total_search_results', 0),
                "qualified_prospects": summary.get('qualified_for_scraping', 0),
                "summary": summary,
                "prospects": data.get('qualified_prospects', [])
            }
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            logger.error(f"❌ FAILED ({elapsed:.1f}s)")
            logger.error(f"  → Error: {error_detail}")

            return {
                "hospital": hospital['name'],
                "city": hospital['city'],
                "state": hospital['state'],
                "account_id": hospital['account_id'],
                "status": "failed",
                "elapsed_seconds": elapsed,
                "error": error_detail
            }

    except Exception as e:
        logger.error(f"❌ EXCEPTION: {str(e)}")
        return {
            "hospital": hospital['name'],
            "city": hospital['city'],
            "state": hospital['state'],
            "account_id": hospital['account_id'],
            "status": "error",
            "error": str(e)
        }


async def run_batch_test():
    """
    Run batch test on all hospitals
    """
    logger.info(f"\n{'#'*80}")
    logger.info(f"BATCH TEST: Account ID-Based Prospect Discovery")
    logger.info(f"Testing {len(HOSPITALS)} hospitals")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'#'*80}\n")

    batch_start = datetime.now()
    results = []

    async with httpx.AsyncClient() as client:
        # Process hospitals one at a time (to avoid rate limiting)
        for i, hospital in enumerate(HOSPITALS, 1):
            logger.info(f"\n[{i}/{len(HOSPITALS)}] Processing hospital...")
            result = await discover_prospects_for_hospital(client, hospital)
            results.append(result)

            # Small delay between hospitals
            if i < len(HOSPITALS):
                await asyncio.sleep(2)

    batch_elapsed = (datetime.now() - batch_start).total_seconds()

    # Generate summary
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']

    total_prospects = sum(r.get('qualified_prospects', 0) for r in successful)

    logger.info(f"\n{'#'*80}")
    logger.info(f"BATCH TEST COMPLETE")
    logger.info(f"{'#'*80}")
    logger.info(f"Total time: {batch_elapsed/60:.1f} minutes ({batch_elapsed:.1f} seconds)")
    logger.info(f"Hospitals processed: {len(HOSPITALS)}")
    logger.info(f"  ✅ Successful: {len(successful)}")
    logger.info(f"  ❌ Failed: {len(failed)}")
    logger.info(f"Total qualified prospects: {total_prospects}")
    if successful:
        logger.info(f"Average prospects per hospital: {total_prospects/len(successful):.1f}")

    # Count hospitals that had parent accounts
    with_parent = [r for r in successful if r.get('searched_with_parent', False)]
    logger.info(f"Hospitals with parent accounts: {len(with_parent)}/{len(successful)}")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save full JSON results
    json_file = f"account_id_batch_results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump({
            "batch_info": {
                "total_hospitals": len(HOSPITALS),
                "successful": len(successful),
                "failed": len(failed),
                "total_prospects": total_prospects,
                "total_time_seconds": batch_elapsed,
                "with_parent_account": len(with_parent)
            },
            "results": results
        }, f, indent=2)
    logger.info(f"\n✅ Full results saved to: {json_file}")

    # Save CSV summary
    csv_file = f"account_id_batch_summary_{timestamp}.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Hospital', 'City', 'State', 'Account ID', 'Status',
            'SF Account Name', 'Parent Name', 'Has Parent',
            'Total Search Results', 'Qualified Prospects', 'Time (s)'
        ])
        for r in results:
            writer.writerow([
                r['hospital'],
                r['city'],
                r['state'],
                r['account_id'],
                r['status'],
                r.get('salesforce_account_name', 'N/A'),
                r.get('parent_name', 'None'),
                'Yes' if r.get('searched_with_parent', False) else 'No',
                r.get('total_search_results', 0),
                r.get('qualified_prospects', 0),
                f"{r.get('elapsed_seconds', 0):.1f}"
            ])
    logger.info(f"✅ Summary saved to: {csv_file}")

    # Save all prospects to a single CSV
    prospects_file = f"account_id_batch_prospects_{timestamp}.csv"
    with open(prospects_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Hospital', 'City', 'State', 'Account ID', 'Parent Name',
            'LinkedIn URL', 'Search Title', 'Target Title', 'AI Score', 'AI Reasoning'
        ])
        for r in successful:
            for prospect in r.get('prospects', []):
                writer.writerow([
                    r['hospital'],
                    r['city'],
                    r['state'],
                    r['account_id'],
                    r.get('parent_name', 'None'),
                    prospect.get('linkedin_url', ''),
                    prospect.get('search_title', ''),
                    prospect.get('target_title', ''),
                    prospect.get('ai_title_score', 0),
                    prospect.get('ai_title_reasoning', '')
                ])
    logger.info(f"✅ All prospects saved to: {prospects_file}")

    # Print failed hospitals if any
    if failed:
        logger.info(f"\n{'='*80}")
        logger.info("FAILED HOSPITALS:")
        logger.info(f"{'='*80}")
        for r in failed:
            logger.info(f"  • {r['hospital']} ({r['city']}, {r['state']})")
            logger.info(f"    Account ID: {r['account_id']}")
            logger.info(f"    Error: {r.get('error', 'Unknown')}")

    return results


if __name__ == "__main__":
    asyncio.run(run_batch_test())
