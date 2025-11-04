"""
Bright Data Prospect Discovery Service
Uses Bright Data LinkedIn Filter API as the starting point for prospect discovery

This replaces the Google Search (Serper) approach with direct LinkedIn dataset filtering.
Follows the same 3-step pattern but with Bright Data as Step 1.

Step 1: Bright Data Filter - Filter LinkedIn dataset by company + titles + location
Step 2: Scrape - Get full LinkedIn data for filtered prospects
Step 3: Rank - AI ranking and final selection
"""

import logging
import os
import requests
import time
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from .linkedin import linkedin_service
from .three_step_prospect_discovery import ThreeStepProspectDiscoveryService
from .ai_company_normalization import ai_company_normalization_service

load_dotenv()
logger = logging.getLogger(__name__)


class BrightDataProspectDiscoveryService:
    """3-step prospect discovery using Bright Data LinkedIn Filter as the starting point"""

    def __init__(self, api_token: Optional[str] = None, raise_on_missing_token: bool = True):
        """
        Initialize the Bright Data prospect discovery service

        Args:
            api_token: Bright Data API token (defaults to BRIGHTDATA_API_TOKEN env var)
            raise_on_missing_token: Whether to raise error if token is missing (default True)
        """
        self.api_token = api_token or os.getenv('BRIGHTDATA_API_TOKEN')
        if not self.api_token and raise_on_missing_token:
            raise ValueError("BRIGHTDATA_API_TOKEN must be set in environment or passed to constructor")

        self.base_url = "https://api.brightdata.com/datasets/filter"
        self.dataset_id = "gd_l1viktl72bvl7bjuj0"  # LinkedIn Profiles dataset

        self.linkedin_service = linkedin_service
        self.three_step_service = ThreeStepProspectDiscoveryService()

        # Target titles optimized for Bright Data (EXACTLY 20 filters - max limit)
        # BEST PERFORMANCE: Specific titles only (no broad keywords)
        # V1 gave 49 profiles → 2 qualified (Amy + Richard)
        # V2 with broad keywords gave only 3 profiles → 1 qualified (worse!)
        self.default_target_titles = [
            # C-Suite (4 titles)
            "Chief Financial Officer",
            "CFO",

            # VP Level (2 titles)
            "VP Facilities",
            "VP Operations",
            "Finance",

            # Director Level (7 titles - PRIORITIZE these, they scored highest in original)
            "Director of Facilities",
            "Facilities Director",          # IMPORTANT: Different word order
            "Director of Engineering",
            "Director of Maintenance",
            "Engineering Director",
            "Maintenance Director",
            "Director of Operations",

            # Manager Level (5 titles)
            "Facilities Manager",
            "Maintenance Manager",
            "Engineering Manager",
            "Energy Manager",
            "Plant Manager",
            "Plant Operations",

            # Finance roles (2 titles - to catch "System Finance Manager")
            "Finance Manager",
            "Financial Manager",
        ]

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }


    async def step1_brightdata_filter(
        self,
        company_name: str,
        parent_account_name: str = None,
        target_titles: List[str] = None,
        company_city: str = None,
        company_state: str = None,
        min_connections: int = 10,  # LOWERED: Was 50, now 10 to catch all prospects
        use_city_filter: bool = False  # NEW: Disabled by default (too restrictive)
    ) -> Dict[str, Any]:
        """
        STEP 1: Filter LinkedIn profiles using Bright Data

        Args:
            company_name: Local account name
            parent_account_name: Parent account name (will search both if provided)
            target_titles: List of job titles (defaults to optimized list)
            company_city: City for location filtering (only used if use_city_filter=True)
            company_state: State for location filtering (not used in BrightData filter)
            min_connections: Minimum LinkedIn connections (default 20 - disabled)
            use_city_filter: Whether to apply city location filter (default False)

        Returns:
            Dict with success status, snapshot_id, and qualified LinkedIn URLs
        """
        try:
            logger.info(f"STEP 1: Starting Bright Data filter for: {company_name}")
            if parent_account_name:
                logger.info(f"   → Parent account: {parent_account_name}")

            # Use default titles if not provided
            if not target_titles:
                target_titles = self.default_target_titles

            logger.info(f"   → Filtering with {len(target_titles)} job titles")
            logger.info(f"   → Minimum connections: {min_connections}")

            # Get AI-generated company name variations
            logger.info("   → Generating company name variations using AI...")
            company_variations = await ai_company_normalization_service.normalize_company_name(
                company_name=company_name,
                parent_account_name=parent_account_name,
                company_city=company_city,
                company_state=company_state
            )
            logger.info(f"   → AI generated {len(company_variations)} company name variations")
            logger.debug(f"   → Variations: {company_variations}")

            # Build company name filters from AI variations (OR logic)
            company_filters = [
                {
                    "name": "current_company_name",
                    "value": variation,
                    "operator": "includes"
                }
                for variation in company_variations
            ]

            # Build title filters (OR logic)
            title_filters = [
                {
                    "name": "position",
                    "value": title,
                    "operator": "includes"
                }
                for title in target_titles
            ]

            # Build main filter (AND logic)
            main_filters = [
                # Company name filter (OR - match any company variation)
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
                # Exclude nursing roles (prevents "COO" from matching "Care Coordinator")
                {
                    "name": "position",
                    "value": "nurse",
                    "operator": "not_includes"
                },
                {
                    "name": "position",
                    "value": "nursing",
                    "operator": "not_includes"
                },
                {
                    "name": "position",
                    "value": "care",
                    "operator": "not_includes"
                },
                {
                    "name": "position",
                    "value": "clinical",
                    "operator": "not_includes"
                },
                {
                    "name": "position",
                    "value": "medical assistant",
                    "operator": "not_includes"
                },
                {
                    "name": "position",
                    "value": "physician",
                    "operator": "not_includes"
                },
                {
                    "name": "position",
                    "value": "therapist",
                    "operator": "not_includes"
                },
                # Minimum connections filter
                {
                    "name": "connections",
                    "value": min_connections,
                    "operator": ">="
                }
            ]

            # Add location filter (city) - OPTIONAL, disabled by default (too restrictive)
            if company_city and use_city_filter:
                logger.info(f"   → Applying city filter: {company_city}")
                main_filters.append({
                    "name": "city",
                    "value": company_city,
                    "operator": "includes"
                })
            else:
                logger.info("   → City filter DISABLED (casting wider net)")

            # Create filter payload
            payload = {
                "dataset_id": self.dataset_id,
                "filter": {
                    "operator": "and",
                    "filters": main_filters
                }
            }

            logger.info("Creating Bright Data snapshot...")

            # Create snapshot
            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if not response.ok:
                error_msg = f"Bright Data filter creation failed (Status {response.status_code})"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"

                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "step": "brightdata_filter_creation"
                }

            response_data = response.json()
            snapshot_id = response_data.get("snapshot_id")

            if not snapshot_id:
                return {
                    "success": False,
                    "error": "No snapshot_id in response",
                    "step": "brightdata_filter_creation"
                }

            logger.info(f"✅ Snapshot created: {snapshot_id}")
            logger.info("Polling for results (up to 5 minutes)...")

            # Poll for results
            profiles = await self._poll_snapshot_results(
                snapshot_id=snapshot_id,
                max_wait_time=300,  # 5 minutes
                poll_interval=10    # Check every 10 seconds
            )

            if not profiles:
                return {
                    "success": False,
                    "error": "No profiles found, snapshot timed out, or result count exceeded limit (max 75)",
                    "step": "brightdata_polling",
                    "snapshot_id": snapshot_id,
                    "suggestion": "Try adding more specific filters or reducing the number of target titles"
                }

            logger.info(f"✅ Retrieved {len(profiles)} profiles from Bright Data")

            # Transform Bright Data profiles to enriched format (no scraping needed!)
            logger.info("Transforming Bright Data profiles to enriched format...")
            enriched_prospects = []
            for profile in profiles:
                url = profile.get("url")
                if url:
                    # Transform Bright Data profile to the format expected by Step 3
                    enriched_prospect = self._transform_brightdata_profile(profile)
                    enriched_prospects.append(enriched_prospect)

            logger.info(f"✅ Transformed {len(enriched_prospects)} Bright Data profiles to enriched format")

            summary = {
                "total_profiles_from_brightdata": len(profiles),
                "profiles_transformed": len(enriched_prospects),
                "snapshot_id": snapshot_id,
                "searched_with_parent_account": parent_account_name is not None,
                "parent_account_name": parent_account_name,
                "filters_applied": {
                    "company_variations": len(company_filters),
                    "target_titles": len(target_titles),
                    "min_connections": min_connections,
                    "location_filter": company_city is not None
                },
                "scraping_skipped": True,
                "reason": "Bright Data already provides LinkedIn profile data"
            }

            return {
                "success": True,
                "step": "brightdata_filter_complete",
                "company_name": company_name,
                "parent_account_name": parent_account_name,
                "company_city": company_city,
                "company_state": company_state,
                "summary": summary,
                "enriched_prospects": enriched_prospects,
                "next_step": "Call step2_filter_prospects to apply validation filters"
            }

        except Exception as e:
            logger.error(f"Error in Bright Data Step 1: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step1_exception"
            }

    def _transform_brightdata_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Bright Data profile to the enriched format expected by Step 3

        Bright Data provides: url, name, first_name, last_name, position, headline,
        current_company_name, city, country, connections, followers, about,
        experience_*, education_*

        We need to transform to the format that three_step_service expects:
        {
            "linkedin_url": "...",
            "linkedin_data": {
                "url": "...",
                "name": "...",
                "job_title": "...",
                "company": "...",
                "location": "...",
                "connections": 123,
                ...
            },
            "has_complete_data": True,
            "data_source": "brightdata"
        }
        """
        # Extract and transform basic fields
        linkedin_data = {
            # Core identity
            "url": profile.get("url"),
            "name": profile.get("name"),
            "first_name": profile.get("first_name"),
            "last_name": profile.get("last_name"),

            # Current position
            "headline": profile.get("headline"),
            "job_title": profile.get("position"),  # Bright Data uses "position"
            "company": profile.get("current_company_name"),
            "company_name": profile.get("current_company_name"),

            # Location
            "location": profile.get("city") or profile.get("country") or "",
            "city": profile.get("city"),
            "state": None,  # Bright Data doesn't provide separate state field
            "country": profile.get("country"),

            # Professional summary
            "summary": profile.get("about"),
            "about": profile.get("about"),

            # Network metrics
            "connections": profile.get("connections"),
            "followers": profile.get("followers"),

            # Experience - Bright Data provides flat fields for most recent experience
            "experience": self._parse_brightdata_experience(profile),

            # Skills (Bright Data may not provide this)
            "skills": [],
            "skills_count": 0,

            # Metadata (set reasonable defaults)
            "profile_completeness_score": 80,  # Assume good since it's from dataset
            "accessibility_score": 8,  # Assume accessible
            "engagement_score": 7,  # Assume moderate engagement
        }

        # Return in the format expected by Step 2 filters and Step 3 AI ranking
        return {
            "linkedin_url": profile.get("url"),
            "linkedin_data": linkedin_data,
            "has_complete_data": True,
            "data_source": "brightdata"
        }

    def _parse_brightdata_experience(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Bright Data experience fields into the format expected by validation

        Bright Data provides: experience_company, experience_title, experience_start_date,
        experience_end_date, experience_location
        """
        experience = []

        # Check if we have experience data
        exp_company = profile.get("experience_company")
        exp_title = profile.get("experience_title")

        if exp_company or exp_title:
            # Format duration from start/end dates
            start_date = profile.get("experience_start_date", "")
            end_date = profile.get("experience_end_date", "")

            if start_date and end_date:
                duration = f"{start_date} - {end_date}"
            elif start_date:
                duration = f"{start_date} - Present"
            else:
                duration = ""

            experience.append({
                "company": exp_company or "",
                "title": exp_title or "",
                "location": profile.get("experience_location", ""),
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration
            })

        return experience

    async def _poll_snapshot_results(
        self,
        snapshot_id: str,
        max_wait_time: int = 300,
        poll_interval: int = 10
    ) -> Optional[List[Dict]]:
        """
        Poll Bright Data snapshot endpoint until results are ready

        Args:
            snapshot_id: Snapshot ID to poll
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Seconds between poll attempts

        Returns:
            List of profile dictionaries or None if failed/timeout
        """
        snapshot_url = f"https://api.brightdata.com/datasets/snapshots/{snapshot_id}"
        start_time = time.time()
        attempt = 0

        while time.time() - start_time < max_wait_time:
            attempt += 1
            elapsed = time.time() - start_time

            try:
                # Check snapshot status
                response = requests.get(
                    snapshot_url,
                    headers=self._get_headers(),
                    timeout=30
                )

                if not response.ok:
                    logger.warning(f"Attempt {attempt}: Status check failed ({response.status_code})")
                    await asyncio.sleep(poll_interval)
                    continue

                snapshot_info = response.json()
                status = snapshot_info.get("status")

                logger.info(f"Attempt {attempt} (elapsed: {elapsed:.0f}s): Status = {status}")

                if status == "ready":
                    # CHECK RESULT COUNT BEFORE DOWNLOADING (max 75 profiles)
                    # BrightData API returns "dataset_size" as the number of records
                    result_count = snapshot_info.get("dataset_size", 0)
                    logger.info(f"Snapshot ready with {result_count} records (dataset_size)")

                    if result_count > 75:
                        logger.warning(f"❌ Snapshot has {result_count} records (max allowed: 75)")
                        logger.warning("   Rejecting snapshot to avoid excessive API costs")
                        logger.warning("   Suggestion: Add more specific filters or reduce target titles")
                        logger.warning(f"   Snapshot ID: {snapshot_id}")
                        return None

                    logger.info(f"✅ Dataset size OK ({result_count} ≤ 75), proceeding with download...")

                    # Add small delay to allow download endpoint to catch up with status endpoint
                    await asyncio.sleep(5)

                    download_url = f"{snapshot_url}/download?format=json"

                    # Try downloading with retries for async download readiness
                    max_download_attempts = 10
                    download_attempt = 0

                    while download_attempt < max_download_attempts:
                        download_attempt += 1

                        try:
                            download_response = requests.get(
                                download_url,
                                headers=self._get_headers(),
                                timeout=60
                            )

                            if download_response.ok:
                                # Check if response is the "still building" message
                                response_text = download_response.text
                                if "building" in response_text.lower() and len(response_text) < 200:
                                    logger.info(f"   Download attempt {download_attempt}/{max_download_attempts}: Endpoint still building, waiting...")
                                    await asyncio.sleep(5)
                                    continue

                                # Try to parse as JSON
                                try:
                                    profiles = download_response.json()
                                    logger.info(f"✅ Successfully retrieved {len(profiles)} profiles")
                                    return profiles
                                except Exception as e:
                                    logger.warning(f"   Download attempt {download_attempt}/{max_download_attempts}: JSON parse failed - {e}")
                                    if download_attempt < max_download_attempts:
                                        await asyncio.sleep(5)
                                        continue
                                    else:
                                        logger.error(f"❌ All download attempts exhausted")
                                        logger.error(f"   Response preview: {repr(response_text[:500])}")
                                        return None
                            else:
                                logger.warning(f"   Download attempt {download_attempt}/{max_download_attempts}: HTTP {download_response.status_code}")
                                if download_attempt < max_download_attempts:
                                    await asyncio.sleep(5)
                                    continue
                                else:
                                    logger.error(f"❌ Download failed after {max_download_attempts} attempts")
                                    return None

                        except Exception as e:
                            logger.error(f"   Download attempt {download_attempt}/{max_download_attempts}: Request failed - {e}")
                            if download_attempt < max_download_attempts:
                                await asyncio.sleep(5)
                                continue
                            else:
                                logger.error(f"❌ Download failed with exception after {max_download_attempts} attempts")
                                return None

                    logger.error("Failed to download profile data after all retries")
                    return None

                elif status == "failed":
                    logger.error(f"Snapshot failed: {snapshot_info}")
                    warning = snapshot_info.get("warning", "Unknown error")
                    logger.warning(f"Failure reason: {warning}")
                    return None

                elif status in ["scheduled", "building"]:
                    # Still processing, wait and retry
                    await asyncio.sleep(poll_interval)
                    continue

                else:
                    logger.warning(f"Unknown status: {status}")
                    await asyncio.sleep(poll_interval)
                    continue

            except Exception as e:
                logger.error(f"Error polling snapshot (attempt {attempt}): {e}")
                await asyncio.sleep(poll_interval)
                continue

        logger.error(f"Timeout after {max_wait_time}s")
        return None

    async def step2_filter_prospects(
        self,
        enriched_prospects: List[Dict],
        company_name: str,
        company_city: str = None,
        company_state: str = None,
        location_filter_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        STEP 2: Filter Bright Data prospects (NO SCRAPING - we already have the data!)

        Applies validation filters directly to Bright Data profiles:
        - Company validation (with St./Saint normalization)
        - Employment status validation (filters retired/former employees)
        - Location validation (same state required)
        - Connection filtering (≥50 connections)

        Args:
            enriched_prospects: Enriched prospects from Step 1 (Bright Data profiles)
            company_name: Company name for validation
            company_city: City for location filtering
            company_state: State for location filtering
            location_filter_enabled: Whether to apply location filter

        Returns:
            Filtered prospects ready for AI ranking
        """
        try:
            logger.info(f"STEP 2: Filtering {len(enriched_prospects)} Bright Data prospects")
            logger.info("   ✅ Skipping LinkedIn scraping - using Bright Data profiles directly")

            # Apply advanced filtering (same logic as three_step_service but no scraping)
            advanced_filter_result = self.three_step_service._advanced_filter_with_linkedin_data(
                enriched_prospects,
                company_name,
                company_city,
                company_state,
                location_filter_enabled
            )

            final_prospects = advanced_filter_result['passed']
            filtered_out = advanced_filter_result['filtered_out']

            logger.info(f"After advanced filter: {len(final_prospects)} prospects")

            if not final_prospects:
                return {
                    "success": False,
                    "error": "No prospects passed advanced filtering",
                    "step": "advanced_filter",
                    "filtered_reasons": filtered_out
                }

            return {
                "success": True,
                "step": "filter_complete",
                "company_name": company_name,
                "summary": {
                    "profiles_from_step1": len(enriched_prospects),
                    "after_advanced_filter": len(final_prospects),
                    "ready_for_ranking": len(final_prospects),
                    "scraping_skipped": True
                },
                "enriched_prospects": final_prospects,
                "filtering_details": {
                    "filtered_out_count": len(filtered_out),
                    "filtered_out": filtered_out
                },
                "next_step": "Call step3_rank_prospects with these filtered prospects"
            }

        except Exception as e:
            logger.error(f"Error in Step 2: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step2_exception"
            }

    async def step3_rank_prospects(
        self,
        enriched_prospects: List[Dict],
        company_name: str,
        min_score_threshold: int = 65,
        max_prospects: int = 10
    ) -> Dict[str, Any]:
        """
        STEP 3: AI ranking and final selection (delegates to three_step_service)

        Args:
            enriched_prospects: Prospects from Step 2 with full LinkedIn data
            company_name: Company name for context
            min_score_threshold: Minimum score to be qualified (default 65)
            max_prospects: Maximum prospects to return (default 10)

        Returns:
            Final ranked and qualified prospects
        """
        logger.info("STEP 3: Delegating to three_step_service.step3_rank_prospects")

        return await self.three_step_service.step3_rank_prospects(
            enriched_prospects=enriched_prospects,
            company_name=company_name,
            min_score_threshold=min_score_threshold,
            max_prospects=max_prospects
        )


# Global instance (lazy initialization - won't raise error if token missing)
try:
    brightdata_prospect_discovery_service = BrightDataProspectDiscoveryService()
except ValueError:
    # Token not configured - service will be None
    brightdata_prospect_discovery_service = None
    logger.warning("BRIGHTDATA_API_TOKEN not configured - Bright Data prospect discovery disabled")
