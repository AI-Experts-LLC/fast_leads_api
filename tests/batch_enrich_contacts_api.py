#!/usr/bin/env python3
"""
Batch Contact Enrichment via Web Search

Enriches contacts from Hospital CSV using the web search enricher directly.
Looks up Salesforce Contact IDs by email if not in CSV.

Usage:
    python batch_enrich_contacts_api.py --test-one    # Test with 1 contact
    python batch_enrich_contacts_api.py --test-three  # Test with 3 contacts
    python batch_enrich_contacts_api.py --all         # Process all contacts
"""

import os
import csv
import argparse
import re
import sys
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import enricher
from app.enrichers.web_search_contact_enricher import WebSearchContactEnricher

# Load environment variables
load_dotenv()

# Configuration
INPUT_CSV = 'tests/Hospital -Sheet2-Table 1.csv'

# Salesforce credentials for direct lookup if needed
SF_DOMAIN = os.getenv('SALESFORCE_DOMAIN')
SF_USERNAME = os.getenv('SALESFORCE_USERNAME')
SF_PASSWORD = os.getenv('SALESFORCE_PASSWORD')
SF_TOKEN = os.getenv('SALESFORCE_SECURITY_TOKEN')


def extract_contact_id_from_url(url_or_text: str) -> Optional[str]:
    """
    Extract Salesforce Contact ID from a Lightning URL.

    Examples:
        https://du0000000ie4tmaw.lightning.force.com/lightning/r/Contact/003VR00000ZPVywYAH/view
        -> 003VR00000ZPVywYAH

    Args:
        url_or_text: URL or text containing Contact ID

    Returns:
        Contact ID (18 characters starting with 003) or None
    """
    if not url_or_text:
        return None

    # Pattern for Contact IDs in URLs: /Contact/{ID}/
    match = re.search(r'/Contact/([a-zA-Z0-9]{15,18})(?:/|$)', url_or_text)
    if match:
        return match.group(1)

    # Pattern for standalone Contact IDs (003...)
    match = re.search(r'\b(003[a-zA-Z0-9]{12,15})\b', url_or_text)
    if match:
        return match.group(1)

    return None


def lookup_contact_by_email(email: str) -> Optional[str]:
    """
    Look up Salesforce Contact ID by email address.

    Args:
        email: Contact email address

    Returns:
        Contact ID or None if not found
    """
    try:
        from simple_salesforce import Salesforce

        sf = Salesforce(
            username=SF_USERNAME,
            password=SF_PASSWORD,
            security_token=SF_TOKEN,
            domain=SF_DOMAIN.replace('https://', '').replace('http://', '')
        )

        # Query for contact by email
        query = f"SELECT Id FROM Contact WHERE Email = '{email}' LIMIT 1"
        result = sf.query(query)

        if result['records']:
            return result['records'][0]['Id']

    except Exception as e:
        print(f"   ⚠️ Salesforce lookup error: {str(e)}")

    return None


async def enrich_contact_directly(contact_id: str, include_linkedin: bool = True) -> Dict[str, Any]:
    """
    Enrich a contact using the web search enricher directly.

    Args:
        contact_id: Salesforce Contact ID
        include_linkedin: Include LinkedIn enrichment

    Returns:
        Enrichment result dictionary
    """
    try:
        # Initialize enricher
        enricher = WebSearchContactEnricher()

        # Process enrichment
        result = await enricher.process_contact_enrichment(
            record_id=contact_id,
            overwrite=True,
            include_linkedin=include_linkedin
        )

        # The enricher writes directly to Salesforce and returns True/False
        if result:
            return {
                'success': True,
                'contact_id': contact_id
            }
        else:
            return {
                'success': False,
                'error': 'Enrichment failed',
                'contact_id': contact_id
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'contact_id': contact_id
        }


