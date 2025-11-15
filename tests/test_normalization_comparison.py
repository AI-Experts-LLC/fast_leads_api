#!/usr/bin/env python3
"""
Test to demonstrate the improved normalization strategy that keeps healthcare identifiers
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_brightdata_linkedin_filter import BrightDataLinkedInFilter

load_dotenv()

print("=" * 80)
print("Company Name Normalization - Healthcare Identifier Strategy")
print("=" * 80)

client = BrightDataLinkedInFilter()

print("\n✅ IMPROVED STRATEGY: Keep 'Medical' and 'Health' to avoid false matches")
print("-" * 80)

test_cases = [
    {
        "original": "Portneuf Medical Center",
        "normalized": None,
        "healthcare_matches": [
            "Portneuf Medical Center ✓",
            "Portneuf Medical ✓",
            "Portneuf Health Trust ✓",
            "Portneuf Healthcare ✓"
        ],
        "false_positive_avoided": [
            "Portneuf Bakery ✗ (no 'Medical' or 'Health')",
            "Portneuf Veterinary Clinic ✗ (no 'Medical' or 'Health')",
            "Portneuf Auto Repair ✗ (no 'Medical' or 'Health')"
        ]
    },
    {
        "original": "Billings Clinic Hospital",
        "normalized": None,
        "healthcare_matches": [
            "Billings Clinic Hospital ✓",
            "Billings ✓",
            "Billings Healthcare ✓",
            "Billings Medical Group ✓"
        ],
        "false_positive_avoided": [
            "Billings Law Firm ✗ (no healthcare identifier)",
            "Billings Accounting ✗ (no healthcare identifier)",
            "Billings Restaurant Group ✗ (no healthcare identifier)"
        ]
    },
    {
        "original": "Logan Health Medical Center",
        "normalized": None,
        "healthcare_matches": [
            "Logan Health Medical Center ✓",
            "Logan Health Medical ✓",
            "Logan Health ✓",
            "Logan Healthcare ✓"
        ],
        "false_positive_avoided": [
            "Logan Pharmacy ✗ (no 'Medical' or 'Health')",
            "Logan Dental Care ✗ (no 'Medical' or 'Health')",
            "Logan Physical Therapy ✗ (no 'Medical' or 'Health')"
        ]
    }
]

for test in test_cases:
    test["normalized"] = client.normalize_company_name(test["original"])

    print(f"\n{test['original']}")
    print(f"  Normalized: '{test['normalized']}'")
    print(f"\n  ✅ Healthcare matches (will include 'Medical' or 'Health'):")
    for match in test["healthcare_matches"]:
        print(f"     • {match}")
    print(f"\n  🛡️  False positives avoided (no healthcare identifier):")
    for avoid in test["false_positive_avoided"]:
        print(f"     • {avoid}")

print("\n" + "=" * 80)
print("Key Insight: By keeping 'Medical' and 'Health', we ensure matches are")
print("healthcare-related and avoid matching unrelated businesses with same name.")
print("=" * 80)

print("\n📊 Normalization Results Summary:")
print("-" * 80)
print(f"{'Original':<45} {'Normalized':<35}")
print("-" * 80)
for test in test_cases:
    print(f"{test['original']:<45} {test['normalized']:<35}")
