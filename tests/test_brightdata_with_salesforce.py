#!/usr/bin/env python3
"""
Test Bright Data LinkedIn Filter with Salesforce Integration
Fetches account + parent account from Salesforce, then searches with both
"""

import os
import sys
import csv
import time
import asyncio
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter
from app.services.salesforce import salesforce_service

load_dotenv()

def flatten_profile(profile, hospital_info):
    """
    Flatten nested LinkedIn profile data into a single-level dict for CSV export
    """
    flat = {
        "hospital_name": hospital_info["company_name"],
        "hospital_city": hospital_info.get("city", ""),
        "hospital_state": hospital_info.get("state", ""),
        "parent_account_name": hospital_info.get("parent_account_name", ""),
        "account_id": hospital_info["account_id"],
        "name": profile.get("name", ""),
        "first_name": profile.get("first_name", ""),
        "last_name": profile.get("last_name", ""),
        "position": profile.get("position", ""),
        "current_company_name": profile.get("current_company_name", ""),
        "headline": profile.get("headline", ""),
        "city": profile.get("city", ""),
        "country": profile.get("country", ""),
        "profile_url": profile.get("url", ""),
        "connections": profile.get("connections", ""),
        "followers": profile.get("followers", ""),
        "about": profile.get("about", ""),
    }

    # Extract experience (most recent job)
    experiences = profile.get("experience", [])
    if experiences and len(experiences) > 0:
        recent_exp = experiences[0]
        flat["experience_title"] = recent_exp.get("title", "")
        flat["experience_company"] = recent_exp.get("company", "")
        flat["experience_location"] = recent_exp.get("location", "")
        flat["experience_start_date"] = recent_exp.get("start_date", "")
        flat["experience_end_date"] = recent_exp.get("end_date", "")
    else:
        flat["experience_title"] = ""
        flat["experience_company"] = ""
        flat["experience_location"] = ""
        flat["experience_start_date"] = ""
        flat["experience_end_date"] = ""

    # Extract education (most recent)
    education = profile.get("education", [])
    if education and len(education) > 0:
        recent_edu = education[0]
        flat["education_school"] = recent_edu.get("school", "")
        flat["education_degree"] = recent_edu.get("degree", "")
        flat["education_field"] = recent_edu.get("field_of_study", "")
    else:
        flat["education_school"] = ""
        flat["education_degree"] = ""
        flat["education_field"] = ""

    return flat

def get_account_from_salesforce(account_id: str):
    """
    Fetch account details from Salesforce including parent account

    Returns:
        dict with company_name, parent_account_name, city, state, account_id
    """
    try:
        print(f"  Fetching account details from Salesforce...")

        # Query Salesforce for account details including parent
        query = f"""
            SELECT Id, Name, BillingCity, BillingState, ParentId, Parent.Name
            FROM Account
            WHERE Id = '{account_id}'
            LIMIT 1
        """

        result = salesforce_service.sf.query(query)

        if not result or not result.get('records'):
            print(f"  ❌ Account not found in Salesforce: {account_id}")
            return None

        account = result['records'][0]

        account_data = {
            "account_id": account_id,
            "company_name": account.get('Name'),
            "city": account.get('BillingCity'),
            "state": account.get('BillingState'),
            "parent_account_name": None
        }

        # Extract parent account name if it exists
        if account.get('ParentId'):
            parent_name = account.get('Parent', {}).get('Name')
            if parent_name:
                account_data["parent_account_name"] = parent_name
                print(f"  ✅ Found parent account: {parent_name}")

        print(f"  ✅ Account: {account_data['company_name']}")
        print(f"     Location: {account_data['city']}, {account_data['state']}")

        return account_data

    except Exception as e:
        print(f"  ❌ Error fetching from Salesforce: {e}")
        return None

