#!/usr/bin/env python3
"""
Test script for Salesforce Enrichment API

Usage:
    python test_enrichment_api.py --account 001VR00000UhY3oYAF
    python test_enrichment_api.py --contact 003VR00000YLIzRYAX --linkedin
    python test_enrichment_api.py --account 001VR00000UhY3oYAF --financial
    python test_enrichment_api.py --account 001VR00000UhY3oYAF --credit-only  # EDFx only
    
    # With custom API key
    python test_enrichment_api.py --account 001VR00000UhY3oYAF --api-key your-key
    
    # Or set environment variable
    export API_KEY=your-api-key
    python test_enrichment_api.py --account 001VR00000UhY3oYAF
"""

import requests
import argparse
import json
import sys
import os
from datetime import datetime


# API Base URL
API_BASE_URL = "https://fast-leads-api.up.railway.app"
# API_BASE_URL = "http://localhost:8000"  # Uncomment for local testing

# Get API key from environment or use default for dev
DEFAULT_API_KEY = os.getenv("API_KEY") or os.getenv("METRUS_API_KEY")


def test_account_enrichment(account_id: str, api_key: str, overwrite: bool = False, include_financial: bool = False, credit_only: bool = False):
    """Test account enrichment endpoint"""
    print(f"\n{'='*80}")
    print(f"Testing Account Enrichment")
    print(f"{'='*80}")
    print(f"Account ID: {account_id}")
    print(f"Overwrite: {overwrite}")
    print(f"Include Financial: {include_financial}")
    print(f"Credit Only (EDFx): {credit_only}")
    print(f"{'='*80}\n")
    
    url = f"{API_BASE_URL}/enrich/account"
    payload = {
        "account_id": account_id,
        "overwrite": overwrite,
        "include_financial": include_financial,
        "credit_only": credit_only
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    print(f"📡 Sending request to: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}\n")
    
    try:
        start_time = datetime.now()
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️  Request completed in {duration:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\n📄 Response:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"\n❌ ERROR!")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ Request timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_contact_enrichment(contact_id: str, api_key: str, overwrite: bool = False, include_linkedin: bool = False):
    """Test contact enrichment endpoint"""
    print(f"\n{'='*80}")
    print(f"Testing Contact Enrichment")
    print(f"{'='*80}")
    print(f"Contact ID: {contact_id}")
    print(f"Overwrite: {overwrite}")
    print(f"Include LinkedIn: {include_linkedin}")
    print(f"{'='*80}\n")
    
    url = f"{API_BASE_URL}/enrich/contact"
    payload = {
        "contact_id": contact_id,
        "overwrite": overwrite,
        "include_linkedin": include_linkedin
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    print(f"📡 Sending request to: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}\n")
    
    try:
        start_time = datetime.now()
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️  Request completed in {duration:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\n📄 Response:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"\n❌ ERROR!")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ Request timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_health_check():
    """Test API health"""
    print(f"\n{'='*80}")
    print(f"Testing API Health")
    print(f"{'='*80}\n")
    
    url = f"{API_BASE_URL}/health"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy!")
            print(f"📄 Response:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test Salesforce Enrichment API')
    parser.add_argument('--account', help='Salesforce Account ID to enrich')
    parser.add_argument('--contact', help='Salesforce Contact ID to enrich')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing data')
    parser.add_argument('--financial', action='store_true', help='Include financial analysis (accounts only)')
    parser.add_argument('--credit-only', action='store_true', help='Run ONLY EDFx credit enrichment, skip AI (accounts only)')
    parser.add_argument('--linkedin', action='store_true', help='Include LinkedIn enrichment (contacts only)')
    parser.add_argument('--health', action='store_true', help='Just check API health')
    parser.add_argument('--api-key', help='API key for authentication (or set API_KEY environment variable)')
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or DEFAULT_API_KEY
    
    if not api_key and (args.account or args.contact):
        print("\n❌ Error: API key required for enrichment endpoints")
        print("   Set API_KEY environment variable or use --api-key argument")
        print("   Example: export API_KEY=your-api-key")
        print("   Or: python test_enrichment_api.py --account ID --api-key your-key")
        sys.exit(1)
    
    # Check if any test was requested
    if not any([args.account, args.contact, args.health]):
        parser.print_help()
        print("\n❌ Error: You must specify at least one test option")
        sys.exit(1)
    
    success = True
    
    # Health check
    if args.health:
        success = test_health_check() and success
    
    # Account enrichment
    if args.account:
        success = test_account_enrichment(
            account_id=args.account,
            api_key=api_key,
            overwrite=args.overwrite,
            include_financial=args.financial,
            credit_only=args.credit_only
        ) and success
    
    # Contact enrichment
    if args.contact:
        success = test_contact_enrichment(
            contact_id=args.contact,
            api_key=api_key,
            overwrite=args.overwrite,
            include_linkedin=args.linkedin
        ) and success
    
    # Final summary
    print(f"\n{'='*80}")
    if success:
        print(f"✅ All tests passed!")
    else:
        print(f"❌ Some tests failed")
    print(f"{'='*80}\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

