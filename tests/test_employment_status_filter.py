"""
Test the employment status validation filter
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.three_step_prospect_discovery import three_step_prospect_discovery_service

# Test cases
test_cases = [
    {
        "name": "Current Employee - Current Company Match",
        "linkedin_data": {
            "name": "John Smith",
            "company": "Mayo Clinic",
            "job_title": "Director of Facilities",
            "experience": []
        },
        "company_name": "Mayo Clinic",
        "expected": True,
        "description": "Should PASS - current company matches"
    },
    {
        "name": "Current Employee - Experience with Present",
        "linkedin_data": {
            "name": "Jane Doe",
            "company": "Other Company",
            "job_title": "Director",
            "experience": [
                {
                    "company": "Mayo Clinic",
                    "title": "Director of Facilities",
                    "duration": "Jan 2020 - Present"
                }
            ]
        },
        "company_name": "Mayo Clinic",
        "expected": True,
        "description": "Should PASS - experience shows 'Present'"
    },
    {
        "name": "Former Employee - Ended Position",
        "linkedin_data": {
            "name": "Bob Johnson",
            "company": "New Hospital",
            "job_title": "Director",
            "experience": [
                {
                    "company": "Mayo Clinic",
                    "title": "Director of Facilities",
                    "duration": "Jan 2018 - Dec 2022"
                }
            ]
        },
        "company_name": "Mayo Clinic",
        "expected": False,
        "description": "Should FAIL - position ended in 2022"
    },
    {
        "name": "Retired Employee",
        "linkedin_data": {
            "name": "Mary Williams",
            "company": "Mayo Clinic",
            "job_title": "Retired CFO",
            "experience": []
        },
        "company_name": "Mayo Clinic",
        "expected": False,
        "description": "Should FAIL - title indicates retired"
    },
    {
        "name": "No Employment Record",
        "linkedin_data": {
            "name": "Tom Davis",
            "company": "Different Hospital",
            "job_title": "Director",
            "experience": [
                {
                    "company": "Other Health System",
                    "title": "Manager",
                    "duration": "2015 - Present"
                }
            ]
        },
        "company_name": "Mayo Clinic",
        "expected": False,
        "description": "Should FAIL - no employment at target company"
    },
    {
        "name": "Healthcare Suffix Variation",
        "linkedin_data": {
            "name": "Sarah Chen",
            "company": "Mayo Medical Center",
            "job_title": "Facilities Director",
            "experience": []
        },
        "company_name": "Mayo Clinic",
        "expected": True,
        "description": "Should PASS - company name variation matches"
    }
]

def run_tests():
    print("=" * 80)
    print("Testing Employment Status Validation Filter")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Description: {test['description']}")

        result = three_step_prospect_discovery_service._validate_employment_status(
            test['linkedin_data'],
            test['company_name']
        )

        is_current = result['is_current_employee']
        reason = result['reason']

        expected_result = test['expected']
        test_passed = is_current == expected_result

        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"  Result: {status}")
        print(f"  Is Current Employee: {is_current}")
        print(f"  Reason: {reason}")

        if test_passed:
            passed += 1
        else:
            failed += 1
            print(f"  ⚠️  Expected: {expected_result}, Got: {is_current}")

    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
