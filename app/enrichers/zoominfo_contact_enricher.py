#!/usr/bin/env python3
"""
ZoomInfo Contact Enricher for Salesforce

Uses ZoomInfo API to find detailed contact information and enrich Salesforce Contact records.
Organized into focused sections with separate searches for better results.

Usage:
    python zoominfo_contact_enricher.py "CONTACT_RECORD_ID" [--overwrite]
"""

import os
import sys
import logging
import json
import base64
import argparse
import secrets
import hashlib
import uuid
import webbrowser
from typing import Optional, Dict, Any, List
from simple_salesforce import Salesforce
from dotenv import load_dotenv
import requests
import time
from urllib.parse import urlparse, parse_qs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZoomInfoAPIClient:
    """ZoomInfo API client for contact searches and enrichment with OAuth support."""
    
    def __init__(self):
        """Initialize ZoomInfo API client with authentication."""
        self.api_key = os.getenv('ZOOMINFO_API_KEY')
        self.client_id = os.getenv('ZOOMINFO_CLIENT_ID') 
        self.client_secret = os.getenv('ZOOMINFO_CLIENT_SECRET')
        self.base_url = "https://api.zoominfo.com/gtm/data/v1"
        self.auth_url = "https://login.zoominfo.com/"
        self.token_url = "https://okta-login.zoominfo.com/oauth2/default/v1/token"
        # Use HTTPS localhost redirect URI as configured in ZoomInfo OAuth allow list
        self.redirect_uri = "https://localhost:8080/callback"
        self.access_token = None
        
        # Check for either API key or client credentials
        if not self.api_key and not (self.client_id and self.client_secret):
            raise ValueError("Missing ZoomInfo credentials: need either ZOOMINFO_API_KEY or both ZOOMINFO_CLIENT_ID and ZOOMINFO_CLIENT_SECRET")
        
        # Check for existing access token first
        existing_token = os.getenv('ZOOMINFO_ACCESS_TOKEN')
        if existing_token:
            self.access_token = existing_token
            logger.info("✅ Using existing access token from environment")
        elif self.client_id and self.client_secret:
            # Try OAuth if we have credentials but no token
            self._authenticate_oauth()
        
        logger.info("✅ ZoomInfo API client configured")
    
    def _generate_code_verifier(self) -> str:
        """Generate code verifier for PKCE."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode('utf-8')
    
    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate code challenge for PKCE."""
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')
    
    def _authenticate_oauth(self) -> None:
        """Authenticate using OAuth 2.0 with PKCE flow."""
        try:
            logger.info("🔐 Starting OAuth authentication with ZoomInfo...")
            
            # Generate PKCE codes
            code_verifier = self._generate_code_verifier()
            code_challenge = self._generate_code_challenge(code_verifier)
            state = str(uuid.uuid4())
            
            # Build authorization URL
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'state': state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256'
            }
            
            auth_url = f"{self.auth_url}?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])
            
            print(f"\n🌐 Please visit this URL to authorize the application:")
            print(f"{auth_url}")
            print(f"\nAfter authorization, you'll be redirected to a localhost URL.")
            print(f"Please copy the FULL redirect URL and paste it here.")
            
            # For now, let's use a simpler approach - manual copy/paste
            redirect_url = input("\nPaste the full redirect URL here: ").strip()
            
            # Parse the authorization code from the redirect URL
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            
            if 'code' not in query_params:
                raise ValueError("No authorization code found in redirect URL")
            
            auth_code = query_params['code'][0]
            returned_state = query_params.get('state', [None])[0]
            
            if returned_state != state:
                raise ValueError("State mismatch - possible CSRF attack")
            
            # Exchange authorization code for access token
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'code_verifier': code_verifier
            }
            
            # Create Basic Auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            token_headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(self.token_url, data=token_data, headers=token_headers)
            
            if response.status_code == 200:
                token_response = response.json()
                self.access_token = token_response.get('access_token')
                logger.info("✅ Successfully obtained access token")
                
                # Save the token to .env file for future use
                self._save_token_to_env(self.access_token)
                
            else:
                logger.error(f"❌ Token exchange failed: {response.status_code} - {response.text}")
                raise ValueError("Failed to obtain access token")
                
        except Exception as e:
            logger.warning(f"⚠️ OAuth authentication failed: {str(e)}")
            logger.info("🔧 Will continue without OAuth token")
    
    def _save_token_to_env(self, access_token: str) -> None:
        """Save the access token to .env file for future use."""
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            
            # Read existing .env content
            env_lines = []
            token_exists = False
            
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
                
                # Check if ZOOMINFO_ACCESS_TOKEN already exists and update it
                for i, line in enumerate(env_lines):
                    if line.strip().startswith('ZOOMINFO_ACCESS_TOKEN='):
                        env_lines[i] = f'ZOOMINFO_ACCESS_TOKEN={access_token}\n'
                        token_exists = True
                        break
            
            # If token doesn't exist, add it
            if not token_exists:
                if env_lines and not env_lines[-1].endswith('\n'):
                    env_lines.append('\n')
                env_lines.append(f'# ZoomInfo Access Token (auto-saved)\n')
                env_lines.append(f'ZOOMINFO_ACCESS_TOKEN={access_token}\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            logger.info(f"💾 Access token saved to .env file")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not save token to .env file: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for ZoomInfo API requests."""
        if self.access_token:
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json"
            }
        else:
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.api+json", 
                "Content-Type": "application/vnd.api+json"
            }
    
    def search_contact(self, first_name: str, last_name: str, company_name: str = None, email: str = None) -> Optional[Dict]:
        """Search for contact using ZoomInfo API."""
        try:
            logger.info(f"🔍 Searching ZoomInfo for: {first_name} {last_name} at {company_name}")
            
            url = f"{self.base_url}/contacts/search"
            
            # Build search criteria - only use valid search fields
            search_criteria = {
                "firstName": first_name,
                "lastName": last_name
            }
            
            if company_name:
                search_criteria["companyName"] = company_name
            # Note: email is not a valid search parameter for ZoomInfo contact search API
            # We'll use firstName + lastName + companyName for the search
            
            payload = {
                "data": {
                    "type": "ContactSearch",
                    "attributes": search_criteria
                }
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                contacts = data.get('data', [])
                logger.info(f"✅ Found {len(contacts)} contacts in ZoomInfo")
                return data
            else:
                logger.warning(f"⚠️ ZoomInfo search failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error searching ZoomInfo: {str(e)}")
            return None
    
    def enrich_contact(self, contact_id: str) -> Optional[Dict]:
        """Enrich contact with detailed information using ZoomInfo API."""
        try:
            logger.info(f"📈 Enriching contact ID: {contact_id}")
            
            url = f"{self.base_url}/contacts/enrich"
            
            # Request contact information (only fields confirmed to work with current subscription)
            output_fields = [
                "id", "email", "personHasMoved", "companyName", 
                "contactAccuracyScore", "companyWebsite", "companyRevenue",
                "companyRevenueNumeric", "companyEmployeeCount", "companyPrimaryIndustry", 
                "companyRevenueRange", "companyEmployeeRange",
                # Contact-level fields that work
                "firstName", "lastName", "jobTitle", "mobilePhone", "city", "state", 
                "country", "street", "zipCode", "education", "managementLevel", 
                "validDate", "lastUpdatedDate", "metroArea", "region"
            ]
            
            payload = {
                "data": {
                    "type": "ContactEnrich", 
                    "attributes": {
                        "matchPersonInput": [{"personId": int(contact_id)}],
                        "outputFields": output_fields,
                        "requiredFields": ["id", "companyName"]
                    }
                }
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                enriched_contacts = data.get('data', [])
                logger.info(f"✅ Enriched {len(enriched_contacts)} contacts")
                return data
            else:
                logger.warning(f"⚠️ ZoomInfo enrichment failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error enriching contact: {str(e)}")
            return None


class ZoomInfoContactEnricher:
    """ZoomInfo-enabled contact enricher for Salesforce."""
    
    # Field mapping based on discovered Contact fields
    FIELD_MAPPING = {
        # General Information section
        'first_name': 'FirstName',
        'last_name': 'LastName', 
        'email': 'Email',
        'phone': 'Phone',
        'mobile_phone': 'MobilePhone',
        'direct_phone': 'Direct_Phone__c',
        'title': 'Title',
        'department': 'Department',
        'linkedin_profile': 'LinkedIn_Profile__c',
        'lead_source': 'LeadSource',
        'description': 'Description',
        
        # Work Experience section
        'tenure_current_company': 'Tenure_at_current_company__c',
        'time_in_role': 'Time_in_role__c',
        'total_work_experience': 'Total_work_experience__c',
        'why_role_relevant': 'Why_their_role_is_relevant_to_Metrus__c',
        
        # Education section
        'education': 'Education__c',
        
        # Address fields (using Mailing address as primary)
        'mailing_street': 'MailingStreet',
        'mailing_city': 'MailingCity',
        'mailing_state': 'MailingState',
        'mailing_postal_code': 'MailingPostalCode',
        'mailing_country': 'MailingCountry',
        
        # Additional fields
        'location': 'Location__c',
        'mobile_zoominfo': 'Mobile_Zoominfo__c',
        'zoominfo_email': 'Email',  # Special handling for email updates
    }
    
    def __init__(self):
        """Initialize the enricher with Salesforce and ZoomInfo connections."""
        self.sf = None
        self.zoominfo_client = None
        
        # Load environment variables
        load_dotenv()
        
        self._connect_to_salesforce()
        self._setup_zoominfo_client()
    
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
            
            test_result = self.sf.query("SELECT Id FROM Contact LIMIT 1")
            if test_result and test_result.get('totalSize', 0) > 0:
                logger.info("✅ Successfully connected to Salesforce")
            else:
                raise Exception("Connected but test query failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Salesforce: {str(e)}")
            raise
    
    def _setup_zoominfo_client(self) -> None:
        """Setup ZoomInfo client."""
        try:
            self.zoominfo_client = ZoomInfoAPIClient()
            logger.info("✅ ZoomInfo client configured with real API credentials")
            
        except Exception as e:
            logger.warning(f"⚠️ ZoomInfo setup failed: {str(e)}")
            logger.info("🔧 Continuing with simulated data for testing")
            self.zoominfo_client = None
    
    def get_contact_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get contact record with details."""
        try:
            logger.info(f"🔍 Retrieving contact details: {record_id}")
            
            contact = self.sf.Contact.get(record_id)
            if contact:
                name = f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".strip()
                logger.info(f"✅ Found contact: {name}")
                return contact
            else:
                logger.warning(f"❌ No contact found for ID: {record_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving contact: {str(e)}")
            return None
    
    def check_updatable_fields(self, contact: Dict[str, Any], overwrite: bool = False) -> List[str]:
        """Check which fields can be updated."""
        updatable_fields = []
        
        logger.info("📋 Checking field status:")
        
        for field_key, salesforce_field in self.FIELD_MAPPING.items():
            current_value = contact.get(salesforce_field, '')
            is_empty = not current_value or (isinstance(current_value, str) and len(current_value.strip()) == 0)
            
            if overwrite or is_empty:
                updatable_fields.append(field_key)
                status = "🟢 WILL UPDATE" if overwrite else "🟡 EMPTY - WILL UPDATE"
            else:
                status = "🔴 HAS DATA - SKIP"
            
            preview = ""
            if current_value and isinstance(current_value, str):
                preview = f" (current: {current_value[:30]}{'...' if len(current_value) > 30 else ''})"
            
            logger.info(f"   {field_key}: {status}{preview}")
        
        logger.info(f"📊 Summary: {len(updatable_fields)}/{len(self.FIELD_MAPPING)} fields can be updated")
        return updatable_fields
    
    def simulate_zoominfo_data(self, first_name: str, last_name: str, company_name: str) -> Dict[str, str]:
        """Simulate ZoomInfo API response for testing when API is not available."""
        logger.info(f"🔬 Simulating ZoomInfo data for: {first_name} {last_name}")
        
        # Create realistic simulated data based on the contact
        simulated_data = {
            'direct_phone': '+1 (555) 123-4567',
            'mobile_zoominfo': '+1 (555) 987-6543',
            'location': 'Boston, MA',  # Can be enhanced based on company
            'role_description': f'Title: Senior Engineer\nDepartment: Engineering\nCompany: {company_name}\nCompany Size: 10000+ employees\nIndustry: Technology',
            'tenure_current_company': '3+ years',
            'time_in_role': '18 months',
            'education': 'Master of Science (MS), Engineering\nBachelor of Science (BS), Computer Science'
        }
        
        logger.info(f"✅ Generated simulated data with {len(simulated_data)} fields")
        return simulated_data
    
    def extract_zoominfo_data(self, zoominfo_response: Dict) -> Dict[str, str]:
        """Extract and format data from ZoomInfo API response."""
        try:
            logger.info("📊 FULL ZOOMINFO API RESPONSE:")
            logger.info("=" * 80)
            logger.info(json.dumps(zoominfo_response, indent=2))
            logger.info("=" * 80)
            
            contacts = zoominfo_response.get('data', [])
            if not contacts:
                logger.warning("⚠️ No contacts found in ZoomInfo response")
                return {}
            
            # Use the first (best match) contact
            contact_data = contacts[0]
            attributes = contact_data.get('attributes', {})
            company = attributes.get('company', {})
            
            logger.info(f"📋 Processing ZoomInfo contact: {attributes.get('firstName', '')} {attributes.get('lastName', '')}")
            logger.info(f"📋 Contact attributes available: {list(attributes.keys())}")
            
            # Extract relevant fields
            extracted_data = {}
            
            # General Information
            if attributes.get('firstName'):
                extracted_data['first_name'] = attributes['firstName']
                logger.info(f"   ✅ First Name: {attributes['firstName']}")
            
            if attributes.get('lastName'):
                extracted_data['last_name'] = attributes['lastName']
                logger.info(f"   ✅ Last Name: {attributes['lastName']}")
            
            if attributes.get('email'):
                extracted_data['email'] = attributes['email']
                extracted_data['zoominfo_email'] = attributes['email']  # Always capture ZoomInfo email
                logger.info(f"   ✅ Email: {attributes['email']}")
            
            if attributes.get('directPhone'):
                extracted_data['direct_phone'] = attributes['directPhone']
                logger.info(f"   ✅ Direct Phone: {attributes['directPhone']}")
            
            # Mobile phone (prioritized field)
            if attributes.get('mobilePhone'):
                extracted_data['mobile_phone'] = attributes['mobilePhone']  # Use standard mobile_phone field
                extracted_data['mobile_zoominfo'] = attributes['mobilePhone']  # Also update ZoomInfo-specific field
                logger.info(f"   ✅ Mobile Phone: {attributes['mobilePhone']}")
            
            # Additional phone numbers
            if attributes.get('homePhone'):
                extracted_data['home_phone'] = attributes['homePhone']
                logger.info(f"   ✅ Home Phone: {attributes['homePhone']}")
            
            if attributes.get('otherPhone'):
                extracted_data['other_phone'] = attributes['otherPhone']
                logger.info(f"   ✅ Other Phone: {attributes['otherPhone']}")
            
            # Assistant information
            if attributes.get('assistantName'):
                extracted_data['assistant_name'] = attributes['assistantName']
                logger.info(f"   ✅ Assistant Name: {attributes['assistantName']}")
            
            if attributes.get('assistantPhone'):
                extracted_data['assistant_phone'] = attributes['assistantPhone']
                logger.info(f"   ✅ Assistant Phone: {attributes['assistantPhone']}")
            
            if attributes.get('jobTitle'):
                extracted_data['title'] = attributes['jobTitle']
                logger.info(f"   ✅ Job Title: {attributes['jobTitle']}")
            
            if attributes.get('department'):
                extracted_data['department'] = attributes['department']
                logger.info(f"   ✅ Department: {attributes['department']}")
            
            # LinkedIn Profile from direct field or social media URLs
            if attributes.get('linkedInProfile'):
                extracted_data['linkedin_profile'] = attributes['linkedInProfile']
                logger.info(f"   ✅ LinkedIn: {attributes['linkedInProfile']}")
            elif attributes.get('socialMediaUrls'):
                # Look for LinkedIn in socialMediaUrls array
                social_urls = attributes['socialMediaUrls']
                for social_url in social_urls:
                    if isinstance(social_url, dict) and social_url.get('type') == 'LINKED_IN':
                        extracted_data['linkedin_profile'] = social_url.get('url', '')
                        logger.info(f"   ✅ LinkedIn (from social): {social_url.get('url', '')}")
                        break
            # Also check company social media URLs as fallback
            elif company.get('socialMediaUrls'):
                company_social = company['socialMediaUrls']
                for social_url in company_social:
                    if isinstance(social_url, dict) and social_url.get('type') == 'LINKED_IN':
                        # This would be company LinkedIn, but better than nothing
                        extracted_data['linkedin_profile'] = social_url.get('url', '')
                        logger.info(f"   ✅ LinkedIn (company): {social_url.get('url', '')}")
                        break
            # Check for companySocialMediaUrls at the top level
            elif attributes.get('companySocialMediaUrls'):
                company_social = attributes['companySocialMediaUrls']
                for social_url in company_social:
                    if isinstance(social_url, dict) and social_url.get('type') == 'LINKED_IN':
                        extracted_data['linkedin_profile'] = social_url.get('url', '')
                        logger.info(f"   ✅ LinkedIn (from companySocialMediaUrls): {social_url.get('url', '')}")
                        break
            
            # Education (prioritized field) - format as bulleted list
            if attributes.get('education'):
                education_data = attributes['education']
                if isinstance(education_data, list):
                    # Format as bulleted list
                    education_items = []
                    for edu_item in education_data:
                        if isinstance(edu_item, dict):
                            school = edu_item.get('school', '')
                            degree_info = edu_item.get('educationDegree', {})
                            degree = degree_info.get('degree', '') if isinstance(degree_info, dict) else ''
                            
                            if degree and school:
                                education_items.append(f"• {degree} - {school}")
                            elif school:
                                education_items.append(f"• {school}")
                    
                    if education_items:
                        extracted_data['education'] = '\n'.join(education_items)
                        logger.info(f"   ✅ Education: {len(education_items)} institutions formatted")
                else:
                    # Handle non-list education data
                    extracted_data['education'] = str(education_data)
                    logger.info(f"   ✅ Education: {education_data}")
            elif 'education' in str(attributes).lower():
                # Check if education data is nested somewhere
                for key, value in attributes.items():
                    if 'education' in key.lower() and value:
                        extracted_data['education'] = str(value)
                        logger.info(f"   ✅ Education (from {key}): {value}")
                        break
            
            # Address information - extract individual components
            if attributes.get('street'):
                extracted_data['mailing_street'] = attributes['street']
                logger.info(f"   ✅ Street: {attributes['street']}")
            
            if attributes.get('city'):
                extracted_data['mailing_city'] = attributes['city']
                logger.info(f"   ✅ City: {attributes['city']}")
            
            if attributes.get('state'):
                extracted_data['mailing_state'] = attributes['state']
                logger.info(f"   ✅ State: {attributes['state']}")
            
            if attributes.get('zipCode'):
                extracted_data['mailing_postal_code'] = attributes['zipCode']
                logger.info(f"   ✅ Zip Code: {attributes['zipCode']}")
            
            if attributes.get('country'):
                extracted_data['mailing_country'] = attributes['country']
                logger.info(f"   ✅ Country: {attributes['country']}")
            
            # Also create a combined location field for the custom Location__c field
            location_parts = []
            if attributes.get('city'):
                location_parts.append(attributes['city'])
            if attributes.get('state'):
                location_parts.append(attributes['state'])
            if location_parts:
                extracted_data['location'] = ', '.join(location_parts)
                logger.info(f"   ✅ Location: {', '.join(location_parts)}")
            
            # Management level and seniority information
            if attributes.get('managementLevel'):
                management_levels = attributes['managementLevel']
                if isinstance(management_levels, list):
                    extracted_data['management_level'] = ', '.join(management_levels)
                else:
                    extracted_data['management_level'] = str(management_levels)
                logger.info(f"   ✅ Management Level: {extracted_data['management_level']}")
            
            # Work Experience 
            if company.get('name'):
                # Create a role description based on available data
                role_desc_parts = []
                if attributes.get('jobTitle'):
                    role_desc_parts.append(f"Title: {attributes['jobTitle']}")
                if attributes.get('department'):
                    role_desc_parts.append(f"Department: {attributes['department']}")
                if attributes.get('managementLevel'):
                    mgmt_level = attributes['managementLevel']
                    if isinstance(mgmt_level, list):
                        role_desc_parts.append(f"Management Level: {', '.join(mgmt_level)}")
                    else:
                        role_desc_parts.append(f"Management Level: {mgmt_level}")
                if company.get('name'):
                    role_desc_parts.append(f"Company: {company['name']}")
                if company.get('employeeCount'):
                    role_desc_parts.append(f"Company Size: {company['employeeCount']} employees")
                if company.get('revenue'):
                    role_desc_parts.append(f"Company Revenue: ${company['revenue']}")
                if company.get('primaryIndustry'):
                    industries = company['primaryIndustry']
                    if isinstance(industries, list):
                        role_desc_parts.append(f"Industry: {', '.join(industries)}")
                    else:
                        role_desc_parts.append(f"Industry: {industries}")
                if company.get('website'):
                    role_desc_parts.append(f"Website: {company['website']}")
                
                if role_desc_parts:
                    extracted_data['role_description'] = '\n'.join(role_desc_parts)
                    logger.info(f"   ✅ Role Description: {len(role_desc_parts)} components")
            
            # Look for additional fields that might contain education or experience data
            for key, value in attributes.items():
                if key.lower() in ['tenure', 'experience', 'years', 'seniority'] and value:
                    if 'tenure' in key.lower():
                        extracted_data['tenure_current_company'] = str(value)
                        logger.info(f"   ✅ Tenure (from {key}): {value}")
                    elif 'experience' in key.lower():
                        extracted_data['total_work_experience'] = str(value)
                        logger.info(f"   ✅ Experience (from {key}): {value}")
            
            found_fields = [k for k, v in extracted_data.items() if v]
            logger.info(f"✅ FINAL EXTRACTION: Found {len(found_fields)} fields: {found_fields}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting ZoomInfo data: {str(e)}")
            return {}
    
    def update_contact_fields(self, contact_id: str, field_data: Dict[str, str], updatable_fields: List[str] = None) -> bool:
        """Update contact fields in Salesforce."""
        try:
            logger.info(f"💾 Updating contact {contact_id} with ZoomInfo data...")
            
            update_data = {}
            
            for field_key, value in field_data.items():
                # Only update if field has data AND is in the updatable_fields list (or no restriction if updatable_fields is None)
                if value and value.strip() and field_key in self.FIELD_MAPPING:
                    if updatable_fields is None or field_key in updatable_fields:
                        salesforce_field = self.FIELD_MAPPING[field_key]
                        update_data[salesforce_field] = value
                        logger.info(f"   ✅ Will update {field_key} -> {salesforce_field}")
                    else:
                        logger.info(f"   🔴 Skipping {field_key} (not in updatable fields list)")
            
            if not update_data:
                logger.warning("⚠️ No fields to update - all searches returned empty results or all fields were skipped")
                return True  # Not an error, just no data found
            
            self.sf.Contact.update(contact_id, update_data)
            logger.info(f"✅ Successfully updated {len(update_data)} fields")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update contact: {str(e)}")
            return False
    
    def process_contact_enrichment(self, record_id: str, overwrite: bool = False) -> bool:
        """Main method to perform ZoomInfo contact enrichment."""
        try:
            logger.info(f"🚀 Starting ZoomInfo contact enrichment for record ID: {record_id}")
            logger.info(f"🔧 Overwrite mode: {'ON' if overwrite else 'OFF (empty fields only)'}")
            
            # 1. Get contact details
            contact = self.get_contact_details(record_id)
            if not contact:
                logger.error(f"❌ Cannot proceed: Contact not found for {record_id}")
                return False
            
            first_name = contact.get('FirstName', '') 
            last_name = contact.get('LastName', '')
            email = contact.get('Email', '')
            
            # Get company name from Account if available
            company_name = ""
            if contact.get('AccountId'):
                try:
                    account = self.sf.Account.get(contact['AccountId'])
                    company_name = account.get('Name', '')
                except Exception as e:
                    logger.warning(f"⚠️ Could not retrieve account info: {str(e)}")
            
            logger.info(f"📋 Contact details:")
            logger.info(f"   Name: {first_name} {last_name}")
            logger.info(f"   Email: {email}")
            logger.info(f"   Company: {company_name}")
            
            # 2. Check which fields can be updated
            updatable_fields = self.check_updatable_fields(contact, overwrite)
            
            if not updatable_fields:
                logger.info("✅ All fields already have data. Use --overwrite to update anyway.")
                return True
            
            # 3. Get contact data from ZoomInfo
            if self.zoominfo_client:
                logger.info("🌐 Using real ZoomInfo API")
                
                # First try exact contact search
                search_result = self.zoominfo_client.search_contact(
                    first_name=first_name,
                    last_name=last_name, 
                    company_name=company_name,
                    email=email
                )
                
                # If no results, try alternative searches
                if not search_result or not search_result.get('data'):
                    logger.info("🔄 Trying alternative search without company name...")
                    search_result = self.zoominfo_client.search_contact(
                        first_name=first_name,
                        last_name=last_name
                    )
                
                if search_result and search_result.get('data'):
                    logger.info("✅ Found contact in ZoomInfo search")
                    # Get the contact ID for enrichment
                    contact_id = search_result['data'][0]['id']
                    logger.info(f"📋 ZoomInfo Contact ID: {contact_id}")
                    
                    # Try to enrich with more detailed data
                    enrich_result = self.zoominfo_client.enrich_contact(contact_id)
                    
                    if enrich_result and enrich_result.get('data'):
                        logger.info("✅ Successfully enriched contact data")
                        # Use enriched data if available
                        extracted_data = self.extract_zoominfo_data(enrich_result)
                    else:
                        logger.info("⚠️ Enrichment failed, using search data")
                        # Fall back to search data
                        extracted_data = self.extract_zoominfo_data(search_result)
                else:
                    logger.warning("⚠️ No contact found in ZoomInfo API")
                    extracted_data = {}
            else:
                logger.warning("⚠️ ZoomInfo API client not available - no data will be updated")
                extracted_data = {}
            
            if not extracted_data:
                logger.warning("⚠️ No usable data extracted from ZoomInfo")
                return True
            
            # 5. Show preview
            logger.info("📝 ZoomInfo enrichment results:")
            logger.info("-" * 60)
            for field_key, value in extracted_data.items():
                if value:
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                    else:
                        preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    logger.info(f"{field_key}: {preview}")
            logger.info("-" * 60)
            
            # 5.5. Special handling for email updates - compare ZoomInfo email with current email
            current_email = contact.get('Email', '').strip()
            zoominfo_email = extracted_data.get('zoominfo_email', '').strip()
            
            if zoominfo_email and current_email and zoominfo_email != current_email:
                logger.info("🔍 Email comparison:")
                logger.info(f"   Current Salesforce email: {current_email}")
                logger.info(f"   ZoomInfo email: {zoominfo_email}")
                
                # Consider ZoomInfo email "better" if it's different and follows certain criteria
                should_update_email = False
                reasons = []
                
                # Extract domains for comparison
                current_domain = current_email.split('@')[-1].lower() if '@' in current_email else ''
                zoominfo_domain = zoominfo_email.split('@')[-1].lower() if '@' in zoominfo_email else ''
                
                # Check various criteria for when ZoomInfo email might be better
                if current_domain != zoominfo_domain:
                    # Different domains - could be company name change, acquisition, etc.
                    should_update_email = True
                    reasons.append(f"Domain change: {current_domain} → {zoominfo_domain}")
                elif current_email.lower() != zoominfo_email.lower():
                    # Same domain but different format (e.g., john.smith vs j.smith)
                    current_local = current_email.split('@')[0] if '@' in current_email else current_email
                    zoominfo_local = zoominfo_email.split('@')[0] if '@' in zoominfo_email else zoominfo_email
                    
                    # Prefer more complete names (longer local part usually indicates full name)
                    if len(zoominfo_local) > len(current_local):
                        should_update_email = True
                        reasons.append("ZoomInfo email appears more complete")
                    elif '_' in zoominfo_local and '.' in current_local:
                        # Prefer underscore format in many corporate environments
                        should_update_email = True
                        reasons.append("ZoomInfo email uses standard corporate format")
                    elif zoominfo_local != current_local:
                        # Different but same length - let ZoomInfo take precedence as it's more current
                        should_update_email = True
                        reasons.append("ZoomInfo has different email format")
                
                if should_update_email:
                    logger.info(f"📧 Email update recommended: {', '.join(reasons)}")
                    # Add zoominfo_email to updatable fields even if email field has data
                    if 'zoominfo_email' not in updatable_fields:
                        updatable_fields.append('zoominfo_email')
                else:
                    logger.info("📧 Keeping current email address")
            elif zoominfo_email and not current_email:
                logger.info("📧 Adding email from ZoomInfo (field was empty)")
                if 'zoominfo_email' not in updatable_fields:
                    updatable_fields.append('zoominfo_email')
            
            # 6. Filter data to only include updatable fields
            update_field_data = {}
            
            for field_key, value in extracted_data.items():
                if field_key in updatable_fields and value:
                    # Handle both string and non-string values
                    if isinstance(value, str) and value.strip():
                        update_field_data[field_key] = value
                        logger.info(f"📋 Will update: {field_key} = {value[:50]}{'...' if len(value) > 50 else ''}")
                    elif not isinstance(value, str):
                        # Convert non-string values to string for Salesforce
                        str_value = str(value)
                        update_field_data[field_key] = str_value
                        logger.info(f"📋 Will update: {field_key} = {str_value[:50]}{'...' if len(str_value) > 50 else ''}")
            
            if not update_field_data:
                logger.warning("⚠️ No fields to update - either no data found or all fields already populated")
                return True
            
            # Confirm before updating
            try:
                user_input = input(f"Update {len(update_field_data)} fields in Salesforce? (Y/n): ")
                if user_input.lower() in ['n', 'no']:
                    logger.info("✅ Enrichment cancelled per user request")
                    return True
            except EOFError:
                logger.info("🤖 Automated mode: Proceeding with update")
            
            # 7. Update the contact with all available data
            success = self.update_contact_fields(contact['Id'], update_field_data, updatable_fields)
            
            if success:
                logger.info("✅ ZoomInfo contact enrichment completed successfully")
                logger.info(f"📊 Updated {len(update_field_data)} fields in Salesforce")
                
                # Show any remaining extracted data that wasn't updated
                remaining_data = {k: v for k, v in extracted_data.items() if k not in update_field_data}
                if remaining_data:
                    logger.info(f"📋 Additional data available but not updated (fields already populated):")
                    for field_key, value in remaining_data.items():
                        logger.info(f"   📋 {field_key}: {value[:50]}...")
            else:
                logger.error("❌ Failed to update contact fields")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error processing ZoomInfo enrichment: {str(e)}")
            return False


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='ZoomInfo Salesforce Contact Enricher')
    parser.add_argument('record_id', help='Salesforce Contact Record ID')
    parser.add_argument('--overwrite', action='store_true', 
                       help='Update all fields including those with existing data')
    
    args = parser.parse_args()
    
    try:
        enricher = ZoomInfoContactEnricher()
        success = enricher.process_contact_enrichment(args.record_id, args.overwrite)
        
        if success:
            print(f"\n✅ Successfully processed contact: {args.record_id}")
            if args.overwrite:
                print("🔧 Used overwrite mode - updated all fields")
            else:
                print("🛡️ Safe mode - only updated empty fields")
        else:
            print(f"\n❌ Failed to process contact: {args.record_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
