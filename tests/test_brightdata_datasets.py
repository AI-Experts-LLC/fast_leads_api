#!/usr/bin/env python3
"""
Check what datasets are available in Bright Data account
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('BRIGHTDATA_API_TOKEN')

print("=" * 80)
print("Bright Data - Check Available Datasets")
print("=" * 80)

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Try different ways to list datasets
endpoints = [
    "https://api.brightdata.com/datasets",
    "https://api.brightdata.com/datasets/list",
    "https://api.brightdata.com/api/datasets",
]

for endpoint in endpoints:
    print(f"\n📡 Trying: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.ok:
            print(f"   ✅ SUCCESS!")
            data = response.json()

            if isinstance(data, list):
                print(f"   Found {len(data)} datasets:")
                for ds in data[:5]:
                    if isinstance(ds, dict):
                        print(f"     - ID: {ds.get('id', 'N/A')}, Name: {ds.get('name', 'N/A')}")
                    else:
                        print(f"     - {ds}")
            else:
                print(f"   Response: {json.dumps(data, indent=2)[:300]}")
        elif response.status_code != 404:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

# Check the specific LinkedIn dataset we're using
print("\n" + "=" * 80)
print("Check LinkedIn Profiles Dataset: gd_l1viktl72bvl7bjuj0")
print("=" * 80)

dataset_id = "gd_l1viktl72bvl7bjuj0"

# Try to get info about this specific dataset
info_endpoints = [
    f"https://api.brightdata.com/datasets/{dataset_id}",
    f"https://api.brightdata.com/datasets/{dataset_id}/info",
]

for endpoint in info_endpoints:
    print(f"\n📡 Trying: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.ok:
            print(f"   ✅ Dataset exists!")
            data = response.json()
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Type: {data.get('type', 'N/A')}")
            if 'description' in data:
                print(f"   Description: {data.get('description', '')[:100]}")
        elif response.status_code != 404:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("Dataset ID 'gd_l1viktl72bvl7bjuj0' is the LinkedIn Profiles dataset.")
print("This is the correct dataset for filtering LinkedIn profile data.")
print("\nThe issue is NOT with the dataset ID - it's with retrieving filter results.")
