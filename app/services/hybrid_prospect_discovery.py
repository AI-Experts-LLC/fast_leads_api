"""
Hybrid Prospect Discovery Service
Combines Serper (web search) + Bright Data (LinkedIn dataset) for maximum coverage

Pipeline:
Step 1: Run Serper AND Bright Data searches in parallel
Step 2: Deduplicate by name (prefer Bright Data data for duplicates)
Step 3: Enrich Serper-only results via Apify scraping
Step 4: Validate and filter all prospects
Step 5: AI ranking and qualification
Step 6: Queue qualified leads to PendingUpdates for approval

Benefits:
- Maximum coverage: Web search + dataset filtering
- Best data quality: Prefer Bright Data's rich profiles
- Fallback enrichment: Scrape Serper-only results
- Review workflow: All leads queued for manual approval
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .search import serper_service
from .brightdata_prospect_discovery import brightdata_prospect_discovery_service
from .linkedin import linkedin_service
from .three_step_prospect_discovery import ThreeStepProspectDiscoveryService

logger = logging.getLogger(__name__)


class HybridProspectDiscoveryService:
    """Hybrid prospect discovery combining Serper + Bright Data"""

    def __init__(self):
        self.serper_service = serper_service
        self.brightdata_service = brightdata_prospect_discovery_service
        self.linkedin_service = linkedin_service
        self.three_step_service = ThreeStepProspectDiscoveryService()

    async def step1_parallel_search(
        self,
        company_name: str,
        parent_account_name: str = None,
        target_titles: List[str] = None,
        company_city: str = None,
        company_state: str = None
    ) -> Dict[str, Any]:
        """
        STEP 1: Run Serper AND Bright Data searches in parallel

        Args:
            company_name: Local account name
            parent_account_name: Parent account name (optional)
            target_titles: List of job titles
            company_city: City for filtering
            company_state: State for filtering (REQUIRED)

        Returns:
            Combined results from both sources with deduplication stats
        """
        try:
            logger.info(f"STEP 1: Starting hybrid search for: {company_name}")
            if parent_account_name:
                logger.info(f"   → Parent account: {parent_account_name}")

            # Validate state is provided
            if not company_state:
                return {
                    "success": False,
                    "error": "company_state is required for hybrid search",
                    "step": "validation"
                }

            # Run BOTH searches in parallel
            logger.info("   → Running Serper AND Bright Data searches in parallel...")

            serper_task = self._run_serper_search(
                company_name, parent_account_name, target_titles,
                company_city, company_state
            )

            brightdata_task = self._run_brightdata_search(
                company_name, parent_account_name, target_titles,
                company_city, company_state
            )

            # Wait for both to complete
            serper_result, brightdata_result = await asyncio.gather(
                serper_task, brightdata_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(serper_result, Exception):
                logger.error(f"❌ Serper search failed: {str(serper_result)}")
                serper_result = {"success": False, "error": str(serper_result), "prospects": []}

            if isinstance(brightdata_result, Exception):
                logger.error(f"❌ Bright Data search failed: {str(brightdata_result)}")
                brightdata_result = {"success": False, "error": str(brightdata_result), "prospects": []}

            # Extract prospects from each source
            serper_prospects = serper_result.get("prospects", [])
            brightdata_prospects = brightdata_result.get("prospects", [])

            logger.info(f"   ✅ Serper: {len(serper_prospects)} prospects")
            logger.info(f"   ✅ Bright Data: {len(brightdata_prospects)} prospects")

            # Check if both failed
            if not serper_prospects and not brightdata_prospects:
                return {
                    "success": False,
                    "error": "Both Serper and Bright Data searches returned no results",
                    "step": "parallel_search",
                    "serper_error": serper_result.get("error"),
                    "brightdata_error": brightdata_result.get("error")
                }

            # Store for Step 2
            return {
                "success": True,
                "step": "parallel_search_complete",
                "company_name": company_name,
                "parent_account_name": parent_account_name,
                "company_city": company_city,
                "company_state": company_state,
                "serper_prospects": serper_prospects,
                "brightdata_prospects": brightdata_prospects,
                "summary": {
                    "serper_count": len(serper_prospects),
                    "brightdata_count": len(brightdata_prospects),
                    "serper_success": serper_result.get("success", False),
                    "brightdata_success": brightdata_result.get("success", False)
                },
                "next_step": "Call step2_deduplicate_and_enrich with these prospects"
            }

        except Exception as e:
            logger.error(f"Error in Step 1: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step1_exception"
            }

    async def _run_serper_search(
        self,
        company_name: str,
        parent_account_name: str,
        target_titles: List[str],
        company_city: str,
        company_state: str
    ) -> Dict[str, Any]:
        """Run Serper search and basic filtering"""
        try:
            # Use three_step_service for Serper search (Step 1)
            result = await self.three_step_service.step1_search_and_filter(
                company_name=company_name,
                parent_account_name=parent_account_name,
                target_titles=target_titles,
                company_city=company_city,
                company_state=company_state
            )

            if result.get("success"):
                prospects = result.get("qualified_prospects", [])
                return {"success": True, "prospects": prospects}
            else:
                return {"success": False, "error": result.get("error"), "prospects": []}

        except Exception as e:
            logger.error(f"Serper search error: {str(e)}")
            return {"success": False, "error": str(e), "prospects": []}

    async def _run_brightdata_search(
        self,
        company_name: str,
        parent_account_name: str,
        target_titles: List[str],
        company_city: str,
        company_state: str
    ) -> Dict[str, Any]:
        """Run Bright Data search"""
        try:
            if not self.brightdata_service:
                return {"success": False, "error": "Bright Data not configured", "prospects": []}

            # Use Bright Data Step 1 (filter + transform)
            result = await self.brightdata_service.step1_brightdata_filter(
                company_name=company_name,
                parent_account_name=parent_account_name,
                target_titles=target_titles,
                company_city=company_city,
                company_state=company_state,
                min_connections=10,
                use_city_filter=False
            )

            if result.get("success"):
                prospects = result.get("enriched_prospects", [])
                return {"success": True, "prospects": prospects}
            else:
                return {"success": False, "error": result.get("error"), "prospects": []}

        except Exception as e:
            logger.error(f"Bright Data search error: {str(e)}")
            return {"success": False, "error": str(e), "prospects": []}

    async def step2_deduplicate_and_enrich(
        self,
        serper_prospects: List[Dict],
        brightdata_prospects: List[Dict],
        company_name: str,
        company_city: str = None,
        company_state: str = None
    ) -> Dict[str, Any]:
        """
        STEP 2: Deduplicate by name + Enrich Serper-only results

        Logic:
        1. Extract names from both sources
        2. Find duplicates by name matching (fuzzy)
        3. For duplicates: Keep Bright Data version (richer data)
        4. For Serper-only: Scrape via Apify to get full LinkedIn data
        5. Combine all enriched prospects

        Args:
            serper_prospects: Prospects from Serper (Step 1)
            brightdata_prospects: Prospects from Bright Data (Step 1)
            company_name: Company name for context
            company_city: City for validation
            company_state: State for validation

        Returns:
            Deduplicated and enriched prospects ready for validation
        """
        try:
            logger.info(f"STEP 2: Deduplicating and enriching prospects")
            logger.info(f"   → Serper: {len(serper_prospects)} prospects")
            logger.info(f"   → Bright Data: {len(brightdata_prospects)} prospects")

            # Step 2.1: Extract names from Bright Data (already enriched)
            brightdata_names = set()
            for prospect in brightdata_prospects:
                name = self._extract_name(prospect)
                if name:
                    brightdata_names.add(name.lower().strip())

            logger.info(f"   → Bright Data unique names: {len(brightdata_names)}")

            # Step 2.2: Find Serper-only prospects (not in Bright Data)
            serper_only_prospects = []
            duplicates_found = []

            for prospect in serper_prospects:
                # Extract name from Serper prospect
                serper_name = self._extract_name_from_serper(prospect)
                if not serper_name:
                    continue

                serper_name_normalized = serper_name.lower().strip()

                # Check if this name is in Bright Data
                is_duplicate = serper_name_normalized in brightdata_names

                if is_duplicate:
                    duplicates_found.append({
                        "name": serper_name,
                        "reason": "Found in Bright Data (preferring Bright Data version)"
                    })
                    logger.debug(f"   → Duplicate: {serper_name} (skipping Serper version)")
                else:
                    serper_only_prospects.append(prospect)

            logger.info(f"   → Duplicates found: {len(duplicates_found)}")
            logger.info(f"   → Serper-only prospects: {len(serper_only_prospects)}")

            # Step 2.3: Scrape Serper-only prospects via Apify
            enriched_serper_prospects = []
            if serper_only_prospects:
                logger.info(f"   → Scraping {len(serper_only_prospects)} Serper-only prospects via Apify...")

                # Extract LinkedIn URLs
                serper_urls = [p.get("linkedin_url") for p in serper_only_prospects if p.get("linkedin_url")]

                if serper_urls:
                    # Use three_step_service Step 2 for scraping
                    scrape_result = await self.three_step_service.step2_scrape_profiles(
                        linkedin_urls=serper_urls,
                        company_name=company_name,
                        company_city=company_city,
                        company_state=company_state,
                        location_filter_enabled=True
                    )

                    if scrape_result.get("success"):
                        enriched_serper_prospects = scrape_result.get("enriched_prospects", [])
                        logger.info(f"   ✅ Enriched {len(enriched_serper_prospects)} Serper prospects")
                    else:
                        logger.warning(f"   ⚠️ Scraping failed: {scrape_result.get('error')}")

            # Step 2.4: Combine Bright Data + Enriched Serper prospects
            all_enriched_prospects = brightdata_prospects + enriched_serper_prospects

            logger.info(f"   ✅ Total enriched prospects: {len(all_enriched_prospects)}")
            logger.info(f"      → From Bright Data: {len(brightdata_prospects)}")
            logger.info(f"      → From Serper (enriched): {len(enriched_serper_prospects)}")

            return {
                "success": True,
                "step": "deduplicate_and_enrich_complete",
                "company_name": company_name,
                "summary": {
                    "brightdata_count": len(brightdata_prospects),
                    "serper_only_count": len(serper_only_prospects),
                    "serper_enriched_count": len(enriched_serper_prospects),
                    "duplicates_skipped": len(duplicates_found),
                    "total_enriched": len(all_enriched_prospects)
                },
                "enriched_prospects": all_enriched_prospects,
                "deduplication_details": {
                    "duplicates": duplicates_found,
                    "serper_only_urls": [p.get("linkedin_url") for p in serper_only_prospects]
                },
                "next_step": "Call step3_rank_and_qualify with these enriched prospects"
            }

        except Exception as e:
            logger.error(f"Error in Step 2: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step2_exception"
            }

    def _extract_name(self, prospect: Dict) -> Optional[str]:
        """Extract name from enriched prospect (Bright Data format)"""
        linkedin_data = prospect.get("linkedin_data", {})
        return linkedin_data.get("name") or linkedin_data.get("first_name", "") + " " + linkedin_data.get("last_name", "")

    def _extract_name_from_serper(self, prospect: Dict) -> Optional[str]:
        """Extract name from Serper prospect (Step 1 format)"""
        # Serper Step 1 format: {"linkedin_url": "...", "search_title": "John Doe - Title at Company"}
        search_title = prospect.get("search_title", "")
        if " - " in search_title:
            name = search_title.split(" - ")[0].strip()
            return name
        return None

    async def step3_rank_and_qualify(
        self,
        enriched_prospects: List[Dict],
        company_name: str,
        min_score_threshold: int = 65,
        max_prospects: int = 10
    ) -> Dict[str, Any]:
        """
        STEP 3: AI ranking and qualification

        Delegates to three_step_service Step 3 for consistent AI ranking.

        Args:
            enriched_prospects: All enriched prospects from Step 2
            company_name: Company name for context
            min_score_threshold: Minimum score to qualify (default 65)
            max_prospects: Maximum prospects to return (default 10)

        Returns:
            Ranked and qualified prospects ready for PendingUpdates
        """
        try:
            logger.info(f"STEP 3: AI ranking and qualification")
            logger.info(f"   → Input: {len(enriched_prospects)} enriched prospects")

            # Delegate to three_step_service for AI ranking
            result = await self.three_step_service.step3_rank_prospects(
                enriched_prospects=enriched_prospects,
                company_name=company_name,
                min_score_threshold=min_score_threshold,
                max_prospects=max_prospects
            )

            if result.get("success"):
                qualified_prospects = result.get("qualified_prospects", [])
                logger.info(f"   ✅ Qualified: {len(qualified_prospects)} prospects (score ≥{min_score_threshold})")

                return {
                    "success": True,
                    "step": "rank_and_qualify_complete",
                    "company_name": company_name,
                    "qualified_prospects": qualified_prospects,
                    "summary": result.get("summary", {}),
                    "next_step": "Call step4_queue_to_pending_updates to add leads for approval"
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error in Step 3: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step3_exception"
            }


# Global instance
hybrid_prospect_discovery_service = HybridProspectDiscoveryService()