def read_contacts_from_csv() -> List[Dict[str, str]]:
    """
    Read contacts from the Hospital CSV.

    Returns:
        List of contact dictionaries with name, email, account, title
    """
    contacts = []

    with open(INPUT_CSV, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Skip empty rows
            name = row.get('Sort by:NameSorted Ascending', '').strip()
            if not name:
                continue

            # Check if there's a Contact ID in any field
            contact_id = None
            for field_value in row.values():
                if field_value:
                    extracted_id = extract_contact_id_from_url(field_value)
                    if extracted_id:
                        contact_id = extracted_id
                        break

            contacts.append({
                'name': name,
                'account_name': row.get('Sort by:Account NameSorted: None', '').strip(),
                'email': row.get('Sort by:EmailSorted: None', '').strip(),
                'title': row.get('Sort by:TitleSorted: None', '').strip(),
                'contact_id': contact_id
            })

    return contacts


async def process_contacts(contacts: List[Dict[str, str]], test_mode: Optional[int] = None):
    """
    Process and enrich contacts.

    Args:
        contacts: List of contact dictionaries
        test_mode: If specified, only process first N contacts
    """
    # Limit contacts in test mode
    if test_mode:
        contacts = contacts[:test_mode]
        print(f"\n🧪 TEST MODE: Processing {test_mode} contact(s)\n")
    else:
        print(f"\n📧 FULL MODE: Processing {len(contacts)} contacts\n")

    # Prepare output CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv = f'tests/contact_enrichment_results_{timestamp}.csv'

    # Output fieldnames (simplified - enricher writes directly to Salesforce)
    output_fieldnames = [
        'name', 'account_name', 'email', 'title', 'contact_id',
        'salesforce_link', 'enrichment_status', 'error_message', 'enrichment_timestamp'
    ]

    # Open output file and write header
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()

        success_count = 0
        error_count = 0

        for i, contact in enumerate(contacts, 1):
            print(f"[{i}/{len(contacts)}] Processing {contact['name']} ({contact['email']})...")

            result_row = {
                'name': contact['name'],
                'account_name': contact['account_name'],
                'email': contact['email'],
                'title': contact['title'],
                'contact_id': contact.get('contact_id', ''),
                'salesforce_link': '',
                'enrichment_status': 'pending',
                'error_message': '',
                'enrichment_timestamp': ''
            }

            # Get Contact ID
            contact_id = contact.get('contact_id')

            # If no Contact ID found in CSV, try looking up by email
            if not contact_id and contact['email']:
                print(f"   🔍 No Contact ID in CSV, looking up by email...")
                contact_id = lookup_contact_by_email(contact['email'])
                if contact_id:
                    result_row['contact_id'] = contact_id
                    print(f"   ✅ Found Contact ID: {contact_id}")

            # Generate Salesforce Lightning link if we have a Contact ID
            if contact_id:
                # Use the Salesforce domain from environment
                sf_base_url = os.getenv('SALESFORCE_DOMAIN', 'login.salesforce.com')
                if 'https://' not in sf_base_url:
                    sf_base_url = f"https://{sf_base_url}"
                # Try to get the actual instance URL (like du0000000ie4tmaw.lightning.force.com)
                # For now, we'll use a generic format - the user's org will redirect correctly
                result_row['salesforce_link'] = f"https://du0000000ie4tmaw.lightning.force.com/lightning/r/Contact/{contact_id}/view"

            if not contact_id:
                print(f"   ❌ No Contact ID found - skipping")
                result_row['enrichment_status'] = 'error'
                result_row['error_message'] = 'No Contact ID found in CSV or Salesforce'
                error_count += 1
            else:
                # Call enrichment directly
                print(f"   🌐 Running web search enrichment...")
                enrichment_result = await enrich_contact_directly(contact_id, include_linkedin=True)

                if enrichment_result.get('success'):
                    print(f"   ✅ Enrichment successful - data written to Salesforce")
                    result_row['enrichment_status'] = 'success'
                    result_row['enrichment_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    success_count += 1
                else:
                    error_msg = enrichment_result.get('error', 'Unknown error')
                    print(f"   ❌ Enrichment failed: {error_msg}")
                    result_row['enrichment_status'] = 'error'
                    result_row['error_message'] = error_msg
                    error_count += 1

            # Write row immediately
            writer.writerow(result_row)
            outfile.flush()

            print()

    print(f"\n✅ Processing complete!")
    print(f"📄 Results saved to: {output_csv}")
    print(f"\n📊 Summary:")
    print(f"   Total processed: {len(contacts)}")
    print(f"   Successful: {success_count}")
    print(f"   Errors: {error_count}")


async def main_async():
    """Async main function."""
    parser = argparse.ArgumentParser(
        description='Batch enrich contacts via web search enricher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 1 contact
  python batch_enrich_contacts_api.py --test-one

  # Test with 3 contacts
  python batch_enrich_contacts_api.py --test-three

  # Process all contacts
  python batch_enrich_contacts_api.py --all
        """
    )

    parser.add_argument('--test-one', action='store_true',
                       help='Test mode: process 1 contact')
    parser.add_argument('--test-three', action='store_true',
                       help='Test mode: process 3 contacts')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Process all contacts')

    args = parser.parse_args()

    # Read contacts from CSV
    print("📖 Reading contacts from CSV...")
    contacts = read_contacts_from_csv()
    print(f"✅ Found {len(contacts)} contacts in CSV\n")

    # Determine test mode
    if args.test_one:
        await process_contacts(contacts, test_mode=1)
    elif args.test_three:
        await process_contacts(contacts, test_mode=3)
    elif args.all:
        await process_contacts(contacts, test_mode=None)
    else:
        print("Please specify either --test-one, --test-three, or --all mode")
        parser.print_help()


def main():
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
