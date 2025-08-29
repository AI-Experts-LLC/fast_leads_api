"""
LinkedIn scraping service using Apify
"""

import os
import logging
from typing import List, Dict, Any, Optional
from apify_client import ApifyClient
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LinkedInProfile:
    """Data class for LinkedIn profile data"""
    url: str
    name: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    experience: Optional[List[Dict]] = None
    education: Optional[List[Dict]] = None
    skills: Optional[List[str]] = None
    raw_data: Optional[Dict] = None


class ApifyLinkedInService:
    """Service for scraping LinkedIn profiles using Apify"""
    
    def __init__(self):
        self.api_token = os.getenv('APIFY_API_TOKEN')
        self.actor_id = "dev_fusion/linkedin-profile-scraper"  # LinkedIn Profile Scraper
        
        if self.api_token:
            self.client = ApifyClient(self.api_token)
        else:
            self.client = None
            logger.warning("APIFY_API_TOKEN not found in environment variables")
    
    async def scrape_profiles(self, linkedin_urls: List[str]) -> Dict[str, Any]:
        """
        Scrape multiple LinkedIn profiles
        
        Args:
            linkedin_urls: List of LinkedIn profile URLs to scrape
        
        Returns:
            Dictionary with scraped profile data
        """
        if not self.client:
            return {
                "success": False,
                "error": "Apify client not configured - missing API token"
            }
        
        if not linkedin_urls:
            return {
                "success": False,
                "error": "No LinkedIn URLs provided"
            }
        
        try:
            logger.info(f"Starting to scrape {len(linkedin_urls)} LinkedIn profiles")
            
            # Prepare the Actor input
            run_input = {
                "profileUrls": linkedin_urls[:10],  # Limit to 10 profiles to control costs
                "fastMode": True,  # Use fast mode for basic info
                "saveToTxt": False,
                "saveToJson": True
            }
            
            # Run the Actor and wait for completion (synchronous within async function)
            run = self.client.actor(self.actor_id).call(run_input=run_input, timeout=300)
            
            # Fetch results from the dataset (synchronous within async function)
            profiles = []
            dataset_items = self.client.dataset(run["defaultDatasetId"]).iterate_items()
            
            for item in dataset_items:
                profile = self._parse_profile_data(item)
                if profile:
                    profiles.append(profile)
            
            logger.info(f"Successfully scraped {len(profiles)} profiles")
            
            return {
                "success": True,
                "profiles_requested": len(linkedin_urls),
                "profiles_scraped": len(profiles),
                "profiles": [self._profile_to_dict(p) for p in profiles],
                "run_id": run.get("id"),
                "cost_estimate": len(linkedin_urls) * 0.15  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn profiles: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_profile_data(self, raw_data: Dict[str, Any]) -> Optional[LinkedInProfile]:
        """Parse raw Apify data into LinkedInProfile object"""
        try:
            if not raw_data:
                return None
            
            # Extract experience data
            experience = []
            if raw_data.get('experience'):
                for exp in raw_data.get('experience', []):
                    experience.append({
                        'title': exp.get('title'),
                        'company': exp.get('companyName'),
                        'duration': exp.get('duration'),
                        'description': exp.get('description')
                    })
            
            # Extract education data
            education = []
            if raw_data.get('education'):
                for edu in raw_data.get('education', []):
                    education.append({
                        'school': edu.get('schoolName'),
                        'degree': edu.get('degreeName'),
                        'field': edu.get('fieldOfStudy')
                    })
            
            return LinkedInProfile(
                url=raw_data.get('url', ''),
                name=raw_data.get('fullName'),
                headline=raw_data.get('headline'),
                company=raw_data.get('company'),
                location=raw_data.get('location'),
                summary=raw_data.get('summary'),
                experience=experience,
                education=education,
                skills=raw_data.get('skills', []),
                raw_data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing profile data: {str(e)}")
            return None
    
    def _profile_to_dict(self, profile: LinkedInProfile) -> Dict[str, Any]:
        """Convert LinkedInProfile to dictionary"""
        return {
            'url': profile.url,
            'name': profile.name,
            'headline': profile.headline,
            'company': profile.company,
            'location': profile.location,
            'summary': profile.summary,
            'experience': profile.experience,
            'education': profile.education,
            'skills': profile.skills,
            'experience_count': len(profile.experience) if profile.experience else 0,
            'education_count': len(profile.education) if profile.education else 0,
            'skills_count': len(profile.skills) if profile.skills else 0
        }
    
    async def test_scraping(self) -> Dict[str, Any]:
        """Test the scraping functionality with a sample profile"""
        if not self.client:
            return {
                "success": False,
                "error": "Apify client not configured"
            }
        
        # Test with a public LinkedIn profile
        test_urls = ["https://www.linkedin.com/in/williamhgates"]
        
        try:
            result = await self.scrape_profiles(test_urls)
            return {
                "success": result.get("success", False),
                "test_url": test_urls[0],
                "profiles_scraped": result.get("profiles_scraped", 0),
                "sample_profile": result.get("profiles", [{}])[0] if result.get("profiles") else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
linkedin_service = ApifyLinkedInService()
