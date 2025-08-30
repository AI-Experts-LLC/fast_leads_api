"""
LinkedIn scraping service using Apify

Based on the official example code:
```python
from apify_client import ApifyClient

# Initialize the ApifyClient with your Apify API token
client = ApifyClient("<YOUR_API_TOKEN>")

# Prepare the Actor input
run_input = { "profileUrls": [
    "https://www.linkedin.com/in/williamhgates",
    "http://www.linkedin.com/in/jeannie-wyrick-b4760710a",
] }

# Run the Actor and wait for it to finish
run = client.actor("dev_fusion/linkedin-profile-scraper").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
print("💾 Check your data here: https://console.apify.com/storage/datasets/" + run["defaultDatasetId"])
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```
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
            
            # Prepare the Actor input (matching example code structure)
            run_input = {
                "profileUrls": linkedin_urls[:10]  # Limit to 10 profiles to control costs
            }
            
            # Run the Actor and wait for it to finish (matching example code)
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            # Log dataset URL for debugging (matching example code pattern)
            logger.info(f"💾 Check your data here: https://console.apify.com/storage/datasets/{run['defaultDatasetId']}")
            
            # Fetch and process Actor results from the run's dataset (matching example code)
            profiles = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
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
        """Test the scraping functionality with sample profiles (matching example code)"""
        if not self.client:
            return {
                "success": False,
                "error": "Apify client not configured"
            }
        
        # Test with the exact same profiles as the example code
        test_urls = [
            "https://www.linkedin.com/in/williamhgates",
            "http://www.linkedin.com/in/jeannie-wyrick-b4760710a"
        ]
        
        try:
            result = await self.scrape_profiles(test_urls)
            return {
                "success": result.get("success", False),
                "test_urls": test_urls,
                "profiles_scraped": result.get("profiles_scraped", 0),
                "sample_profiles": result.get("profiles", []) if result.get("profiles") else [],
                "dataset_url": f"https://console.apify.com/storage/datasets/{result.get('run_id', 'unknown')}" if result.get("run_id") else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
linkedin_service = ApifyLinkedInService()
