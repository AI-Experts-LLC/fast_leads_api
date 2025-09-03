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
from apify_client import ApifyClient # type: ignore
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
            
            # Extract experience data from Apify format
            experience = []
            if raw_data.get('experiences'):
                for exp in raw_data.get('experiences', []):
                    experience.append({
                        'title': exp.get('title'),
                        'company': exp.get('subtitle', '').split(' · ')[0] if exp.get('subtitle') else None,
                        'duration': exp.get('caption'),
                        'location': exp.get('metadata'),
                        'description': exp.get('subComponents', [{}])[0].get('description', []) if exp.get('subComponents') else [],
                        'company_logo': exp.get('logo'),
                        'company_link': exp.get('companyLink1')
                    })
            
            # Extract education data from Apify format
            education = []
            if raw_data.get('educations'):
                for edu in raw_data.get('educations', []):
                    education.append({
                        'school': edu.get('title'),
                        'degree': edu.get('subtitle'),
                        'duration': edu.get('caption'),
                        'activities': edu.get('subComponents', [{}])[0].get('description', []) if edu.get('subComponents') else [],
                        'school_logo': edu.get('logo'),
                        'school_link': edu.get('companyLink1')
                    })
            
            # Extract skills data from Apify format
            skills = []
            if raw_data.get('skills'):
                for skill in raw_data.get('skills', []):
                    skill_data = {
                        'name': skill.get('title'),
                        'endorsements': []
                    }
                    
                    # Extract endorsement information
                    if skill.get('subComponents'):
                        for sub_comp in skill.get('subComponents', []):
                            for desc in sub_comp.get('description', []):
                                if desc.get('type') == 'insightComponent':
                                    skill_data['endorsements'].append(desc.get('text'))
                    
                    skills.append(skill_data)
            
            # Extract top skills by endorsements
            top_skills = raw_data.get('topSkillsByEndorsements', '').split(', ') if raw_data.get('topSkillsByEndorsements') else []
            
            return LinkedInProfile(
                url=raw_data.get('linkedinUrl', ''),
                name=raw_data.get('fullName'),
                headline=raw_data.get('headline'),
                company=raw_data.get('companyName'),
                location=raw_data.get('addressWithoutCountry') or raw_data.get('addressWithCountry'),
                summary=raw_data.get('about'),
                experience=experience,
                education=education,
                skills=skills,
                raw_data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing profile data: {str(e)}")
            return None
    
    def _profile_to_dict(self, profile: LinkedInProfile) -> Dict[str, Any]:
        """Convert LinkedInProfile to dictionary with comprehensive data"""
        raw_data = profile.raw_data or {}
        
        # Extract additional profile metrics from Apify data
        profile_dict = {
            # Basic information
            'url': profile.url,
            'name': profile.name,
            'first_name': raw_data.get('firstName'),
            'last_name': raw_data.get('lastName'),
            'headline': profile.headline,
            'company': profile.company,
            'location': profile.location,
            'summary': profile.summary,
            
            # Professional details
            'job_title': raw_data.get('jobTitle'),
            'company_industry': raw_data.get('companyIndustry'),
            'company_website': raw_data.get('companyWebsite'),
            'company_linkedin': raw_data.get('companyLinkedin'),
            'company_size': raw_data.get('companySize'),
            'company_founded': raw_data.get('companyFoundedIn'),
            
            # Job tenure
            'current_job_duration': raw_data.get('currentJobDuration'),
            'current_job_duration_years': raw_data.get('currentJobDurationInYrs'),
            
            # Network metrics
            'connections': raw_data.get('connections'),
            'followers': raw_data.get('followers'),
            
            # Skills and endorsements
            'top_skills_by_endorsements': raw_data.get('topSkillsByEndorsements'),
            
            # Contact information (usually null for privacy)
            'email': raw_data.get('email'),
            'mobile_number': raw_data.get('mobileNumber'),
            
            # Profile identifiers
            'public_identifier': raw_data.get('publicIdentifier'),
            'urn': raw_data.get('urn'),
            
            # Structured data
            'experience': profile.experience,
            'education': profile.education,
            'skills': profile.skills,
            
            # Counts for quick reference
            'experience_count': len(profile.experience) if profile.experience else 0,
            'education_count': len(profile.education) if profile.education else 0,
            'skills_count': len(profile.skills) if profile.skills else 0,
            
            # Additional sections from Apify
            'interests': raw_data.get('interests', []),
            'languages': raw_data.get('languages', []),
            'certifications': raw_data.get('licenseAndCertificates', []),
            'honors_awards': raw_data.get('honorsAndAwards', []),
            'volunteer_work': raw_data.get('volunteerAndAwards', []),
            'projects': raw_data.get('projects', []),
            'publications': raw_data.get('publications', []),
            'recommendations': raw_data.get('recommendations', []),
            
            # Meta information
            'has_detailed_data': True,
            'scrape_timestamp': None,  # Would add in production
            'data_source': 'apify_linkedin_scraper'
        }
        
        return profile_dict
    
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
