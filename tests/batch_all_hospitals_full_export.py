"""
Comprehensive batch processing for all hospitals in HospitalAccountsAndIDs.csv
Exports detailed CSV with ALL prospect data fields
"""
import requests
import json
import csv
import time
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CSV_FILE = "HospitalAccountsAndIDs.csv"
OUTPUT_DIR = f"hospital_prospects_full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*100)
    print(f"  {title}")
    print("="*100 + "\n")

def save_json(filename, data):
    """Save data to JSON file"""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    filepath = output_path / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return str(filepath)

def flatten_prospect_data(prospect, hospital):
    """
    Flatten prospect data into a single-level dictionary for CSV export.
    Includes ALL fields from LinkedIn data, AI ranking, and hospital context.
    """
    linkedin_data = prospect.get('linkedin_data', {})
    ai_ranking = prospect.get('ai_ranking', {})
    advanced_filter = prospect.get('advanced_filter', {})

    # Build comprehensive flat dictionary with ALL available fields
    flat_data = {
        # Hospital Information
        'hospital_name': hospital['name'],
        'hospital_city': hospital['city'],
        'hospital_state': hospital['state'],
        'hospital_account_id': hospital['account_id'],

        # Prospect Core Identity
        'linkedin_url': linkedin_data.get('url', ''),
        'first_name': linkedin_data.get('first_name', ''),
        'last_name': linkedin_data.get('last_name', ''),
        'full_name': linkedin_data.get('name', ''),

        # Current Position
        'headline': linkedin_data.get('headline', ''),
        'job_title': linkedin_data.get('job_title', ''),
        'company': linkedin_data.get('company', ''),
        'company_name': linkedin_data.get('company_name', ''),

        # Location
        'location': linkedin_data.get('location', ''),
        'city': linkedin_data.get('city', ''),
        'state': linkedin_data.get('state', ''),

        # Professional Summary
        'summary': linkedin_data.get('summary', ''),
        'about': linkedin_data.get('about', ''),

        # Network Metrics
        'connections': linkedin_data.get('connections', ''),
        'followers': linkedin_data.get('followers', ''),

        # Experience & Skills
        'total_experience_years': linkedin_data.get('total_experience_years', ''),
        'professional_authority_score': linkedin_data.get('professional_authority_score', ''),
        'skills_count': linkedin_data.get('skills_count', 0),
        'top_skills': ', '.join(linkedin_data.get('skills', [])[:10]) if linkedin_data.get('skills') else '',
        'top_skills_by_endorsements': linkedin_data.get('top_skills_by_endorsements', ''),

        # Contact Information
        'email': linkedin_data.get('email', ''),
        'mobile_number': linkedin_data.get('mobile_number', ''),

        # Profile Metrics
        'profile_completeness_score': linkedin_data.get('profile_completeness_score', ''),
        'accessibility_score': linkedin_data.get('accessibility_score', ''),
        'engagement_score': linkedin_data.get('engagement_score', ''),

        # AI Ranking
        'ai_ranking_score': ai_ranking.get('ranking_score', ''),
        'ai_ranking_reasoning': ai_ranking.get('ranking_reasoning', ''),
        'ranked_by': ai_ranking.get('ranked_by', ''),
        'rank_position': ai_ranking.get('rank_position', ''),

        # Advanced Filter Results
        'seniority_score': advanced_filter.get('seniority_score', ''),
        'company_match': advanced_filter.get('company_match', ''),
        'filter_current_title': advanced_filter.get('current_title', ''),
        'filter_current_company': advanced_filter.get('current_company', ''),

        # Data Source
        'data_source': prospect.get('data_source', ''),
        'has_complete_data': prospect.get('has_complete_data', ''),

        # Timestamp
        'export_timestamp': datetime.now().isoformat()
    }

    return flat_data

def save_prospects_csv(all_prospects, hospitals_processed):
    """Save detailed CSV with ALL prospect fields"""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    filepath = output_path / "all_prospects_detailed.csv"

    if not all_prospects:
        print("⚠️  No prospects to export")
        return None

    # Get all field names from first prospect
    fieldnames = list(all_prospects[0].keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_prospects)

    print(f"✅ Detailed prospects CSV saved to: {filepath}")
    print(f"   Total prospects: {len(all_prospects)}")
    print(f"   Total fields per prospect: {len(fieldnames)}")
    return str(filepath)

