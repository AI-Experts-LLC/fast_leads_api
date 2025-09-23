"""
IMPROVED Prospect Discovery Service
Fixes accuracy issues by:
1. Basic filtering BEFORE AI involvement
2. LinkedIn scraping BEFORE AI qualification  
3. AI only ranks real data, doesn't create data
"""

import logging
import re
from typing import Dict, Any, List, Optional
import asyncio
from .search import serper_service
from .linkedin import linkedin_service

logger = logging.getLogger(__name__)


class ImprovedProspectDiscoveryService:
    """Improved prospect discovery with better accuracy"""
    
    def __init__(self):
        self.search_service = serper_service
        self.linkedin_service = linkedin_service
    
    async def discover_prospects(self, company_name: str, target_titles: List[str] = None) -> Dict[str, Any]:
        """
        Improved prospect discovery pipeline
        
        Args:
            company_name: Name of the target company
            target_titles: Optional list of specific job titles to search for
        
        Returns:
            Dictionary with discovered prospects and their complete LinkedIn data
        """
        try:
            logger.info(f"Starting IMPROVED prospect discovery for: {company_name}")
            
            # Step 1: Search for LinkedIn profiles
            logger.info("Step 1: Searching for LinkedIn profiles...")
            search_result = await self.search_service.search_linkedin_profiles(
                company_name=company_name,
                target_titles=target_titles
            )
            
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
            
            # Step 2: Basic data filtering (NO AI - just rule-based filtering)
            logger.info("Step 2: Basic data filtering...")
            filtered_prospects = self._basic_filter_prospects(search_results, company_name)
            logger.info(f"Filtered to {len(filtered_prospects)} prospects after removing obvious mismatches")
            
            if not filtered_prospects:
                return {
                    "success": True,
                    "message": "No prospects passed basic filtering",
                    "search_results": len(search_results),
                    "filtered_prospects": [],
                    "filter_summary": {"removed_prospects": len(search_results)}
                }
            
            # Step 3: LinkedIn scraping (GET REAL DATA FIRST)
            logger.info("Step 3: Scraping complete LinkedIn data...")
            linkedin_urls = [p.get("link") for p in filtered_prospects if p.get("link")]
            
            linkedin_result = await self.linkedin_service.scrape_profiles(linkedin_urls)
            
            if not linkedin_result.get("success"):
                return {
                    "success": False,
                    "error": f"LinkedIn scraping failed: {linkedin_result.get('error')}",
                    "step_failed": "scraping"
                }
            
            linkedin_profiles = linkedin_result.get("profiles", [])
            logger.info(f"Successfully scraped {len(linkedin_profiles)} complete LinkedIn profiles")
            
            # Step 4: Combine search results with scraped LinkedIn data
            logger.info("Step 4: Combining search results with LinkedIn data...")
            enriched_prospects = self._combine_search_and_linkedin_data(
                filtered_prospects, linkedin_profiles
            )
            
            # Step 5: FINAL filtering based on complete LinkedIn data
            logger.info("Step 5: Final filtering based on complete LinkedIn data...")
            final_prospects = self._advanced_filter_with_linkedin_data(
                enriched_prospects, company_name
            )
            
            # Step 6: AI ranking (ONLY ranking, no data modification)
            logger.info("Step 6: AI ranking of validated prospects...")
            ranked_prospects = await self._ai_rank_prospects(final_prospects, company_name)
            
            return {
                "success": True,
                "company_name": company_name,
                "pipeline_summary": {
                    "search_results_found": len(search_results),
                    "prospects_after_basic_filter": len(filtered_prospects),
                    "linkedin_profiles_scraped": len(linkedin_profiles),
                    "prospects_after_advanced_filter": len(final_prospects),
                    "final_ranked_prospects": len(ranked_prospects)
                },
                "qualified_prospects": ranked_prospects,
                "cost_estimates": {
                    "search_cost": 0.01 * len(search_results[:10]),
                    "linkedin_cost": linkedin_result.get("cost_estimate", 0),
                    "ai_ranking_cost": 0.02,  # Only for ranking, not data creation
                    "total_estimated": 0.01 * len(search_results[:10]) + linkedin_result.get("cost_estimate", 0) + 0.02
                }
            }
            
        except Exception as e:
            logger.error(f"Error in improved prospect discovery pipeline: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step_failed": "pipeline"
            }
    
    def _basic_filter_prospects(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """
        Basic rule-based filtering to remove obvious mismatches
        NO AI involved - just simple text analysis
        """
        filtered = []
        
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
            for pattern in exclusion_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    excluded = True
                    logger.debug(f"Excluded prospect: {prospect.get('title')} - matched pattern: {pattern}")
                    break
            
            if excluded:
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
            
            # Include if has senior indicator AND company is mentioned
            if has_senior_indicator and company_mentioned:
                # Add filtering metadata
                prospect["basic_filter"] = {
                    "passed": True,
                    "has_senior_indicator": has_senior_indicator,
                    "company_mentioned": company_mentioned,
                    "filter_reason": "Passed basic filtering"
                }
                filtered.append(prospect)
            else:
                logger.debug(f"Filtered out: {prospect.get('title')} - senior: {has_senior_indicator}, company: {company_mentioned}")
        
        return filtered
    
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
    
    def _advanced_filter_with_linkedin_data(self, prospects: List[Dict], company_name: str) -> List[Dict]:
        """
        Advanced filtering using complete LinkedIn data
        Still rule-based, not AI-based
        """
        filtered = []
        
        for prospect in prospects:
            linkedin_data = prospect.get("linkedin_data", {})
            
            # Check current job title from LinkedIn
            current_title = (linkedin_data.get("job_title") or "").lower()
            current_company = (linkedin_data.get("company") or "").lower()
            
            # Advanced exclusion checks
            if "intern" in current_title or "student" in current_title:
                logger.debug(f"Excluded: {linkedin_data.get('name')} - intern/student title")
                continue
            
            # Company verification using LinkedIn data
            company_variations = self._generate_company_variations(company_name)
            company_match = any(
                variation.lower() in current_company for variation in company_variations
            )
            
            if not company_match:
                logger.debug(f"Excluded: {linkedin_data.get('name')} - company mismatch: {current_company}")
                continue
            
            # Check for decision-making seniority
            seniority_score = self._calculate_seniority_score(linkedin_data)
            
            if seniority_score < 30:  # Minimum threshold for consideration
                logger.debug(f"Excluded: {linkedin_data.get('name')} - low seniority score: {seniority_score}")
                continue
            
            # Add advanced filter metadata
            prospect["advanced_filter"] = {
                "passed": True,
                "company_match": company_match,
                "seniority_score": seniority_score,
                "current_title": current_title,
                "current_company": current_company
            }
            
            filtered.append(prospect)
        
        return filtered
    
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
        
        # Senior title indicators
        senior_keywords = {
            "ceo": 100, "cfo": 95, "coo": 95, "chief": 90,
            "president": 85, "vp": 80, "vice president": 80,
            "director": 70, "head": 65, "lead": 60,
            "manager": 50, "senior": 40, "principal": 40,
            "supervisor": 35, "coordinator": 25
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
