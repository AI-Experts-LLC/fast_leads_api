#!/usr/bin/env python3
"""
Quick test of Bright Data LinkedIn Filter API with Baptist Health
Tests the complete flow: Create filter → Poll status → Download data
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import the test module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

print("=" * 80)
print("Bright Data LinkedIn Filter API - Baptist Health Test")
print("=" * 80)

try:
    # Initialize the client
    client = BrightDataLinkedInFilter()

    # Test with Baptist Health
    print("\n🏥 Testing with: Baptist Health")
    print("=" * 80)

    # Create filter
    filter_result = client.search_by_title_and_company(
        company_name="Baptist Health"
    )

    if filter_result and isinstance(filter_result, dict):
        snapshot_id = filter_result.get("snapshot_id")

        if snapshot_id:
            print(f"\n✅ Filter created successfully!")
            print(f"   Snapshot ID: {snapshot_id}")

            # Fetch the actual results from the snapshot (wait up to 5 minutes)
            print(f"\n📥 Fetching results (this may take up to 5 minutes)...")
            print("=" * 80)

            profiles = client.get_snapshot_results(
                snapshot_id=snapshot_id,
                max_wait_time=300,  # 5 minutes
                poll_interval=10    # Check every 10 seconds
            )

            if profiles and isinstance(profiles, list):
                print(f"\n✅ SUCCESS! Retrieved {len(profiles)} profiles")
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
                print(f"\n📊 Response received (not a list):")
                print(f"   {profiles}")
            else:
                print(f"\n⚠️  No profiles returned")
                print(f"   This likely means no matching data exists in the dataset")
                print(f"   Note: The Filter API only filters EXISTING collected data")

    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("=" * 80)

except ValueError as e:
    print(f"\n❌ Configuration error: {e}")
    print("\nPlease ensure BRIGHTDATA_API_TOKEN is set in your .env file:")
    print("  BRIGHTDATA_API_TOKEN=your_token_here")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
