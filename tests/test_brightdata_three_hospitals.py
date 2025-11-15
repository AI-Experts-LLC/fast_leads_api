#!/usr/bin/env python3
"""
Test Bright Data LinkedIn Filter API with 3 hospitals from HospitalAccountsAndIDs.csv
Export results to CSV with all response fields
"""

import os
import sys
import csv
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

# Test with first 3 hospitals from the CSV
TEST_HOSPITALS = [
    {
        "company_name": "Benefis Hospitals Inc",
        "city": "Great Falls",
        "state": "MT",
        "account_id": "001VR00000UhXwBYAV"
    },
    {
        "company_name": "Billings Clinic Hospital",
        "city": "Billings",
        "state": "MT",
        "account_id": "0017V00001YEA77QAH"
    },
    {
        "company_name": "Portneuf Medical Center",
        "city": "Pocatello",
        "state": "ID",
        "account_id": "001VR00000Vh74QYAR"
    }
]

def flatten_profile(profile, hospital_info):
    """
    Flatten nested LinkedIn profile data into a single-level dict for CSV export
    """
    flat = {
        "hospital_name": hospital_info["company_name"],
        "hospital_city": hospital_info["city"],
        "hospital_state": hospital_info["state"],
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

def main():
    print("=" * 80)
    print("Bright Data LinkedIn Filter - 3 Hospital Test")
    print("=" * 80)

    client = BrightDataLinkedInFilter()
    all_results = []

    for i, hospital in enumerate(TEST_HOSPITALS, 1):
        print(f"\n[{i}/3] Testing: {hospital['company_name']} ({hospital['city']}, {hospital['state']})")
        print("-" * 80)

        try:
            # Create filter (no parent account for these hospitals)
            print(f"Creating filter...")
            filter_result = client.search_with_parent_account(
                company_name=hospital["company_name"],
                parent_account_name=None,  # No parent account info in CSV
                company_city=hospital["city"],
                company_state=hospital["state"]
            )

            if not filter_result or not filter_result.get("snapshot_id"):
                print(f"❌ Failed to create filter for {hospital['company_name']}")
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
                    flat_profile = flatten_profile(profile, hospital)
                    all_results.append(flat_profile)

                # Show sample
                if len(profiles) > 0:
                    print(f"\nSample profile:")
                    sample = profiles[0]
                    print(f"  Name: {sample.get('name', 'N/A')}")
                    print(f"  Position: {sample.get('position', 'N/A')}")
                    print(f"  Company: {sample.get('current_company_name', 'N/A')}")
                    print(f"  Location: {sample.get('city', 'N/A')}")
            else:
                print(f"⚠️  No profiles found (may not be in dataset)")

        except Exception as e:
            print(f"❌ Error processing {hospital['company_name']}: {e}")
            import traceback
            traceback.print_exc()

        # Small delay between hospitals
        if i < len(TEST_HOSPITALS):
            print(f"\nWaiting 5 seconds before next hospital...")
            time.sleep(5)

    # Export to CSV
    if all_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"brightdata_hospital_results_{timestamp}.csv"

        print("\n" + "=" * 80)
        print(f"Exporting {len(all_results)} profiles to CSV...")
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
        print("\nResults by hospital:")
        for hospital in TEST_HOSPITALS:
            count = sum(1 for r in all_results if r["hospital_name"] == hospital["company_name"])
            print(f"  {hospital['company_name']}: {count} profiles")
    else:
        print("\n⚠️  No results to export")

if __name__ == "__main__":
    main()
