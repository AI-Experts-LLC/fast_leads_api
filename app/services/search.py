"""
Search service for finding LinkedIn profiles using Serper API
"""

import os
import logging
from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Data class for search results"""
    title: str
    link: str
    snippet: str
    position: int


class SerperSearchService:
    """Service for searching LinkedIn profiles using Serper API"""
    
    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY')
        self.base_url = "https://google.serper.dev/search"
        
        if not self.api_key:
            logger.warning("SERPER_API_KEY not found in environment variables")
    
    async def search_linkedin_profiles(self, company_name: str, target_titles: List[str] = None, company_city: str = None, company_state: str = None) -> Dict[str, Any]:
        """
        Search for LinkedIn profiles at a specific company

        Args:
            company_name: Name of the company to search
            target_titles: List of job titles to search for (optional)
            company_city: City where company is located (optional, improves search accuracy)
            company_state: State where company is located (optional, improves search accuracy)

        Returns:
            Dictionary with search results and metadata
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Serper API key not configured"
            }

        try:
            # Default target titles if none provided
            # Based on buyer_persona.md: Primary decision-makers for energy infrastructure projects
            if not target_titles:
                target_titles = [
                    # Primary decision-makers (Directors & VPs)
                    "Director of Facilities",
                    "Director of Engineering",
                    "Director of Maintenance",
                    "VP Facilities",
                    "VP Operations",

                    # Financial decision-makers
                    "Chief Financial Officer",
                    "Chief Operating Officer",

                    # Manager-level contacts
                    "Facilities Manager",
                    "Energy Manager",
                    "Plant Manager",
                    "Maintenance Manager"
                ]

            all_results = []

            # Build location string for search query
            location_str = ""
            if company_city and company_state:
                location_str = f"{company_city} {company_state} "
            elif company_state:
                location_str = f"{company_state} "

            # Search for each target title
            for title in target_titles:
                # Format: "Company City State Title site:linkedin.com/in"
                search_query = f'{company_name} {location_str}{title} site:linkedin.com/in'

                logger.info(f"Searching: {search_query}")
                
                results = await self._perform_search(search_query)
                if results.get("success"):
                    # OPTIMIZED: Limit to first 3 per title (reduced from 5)
                    title_results = results.get("results", [])[:3]
                    for result in title_results:
                        result["target_title"] = title
                    all_results.extend(title_results)

                # No delay needed when running in parallel
                # await asyncio.sleep(0.1)
            
            # Remove duplicates based on LinkedIn URL
            unique_results = self._deduplicate_results(all_results)
            
            return {
                "success": True,
                "company_name": company_name,
                "total_results": len(unique_results),
                "results": unique_results,  # Limit to top 20 results
                "target_titles_searched": target_titles
            }
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn profiles: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _perform_search(self, query: str) -> Dict[str, Any]:
        """Perform a single search request to Serper API"""
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': query,
            'num': 10  # Number of results per search
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse organic results
                        organic_results = data.get('organic', [])
                        
                        search_results = []
                        for i, result in enumerate(organic_results):
                            if 'linkedin.com/in/' in result.get('link', ''):
                                search_results.append({
                                    'title': result.get('title', ''),
                                    'link': result.get('link', ''),
                                    'snippet': result.get('snippet', ''),
                                    'position': i + 1
                                })
                        
                        return {
                            "success": True,
                            "results": search_results,
                            "query": query
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Serper API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"API request failed with status {response.status}"
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout searching for: {query}")
            return {
                "success": False,
                "error": "Search request timed out"
            }
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate LinkedIn URLs from results"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('link', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def test_search(self) -> Dict[str, Any]:
        """Test the search functionality with a simple query"""
        if not self.api_key:
            return {
                "success": False,
                "error": "Serper API key not configured"
            }
        
        test_query = 'Microsoft CFO site:linkedin.com/in'
        
        try:
            result = await self._perform_search(test_query)
            return {
                "success": result.get("success", False),
                "test_query": test_query,
                "results_count": len(result.get("results", [])),
                "sample_results": result.get("results", [])[:3]  # First 3 results
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
serper_service = SerperSearchService()
