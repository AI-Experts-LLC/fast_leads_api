#!/usr/bin/env python3
"""
Test script for Bright Data LinkedIn Filter API
Filters LinkedIn profiles by job title and company name using nested AND/OR operators

⏱️  IMPORTANT: Filter processing takes up to 5 minutes!
This script polls the snapshot endpoint every 10 seconds until results are ready.

The filter creates a snapshot with this structure:
- Company name must match (AND operator)
- Title must match one of multiple target titles (OR operator)
- Optional location filtering

Example filter for Baptist Health:
- current_company_name includes "Baptist Health" AND
- position includes ("Director of Facilities" OR "CFO" OR "VP Operations" OR ...)
"""

import os
import requests
import json
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BrightDataLinkedInFilter:
    """
    Simple OOP wrapper for Bright Data LinkedIn Profile API
    Note: The API uses trigger-based collection, not filtering
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the LinkedIn API client

        Args:
            api_token: Bright Data API token (defaults to BRIGHTDATA_API_TOKEN env var)
        """
        self.api_token = api_token or os.getenv('BRIGHTDATA_API_TOKEN')
        if not self.api_token:
            raise ValueError("BRIGHTDATA_API_TOKEN must be set in environment or passed to constructor")

        # Use filter endpoint (no version in path)
        self.base_url = "https://api.brightdata.com/datasets/filter"
        self.dataset_id = "gd_l1viktl72bvl7bjuj0"  # LinkedIn Profiles dataset

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def normalize_company_name(self, company_name: str) -> str:
        """
        Normalize company name by removing generic organizational suffixes
        while KEEPING healthcare identifiers to avoid false matches

        Strategy:
        - KEEP: Medical, Health, Healthcare, Clinic (healthcare identifiers)
        - REMOVE: Hospital, Center, Inc, LLC, Regional, etc. (generic suffixes)

        This prevents matching "Portneuf Bakery" when searching "Portneuf Medical Center"
        by keeping "Medical" but removing "Center"

        Args:
            company_name: Original company name

        Returns:
            Normalized company name with generic suffixes removed
        """
        import re

        # Remove generic organizational suffixes (case-insensitive)
        # Order matters - remove longer phrases first to avoid partial matches
        # IMPORTANT: We intentionally KEEP "Medical", "Health", "Healthcare", "Clinic"
        suffixes_to_remove = [
            # Facility types (but NOT "Medical" or "Clinic" - we keep those!)
            r'\bHospitals?\b',  # Hospital or Hospitals
            r'\bRMC\b',
            r'\bCenter\b',

            # Corporate structures
            r'\bCorporation\b',
            r'\bCorp\.?\b',
            r'\bCompany\b',
            r'\bCo\.?\b',
            r'\bInc\.?\b',
            r'\bLLC\b',
            r'\bL\.L\.C\.?\b',

            # Organizational structures
            r'\bSystems?\b',  # System or Systems
            r'\bNetwork\b',
            r'\bFoundation\b',
            r'\bTrust\b',
            r'\bGroup\b',
            r'\bAssociates\b',
            r'\bPartners\b',

            # Descriptors (but NOT "Health" or "Healthcare" - we keep those!)
            r'\bRegional\b',
            r'\bServices?\b',  # Service or Services
            r'\bCare\b(?!.*\bHealth)',  # Remove "Care" unless part of "Healthcare"

            # Common connectors (if at end)
            r'\band\b$',
            r'\&$'
        ]

        normalized = company_name
        for suffix in suffixes_to_remove:
            normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)

        # Clean up extra whitespace and trailing punctuation
        normalized = ' '.join(normalized.split())
        normalized = normalized.strip(' ,&-')

        return normalized.strip()

    def search_with_parent_account(
        self,
        company_name: str,
        parent_account_name: str = None,
        target_titles: List[str] = None,
        company_city: str = None,
        company_state: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Filter LinkedIn profiles by LOCAL or PARENT company name + titles + location

        This mirrors the three_step_prospect_discovery.py logic:
        - Search for prospects at EITHER the local account OR parent account
        - Filter by job titles (OR logic)
        - Filter by location (city/state)
        - Exclude interns/students
        - Company names are normalized to remove healthcare suffixes

        Args:
            company_name: Local account name (e.g., "St. Patrick Hospital")
            parent_account_name: Parent account name (e.g., "Providence Health & Services")
            target_titles: List of job titles to search for
            company_city: City for location filtering
            company_state: State for location filtering

        Returns:
            API response dictionary or None if request failed
        """
        # Normalize company names before searching
        normalized_company = self.normalize_company_name(company_name)
        normalized_parent = self.normalize_company_name(parent_account_name) if parent_account_name else None

        # Top 20 target titles (Bright Data API limit: max 20 filters per OR group)
        # Prioritized by decision authority: C-Suite → VPs → Directors → Managers → Keywords
        # Based on search.py, improved_prospect_discovery.py, and improved_ai_ranking.py
        if not target_titles:
            target_titles = [
                # C-Suite (Ultimate decision authority - 3 titles)
                "Chief Financial Officer",
                "Chief Operating Officer",
                "CFO",

                # VP Level (High authority - 2 titles)
                "VP Facilities",
                "VP Operations",

                # Director Level (Primary decision-makers - 6 titles)
                "Director of Facilities",
                "Director of Engineering",
                "Director of Maintenance",
                "Director of Operations",
                "Facilities Director",
                "Engineering Director",

                # Manager Level (Operational decision-makers - 4 titles)
                "Facilities Manager",
                "Engineering Manager",
                "Energy Manager",
                "Plant Manager",

                # Broad keyword searches (4 keywords)
                # These will match any position containing these words
                "Sustainability",
                "Energy",
                "Facilities",
                "Maintenance",
            ]

        # Build title filters (OR logic - match any of these titles)
        title_filters = [
            {
                "name": "position",
                "value": title,
                "operator": "includes"
            }
            for title in target_titles
        ]

        # Build company name filters (OR logic - match local OR parent OR location variations)
        # Use BOTH normalized and original names to maximize matches
        company_filters = [
            {
                "name": "current_company_name",
                "value": company_name,
                "operator": "includes"
            },
            {
                "name": "current_company_name",
                "value": normalized_company,
                "operator": "includes"
            }
        ]

        # Add parent account if provided (both normalized and original)
        if parent_account_name and normalized_parent:
            company_filters.append({
                "name": "current_company_name",
                "value": parent_account_name,
                "operator": "includes"
            })
            company_filters.append({
                "name": "current_company_name",
                "value": normalized_parent,
                "operator": "includes"
            })

        # Add location-based company name variations
        # Example: "Mayo Clinic Rochester", "Baptist Health Miami"
        if company_city:
            # Local + City (e.g., "St. Patrick Hospital Missoula")
            company_filters.append({
                "name": "current_company_name",
                "value": f"{company_name} {company_city}",
                "operator": "includes"
            })
            company_filters.append({
                "name": "current_company_name",
                "value": f"{normalized_company} {company_city}",
                "operator": "includes"
            })

            # Parent + City (e.g., "Providence Health Missoula")
            if parent_account_name and normalized_parent:
                company_filters.append({
                    "name": "current_company_name",
                    "value": f"{parent_account_name} {company_city}",
                    "operator": "includes"
                })
                company_filters.append({
                    "name": "current_company_name",
                    "value": f"{normalized_parent} {company_city}",
                    "operator": "includes"
                })

        # Build main filter with AND logic
        main_filters = [
            # Company name filter (local OR parent)
            {
                "operator": "or",
                "filters": company_filters
            },
            # Title filters (OR - match any title)
            {
                "operator": "or",
                "filters": title_filters
            },
            # Exclude interns/students
            {
                "name": "position",
                "value": "intern",
                "operator": "not_includes"
            },
            {
                "name": "position",
                "value": "student",
                "operator": "not_includes"
            },
            # Minimum connections filter (≥20 connections)
            {
                "name": "connections",
                "value": "20",
                "operator": ">="
            }
        ]

        # Add location filter (city only - more flexible)
        if company_city:
            main_filters.append({
                "name": "city",
                "value": company_city,
                "operator": "includes"
            })

        payload = {
            "dataset_id": self.dataset_id,
            "filter": {
                "operator": "and",
                "filters": main_filters
            }
        }

        print(f"\n🔍 Filtering LinkedIn profiles (Local + Parent + Location Variations)...")
        print(f"   Company Names (OR - match any):")

        # Show normalized versions
        print(f"     Original: '{company_name}'")
        if normalized_company != company_name:
            print(f"     Normalized: '{normalized_company}'")

        if parent_account_name:
            print(f"     Parent: '{parent_account_name}'")
            if normalized_parent and normalized_parent != parent_account_name:
                print(f"     Parent Normalized: '{normalized_parent}'")

        if company_city:
            print(f"     With Location: '{company_name} {company_city}'")
            if normalized_company != company_name:
                print(f"     Normalized + Location: '{normalized_company} {company_city}'")

            if parent_account_name:
                print(f"     Parent + Location: '{parent_account_name} {company_city}'")
                if normalized_parent and normalized_parent != parent_account_name:
                    print(f"     Parent Normalized + Location: '{normalized_parent} {company_city}'")

        print(f"\n   Titles (OR): {len(target_titles)} titles")
        for title in target_titles[:3]:
            print(f"     - {title}")
        if len(target_titles) > 3:
            print(f"     ... and {len(target_titles) - 3} more")

        print(f"\n   Quality Filters:")
        print(f"     - Minimum connections: ≥20")
        print(f"     - Exclude: interns, students")

        if company_city:
            print(f"\n   Location Filter: City contains '{company_city}'")
        print(f"\n📤 Request payload:")
        print(json.dumps(payload, indent=2))

        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if response.ok:
                print(f"\n✅ Request succeeded (Status: {response.status_code})")
                result = response.json()
                print(f"\n📥 Response:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"\n❌ Request failed (Status: {response.status_code})")
                print(f"Error: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("\n⏱️  Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request error: {str(e)}")
            return None

    def search_by_title_and_company(
        self,
        company_name: str,
        target_titles: List[str] = None,
        company_city: str = None,
        company_state: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Filter LinkedIn profiles by company name and job titles

        Uses nested AND/OR operators:
        - Company name must match (AND)
        - Title must match one of the target titles (OR)
        - Optional: City/state filtering

        Args:
            company_name: Company name to filter (e.g., "Baptist Health")
            target_titles: List of job titles to search for (uses defaults if not provided)
            company_city: City to filter by (optional)
            company_state: State to filter by (optional)

        Returns:
            API response dictionary or None if request failed
        """
        # Top 20 target titles (Bright Data API limit: max 20 filters per OR group)
        # Prioritized by decision authority: C-Suite → VPs → Directors → Managers
        # Based on search.py, improved_prospect_discovery.py, and improved_ai_ranking.py
        if not target_titles:
            target_titles = [
                # C-Suite (Ultimate decision authority - 3 titles)
                "Chief Financial Officer",
                "Chief Operating Officer",
                "CFO",

                # VP Level (High authority - 3 titles)
                "VP Facilities",
                "VP Operations",
                "Vice President",

                # Director Level (Primary decision-makers - 8 titles)
                "Director of Facilities",
                "Director of Engineering",
                "Director of Maintenance",
                "Director of Operations",
                "Facilities Director",
                "Engineering Director",
                "Operations Director",
                "Director",

                # Manager Level (Operational decision-makers - 6 titles)
                "Facilities Manager",
                "Engineering Manager",
                "Energy Manager",
                "Plant Manager",
                "Operations Manager",
                "Manager"
            ]

        # Build title filters (OR logic - match any of these titles)
        title_filters = [
            {
                "name": "position",
                "value": title,
                "operator": "includes"
            }
            for title in target_titles
        ]

        # Build main filter with AND logic
        main_filters = [
            # Company name filter (required)
            {
                "name": "current_company_name",
                "value": company_name,
                "operator": "includes"
            },
            # Title filters (OR - match any title)
            {
                "operator": "or",
                "filters": title_filters
            }
        ]

        # Add optional location filters
        if company_city:
            main_filters.append({
                "name": "city",
                "value": company_city,
                "operator": "includes"
            })

        if company_state:
            main_filters.append({
                "name": "city",  # Assuming state is in city field, adjust if needed
                "value": company_state,
                "operator": "includes"
            })

        payload = {
            "dataset_id": self.dataset_id,
            "filter": {
                "operator": "and",
                "filters": main_filters
            }
        }

        print(f"\n🔍 Filtering LinkedIn profiles...")
        print(f"   Company: '{company_name}'")
        print(f"   Titles (OR): {len(target_titles)} titles")
        for title in target_titles[:3]:
            print(f"     - {title}")
        if len(target_titles) > 3:
            print(f"     ... and {len(target_titles) - 3} more")
        if company_city:
            print(f"   City: '{company_city}'")
        if company_state:
            print(f"   State: '{company_state}'")
        print(f"\n📤 Request payload:")
        print(json.dumps(payload, indent=2))

        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if response.ok:
                print(f"\n✅ Request succeeded (Status: {response.status_code})")
                result = response.json()
                print(f"\n📥 Response:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"\n❌ Request failed (Status: {response.status_code})")
                print(f"Error: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("\n⏱️  Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request error: {str(e)}")
            return None

    def get_snapshot_results(
        self,
        snapshot_id: str,
        max_wait_time: int = 300,  # 5 minutes max
        poll_interval: int = 10     # Check every 10 seconds
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve results from a snapshot with polling

        The filter API takes up to 5 minutes to process results.
        This method polls the snapshot endpoint until data is ready.

        Args:
            snapshot_id: The snapshot ID returned from filter request
            max_wait_time: Maximum seconds to wait (default: 300 = 5 minutes)
            poll_interval: Seconds between polling attempts (default: 10)

        Returns:
            List of profile results or None if request failed/timeout
        """
        import time

        print(f"\n📥 Fetching snapshot results...")
        print(f"   Snapshot ID: {snapshot_id}")
        print(f"   ⏱️  Filter processing takes up to 5 minutes...")
        print(f"   Polling every {poll_interval} seconds (max {max_wait_time}s)")

        # CORRECT endpoint: /datasets/snapshots/{snapshot_id} (NO v3 in path!)
        snapshot_url = f"https://api.brightdata.com/datasets/snapshots/{snapshot_id}"

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < max_wait_time:
            attempt += 1
            elapsed = int(time.time() - start_time)

            print(f"\n   🔄 Attempt {attempt} (elapsed: {elapsed}s)...")

            try:
                response = requests.get(
                    snapshot_url,
                    headers=self._get_headers(),
                    timeout=30
                )

                if response.ok:
                    snapshot_info = response.json()
                    status = snapshot_info.get('status', snapshot_info.get('Status', 'unknown'))

                    print(f"      Status: {status}")

                    if status == 'ready':
                        print(f"\n✅ Snapshot ready! (Status: {response.status_code})")
                        print(f"📊 Snapshot Info:")
                        print(f"   Dataset Size: {snapshot_info.get('dataset_size', 'N/A')} records")
                        print(f"   File Size: {snapshot_info.get('file_size', 'N/A')} bytes")
                        print(f"   Created: {snapshot_info.get('created', 'N/A')}")

                        # Download the actual data using the snapshot download endpoint
                        print(f"\n📥 Downloading profile data...")
                        download_url = f"https://api.brightdata.com/datasets/snapshots/{snapshot_id}/download?format=json"

                        download_response = requests.get(
                            download_url,
                            headers=self._get_headers(),
                            timeout=60
                        )

                        if download_response.ok:
                            profiles = download_response.json()
                            if isinstance(profiles, list):
                                print(f"✅ Retrieved {len(profiles)} profiles")
                                return profiles
                            else:
                                print(f"📊 Data format:")
                                print(json.dumps(profiles, indent=2)[:500])
                                return profiles
                        else:
                            print(f"❌ Failed to download data: {download_response.status_code}")
                            print(f"   {download_response.text[:200]}")
                            return None
                    elif status in ['scheduled', 'building']:
                        print(f"      ⏳ Still processing (status: {status})...")
                        # Sleep before next poll
                        if time.time() - start_time < max_wait_time:
                            time.sleep(poll_interval)
                            continue
                        else:
                            print(f"\n⏱️  Timeout: Snapshot still {status} after {max_wait_time}s")
                            return None
                    elif status == 'failed':
                        print(f"      ❌ Snapshot failed!")
                        print(json.dumps(snapshot_info, indent=2)[:500])
                        return None
                    else:
                        print(f"      ⚠️  Unknown status: {status}")
                        print(json.dumps(snapshot_info, indent=2)[:500])
                        # Sleep and continue polling in case it's a temporary state
                        if time.time() - start_time < max_wait_time:
                            time.sleep(poll_interval)
                            continue
                        else:
                            return None

                elif response.status_code == 404:
                    # Snapshot not ready yet, keep polling
                    print(f"      ⏳ Still processing (404 - snapshot not found)...")

                    # On first attempt, also check alternative endpoints
                    if attempt == 1:
                        print(f"      📝 Note: 404 may indicate no matching data in dataset")
                        print(f"      📝 Ensure LinkedIn profiles for 'Baptist Health' were collected first")

                    if time.time() - start_time < max_wait_time:
                        time.sleep(poll_interval)
                        continue
                    else:
                        print(f"\n⏱️  Timeout: Snapshot not ready after {max_wait_time}s")
                        return None
                else:
                    # Other error - stop polling
                    print(f"\n❌ Error (Status: {response.status_code}): {response.text}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"      ❌ Request error: {str(e)}")
                if time.time() - start_time < max_wait_time:
                    time.sleep(poll_interval)
                    continue
                else:
                    return None

        print(f"\n⏱️  Timeout: Maximum wait time ({max_wait_time}s) reached")
        return None

    def search_profiles(
        self,
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generic search with custom filters

        Args:
            filters: Dictionary of filter conditions

        Returns:
            API response dictionary or None if request failed
        """
        payload = {
            "dataset_id": self.dataset_id,
            "filter": filters
        }

        print(f"\n🔍 Searching with custom filters...")
        print(f"📤 Request payload:")
        print(json.dumps(payload, indent=2))

        try:
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if response.ok:
                print(f"\n✅ Request succeeded (Status: {response.status_code})")
                result = response.json()
                print(f"\n📥 Response:")
                print(json.dumps(result, indent=2))
                return result
            else:
                print(f"\n❌ Request failed (Status: {response.status_code})")
                print(f"Error: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request error: {str(e)}")
            return None


def main():
    """
    Test the Bright Data LinkedIn Filter API

    Test Case 1: Known working filter (HCA Healthcare in Tampa)
    Test Case 2: Baptist Health with all target titles
    """
    print("=" * 80)
    print("Bright Data LinkedIn Profile Filter API - Test Script")
    print("=" * 80)
    print("\nℹ️  NOTE: This API filters existing collected data in the dataset.")
    print("   Ensure you have data collected before filtering.\n")

    try:
        # Initialize the client
        client = BrightDataLinkedInFilter()

        # Test Case 1: Known working filter - HCA Healthcare in Tampa
        print("=" * 80)
        print("TEST CASE 1: HCA Healthcare in Tampa (Known Working Example)")
        print("=" * 80)

        # Use custom filter for HCA Healthcare
        hca_filter_result = client.search_profiles({
            "operator": "and",
            "filters": [
                {"name": "current_company_name", "value": "HCA Healthcare", "operator": "includes"},
                {
                    "operator": "or",
                    "filters": [
                        {"name": "position", "value": "finance", "operator": "includes"},
                        {"name": "position", "value": "director", "operator": "includes"}
                    ]
                },
                {"name": "city", "value": "Tampa", "operator": "includes"},
                {"name": "position", "value": "medicine", "operator": "not_includes"},
                {"name": "position", "value": "Laboratory", "operator": "not_includes"},
                {"name": "position", "value": "patient", "operator": "not_includes"}
            ]
        })

        if hca_filter_result and isinstance(hca_filter_result, dict):
            snapshot_id = hca_filter_result.get("snapshot_id")

            if snapshot_id:
                print(f"\n✅ Filter created successfully!")
                print(f"   Snapshot ID: {snapshot_id}")

                # Fetch the actual results from the snapshot
                print("\n" + "=" * 80)
                print("Fetching HCA Healthcare snapshot results...")
                print("=" * 80)

                profiles = client.get_snapshot_results(snapshot_id, max_wait_time=120, poll_interval=10)

                if profiles and isinstance(profiles, list):
                    print(f"\n✅ Retrieved {len(profiles)} profiles")

                    # Display sample profiles
                    for i, profile in enumerate(profiles[:3], 1):
                        print(f"\n📋 Profile {i}:")
                        print(f"   Name: {profile.get('name', 'N/A')}")
                        print(f"   Position: {profile.get('position', 'N/A')}")
                        print(f"   Company: {profile.get('current_company_name', 'N/A')}")
                        print(f"   Location: {profile.get('city', 'N/A')}, {profile.get('country_code', 'N/A')}")
                        print(f"   LinkedIn: {profile.get('url', 'N/A')}")

                    if len(profiles) > 3:
                        print(f"\n   ... and {len(profiles) - 3} more profiles")
                elif profiles:
                    print(f"\n📊 Snapshot response:")
                    print(json.dumps(profiles, indent=2)[:500])

        # Test Case 2: Baptist Health
        print("\n\n" + "=" * 80)
        print("TEST CASE 2: Baptist Health - All Target Titles")
        print("=" * 80)
        filter_result = client.search_by_title_and_company(
            company_name="Baptist Health"
        )

        if filter_result and isinstance(filter_result, dict):
            snapshot_id = filter_result.get("snapshot_id")

            if snapshot_id:
                print(f"\n✅ Filter created successfully!")
                print(f"   Snapshot ID: {snapshot_id}")

                # Fetch the actual results from the snapshot
                print("\n" + "=" * 80)
                print("Fetching snapshot results...")
                print("=" * 80)

                profiles = client.get_snapshot_results(snapshot_id)

                if profiles and isinstance(profiles, list):
                    print(f"\n✅ Retrieved {len(profiles)} profiles")

                    # Display sample profiles
                    for i, profile in enumerate(profiles[:3], 1):
                        print(f"\n📋 Profile {i}:")
                        print(f"   Name: {profile.get('name', 'N/A')}")
                        print(f"   Position: {profile.get('position', 'N/A')}")
                        print(f"   Company: {profile.get('current_company_name', 'N/A')}")
                        print(f"   Location: {profile.get('city', 'N/A')}, {profile.get('country_code', 'N/A')}")
                        print(f"   LinkedIn: {profile.get('url', 'N/A')}")

                    if len(profiles) > 3:
                        print(f"\n   ... and {len(profiles) - 3} more profiles")
                elif profiles:
                    print(f"\n📊 Snapshot response:")
                    print(json.dumps(profiles, indent=2)[:500])

        print("\n" + "=" * 80)
        print("✅ Test completed!")
        print("=" * 80)

    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease ensure BRIGHTDATA_API_TOKEN is set in your .env file:")
        print("  BRIGHTDATA_API_TOKEN=your_token_here")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    print("\nℹ️  If you get 'ImportError: No module named requests', install it:")
    print("   pip install requests python-dotenv\n")
    main()
