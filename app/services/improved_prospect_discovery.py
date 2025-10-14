"""
IMPROVED Prospect Discovery Service
Fixes accuracy issues by:
1. Company name expansion to find all LinkedIn variations
2. Basic filtering BEFORE AI involvement
3. LinkedIn scraping BEFORE AI qualification
4. AI only ranks real data, doesn't create data
"""

import logging
import re
from typing import Dict, Any, List, Optional
import asyncio
from .search import serper_service
from .linkedin import linkedin_service
from .company_name_expansion import company_name_expansion_service

logger = logging.getLogger(__name__)


class ImprovedProspectDiscoveryService:
    """Improved prospect discovery with better accuracy"""
    
    def __init__(self):
        self.search_service = serper_service
        self.linkedin_service = linkedin_service
    
    async def discover_prospects(self, company_name: str, target_titles: List[str] = None, company_city: str = None, company_state: str = None, location_filter_enabled: bool = True) -> Dict[str, Any]:
        """
        Improved prospect discovery pipeline

        Args:
            company_name: Name of the target company
            target_titles: Optional list of specific job titles to search for
            company_city: Optional company city for location matching
            company_state: Optional company state for location matching

        Returns:
            Dictionary with discovered prospects and their complete LinkedIn data
        """
        try:
            logger.info(f"Starting IMPROVED prospect discovery for: {company_name}")

            # Initialize filtering funnel report
            filtering_funnel = {
                "stages": [],
                "filtered_out": []
            }

            # Step 0: Expand company name into all LinkedIn variations
            logger.info("Step 0: Expanding company name variations...")
            expansion_result = await company_name_expansion_service.expand_company_name(
                company_name=company_name,
                company_city=company_city,
                company_state=company_state
            )

            company_variations = expansion_result.get("variations", [company_name])
            logger.info(f"Expanded to {len(company_variations)} variations: {', '.join(company_variations[:5])}{'...' if len(company_variations) > 5 else ''}")

            # Step 1: Search for LinkedIn profiles using ALL company name variations
            logger.info("Step 1: Searching for LinkedIn profiles across all company variations...")
            all_search_results = []

            for variation in company_variations:
                logger.info(f"  Searching for: {variation}")
                search_result = await self.search_service.search_linkedin_profiles(
                    company_name=variation,
                    target_titles=target_titles,
                    company_city=company_city,
                    company_state=company_state
                )

                if search_result.get("success") and search_result.get("results"):
                    # Tag each result with which variation it came from
                    for result in search_result.get("results", []):
                        result["search_company_variation"] = variation
                    all_search_results.extend(search_result.get("results", []))

            # Deduplicate by LinkedIn URL
            seen_urls = set()
            search_results = []
            for result in all_search_results:
                url = result.get("link", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    search_results.append(result)

            # Update search_result for compatibility with rest of pipeline
            search_result = {
                "success": True if search_results else False,
                "results": search_results,
                "company_variations_searched": len(company_variations)
            }
            
            if not search_result.get("success"):
                return {
                    "success": False,
                    "error": f"LinkedIn search failed: {search_result.get('error')}",
                    "step_failed": "search"
                }
            
            search_results = search_result.get("results", [])
            if not search_results:
                return {
                    "success": False,
                    "error": "No LinkedIn profiles found for this company",
                    "step_failed": "search"
                }
            
            logger.info(f"Found {len(search_results)} LinkedIn profiles")
            
            # Log all search results found
            logger.info("=== ALL SEARCH RESULTS FOUND ===")
            for i, result in enumerate(search_results):
                logger.info(f"{i+1}. {result.get('title', 'N/A')} | Target: {result.get('target_title', 'N/A')} | URL: {result.get('link', 'N/A')}")
            logger.info("=== END SEARCH RESULTS ===")
            
            # Step 2: Basic data filtering (NO AI - just rule-based filtering)
            logger.info("Step 2: Basic data filtering...")
            basic_filter_result = self._basic_filter_prospects(search_results, company_name, company_state)
            filtered_prospects = basic_filter_result['passed']
            filtering_funnel['filtered_out'].extend(basic_filter_result['filtered_out'])
            logger.info(f"Filtered to {len(filtered_prospects)} prospects after removing obvious mismatches")
            
            # Log prospects that passed basic filtering
            logger.info("=== PROSPECTS AFTER BASIC FILTER ===")
            for i, prospect in enumerate(filtered_prospects):
                basic_filter = prospect.get('basic_filter', {})
                logger.info(f"{i+1}. {prospect.get('title', 'N/A')} | Target: {prospect.get('target_title', 'N/A')} | Senior: {basic_filter.get('has_senior_indicator', False)} | Company: {basic_filter.get('company_mentioned', False)} | Location Score: {basic_filter.get('location_score', 0)}")
            logger.info("=== END BASIC FILTER RESULTS ===")
            
            if not filtered_prospects:
                return {
                    "success": True,
                    "message": "No prospects passed basic filtering",
                    "search_results": len(search_results),
                    "filtered_prospects": [],
                    "filter_summary": {"removed_prospects": len(search_results)}
                }

            
            
            # Step 3: AI-powered basic filter for company accuracy and connection count
            logger.info("Step 3: AI-powered company accuracy and connection filter...")
            ai_filtered_prospects = await self._ai_basic_filter_prospects(filtered_prospects, company_name)
            logger.info(f"AI filtered to {len(ai_filtered_prospects)} prospects after removing wrong companies and low-connection profiles")

            # Step 3.5: AI filter for proper job titles - if job title is not relevant, remove the prospect
            logger.info("Step 3.5: AI filter for proper job titles...")
            prospects_before_title_filter = len(ai_filtered_prospects)
            ai_filtered_prospects = await self._ai_title_filter_prospects(ai_filtered_prospects, company_name)
            filtered_by_title = prospects_before_title_filter - len(ai_filtered_prospects)
            logger.info(f"AI filtered to {len(ai_filtered_prospects)} prospects after removing {filtered_by_title} with irrelevant job titles")
            
            # Log prospects that passed title filtering
            logger.info("=== PROSPECTS AFTER AI TITLE FILTER ===")
            for i, prospect in enumerate(ai_filtered_prospects):
                title_filter = prospect.get('ai_title_filter', {})
                logger.info(f"{i+1}. {prospect.get('title', 'N/A')} | Score: {title_filter.get('score', 'N/A')}/100 | {title_filter.get('reasoning', 'N/A')}")
            logger.info("=== END AI TITLE FILTER RESULTS ===")
            
            if not ai_filtered_prospects:
                return {
                    "success": True,
                    "message": "No prospects passed AI title filtering",
                    "search_results": len(search_results),
                    "basic_filtered_prospects": len(filtered_prospects),
                    "after_title_filter": 0,
                    "ai_filtered_prospects": [],
                    "filter_summary": {"removed_prospects": len(search_results)}
                }
            
            # Step 4: LinkedIn scraping (GET REAL DATA FIRST)
            logger.info("Step 4: Scraping complete LinkedIn data...")
            linkedin_urls = [p.get("link") for p in ai_filtered_prospects if p.get("link")]
            
            linkedin_result = await self.linkedin_service.scrape_profiles(linkedin_urls)
            
            if not linkedin_result.get("success"):
                return {
                    "success": False,
                    "error": f"LinkedIn scraping failed: {linkedin_result.get('error')}",
                    "step_failed": "scraping"
                }
            
            linkedin_profiles = linkedin_result.get("profiles", [])
            logger.info(f"Successfully scraped {len(linkedin_profiles)} complete LinkedIn profiles")
            
            # Step 5: Combine search results with scraped LinkedIn data
            logger.info("Step 5: Combining search results with LinkedIn data...")
            enriched_prospects = self._combine_search_and_linkedin_data(
                ai_filtered_prospects, linkedin_profiles
            )
            
            # Step 6: FINAL filtering based on complete LinkedIn data
            logger.info("Step 6: Final filtering based on complete LinkedIn data...")
            advanced_filter_result = self._advanced_filter_with_linkedin_data(
                enriched_prospects, company_name, company_city, company_state, location_filter_enabled
            )
            final_prospects = advanced_filter_result['passed']
            filtering_funnel['filtered_out'].extend(advanced_filter_result['filtered_out'])
            
            # Log prospects that passed advanced filtering
            logger.info("=== PROSPECTS AFTER ADVANCED FILTER ===")
            for i, prospect in enumerate(final_prospects):
                linkedin_data = prospect.get('linkedin_data', {})
                advanced_filter = prospect.get('advanced_filter', {})
                logger.info(f"{i+1}. {linkedin_data.get('name', 'N/A')} | Title: {linkedin_data.get('job_title', 'N/A')} | Company: {linkedin_data.get('company', 'N/A')} | Seniority Score: {advanced_filter.get('seniority_score', 0)}")
            logger.info("=== END ADVANCED FILTER RESULTS ===")
            
            # Step 7: AI ranking (ONLY ranking, no data modification)
            logger.info("Step 7: AI ranking of validated prospects...")
            ranked_prospects = await self._ai_rank_prospects(final_prospects, company_name)

            # Step 8: Apply minimum score threshold and limit to top prospects
            logger.info("Step 8: Applying score threshold and limiting to top prospects...")
            MIN_SCORE_THRESHOLD = 70  # Minimum score to be considered qualified
            MAX_PROSPECTS = 10  # Maximum number of prospects to return

            # Filter by minimum score
            qualified_prospects = [
                p for p in ranked_prospects
                if p.get('ai_ranking', {}).get('ranking_score', 0) >= MIN_SCORE_THRESHOLD
            ]

            # Sort by score (descending) and limit to top MAX_PROSPECTS
            qualified_prospects.sort(
                key=lambda p: p.get('ai_ranking', {}).get('ranking_score', 0),
                reverse=True
            )
            top_prospects = qualified_prospects[:MAX_PROSPECTS]

            logger.info(f"Filtered to {len(top_prospects)} prospects (min score {MIN_SCORE_THRESHOLD}, max {MAX_PROSPECTS})")

            # Log final ranked prospects
            logger.info("=== FINAL TOP PROSPECTS ===")
            for i, prospect in enumerate(top_prospects):
                linkedin_data = prospect.get('linkedin_data', {})
                ai_ranking = prospect.get('ai_ranking', {})
                target_title = prospect.get('target_title', 'N/A')
                logger.info(f"{i+1}. {linkedin_data.get('name', 'N/A')} | Target: {target_title} | LinkedIn Title: {linkedin_data.get('job_title', 'N/A')} | AI Score: {ai_ranking.get('ranking_score', 0)}/100")
            logger.info("=== END FINAL PROSPECTS ===")
            
            return {
                "success": True,
                "company_name": company_name,
                "company_variations_used": company_variations,
                "pipeline_summary": {
                    "company_variations_searched": len(company_variations),
                    "search_results_found": len(search_results),
                    "prospects_after_basic_filter": len(filtered_prospects),
                    "prospects_after_ai_basic_filter": prospects_before_title_filter,
                    "prospects_after_ai_title_filter": len(ai_filtered_prospects) if ai_filtered_prospects else 0,
                    "filtered_by_title": filtered_by_title,
                    "linkedin_profiles_scraped": len(linkedin_profiles),
                    "prospects_after_advanced_filter": len(final_prospects),
                    "prospects_after_ai_ranking": len(ranked_prospects),
                    "prospects_meeting_threshold": len(qualified_prospects),
                    "final_top_prospects": len(top_prospects)
                },
                "qualified_prospects": top_prospects,
                "all_ranked_prospects": ranked_prospects,  # All prospects with AI ranking (before threshold)
                "prospects_after_advanced_filter": final_prospects,  # All 9 prospects that passed advanced filter (before AI ranking)
                "filtering_funnel": {
                    "total_filtered_out": len(filtering_funnel['filtered_out']),
                    "filtered_out_by_stage": self._group_filtered_by_stage(filtering_funnel['filtered_out']),
                    "detailed_filtered_prospects": filtering_funnel['filtered_out']
                },
                "cost_estimates": {
                    "company_expansion_cost": 0.01,  # Cost of AI name expansion
                    "search_cost": 0.01 * len(company_variations),  # Search cost per variation
                    "linkedin_cost": linkedin_result.get("cost_estimate", 0),
                    "ai_ranking_cost": 0.02,
                    "total_estimated": 0.01 + (0.01 * len(company_variations)) + linkedin_result.get("cost_estimate", 0) + 0.02
                }
            }
            
        except Exception as e:
            logger.error(f"Error in improved prospect discovery pipeline: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step_failed": "pipeline"
            }
    
    def _basic_filter_prospects(self, prospects: List[Dict], company_name: str, company_state: str = None) -> Dict[str, List]:
        """
        Basic rule-based filtering to remove obvious mismatches
        NO AI involved - just simple text analysis

        Returns:
            dict with 'passed' and 'filtered_out' lists
        """
        passed = []
        filtered_out = []

        # Common exclusion patterns
        exclusion_patterns = [
            r'\bintern\b',
            r'\bstudent\b', 
            r'\bgraduate\b',
            r'\bentry.level\b',
            r'\bformer\b.*\bat\b.*' + re.escape(company_name.lower()),
            r'\bpreviously\b.*\bat\b.*' + re.escape(company_name.lower()),
            r'\bex[\-\s]' + re.escape(company_name.lower()),
        ]
        
        # Required inclusion indicators
        senior_indicators = [
            r'\bdirector\b', r'\bmanager\b', r'\bvp\b', r'\bvice.president\b',
            r'\bcfo\b', r'\bcoo\b', r'\bceo\b', r'\bchief\b', r'\bhead\b',
            r'\blead\b', r'\bsenior\b', r'\bprincipal\b', r'\bsupervisor\b'
        ]
        
        for prospect in prospects:
            title = prospect.get("title", "").lower()
            snippet = prospect.get("snippet", "").lower()
            combined_text = f"{title} {snippet}"
            
            # Check for exclusion patterns
            excluded = False
            exclusion_reason = None
            for pattern in exclusion_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    excluded = True
                    exclusion_reason = f"Matched exclusion pattern: {pattern}"
                    logger.debug(f"Excluded prospect: {prospect.get('title')} - matched pattern: {pattern}")
                    break

            if excluded:
                filtered_out.append({
                    "stage": "basic_filter",
                    "name": prospect.get('title', 'Unknown'),
                    "linkedin_url": prospect.get('link', ''),
                    "reason": exclusion_reason
                })
                continue
            
            # Check for senior role indicators
            has_senior_indicator = False
            for indicator in senior_indicators:
                if re.search(indicator, combined_text, re.IGNORECASE):
                    has_senior_indicator = True
                    break
            
            # Basic company name validation (simple text matching)
            company_mentioned = (
                company_name.lower() in combined_text or
                any(part.lower() in combined_text for part in company_name.split() if len(part) > 3)
            )
            
            # State location matching (prefer local prospects)
            location_score = self._calculate_location_score(combined_text, company_state)
            
            # Include if has senior indicator OR company is mentioned (more permissive)
            # We want to capture more prospects at this stage and filter later
            if has_senior_indicator or company_mentioned:
                # Add filtering metadata
                prospect["basic_filter"] = {
                    "passed": True,
                    "has_senior_indicator": has_senior_indicator,
                    "company_mentioned": company_mentioned,
                    "location_score": location_score,
                    "filter_reason": "Passed basic filtering"
                }
                passed.append(prospect)
            else:
                filtered_out.append({
                    "stage": "basic_filter",
                    "name": prospect.get('title', 'Unknown'),
                    "linkedin_url": prospect.get('link', ''),
                    "reason": f"No senior indicator and no company mention (senior: {has_senior_indicator}, company: {company_mentioned})"
                })
                logger.debug(f"Filtered out: {prospect.get('title')} - senior: {has_senior_indicator}, company: {company_mentioned}")

        return {"passed": passed, "filtered_out": filtered_out}
    
    def _calculate_location_score(self, combined_text: str, company_state: str = None) -> int:
        """
        Calculate location preference score (0-100)
        Higher score for prospects in the same state as the company
        """
        if not company_state:
            return 50  # Neutral score if no company state provided
        
        # Common state representations
        state_variations = self._get_state_variations(company_state)
        
        # Check for exact state matches in the text
        for variation in state_variations:
            if variation.lower() in combined_text.lower():
                return 100  # Perfect match
        
        # Check for nearby states (could expand this logic)
        # For now, just return neutral for non-matches
        return 25  # Lower preference for out-of-state
    
    def _get_state_variations(self, state: str) -> List[str]:
        """Get common variations of state names"""
        # Map of state abbreviations to full names
        state_map = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        
        variations = [state]
        
        # If it's an abbreviation, add the full name
        if state.upper() in state_map:
            variations.append(state_map[state.upper()])
        
        # If it's a full name, find and add the abbreviation
        for abbr, full_name in state_map.items():
            if state.lower() == full_name.lower():
                variations.append(abbr)
                break
        
        return variations
    
    def _combine_search_and_linkedin_data(self, search_prospects: List[Dict], linkedin_profiles: List[Dict]) -> List[Dict]:
        """Combine search results with scraped LinkedIn data"""
        enriched_prospects = []
        
        # Create lookup by LinkedIn URL
        linkedin_lookup = {}
        for profile in linkedin_profiles:
            url = profile.get("url", "")
            if url:
                linkedin_lookup[url] = profile
        
        for prospect in search_prospects:
            linkedin_url = prospect.get("link", "")
            linkedin_data = linkedin_lookup.get(linkedin_url, {})
            
            if linkedin_data:
                # Combine search data with complete LinkedIn profile
                enriched_prospect = {
                    # Original search data (preserved)
                    "search_title": prospect.get("title", ""),
                    "search_snippet": prospect.get("snippet", ""),
                    "linkedin_url": linkedin_url,
                    "target_title": prospect.get("target_title", ""),
                    "basic_filter": prospect.get("basic_filter", {}),
                    
                    # Complete LinkedIn data (real, not AI-generated)
                    "linkedin_data": linkedin_data,
                    
                    # Flag that this has complete data
                    "has_complete_data": True,
                    "data_source": "linkedin_scrape"
                }
                enriched_prospects.append(enriched_prospect)
            else:
                logger.warning(f"No LinkedIn data found for {linkedin_url}")
        
        return enriched_prospects
    
    def _advanced_filter_with_linkedin_data(self, prospects: List[Dict], company_name: str, company_city: str = None, company_state: str = None, location_filter_enabled: bool = True) -> Dict[str, List]:
        """
        Advanced filtering using complete LinkedIn data
        Still rule-based, not AI-based

        Returns:
            dict with 'passed' and 'filtered_out' lists
        """
        passed = []
        filtered_out = []

        for prospect in prospects:
            linkedin_data = prospect.get("linkedin_data", {})

            # FILTER 1: Minimum connections threshold (≥75)
            connections = linkedin_data.get("connections", 0)
            if connections and connections < 75:
                filtered_out.append({
                    "stage": "linkedin_connections",
                    "name": linkedin_data.get('name', 'Unknown'),
                    "linkedin_url": prospect.get('linkedin_url', ''),
                    "reason": f"Low connections ({connections} < 75)"
                })
                logger.info(f"Filtered out: {linkedin_data.get('name', 'Unknown')} - Low connections ({connections} < 75)")
                continue

            # Check current job title from LinkedIn
            current_title = (linkedin_data.get("job_title") or "").lower()
            current_company = (linkedin_data.get("company") or "").lower()

            # Advanced exclusion checks
            if "intern" in current_title or "student" in current_title:
                logger.debug(f"Excluded: {linkedin_data.get('name')} - intern/student title")
                continue

            # FILTER 2: Strict company validation
            company_match_result = self._validate_company_match(
                current_company,
                company_name,
                linkedin_data.get('name', 'Unknown')
            )

            if not company_match_result['is_match']:
                filtered_out.append({
                    "stage": "company_validation",
                    "name": linkedin_data.get('name', 'Unknown'),
                    "linkedin_url": prospect.get('linkedin_url', ''),
                    "reason": company_match_result['reason'],
                    "company_listed": current_company
                })
                logger.info(f"Filtered out: {linkedin_data.get('name')} - {company_match_result['reason']}")
                continue

            # FILTER 3: Location-based filtering (if enabled and location data available)
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
                        "reason": location_match_result['reason'],
                        "location_listed": linkedin_data.get('location', '')
                    })
                    logger.info(f"Filtered out: {linkedin_data.get('name')} - {location_match_result['reason']}")
                    continue
            
            # Calculate seniority score for metadata, but don't filter based on it
            # Let AI ranking determine qualification instead
            seniority_score = self._calculate_seniority_score(linkedin_data)

            # Add advanced filter metadata
            prospect["advanced_filter"] = {
                "passed": True,
                "company_match": company_match_result['is_match'],
                "seniority_score": seniority_score,
                "current_title": current_title,
                "current_company": current_company
            }

            passed.append(prospect)

        return {"passed": passed, "filtered_out": filtered_out}

    def _validate_location_match(self, prospect_location: str, company_city: str, company_state: str, prospect_name: str) -> Dict[str, Any]:
        """
        Validate if prospect location is within reasonable distance of company location

        Strategy: Allow prospects within ~50 miles of the company city.
        - Same city = always match
        - Same state = likely match (we rely on location being accurate)
        - Different state = only match if it's a border city or metro area

        Returns:
            dict with 'is_match' (bool) and 'reason' (str)
        """
        if not prospect_location or prospect_location.lower() == 'none':
            # If no location data, allow through (benefit of the doubt)
            return {'is_match': True, 'reason': 'No location data available'}

        location_lower = prospect_location.lower().strip()

        # 1. Check for exact city match (within 50 miles is basically same city area)
        if company_city and company_city.lower() in location_lower:
            return {'is_match': True, 'reason': f'Same city ({company_city})'}

        # 2. Get state variations
        state_variations = self._get_state_variations(company_state)
        state_variations_lower = [v.lower() for v in state_variations]

        # Check if prospect is in the same state (assume within reasonable distance if same state)
        state_match = any(state_var in location_lower for state_var in state_variations_lower)

        if state_match:
            # Same state - likely within commuting/operating distance
            return {'is_match': True, 'reason': f'Same state ({company_state})'}

        # 3. Check for adjacent/regional states that might be within 50 miles
        # (e.g., border cities)
        regional_matches = self._get_regional_states(company_state)
        regional_match = any(state.lower() in location_lower for state in regional_matches)

        if regional_match:
            # Adjacent state - could be border city within 50 miles
            return {'is_match': True, 'reason': 'Adjacent state (possible border city)'}

        # 4. Check for major metro areas that span states (e.g., DC/MD/VA)
        metro_areas = {
            'maryland': ['washington', 'dc', 'district of columbia', 'virginia', 'falls church'],
            'virginia': ['washington', 'dc', 'district of columbia', 'maryland'],
            'pennsylvania': ['philadelphia', 'delaware', 'new jersey'],
            'oregon': ['washington', 'vancouver'],  # Portland metro spans OR/WA
            'washington': ['oregon', 'portland'],
        }

        if company_state.lower() in metro_areas:
            metro_keywords = metro_areas[company_state.lower()]
            metro_match = any(keyword in location_lower for keyword in metro_keywords)

            if metro_match:
                return {'is_match': True, 'reason': 'Metro area spans state border'}

        # No match - prospect is clearly too far away (different state, not adjacent)
        return {
            'is_match': False,
            'reason': f"Location too far: '{prospect_location}' vs '{company_city}, {company_state}'"
        }

    def _get_regional_states(self, state: str) -> List[str]:
        """Get adjacent/regional states that might be acceptable"""
        # Regional groupings for healthcare systems (they often span nearby states)
        regions = {
            'maryland': ['Virginia', 'DC', 'District of Columbia', 'Delaware', 'Pennsylvania'],
            'virginia': ['Maryland', 'DC', 'District of Columbia', 'North Carolina'],
            'pennsylvania': ['New Jersey', 'Delaware', 'Maryland', 'Ohio'],
            'new york': ['New Jersey', 'Connecticut', 'Pennsylvania'],
            'california': [],  # California hospitals usually don't span states
            'texas': [],  # Texas is large enough to not need adjacent states
            'florida': [],
            'illinois': ['Indiana', 'Wisconsin'],
            'ohio': ['Pennsylvania', 'Indiana', 'Michigan'],
        }

        return regions.get(state.lower(), [])

    def _validate_company_match(self, current_company: str, target_company: str, prospect_name: str) -> Dict[str, Any]:
        """
        Flexible company validation with focus on location proximity over exact name match

        Strategy: If prospect's company shares the main identifier (e.g., "Providence")
        with target company, allow it through. Location filtering will handle geographic relevance.

        Returns:
            dict with 'is_match' (bool) and 'reason' (str)
        """
        if not current_company:
            return {'is_match': False, 'reason': 'No company listed'}

        current_lower = current_company.lower().strip()
        target_lower = target_company.lower().strip()

        # Exact match
        if current_lower == target_lower:
            return {'is_match': True, 'reason': 'Exact match'}

        # Get base company names (remove common suffixes)
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

        # Exact base match
        if current_base == target_base:
            return {'is_match': True, 'reason': 'Base name match'}

        # FLEXIBLE MATCHING: Check if main company identifier matches
        # E.g., "Providence" in both "Providence Health & Services" and "Providence Medford Medical Center"
        target_words = [w for w in target_base.split() if len(w) > 4]  # Significant words only

        if target_words:
            # Get the main identifier (usually first significant word)
            main_identifier = target_words[0]

            # If the main identifier appears in current company, it's likely a match
            # Examples:
            # - "Providence Health & Services" matches "Providence Medford Medical Center" (both have "Providence")
            # - "MedStar Health" matches "MedStar Georgetown Hospital" (both have "MedStar")
            # - But "MedStar Mobile Healthcare" would NOT match because location filter will catch it

            if main_identifier in current_base:
                return {'is_match': True, 'reason': f'Shared main identifier ({main_identifier}) - location will validate geographic fit'}

        # Check for division/subsidiary patterns
        # E.g., "MedStar Georgetown University Hospital" should match "MedStar Health"
        subsidiary_indicators = [
            "university", "medical center", "hospital", "institute",
            "foundation", "research", "regional", "community", "medical group"
        ]

        has_subsidiary_indicator = any(ind in current_lower for ind in subsidiary_indicators)

        if has_subsidiary_indicator and target_words:
            # If current company has a subsidiary indicator and shares ANY significant word with target
            for word in target_words:
                if word in current_base:
                    return {'is_match': True, 'reason': f'Division/subsidiary ({word})'}

        # No match
        return {
            'is_match': False,
            'reason': f"Company mismatch: '{current_company}' vs '{target_company}'"
        }

    def _generate_company_variations(self, company_name: str) -> List[str]:
        """Generate common variations of company name for matching"""
        variations = [company_name]
        
        # Add common variations
        name_parts = company_name.split()
        if len(name_parts) > 1:
            variations.append(" ".join(name_parts[:-1]))  # Remove last word
            variations.append(name_parts[0])  # First word only
        
        # Common healthcare suffixes
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
    
    def _calculate_seniority_score(self, linkedin_data: Dict) -> int:
        """Calculate seniority score based on LinkedIn data (0-100)"""
        score = 0
        
        title = linkedin_data.get("job_title", "").lower()
        
        # Senior title indicators (more inclusive)
        senior_keywords = {
            "ceo": 100, "cfo": 95, "coo": 95, "chief": 90,
            "president": 85, "vp": 80, "vice president": 80,
            "director": 70, "head": 65, "lead": 60,
            "manager": 50, "senior": 45, "principal": 45,
            "supervisor": 40, "coordinator": 30, "specialist": 28,
            "engineer": 26, "consultant": 26, "analyst": 25
        }
        
        for keyword, points in senior_keywords.items():
            if keyword in title:
                score = max(score, points)
        
        # Experience bonus
        experience_years = linkedin_data.get("total_experience_years", 0) or 0
        if isinstance(experience_years, (int, float)) and experience_years >= 10:
            score += 15
        elif isinstance(experience_years, (int, float)) and experience_years >= 5:
            score += 10
        elif isinstance(experience_years, (int, float)) and experience_years >= 3:
            score += 5
        
        # Authority score bonus
        authority_score = linkedin_data.get("professional_authority_score", 0) or 0
        if isinstance(authority_score, (int, float)):
            score += min(authority_score // 10, 15)  # Max 15 bonus points
        
        return min(score, 100)
    
    async def _ai_title_filter_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """
        AI-powered job title filtering to remove irrelevant prospects
        Uses the same scoring logic as AI ranking but filters early
        
        Args:
            prospects: List of prospects to filter
            company_name: Target company name
            
        Returns:
            List of prospects with relevant job titles (score >= 55)
        """
        if not prospects:
            return []
        
        try:
            # Import AI ranking service to use same prompt logic
            from .improved_ai_ranking import ImprovedAIRankingService
            from app.prompts import AI_RANKING_USER_PROMPT_TEMPLATE
            
            ai_service = ImprovedAIRankingService()
            
            if not ai_service.client:
                logger.warning("OpenAI client not available - skipping title filter")
                return prospects
            
            # Score each prospect's title individually
            filtering_tasks = []
            for i, prospect in enumerate(prospects):
                task = self._score_title_relevance(prospect, company_name, ai_service, i)
                filtering_tasks.append(task)
            
            logger.info(f"Scoring {len(prospects)} prospects for title relevance...")
            scoring_results = await asyncio.gather(*filtering_tasks, return_exceptions=True)
            
            # Filter prospects based on scores
            filtered_prospects = []
            MIN_TITLE_SCORE = 55  # Minimum score to pass title filter
            
            for i, (prospect, result) in enumerate(zip(prospects, scoring_results)):
                if isinstance(result, Exception):
                    logger.error(f"Error scoring prospect {i}: {result}")
                    # Keep prospect on error (benefit of doubt)
                    filtered_prospects.append(prospect)
                    continue
                
                if isinstance(result, dict) and result.get("success"):
                    score = result.get("score", 0)
                    reasoning = result.get("reasoning", "")
                    
                    # Add title filter metadata
                    prospect["ai_title_filter"] = {
                        "score": score,
                        "reasoning": reasoning,
                        "passed": score >= MIN_TITLE_SCORE
                    }
                    
                    if score >= MIN_TITLE_SCORE:
                        filtered_prospects.append(prospect)
                        logger.debug(f"✓ Passed: {prospect.get('title', 'Unknown')} - Score: {score}")
                    else:
                        logger.info(f"✗ Filtered: {prospect.get('title', 'Unknown')} - Score: {score} - {reasoning}")
                else:
                    # Keep on error
                    logger.warning(f"No valid score for prospect {i} - keeping by default")
                    filtered_prospects.append(prospect)
            
            logger.info(f"Title filter: {len(filtered_prospects)}/{len(prospects)} passed (score >= {MIN_TITLE_SCORE})")
            return filtered_prospects
            
        except Exception as e:
            logger.error(f"Error in title filtering: {str(e)}")
            # Return all prospects on error
            return prospects
    
    async def _score_title_relevance(self, prospect: Dict, company_name: str, ai_service, index: int) -> Dict[str, Any]:
        """
        Score a single prospect's title relevance using AI
        
        Args:
            prospect: Prospect with title and snippet
            company_name: Target company name
            ai_service: AI ranking service instance
            index: Prospect index for tracking
            
        Returns:
            Dict with success, score, and reasoning
        """
        try:
            from app.prompts import AI_RANKING_USER_PROMPT_TEMPLATE
            
            title = prospect.get("title", "")
            snippet = prospect.get("snippet", "")
            
            # Extract basic info from search result
            # Title format is usually: "Name - Job Title at Company"
            parts = title.split(" - ")
            name = parts[0] if len(parts) > 0 else "Unknown"
            job_title = parts[1] if len(parts) > 1 else title
            
            # Build prompt using same template as ranking
            prompt = AI_RANKING_USER_PROMPT_TEMPLATE.format(
                company_name=company_name,
                name=name,
                title=job_title,
                company=company_name,
                summary=snippet[:300],
                skills="N/A (search result)",
                experience_years="N/A"
            )
            
            # Combine system prompt with user prompt
            from app.prompts import AI_RANKING_SYSTEM_PROMPT
            full_input = f"{AI_RANKING_SYSTEM_PROMPT}\n\n{prompt}"
            
            # Use Responses API like in ranking service
            api_params = {
                "model": ai_service.model,
                "input": full_input,
                "text": {"format": {"type": "json_object"}},
                "max_output_tokens": 300,
                "timeout": 20
            }

            # Only add reasoning parameter for gpt-5 or o-series models
            # Note: temperature is NOT supported in Responses API for GPT-5/o-series
            if "gpt-5" in ai_service.model or ai_service.model.startswith("o"):
                api_params["reasoning"] = {"effort": "minimal"}  # Fast for filtering
            
            response = ai_service.client.responses.create(**api_params)

            # Parse response with proper error handling
            import json

            # Check if response is valid
            if not response or not hasattr(response, 'output') or not response.output:
                return {
                    "success": False,
                    "index": index,
                    "error": "Invalid response structure from API"
                }

            try:
                output_text = response.output[0].content[0].text
            except (IndexError, AttributeError, TypeError) as e:
                return {
                    "success": False,
                    "index": index,
                    "error": f"Error accessing response fields: {type(e).__name__}: {str(e)}"
                }

            result_data = json.loads(output_text)
            
            if "score" in result_data:
                return {
                    "success": True,
                    "index": index,
                    "score": int(result_data["score"]),
                    "reasoning": result_data.get("reasoning", "")
                }
            else:
                return {
                    "success": False,
                    "index": index,
                    "error": "Missing score in response"
                }
                
        except Exception as e:
            logger.error(f"Error scoring title for prospect {index}: {str(e)}")
            return {
                "success": False,
                "index": index,
                "error": str(e)
            }
    
    async def _ai_basic_filter_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """
        Simple rule-based filtering to validate company match and connection count
        This should be MORE permissive to allow more prospects through
        """
        if not prospects:
            return []

        filtered = []

        for prospect in prospects:
            title = prospect.get("title", "").lower()
            snippet = prospect.get("snippet", "").lower()
            combined_text = f"{title} {snippet}"

            # Extract connection count from snippet if available (e.g., "500+ connections")
            connection_count = 0
            connection_match = re.search(r'(\d+)\+?\s*connections?', snippet, re.IGNORECASE)
            if connection_match:
                connection_count = int(connection_match.group(1))

            # Check for spam indicators (very low connection count < 75)
            if connection_count > 0 and connection_count < 75:
                logger.debug(f"Filtered out low connection account: {prospect.get('title')} - {connection_count} connections")
                continue

            # Verify company is mentioned (flexible matching)
            company_variations = self._generate_company_variations(company_name)
            company_match = any(
                variation.lower() in combined_text for variation in company_variations
            )

            if not company_match:
                # Try partial word matching
                company_parts = [part.strip() for part in company_name.split() if len(part) > 3]
                company_match = any(
                    part.lower() in combined_text for part in company_parts
                )

            # Only filter out if company is clearly NOT mentioned
            if company_match or connection_count >= 75:
                prospect["ai_basic_filter"] = {
                    "passed": True,
                    "company_match": company_match,
                    "connection_count": connection_count if connection_count > 0 else "Unknown",
                    "company_match_confidence": 100 if company_match else 50
                }
                filtered.append(prospect)
            else:
                logger.debug(f"Filtered out: {prospect.get('title')} - no company match and low/unknown connections")

        return filtered

    def _group_filtered_by_stage(self, filtered_list: List[Dict]) -> Dict[str, int]:
        """Group filtered prospects by stage and count them"""
        stage_counts = {}
        for item in filtered_list:
            stage = item.get('stage', 'unknown')
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        return stage_counts

    async def _ai_rank_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """
        Use AI ONLY for ranking prospects based on complete LinkedIn data
        AI does NOT create or modify data - only ranks it
        """
        if not prospects:
            return []
        
        try:
            # Import AI service here to avoid circular imports
            from .improved_ai_ranking import ImprovedAIRankingService
            ai_service = ImprovedAIRankingService()
            
            ranking_result = await ai_service.rank_prospects(prospects, company_name)
            
            if ranking_result.get("success"):
                return ranking_result.get("ranked_prospects", prospects)
            else:
                logger.warning(f"AI ranking failed: {ranking_result.get('error')}")
                # Return prospects with default ranking if AI fails
                return prospects
                
        except ImportError:
            logger.warning("AI ranking service not available - returning unranked prospects")
            return prospects
        except Exception as e:
            logger.error(f"Error in AI ranking: {str(e)}")
            return prospects


# Global instance
improved_prospect_discovery_service = ImprovedProspectDiscoveryService()
