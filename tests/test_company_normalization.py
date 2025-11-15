#!/usr/bin/env python3
"""
Test company name normalization to show what gets removed
"""

import os
import sys
import csv
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

print("=" * 80)
print("Company Name Normalization Test")
print("=" * 80)

client = BrightDataLinkedInFilter()

# Read hospitals from CSV
csv_path = "docs/archive/HospitalAccountsAndIDs.csv"
hospitals = []

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        hospitals.append(row['Hospital'])

print(f"\nTesting normalization on {len(hospitals)} hospitals:")
print("-" * 80)

for hospital in hospitals:
    normalized = client.normalize_company_name(hospital)
    if normalized != hospital:
        print(f"✓ {hospital}")
        print(f"  → {normalized}")
    else:
        print(f"  {hospital} (no change)")

print("\n" + "=" * 80)
print("Examples of what gets matched:")
print("=" * 80)

examples = [
    ("Portneuf Medical Center", [
        "Portneuf Medical Center",
        "Portneuf",
        "PORTNEUF HEALTH TRUST",
        "Portneuf Health",
        "Portneuf Hospital"
    ]),
    ("Billings Clinic Hospital", [
        "Billings Clinic Hospital",
        "Billings Clinic",
        "Billings",
        "Billings Healthcare",
        "Billings Medical Center"
    ]),
    ("St. Luke's Regional Medical Center", [
        "St. Luke's Regional Medical Center",
        "St. Luke's",
        "Saint Luke's",
        "St Luke's Hospital",
        "St. Luke's Health System"
    ])
]

for original, variations in examples:
    normalized = client.normalize_company_name(original)
    print(f"\n{original} → '{normalized}'")
    print("  Would match variations like:")
    for variation in variations:
        print(f"    • {variation}")
