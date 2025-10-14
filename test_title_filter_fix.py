#!/usr/bin/env python3
"""
Test the fixed title filter with a small hospital
"""
import requests
import json

API_URL = "http://127.0.0.1:8000/discover-prospects-improved"

# Small hospital to test quickly
payload = {
    "company_name": "Baptist Health South Florida",
    "company_city": "Miami",
    "company_state": "Florida"
}

print("=" * 80)
print("Testing FIXED Title Filter")
print("=" * 80)
print()

try:
    response = requests.post(API_URL, json=payload, timeout=600)

    if response.status_code == 200:
        result = response.json()
        data = result['data']
        summary = data['pipeline_summary']

        print("FILTERING FUNNEL:")
        print(f"  1. Search results: {summary['search_results_found']}")
        print(f"  2. After basic filter: {summary['prospects_after_basic_filter']}")
        print(f"  3. After AI basic filter: {summary.get('prospects_after_ai_basic_filter', 'N/A')}")
        print(f"  4. ✓ After AI TITLE filter: {summary.get('prospects_after_ai_title_filter', 'N/A')}")
        print(f"     → ✓ Filtered by title: {summary.get('filtered_by_title', 'N/A')}")
        print(f"  5. LinkedIn profiles scraped: {summary['linkedin_profiles_scraped']}")
        print(f"  6. After advanced filter: {summary['prospects_after_advanced_filter']}")
        print(f"  7. Final prospects: {summary['final_top_prospects']}")
        print()

        filtered_count = summary.get('filtered_by_title', 0)
        if filtered_count > 0:
            print(f"✓ SUCCESS: Title filter removed {filtered_count} clinical/irrelevant roles")
            print(f"  LinkedIn profiles saved from scraping: {filtered_count}")
            print(f"  Cost savings: ${filtered_count * 0.0047:.2f}")
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
                print(f"     ✗ CLINICAL ROLE DETECTED!")

    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"Error: {e}")

print("=" * 80)
