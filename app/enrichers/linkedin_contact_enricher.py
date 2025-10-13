#!/usr/bin/env python3
"""
LinkedIn Contact Enricher for Salesforce

Two-step process:
1. Search for LinkedIn URL using Google (if not already present)
2. Scrape LinkedIn profile data using Apify

Usage:
    python linkedin_contact_enricher.py "CONTACT_RECORD_ID" [--step1-only] [--step2-only]
"""

import os
import sys
import logging
import json
import argparse
import asyncio
import re
from typing import Optional, Dict, Any, List
from simple_salesforce import Salesforce
from dotenv import load_dotenv
import aiohttp
from apify_client import ApifyClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInContactEnricher:
    """LinkedIn contact enricher for Salesforce with two-step process."""

    def __init__(self):
        """Initialize the enricher with Salesforce, Serper, and Apify connections."""
        self.sf = None
        self.serper_api_key = None
        self.apify_client = None

        # Load environment variables
        load_dotenv()

        self._connect_to_salesforce()
        self._setup_apis()

    def _connect_to_salesforce(self) -> None:
        """Connect to Salesforce using environment variables."""
        try:
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'login')

            if not username or not password:
                raise ValueError("Missing required Salesforce credentials")

            logger.info("🔗 Connecting to Salesforce...")

            if security_token:
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    security_token=security_token,
                    domain=domain
                )
            else:
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    domain=domain
                )

            # Test connection
            test_result = self.sf.query("SELECT Id FROM Contact LIMIT 1")
            if test_result and test_result.get('totalSize', 0) >= 0:
                logger.info("✅ Successfully connected to Salesforce")
            else:
                raise Exception("Connected but test query failed")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Salesforce: {str(e)}")
            raise

    def _setup_apis(self) -> None:
        """Setup Serper and Apify API clients."""
        try:
            # Setup Serper for Google search
            self.serper_api_key = os.getenv('SERPER_API_KEY')
            if not self.serper_api_key:
                logger.warning("⚠️ SERPER_API_KEY not found - Step 1 (LinkedIn search) will not work")

            # Setup Apify for LinkedIn scraping
            apify_token = os.getenv('APIFY_API_TOKEN')
            if apify_token:
                self.apify_client = ApifyClient(apify_token)
                logger.info("✅ Apify client configured")
            else:
                logger.warning("⚠️ APIFY_API_TOKEN not found - Step 2 (LinkedIn scraping) will not work")

        except Exception as e:
            logger.error(f"❌ Failed to setup APIs: {str(e)}")
            raise

    def get_contact_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get contact record from Salesforce."""
        try:
            logger.info(f"🔍 Retrieving contact details: {record_id}")

            # Get contact with LinkedIn field
            contact = self.sf.Contact.get(record_id)
            if not contact:
                logger.warning(f"❌ No contact found for ID: {record_id}")
                return None

            # Get account details for company name
            account_info = {}
            if contact.get('AccountId'):
                try:
                    account = self.sf.Account.get(contact['AccountId'])
                    account_info = {
                        'account_name': account.get('Name', ''),
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Could not retrieve account info: {str(e)}")

            # Combine contact and account info
            contact.update(account_info)

            name = f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".strip()
            company = contact.get('account_name', 'Unknown Company')
            linkedin_url = contact.get('LinkedIn_Profile__c', '')

            logger.info(f"✅ Found contact: {name} at {company}")
            if linkedin_url:
                logger.info(f"📎 Existing LinkedIn URL: {linkedin_url}")
            else:
                logger.info("📎 No LinkedIn URL found")

            return contact

        except Exception as e:
            logger.error(f"❌ Error retrieving contact: {str(e)}")
            return None

    async def step1_find_linkedin_url(self, contact: Dict[str, Any]) -> Optional[str]:
        """Step 1: Search for LinkedIn URL using Google if not already present."""
        try:
            # Check if LinkedIn URL already exists
            existing_url = contact.get('LinkedIn_Profile__c', '')
            if existing_url and existing_url.strip():
                logger.info(f"✅ LinkedIn URL already exists: {existing_url}")
                return existing_url.strip()

            if not self.serper_api_key:
                logger.error("❌ SERPER_API_KEY not configured - cannot search for LinkedIn URL")
                return None

            first_name = contact.get('FirstName', '')
            last_name = contact.get('LastName', '')
            company = contact.get('account_name', '')
            title = contact.get('Title', '')

            if not first_name or not last_name or not company:
                logger.error("❌ Missing required contact information for LinkedIn search")
                return None

            # Try multiple search variations to handle company name differences
            all_results = []
            search_variations = self._generate_search_variations(first_name, last_name, company, title)

            for search_query in search_variations:
                logger.info(f"🔍 Searching Google for: {search_query}")

                # Perform Google search
                search_results = await self._perform_google_search(search_query)

                if search_results.get("success"):
                    results = search_results.get("results", [])
                    if results:
                        all_results.extend(results)
                        # If we found good results with the first query, we can stop early
                        if len(results) >= 3:
                            break
                else:
                    logger.warning(f"⚠️ Search variation failed: {search_results.get('error')}")

                # Small delay between searches to respect rate limits
                await asyncio.sleep(0.2)

            if not all_results:
                logger.warning("⚠️ No LinkedIn profiles found in any search variations")
                return None

            # Remove duplicates based on URL
            unique_results = self._deduplicate_search_results(all_results)

            # Filter and score results
            best_profile = self._select_best_linkedin_profile(unique_results, first_name, last_name, company, title)

            if not best_profile:
                logger.warning("⚠️ No suitable LinkedIn profile found")
                return None

            linkedin_url = best_profile['link']
            logger.info(f"✅ Found LinkedIn URL: {linkedin_url}")

            # Update Salesforce with the LinkedIn URL
            success = self._update_linkedin_url(contact['Id'], linkedin_url)
            if success:
                logger.info("✅ Updated LinkedIn URL in Salesforce")
                return linkedin_url
            else:
                logger.error("❌ Failed to update LinkedIn URL in Salesforce")
                return None

        except Exception as e:
            logger.error(f"❌ Error in step 1 - find LinkedIn URL: {str(e)}")
            return None

    def _generate_search_variations(self, first_name: str, last_name: str, company: str, title: str) -> List[str]:
        """Generate multiple search query variations to handle company name differences and middle names."""
        variations = []

        # Normalize company name and create variations
        company_variations = self._generate_company_variations(company)

        # Generate name variations to handle middle names/initials
        name_variations = self._generate_name_variations(first_name, last_name)

        # Search pattern 1: Name variations + company variations (most specific)
        for name_var in name_variations[:3]:  # Limit to top 3 name variations
            for company_var in company_variations[:2]:  # Limit to top 2 company variations
                variations.append(f'{name_var} {company_var} site:linkedin.com/in')

        # Search pattern 2: Name + title + simplified company
        if title:
            company_core = self._extract_company_core(company)
            for name_var in name_variations[:2]:
                variations.append(f'{name_var} "{title}" {company_core} site:linkedin.com/in')

        # Search pattern 3: Just name + core company (fallback)
        company_core = self._extract_company_core(company)
        for name_var in name_variations[:1]:  # Just the primary name variation
            variations.append(f'{name_var} {company_core} site:linkedin.com/in')

        return variations[:8]  # Limit total variations to prevent too many searches

    def _generate_company_variations(self, company: str) -> List[str]:
        """Generate company name variations to handle different naming conventions."""
        if not company:
            return ['']

        variations = [company]  # Original company name

        # Remove common suffixes and create variations
        company_lower = company.lower()

        # Common company suffixes to try removing/replacing
        suffix_replacements = [
            ('company', ''),
            ('corporation', ''),
            ('corp', ''),
            ('incorporated', ''),
            ('inc', ''),
            ('limited', ''),
            ('ltd', ''),
            ('llc', ''),
            ('technologies', 'tech'),
            ('technology', 'tech'),
            ('systems', ''),
            ('solutions', ''),
            ('group', ''),
            ('enterprises', ''),
        ]

        for old_suffix, new_suffix in suffix_replacements:
            if old_suffix in company_lower:
                # Try removing the suffix
                if new_suffix == '':
                    new_company = company.replace(old_suffix, '').replace(old_suffix.title(), '').strip()
                    if new_company and new_company != company:
                        variations.append(new_company)

                # Try replacing with alternative
                else:
                    new_company = company.replace(old_suffix, new_suffix).replace(old_suffix.title(), new_suffix.title())
                    if new_company != company:
                        variations.append(new_company)

        # Add core name without any suffixes
        core_name = self._extract_company_core(company)
        if core_name not in variations:
            variations.append(core_name)

        return variations[:3]  # Limit to top 3 variations to avoid too many searches

    def _generate_name_variations(self, first_name: str, last_name: str) -> List[str]:
        """Generate name variations to handle middle names, initials, and credentials."""
        variations = []

        # Primary variation: quoted full name
        variations.append(f'"{first_name} {last_name}"')

        # Variation 2: Try with middle initial "P" (common pattern)
        variations.append(f'"{first_name} P {last_name}"')
        variations.append(f'"{first_name} P. {last_name}"')

        # Variation 3: Try with common credentials
        variations.append(f'"{first_name} P. {last_name}, CHFM"')
        variations.append(f'"{first_name} P {last_name} CHFM"')

        # Variation 4: Just first and last name without quotes (broader search)
        variations.append(f'{first_name} {last_name}')

        return variations

    def _is_obviously_wrong_company(self, expected_company: str, result_text: str) -> bool:
        """Check if the result is obviously from a wrong company."""
        result_lower = result_text.lower()
        expected_lower = expected_company.lower()

        # If expected company is healthcare/medical, penalize results with clearly different industries
        if 'cleveland clinic' in expected_lower or 'hospital' in expected_lower or 'medical' in expected_lower:
            wrong_indicators = [
                'driver at slices',
                'uber', 'lyft', 'doordash', 'postmates', 'grubhub',
                'restaurant', 'delivery', 'retail', 'warehouse',
                'walmart', 'target', 'amazon warehouse',
                'construction worker', 'mechanic', 'plumber',
                'freelancer', 'self-employed', 'independent contractor',
                'pizza', 'fast food', 'cashier', 'sales associate'
            ]
            for indicator in wrong_indicators:
                if indicator in result_lower:
                    return True

        # Additional check: if expected company name doesn't appear anywhere in result
        company_core = self._extract_company_core(expected_company)
        if company_core and len(company_core) > 3:
            if company_core.lower() not in result_lower:
                # Only penalize if the result has a clearly different company mentioned
                other_company_indicators = [
                    ' at ', ' - ', ' | ', 'works at', 'employed at', 'manager at'
                ]
                for indicator in other_company_indicators:
                    if indicator in result_lower:
                        return True

        return False

    def _extract_company_core(self, company: str) -> str:
        """Extract the core company name by removing common business suffixes."""
        if not company:
            return ''

        # List of common business suffixes to remove
        suffixes_to_remove = [
            'company', 'corporation', 'corp', 'incorporated', 'inc', 'limited', 'ltd',
            'llc', 'technologies', 'technology', 'tech', 'systems', 'solutions',
            'group', 'enterprises', 'holdings', 'international', 'worldwide', 'global'
        ]

        words = company.split()
        filtered_words = []

        for word in words:
            word_clean = word.lower().rstrip('.,')
            if word_clean not in suffixes_to_remove:
                filtered_words.append(word)

        return ' '.join(filtered_words) if filtered_words else company

    def _deduplicate_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate LinkedIn URLs from search results."""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get('link', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results

    def _calculate_company_match_score(self, company: str, result_text: str) -> int:
        """Calculate a flexible company matching score."""
        if not company:
            return 0

        result_text_lower = result_text.lower()
        company_lower = company.lower()

        # Exact company match (highest score)
        if company_lower in result_text_lower:
            return 25

        # Try company variations
        company_variations = self._generate_company_variations(company)
        for variation in company_variations:
            if variation.lower() in result_text_lower:
                return 20

        # Try core company name
        core_name = self._extract_company_core(company)
        if core_name.lower() in result_text_lower:
            return 15

        # Try individual words from company name (partial match)
        company_words = [word.strip() for word in company.split() if len(word.strip()) > 2]
        matched_words = 0
        for word in company_words:
            if word.lower() in result_text_lower:
                matched_words += 1

        # Score based on percentage of words matched
        if company_words:
            word_match_ratio = matched_words / len(company_words)
            if word_match_ratio >= 0.5:  # At least 50% of words match
                return int(10 * word_match_ratio)

        return 0

    async def _perform_google_search(self, query: str) -> Dict[str, Any]:
        """Perform Google search using Serper API."""
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': 10
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://google.serper.dev/search",
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

        except Exception as e:
            logger.error(f"Error performing Google search: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _select_best_linkedin_profile(self, results: List[Dict], first_name: str, last_name: str, company: str, title: str) -> Optional[Dict]:
        """Select the best LinkedIn profile from search results."""
        if not results:
            return None

        scored_results = []

        for result in results:
            score = 0
            result_text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()

            # Name matching (high priority)
            if first_name.lower() in result_text:
                score += 30
            if last_name.lower() in result_text:
                score += 30

            # Company matching (high priority) - flexible matching
            company_score = self._calculate_company_match_score(company, result_text)
            score += company_score

            # STRICT company validation - penalize obviously wrong companies
            if self._is_obviously_wrong_company(company, result_text):
                score -= 50  # Heavy penalty for wrong companies

            # Title matching (medium priority)
            if title and title.lower() in result_text:
                score += 15

            # Check for connection count indicators (prefer profiles with 100+ connections)
            connection_patterns = [
                r'(\d+)\+?\s*connections?',
                r'(\d+)\+?\s*followers?',
                r'500\+',
                r'1st degree'
            ]

            for pattern in connection_patterns:
                matches = re.findall(pattern, result_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, str):
                        if '500+' in match or '1st' in match:
                            score += 20
                        continue
                    try:
                        count = int(match)
                        if count >= 500:
                            score += 20
                        elif count >= 100:
                            score += 15
                        elif count >= 50:
                            score += 10
                    except (ValueError, TypeError):
                        continue

            # Prefer higher search positions (slight boost)
            position_bonus = max(0, 10 - result.get('position', 10))
            score += position_bonus

            scored_results.append((score, result))

        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Log all scored results for debugging
        logger.info(f"📊 Profile scoring results:")
        for i, (score, result) in enumerate(scored_results[:5]):
            logger.info(f"   {i+1}. Score {score}: {result['title']}")

        # Return best result if it meets minimum threshold AND has valid company
        if scored_results and scored_results[0][0] >= 60:  # Raise minimum score threshold
            best_score, best_result = scored_results[0]
            logger.info(f"📊 Selected LinkedIn profile with score {best_score}: {best_result['title']}")
            return best_result

        logger.warning("⚠️ No LinkedIn profile met the minimum score threshold")
        return None

    def _update_linkedin_url(self, contact_id: str, linkedin_url: str) -> bool:
        """Update the LinkedIn URL in Salesforce."""
        try:
            self.sf.Contact.update(contact_id, {'LinkedIn_Profile__c': linkedin_url})
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update LinkedIn URL: {str(e)}")
            return False

    async def step2_scrape_linkedin_data(self, contact: Dict[str, Any], linkedin_url: str = None) -> bool:
        """Step 2: Scrape LinkedIn profile data using Apify."""
        try:
            if not self.apify_client:
                logger.error("❌ Apify client not configured - cannot scrape LinkedIn data")
                return False

            # Get LinkedIn URL
            if not linkedin_url:
                linkedin_url = contact.get('LinkedIn_Profile__c', '')

            if not linkedin_url or not linkedin_url.strip():
                logger.error("❌ No LinkedIn URL available for scraping")
                return False

            linkedin_url = linkedin_url.strip()
            logger.info(f"🕷️ Scraping LinkedIn profile: {linkedin_url}")

            # Prepare Apify input
            run_input = {
                "profileUrls": [linkedin_url]
            }

            # Run the LinkedIn scraper
            logger.info("⏳ Starting Apify LinkedIn scraper...")
            run = self.apify_client.actor("dev_fusion/linkedin-profile-scraper").call(run_input=run_input)

            logger.info(f"💾 Dataset URL: https://console.apify.com/storage/datasets/{run['defaultDatasetId']}")

            # Fetch results
            profile_data = None
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                profile_data = item
                break  # We only expect one profile

            if not profile_data:
                logger.error("❌ No profile data returned from Apify")
                return False

            # Consolidate the LinkedIn data to reduce size and keep only relevant info
            consolidated_data = self._consolidate_linkedin_data(profile_data)

            # Convert to JSON string for storage
            profile_json = json.dumps(consolidated_data, indent=2, default=str)

            logger.info(f"✅ Successfully scraped LinkedIn profile data ({len(profile_json)} characters)")

            # Extract additional fields from LinkedIn data (use original data for complete field extraction)
            additional_fields = await self._extract_salesforce_fields(profile_data)

            # Update Salesforce with the full LinkedIn data and additional fields
            success = self._update_full_linkedin_data(contact['Id'], profile_json)
            if success:
                logger.info("✅ Updated Full LinkedIn Data in Salesforce")

                # Update additional Salesforce fields if available
                if additional_fields:
                    field_success = self._update_additional_fields(contact['Id'], additional_fields)
                    if field_success:
                        logger.info("✅ Updated additional Salesforce fields from LinkedIn data")
                    else:
                        logger.warning("⚠️ Failed to update some additional fields")

                return True
            else:
                logger.error("❌ Failed to update Full LinkedIn Data in Salesforce")
                return False

        except Exception as e:
            logger.error(f"❌ Error in step 2 - scrape LinkedIn data: {str(e)}")
            return False

    def _consolidate_linkedin_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate LinkedIn data to keep only relevant information and reduce size."""
        try:
            consolidated = {}

            # CORE PROFILE INFO (keep as-is)
            core_fields = [
                'linkedinUrl', 'firstName', 'lastName', 'fullName', 'headline',
                'connections', 'followers', 'email', 'mobileNumber'
            ]
            for field in core_fields:
                consolidated[field] = profile_data.get(field)

            # JOB DESCRIPTION/SUMMARY (near top as requested)
            consolidated['about'] = profile_data.get('about', '')

            # CURRENT JOB INFO (keep as-is)
            job_fields = [
                'jobTitle', 'companyName', 'companyIndustry', 'companyWebsite',
                'companyLinkedin', 'companyFoundedIn', 'companySize',
                'currentJobDuration', 'currentJobDurationInYrs'
            ]
            for field in job_fields:
                consolidated[field] = profile_data.get(field)

            # LOCATION INFO (keep as-is)
            location_fields = ['addressCountryOnly', 'addressWithCountry', 'addressWithoutCountry']
            for field in location_fields:
                consolidated[field] = profile_data.get(field)

            # SKILLS (first 10 only from topSkillsByEndorsements)
            skills_raw = profile_data.get('topSkillsByEndorsements', '')
            if isinstance(skills_raw, str) and skills_raw:
                skills_list = [skill.strip() for skill in skills_raw.split(',')]
                consolidated['topSkillsByEndorsements'] = ', '.join(skills_list[:10])
            else:
                consolidated['topSkillsByEndorsements'] = skills_raw

            # CERTIFICATIONS (comma-separated brief list)
            certs = profile_data.get('licenseAndCertificates', [])
            if certs:
                cert_names = []
                for cert in certs:
                    name = cert.get('name', '')
                    issuer = cert.get('authority', '')
                    if name:
                        if issuer:
                            cert_names.append(f"{name} - {issuer}")
                        else:
                            cert_names.append(name)
                consolidated['certifications'] = ', '.join(cert_names)
            else:
                consolidated['certifications'] = ''

            # EXPERIENCE DATA (summarized)
            experiences = profile_data.get('experiences', [])
            consolidated_experiences = []

            for exp in experiences:
                consolidated_exp = {
                    'title': exp.get('title', ''),
                    'company': exp.get('subtitle', ''),  # using "company" as field name
                    'duration': exp.get('caption', ''),
                    'roles': []
                }

                # Add company LinkedIn if available
                if exp.get('companyLink1'):
                    consolidated_exp['companyLinkedin'] = exp.get('companyLink1')

                # Summarize subComponents (keep only title + duration)
                sub_components = exp.get('subComponents', [])
                for sub in sub_components:
                    if sub.get('title') and sub.get('caption'):
                        consolidated_exp['roles'].append({
                            'title': sub.get('title'),
                            'duration': sub.get('caption')
                        })

                consolidated_experiences.append(consolidated_exp)

            consolidated['experiences'] = consolidated_experiences

            # EDUCATION (school + degree only, keep LinkedIn URLs)
            educations = profile_data.get('educations', [])
            consolidated_education = []

            for edu in educations:
                consolidated_edu = {
                    'school': edu.get('schoolName', ''),
                    'degree': edu.get('degree', '')
                }
                # Add school LinkedIn if available
                if edu.get('schoolUrl'):
                    consolidated_edu['schoolLinkedin'] = edu.get('schoolUrl')

                if consolidated_edu['school'] or consolidated_edu['degree']:
                    consolidated_education.append(consolidated_edu)

            consolidated['education'] = consolidated_education

            # PUBLICATIONS (only if relevant, otherwise empty array)
            publications = profile_data.get('publications', [])
            relevant_publications = []

            # Keywords that indicate relevance to our domain
            relevant_keywords = [
                'energy', 'facility', 'facilities', 'engineering', 'healthcare',
                'hospital', 'mechanical', 'maintenance', 'operations', 'efficiency',
                'sustainability', 'leed', 'hvac', 'building'
            ]

            for pub in publications:
                title = pub.get('title', '').lower()
                if any(keyword in title for keyword in relevant_keywords):
                    relevant_publications.append({
                        'title': pub.get('title', ''),
                        'date': pub.get('date', '')
                    })

            consolidated['publications'] = relevant_publications

            logger.info(f"📊 Consolidated LinkedIn data from {len(str(profile_data))} to {len(str(consolidated))} characters")
            return consolidated

        except Exception as e:
            logger.error(f"❌ Error consolidating LinkedIn data: {str(e)}")
            return profile_data  # Return original if consolidation fails

    async def _extract_salesforce_fields(self, profile_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract Salesforce field updates from LinkedIn profile data."""
        try:
            logger.info("📊 Extracting Salesforce fields from LinkedIn data...")
            fields = {}

            # Department from current position
            if profile_data.get('jobTitle'):
                # Try to extract department from job title or company info
                job_title = profile_data.get('jobTitle', '')
                if any(dept in job_title.lower() for dept in ['facilities', 'maintenance', 'operations']):
                    fields['Department'] = 'Facilities'
                elif any(dept in job_title.lower() for dept in ['finance', 'financial', 'cfo']):
                    fields['Department'] = 'Finance'
                elif any(dept in job_title.lower() for dept in ['sustainability', 'energy', 'environmental']):
                    fields['Department'] = 'Sustainability'

            # Time in role
            current_duration = profile_data.get('currentJobDuration')
            if current_duration:
                fields['Time_in_role__c'] = current_duration

            # Total work experience - calculate from all experiences, not just current job
            total_exp_years = self._calculate_total_experience_from_linkedin(profile_data)
            if not total_exp_years:
                # Fallback to current job duration only if experiences calculation fails
                total_exp_years = profile_data.get('currentJobDurationInYrs')
            if total_exp_years:
                fields['Total_work_experience__c'] = str(total_exp_years)

            # Tenure at current company
            current_job_duration = profile_data.get('currentJobDuration')
            if current_job_duration:
                fields['Tenure_at_current_company__c'] = current_job_duration

            # Time zone from location
            location = (profile_data.get('addressWithoutCountry') or
                       profile_data.get('addressWithCountry') or
                       profile_data.get('city', ''))
            if location:
                timezone = self._determine_timezone(location)
                if timezone:
                    fields['Time_Zone__c'] = timezone

            # AI-generated description summary
            description_summary = await self._generate_description_summary(profile_data)
            if description_summary:
                fields['Description'] = description_summary

            logger.info(f"📊 Extracted {len(fields)} fields from LinkedIn data")
            return fields

        except Exception as e:
            logger.error(f"❌ Error extracting Salesforce fields: {str(e)}")
            return {}

    def _calculate_total_experience_from_linkedin(self, profile_data: Dict[str, Any]) -> Optional[str]:
        """Calculate total work experience from LinkedIn experiences."""
        try:
            experiences = profile_data.get('experiences', [])
            if not experiences:
                return None

            total_years = 0.0
            for exp in experiences:
                # First, try to get duration from caption
                duration = exp.get('caption', '')
                years = self._extract_years_from_duration(duration)

                # If no duration from caption, check if this experience has subComponents
                if years == 0.0 and exp.get('subComponents'):
                    subComponents = exp.get('subComponents', [])
                    for sub in subComponents:
                        sub_duration = sub.get('caption', '')
                        sub_years = self._extract_years_from_duration(sub_duration)
                        years += sub_years

                # If still no duration, try alternative fields
                if years == 0.0:
                    # Some experiences might have duration in subtitle (like "12 yrs 5 mos")
                    subtitle = exp.get('subtitle', '')
                    years = self._extract_years_from_duration(subtitle)

                total_years += years

            if total_years > 0:
                return f"{total_years:.1f} years"
            return None

        except Exception as e:
            logger.error(f"Error calculating experience: {str(e)}")
            return None

    def _extract_years_from_duration(self, duration_str: str) -> float:
        """Extract years from duration string like '2 yrs 5 mos', '3 years 2 months', 'Dec 2020 - Jan 2023'."""
        if not duration_str:
            return 0.0

        import re
        from datetime import datetime, date

        years = 0.0
        months = 0.0

        # Convert to lowercase for easier matching
        duration_lower = duration_str.lower().strip()

        # Pattern 1: "X yrs Y mos" format
        year_match = re.search(r'(\d+)\s*yrs?', duration_lower)
        if year_match:
            years = float(year_match.group(1))

        month_match = re.search(r'(\d+)\s*mos?', duration_lower)
        if month_match:
            months = float(month_match.group(1))

        # Pattern 2: "X years Y months" format (try if no previous matches)
        if years == 0:
            year_match = re.search(r'(\d+)\s*years?', duration_lower)
            if year_match:
                years = float(year_match.group(1))

        if months == 0:
            month_match = re.search(r'(\d+)\s*months?', duration_lower)
            if month_match:
                months = float(month_match.group(1))

        # Pattern 3: "X+ years" or "X+ yrs" format
        if years == 0 and months == 0:
            plus_year_match = re.search(r'(\d+)\+\s*(?:years?|yrs?)', duration_lower)
            if plus_year_match:
                years = float(plus_year_match.group(1))

        # Pattern 4: Date ranges like "Dec 2020 - Present" or "Jan 2018 - Dec 2021"
        if years == 0 and months == 0:
            date_range_match = re.search(r'(\w{3})\s+(\d{4})\s*-\s*(?:(\w{3})\s+(\d{4})|present|current)', duration_lower)
            if date_range_match:
                try:
                    start_month, start_year = date_range_match.group(1), int(date_range_match.group(2))

                    # Handle end date
                    if date_range_match.group(3) and date_range_match.group(4):
                        end_month, end_year = date_range_match.group(3), int(date_range_match.group(4))
                    else:
                        # Present/Current - use current date
                        now = datetime.now()
                        end_month, end_year = now.strftime('%b').lower(), now.year

                    # Convert month names to numbers
                    month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

                    start_month_num = month_map.get(start_month, 1)
                    end_month_num = month_map.get(end_month, 12)

                    # Calculate difference
                    start_date = date(start_year, start_month_num, 1)
                    end_date = date(end_year, end_month_num, 1)

                    # Calculate months difference
                    total_months = (end_year - start_year) * 12 + (end_month_num - start_month_num)
                    if total_months > 0:
                        years = total_months / 12.0
                except:
                    pass  # If date parsing fails, continue to other patterns

        # Pattern 5: Year ranges like "2015 - 2020" or "2018-2021"
        if years == 0 and months == 0:
            year_range_match = re.search(r'(\d{4})\s*-\s*(\d{4})', duration_lower)
            if year_range_match:
                start_year, end_year = int(year_range_match.group(1)), int(year_range_match.group(2))
                years = float(end_year - start_year)

        # Pattern 6: Single year ranges like "2018 - Present"
        if years == 0 and months == 0:
            year_present_match = re.search(r'(\d{4})\s*-\s*(?:present|current)', duration_lower)
            if year_present_match:
                start_year = int(year_present_match.group(1))
                current_year = datetime.now().year
                years = float(current_year - start_year)

        return years + (months / 12.0)

    def _determine_timezone(self, location: str) -> Optional[str]:
        """Determine timezone from location string."""
        if not location:
            return None

        location_lower = location.lower()

        # Eastern Time (ET) - check first, using word boundaries to avoid false matches
        eastern_keywords = [
            'new york', 'ny', 'florida', 'fl', 'georgia', 'ga', 'virginia', 'va',
            'north carolina', 'nc', 'south carolina', 'sc', 'pennsylvania', 'pa',
            'ohio', 'oh', 'michigan', 'mi', 'kentucky', 'ky', 'tennessee', 'tn',
            'indiana', 'in', 'west virginia', 'wv', 'maine', 'me', 'vermont', 'vt',
            'new hampshire', 'nh', 'massachusetts', 'ma', 'rhode island', 'ri',
            'connecticut', 'ct', 'new jersey', 'nj', 'delaware', 'de', 'maryland', 'md',
            'district of columbia', 'dc',
            # Major cities
            'boston', 'atlanta', 'miami', 'philadelphia', 'cleveland', 'detroit',
            'manhattan', 'brooklyn', 'tampa', 'orlando', 'pittsburgh', 'columbus',
            'cincinnati', 'nashville', 'memphis', 'louisville', 'indianapolis',
            'charleston', 'richmond', 'norfolk', 'raleigh', 'charlotte', 'columbia',
            'jacksonville', 'washington', 'baltimore', 'buffalo', 'rochester',
            'albany', 'syracuse', 'newark', 'jersey city', 'hartford', 'providence',
            'manchester', 'portland', 'burlington', 'lexington', 'knoxville'
        ]

        # Check for exact word matches to avoid false positives
        for keyword in eastern_keywords:
            if f' {keyword} ' in f' {location_lower} ' or location_lower.startswith(keyword + ' ') or location_lower.endswith(' ' + keyword) or location_lower == keyword:
                return 'ET'

        # Central Time (CT)
        central_keywords = [
            'texas', 'tx', 'illinois', 'il', 'wisconsin', 'wi', 'minnesota', 'mn',
            'iowa', 'ia', 'missouri', 'mo', 'arkansas', 'ar', 'louisiana', 'la',
            'oklahoma', 'ok', 'kansas', 'ks', 'nebraska', 'ne', 'north dakota', 'nd',
            'south dakota', 'sd', 'alabama', 'al', 'mississippi', 'ms',
            # Major cities
            'chicago', 'dallas', 'houston', 'milwaukee', 'minneapolis', 'kansas city',
            'new orleans', 'austin', 'san antonio', 'st. louis', 'st louis',
            'oklahoma city', 'tulsa', 'wichita', 'omaha', 'lincoln', 'little rock',
            'jackson', 'birmingham', 'mobile', 'huntsville', 'montgomery', 'des moines',
            'cedar rapids', 'sioux city', 'fargo', 'bismarck', 'sioux falls', 'rapid city'
        ]

        for keyword in central_keywords:
            if f' {keyword} ' in f' {location_lower} ' or location_lower.startswith(keyword + ' ') or location_lower.endswith(' ' + keyword) or location_lower == keyword:
                return 'CT'

        # Pacific Time (PT)
        pacific_keywords = [
            'california', 'ca', 'oregon', 'or', 'washington', 'wa', 'nevada', 'nv',
            'los angeles', 'san francisco', 'seattle', 'portland', 'san diego',
            'silicon valley', 'bay area', 'sacramento', 'fresno', 'san jose', 'oakland'
        ]

        for keyword in pacific_keywords:
            if f' {keyword} ' in f' {location_lower} ' or location_lower.startswith(keyword + ' ') or location_lower.endswith(' ' + keyword) or location_lower == keyword:
                return 'PT'

        # Mountain Time (MT)
        mountain_keywords = [
            'colorado', 'co', 'utah', 'ut', 'wyoming', 'wy', 'montana', 'mt',
            'idaho', 'id', 'arizona', 'az', 'new mexico', 'nm',
            # Major cities
            'denver', 'salt lake city', 'phoenix', 'albuquerque', 'boise',
            'cheyenne', 'billings', 'missoula', 'tucson', 'mesa', 'scottsdale',
            'las cruces', 'santa fe', 'casper', 'laramie'
        ]

        for keyword in mountain_keywords:
            if f' {keyword} ' in f' {location_lower} ' or location_lower.startswith(keyword + ' ') or location_lower.endswith(' ' + keyword) or location_lower == keyword:
                return 'MT'

        # Alaska Time (AT)
        alaska_keywords = ['alaska', 'ak', 'anchorage', 'fairbanks', 'juneau', 'sitka', 'ketchikan']
        for keyword in alaska_keywords:
            if f' {keyword} ' in f' {location_lower} ' or location_lower.startswith(keyword + ' ') or location_lower.endswith(' ' + keyword) or location_lower == keyword:
                return 'AT'

        # Hawaii Time (HT)
        hawaii_keywords = ['hawaii', 'hi', 'honolulu', 'hilo', 'kona', 'maui', 'kauai', 'oahu']
        for keyword in hawaii_keywords:
            if f' {keyword} ' in f' {location_lower} ' or location_lower.startswith(keyword + ' ') or location_lower.endswith(' ' + keyword) or location_lower == keyword:
                return 'HT'

        return None

    async def _generate_description_summary(self, profile_data: Dict[str, Any]) -> Optional[str]:
        """Generate AI summary of LinkedIn background, skills, and interests."""
        try:
            # Import OpenAI here to avoid dependency issues if not needed
            import openai

            # Setup OpenAI client (reuse from web search enricher pattern)
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("⚠️ OPENAI_API_KEY not found - skipping description summary")
                return None

            client = openai.OpenAI(api_key=api_key)

            # Extract key information for summary
            name = profile_data.get('fullName', 'Professional')
            headline = profile_data.get('headline', '')
            about = profile_data.get('about', '')
            job_title = profile_data.get('jobTitle', '')
            company = profile_data.get('companyName', '')

            # Extract experience summaries
            experiences = profile_data.get('experiences', [])
            experience_summary = []
            for exp in experiences[:3]:  # Top 3 experiences
                title = exp.get('title', '')
                company_name = exp.get('subtitle', '').split(' · ')[0] if exp.get('subtitle') else ''
                if title and company_name:
                    experience_summary.append(f"{title} at {company_name}")

            # Extract skills
            skills = profile_data.get('topSkillsByEndorsements', '')

            # Check if we have sufficient data to generate a meaningful description
            data_quality_score = self._assess_data_quality(
                headline, about, experience_summary, skills, job_title, company
            )

            if data_quality_score < 3:
                logger.info("⚠️ Insufficient LinkedIn data quality for description generation - returning empty")
                return None

            # Build context for AI
            context = f"""
Name: {name}
Current Role: {job_title} at {company}
Headline: {headline}
About: {about[:500] if about else 'Not provided'}
Key Experience: {'; '.join(experience_summary)}
Top Skills: {skills}
"""

            prompt = f"""Based on this LinkedIn profile information, write a concise 2-3 sentence professional summary that captures the person's key background, skills, and expertise. Focus on their professional value and core competencies.

IMPORTANT: Only generate a summary if there is substantial professional information available. If the profile lacks meaningful details about experience, skills, or background, respond with "INSUFFICIENT_DATA".

Profile Information:
{context}

Guidelines:
- 2-3 sentences maximum
- Professional tone
- Highlight key expertise and background
- Focus on value and competencies
- Avoid redundant information

Write a summary that would be useful for understanding their professional background at a glance."""

            # Make API call (no web search needed)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )

            summary = response.choices[0].message.content.strip()

            # Check if AI determined insufficient data
            if "INSUFFICIENT_DATA" in summary:
                logger.info("⚠️ AI determined insufficient data for meaningful description")
                return None

            logger.info("✅ Generated AI description summary")
            return summary

        except Exception as e:
            logger.error(f"❌ Error generating description summary: {str(e)}")
            return None

    def _assess_data_quality(self, headline: str, about: str, experience_summary: List[str],
                           skills: str, job_title: str, company: str) -> int:
        """Assess the quality and completeness of LinkedIn data for description generation.

        Returns a score from 0-10 where 3+ indicates sufficient data for meaningful description.
        """
        score = 0

        # Job title and company (basic requirements)
        if job_title and len(job_title.strip()) > 3:
            score += 1
        if company and len(company.strip()) > 3:
            score += 1

        # Headline (important for context)
        if headline and len(headline.strip()) > 10:
            score += 2

        # About section (high value)
        if about and len(about.strip()) > 50:
            score += 3
        elif about and len(about.strip()) > 10:
            score += 1

        # Experience data (important for background)
        if len(experience_summary) >= 2:
            score += 2
        elif len(experience_summary) == 1:
            score += 1

        # Skills (useful for competencies)
        if skills and len(skills.split(',')) >= 3:
            score += 1

        return score

    def _update_additional_fields(self, contact_id: str, fields: Dict[str, str]) -> bool:
        """Update additional Salesforce fields from LinkedIn data."""
        try:
            if not fields:
                return True

            logger.info(f"💾 Updating {len(fields)} additional Salesforce fields...")
            for field_name, value in fields.items():
                logger.info(f"   📝 {field_name}: {value}")

            self.sf.Contact.update(contact_id, fields)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update additional fields: {str(e)}")
            return False

    def _update_full_linkedin_data(self, contact_id: str, profile_json: str) -> bool:
        """Update the Full LinkedIn Data field in Salesforce."""
        try:
            self.sf.Contact.update(contact_id, {'Full_Linkedin_Data__c': profile_json})
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update Full LinkedIn Data: {str(e)}")
            return False

    async def process_contact_enrichment(self, record_id: str, step1_only: bool = False, step2_only: bool = False) -> bool:
        """Main method to perform LinkedIn contact enrichment."""
        try:
            logger.info(f"🚀 Starting LinkedIn contact enrichment for record ID: {record_id}")

            if step1_only and step2_only:
                logger.error("❌ Cannot specify both --step1-only and --step2-only")
                return False

            # Get contact details
            contact = self.get_contact_details(record_id)
            if not contact:
                logger.error(f"❌ Cannot proceed: Contact not found for {record_id}")
                return False

            first_name = contact.get('FirstName', '')
            last_name = contact.get('LastName', '')
            company = contact.get('account_name', '')

            logger.info(f"📋 Contact: {first_name} {last_name} at {company}")

            success = True

            # Step 1: Find LinkedIn URL (if needed)
            linkedin_url = None
            if not step2_only:
                logger.info("\n🔍 Step 1: Finding LinkedIn URL...")
                linkedin_url = await self.step1_find_linkedin_url(contact)
                if not linkedin_url and not step1_only:
                    logger.error("❌ Cannot proceed to step 2 without LinkedIn URL")
                    return False

            # Step 2: Scrape LinkedIn data (if needed)
            if not step1_only:
                logger.info("\n🕷️ Step 2: Scraping LinkedIn data...")
                if not linkedin_url:
                    linkedin_url = contact.get('LinkedIn_Profile__c', '')

                step2_success = await self.step2_scrape_linkedin_data(contact, linkedin_url)
                success = success and step2_success

            if success:
                logger.info("✅ LinkedIn contact enrichment completed successfully")
            else:
                logger.error("❌ LinkedIn contact enrichment completed with errors")

            return success

        except Exception as e:
            logger.error(f"❌ Error processing LinkedIn contact enrichment: {str(e)}")
            return False


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='LinkedIn Salesforce Contact Enricher')
    parser.add_argument('record_id', help='Salesforce Contact Record ID')
    parser.add_argument('--step1-only', action='store_true',
                       help='Only perform step 1 (find LinkedIn URL)')
    parser.add_argument('--step2-only', action='store_true',
                       help='Only perform step 2 (scrape LinkedIn data)')

    args = parser.parse_args()

    try:
        enricher = LinkedInContactEnricher()

        # Run async function
        success = asyncio.run(enricher.process_contact_enrichment(
            args.record_id,
            args.step1_only,
            args.step2_only
        ))

        if success:
            print(f"\n✅ Successfully processed contact: {args.record_id}")
            if args.step1_only:
                print("🔍 Step 1 only: LinkedIn URL search completed")
            elif args.step2_only:
                print("🕷️ Step 2 only: LinkedIn data scraping completed")
            else:
                print("🔗 Both steps completed: LinkedIn URL search + data scraping")
        else:
            print(f"\n❌ Failed to process contact: {args.record_id}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()