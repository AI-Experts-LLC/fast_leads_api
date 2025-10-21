"""
Batch test script for REMAINING 8 hospitals (rows 3-10)
Tests hospitals from CSV file with configurable start/end rows
"""
import requests
import json
import csv
import time
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CSV_FILE = "tests/LUCAS EDIT Hospital Campaign 2 - ID-MT w Parent Accounts.csv"
OUTPUT_DIR = f"batch_results_remaining_8_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Batch configuration - REMAINING 8 HOSPITALS (rows 3-10 in CSV, which is indices 2-10 in 0-indexed)
START_ROW = 2  # St. Vincent Healthcare (row 3)
END_ROW = 10   # Exclusive (so processes up to and including row 10 - Portneuf Medical Center)

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

def save_summary_csv(results):
    """Save summary CSV with all results"""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    filepath = output_path / "batch_summary.csv"

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'Hospital Name', 'City', 'State', 'Health System', 'Account ID',
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
                hospital['health_system'],
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
                'name': row['Hospital Name'],
                'city': row['City'],
                'state': row['State'],
                'health_system': row['Health System'],
                'account_id': row['Account ID'],
                'parent_id': row.get('Parent ID', '')
            })
    return hospitals

def run_step1(hospital):
    """Run Step 1: Search and Filter"""
    payload = {
        "company_name": hospital['name'],
        "company_city": hospital['city'],
        "company_state": hospital['state']
    }

    # Add parent account name if available (health system)
    if hospital.get('health_system') and hospital['health_system'].strip():
        payload['parent_account_name'] = hospital['health_system']

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
        'error_message': ''
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

                # Extract top prospect
                qualified = step3_result.get('qualified_prospects', [])
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
    print_section(f"3-STEP BATCH PROSPECT DISCOVERY - REMAINING 8 HOSPITALS")
    print(f"CSV File: {CSV_FILE}")
    print(f"Processing rows {START_ROW+1} to {END_ROW} (CSV rows, inclusive)")
    print(f"Output directory: {OUTPUT_DIR}")

    # Load hospitals
    all_hospitals = load_hospitals_from_csv()
    hospitals_to_process = all_hospitals[START_ROW:END_ROW]

    print(f"\nTotal hospitals in CSV: {len(all_hospitals)}")
    print(f"Hospitals to process: {len(hospitals_to_process)}")
    print(f"\nHospitals in this batch:")
    for i, h in enumerate(hospitals_to_process, 1):
        print(f"  {i}. {h['name']} - {h['city']}, {h['state']}")

    # Process each hospital
    batch_start = time.time()
    results = []

    for i, hospital in enumerate(hospitals_to_process, 1):
        result = process_hospital(hospital, i, len(hospitals_to_process))
        results.append(result)

        # Pause between hospitals to avoid rate limits
        if i < len(hospitals_to_process):
            print(f"\n⏳ Waiting 5 seconds before next hospital...")
            time.sleep(5)

    batch_elapsed = time.time() - batch_start

    # Save summary
    print_section("BATCH SUMMARY")
    print(f"Total batch time: {batch_elapsed:.1f}s ({batch_elapsed/60:.1f} minutes)")
    print(f"Average time per hospital: {batch_elapsed/len(hospitals_to_process):.1f}s")

    # Count successes
    successful = sum(1 for r in results if r['step3_status'] == 'Success')
    print(f"\n✅ Successfully processed: {successful}/{len(results)} hospitals")

    # Save summary CSV
    summary_path = save_summary_csv(results)

    # Save full results JSON
    full_results_path = save_json("full_batch_results.json", {
        'batch_config': {
            'csv_file': CSV_FILE,
            'start_row': START_ROW,
            'end_row': END_ROW,
            'total_processed': len(results)
        },
        'batch_summary': {
            'total_time': batch_elapsed,
            'successful': successful,
            'failed': len(results) - successful
        },
        'results': results
    })

    print(f"\n📊 Full results saved to: {full_results_path}")

    # Print top prospects summary
    print(f"\n🎯 TOP PROSPECTS SUMMARY:")
    print("-" * 100)
    for result in results:
        if 'top_prospect' in result:
            tp = result['top_prospect']
            print(f"\n{result['hospital']['name']} ({result['hospital']['city']}, {result['hospital']['state']})")
            print(f"  → {tp['name']} - {tp['title']}")
            print(f"  → Score: {tp['score']}/100 | Email: {tp['email']}")
            print(f"  → LinkedIn: {tp['linkedin_url']}")
        else:
            print(f"\n{result['hospital']['name']} ({result['hospital']['city']}, {result['hospital']['state']})")
            print(f"  → ❌ No qualified prospects found")
            if result['error_message']:
                print(f"  → Error: {result['error_message'][:100]}")

if __name__ == "__main__":
    main()
