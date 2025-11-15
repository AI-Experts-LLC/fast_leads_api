#!/usr/bin/env python3
"""
Test Bright Data LinkedIn Filter with Mayo Clinic
Tests filtering with local + parent account names + location
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

print("=" * 80)
print("Bright Data LinkedIn Filter - Mayo Clinic Test")
print("Testing: Local + Parent Account Search with Location Filter")
print("=" * 80)

try:
    client = BrightDataLinkedInFilter()

    # Test 1: Mayo Clinic in Rochester, MN
    print("\n" + "=" * 80)
    print("TEST 1: Mayo Clinic (Rochester, Minnesota)")
    print("=" * 80)

    filter_result = client.search_with_parent_account(
        company_name="Mayo Clinic",
        parent_account_name=None,  # Mayo is typically the parent
        company_city="Rochester",
        company_state="Minnesota"
    )

    if filter_result and filter_result.get("snapshot_id"):
        snapshot_id = filter_result["snapshot_id"]
        print(f"\n✅ Filter created! Snapshot ID: {snapshot_id}")
        print(f"\n📥 Fetching results (up to 5 minutes)...")
        print("=" * 80)

        profiles = client.get_snapshot_results(
            snapshot_id=snapshot_id,
            max_wait_time=300,
            poll_interval=10
        )

        if profiles and isinstance(profiles, list):
            print(f"\n✅ SUCCESS! Retrieved {len(profiles)} profiles from Mayo Clinic")
            print("=" * 80)

            # Display sample profiles
            for i, profile in enumerate(profiles[:5], 1):
                print(f"\n📋 Profile {i}:")
                print(f"   Name: {profile.get('name', 'N/A')}")
                print(f"   Position: {profile.get('position', 'N/A')}")
                print(f"   Company: {profile.get('current_company_name', 'N/A')}")
                print(f"   Location: {profile.get('city', 'N/A')}, {profile.get('country_code', 'N/A')}")
                print(f"   LinkedIn: {profile.get('url', 'N/A')}")

            if len(profiles) > 5:
                print(f"\n   ... and {len(profiles) - 5} more profiles")

        elif profiles:
            print(f"\n📊 Snapshot response (not a list):")
            print(f"   {profiles}")
        else:
            print(f"\n⚠️  No profiles returned")

    # Test 2: Baptist Health with parent
    print("\n\n" + "=" * 80)
    print("TEST 2: Baptist Health South Florida (with possible parent)")
    print("=" * 80)

    filter_result2 = client.search_with_parent_account(
        company_name="Baptist Health South Florida",
        parent_account_name="Baptist Health",  # Try with parent
        company_city="Miami",
        company_state="Florida"
    )

    if filter_result2 and filter_result2.get("snapshot_id"):
        snapshot_id2 = filter_result2["snapshot_id"]
        print(f"\n✅ Filter created! Snapshot ID: {snapshot_id2}")
        print(f"\n📥 Fetching results (up to 5 minutes)...")
        print("=" * 80)

        profiles2 = client.get_snapshot_results(
            snapshot_id=snapshot_id2,
            max_wait_time=300,
            poll_interval=10
        )

        if profiles2 and isinstance(profiles2, list):
            print(f"\n✅ SUCCESS! Retrieved {len(profiles2)} profiles from Baptist Health")
            print("=" * 80)

            # Display sample profiles
            for i, profile in enumerate(profiles2[:5], 1):
                print(f"\n📋 Profile {i}:")
                print(f"   Name: {profile.get('name', 'N/A')}")
                print(f"   Position: {profile.get('position', 'N/A')}")
                print(f"   Company: {profile.get('current_company_name', 'N/A')}")
                print(f"   Location: {profile.get('city', 'N/A')}, {profile.get('country_code', 'N/A')}")
                print(f"   LinkedIn: {profile.get('url', 'N/A')}")

            if len(profiles2) > 5:
                print(f"\n   ... and {len(profiles2) - 5} more profiles")

    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("=" * 80)

except ValueError as e:
    print(f"\n❌ Configuration error: {e}")
    print("\nPlease ensure BRIGHTDATA_API_TOKEN is set in your .env file")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
