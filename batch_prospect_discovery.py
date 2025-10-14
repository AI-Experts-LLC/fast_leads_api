#!/usr/bin/env python3
"""
Batch Prospect Discovery Script

Reads a CSV of hospital accounts and runs improved prospect discovery
on each one via the Fast Leads API on Railway.
"""

import csv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'batch_prospect_discovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "https://fast-leads-api.up.railway.app"
API_KEY = os.getenv("API_KEY", "metrus-secure-2025-key")
INPUT_CSV = "/Users/lucaserb/Documents/MetrusEnergy/metrus/salesforce_testing/data/LUCAS EDIT Hospital Campaign 2 - ID-MT w Parent Accounts.csv"
OUTPUT_DIR = "/Users/lucaserb/Documents/MetrusEnergy/fast_leads_api"

# TEST MODE - Set to True to only process first hospital
TEST_MODE = True
MAX_HOSPITALS = 1 if TEST_MODE else None

# TEST SPECIFIC HOSPITAL - Set hospital name to test specific one
TEST_HOSPITAL_NAME = "St. Vincent Healthcare"  # Set to None to test first in CSV

# Target titles for hospital buyer persona
DEFAULT_TARGET_TITLES = [
    "Chief Financial Officer",
    "CFO",
    "VP Finance",
    "Vice President Finance",
    "Director of Finance",
    "Chief Operating Officer",
    "COO",
    "VP Operations",
    "Vice President Operations",
    "Director of Facilities",
    "Facilities Director",
    "Energy Manager",
    "Sustainability Director"
]


