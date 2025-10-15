#!/usr/bin/env python3
"""
Batch Prospect Discovery Test for All Hospitals
Runs the 4-step pipeline for a list of hospitals and compiles results into one CSV
"""

import requests
import json
import time
import csv
from datetime import datetime
from typing import Dict, Any, List
import sys

# Railway deployment URL
BASE_URL = "https://fast-leads-api.up.railway.app"

# Hospital list from user
HOSPITALS = [
    {
        "name": "St. Joseph Regional Medical Center",
        "city": "Lewiston",
        "state": "Idaho",
        "health_system": "RCCH HealthCare Partners (formerly Ascension)",
        "edfx_rating": "Ba1",
        "account_id": "001VR00000UhY3oYAF"
    },
    {
        "name": "St. Patrick Hospital",
        "city": "Missoula",
        "state": "Montana",
        "health_system": "Providence Health & Services (Providence Montana)",
        "edfx_rating": "Ba1",
        "account_id": "001VR00000UhY4hYAF"
    },
    {
        "name": "St. Vincent Healthcare",
        "city": "Billings",
        "state": "Montana",
        "health_system": "Intermountain Health (formerly SCL Health)",
        "edfx_rating": "Ba2",
        "account_id": "001VR00000UhXv2YAF"
    },
    {
        "name": "Community Medical Center",
        "city": "Missoula",
        "state": "Montana",
        "health_system": "Community Medical Center (Providence affiliated)",
        "edfx_rating": "Ba3",
        "account_id": "001VR00000VhCFNYA3"
    },
    {
        "name": "West Valley Medical Center",
        "city": "Caldwell",
        "state": "Idaho",
        "health_system": "HCA Healthcare",
        "edfx_rating": "",
        "account_id": "0017V00001SOG6LQAX"
    },
    {
        "name": "St. Luke's Magic Valley RMC",
        "city": "Twin Falls",
        "state": "Idaho",
        "health_system": "St. Luke's Health System",
        "edfx_rating": "",
        "account_id": "001VR00000VhECLYA3"
    },
    {
        "name": "Saint Alphonsus Regional Medical Center",
        "city": "Boise",
        "state": "Idaho",
        "health_system": "Saint Alphonsus Health System",
        "edfx_rating": "Ba1",
        "account_id": "001VR00000UhY7xYAF"
    },
    {
        "name": "Benefis Hospitals Inc",
        "city": "Great Falls",
        "state": "Montana",
        "health_system": "Benefis Health System",
        "edfx_rating": "Ba1",
        "account_id": "001VR00000UhXwBYAV"
    },
    {
        "name": "Bozeman Health Deaconess Regional Medical Center",
        "city": "Bozeman",
        "state": "Montana",
        "health_system": "Bozeman Health",
        "edfx_rating": "",
        "account_id": "0017V00001aggoqQAA"
    },
    {
        "name": "Billings Clinic Hospital",
        "city": "Billings",
        "state": "Montana",
        "health_system": "Billings Clinic (Independent)",
        "edfx_rating": "",
        "account_id": "0017V00001YEA77QAH"
    },
    {
        "name": "Logan Health Medical Center",
        "city": "Kalispell",
        "state": "Montana",
        "health_system": "Logan Health (formerly Kalispell Regional Healthcare)",
        "edfx_rating": "B1",
        "account_id": "001VR00000VhD3NYAV"
    },
    {
        "name": "Portneuf Medical Center",
        "city": "Pocatello",
        "state": "Idaho",
        "health_system": "Portneuf Health System",
        "edfx_rating": "B1",
        "account_id": "001VR00000Vh74QYAR"
    },
    {
        "name": "St. Luke's Regional Medical Center",
        "city": "Boise",
        "state": "Idaho",
        "health_system": "St. Luke's Health System",
        "edfx_rating": "Ba1",
        "account_id": "001VR00000UhY5JYAV"
    }
]


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_pipeline_for_hospital(hospital: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run the complete 4-step pipeline for a single hospital
    Returns list of qualified prospects
    """
    print_section(f"PROCESSING: {hospital['name']}")
    print(f"📍 Location: {hospital['city']}, {hospital['state']}")
    print(f"🏥 Health System: {hospital['health_system']}")
    print(f"💰 EDFX Rating: {hospital['edfx_rating'] or 'N/A'}")
    print(f"🔑 Account ID: {hospital['account_id']}")

    # STEP 1: Search & Filter
    print(f"\n⏳ Step 1: Search & Filter...")
    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step1",
            json={
                "company_name": hospital["name"],
                "company_city": hospital["city"],
                "company_state": hospital["state"]
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"❌ Step 1 failed: {response.status_code}")
            return []

        step1_data = response.json().get("data", response.json())
        if not step1_data.get("success"):
            print(f"❌ Step 1 failed: {step1_data.get('error')}")
            return []

        qualified = step1_data.get("qualified_prospects", [])
        print(f"✅ Step 1 complete: {len(qualified)} prospects qualified")

        if not qualified:
            print("⚠️  No prospects found, skipping to next hospital")
            return []

    except Exception as e:
        print(f"❌ Step 1 error: {str(e)}")
        return []

    time.sleep(2)

    # STEP 2: Scrape Profiles
    print(f"\n⏳ Step 2: Scrape LinkedIn Profiles...")
    try:
        linkedin_urls = [p.get("linkedin_url") for p in qualified if p.get("linkedin_url")]

        response = requests.post(
            f"{BASE_URL}/discover-prospects-step2",
            json={
                "linkedin_urls": linkedin_urls,
                "company_name": hospital["name"],
                "company_city": hospital["city"],
                "company_state": hospital["state"]
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"❌ Step 2 failed: {response.status_code}")
            return []

        step2_data = response.json().get("data", response.json())
        if not step2_data.get("success"):
            print(f"❌ Step 2 failed: {step2_data.get('error')}")
            return []

        enriched = step2_data.get("enriched_prospects", [])
        print(f"✅ Step 2 complete: {len(enriched)} prospects enriched")

        if not enriched:
            print("⚠️  No prospects passed filters, skipping to next hospital")
            return []

    except Exception as e:
        print(f"❌ Step 2 error: {str(e)}")
        return []

    time.sleep(2)

    # STEP 3: AI Ranking
    print(f"\n⏳ Step 3: AI Ranking...")
    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step3",
            json={
                "enriched_prospects": enriched,
                "company_name": hospital["name"],
                "min_score_threshold": 65,
                "max_prospects": 20  # Get more prospects per hospital
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"❌ Step 3 failed: {response.status_code}")
            return []

        step3_data = response.json().get("data", response.json())
        if not step3_data.get("success"):
            print(f"❌ Step 3 failed: {step3_data.get('error')}")
            return []

        final_prospects = step3_data.get("qualified_prospects", [])
        print(f"✅ Step 3 complete: {len(final_prospects)} prospects qualified")

        if not final_prospects:
            print("⚠️  No prospects scored above threshold, skipping to next hospital")
            return []

    except Exception as e:
        print(f"❌ Step 3 error: {str(e)}")
        return []

    time.sleep(2)

    # STEP 4: ZoomInfo Validation (disabled by default)
    print(f"\n⏳ Step 4: ZoomInfo Validation (disabled)...")
    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step4",
            json={
                "qualified_prospects": final_prospects,
                "company_name": hospital["name"],
                "enable_zoominfo": False
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"⚠️  Step 4 failed, using Step 3 results")
            validated_prospects = final_prospects
        else:
            step4_data = response.json().get("data", response.json())
            validated_prospects = step4_data.get("prospects", final_prospects)
            print(f"✅ Step 4 complete (validation skipped)")

    except Exception as e:
        print(f"⚠️  Step 4 error: {str(e)}, using Step 3 results")
        validated_prospects = final_prospects

    # Add hospital metadata to each prospect
    for prospect in validated_prospects:
        prospect["hospital_name"] = hospital["name"]
        prospect["hospital_city"] = hospital["city"]
        prospect["hospital_state"] = hospital["state"]
        prospect["health_system"] = hospital["health_system"]
        prospect["edfx_rating"] = hospital["edfx_rating"]
        prospect["account_id"] = hospital["account_id"]

    print(f"\n🎯 SUCCESS: Found {len(validated_prospects)} qualified prospects for {hospital['name']}")
    return validated_prospects


def save_all_to_csv(all_prospects: List[Dict[str, Any]], filename: str):
    """
    Save all prospects from all hospitals to a single CSV file
    """
    if not all_prospects:
        print("\n⚠️  No prospects to save")
        return

    fieldnames = [
        # Hospital info
        'hospital_name',
        'hospital_city',
        'hospital_state',
        'health_system',
        'edfx_rating',
        'account_id',
        # Prospect info
        'rank',
        'name',
        'job_title',
        'company',
        'location',
        'connections',
        'email',
        'mobile_number',
        'ai_score',
        'ai_reasoning',
        'linkedin_url',
        'headline',
        'summary',
        'total_experience_years',
        'professional_authority_score',
        'skills_count',
        'top_skills',
        'full_linkedin_data_json'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        rank = 1
        for prospect in all_prospects:
            linkedin_data = prospect.get("linkedin_data", {})
            ai_ranking = prospect.get("ai_ranking", {})

            # Get summary/about text safely
            summary_text = linkedin_data.get('summary') or linkedin_data.get('about') or ''
            summary_truncated = summary_text[:500] if summary_text else ''

            row = {
                # Hospital info
                'hospital_name': prospect.get('hospital_name', ''),
                'hospital_city': prospect.get('hospital_city', ''),
                'hospital_state': prospect.get('hospital_state', ''),
                'health_system': prospect.get('health_system', ''),
                'edfx_rating': prospect.get('edfx_rating', ''),
                'account_id': prospect.get('account_id', ''),
                # Prospect info
                'rank': rank,
                'name': linkedin_data.get('name', ''),
                'job_title': linkedin_data.get('job_title', ''),
                'company': linkedin_data.get('company', ''),
                'location': linkedin_data.get('location', ''),
                'connections': linkedin_data.get('connections', ''),
                'email': linkedin_data.get('email', ''),
                'mobile_number': linkedin_data.get('mobile_number', ''),
                'ai_score': ai_ranking.get('ranking_score', ''),
                'ai_reasoning': ai_ranking.get('reasoning', ''),
                'linkedin_url': linkedin_data.get('url', ''),
                'headline': linkedin_data.get('headline', ''),
                'summary': summary_truncated,
                'total_experience_years': linkedin_data.get('total_experience_years', ''),
                'professional_authority_score': linkedin_data.get('professional_authority_score', ''),
                'skills_count': linkedin_data.get('skills_count', ''),
                'top_skills': linkedin_data.get('top_skills_by_endorsements', ''),
                'full_linkedin_data_json': json.dumps(linkedin_data, ensure_ascii=False)
            }

            writer.writerow(row)
            rank += 1

    print(f"\n💾 Results saved to: {filename}")
    print(f"   {len(all_prospects)} total prospects exported")


def main():
    """
    Run prospect discovery pipeline for all hospitals
    """
    print_section("🏥 BATCH PROSPECT DISCOVERY - ALL HOSPITALS")
    print(f"\n🚀 Testing Railway Deployment: {BASE_URL}")
    print(f"📊 Total Hospitals: {len(HOSPITALS)}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    overall_start = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_prospects = []
    hospital_stats = []

    # Process each hospital
    for i, hospital in enumerate(HOSPITALS, 1):
        print(f"\n\n{'='*80}")
        print(f"  HOSPITAL {i}/{len(HOSPITALS)}")
        print(f"{'='*80}")

        try:
            prospects = run_pipeline_for_hospital(hospital)

            hospital_stats.append({
                'name': hospital['name'],
                'city': hospital['city'],
                'state': hospital['state'],
                'prospects_found': len(prospects),
                'success': len(prospects) > 0
            })

            all_prospects.extend(prospects)

            print(f"\n✅ Hospital {i}/{len(HOSPITALS)} complete")
            print(f"   Total prospects so far: {len(all_prospects)}")

        except Exception as e:
            print(f"\n❌ Error processing {hospital['name']}: {str(e)}")
            hospital_stats.append({
                'name': hospital['name'],
                'city': hospital['city'],
                'state': hospital['state'],
                'prospects_found': 0,
                'success': False,
                'error': str(e)
            })

        # Pause between hospitals to avoid rate limits
        if i < len(HOSPITALS):
            print(f"\n⏸️  Pausing 3 seconds before next hospital...")
            time.sleep(3)

    overall_elapsed = time.time() - overall_start

    # Save combined CSV
    csv_filename = f"all_hospitals_prospects_{timestamp}.csv"
    save_all_to_csv(all_prospects, csv_filename)

    # Save summary JSON
    json_filename = f"all_hospitals_summary_{timestamp}.json"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_hospitals": len(HOSPITALS),
        "successful_hospitals": sum(1 for s in hospital_stats if s['success']),
        "total_prospects": len(all_prospects),
        "total_time_seconds": overall_elapsed,
        "hospital_stats": hospital_stats,
        "hospitals": HOSPITALS
    }

    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Summary saved to: {json_filename}")

    # Final summary
    print_section("✅ BATCH PROCESSING COMPLETE")
    print(f"\n⏱️  Total Time: {overall_elapsed:.2f} seconds ({overall_elapsed/60:.2f} minutes)")
    print(f"\n📊 Final Statistics:")
    print(f"   • Total hospitals processed: {len(HOSPITALS)}")
    print(f"   • Successful: {sum(1 for s in hospital_stats if s['success'])}")
    print(f"   • Failed: {sum(1 for s in hospital_stats if not s['success'])}")
    print(f"   • 🎯 Total prospects found: {len(all_prospects)}")

    print(f"\n📋 Per-Hospital Breakdown:")
    for stat in hospital_stats:
        status = "✅" if stat['success'] else "❌"
        print(f"   {status} {stat['name']} ({stat['city']}, {stat['state']}): {stat['prospects_found']} prospects")

    print(f"\n📁 Output Files:")
    print(f"   • CSV: {csv_filename}")
    print(f"   • Summary: {json_filename}")

    print("\n" + "=" * 80)
    print("✅ Batch processing completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Batch processing failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
