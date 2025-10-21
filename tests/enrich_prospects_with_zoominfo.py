#!/usr/bin/env python3
"""
Enrich Prospect CSV with ZoomInfo Data

Takes a CSV file of prospects and enriches each row with ZoomInfo contact information.
Updates the output CSV line-by-line as data is gathered.

Usage:
    python enrich_prospects_with_zoominfo.py input.csv [--test-mode] [--limit N]
"""

import os
import sys
import csv
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Import the ZoomInfo client from the existing enricher
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'enrichers'))
try:
    from zoominfo_contact_enricher import ZoomInfoAPIClient
except ImportError:
    # Try alternative import path
    sys.path.insert(0, os.path.dirname(__file__))
    from app.enrichers.zoominfo_contact_enricher import ZoomInfoAPIClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProspectZoomInfoEnricher:
    """Enrich prospect CSV data with ZoomInfo information."""

    # Additional fields we'll add from ZoomInfo
    ZOOMINFO_FIELDS = [
        'ZoomInfo_Email',
        'ZoomInfo_Direct_Phone',
        'ZoomInfo_Mobile_Phone',
        'ZoomInfo_Education',
        'ZoomInfo_Location',
        'ZoomInfo_City',
        'ZoomInfo_State',
        'ZoomInfo_Management_Level',
        'ZoomInfo_Department',
        'ZoomInfo_Company_Size',
        'ZoomInfo_Company_Revenue',
        'ZoomInfo_LinkedIn_Profile',
        'ZoomInfo_Contact_ID',
        'ZoomInfo_Status'
    ]

    def __init__(self):
        """Initialize with ZoomInfo client."""
        load_dotenv()

        try:
            self.zoominfo_client = ZoomInfoAPIClient()
            logger.info("✅ ZoomInfo client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ZoomInfo client: {str(e)}")
            logger.info("📋 Please authenticate with ZoomInfo first to generate bearer token")
            raise

    def parse_name_from_title(self, search_title: str) -> tuple:
        """
        Extract first and last name from search title.

        Example: "John Smith - CFO at Hospital" -> ("John", "Smith")
        """
        try:
            # Split by common separators
            parts = search_title.split(' - ')
            if len(parts) > 0:
                name_part = parts[0].strip()

                # Remove common suffixes like Jr., Sr., III, etc.
                name_part = name_part.replace(', Jr.', '').replace(', Sr.', '')
                name_part = name_part.replace(' Jr.', '').replace(' Sr.', '')
                name_part = name_part.replace(' III', '').replace(' II', '')

                # Split into first and last name
                name_words = name_part.split()
                if len(name_words) >= 2:
                    first_name = name_words[0]
                    last_name = name_words[-1]
                    return (first_name, last_name)
                elif len(name_words) == 1:
                    return (name_words[0], '')

            return ('', '')

        except Exception as e:
            logger.warning(f"⚠️ Error parsing name from '{search_title}': {str(e)}")
            return ('', '')

    def extract_company_from_title(self, search_title: str) -> str:
        """
        Extract company name from search title.

        Example: "John Smith - CFO at Acme Hospital" -> "Acme Hospital"
        """
        try:
            # Look for " at " pattern
            if ' at ' in search_title:
                parts = search_title.split(' at ')
                if len(parts) > 1:
                    company = parts[-1].strip()
                    # Clean up common trailing text
                    company = company.split(' |')[0]  # Remove pipe separators
                    company = company.split(' -')[0]  # Remove dashes
                    return company.strip()
            return ''
        except Exception as e:
            logger.warning(f"⚠️ Error extracting company: {str(e)}")
            return ''

    def search_and_enrich_prospect(self, row: Dict[str, str]) -> Dict[str, str]:
        """
        Search ZoomInfo and enrich a single prospect row.

        Args:
            row: Dictionary containing prospect data from CSV

        Returns:
            Dictionary with original data plus ZoomInfo fields
        """
        enriched_row = row.copy()

        # Initialize all ZoomInfo fields as empty
        for field in self.ZOOMINFO_FIELDS:
            enriched_row[field] = ''

        try:
            # Extract name from search title
            search_title = row.get('Search Title', '')
            first_name, last_name = self.parse_name_from_title(search_title)

            if not first_name or not last_name:
                logger.warning(f"⚠️ Could not parse name from: {search_title}")
                enriched_row['ZoomInfo_Status'] = 'Name parsing failed'
                return enriched_row

            # Use the hospital name as company name
            company_name = row.get('Hospital', '')

            # Also try to extract company from search title as fallback
            if not company_name:
                company_name = self.extract_company_from_title(search_title)

            logger.info(f"🔍 Searching ZoomInfo for: {first_name} {last_name} at {company_name}")

            # Search ZoomInfo
            search_result = self.zoominfo_client.search_contact(
                first_name=first_name,
                last_name=last_name,
                company_name=company_name
            )

            if not search_result or not search_result.get('data'):
                logger.info(f"   ℹ️ No results found, trying without company...")
                # Try without company name
                search_result = self.zoominfo_client.search_contact(
                    first_name=first_name,
                    last_name=last_name
                )

            if search_result and search_result.get('data'):
                contacts = search_result['data']
                logger.info(f"   ✅ Found {len(contacts)} matches")

                # Use the first (best) match
                contact = contacts[0]
                contact_id = contact.get('id')

                if contact_id:
                    enriched_row['ZoomInfo_Contact_ID'] = str(contact_id)

                    # Try to get enriched data
                    logger.info(f"   📊 Enriching contact ID: {contact_id}")
                    enrich_result = self.zoominfo_client.enrich_contact(str(contact_id))

                    if enrich_result and enrich_result.get('data'):
                        enriched_data = enrich_result['data'][0] if enrich_result['data'] else {}
                    else:
                        # Fall back to search result
                        enriched_data = contact

                    # Extract attributes
                    attributes = enriched_data.get('attributes', {})
                    company = attributes.get('company', {})

                    # Populate ZoomInfo fields
                    if attributes.get('email'):
                        enriched_row['ZoomInfo_Email'] = attributes['email']
                        logger.info(f"   📧 Email: {attributes['email']}")

                    if attributes.get('directPhone'):
                        enriched_row['ZoomInfo_Direct_Phone'] = attributes['directPhone']
                        logger.info(f"   📞 Direct: {attributes['directPhone']}")

                    if attributes.get('mobilePhone'):
                        enriched_row['ZoomInfo_Mobile_Phone'] = attributes['mobilePhone']
                        logger.info(f"   📱 Mobile: {attributes['mobilePhone']}")

                    # Education
                    if attributes.get('education'):
                        education_data = attributes['education']
                        if isinstance(education_data, list):
                            education_items = []
                            for edu_item in education_data:
                                if isinstance(edu_item, dict):
                                    school = edu_item.get('school', '')
                                    degree_info = edu_item.get('educationDegree', {})
                                    degree = degree_info.get('degree', '') if isinstance(degree_info, dict) else ''

                                    if degree and school:
                                        education_items.append(f"{degree} - {school}")
                                    elif school:
                                        education_items.append(school)

                            if education_items:
                                enriched_row['ZoomInfo_Education'] = ' | '.join(education_items)
                                logger.info(f"   🎓 Education: {len(education_items)} institutions")

                    # Location
                    location_parts = []
                    if attributes.get('city'):
                        enriched_row['ZoomInfo_City'] = attributes['city']
                        location_parts.append(attributes['city'])

                    if attributes.get('state'):
                        enriched_row['ZoomInfo_State'] = attributes['state']
                        location_parts.append(attributes['state'])

                    if location_parts:
                        enriched_row['ZoomInfo_Location'] = ', '.join(location_parts)
                        logger.info(f"   📍 Location: {', '.join(location_parts)}")

                    # Management level
                    if attributes.get('managementLevel'):
                        mgmt = attributes['managementLevel']
                        if isinstance(mgmt, list):
                            enriched_row['ZoomInfo_Management_Level'] = ', '.join(mgmt)
                        else:
                            enriched_row['ZoomInfo_Management_Level'] = str(mgmt)
                        logger.info(f"   👔 Management: {enriched_row['ZoomInfo_Management_Level']}")

                    # Department
                    if attributes.get('department'):
                        enriched_row['ZoomInfo_Department'] = attributes['department']
                        logger.info(f"   🏢 Department: {attributes['department']}")

                    # Company info
                    if company.get('employeeCount'):
                        enriched_row['ZoomInfo_Company_Size'] = str(company['employeeCount'])
                        logger.info(f"   👥 Company Size: {company['employeeCount']}")

                    if company.get('revenue'):
                        enriched_row['ZoomInfo_Company_Revenue'] = str(company['revenue'])
                        logger.info(f"   💰 Revenue: {company['revenue']}")

                    # LinkedIn (check multiple possible fields)
                    linkedin_url = None
                    if attributes.get('linkedInProfile'):
                        linkedin_url = attributes['linkedInProfile']
                    elif attributes.get('socialMediaUrls'):
                        for social in attributes['socialMediaUrls']:
                            if isinstance(social, dict) and social.get('type') == 'LINKED_IN':
                                linkedin_url = social.get('url')
                                break

                    if linkedin_url:
                        enriched_row['ZoomInfo_LinkedIn_Profile'] = linkedin_url
                        logger.info(f"   🔗 LinkedIn: {linkedin_url}")

                    enriched_row['ZoomInfo_Status'] = 'Success'
                    logger.info(f"   ✅ Enrichment complete")

                else:
                    enriched_row['ZoomInfo_Status'] = 'No contact ID'
                    logger.warning(f"   ⚠️ No contact ID in result")

            else:
                enriched_row['ZoomInfo_Status'] = 'Not found'
                logger.info(f"   ℹ️ No match found in ZoomInfo")

        except Exception as e:
            error_msg = str(e)
            enriched_row['ZoomInfo_Status'] = f'Error: {error_msg[:50]}'
            logger.error(f"   ❌ Error enriching prospect: {error_msg}")

        return enriched_row

    def enrich_csv_file(self, input_csv: str, output_csv: str, test_mode: bool = False, limit: int = None):
        """
        Enrich all prospects in CSV file.

        Args:
            input_csv: Path to input CSV file
            output_csv: Path to output CSV file
            test_mode: If True, only process first 3 rows
            limit: Maximum number of rows to process (None = all)
        """
        logger.info(f"{'='*80}")
        logger.info(f"ZoomInfo Prospect Enrichment")
        logger.info(f"{'='*80}")
        logger.info(f"Input:  {input_csv}")
        logger.info(f"Output: {output_csv}")

        if test_mode:
            logger.info(f"🧪 TEST MODE: Processing first 3 rows only")
            limit = 3
        elif limit:
            logger.info(f"📊 Processing limit: {limit} rows")

        # Read input CSV
        with open(input_csv, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            input_fieldnames = reader.fieldnames

            # Add ZoomInfo fields to output
            output_fieldnames = list(input_fieldnames) + self.ZOOMINFO_FIELDS

            # Create output CSV and write header
            with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
                writer.writeheader()
                outfile.flush()

                # Process each row
                row_count = 0
                enriched_count = 0
                failed_count = 0

                for row in reader:
                    row_count += 1

                    # Check limit
                    if limit and row_count > limit:
                        logger.info(f"📊 Reached limit of {limit} rows")
                        break

                    logger.info(f"\n{'='*80}")
                    logger.info(f"[{row_count}] Processing: {row.get('Search Title', 'Unknown')}")
                    logger.info(f"{'='*80}")

                    # Enrich the prospect
                    enriched_row = self.search_and_enrich_prospect(row)

                    # Track status
                    status = enriched_row.get('ZoomInfo_Status', '')
                    if status == 'Success':
                        enriched_count += 1
                    else:
                        failed_count += 1

                    # Write to output CSV immediately (line-by-line)
                    writer.writerow(enriched_row)
                    outfile.flush()

                    logger.info(f"✅ Row {row_count} written to output")

                    # Brief delay to avoid rate limiting
                    import time
                    time.sleep(1)

        # Summary
        logger.info(f"\n{'='*80}")
        logger.info(f"ENRICHMENT COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Total rows processed: {row_count}")
        logger.info(f"  ✅ Successfully enriched: {enriched_count}")
        logger.info(f"  ❌ Failed/Not found: {failed_count}")
        logger.info(f"  📊 Success rate: {(enriched_count/row_count*100):.1f}%")
        logger.info(f"\n✅ Output saved to: {output_csv}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Enrich prospect CSV with ZoomInfo data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (first 3 rows only)
  python enrich_prospects_with_zoominfo.py prospects.csv --test-mode

  # Process first 10 rows
  python enrich_prospects_with_zoominfo.py prospects.csv --limit 10

  # Process entire file
  python enrich_prospects_with_zoominfo.py prospects.csv
        """
    )

    parser.add_argument('input_csv', help='Input CSV file with prospects')
    parser.add_argument('--output', '-o', help='Output CSV file (default: input_enriched.csv)')
    parser.add_argument('--test-mode', '-t', action='store_true',
                       help='Test mode: only process first 3 rows')
    parser.add_argument('--limit', '-l', type=int,
                       help='Maximum number of rows to process')

    args = parser.parse_args()

    # Determine output filename
    if args.output:
        output_csv = args.output
    else:
        base_name = args.input_csv.rsplit('.', 1)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_csv = f"{base_name}_enriched_{timestamp}.csv"

    try:
        enricher = ProspectZoomInfoEnricher()
        enricher.enrich_csv_file(
            args.input_csv,
            output_csv,
            test_mode=args.test_mode,
            limit=args.limit
        )

        print(f"\n✅ Enrichment completed successfully!")
        print(f"📄 Output file: {output_csv}")

    except Exception as e:
        logger.error(f"❌ Enrichment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
