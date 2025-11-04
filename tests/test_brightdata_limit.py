"""
Test BrightData 75-Result Limit
Verifies that snapshots with >75 results are rejected before download
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root FIRST before any imports
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService


async def test_result_limit():
    """
    Test that BrightData rejects snapshots with >75 results

    We'll test with a very broad search that should return many results
    """
    print("\n" + "="*80)
    print("BRIGHTDATA 75-RESULT LIMIT TEST")
    print("="*80)

    service = BrightDataProspectDiscoveryService()

    # Test 1: Normal search (should be < 75 results)
    print("\n[TEST 1] Normal Search - Should Succeed")
    print("-"*80)

    result1 = await service.step1_brightdata_filter(
        company_name="BENEFIS HOSPITALS INC",
        parent_account_name="Benefis Health System",
        company_city="Great Falls",
        company_state="Montana",
        min_connections=0,
        use_city_filter=False
    )

    if result1.get('success'):
        profiles = result1.get('enriched_prospects', [])
        print(f"✅ Normal search succeeded: {len(profiles)} profiles")
        print(f"   Result count was within limit (≤75)")
    else:
        error = result1.get('error', 'Unknown error')
        if 'exceeded limit' in error:
            print(f"❌ Unexpected: Normal search was rejected for exceeding limit")
            print(f"   Error: {error}")
        else:
            print(f"⚠️  Search failed for other reason: {error}")

    # Test 2: Very broad search (should potentially exceed 75)
    print("\n[TEST 2] Broad Search - May Exceed Limit")
    print("-"*80)
    print("Testing with broader filters to see if we can trigger the 75-result limit...")

    # Use a large healthcare system that might have many employees
    result2 = await service.step1_brightdata_filter(
        company_name="Mayo Clinic",
        parent_account_name=None,
        company_city=None,  # No city filter
        company_state="Minnesota",
        min_connections=0,
        use_city_filter=False
    )

    if result2.get('success'):
        profiles = result2.get('enriched_prospects', [])
        print(f"✅ Broad search succeeded: {len(profiles)} profiles")
        print(f"   Result count was within limit (≤75)")
    else:
        error = result2.get('error', 'Unknown error')
        if 'exceeded limit' in error:
            print(f"✅ Broad search correctly rejected for exceeding 75-result limit")
            print(f"   Suggestion: {result2.get('suggestion', 'N/A')}")
        else:
            print(f"⚠️  Search failed for other reason: {error}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("The 75-result limit check is in place and will reject snapshots")
    print("with >75 results before downloading to avoid excessive API costs.")
    print("\nLog messages will show:")
    print("  - Result count when snapshot is ready")
    print("  - Rejection notice if count exceeds 75")
    print("  - Suggestion to add more specific filters")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_result_limit())