async def main():
    # Test account IDs - 3 different hospitals
    TEST_ACCOUNT_IDS = [
        "001VR00000Vh74QYAR",  # Portneuf Medical Center (Pocatello, ID)
        "001VR00000UhXwBYAV",  # Benefis Hospitals Inc (Great Falls, MT)
        "0017V00001YEA77QAH",  # Billings Clinic Hospital (Billings, MT)
    ]

    print("=" * 80)
    print("Bright Data LinkedIn Filter - Salesforce Integration Test")
    print("=" * 80)

    # Connect to Salesforce
    print("\n🔗 Connecting to Salesforce...")
    try:
        success = await salesforce_service.connect()
        if not success:
            print("❌ Failed to connect to Salesforce")
            return
        print("✅ Connected to Salesforce")
    except Exception as e:
        print(f"❌ Failed to connect to Salesforce: {e}")
        return

    client = BrightDataLinkedInFilter()
    all_results = []

    for i, account_id in enumerate(TEST_ACCOUNT_IDS, 1):
        print(f"\n[{i}/3] Processing Account ID: {account_id}")
        print("-" * 80)

        # Get account details from Salesforce
        account_data = get_account_from_salesforce(account_id)

        if not account_data:
            print(f"⚠️  Skipping account {account_id} - could not fetch details")
            continue

        try:
            # Create Bright Data filter with BOTH local and parent account names
            print(f"\nCreating Bright Data filter...")
            filter_result = client.search_with_parent_account(
                company_name=account_data["company_name"],
                parent_account_name=account_data["parent_account_name"],  # Include parent!
                company_city=account_data["city"],
                company_state=account_data["state"]
            )

            if not filter_result or not filter_result.get("snapshot_id"):
                print(f"❌ Failed to create filter for {account_data['company_name']}")
                continue

            snapshot_id = filter_result["snapshot_id"]
            print(f"✅ Filter created! Snapshot ID: {snapshot_id}")
            print(f"Polling for results (up to 5 minutes)...")

            # Poll for results
            profiles = client.get_snapshot_results(
                snapshot_id=snapshot_id,
                max_wait_time=300,  # 5 minutes
                poll_interval=10    # Check every 10 seconds
            )

            if profiles:
                print(f"✅ Found {len(profiles)} profiles!")

                # Flatten each profile and add to results
                for profile in profiles:
                    flat_profile = flatten_profile(profile, account_data)
                    all_results.append(flat_profile)

                # Show sample
                if len(profiles) > 0:
                    print(f"\nSample profiles:")
                    for j, sample in enumerate(profiles[:3], 1):
                        print(f"  {j}. {sample.get('name', 'N/A')}")
                        print(f"     Position: {sample.get('position', 'N/A')}")
                        print(f"     Company: {sample.get('current_company_name', 'N/A')}")
                        print(f"     Location: {sample.get('city', 'N/A')}")
            else:
                print(f"⚠️  No profiles found (may not be in dataset)")

        except Exception as e:
            print(f"❌ Error processing {account_data['company_name']}: {e}")
            import traceback
            traceback.print_exc()

        # Small delay between accounts
        if i < len(TEST_ACCOUNT_IDS):
            print(f"\nWaiting 5 seconds before next account...")
            time.sleep(5)

    # Export to CSV with timestamp for expanded titles test
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"Lucas_test_expanded_titles_{timestamp}.csv"

    if all_results:
        print("\n" + "=" * 80)
        print(f"Exporting {len(all_results)} profiles to {output_file}...")
        print("=" * 80)

        # Get all unique keys from all results (in case fields vary)
        all_keys = set()
        for result in all_results:
            all_keys.update(result.keys())

        fieldnames = sorted(list(all_keys))

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)

        print(f"✅ Results exported to: {output_file}")
        print(f"   Total profiles: {len(all_results)}")
        print(f"   Columns: {len(fieldnames)}")

        # Show summary by hospital
        print("\n📊 Results by account:")
        for account_id in TEST_ACCOUNT_IDS:
            count = sum(1 for r in all_results if r["account_id"] == account_id)
            account_name = next((r["hospital_name"] for r in all_results if r["account_id"] == account_id), "Unknown")
            parent_name = next((r["parent_account_name"] for r in all_results if r["account_id"] == account_id), "None")

            print(f"  {account_name}: {count} profiles")
            if parent_name:
                print(f"    → Parent: {parent_name}")
    else:
        print("\n⚠️  No results to export")
        # Create empty CSV with headers
        fieldnames = [
            "hospital_name", "hospital_city", "hospital_state", "parent_account_name", "account_id",
            "name", "first_name", "last_name", "position", "current_company_name",
            "headline", "city", "country", "profile_url", "connections", "followers",
            "about", "experience_title", "experience_company", "experience_location",
            "experience_start_date", "experience_end_date", "education_school",
            "education_degree", "education_field"
        ]
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        print(f"⚠️  Created empty CSV: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