def save_summary_csv(results):
    """Save high-level summary CSV"""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    filepath = output_path / "batch_summary.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'Hospital Name', 'City', 'State', 'Account ID',
            'Step 1 Status', 'Step 2 Status', 'Step 3 Status',
            'Search Results', 'After Title Filter', 'Profiles Scraped',
            'After Advanced Filter', 'Final Qualified', 'Total Time (s)',
            'Top Prospect Name', 'Top Prospect Title', 'Top Prospect Score',
            'Top Prospect LinkedIn', 'Top Prospect Email', 'Error Message'
        ])

        # Data rows
        for result in results:
            hospital = result['hospital']
            step1 = result.get('step1_summary', {})
            step2 = result.get('step2_summary', {})
            step3 = result.get('step3_summary', {})
            top_prospect = result.get('top_prospect', {})

            writer.writerow([
                hospital['name'],
                hospital['city'],
                hospital['state'],
                hospital['account_id'],
                result.get('step1_status', 'Failed'),
                result.get('step2_status', 'Failed'),
                result.get('step3_status', 'Failed'),
                step1.get('total_search_results', 0),
                step1.get('after_title_filter', 0),
                step2.get('profiles_scraped', 0),
                step2.get('after_advanced_filter', 0),
                step3.get('final_top_prospects', 0),
                result.get('total_time', 0),
                top_prospect.get('name', ''),
                top_prospect.get('title', ''),
                top_prospect.get('score', ''),
                top_prospect.get('linkedin_url', ''),
                top_prospect.get('email', ''),
                result.get('error_message', '')
            ])

    print(f"✅ Summary CSV saved to: {filepath}")
    return str(filepath)

def load_hospitals_from_csv():
    """Load hospitals from CSV file"""
    hospitals = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hospitals.append({
                'name': row['Hospital'],
                'city': row['City'],
                'state': row['State'],
                'account_id': row['Account ID']
            })
    return hospitals

