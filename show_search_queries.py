#!/usr/bin/env python3
"""
Show Search Queries - Display what search terms are being used
"""

# Default target titles from search.py
DEFAULT_TITLES = [
    "Director of Facilities",
    "CFO",
    "Chief Financial Officer",
    "Sustainability Manager",
    "Energy Manager",
    "Chief Operating Officer",
    "Facilities Manager"
]

def show_search_queries(company_name, company_variations=None):
    """Show what search queries would be generated"""

    print("=" * 80)
    print(f"SEARCH QUERIES FOR: {company_name}")
    print("=" * 80)

    if company_variations:
        print(f"\nCompany Variations ({len(company_variations)}):")
        for i, variation in enumerate(company_variations, 1):
            print(f"  {i}. {variation}")

    print(f"\nTarget Titles ({len(DEFAULT_TITLES)}):")
    for i, title in enumerate(DEFAULT_TITLES, 1):
        print(f"  {i}. {title}")

    print(f"\n{'=' * 80}")
    print(f"EXAMPLE SEARCH QUERIES")
    print(f"{'=' * 80}")

    # Show first 5 queries as examples
    example_variations = company_variations[:2] if company_variations else [company_name]
    example_titles = DEFAULT_TITLES[:3]

    query_count = 0
    for variation in example_variations:
        for title in example_titles:
            query_count += 1
            query = f'{variation} {title} site:linkedin.com/in'
            print(f"\n{query_count}. Query: {query}")
            print(f"   → Searching Google for LinkedIn profiles with:")
            print(f"      • Company: '{variation}'")
            print(f"      • Title: '{title}'")
            print(f"      • Limited to: linkedin.com/in pages")
            print(f"   → Returns: Top 10 results (limited to first 5 per title)")

    total_queries = len(company_variations) * len(DEFAULT_TITLES) if company_variations else len(DEFAULT_TITLES)
    print(f"\n{'=' * 80}")
    print(f"TOTAL QUERIES: {total_queries}")
    print(f"{'=' * 80}")
    print(f"Expected results: ~{total_queries * 5} profiles (5 per query, deduplicated)")


if __name__ == "__main__":
    # Example 1: MedStar Health
    print("\n\n")
    medstar_variations = [
        "MedStar Health",
        "MedStar",
        "MedStar Health System",
        "MedStar Columbia",
        "MedStar Health - Columbia",
        "MedStar Health - Maryland",
        "MedStar Health Research Institute",
        "MedStar Health Foundation",
        "MedStar Health - Finance",
        "MedStar Health - Operations",
        "MedStar Health - Administration"
    ]
    show_search_queries("MedStar Health", medstar_variations)

    # Example 2: Mercy Medical Center
    print("\n\n")
    mercy_variations = [
        "Mercy Medical Center",
        "Mercy Medical Center Springfield",
        "Mercy Medical Center - Springfield",
        "Mercy Medical Center Massachusetts",
        "Mercy Springfield"
    ]
    show_search_queries("Mercy Medical Center", mercy_variations)

    # Show potential issues
    print("\n\n")
    print("=" * 80)
    print("⚠️  POTENTIAL SEARCH ISSUES & RECOMMENDATIONS")
    print("=" * 80)

    print("\n1. COMPANY NAME AMBIGUITY:")
    print("   Issue: 'Mercy Medical Center' exists in multiple cities")
    print("   Current: Searches for 'Mercy Medical Center' without location")
    print("   Result: Gets prospects from ALL Mercy Medical Centers nationwide")
    print("   Fix: Add city/state to search query")
    print("   Example: 'Mercy Medical Center Springfield Massachusetts Director of Facilities'")

    print("\n2. BROAD TITLE TERMS:")
    print("   Issue: 'CFO' and 'Chief Financial Officer' are redundant")
    print("   Current: Separate searches for both")
    print("   Result: Duplicate results, wasted API calls")
    print("   Fix: Remove 'CFO' and keep only 'Chief Financial Officer'")

    print("\n3. MISSING KEY TITLES:")
    print("   Issue: Not searching for energy-focused roles")
    print("   Current titles: Director of Facilities, CFO, COO, etc.")
    print("   Missing: Director of Engineering, VP of Facilities, Plant Manager")
    print("   According to buyer_persona.md:")
    print("   - Director of Engineering/Maintenance")
    print("   - VP Operations")
    print("   - Plant Operations")
    print("   - Maintenance Manager")

    print("\n4. TITLE SPECIFICITY:")
    print("   Issue: 'Sustainability Manager' and 'Energy Manager' are too specific")
    print("   Per buyer_persona.md: These are 'foot in door' but not primary buyers")
    print("   Primary buyers: Director of Facilities, CFO, Director of Engineering")
    print("   Fix: Prioritize decision-makers over sustainability roles")

    print("\n5. SEARCH QUERY FORMAT:")
    print("   Current: '{company} {title} site:linkedin.com/in'")
    print("   Better: '{company} {city} {state} {title} site:linkedin.com/in'")
    print("   Example: 'Mercy Medical Center Springfield Massachusetts CFO site:linkedin.com/in'")

    print("\n" + "=" * 80)
    print("💡 RECOMMENDED TITLE CHANGES")
    print("=" * 80)

    print("\nCurrent Titles:")
    for i, title in enumerate(DEFAULT_TITLES, 1):
        print(f"  {i}. {title}")

    print("\nRecommended Titles (based on buyer_persona.md):")
    recommended = [
        "Director of Facilities",
        "Director of Engineering",
        "Director of Maintenance",
        "Chief Financial Officer",
        "Chief Operating Officer",
        "VP Operations",
        "VP Facilities",
        "Facilities Manager",
        "Energy Manager",
        "Plant Manager",
        "Maintenance Manager"
    ]
    for i, title in enumerate(recommended, 1):
        print(f"  {i}. {title}")

    print("\n✅ This would better align with the buyer personas identified in your research!")
