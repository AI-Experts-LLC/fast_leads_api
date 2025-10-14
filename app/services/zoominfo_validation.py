"""
ZoomInfo Contact Validation Service for Prospect Discovery

⚠️ DISABLED BY DEFAULT - OAuth authentication issues on Railway

Step 4: Validates and enriches contact information (email, phone) using ZoomInfo API.
Compares LinkedIn data with ZoomInfo data and uses the most accurate information.

This service is disabled by default in the Step 4 endpoint due to ZoomInfo's OAuth
requirements which are incompatible with Railway's serverless deployment.
To enable, pass enable_zoominfo=true in the API request.
"""

import os
import logging
import base64
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class ZoomInfoValidationService:
    """Service for validating and enriching contact information using ZoomInfo API"""

    def __init__(self):
        """Initialize ZoomInfo API client"""
        self.api_key = os.getenv('ZOOMINFO_API_KEY')
        self.client_id = os.getenv('ZOOMINFO_CLIENT_ID')
        self.client_secret = os.getenv('ZOOMINFO_CLIENT_SECRET')
        self.access_token = os.getenv('ZOOMINFO_ACCESS_TOKEN')
        self.base_url = "https://api.zoominfo.com/gtm/data/v1"

        # Check for credentials
        if not self.access_token and not self.api_key and not (self.client_id and self.client_secret):
            logger.warning("⚠️ No ZoomInfo credentials found - validation will be skipped")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ ZoomInfo validation service initialized")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for ZoomInfo API requests"""
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

    async def search_contact(
        self,
        first_name: str,
        last_name: str,
        company_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a contact in ZoomInfo

        Args:
            first_name: Contact's first name
            last_name: Contact's last name
            company_name: Company name

        Returns:
            ZoomInfo search result or None
        """
        try:
            if not self.enabled:
                return None

            logger.info(f"🔍 Searching ZoomInfo: {first_name} {last_name} at {company_name}")

            url = f"{self.base_url}/contacts/search"

            search_criteria = {
                "firstName": first_name,
                "lastName": last_name
            }

            if company_name:
                search_criteria["companyName"] = company_name

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

                if contacts:
                    logger.info(f"✅ Found {len(contacts)} contacts in ZoomInfo")
                    return data
                else:
                    logger.info("📭 No contacts found in ZoomInfo")
                    return None
            else:
                logger.warning(f"⚠️ ZoomInfo search failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error searching ZoomInfo: {str(e)}")
            return None

    async def enrich_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Enrich contact with detailed information

        Args:
            contact_id: ZoomInfo contact ID

        Returns:
            Enriched contact data or None
        """
        try:
            if not self.enabled:
                return None

            logger.info(f"📈 Enriching ZoomInfo contact: {contact_id}")

            url = f"{self.base_url}/contacts/enrich"

            output_fields = [
                "id", "email", "firstName", "lastName", "jobTitle",
                "mobilePhone", "directPhone", "companyName",
                "city", "state", "country", "street", "zipCode",
                "education", "managementLevel", "companyWebsite"
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
                logger.info("✅ Successfully enriched contact")
                return data
            else:
                logger.warning(f"⚠️ ZoomInfo enrichment failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error enriching contact: {str(e)}")
            return None

    def _extract_contact_info(self, zoominfo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract contact information from ZoomInfo response

        Args:
            zoominfo_data: ZoomInfo API response

        Returns:
            Extracted contact information
        """
        try:
            contacts = zoominfo_data.get('data', [])
            if not contacts:
                return {}

            # Use the first (best match) contact
            contact = contacts[0]
            attributes = contact.get('attributes', {})

            extracted = {
                'zoominfo_id': contact.get('id'),
                'first_name': attributes.get('firstName'),
                'last_name': attributes.get('lastName'),
                'email': attributes.get('email'),
                'mobile_phone': attributes.get('mobilePhone'),
                'direct_phone': attributes.get('directPhone'),
                'job_title': attributes.get('jobTitle'),
                'company_name': attributes.get('companyName'),
                'city': attributes.get('city'),
                'state': attributes.get('state'),
                'country': attributes.get('country'),
                'street': attributes.get('street'),
                'zip_code': attributes.get('zipCode'),
                'education': attributes.get('education'),
                'management_level': attributes.get('managementLevel'),
                'company_website': attributes.get('companyWebsite')
            }

            # Remove None values
            return {k: v for k, v in extracted.items() if v is not None}

        except Exception as e:
            logger.error(f"❌ Error extracting contact info: {str(e)}")
            return {}

    def _compare_and_select(
        self,
        linkedin_value: Optional[str],
        zoominfo_value: Optional[str],
        field_name: str
    ) -> tuple[Optional[str], str]:
        """
        Compare LinkedIn and ZoomInfo values and select the best one

        Args:
            linkedin_value: Value from LinkedIn
            zoominfo_value: Value from ZoomInfo
            field_name: Name of the field being compared

        Returns:
            Tuple of (selected_value, source_name)
        """
        # If both are None or empty
        if not linkedin_value and not zoominfo_value:
            return None, "none"

        # If only one has a value
        if not linkedin_value and zoominfo_value:
            return zoominfo_value, "zoominfo"
        if linkedin_value and not zoominfo_value:
            return linkedin_value, "linkedin"

        # Both have values - compare them
        linkedin_clean = str(linkedin_value).strip().lower()
        zoominfo_clean = str(zoominfo_value).strip().lower()

        if linkedin_clean == zoominfo_clean:
            return linkedin_value, "both_match"

        # Values differ - prefer ZoomInfo for contact info as it's more up-to-date
        if field_name in ['email', 'mobile_phone', 'direct_phone']:
            logger.info(f"   🔄 {field_name} differs:")
            logger.info(f"      LinkedIn: {linkedin_value}")
            logger.info(f"      ZoomInfo: {zoominfo_value}")
            logger.info(f"      ✅ Using ZoomInfo value (more current)")
            return zoominfo_value, "zoominfo_preferred"

        # For other fields, prefer LinkedIn if available
        return linkedin_value, "linkedin_preferred"

    async def validate_and_enrich_prospect(
        self,
        prospect: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and enrich a single prospect with ZoomInfo data

        Args:
            prospect: Prospect data from Step 3 (with linkedin_data and ai_ranking)

        Returns:
            Enhanced prospect with validated contact information
        """
        try:
            if not self.enabled:
                logger.info("⚠️ ZoomInfo validation disabled - skipping")
                prospect['zoominfo_validation'] = {
                    'status': 'skipped',
                    'reason': 'ZoomInfo credentials not configured'
                }
                return prospect

            linkedin_data = prospect.get('linkedin_data', {})

            # Extract name and company from LinkedIn data
            first_name = linkedin_data.get('first_name') or linkedin_data.get('name', '').split()[0] if linkedin_data.get('name') else None
            last_name = linkedin_data.get('last_name') or ' '.join(linkedin_data.get('name', '').split()[1:]) if linkedin_data.get('name') else None
            company_name = linkedin_data.get('company_name') or linkedin_data.get('company')

            if not first_name or not last_name:
                logger.warning(f"⚠️ Missing name for prospect - skipping ZoomInfo validation")
                prospect['zoominfo_validation'] = {
                    'status': 'skipped',
                    'reason': 'Missing first or last name'
                }
                return prospect

            logger.info(f"🔍 Validating: {first_name} {last_name}")

            # Search ZoomInfo
            search_result = await self.search_contact(first_name, last_name, company_name)

            if not search_result or not search_result.get('data'):
                logger.info(f"📭 Not found in ZoomInfo: {first_name} {last_name}")
                prospect['zoominfo_validation'] = {
                    'status': 'not_found',
                    'searched': True,
                    'contact_verified': False
                }
                return prospect

            # Get ZoomInfo contact ID
            zoominfo_id = search_result['data'][0].get('id')

            # Enrich with detailed data
            enrich_result = await self.enrich_contact(zoominfo_id)

            if enrich_result:
                zoominfo_info = self._extract_contact_info(enrich_result)
            else:
                zoominfo_info = self._extract_contact_info(search_result)

            # Compare and select best values for each field
            validation_details = {
                'status': 'validated',
                'searched': True,
                'contact_verified': True,
                'zoominfo_id': zoominfo_id,
                'comparisons': {}
            }

            # Compare email
            email_value, email_source = self._compare_and_select(
                linkedin_data.get('email'),
                zoominfo_info.get('email'),
                'email'
            )
            if email_value:
                linkedin_data['email'] = email_value
                validation_details['comparisons']['email'] = {
                    'source': email_source,
                    'linkedin_value': linkedin_data.get('email'),
                    'zoominfo_value': zoominfo_info.get('email'),
                    'selected_value': email_value
                }

            # Compare mobile phone
            mobile_value, mobile_source = self._compare_and_select(
                linkedin_data.get('mobile_number'),
                zoominfo_info.get('mobile_phone'),
                'mobile_phone'
            )
            if mobile_value:
                linkedin_data['mobile_number'] = mobile_value
                validation_details['comparisons']['mobile_phone'] = {
                    'source': mobile_source,
                    'linkedin_value': linkedin_data.get('mobile_number'),
                    'zoominfo_value': zoominfo_info.get('mobile_phone'),
                    'selected_value': mobile_value
                }

            # Add direct phone if available from ZoomInfo
            if zoominfo_info.get('direct_phone'):
                linkedin_data['direct_phone'] = zoominfo_info['direct_phone']
                validation_details['comparisons']['direct_phone'] = {
                    'source': 'zoominfo',
                    'linkedin_value': None,
                    'zoominfo_value': zoominfo_info['direct_phone'],
                    'selected_value': zoominfo_info['direct_phone']
                }

            # Store all ZoomInfo data for reference
            validation_details['zoominfo_data'] = zoominfo_info

            prospect['zoominfo_validation'] = validation_details
            prospect['linkedin_data'] = linkedin_data

            logger.info(f"✅ Validated and enriched: {first_name} {last_name}")

            return prospect

        except Exception as e:
            logger.error(f"❌ Error validating prospect: {str(e)}")
            prospect['zoominfo_validation'] = {
                'status': 'error',
                'error': str(e)
            }
            return prospect

    async def validate_and_enrich_prospects(
        self,
        prospects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate and enrich multiple prospects with ZoomInfo data

        Args:
            prospects: List of prospects from Step 3

        Returns:
            Results with validated prospects
        """
        try:
            if not self.enabled:
                return {
                    "success": False,
                    "error": "ZoomInfo validation service not configured",
                    "prospects": prospects
                }

            logger.info(f"🔍 Starting ZoomInfo validation for {len(prospects)} prospects")

            validated_prospects = []
            stats = {
                'total': len(prospects),
                'validated': 0,
                'not_found': 0,
                'skipped': 0,
                'errors': 0,
                'email_enriched': 0,
                'phone_enriched': 0
            }

            # Process each prospect
            import asyncio
            tasks = [self.validate_and_enrich_prospect(prospect) for prospect in prospects]
            validated_prospects = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error prospects
            for i, result in enumerate(validated_prospects):
                if isinstance(result, Exception):
                    logger.error(f"❌ Error validating prospect {i}: {result}")
                    validated_prospects[i] = prospects[i]
                    validated_prospects[i]['zoominfo_validation'] = {
                        'status': 'error',
                        'error': str(result)
                    }

            # Calculate statistics
            for prospect in validated_prospects:
                validation = prospect.get('zoominfo_validation', {})
                status = validation.get('status', 'unknown')

                if status == 'validated':
                    stats['validated'] += 1
                    comparisons = validation.get('comparisons', {})
                    if 'email' in comparisons:
                        stats['email_enriched'] += 1
                    if 'mobile_phone' in comparisons or 'direct_phone' in comparisons:
                        stats['phone_enriched'] += 1
                elif status == 'not_found':
                    stats['not_found'] += 1
                elif status == 'skipped':
                    stats['skipped'] += 1
                elif status == 'error':
                    stats['errors'] += 1

            logger.info(f"✅ ZoomInfo validation complete:")
            logger.info(f"   • Validated: {stats['validated']}/{stats['total']}")
            logger.info(f"   • Email enriched: {stats['email_enriched']}")
            logger.info(f"   • Phone enriched: {stats['phone_enriched']}")
            logger.info(f"   • Not found: {stats['not_found']}")
            logger.info(f"   • Skipped: {stats['skipped']}")

            return {
                "success": True,
                "prospects": validated_prospects,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"❌ Error in ZoomInfo validation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prospects": prospects
            }


# Global instance
zoominfo_validation_service = ZoomInfoValidationService()
