#!/usr/bin/env python3
"""
Simple test to show Mayo Clinic filter with location variations
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

print("=" * 80)
print("Mayo Clinic - Company Name Variations Test")
print("=" * 80)

try:
    client = BrightDataLinkedInFilter()

    # Create filter (but don't wait for results)
    print("\nCreating filter for Mayo Clinic with location variations...")
    filter_result = client.search_with_parent_account(
        company_name="Mayo Clinic",
        parent_account_name=None,
        company_city="Rochester",
        company_state="Minnesota"
    )

    if filter_result and filter_result.get("snapshot_id"):
        print(f"\n✅ Filter created successfully!")
        print(f"   Snapshot ID: {filter_result['snapshot_id']}")
        print(f"\n   Company name variations searched:")
        print(f"     1. 'Mayo Clinic'")
        print(f"     2. 'Mayo Clinic Rochester' (local + city)")
        print(f"\n   This filter will match LinkedIn profiles where")
        print(f"   current_company_name includes ANY of these variations")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
