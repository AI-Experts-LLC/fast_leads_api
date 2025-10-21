#!/usr/bin/env python3
"""
Simple Email Validation Script using ZeroBounce API

Validates bounced emails from the mailings CSV to check if they're actually valid.
Usage:
    python validate_emails_zerobounce.py --test    # Test with 1-2 emails
    python validate_emails_zerobounce.py --all     # Validate all bounced emails
"""

import os
import csv
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ZeroBounce API configuration
ZEROBOUNCE_API_KEY = os.getenv('ZEROBOUNCE_API_KEY')
ZEROBOUNCE_API_URL = 'https://api.zerobounce.net/v2/validate'

# Input CSV file
INPUT_CSV = 'tests/Mailings_2025-10-07 (1).csv'


def validate_email(email, ip_address=''):
    """
    Validate a single email using ZeroBounce API.

    Args:
        email: Email address to validate
        ip_address: Optional IP address for additional validation

    Returns:
        Dictionary with validation results or None if error
    """
    if not ZEROBOUNCE_API_KEY:
        print("❌ Error: ZEROBOUNCE_API_KEY not found in environment variables")
        return None

    params = {
        'api_key': ZEROBOUNCE_API_KEY,
        'email': email,
        'ip_address': ip_address
    }

    try:
        response = requests.get(ZEROBOUNCE_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {str(e)}")
        return None


def read_bounced_emails():
    """
    Read bounced emails from the CSV file.

    Returns:
        List of dictionaries with email data
    """
    bounced_emails = []

    with open(INPUT_CSV, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Only include rows where there's a bounce
            if row.get('Bounced At'):
                bounced_emails.append({
                    'email': row.get('Prospect Email'),
                    'first_name': row.get('Prospect First Name'),
                    'last_name': row.get('Prospect Last Name'),
                    'company': row.get('Prospect Account Name'),
                    'bounce_category': row.get('Bounce Category'),
                    'bounced_at': row.get('Bounced At')
                })

    return bounced_emails


def print_validation_result(email_data, result):
    """
    Print validation result in a readable format.

    Args:
        email_data: Dictionary with email metadata
        result: ZeroBounce API response
    """
    print("\n" + "="*80)
    print(f"Email: {email_data['email']}")
    print(f"Name: {email_data['first_name']} {email_data['last_name']}")
    print(f"Company: {email_data['company']}")
    print(f"Original Bounce Category: {email_data['bounce_category']}")
    print("-"*80)

    if result:
        status = result.get('status', 'unknown')
        sub_status = result.get('sub_status', 'N/A')

        # Status emoji mapping
        status_emoji = {
            'valid': '✅',
            'invalid': '❌',
            'catch-all': '⚠️',
            'unknown': '❓',
            'spamtrap': '🚫',
            'abuse': '🚫',
            'do_not_mail': '🚫'
        }

        emoji = status_emoji.get(status, '❓')

        print(f"ZeroBounce Status: {emoji} {status.upper()}")
        print(f"Sub-Status: {sub_status}")

        if result.get('free_email'):
            print(f"Free Email: Yes (e.g., Gmail, Yahoo)")

        if result.get('did_you_mean'):
            print(f"💡 Suggestion: {result['did_you_mean']}")

        if result.get('mx_found'):
            print(f"MX Record: Found ✓")
        else:
            print(f"MX Record: Not Found ✗")

        if result.get('smtp_provider'):
            print(f"SMTP Provider: {result['smtp_provider']}")
    else:
        print("❌ Validation failed")

    print("="*80)


def test_mode():
    """
    Test mode: validate first 2 bounced emails.
    """
    print("\n🧪 TEST MODE: Validating first 2 bounced emails\n")

    bounced_emails = read_bounced_emails()

    if not bounced_emails:
        print("❌ No bounced emails found in CSV")
        return

    print(f"📊 Total bounced emails in CSV: {len(bounced_emails)}")
    print(f"🔍 Testing first 2 emails...\n")

    test_emails = bounced_emails[:2]

    for i, email_data in enumerate(test_emails, 1):
        print(f"\n[{i}/2] Validating {email_data['email']}...")
        result = validate_email(email_data['email'])
        print_validation_result(email_data, result)

    print("\n✅ Test complete!")
    print(f"\n💡 To validate all {len(bounced_emails)} bounced emails, run:")
    print("   python validate_emails_zerobounce.py --all")


def validate_limited(limit):
    """
    Validate limited number of bounced emails.

    Args:
        limit: Number of emails to validate
    """
    print(f"\n📧 LIMITED VALIDATION MODE: Validating first {limit} bounced emails\n")

    bounced_emails = read_bounced_emails()

    if not bounced_emails:
        print("❌ No bounced emails found in CSV")
        return

    # Limit the number of emails
    bounced_emails = bounced_emails[:limit]
    print(f"📊 Validating {len(bounced_emails)} emails...\n")

    # Prepare output CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv = f'tests/email_validation_results_{timestamp}.csv'

    results = []

    for i, email_data in enumerate(bounced_emails, 1):
        print(f"[{i}/{len(bounced_emails)}] Validating {email_data['email']}...")

        result = validate_email(email_data['email'])

        if result:
            validation_result = {
                'email': email_data['email'],
                'first_name': email_data['first_name'],
                'last_name': email_data['last_name'],
                'company': email_data['company'],
                'original_bounce_category': email_data['bounce_category'],
                'zerobounce_status': result.get('status', 'unknown'),
                'zerobounce_sub_status': result.get('sub_status', 'N/A'),
                'free_email': result.get('free_email', False),
                'did_you_mean': result.get('did_you_mean', ''),
                'mx_found': result.get('mx_found', False),
                'smtp_provider': result.get('smtp_provider', ''),
                'bounced_at': email_data['bounced_at']
            }
            results.append(validation_result)

            # Print brief status
            status_emoji = {
                'valid': '✅',
                'invalid': '❌',
                'catch-all': '⚠️',
                'unknown': '❓',
                'spamtrap': '🚫',
                'abuse': '🚫',
                'do_not_mail': '🚫'
            }
            emoji = status_emoji.get(result.get('status'), '❓')
            print(f"   {emoji} {result.get('status', 'unknown').upper()}")
        else:
            print("   ❌ Validation failed")

    # Save results to CSV
    if results:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'email', 'first_name', 'last_name', 'company',
                'original_bounce_category', 'zerobounce_status', 'zerobounce_sub_status',
                'free_email', 'did_you_mean', 'mx_found', 'smtp_provider', 'bounced_at'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ Validation complete!")
        print(f"📄 Results saved to: {output_csv}")

        # Print summary
        status_counts = {}
        for result in results:
            status = result['zerobounce_status']
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n📊 Summary:")
        print(f"   Total validated: {len(results)}")
        for status, count in sorted(status_counts.items()):
            print(f"   {status}: {count}")
    else:
        print("\n❌ No results to save")


def validate_all():
    """
    Validate all bounced emails and save results to CSV with all original columns plus validation results.
    """
    print("\n📧 FULL VALIDATION MODE: Validating all bounced emails\n")

    # Read the original CSV to preserve all columns
    original_rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        original_fieldnames = reader.fieldnames

        for row in reader:
            # Only process bounced emails
            if row.get('Bounced At'):
                original_rows.append(row)

    if not original_rows:
        print("❌ No bounced emails found in CSV")
        return

    print(f"📊 Total bounced emails to validate: {len(original_rows)}\n")

    # Prepare output CSV with original columns + new validation columns
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv = f'tests/email_validation_results_full_{timestamp}.csv'

    # New columns to add
    new_columns = [
        'ZeroBounce_Status',
        'ZeroBounce_Sub_Status',
        'ZeroBounce_Free_Email',
        'ZeroBounce_Did_You_Mean',
        'ZeroBounce_MX_Found',
        'ZeroBounce_SMTP_Provider'
    ]

    output_fieldnames = list(original_fieldnames) + new_columns

    # Open output file and write header
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()

        status_counts = {}

        for i, row in enumerate(original_rows, 1):
            email = row.get('Prospect Email')
            print(f"[{i}/{len(original_rows)}] Validating {email}...")

            # Validate the email
            result = validate_email(email)

            # Add validation results to the row
            if result:
                row['ZeroBounce_Status'] = result.get('status', 'unknown')
                row['ZeroBounce_Sub_Status'] = result.get('sub_status', '')
                row['ZeroBounce_Free_Email'] = 'Yes' if result.get('free_email') else 'No'
                row['ZeroBounce_Did_You_Mean'] = result.get('did_you_mean', '')
                row['ZeroBounce_MX_Found'] = 'Yes' if result.get('mx_found') else 'No'
                row['ZeroBounce_SMTP_Provider'] = result.get('smtp_provider', '')

                status = result.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

                # Print brief status
                status_emoji = {
                    'valid': '✅',
                    'invalid': '❌',
                    'catch-all': '⚠️',
                    'unknown': '❓',
                    'spamtrap': '🚫',
                    'abuse': '🚫',
                    'do_not_mail': '🚫'
                }
                emoji = status_emoji.get(status, '❓')
                print(f"   {emoji} {status.upper()}")
            else:
                # Validation failed
                row['ZeroBounce_Status'] = 'API_ERROR'
                row['ZeroBounce_Sub_Status'] = ''
                row['ZeroBounce_Free_Email'] = ''
                row['ZeroBounce_Did_You_Mean'] = ''
                row['ZeroBounce_MX_Found'] = ''
                row['ZeroBounce_SMTP_Provider'] = ''
                print("   ❌ Validation failed")

            # Write row immediately
            writer.writerow(row)
            outfile.flush()

    print(f"\n✅ Validation complete!")
    print(f"📄 Results saved to: {output_csv}")

    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total validated: {len(original_rows)}")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Validate bounced emails using ZeroBounce API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with first 2 emails
  python validate_emails_zerobounce.py --test

  # Validate all bounced emails
  python validate_emails_zerobounce.py --all
        """
    )

    parser.add_argument('--test', '-t', action='store_true',
                       help='Test mode: validate first 2 emails')
    parser.add_argument('--limit', '-l', type=int,
                       help='Validate first N emails (e.g., --limit 10)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Validate all bounced emails')

    args = parser.parse_args()

    # Check for API key
    if not ZEROBOUNCE_API_KEY:
        print("❌ Error: ZEROBOUNCE_API_KEY not found in .env file")
        print("Please add: ZEROBOUNCE_API_KEY=your_api_key_here")
        return

    if args.test:
        test_mode()
    elif args.limit:
        validate_limited(args.limit)
    elif args.all:
        validate_all()
    else:
        print("Please specify either --test, --limit N, or --all mode")
        parser.print_help()


if __name__ == "__main__":
    main()
