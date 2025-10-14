"""
Three-Step Prospect Discovery Service
Breaks the pipeline into 3 separate API calls to avoid Railway 5-minute timeout

Step 1: Search & Filter - Find and filter LinkedIn profiles
Step 2: Scrape - Get full LinkedIn data for qualified prospects
Step 3: Rank - AI ranking and final selection
"""

import logging
import re
from typing import Dict, Any, List, Optional
import asyncio
from .search import serper_service
from .linkedin import linkedin_service

logger = logging.getLogger(__name__)


class ThreeStepProspectDiscoveryService:
    """Three-step prospect discovery to avoid timeout issues"""

    def __init__(self):
        self.search_service = serper_service
        self.linkedin_service = linkedin_service

    async def step1_search_and_filter(
        self,
        company_name: str,
        target_titles: List[str] = None,
        company_city: str = None,
        company_state: str = None
    ) -> Dict[str, Any]:
        """
        STEP 1: Search LinkedIn and filter to qualified prospects

        Returns:
            List of LinkedIn URLs and metadata for prospects that passed filters
        """
        try:
            logger.info(f"STEP 1: Starting search and filter for: {company_name}")

            # Step 1.1: Search for LinkedIn profiles
            logger.info("Step 1.1: Searching LinkedIn profiles...")
            search_result = await self.search_service.search_linkedin_profiles(
                company_name=company_name,
                target_titles=target_titles,
                company_city=company_city,
                company_state=company_state
            )

            if not search_result.get("success"):
                return {
                    "success": False,
                    "error": f"LinkedIn search failed: {search_result.get('error')}",
                    "step": "search"
                }

            search_results = search_result.get("results", [])
            if not search_results:
                return {
                    "success": False,
                    "error": "No LinkedIn profiles found for this company",
                    "step": "search"
                }

            logger.info(f"Found {len(search_results)} LinkedIn profiles")

            # Step 1.2: Basic filtering (rule-based)
            logger.info("Step 1.2: Applying basic filters...")
            filtered_prospects = self._basic_filter_prospects(search_results, company_name, company_state)
            logger.info(f"After basic filter: {len(filtered_prospects)} prospects")

            if not filtered_prospects:
                return {
                    "success": False,
                    "error": "No prospects passed basic filtering",
                    "step": "basic_filter"
                }

            # Step 1.3: AI basic filter (connections)
            logger.info("Step 1.3: Applying AI basic filter...")
            ai_filtered_prospects = await self._ai_basic_filter_prospects(filtered_prospects, company_name)
            logger.info(f"After AI basic filter: {len(ai_filtered_prospects)} prospects")

            # Step 1.4: AI title filter
            logger.info("Step 1.4: Applying AI title filter...")
            title_filtered_prospects = await self._ai_title_filter_prospects(ai_filtered_prospects, company_name)
            logger.info(f"After AI title filter: {len(title_filtered_prospects)} prospects")

            if not title_filtered_prospects:
                return {
                    "success": False,
                    "error": "No prospects passed AI title filtering",
                    "step": "title_filter"
                }

            # Prepare output for Step 2
            qualified_urls = [
                {
                    "linkedin_url": p.get("link"),
                    "search_title": p.get("title"),
                    "search_snippet": p.get("snippet"),
                    "target_title": p.get("target_title"),
                    "ai_title_score": p.get("ai_title_filter", {}).get("score"),
                    "ai_title_reasoning": p.get("ai_title_filter", {}).get("reasoning")
                }
                for p in title_filtered_prospects
                if p.get("link")
            ]

            return {
                "success": True,
                "step": "search_and_filter_complete",
                "company_name": company_name,
                "company_city": company_city,
                "company_state": company_state,
                "summary": {
                    "total_search_results": len(search_results),
                    "after_basic_filter": len(filtered_prospects),
                    "after_ai_basic_filter": len(ai_filtered_prospects),
                    "after_title_filter": len(title_filtered_prospects),
                    "qualified_for_scraping": len(qualified_urls)
                },
                "qualified_prospects": qualified_urls,
                "next_step": "Call /discover-prospects-scrape with these LinkedIn URLs"
            }

        except Exception as e:
            logger.error(f"Error in Step 1: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step1_exception"
            }

    async def step2_scrape_profiles(
        self,
        linkedin_urls: List[str],
        company_name: str,
        company_city: str = None,
        company_state: str = None,
        location_filter_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        STEP 2: Scrape full LinkedIn data and apply advanced filters

        Args:
            linkedin_urls: List of LinkedIn URLs from Step 1
            company_name: Company name for validation
            company_city: City for location filtering
            company_state: State for location filtering
            location_filter_enabled: Whether to apply location filter

        Returns:
            Enriched prospects with full LinkedIn data ready for ranking
        """
        try:
            logger.info(f"STEP 2: Starting LinkedIn scraping for {len(linkedin_urls)} profiles")

            # Step 2.1: Scrape LinkedIn profiles
            logger.info("Step 2.1: Scraping LinkedIn profiles...")
            linkedin_result = await self.linkedin_service.scrape_profiles(linkedin_urls)

            if not linkedin_result.get("success"):
                return {
                    "success": False,
                    "error": f"LinkedIn scraping failed: {linkedin_result.get('error')}",
                    "step": "scraping"
                }

            linkedin_profiles = linkedin_result.get("profiles", [])
            logger.info(f"Successfully scraped {len(linkedin_profiles)} profiles")

            if not linkedin_profiles:
                return {
                    "success": False,
                    "error": "No profiles were successfully scraped",
                    "step": "scraping"
                }

            # Step 2.2: Create enriched prospects with lightweight data
            logger.info("Step 2.2: Creating enriched prospect data (consolidated)...")
            enriched_prospects = []
            for profile in linkedin_profiles:
                # Consolidate LinkedIn data to only essential fields
                consolidated_data = self._consolidate_linkedin_data(profile)
                enriched_prospects.append({
                    "linkedin_url": profile.get("url"),
                    "linkedin_data": consolidated_data,
                    "has_complete_data": True,
                    "data_source": "linkedin_scrape"
                })

            # Step 2.3: Advanced filtering
            logger.info("Step 2.3: Applying advanced filters...")
            advanced_filter_result = self._advanced_filter_with_linkedin_data(
                enriched_prospects, company_name, company_city, company_state, location_filter_enabled
            )
            final_prospects = advanced_filter_result['passed']

            logger.info(f"After advanced filter: {len(final_prospects)} prospects")

            if not final_prospects:
                return {
                    "success": False,
                    "error": "No prospects passed advanced filtering",
                    "step": "advanced_filter",
                    "filtered_reasons": advanced_filter_result['filtered_out']
                }

            return {
                "success": True,
                "step": "scrape_and_filter_complete",
                "company_name": company_name,
                "summary": {
                    "profiles_scraped": len(linkedin_profiles),
                    "after_advanced_filter": len(final_prospects),
                    "ready_for_ranking": len(final_prospects)
                },
                "enriched_prospects": final_prospects,
                "filtering_details": {
                    "filtered_out_count": len(advanced_filter_result['filtered_out']),
                    "filtered_out": advanced_filter_result['filtered_out']
                },
                "next_step": "Call /discover-prospects-rank with these enriched prospects"
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
        min_score_threshold: int = 70,
        max_prospects: int = 10
    ) -> Dict[str, Any]:
        """
        STEP 3: AI ranking and final selection

        Args:
            enriched_prospects: Prospects from Step 2 with full LinkedIn data
            company_name: Company name for context
            min_score_threshold: Minimum score to be qualified (default 70)
            max_prospects: Maximum prospects to return (default 10)

        Returns:
            Final ranked and qualified prospects
        """
        try:
            logger.info(f"STEP 3: Starting AI ranking for {len(enriched_prospects)} prospects")

            # Step 3.1: AI ranking
            logger.info("Step 3.1: Running AI ranking...")
            ranked_prospects = await self._ai_rank_prospects(enriched_prospects, company_name)

            if not ranked_prospects:
                return {
                    "success": False,
                    "error": "AI ranking failed to rank any prospects",
                    "step": "ranking"
                }

            logger.info(f"Successfully ranked {len(ranked_prospects)} prospects")

            # Step 3.2: Apply threshold and limit
            logger.info(f"Step 3.2: Applying score threshold ({min_score_threshold}) and limit ({max_prospects})...")

            # Filter by minimum score
            qualified_prospects = [
                p for p in ranked_prospects
                if p.get('ai_ranking', {}).get('ranking_score', 0) >= min_score_threshold
            ]

            # Sort by score (descending) and limit
            qualified_prospects.sort(
                key=lambda p: p.get('ai_ranking', {}).get('ranking_score', 0),
                reverse=True
            )
            top_prospects = qualified_prospects[:max_prospects]

            logger.info(f"Final qualified prospects: {len(top_prospects)}")

            return {
                "success": True,
                "step": "ranking_complete",
                "company_name": company_name,
                "summary": {
                    "prospects_ranked": len(ranked_prospects),
                    "above_threshold": len(qualified_prospects),
                    "final_top_prospects": len(top_prospects),
                    "min_score_threshold": min_score_threshold,
                    "max_prospects": max_prospects
                },
                "qualified_prospects": top_prospects,
                "all_ranked_prospects": ranked_prospects,
                "pipeline_complete": True
            }

        except Exception as e:
            logger.error(f"Error in Step 3: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step": "step3_exception"
            }

    # ========== HELPER METHODS (copied from improved_prospect_discovery.py) ==========

    def _basic_filter_prospects(self, prospects: List[Dict], company_name: str, company_state: str = None) -> List[Dict]:
        """Basic rule-based filtering - same as original"""
        passed = []

        exclusion_patterns = [
            r'\bintern\b', r'\bstudent\b', r'\bgraduate\b', r'\bentry.level\b',
            r'\bformer\b.*\bat\b.*' + re.escape(company_name.lower()),
            r'\bpreviously\b.*\bat\b.*' + re.escape(company_name.lower()),
            r'\bex[\-\s]' + re.escape(company_name.lower()),
        ]

        senior_indicators = [
            r'\bdirector\b', r'\bmanager\b', r'\bvp\b', r'\bvice.president\b',
            r'\bcfo\b', r'\bcoo\b', r'\bceo\b', r'\bchief\b', r'\bhead\b',
            r'\blead\b', r'\bsenior\b', r'\bprincipal\b', r'\bsupervisor\b'
        ]

        for prospect in prospects:
            title = prospect.get("title", "").lower()
            snippet = prospect.get("snippet", "").lower()
            combined_text = f"{title} {snippet}"

            # Check exclusions
            excluded = False
            for pattern in exclusion_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    excluded = True
                    break

            if excluded:
                continue

            # Check senior indicators
            has_senior_indicator = any(
                re.search(indicator, combined_text, re.IGNORECASE)
                for indicator in senior_indicators
            )

            # Check company mention
            company_mentioned = (
                company_name.lower() in combined_text or
                any(part.lower() in combined_text for part in company_name.split() if len(part) > 3)
            )

            if has_senior_indicator or company_mentioned:
                prospect["basic_filter"] = {
                    "passed": True,
                    "has_senior_indicator": has_senior_indicator,
                    "company_mentioned": company_mentioned
                }
                passed.append(prospect)

        return passed

    async def _ai_basic_filter_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """Simple rule-based filtering for connections - same as original"""
        filtered = []

        for prospect in prospects:
            title = prospect.get("title", "").lower()
            snippet = prospect.get("snippet", "").lower()
            combined_text = f"{title} {snippet}"

            # Extract connection count
            connection_count = 0
            connection_match = re.search(r'(\d+)\+?\s*connections?', snippet, re.IGNORECASE)
            if connection_match:
                connection_count = int(connection_match.group(1))

            # Filter low connections
            if connection_count > 0 and connection_count < 75:
                continue

            # Check company mention
            company_variations = self._generate_company_variations(company_name)
            company_match = any(
                variation.lower() in combined_text for variation in company_variations
            )

            if not company_match:
                company_parts = [part.strip() for part in company_name.split() if len(part) > 3]
                company_match = any(part.lower() in combined_text for part in company_parts)

            if company_match or connection_count >= 75:
                prospect["ai_basic_filter"] = {
                    "passed": True,
                    "company_match": company_match,
                    "connection_count": connection_count if connection_count > 0 else "Unknown"
                }
                filtered.append(prospect)

        return filtered

    async def _ai_title_filter_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """AI title filtering - same as original"""
        if not prospects:
            return []

        try:
            from .improved_ai_ranking import ImprovedAIRankingService
            from app.prompts import AI_TITLE_FILTER_SYSTEM_PROMPT, AI_TITLE_FILTER_USER_PROMPT_TEMPLATE

            ai_service = ImprovedAIRankingService()

            if not ai_service.client:
                logger.warning("OpenAI client not available - skipping title filter")
                return prospects

            # Score each prospect's title
            filtering_tasks = []
            for i, prospect in enumerate(prospects):
                task = self._score_title_relevance(prospect, company_name, ai_service, i)
                filtering_tasks.append(task)

            logger.info(f"Scoring {len(prospects)} prospects for title relevance...")
            scoring_results = await asyncio.gather(*filtering_tasks, return_exceptions=True)

            # Filter based on scores
            filtered_prospects = []
            MIN_TITLE_SCORE = 55

            for i, (prospect, result) in enumerate(zip(prospects, scoring_results)):
                if isinstance(result, Exception):
                    logger.error(f"Error scoring prospect {i}: {result}")
                    filtered_prospects.append(prospect)
                    continue

                if isinstance(result, dict) and result.get("success"):
                    score = result.get("score", 0)
                    reasoning = result.get("reasoning", "")

                    prospect["ai_title_filter"] = {
                        "score": score,
                        "reasoning": reasoning,
                        "passed": score >= MIN_TITLE_SCORE
                    }

                    if score >= MIN_TITLE_SCORE:
                        filtered_prospects.append(prospect)
                else:
                    filtered_prospects.append(prospect)

            return filtered_prospects

        except Exception as e:
            logger.error(f"Error in title filtering: {str(e)}")
            return prospects

    async def _score_title_relevance(self, prospect: Dict, company_name: str, ai_service, index: int) -> Dict[str, Any]:
        """Score single prospect title - same as original"""
        try:
            from app.prompts import AI_TITLE_FILTER_SYSTEM_PROMPT, AI_TITLE_FILTER_USER_PROMPT_TEMPLATE
            import json

            title = prospect.get("title", "")
            snippet = prospect.get("snippet", "")

            prompt = AI_TITLE_FILTER_USER_PROMPT_TEMPLATE.format(
                company_name=company_name,
                title=title,
                snippet=snippet[:300]
            )

            full_input = f"{AI_TITLE_FILTER_SYSTEM_PROMPT}\n\n{prompt}"

            api_params = {
                "model": ai_service.model,
                "input": full_input,
                "text": {"format": {"type": "json_object"}},
                "max_output_tokens": 300,
                "timeout": 20
            }

            if "gpt-5" in ai_service.model or ai_service.model.startswith("o"):
                api_params["reasoning"] = {"effort": "minimal"}

            response = ai_service.client.responses.create(**api_params)

            if not response or not hasattr(response, 'output') or not response.output:
                return {"success": False, "index": index, "error": "Invalid response"}

            try:
                output_item = response.output[-1]
                output_text = output_item.content[0].text
            except (IndexError, AttributeError, TypeError) as e:
                return {"success": False, "index": index, "error": str(e)}

            result_data = json.loads(output_text)

            if "score" in result_data:
                return {
                    "success": True,
                    "index": index,
                    "score": int(result_data["score"]),
                    "reasoning": result_data.get("reasoning", "")
                }
            else:
                return {"success": False, "index": index, "error": "Missing score"}

        except Exception as e:
            logger.error(f"Error scoring title for prospect {index}: {str(e)}")
            return {"success": False, "index": index, "error": str(e)}

    def _advanced_filter_with_linkedin_data(
        self,
        prospects: List[Dict],
        company_name: str,
        company_city: str = None,
        company_state: str = None,
        location_filter_enabled: bool = True
    ) -> Dict[str, List]:
        """Advanced filtering with LinkedIn data - same as original"""
        passed = []
        filtered_out = []

        for prospect in prospects:
            linkedin_data = prospect.get("linkedin_data", {})

            # Filter by connections
            connections = linkedin_data.get("connections", 0)
            if connections and connections < 75:
                filtered_out.append({
                    "stage": "linkedin_connections",
                    "name": linkedin_data.get('name', 'Unknown'),
                    "linkedin_url": prospect.get('linkedin_url', ''),
                    "reason": f"Low connections ({connections} < 75)"
                })
                continue

            current_title = (linkedin_data.get("job_title") or "").lower()
            current_company = (linkedin_data.get("company") or "").lower()

            # Filter interns/students
            if "intern" in current_title or "student" in current_title:
                continue

            # Company validation
            company_match_result = self._validate_company_match(
                current_company, company_name, linkedin_data.get('name', 'Unknown')
            )

            if not company_match_result['is_match']:
                filtered_out.append({
                    "stage": "company_validation",
                    "name": linkedin_data.get('name', 'Unknown'),
                    "linkedin_url": prospect.get('linkedin_url', ''),
                    "reason": company_match_result['reason']
                })
                continue

            # Location validation
            if location_filter_enabled and company_state:
                location_match_result = self._validate_location_match(
                    linkedin_data.get('location', ''),
                    company_city,
                    company_state,
                    linkedin_data.get('name', 'Unknown')
                )

                if not location_match_result['is_match']:
                    filtered_out.append({
                        "stage": "location_validation",
                        "name": linkedin_data.get('name', 'Unknown'),
                        "linkedin_url": prospect.get('linkedin_url', ''),
                        "reason": location_match_result['reason']
                    })
                    continue

            # Calculate seniority score
            from .improved_prospect_discovery import improved_prospect_discovery_service
            seniority_score = improved_prospect_discovery_service._calculate_seniority_score(linkedin_data)

            prospect["advanced_filter"] = {
                "passed": True,
                "company_match": company_match_result['is_match'],
                "seniority_score": seniority_score,
                "current_title": current_title,
                "current_company": current_company
            }

            passed.append(prospect)

        return {"passed": passed, "filtered_out": filtered_out}

    def _validate_company_match(self, current_company: str, target_company: str, prospect_name: str) -> Dict[str, Any]:
        """Company validation - same as original"""
        if not current_company:
            return {'is_match': False, 'reason': 'No company listed'}

        current_lower = current_company.lower().strip()
        target_lower = target_company.lower().strip()

        if current_lower == target_lower:
            return {'is_match': True, 'reason': 'Exact match'}

        healthcare_suffixes = [
            "medical center", "hospital", "health system", "healthcare",
            "medical", "health", "clinic", "regional medical center",
            "health care", "medical group", "health services", "health & services"
        ]

        current_base = current_lower
        target_base = target_lower

        for suffix in healthcare_suffixes:
            current_base = current_base.replace(suffix, "").strip()
            target_base = target_base.replace(suffix, "").strip()

        if current_base == target_base:
            return {'is_match': True, 'reason': 'Base name match'}

        target_words = [w for w in target_base.split() if len(w) > 4]

        if target_words:
            main_identifier = target_words[0]
            if main_identifier in current_base:
                return {'is_match': True, 'reason': f'Shared main identifier ({main_identifier})'}

        return {'is_match': False, 'reason': f"Company mismatch: '{current_company}' vs '{target_company}'"}

    def _validate_location_match(self, prospect_location: str, company_city: str, company_state: str, prospect_name: str) -> Dict[str, Any]:
        """Location validation - simplified from original"""
        if not prospect_location or prospect_location.lower() == 'none':
            return {'is_match': True, 'reason': 'No location data available'}

        location_lower = prospect_location.lower().strip()

        if company_city and company_city.lower() in location_lower:
            return {'is_match': True, 'reason': f'Same city ({company_city})'}

        # Check state match
        from .improved_prospect_discovery import improved_prospect_discovery_service
        state_variations = improved_prospect_discovery_service._get_state_variations(company_state)
        state_variations_lower = [v.lower() for v in state_variations]

        state_match = any(state_var in location_lower for state_var in state_variations_lower)

        if state_match:
            return {'is_match': True, 'reason': f'Same state ({company_state})'}

        return {'is_match': False, 'reason': f"Location too far: '{prospect_location}' vs '{company_city}, {company_state}'"}

    def _generate_company_variations(self, company_name: str) -> List[str]:
        """Generate company name variations - same as original"""
        variations = [company_name]

        name_parts = company_name.split()
        if len(name_parts) > 1:
            variations.append(" ".join(name_parts[:-1]))
            variations.append(name_parts[0])

        healthcare_suffixes = [
            "Medical Center", "Hospital", "Health System", "Healthcare",
            "Medical", "Health", "Clinic", "Regional Medical Center"
        ]

        base_name = company_name
        for suffix in healthcare_suffixes:
            if suffix in company_name:
                base_name = company_name.replace(suffix, "").strip()
                break

        for suffix in healthcare_suffixes:
            variations.append(f"{base_name} {suffix}")

        return list(set(variations))

    async def _ai_rank_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """AI ranking - same as original"""
        if not prospects:
            return []

        try:
            from .improved_ai_ranking import ImprovedAIRankingService
            ai_service = ImprovedAIRankingService()

            ranking_result = await ai_service.rank_prospects(prospects, company_name)

            if ranking_result.get("success"):
                return ranking_result.get("ranked_prospects", prospects)
            else:
                logger.warning(f"AI ranking failed: {ranking_result.get('error')}")
                return prospects

        except Exception as e:
            logger.error(f"Error in AI ranking: {str(e)}")
            return prospects

    def _consolidate_linkedin_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract only essential fields from linkedin.py's transformed data.
        The linkedin service already provides snake_case transformed data,
        so we just need to select the fields we need for filtering and AI ranking.
        """
        try:
            # Essential fields for filtering and AI ranking
            consolidated = {
                # Core identity
                'url': profile_data.get('url'),
                'name': profile_data.get('name'),
                'first_name': profile_data.get('first_name'),
                'last_name': profile_data.get('last_name'),

                # Current position
                'headline': profile_data.get('headline'),
                'job_title': profile_data.get('job_title'),
                'company': profile_data.get('company'),
                'company_name': profile_data.get('company_name'),

                # Location
                'location': profile_data.get('location'),
                'city': profile_data.get('city'),
                'state': profile_data.get('state'),

                # Professional summary
                'summary': profile_data.get('summary'),
                'about': profile_data.get('about'),

                # Network metrics
                'connections': profile_data.get('connections'),
                'followers': profile_data.get('followers'),

                # Experience & skills
                'total_experience_years': profile_data.get('total_experience_years'),
                'professional_authority_score': profile_data.get('professional_authority_score'),
                'skills': profile_data.get('skills', []),
                'skills_count': profile_data.get('skills_count', 0),
                'top_skills_by_endorsements': profile_data.get('top_skills_by_endorsements'),

                # Contact
                'email': profile_data.get('email'),
                'mobile_number': profile_data.get('mobile_number'),

                # Metadata
                'profile_completeness_score': profile_data.get('profile_completeness_score'),
                'accessibility_score': profile_data.get('accessibility_score'),
                'engagement_score': profile_data.get('engagement_score'),
            }

            logger.info(f"📊 Consolidated LinkedIn data - kept {len(consolidated)} essential fields from {len(profile_data)} total fields")
            return consolidated

        except Exception as e:
            logger.error(f"❌ Error consolidating LinkedIn data: {str(e)}")
            # Return the essential fields we need even if consolidation fails
            return {
                'name': profile_data.get('name'),
                'job_title': profile_data.get('job_title'),
                'company': profile_data.get('company'),
                'company_name': profile_data.get('company_name'),
                'location': profile_data.get('location'),
                'connections': profile_data.get('connections'),
                'total_experience_years': profile_data.get('total_experience_years', 0),
                'professional_authority_score': profile_data.get('professional_authority_score', 50),
                'skills': profile_data.get('skills', []),
            }


# Global instance
three_step_prospect_discovery_service = ThreeStepProspectDiscoveryService()