def read_hospital_csv(file_path: str) -> List[Dict[str, str]]:
    """Read the hospital CSV file and return list of hospital records."""
    hospitals = []
    
    logger.info(f"Reading CSV file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hospitals.append(row)
    
    logger.info(f"📋 Loaded {len(hospitals)} hospitals from CSV")
    return hospitals


def call_prospect_discovery_api(
    company_name: str,
    city: str,
    state: str,
    account_id: str
) -> Dict[str, Any]:
    """
    Call the improved prospect discovery API for a hospital.
    
    Args:
        company_name: Hospital name
        city: City location
        state: State location
        account_id: Salesforce Account ID
        
    Returns:
        API response dict
    """
    url = f"{API_BASE_URL}/discover-prospects-improved"
    
    payload = {
        "company_name": company_name,
        "company_city": city,
        "company_state": state,
        "target_titles": DEFAULT_TARGET_TITLES
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    logger.info("="*80)
    logger.info(f"🔍 Discovering prospects for: {company_name}")
    logger.info(f"📍 Location: {city}, {state}")
    logger.info(f"🏥 Account ID: {account_id}")
    logger.info("="*80)
    
    try:
        logger.info("⏳ Calling API...")
        logger.info("   This may take 5-10 minutes due to AI filtering and LinkedIn scraping...")
        start_time = time.time()
        
        # Set longer timeout: (connect timeout, read timeout)
        # Connect timeout: 10s, Read timeout: 15 minutes for long-running prospect discovery
        response = requests.post(url, json=payload, headers=headers, timeout=(10, 900))
        
        elapsed = time.time() - start_time
        logger.info(f"⏱️  Response received in {elapsed:.1f} seconds")
        logger.info(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract prospect counts
            data = result.get('data', {})
            prospects = data.get('prospects', [])
            stats = data.get('stats', {})
            
            logger.info("✅ SUCCESS!")
            logger.info(f"   Found {len(prospects)} prospects")
            logger.info(f"   LinkedIn search: {stats.get('linkedin_search_results', 0)} results")
            logger.info(f"   After filtering: {stats.get('after_filtering', 0)} prospects")
            logger.info(f"   Successfully scraped: {stats.get('successfully_scraped', 0)} profiles")
            logger.info(f"   AI ranked: {stats.get('ai_ranked', 0)} prospects")
            
            return {
                "success": True,
                "company_name": company_name,
                "account_id": account_id,
                "city": city,
                "state": state,
                "prospects": prospects,
                "stats": stats,
                "response_time": elapsed
            }
        else:
            logger.error(f"❌ API Error: {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            
            return {
                "success": False,
                "company_name": company_name,
                "account_id": account_id,
                "error": f"API returned {response.status_code}",
                "response_time": elapsed
            }
            
    except requests.Timeout:
        logger.error("⏰ Timeout after 600 seconds (10 minutes)")
        return {
            "success": False,
            "company_name": company_name,
            "account_id": account_id,
            "error": "Request timeout"
        }
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return {
            "success": False,
            "company_name": company_name,
            "account_id": account_id,
            "error": str(e)
        }


def save_results_to_csv(all_results: List[Dict[str, Any]], output_path: str):
    """
    Save all prospect discovery results to a comprehensive CSV.
    
    Args:
        all_results: List of API results for each hospital
        output_path: Path to save CSV file
    """
    # Flatten all prospects into rows
    rows = []
    
    for result in all_results:
        if not result.get('success'):
            # Add error row
            rows.append({
                'Hospital Name': result['company_name'],
                'City': result.get('city', ''),
                'State': result.get('state', ''),
                'Account ID': result['account_id'],
                'Status': 'ERROR',
                'Error': result.get('error', 'Unknown error'),
                'Prospect Name': '',
                'Title': '',
                'LinkedIn URL': '',
                'AI Score': '',
                'Rejection Reason': '',
                'Company': '',
                'Location': '',
                'Email': '',
                'Phone': ''
            })
            continue
        
        prospects = result.get('prospects', [])
        
        if not prospects:
            # Add row indicating no prospects found
            rows.append({
                'Hospital Name': result['company_name'],
                'City': result['city'],
                'State': result['state'],
                'Account ID': result['account_id'],
                'Status': 'NO PROSPECTS FOUND',
                'Error': '',
                'Prospect Name': '',
                'Title': '',
                'LinkedIn URL': '',
                'AI Score': '',
                'Rejection Reason': '',
                'Company': '',
                'Location': '',
                'Email': '',
                'Phone': ''
            })
            continue
        
        # Add row for each prospect
        for prospect in prospects:
            rows.append({
                'Hospital Name': result['company_name'],
                'City': result['city'],
                'State': result['state'],
                'Account ID': result['account_id'],
                'Status': 'SUCCESS',
                'Error': '',
                'Prospect Name': prospect.get('name', ''),
                'Title': prospect.get('title', ''),
                'LinkedIn URL': prospect.get('linkedin_url', ''),
                'AI Score': prospect.get('ai_ranking', {}).get('total_score', ''),
                'Rejection Reason': prospect.get('ai_ranking', {}).get('rejection_reason', ''),
                'Company': prospect.get('company', ''),
                'Location': prospect.get('location', ''),
                'Email': prospect.get('email', ''),
                'Phone': prospect.get('phone', '')
            })
    
    # Write to CSV
    if rows:
        fieldnames = [
            'Hospital Name', 'City', 'State', 'Account ID', 'Status', 'Error',
            'Prospect Name', 'Title', 'LinkedIn URL', 'AI Score', 'Rejection Reason',
            'Company', 'Location', 'Email', 'Phone'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"✅ Results saved to: {output_path}")
        logger.info(f"   Total rows: {len(rows)}")
    else:
        logger.warning("⚠️ No results to save")


def save_full_json_results(all_results: List[Dict[str, Any]], output_path: str):
    """Save complete JSON results for reference."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"📄 Full JSON results saved to: {output_path}")


def main():
    """Main execution function."""
    logger.info("="*80)
    logger.info("🚀 BATCH PROSPECT DISCOVERY - Fast Leads API")
    logger.info("="*80)
    
    if TEST_MODE:
        logger.info(f"⚠️  TEST MODE ENABLED - Processing only first {MAX_HOSPITALS} hospital(s)")
    
    # Read hospitals from CSV
    hospitals = read_hospital_csv(INPUT_CSV)
    
    if not hospitals:
        logger.error("❌ No hospitals found in CSV")
        return
    
    # Filter for specific hospital if TEST_HOSPITAL_NAME is set
    if TEST_HOSPITAL_NAME:
        filtered_hospitals = [h for h in hospitals if h.get('Hospital Name', '').strip() == TEST_HOSPITAL_NAME]
        if filtered_hospitals:
            hospitals = filtered_hospitals
            logger.info(f"Testing specific hospital: {TEST_HOSPITAL_NAME}")
        else:
            logger.error(f"Hospital '{TEST_HOSPITAL_NAME}' not found in CSV")
            return
    # Limit hospitals in test mode
    elif TEST_MODE and MAX_HOSPITALS:
        hospitals = hospitals[:MAX_HOSPITALS]
        logger.info(f"Limited to {len(hospitals)} hospital(s) for testing")
    
    # Process each hospital
    all_results = []
    
    for i, hospital in enumerate(hospitals, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"📍 Processing {i}/{len(hospitals)}")
        logger.info(f"{'='*80}")
        
        company_name = hospital.get('Hospital Name', '').strip()
        city = hospital.get('City', '').strip()
        state = hospital.get('State', '').strip()
        account_id = hospital.get('Account ID', '').strip()
        
        if not company_name or not account_id:
            logger.warning("⚠️ Skipping row - missing hospital name or account ID")
            continue
        
        # Call API
        result = call_prospect_discovery_api(
            company_name=company_name,
            city=city,
            state=state,
            account_id=account_id
        )
        
        all_results.append(result)
        
        # Brief pause between requests to be nice to the API
        if i < len(hospitals):
            logger.info("\n⏸️  Waiting 5 seconds before next request...")
            time.sleep(5)
    
    # Generate output filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_output = os.path.join(OUTPUT_DIR, f"prospect_discovery_results_{timestamp}.csv")
    json_output = os.path.join(OUTPUT_DIR, f"prospect_discovery_results_{timestamp}.json")
    
    # Save results
    logger.info("\n" + "="*80)
    logger.info("💾 SAVING RESULTS")
    logger.info("="*80)
    
    save_results_to_csv(all_results, csv_output)
    save_full_json_results(all_results, json_output)
    
    # Summary statistics
    logger.info("\n" + "="*80)
    logger.info("📊 SUMMARY STATISTICS")
    logger.info("="*80)
    
    total_hospitals = len(all_results)
    successful = sum(1 for r in all_results if r.get('success'))
    failed = total_hospitals - successful
    total_prospects = sum(len(r.get('prospects', [])) for r in all_results if r.get('success'))
    
    logger.info(f"Total Hospitals: {total_hospitals}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total Prospects Found: {total_prospects}")
    logger.info(f"Average Prospects per Hospital: {total_prospects / successful if successful > 0 else 0:.1f}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ BATCH PROSPECT DISCOVERY COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    main()

