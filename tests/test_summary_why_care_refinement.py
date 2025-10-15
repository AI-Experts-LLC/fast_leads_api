"""
Test script to verify summary_why_care refinement functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.enrichers.web_search_contact_enricher import WebSearchContactEnricher


def test_refinement():
    """Test the summary_why_care refinement with sample data."""
    print("=" * 80)
    print("Testing summary_why_care Refinement")
    print("=" * 80)

    # Initialize enricher
    print("\n1. Initializing enricher...")
    enricher = WebSearchContactEnricher()
    print("✅ Enricher initialized")

    # Test cases with formal/robotic summaries
    test_cases = [
        {
            "first_name": "John",
            "company": "BOZEMAN HEALTH DEACONESS REGIONAL MEDICAL CENTER",
            "summary_why_care": "As the Chief Financial Officer at BOZEMAN HEALTH DEACONESS REGIONAL MEDICAL CENTER, I am certain you have experienced challenges with energy costs representing a significant operational expense and emergency repairs disrupting budgets."
        },
        {
            "first_name": "Sarah",
            "company": "ST. VINCENT HEALTHCARE, LLC",
            "summary_why_care": "Given your position as Senior Director, Facilities Operations at ST. VINCENT HEALTHCARE, LLC, you have undoubtedly encountered difficulties with aging infrastructure requiring constant maintenance and rising energy costs with limited budget."
        },
        {
            "first_name": "Mike",
            "company": "Providence Health & Services, Inc.",
            "summary_why_care": "In your capacity as Director of Facilities at Providence Health & Services, Inc., you certainly face challenges with constant firefighting with old equipment, pressure to reduce energy consumption, and increasing costs of emergency repairs."
        }
    ]

    print("\n2. Running refinement tests...\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}")
        print(f"{'='*80}")
        print(f"Name: {test_case['first_name']}")
        print(f"Company: {test_case['company']}")
        print(f"\nOriginal (formal/robotic):")
        print(f"  {test_case['summary_why_care']}")

        # Create data dict
        data = {"summary_why_care": test_case['summary_why_care']}

        # Refine it
        print(f"\nRefining...")
        refined_data = enricher._refine_summary_why_care(
            data,
            test_case['first_name'],
            test_case['company']
        )

        if refined_data and 'summary_why_care' in refined_data:
            print(f"\n✅ Refined (conversational):")
            print(f"  {refined_data['summary_why_care']}")

            # Check improvements
            original = test_case['summary_why_care']
            refined = refined_data['summary_why_care']

            improvements = []
            if original.isupper() != refined.isupper() and not refined.isupper():
                improvements.append("✓ Fixed all-caps text")
            if 'LLC' in original and 'LLC' not in refined:
                improvements.append("✓ Removed LLC suffix")
            if 'Inc.' in original and 'Inc.' not in refined:
                improvements.append("✓ Removed Inc. suffix")
            if len(refined) < len(original):
                improvements.append("✓ More concise")
            if "I'm sure" in refined or "I imagine" in refined:
                improvements.append("✓ Added conversational softeners")

            if improvements:
                print(f"\nImprovements detected:")
                for improvement in improvements:
                    print(f"  {improvement}")
        else:
            print(f"\n❌ Refinement failed")

    print(f"\n{'='*80}")
    print("Test completed!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    try:
        test_refinement()
        print("\n✅ All tests completed successfully")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
