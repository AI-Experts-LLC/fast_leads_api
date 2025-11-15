#!/usr/bin/env python3
"""
Simple test to show Baptist Health filter with all company variations
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

print("=" * 80)
print("Baptist Health - Company Name Variations Test")
print("=" * 80)

try:
    client = BrightDataLinkedInFilter()

    # Create filter (but don't wait for results)
    print("\nCreating filter for Baptist Health with ALL variations...")
    filter_result = client.search_with_parent_account(
        company_name="Baptist Health South Florida",
        parent_account_name="Baptist Health",
        company_city="Miami",
        company_state="Florida"
    )

    if filter_result and filter_result.get("snapshot_id"):
        print(f"\n✅ Filter created successfully!")
        print(f"   Snapshot ID: {filter_result['snapshot_id']}")
        print(f"\n   Company name variations searched (OR - match ANY):")
        print(f"     1. 'Baptist Health South Florida' (local)")
        print(f"     2. 'Baptist Health' (parent)")
        print(f"     3. 'Baptist Health South Florida Miami' (local + city)")
        print(f"     4. 'Baptist Health Miami' (parent + city)")
        print(f"\n   This filter will match LinkedIn profiles where")
        print(f"   current_company_name includes ANY of these 4 variations")
        print(f"\n   Examples of matches:")
        print(f"     ✓ 'Baptist Health'")
        print(f"     ✓ 'Baptist Health South Florida'")
        print(f"     ✓ 'Baptist Health Miami Cancer Institute'")
        print(f"     ✓ 'Baptist Health South Florida - Miami'")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
