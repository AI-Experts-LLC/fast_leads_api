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
            # === BASIC PROFILE INFORMATION ===
            'url': profile.url,
            'name': profile.name,
            'first_name': raw_data.get('firstName'),
            'last_name': raw_data.get('lastName'),
            'headline': profile.headline,
            'company': profile.company,
            'location': profile.location,
            'summary': profile.summary,
            'about': raw_data.get('about'),  # Full about section
            
            # === CURRENT POSITION DETAILS ===
            'job_title': raw_data.get('jobTitle'),
            'company_name': raw_data.get('companyName'),
            'company_industry': raw_data.get('companyIndustry'),
            'company_website': raw_data.get('companyWebsite'),
            'company_linkedin': raw_data.get('companyLinkedin'),
            'company_size': raw_data.get('companySize'),
            'company_founded': raw_data.get('companyFoundedIn'),
            
            # === JOB TENURE & CAREER METRICS ===
            'current_job_duration': raw_data.get('currentJobDuration'),
            'current_job_duration_years': raw_data.get('currentJobDurationInYrs'),
            
            # === NETWORK & SOCIAL PROOF ===
            'connections': raw_data.get('connections'),
            'followers': raw_data.get('followers'),
            
            # === SKILLS & EXPERTISE ===
            'top_skills_by_endorsements': raw_data.get('topSkillsByEndorsements'),
            'skills': profile.skills,
            'skills_count': len(profile.skills) if profile.skills else 0,
            
            # === CONTACT INFORMATION ===
            'email': raw_data.get('email'),
            'mobile_number': raw_data.get('mobileNumber'),
            'phone': raw_data.get('phone'),
            'website': raw_data.get('website'),
            
            # === PROFILE IDENTIFIERS ===
            'public_identifier': raw_data.get('publicIdentifier'),
            'urn': raw_data.get('urn'),
            'linkedin_id': raw_data.get('linkedinId'),
            'profile_id': raw_data.get('profileId'),
            
            # === GEOGRAPHIC INFORMATION ===
            'address_with_country': raw_data.get('addressWithCountry'),
            'address_without_country': raw_data.get('addressWithoutCountry'),
            'country': raw_data.get('country'),
            'city': raw_data.get('city'),
            'state': raw_data.get('state'),
            'postal_code': raw_data.get('postalCode'),
            'geo_location': raw_data.get('geoLocation'),
            
            # === PROFESSIONAL EXPERIENCE ===
            'experience': profile.experience,
            'experience_count': len(profile.experience) if profile.experience else 0,
            'total_experience_years': self._calculate_total_experience(profile.experience),
            'industry_experience': self._extract_industry_experience(profile.experience),
            
            # === EDUCATION BACKGROUND ===
            'education': profile.education,
            'education_count': len(profile.education) if profile.education else 0,
            'highest_degree': self._extract_highest_degree(profile.education),
            'alma_maters': self._extract_alma_maters(profile.education),
            
            # === ADDITIONAL PROFILE SECTIONS ===
            'interests': raw_data.get('interests', []),
            'languages': raw_data.get('languages', []),
            'certifications': raw_data.get('licenseAndCertificates', []),
            'honors_awards': raw_data.get('honorsAndAwards', []),
            'volunteer_work': raw_data.get('volunteerAndAwards', []),
            'projects': raw_data.get('projects', []),
            'publications': raw_data.get('publications', []),
            'patents': raw_data.get('patents', []),
            'courses': raw_data.get('courses', []),
            'test_scores': raw_data.get('testScores', []),
            
            # === RECOMMENDATIONS & SOCIAL PROOF ===
            'recommendations': raw_data.get('recommendations', []),
            'recommendations_count': self._count_recommendations(raw_data.get('recommendations', [])),
            'endorsements_received': self._count_total_endorsements(profile.skills),
            
            # === ACTIVITY & ENGAGEMENT ===
            'activity': raw_data.get('activity', []),
            'posts': raw_data.get('posts', []),
            'articles': raw_data.get('articles', []),
            'recent_activity_count': len(raw_data.get('activity', [])),
            
            # === PREMIUM FEATURES ===
            'is_premium': raw_data.get('isPremium', False),
            'is_open_to_work': raw_data.get('isOpenToWork', False),
            'is_hiring': raw_data.get('isHiring', False),
            'premium_badge': raw_data.get('premiumBadge'),
            
            # === PROFILE COMPLETENESS METRICS ===
            'profile_picture_url': raw_data.get('profilePictureUrl') or raw_data.get('photo'),
            'background_image_url': raw_data.get('backgroundImageUrl'),
            'has_profile_picture': bool(raw_data.get('profilePictureUrl') or raw_data.get('photo')),
            'profile_completeness_score': self._calculate_profile_completeness(profile, raw_data),
            
            # === COUNTS FOR QUICK REFERENCE ===
            'total_sections_completed': self._count_completed_sections(profile, raw_data),
            'interests_count': len(raw_data.get('interests', [])),
            'languages_count': len(raw_data.get('languages', [])),
            'certifications_count': len(raw_data.get('licenseAndCertificates', [])),
            'honors_awards_count': len(raw_data.get('honorsAndAwards', [])),
            'volunteer_work_count': len(raw_data.get('volunteerAndAwards', [])),
            'projects_count': len(raw_data.get('projects', [])),
            'publications_count': len(raw_data.get('publications', [])),
            
            # === ENGAGEMENT POTENTIAL ASSESSMENT ===
            'engagement_score': self._calculate_engagement_score(raw_data),
            'accessibility_score': self._calculate_accessibility_score(raw_data),
            'professional_authority_score': self._calculate_authority_score(profile, raw_data),
            
            # === META INFORMATION ===
            'has_detailed_data': True,
            'scrape_timestamp': raw_data.get('timestamp'),
            'data_source': 'apify_linkedin_scraper',
            'data_quality_score': self._calculate_data_quality_score(profile, raw_data),
            'last_updated': raw_data.get('lastUpdated'),
            
            # === RAW DATA (for debugging/advanced use) ===
            'raw_data': raw_data if raw_data else None
        }
        
        return profile_dict
    
    def _calculate_total_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of professional experience"""
        if not experience:
            return 0.0
        
        total_years = 0.0
        for exp in experience:
            duration = exp.get('duration', '')
            years = self._extract_years_from_duration(duration)
            total_years += years
        
        return round(total_years, 1)
    
    def _extract_years_from_duration(self, duration_str: str) -> float:
        """Extract years from duration string like '2 yrs 5 mos'"""
        if not duration_str:
            return 0.0
        
        years = 0.0
        months = 0.0
        
        # Look for year patterns
        import re
        year_match = re.search(r'(\d+)\s*yrs?', duration_str, re.IGNORECASE)
        if year_match:
            years = float(year_match.group(1))
        
        # Look for month patterns
        month_match = re.search(r'(\d+)\s*mos?', duration_str, re.IGNORECASE)
        if month_match:
            months = float(month_match.group(1))
        
        return years + (months / 12.0)
    
    def _extract_industry_experience(self, experience: List[Dict]) -> Dict[str, float]:
        """Extract experience by industry/company type"""
        industry_exp = {}
        
        if not experience:
            return industry_exp
        
        for exp in experience:
            company = (exp.get('company') or '').lower()
            duration = exp.get('duration', '')
            years = self._extract_years_from_duration(duration)
            
            # Simple industry categorization
            if any(term in company for term in ['hospital', 'medical', 'health', 'clinic']):
                industry_exp['healthcare'] = industry_exp.get('healthcare', 0) + years
            elif any(term in company for term in ['tech', 'software', 'ai', 'data']):
                industry_exp['technology'] = industry_exp.get('technology', 0) + years
            elif any(term in company for term in ['consult', 'advisory', 'strategy']):
                industry_exp['consulting'] = industry_exp.get('consulting', 0) + years
            elif any(term in company for term in ['university', 'school', 'academic']):
                industry_exp['education'] = industry_exp.get('education', 0) + years
            else:
                industry_exp['other'] = industry_exp.get('other', 0) + years
        
        return {k: round(v, 1) for k, v in industry_exp.items()}
    
    def _extract_highest_degree(self, education: List[Dict]) -> str:
        """Extract the highest degree achieved"""
        if not education:
            return "Unknown"
        
        degree_hierarchy = {
            'phd': 6, 'doctorate': 6, 'doctoral': 6,
            'md': 5, 'jd': 5, 'pharmd': 5,
            'masters': 4, 'master': 4, 'mba': 4, 'ms': 4, 'ma': 4,
            'bachelor': 3, 'ba': 3, 'bs': 3, 'bsc': 3,
            'associate': 2, 'diploma': 1, 'certificate': 1
        }
        
        highest_level = 0
        highest_degree = "Unknown"
        
        for edu in education:
            degree = (edu.get('degree') or '').lower()
            for degree_type, level in degree_hierarchy.items():
                if degree_type in degree and level > highest_level:
                    highest_level = level
                    highest_degree = edu.get('degree', 'Unknown')
        
        return highest_degree
    
    def _extract_alma_maters(self, education: List[Dict]) -> List[str]:
        """Extract list of schools attended"""
        if not education:
            return []
        
        return [edu.get('school', 'Unknown') for edu in education if edu.get('school')]
    
    def _count_recommendations(self, recommendations: List[Dict]) -> Dict[str, int]:
        """Count recommendations given vs received"""
        counts = {'received': 0, 'given': 0}
        
        if not recommendations:
            return counts
        
        for rec_section in recommendations:
            section_name = (rec_section.get('section_name') or '').lower()
            section_components = rec_section.get('section_components', [])
            
            if 'received' in section_name:
                counts['received'] += len(section_components)
            elif 'given' in section_name:
                counts['given'] += len(section_components)
        
        return counts
    
    def _count_total_endorsements(self, skills: List[Dict]) -> int:
        """Count total endorsements across all skills"""
        if not skills:
            return 0
        
        total = 0
        for skill in skills:
            endorsements = skill.get('endorsements', [])
            for endorsement in endorsements:
                # Extract number from endorsement text like "33 endorsements"
                import re
                numbers = re.findall(r'(\d+)', endorsement)
                if numbers:
                    total += int(numbers[-1])  # Take the last number found
        
        return total
    
    def _calculate_engagement_score(self, raw_data: Dict) -> int:
        """Calculate engagement potential score (0-100)"""
        score = 0
        
        # Recent activity
        activity_count = len(raw_data.get('activity', []))
        score += min(activity_count * 10, 30)  # Max 30 points
        
        # Followers count (social proof)
        followers = raw_data.get('followers', 0)
        if followers > 10000:
            score += 25
        elif followers > 1000:
            score += 15
        elif followers > 500:
            score += 10
        elif followers > 100:
            score += 5
        
        # Connection count (network size)
        connections = raw_data.get('connections', 0)
        if connections > 500:
            score += 20
        elif connections > 100:
            score += 15
        elif connections > 50:
            score += 10
        
        # Premium membership
        if raw_data.get('isPremium'):
            score += 15
        
        # Profile completeness
        if raw_data.get('about'):
            score += 10
        
        return min(score, 100)
    
    def _calculate_accessibility_score(self, raw_data: Dict) -> int:
        """Calculate how accessible/reachable the person seems (0-100)"""
        score = 0
        
        # Contact information available
        if raw_data.get('email'):
            score += 30
        if raw_data.get('website'):
            score += 20
        if raw_data.get('phone'):
            score += 25
        
        # Open to work/hiring
        if raw_data.get('isOpenToWork'):
            score += 15
        if raw_data.get('isHiring'):
            score += 10
        
        # Recent activity suggests active user
        if len(raw_data.get('activity', [])) > 0:
            score += 20
        
        return min(score, 100)
    
    def _calculate_authority_score(self, profile: LinkedInProfile, raw_data: Dict) -> int:
        """Calculate professional authority score (0-100)"""
        score = 0
        
        # Leadership positions
        experience = profile.experience or []
        for exp in experience:
            title = (exp.get('title') or '').lower()
            if any(term in title for term in ['director', 'vp', 'ceo', 'cfo', 'coo', 'founder']):
                score += 20
            elif any(term in title for term in ['manager', 'lead', 'head', 'chief']):
                score += 10
        
        # Education quality
        education = profile.education or []
        for edu in education:
            school = (edu.get('school') or '').lower()
            if any(term in school for term in ['harvard', 'stanford', 'mit', 'wharton', 'yale']):
                score += 15
            degree = (edu.get('degree') or '').lower()
            if any(term in degree for term in ['phd', 'doctorate', 'mba']):
                score += 10
        
        # Publications and projects
        score += min(len(raw_data.get('publications', [])) * 5, 20)
        score += min(len(raw_data.get('projects', [])) * 3, 15)
        
        # Awards and honors
        score += min(len(raw_data.get('honorsAndAwards', [])) * 5, 20)
        
        return min(score, 100)
    
    def _calculate_profile_completeness(self, profile: LinkedInProfile, raw_data: Dict) -> int:
        """Calculate profile completeness score (0-100)"""
        score = 0
        total_sections = 10
        
        # Core sections
        if profile.name: score += 10
        if profile.headline: score += 10
        if profile.summary or raw_data.get('about'): score += 10
        if profile.experience: score += 10
        if profile.education: score += 10
        if profile.skills: score += 10
        if raw_data.get('profilePictureUrl') or raw_data.get('photo'): score += 10
        
        # Additional sections
        additional_sections = 0
        if raw_data.get('interests'): additional_sections += 1
        if raw_data.get('certifications'): additional_sections += 1
        if raw_data.get('recommendations'): additional_sections += 1
        if raw_data.get('volunteerAndAwards'): additional_sections += 1
        if raw_data.get('projects'): additional_sections += 1
        
        score += min(additional_sections * 6, 30)
        
        return min(score, 100)
    
    def _calculate_data_quality_score(self, profile: LinkedInProfile, raw_data: Dict) -> int:
        """Calculate the quality/richness of scraped data (0-100)"""
        score = 0
        
        # Basic data availability
        if profile.name: score += 10
        if profile.headline: score += 10
        if profile.summary: score += 10
        if profile.location: score += 5
        
        # Detailed sections
        if profile.experience: score += 15
        if profile.education: score += 10
        if profile.skills: score += 10
        
        # Extended data
        if raw_data.get('interests'): score += 5
        if raw_data.get('recommendations'): score += 10
        if raw_data.get('certifications'): score += 5
        if raw_data.get('connections'): score += 5
        if raw_data.get('followers'): score += 5
        
        return min(score, 100)
    
    def _count_completed_sections(self, profile: LinkedInProfile, raw_data: Dict) -> int:
        """Count how many profile sections are completed"""
        sections = 0
        
        if profile.name: sections += 1
        if profile.headline: sections += 1
        if profile.summary or raw_data.get('about'): sections += 1
        if profile.experience: sections += 1
        if profile.education: sections += 1
        if profile.skills: sections += 1
        if raw_data.get('interests'): sections += 1
        if raw_data.get('certifications'): sections += 1
        if raw_data.get('recommendations'): sections += 1
        if raw_data.get('volunteerAndAwards'): sections += 1
        if raw_data.get('projects'): sections += 1
        if raw_data.get('publications'): sections += 1
        if raw_data.get('honorsAndAwards'): sections += 1
        
        return sections
    
    def _calculate_engagement_score(self, raw_data: Dict) -> int:
        """Calculate engagement potential score based on activity and connections (0-100)"""
        score = 0
        
        # Activity indicators
        activity_count = len(raw_data.get('activity', []))
        posts_count = len(raw_data.get('posts', []))
        articles_count = len(raw_data.get('articles', []))
        
        # Score based on activity
        score += min(activity_count * 5, 30)
        score += min(posts_count * 3, 20)
        score += min(articles_count * 10, 30)
        
        # Connection indicators
        connections = raw_data.get('connections', 0) or 0
        followers = raw_data.get('followers', 0) or 0
        
        if isinstance(connections, int) and connections > 500:
            score += 10
        elif isinstance(connections, int) and connections > 100:
            score += 5
        
        if isinstance(followers, int) and followers > 1000:
            score += 10
        elif isinstance(followers, int) and followers > 100:
            score += 5
        
        return min(score, 100)
    
    def _calculate_accessibility_score(self, raw_data: Dict) -> int:
        """Calculate how accessible/reachable the person is (0-100)"""
        score = 50  # Base accessibility score
        
        # Premium users might be more accessible
        if raw_data.get('isPremium'):
            score += 10
        
        # Open to work indicates higher accessibility
        if raw_data.get('isOpenToWork'):
            score += 15
        
        # Hiring managers are typically accessible
        if raw_data.get('isHiring'):
            score += 10
        
        # Public activity indicates accessibility
        activity_count = len(raw_data.get('activity', []))
        if activity_count > 10:
            score += 10
        elif activity_count > 5:
            score += 5
        
        # Contact info availability
        if raw_data.get('email'):
            score += 10
        if raw_data.get('phone'):
            score += 5
        
        return min(score, 100)
    
    def _calculate_authority_score(self, profile: LinkedInProfile, raw_data: Dict) -> int:
        """Calculate professional authority score (0-100)"""
        score = 0
        
        # Experience-based authority
        experience_years = self._calculate_total_experience(profile.experience or [])
        if isinstance(experience_years, (int, float)):
            if experience_years >= 15:
                score += 25
            elif experience_years >= 10:
                score += 20
            elif experience_years >= 5:
                score += 15
            elif experience_years >= 2:
                score += 10
        
        # Education authority
        education_count = len(profile.education or [])
        score += min(education_count * 5, 15)
        
        # Skills and endorsements
        skills_count = len(profile.skills or [])
        score += min(skills_count * 2, 20)
        
        # Recommendations as authority indicator
        recommendations_count = len(raw_data.get('recommendations', []))
        score += min(recommendations_count * 3, 15)
        
        # Publications and achievements
        publications_count = len(raw_data.get('publications', []))
        score += min(publications_count * 5, 15)
        
        # Certifications
        certifications_count = len(raw_data.get('licenseAndCertificates', []))
        score += min(certifications_count * 2, 10)
        
        return min(score, 100)
    
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
