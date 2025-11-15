#!/usr/bin/env python3
"""
Diagnostic test for Bright Data download endpoint issues
Tests with minimal configuration: 1 account, max 10 records
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.services.brightdata_prospect_discovery import BrightDataProspectDiscoveryService

async def test_diagnostic():
    """
    Diagnostic test with:
    - 1 account only (Billings Clinic)
    - Max 10 records limit
    - Comprehensive logging enabled
    """

    print("=" * 80)
    print("BRIGHT DATA DIAGNOSTIC TEST")
    print("=" * 80)
    print()
    print("Configuration:")
    print("  - Test Account: Billings Clinic, Billings, Montana")
    print("  - Records Limit: 10")
    print("  - Enhanced Logging: ENABLED")
    print()
    print("=" * 80)
    print()

    service = BrightDataProspectDiscoveryService()

    # Test with Billings Clinic (previously showed 6 profiles)
    result = await service.step1_brightdata_filter(
        company_name='Billings Clinic',
        company_city='Billings',
        company_state='Montana',
        min_connections=20
    )

    print()
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print()
    print(f"Success: {result.get('success')}")

    if result.get('success'):
        summary = result.get('summary', {})
        print(f"Profiles Found: {summary.get('total_profiles_from_brightdata', 0)}")
        print(f"Profiles Transformed: {summary.get('profiles_transformed', 0)}")
        print(f"Snapshot ID: {summary.get('snapshot_id')}")
        print()
        print("✅ TEST PASSED - Check logs above for response diagnostics")
    else:
        print(f"Error: {result.get('error')}")
        print(f"Step: {result.get('step')}")
        print()
        print("❌ TEST FAILED - Check logs above for failure details")

    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_diagnostic())
