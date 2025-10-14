#!/usr/bin/env python3
"""
Quick test of title filter on clinical vs facilities roles
"""
import requests
import json

API_URL = "http://127.0.0.1:8000/discover-prospects-improved"

# Test with a smaller hospital to see filter in action quickly
payload = {
    "company_name": "Lankenau Medical Center",
    "company_city": "Wynnewood",
    "company_state": "Pennsylvania"
}

print("="*80)
print("Testing Title Filter with Lankenau Medical Center")
print("="*80)
print("This test will show how many clinical roles get filtered out...")
print()

try:
    response = requests.post(
        API_URL,
        json=payload,
        timeout=600
    )

    if response.status_code == 200:
        result = response.json()
        data = result['data']
        summary = data['pipeline_summary']

        print("FILTERING FUNNEL:")
        print(f"  1. Search results: {summary['search_results_found']}")
        print(f"  2. After basic filter: {summary['prospects_after_basic_filter']}")
        print(f"  3. After AI basic filter: {summary.get('prospects_after_ai_basic_filter', 'N/A')}")
        print(f"  4. After AI TITLE filter: {summary.get('prospects_after_ai_title_filter', 'N/A')}")
        print(f"     → Filtered by title: {summary.get('filtered_by_title', 'N/A')}")
        print(f"  5. LinkedIn profiles scraped: {summary['linkedin_profiles_scraped']}")
        print(f"  6. After advanced filter: {summary['prospects_after_advanced_filter']}")
        print(f"  7. Final prospects: {summary['final_top_prospects']}")
        print()

        if summary.get('filtered_by_title', 0) > 0:
            print(f"✓ SUCCESS: Title filter removed {summary['filtered_by_title']} clinical/irrelevant roles")
            print(f"  Cost savings: ${summary['filtered_by_title'] * 0.0047:.2f}")
        else:
            print("⚠ WARNING: Title filter did not filter any prospects")

        print()
        print("FINAL PROSPECTS:")
        for i, p in enumerate(data.get('qualified_prospects', [])[:10], 1):
            ld = p.get('linkedin_data', {})
            title = ld.get('job_title', 'N/A')
            score = p.get('ai_ranking', {}).get('ranking_score', 0)
            print(f"  {i}. {title} - Score: {score}")

            # Check if clinical role slipped through
            clinical_keywords = ['cardiovascular', 'surgery', 'wound', 'radiology',
                                'emergency', 'clinical', 'medical', 'nursing', 'patient']
            if any(kw in title.lower() for kw in clinical_keywords):
                print(f"     ⚠ CLINICAL ROLE DETECTED!")

    else:
        print(f"Error: {response.status_code}")
        print(response.text[:200])

except Exception as e:
    print(f"Error: {e}")

print("="*80)
