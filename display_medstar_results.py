#!/usr/bin/env python3
"""
Display MedStar Health Prospect Discovery Results
"""

import json
import sys

def display_results(filename):
    """Display formatted results from JSON file"""

    with open(filename, 'r') as f:
        data = json.load(f)

    if data.get('status') != 'success':
        print("❌ Discovery failed")
        return

    result = data['data']
    prospects = result['qualified_prospects']
    pipeline = result['pipeline_summary']

    print("=" * 80)
    print("🏥 MEDSTAR HEALTH - PROSPECT DISCOVERY RESULTS")
    print("=" * 80)

    print(f"\n📊 PIPELINE SUMMARY:")
    print(f"   Company Variations Searched: {pipeline['company_variations_searched']}")
    print(f"   Search Results Found: {pipeline['search_results_found']}")
    print(f"   After Basic Filter: {pipeline['prospects_after_basic_filter']}")
    print(f"   LinkedIn Profiles Scraped: {pipeline['linkedin_profiles_scraped']}")
    print(f"   After Advanced Filter: {pipeline['prospects_after_advanced_filter']}")
    print(f"   Final Ranked Prospects: {pipeline['final_ranked_prospects']}")

    print(f"\n🎯 QUALIFIED PROSPECTS ({len(prospects)} total)")
    print("=" * 80)

    for i, prospect in enumerate(prospects, 1):
        linkedin_data = prospect.get('linkedin_data', {})
        ai_ranking = prospect.get('ai_ranking', {})

        name = linkedin_data.get('name', 'N/A')
        title = linkedin_data.get('job_title', linkedin_data.get('headline', 'N/A'))
        company = linkedin_data.get('company_name', linkedin_data.get('company', 'N/A'))
        location = linkedin_data.get('location', 'N/A')
        linkedin_url = prospect.get('linkedin_url', 'N/A')

        score = ai_ranking.get('ranking_score', 0)
        reasoning = ai_ranking.get('ranking_reasoning', 'N/A')

        print(f"\n{'='*80}")
        print(f"{i}. {name}")
        print(f"{'='*80}")
        print(f"   AI Score: {score}/100")
        print(f"   Title: {title}")
        print(f"   Company: {company}")
        print(f"   Location: {location}")
        print(f"   LinkedIn: {linkedin_url}")
        print(f"   \n   Scoring: {reasoning}")

        # Additional details
        connections = linkedin_data.get('connections', 'N/A')
        duration = linkedin_data.get('current_job_duration', 'N/A')
        skills = linkedin_data.get('top_skills_by_endorsements', 'N/A')

        print(f"\n   Details:")
        print(f"     • Current Role Duration: {duration}")
        print(f"     • LinkedIn Connections: {connections}")
        print(f"     • Top Skills: {skills}")

        # Show company info
        company_size = linkedin_data.get('company_size', 'N/A')
        company_industry = linkedin_data.get('company_industry', 'N/A')

        print(f"\n   Company Info:")
        print(f"     • Industry: {company_industry}")
        print(f"     • Size: {company_size}")

    print(f"\n{'='*80}")
    print(f"✅ Discovery complete - {len(prospects)} qualified prospects found")
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Find most recent medstar file
        import glob
        files = glob.glob("medstar_prospects_*.json")
        if not files:
            print("No medstar_prospects_*.json files found")
            sys.exit(1)
        filename = max(files)
        print(f"Using most recent file: {filename}\n")

    display_results(filename)
