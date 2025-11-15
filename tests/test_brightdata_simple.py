#!/usr/bin/env python3
"""
Simple test to understand Bright Data Filter API response structure
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('BRIGHTDATA_API_TOKEN')

print("=" * 80)
print("Simple Bright Data Filter Test - HCA Healthcare")
print("=" * 80)

# Create filter
url = "https://api.brightdata.com/datasets/filter"
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "dataset_id": "gd_l1viktl72bvl7bjuj0",
    "filter": {
        "operator": "and",
        "filters": [
            {"name": "current_company_name", "value": "HCA Healthcare", "operator": "includes"},
            {
                "operator": "or",
                "filters": [
                    {"name": "position", "value": "finance", "operator": "includes"},
                    {"name": "position", "value": "director", "operator": "includes"}
                ]
            },
            {"name": "city", "value": "Tampa", "operator": "includes"}
        ]
    }
}

print("\n📤 Creating filter...")
print(json.dumps(payload, indent=2))

response = requests.post(url, headers=headers, json=payload)

print(f"\n📥 Response Status: {response.status_code}")
print(f"Response Headers:")
for key, value in response.headers.items():
    if 'content' in key.lower() or 'location' in key.lower():
        print(f"  {key}: {value}")

if response.ok:
    print(f"\n✅ Filter created successfully!")
    result = response.json()
    print(f"\nFull Response:")
    print(json.dumps(result, indent=2))

    snapshot_id = result.get('snapshot_id')

    if snapshot_id:
        print(f"\n🔍 Snapshot ID: {snapshot_id}")
        print(f"\n💡 Trying different retrieval endpoints...")

        # Try different endpoint patterns
        endpoints_to_try = [
            f"https://api.brightdata.com/datasets/v3/log/{snapshot_id}",  # CORRECT endpoint!
            f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}",
            f"https://api.brightdata.com/datasets/gd_l1viktl72bvl7bjuj0/snapshot/{snapshot_id}",
            f"https://api.brightdata.com/datasets/v3/gd_l1viktl72bvl7bjuj0/items?snapshot_id={snapshot_id}",
            f"https://api.brightdata.com/datasets/gd_l1viktl72bvl7bjuj0/items?snapshot_id={snapshot_id}",
        ]

        import time

        # Wait a bit for snapshot to be ready
        print(f"\n⏱️  Waiting 10 seconds for snapshot processing...")
        time.sleep(10)

        for i, endpoint in enumerate(endpoints_to_try, 1):
            print(f"\n{i}. Trying: {endpoint}")
            try:
                resp = requests.get(endpoint, headers=headers, timeout=5)
                print(f"   Status: {resp.status_code}")
                if resp.status_code != 404:
                    print(f"   Response: {resp.text[:500]}")
                    if resp.ok:
                        print(f"\n✅ SUCCESS! This endpoint works!")
                        break
            except Exception as e:
                print(f"   Error: {e}")
else:
    print(f"\n❌ Filter creation failed!")
    print(f"Response: {response.text}")
