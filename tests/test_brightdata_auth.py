#!/usr/bin/env python3
"""
Test Bright Data API authentication and basic endpoints
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('BRIGHTDATA_API_TOKEN')

print("=" * 80)
print("Bright Data API Authentication Test")
print("=" * 80)

if not API_TOKEN:
    print("❌ BRIGHTDATA_API_TOKEN not found in environment!")
    exit(1)

print(f"\n✅ API Token loaded: {API_TOKEN[:10]}...{API_TOKEN[-5:]}")
print(f"   Length: {len(API_TOKEN)} characters")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Test 1: List datasets (should work with valid auth)
print("\n" + "=" * 80)
print("TEST 1: List Datasets (GET /datasets/v3)")
print("=" * 80)

list_url = "https://api.brightdata.com/datasets/v3"
print(f"URL: {list_url}")

try:
    response = requests.get(list_url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 401 or response.status_code == 403:
        print("❌ AUTHENTICATION FAILED!")
        print(f"Response: {response.text}")
    elif response.ok:
        print("✅ AUTHENTICATION SUCCESS!")
        data = response.json()
        if isinstance(data, list):
            print(f"Found {len(data)} datasets")
            print(f"First few: {[d.get('id', 'unknown') for d in data[:3]]}")
        else:
            print(f"Response: {str(data)[:200]}")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Get specific dataset info
print("\n" + "=" * 80)
print("TEST 2: Get LinkedIn Profiles Dataset (GET /datasets/v3/{id})")
print("=" * 80)

dataset_id = "gd_l1viktl72bvl7bjuj0"
dataset_url = f"https://api.brightdata.com/datasets/v3/{dataset_id}"
print(f"URL: {dataset_url}")

try:
    response = requests.get(dataset_url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 401 or response.status_code == 403:
        print("❌ AUTHENTICATION FAILED!")
        print(f"Response: {response.text}")
    elif response.ok:
        print("✅ Dataset found!")
        data = response.json()
        print(f"Name: {data.get('name', 'N/A')}")
        print(f"ID: {data.get('id', 'N/A')}")
        print(f"Type: {data.get('type', 'N/A')}")
    else:
        print(f"⚠️  Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Create filter (this is what we're doing)
print("\n" + "=" * 80)
print("TEST 3: Create Filter (POST /datasets/filter)")
print("=" * 80)

filter_url = "https://api.brightdata.com/datasets/filter"
payload = {
    "dataset_id": dataset_id,
    "filter": {
        "operator": "and",
        "filters": [
            {"name": "current_company_name", "value": "Test Company", "operator": "includes"}
        ]
    }
}

print(f"URL: {filter_url}")
print(f"Dataset: {dataset_id}")

try:
    response = requests.post(filter_url, headers=headers, json=payload, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 401 or response.status_code == 403:
        print("❌ AUTHENTICATION FAILED!")
        print(f"Response: {response.text}")
    elif response.ok:
        print("✅ Filter created successfully!")
        data = response.json()
        print(f"Response: {data}")

        # This proves the API key works!
        if 'snapshot_id' in data:
            print(f"\n🎉 API KEY IS VALID - Filter created with snapshot: {data['snapshot_id']}")
    else:
        print(f"⚠️  Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("If you see 'Filter created successfully' above, your API key is valid!")
print("The 404 errors are happening when trying to RETRIEVE the filter results.")
