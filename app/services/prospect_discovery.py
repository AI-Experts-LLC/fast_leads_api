"""
Prospect Discovery Service
Orchestrates the complete prospect discovery pipeline:
1. Search for LinkedIn profiles using Serper
2. Qualify prospects using OpenAI
3. Scrape LinkedIn data using Apify
4. Generate personalized outreach messages
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
from .search import serper_service
from .ai_qualification import ai_qualification_service
from .linkedin import linkedin_service
from .company_validation import company_validation_service

logger = logging.getLogger(__name__)


class ProspectDiscoveryService:
    """Main service for discovering and qualifying prospects"""
    
    def __init__(self):
        self.search_service = serper_service
        self.ai_service = ai_qualification_service
        self.linkedin_service = linkedin_service
        self.validation_service = company_validation_service
    
    async def discover_prospects(self, company_name: str, target_titles: List[str] = None) -> Dict[str, Any]:
        """
        Complete prospect discovery pipeline
        
        Args:
            company_name: Name of the target company
            target_titles: Optional list of specific job titles to search for
        
        Returns:
            Dictionary with discovered prospects and their LinkedIn data
        """
        try:
            logger.info(f"Starting prospect discovery for: {company_name}")
            
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
            
            # Step 2: Company validation - ensure prospects currently work at target company
            logger.info("Step 2: Validating current employment at target company...")
            validation_result = await self.validation_service.validate_current_employment(
                prospects=search_results,
                target_company=company_name
            )
            
            if not validation_result.get("success"):
                logger.warning(f"Company validation failed: {validation_result.get('error')}")
                # Continue with original results if validation fails
                validated_prospects = search_results
            else:
                validated_prospects = validation_result.get("validated_prospects", [])
                logger.info(f"Validated {len(validated_prospects)} prospects as currently employed at {company_name}")
            
            if not validated_prospects:
                return {
                    "success": True,
                    "message": "No prospects found who currently work at the target company",
                    "search_results": len(search_results),
                    "validated_prospects": [],
                    "validation_summary": validation_result.get("validation_details", {})
                }
            
            # Step 3: AI qualification of validated prospects
            logger.info("Step 3: AI qualification of validated prospects...")
            qualification_result = await self.ai_service.qualify_prospects(
                search_results=validated_prospects,
                company_name=company_name
            )
            
            if not qualification_result.get("success"):
                return {
                    "success": False,
                    "error": f"AI qualification failed: {qualification_result.get('error')}",
                    "step_failed": "qualification"
                }
            
            qualified_prospects = qualification_result.get("qualified_prospects", [])
            if not qualified_prospects:
                return {
                    "success": True,
                    "message": "No prospects met qualification criteria",
                    "search_results": len(search_results),
                    "validated_prospects": len(validated_prospects),
                    "qualified_prospects": [],
                    "qualification_summary": qualification_result.get("ai_analysis", {}),
                    "validation_summary": validation_result.get("validation_details", {})
                }
            
            logger.info(f"Qualified {len(qualified_prospects)} prospects")
            
            # Step 4: LinkedIn data scraping for top prospects
            logger.info("Step 4: Scraping LinkedIn data for top prospects...")
            top_prospects = qualified_prospects[:5]  # Limit to top 5 to control costs
            linkedin_urls = [p.get("link") for p in top_prospects if p.get("link")]
            
            linkedin_result = await self.linkedin_service.scrape_profiles(linkedin_urls)
            
            if not linkedin_result.get("success"):
                logger.warning(f"LinkedIn scraping failed: {linkedin_result.get('error')}")
                # Continue without LinkedIn data
                linkedin_profiles = []
            else:
                linkedin_profiles = linkedin_result.get("profiles", [])
                logger.info(f"Scraped {len(linkedin_profiles)} LinkedIn profiles")
            
            # Step 5: Combine all data and generate final results
            logger.info("Step 5: Combining data and generating results...")
            final_prospects = await self._combine_prospect_data(
                qualified_prospects=qualified_prospects,
                linkedin_profiles=linkedin_profiles,
                company_name=company_name
            )
            
            return {
                "success": True,
                "company_name": company_name,
                "pipeline_summary": {
                    "search_results_found": len(search_results),
                    "prospects_validated": len(validated_prospects),
                    "prospects_qualified": len(qualified_prospects),
                    "linkedin_profiles_scraped": len(linkedin_profiles),
                    "final_prospects": len(final_prospects)
                },
                "qualified_prospects": final_prospects,
                "ai_analysis": qualification_result.get("ai_analysis", {}),
                "validation_summary": validation_result.get("validation_details", {}),
                "cost_estimates": {
                    "search_cost": 0.01 * len(search_results[:10]),  # Estimate
                    "validation_cost": validation_result.get("cost_estimate", 0.015) if validation_result.get("success") else 0,
                    "ai_cost": qualification_result.get("cost_estimate", 0.02),
                    "linkedin_cost": linkedin_result.get("cost_estimate", 0) if linkedin_result.get("success") else 0,
                    "total_estimated": 0.01 * len(search_results[:10]) + (validation_result.get("cost_estimate", 0.015) if validation_result.get("success") else 0) + 0.02 + (linkedin_result.get("cost_estimate", 0) if linkedin_result.get("success") else 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prospect discovery pipeline: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "step_failed": "pipeline"
            }
    
    async def _combine_prospect_data(self, qualified_prospects: List[Dict], linkedin_profiles: List[Dict], company_name: str) -> List[Dict]:
        """Combine qualification data with LinkedIn profile data"""
        combined_prospects = []
        
        # Create a lookup dict for LinkedIn profiles by URL
        linkedin_lookup = {}
        for profile in linkedin_profiles:
            url = profile.get("url", "")
            if url:
                linkedin_lookup[url] = profile
        
        for prospect in qualified_prospects:
            linkedin_url = prospect.get("link", "")
            linkedin_data = linkedin_lookup.get(linkedin_url, {})
            
            # Combine prospect qualification with LinkedIn data
            combined_prospect = {
                # Qualification data
                "qualification_score": prospect.get("qualification_score", 0),
                "persona_match": prospect.get("persona_match", ""),
                "decision_authority": prospect.get("decision_authority", ""),
                "priority_rank": prospect.get("priority_rank", 0),
                "ai_reasoning": prospect.get("ai_reasoning", ""),
                "pain_points": prospect.get("pain_points", []),
                "outreach_approach": prospect.get("outreach_approach", ""),
                
                # Original search data
                "search_title": prospect.get("title", ""),
                "search_snippet": prospect.get("snippet", ""),
                "linkedin_url": linkedin_url,
                "target_title": prospect.get("target_title", ""),
                
                # LinkedIn profile data (if available)
                "linkedin_data": {
                    # Basic information
                    "name": linkedin_data.get("name"),
                    "first_name": linkedin_data.get("first_name"),
                    "last_name": linkedin_data.get("last_name"),
                    "headline": linkedin_data.get("headline"),
                    "location": linkedin_data.get("location"),
                    "summary": linkedin_data.get("summary"),
                    
                    # Professional details
                    "job_title": linkedin_data.get("job_title"),
                    "company": linkedin_data.get("company"),
                    "company_industry": linkedin_data.get("company_industry"),
                    "company_website": linkedin_data.get("company_website"),
                    "company_size": linkedin_data.get("company_size"),
                    "current_job_duration": linkedin_data.get("current_job_duration"),
                    "current_job_duration_years": linkedin_data.get("current_job_duration_years"),
                    
                    # Network metrics
                    "connections": linkedin_data.get("connections"),
                    "followers": linkedin_data.get("followers"),
                    
                    # Skills and experience
                    "top_skills": linkedin_data.get("top_skills_by_endorsements"),
                    "experience_count": linkedin_data.get("experience_count", 0),
                    "education_count": linkedin_data.get("education_count", 0),
                    "skills_count": linkedin_data.get("skills_count", 0),
                    
                    # Structured data (summary for response size management)
                    "recent_experience": linkedin_data.get("experience", [])[:3] if linkedin_data.get("experience") else [],
                    "education": linkedin_data.get("education", [])[:2] if linkedin_data.get("education") else [],
                    "key_skills": linkedin_data.get("skills", [])[:10] if linkedin_data.get("skills") else [],
                    
                    # Meta information
                    "has_detailed_data": bool(linkedin_data),
                    "data_source": linkedin_data.get("data_source", "unknown")
                },
                
                # Generated data
                "company_name": company_name,
                "discovery_timestamp": None  # Would add timestamp in real implementation
            }
            
            combined_prospects.append(combined_prospect)
        
        return combined_prospects
    
    async def generate_outreach_messages(self, prospects: List[Dict]) -> Dict[str, Any]:
        """Generate personalized outreach messages for discovered prospects"""
        try:
            messages = []
            
            for prospect in prospects[:3]:  # Limit to top 3 for cost control
                company_context = {"name": prospect.get("company_name", "")}
                
                message_result = await self.ai_service.generate_personalized_message(
                    prospect=prospect,
                    company_context=company_context
                )
                
                if message_result.get("success"):
                    messages.append({
                        "prospect": {
                            "name": prospect.get("linkedin_data", {}).get("name", "Professional"),
                            "title": prospect.get("persona_match", ""),
                            "linkedin_url": prospect.get("linkedin_url", "")
                        },
                        "message_data": message_result.get("personalized_message", {}),
                        "qualification_score": prospect.get("qualification_score", 0)
                    })
            
            return {
                "success": True,
                "messages_generated": len(messages),
                "personalized_messages": messages
            }
            
        except Exception as e:
            logger.error(f"Error generating outreach messages: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_services(self) -> Dict[str, Any]:
        """Test all component services"""
        results = {}
        
        # Test search service
        try:
            search_test = await self.search_service.test_search()
            results["search_service"] = search_test
        except Exception as e:
            results["search_service"] = {"success": False, "error": str(e)}
        
        # Test validation service
        try:
            validation_test = await self.validation_service.test_validation()
            results["validation_service"] = validation_test
        except Exception as e:
            results["validation_service"] = {"success": False, "error": str(e)}
        
        # Test AI service
        try:
            ai_test = await self.ai_service.test_qualification()
            results["ai_service"] = ai_test
        except Exception as e:
            results["ai_service"] = {"success": False, "error": str(e)}
        
        # Test LinkedIn service
        try:
            linkedin_test = await self.linkedin_service.test_scraping()
            results["linkedin_service"] = linkedin_test
        except Exception as e:
            results["linkedin_service"] = {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "service_tests": results,
            "all_services_working": all(test.get("success", False) for test in results.values())
        }


# Global instance
prospect_discovery_service = ProspectDiscoveryService()