def run_step1(hospital):
    """Run Step 1: Search and Filter"""
    payload = {
        "company_name": hospital['name'],
        "company_city": hospital['city'],
        "company_state": hospital['state']
    }

    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step1",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get("data", response_data)

            if result.get("success"):
                return {
                    'success': True,
                    'result': result,
                    'summary': result.get('summary', {}),
                    'qualified_prospects': result.get('qualified_prospects', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'result': result
                }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def run_step2(hospital, step1_result):
    """Run Step 2: Scrape LinkedIn Profiles"""
    qualified_prospects = step1_result.get('qualified_prospects', [])
    linkedin_urls = [p.get('linkedin_url') for p in qualified_prospects if p.get('linkedin_url')]

    if not linkedin_urls:
        return {
            'success': False,
            'error': 'No LinkedIn URLs from Step 1'
        }

    payload = {
        "linkedin_urls": linkedin_urls,
        "company_name": hospital['name'],
        "company_city": hospital['city'],
        "company_state": hospital['state'],
        "location_filter_enabled": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step2",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180
        )

        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get("data", response_data)

            if result.get("success"):
                return {
                    'success': True,
                    'result': result,
                    'summary': result.get('summary', {}),
                    'enriched_prospects': result.get('enriched_prospects', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'result': result
                }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def run_step3(hospital, step2_result):
    """Run Step 3: AI Ranking"""
    enriched_prospects = step2_result.get('enriched_prospects', [])

    if not enriched_prospects:
        return {
            'success': False,
            'error': 'No enriched prospects from Step 2'
        }

    payload = {
        "enriched_prospects": enriched_prospects,
        "company_name": hospital['name'],
        "min_score_threshold": 65,
        "max_prospects": 10
    }

    try:
        response = requests.post(
            f"{BASE_URL}/discover-prospects-step3",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        if response.status_code == 200:
            response_data = response.json()
            result = response_data.get("data", response_data)

            if result.get("success"):
                return {
                    'success': True,
                    'result': result,
                    'summary': result.get('summary', {}),
                    'qualified_prospects': result.get('qualified_prospects', [])
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'result': result
                }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_hospital(hospital, index, total):
    """Process a single hospital through all 3 steps"""
    print_section(f"Hospital {index}/{total}: {hospital['name']} - {hospital['city']}, {hospital['state']}")

    result = {
        'hospital': hospital,
        'step1_status': 'Not Started',
        'step2_status': 'Not Started',
        'step3_status': 'Not Started',
        'total_time': 0,
        'error_message': '',
        'all_qualified_prospects': []  # Store ALL qualified prospects for CSV export
    }

    start_time = time.time()

    # Step 1: Search and Filter
    print(f"\n🔍 Step 1: Searching and filtering prospects...")
    step1_start = time.time()
    step1_result = run_step1(hospital)
    step1_time = time.time() - step1_start

    if step1_result['success']:
        result['step1_status'] = 'Success'
        result['step1_summary'] = step1_result['summary']
        result['step1_data'] = step1_result['result']
        print(f"✅ Step 1 completed in {step1_time:.1f}s")
        print(f"   Found {step1_result['summary'].get('after_title_filter', 0)} qualified prospects")

        # Step 2: Scrape Profiles
        print(f"\n🔍 Step 2: Scraping LinkedIn profiles...")
        step2_start = time.time()
        step2_result = run_step2(hospital, step1_result['result'])
        step2_time = time.time() - step2_start

        if step2_result['success']:
            result['step2_status'] = 'Success'
            result['step2_summary'] = step2_result['summary']
            result['step2_data'] = step2_result['result']
            print(f"✅ Step 2 completed in {step2_time:.1f}s")
            print(f"   {step2_result['summary'].get('after_advanced_filter', 0)} prospects passed advanced filter")

            # Step 3: AI Ranking
            print(f"\n🤖 Step 3: AI ranking...")
            step3_start = time.time()
            step3_result = run_step3(hospital, step2_result['result'])
            step3_time = time.time() - step3_start

            if step3_result['success']:
                result['step3_status'] = 'Success'
                result['step3_summary'] = step3_result['summary']
                result['step3_data'] = step3_result['result']
                print(f"✅ Step 3 completed in {step3_time:.1f}s")
                print(f"   {step3_result['summary'].get('final_top_prospects', 0)} final qualified prospects")

                # Store ALL qualified prospects
                qualified = step3_result.get('qualified_prospects', [])
                result['all_qualified_prospects'] = qualified

                # Extract top prospect for summary
                if qualified:
                    top = qualified[0]
                    linkedin_data = top.get('linkedin_data', {})
                    ai_ranking = top.get('ai_ranking', {})

                    result['top_prospect'] = {
                        'name': linkedin_data.get('name', ''),
                        'title': linkedin_data.get('job_title', ''),
                        'score': ai_ranking.get('ranking_score', 0),
                        'linkedin_url': linkedin_data.get('url', ''),
                        'email': linkedin_data.get('email', ''),
                        'phone': linkedin_data.get('mobile_number', '')
                    }

                    print(f"\n🎯 Top Prospect: {result['top_prospect']['name']}")
                    print(f"   Title: {result['top_prospect']['title']}")
                    print(f"   Score: {result['top_prospect']['score']}/100")

                    # Print all qualified prospects
                    if len(qualified) > 1:
                        print(f"\n📋 All {len(qualified)} qualified prospects:")
                        for i, p in enumerate(qualified, 1):
                            ld = p.get('linkedin_data', {})
                            ar = p.get('ai_ranking', {})
                            print(f"   {i}. {ld.get('name', 'Unknown')} - {ld.get('job_title', 'Unknown')} (Score: {ar.get('ranking_score', 0)})")
            else:
                result['step3_status'] = 'Failed'
                result['error_message'] = step3_result['error']
                print(f"❌ Step 3 failed: {step3_result['error']}")
        else:
            result['step2_status'] = 'Failed'
            result['error_message'] = step2_result['error']
            print(f"❌ Step 2 failed: {step2_result['error']}")
    else:
        result['step1_status'] = 'Failed'
        result['error_message'] = step1_result['error']
        print(f"❌ Step 1 failed: {step1_result['error']}")

    result['total_time'] = time.time() - start_time
    print(f"\n⏱️  Total time for {hospital['name']}: {result['total_time']:.1f}s")

    # Save individual hospital results
    filename = f"{hospital['name'].replace(' ', '_')}_{hospital['city']}.json"
    save_json(filename, result)

    return result

def main():
    """Main batch processing function"""
    print_section(f"COMPREHENSIVE HOSPITAL PROSPECT DISCOVERY")
    print(f"CSV File: {CSV_FILE}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Load hospitals
    hospitals = load_hospitals_from_csv()

    print(f"\nTotal hospitals to process: {len(hospitals)}")
    print(f"\nHospitals:")
    for i, h in enumerate(hospitals, 1):
        print(f"  {i}. {h['name']} - {h['city']}, {h['state']} (ID: {h['account_id']})")

    # Confirm before starting
    print(f"\n⚠️  This will take approximately {len(hospitals) * 2} minutes to complete.")
    print(f"   Press Ctrl+C to cancel\n")
    time.sleep(3)

    # Process each hospital
    batch_start = time.time()
    results = []
    all_prospects_for_export = []

    for i, hospital in enumerate(hospitals, 1):
        result = process_hospital(hospital, i, len(hospitals))
        results.append(result)

        # Collect all prospects for detailed CSV export
        for prospect in result.get('all_qualified_prospects', []):
            flat_prospect = flatten_prospect_data(prospect, hospital)
            all_prospects_for_export.append(flat_prospect)

        # Pause between hospitals to avoid rate limits
        if i < len(hospitals):
            print(f"\n⏳ Waiting 5 seconds before next hospital...")
            time.sleep(5)

    batch_elapsed = time.time() - batch_start

    # Save exports
    print_section("EXPORTING RESULTS")

    # 1. Detailed prospects CSV with ALL fields
    prospects_csv_path = save_prospects_csv(all_prospects_for_export, results)

    # 2. Summary CSV
    summary_csv_path = save_summary_csv(results)

    # 3. Full JSON results
    full_results_path = save_json("full_batch_results.json", {
        'batch_config': {
            'csv_file': CSV_FILE,
            'total_hospitals': len(hospitals),
            'processing_date': datetime.now().isoformat()
        },
        'batch_summary': {
            'total_time_seconds': batch_elapsed,
            'total_time_minutes': batch_elapsed / 60,
            'successful_hospitals': sum(1 for r in results if r['step3_status'] == 'Success'),
            'failed_hospitals': sum(1 for r in results if r['step3_status'] != 'Success'),
            'total_prospects_found': len(all_prospects_for_export)
        },
        'results': results
    })

    # Final Summary
    print_section("FINAL BATCH SUMMARY")
    print(f"⏱️  Total batch time: {batch_elapsed:.1f}s ({batch_elapsed/60:.1f} minutes)")
    print(f"   Average time per hospital: {batch_elapsed/len(hospitals):.1f}s")

    successful = sum(1 for r in results if r['step3_status'] == 'Success')
    print(f"\n✅ Successfully processed: {successful}/{len(results)} hospitals")
    print(f"❌ Failed: {len(results) - successful}/{len(results)} hospitals")
    print(f"\n📊 Total prospects found: {len(all_prospects_for_export)}")
    print(f"   Average prospects per successful hospital: {len(all_prospects_for_export) / max(successful, 1):.1f}")

    print(f"\n📁 Output files:")
    print(f"   • Detailed prospects CSV: {prospects_csv_path}")
    print(f"   • Summary CSV: {summary_csv_path}")
    print(f"   • Full JSON results: {full_results_path}")
    print(f"   • Individual hospital JSONs: {OUTPUT_DIR}/")

    # Print top prospects summary
    print_section("TOP PROSPECTS BY HOSPITAL")
    for result in results:
        if 'top_prospect' in result:
            tp = result['top_prospect']
            print(f"\n✅ {result['hospital']['name']} ({result['hospital']['city']}, {result['hospital']['state']})")
            print(f"   → {tp['name']} - {tp['title']}")
            print(f"   → Score: {tp['score']}/100 | Email: {tp['email'] or 'N/A'}")
            print(f"   → LinkedIn: {tp['linkedin_url']}")
            print(f"   → Total qualified prospects: {len(result.get('all_qualified_prospects', []))}")
        else:
            print(f"\n❌ {result['hospital']['name']} ({result['hospital']['city']}, {result['hospital']['state']})")
            if result['error_message']:
                print(f"   → Error: {result['error_message'][:150]}")

    print("\n" + "="*100)
    print("  BATCH PROCESSING COMPLETE")
    print("="*100 + "\n")

if __name__ == "__main__":
    main()
