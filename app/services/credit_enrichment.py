#!/usr/bin/env python3
"""
Credit Rating Enrichment Service
Uses EDF-X API to enrich company data with Moody's credit ratings and PD values.
Generalized version for any company type with website-based matching.
"""

import json
import logging
import requests
import time
import re
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urljoin, urlparse
import os

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CompanyRecord:
    """Data class for company information."""
    name: str
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

@dataclass
class CreditInfo:
    """Data class for credit information from EDF-X."""
    entity_id: Optional[str] = None
    pd_value: Optional[float] = None
    implied_rating: Optional[str] = None
    confidence: Optional[str] = None
    confidence_translated: Optional[str] = None
    as_of_date: Optional[str] = None
    search_success: bool = False
    error_message: Optional[str] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    selected_entity: Optional[Dict[str, Any]] = None
    matching_logic: Optional[str] = None

class EDFXAuthenticator:
    """Handles OAuth 2.0 authentication for EDF-X API."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.token = None
        self.token_expires_at = 0
        self.auth_url = "https://sso.moodysanalytics.com/sso-api/v1/token"
    
    def get_token(self) -> str:
        """Get valid authentication token, refreshing if necessary."""
        if self.token and time.time() < self.token_expires_at:
            return self.token
        
        return self._refresh_token()
    
    def _refresh_token(self) -> str:
        """Refresh authentication token."""
        logger.info("Refreshing EDF-X authentication token...")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        data = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password',
            'scope': 'openid'
        }
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data['id_token']
            # Set expiration to 55 minutes (5 minutes before actual expiry)
            self.token_expires_at = time.time() + (55 * 60)
            
            logger.info("Successfully refreshed authentication token")
            return self.token
            
        except requests.RequestException as e:
            logger.error(f"Failed to authenticate with EDF-X API: {e}")
            raise

class EDFXClient:
    """Client for interacting with EDF-X API."""
    
    def __init__(self, authenticator: EDFXAuthenticator):
        self.authenticator = authenticator
        self.base_url = "https://api-lb.edfx.moodysanalytics.com/"
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        token = self.authenticator.get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated request to EDF-X API."""
        url = urljoin(self.base_url, endpoint)
        headers = self._get_headers()
        
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=60)
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 422:
                logger.error(f"422 Error for {endpoint}. Response: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response text: {e.response.text}")
            return None
    
    def search_entity(self, company_name: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Search for entity by company name."""
        endpoint = "entity/v1/search"
        data = {
            "query": company_name,
            "limit": limit
        }
        
        logger.debug(f"Searching for entity: {company_name}")
        response = self._make_request(endpoint, data)
        
        if response and 'entities' in response:
            return response['entities']
        return None
    
    def get_pd_values(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get PD values and credit rating for entity."""
        endpoint = "edfx/v1/entities/pds"
        data = {
            "entities": [{"entityId": entity_id}]
        }
        
        logger.debug(f"Getting PD values for entity: {entity_id}")
        response = self._make_request(endpoint, data)
        
        if response and 'entities' in response and response['entities']:
            return response['entities'][0]
        return None

class CreditEnrichmentService:
    """Main service for enriching company data with credit information."""
    
    def __init__(self):
        self.authenticator = None
        self.client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of the service."""
        if self._initialized:
            return
        
        # Get credentials from environment variables
        username = os.getenv('EDFX_USERNAME')
        password = os.getenv('EDFX_PASSWORD')
        
        if not username or not password:
            raise ValueError("EDF-X credentials not found in environment variables. Please set EDFX_USERNAME and EDFX_PASSWORD.")
        
        self.authenticator = EDFXAuthenticator(username, password)
        self.client = EDFXClient(self.authenticator)
        self._initialized = True
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison by removing protocol, www, and trailing characters.
        
        Args:
            url: Raw URL string
            
        Returns:
            Normalized URL string
        """
        if not url:
            return ""
        
        # Convert to lowercase
        url = url.lower().strip()
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        
        # Remove www prefix
        url = re.sub(r'^www\.', '', url)
        
        # Remove trailing slash and common trailing characters
        url = url.rstrip('/')
        url = url.rstrip('.,;')
        
        # Remove common path suffixes that might not match exactly
        url = re.sub(r'/home$|/index\.html?$|/index\.php$', '', url)
        
        return url
    
    def _calculate_url_similarity(self, url1: str, url2: str) -> float:
        """
        Calculate similarity score between two URLs.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            Similarity score between 0 and 1
        """
        norm_url1 = self._normalize_url(url1)
        norm_url2 = self._normalize_url(url2)
        
        if not norm_url1 or not norm_url2:
            return 0.0
        
        # Exact match
        if norm_url1 == norm_url2:
            return 1.0
        
        # Check if one is a subdomain of the other
        if norm_url1 in norm_url2 or norm_url2 in norm_url1:
            return 0.8
        
        # Check domain similarity (extract domain from URL)
        def extract_domain(url):
            if '/' in url:
                return url.split('/')[0]
            return url
        
        domain1 = extract_domain(norm_url1)
        domain2 = extract_domain(norm_url2)
        
        if domain1 == domain2:
            return 0.9
        
        # Check if domains are similar (accounting for ccTLD differences)
        # Remove common TLDs for comparison
        base_domain1 = re.sub(r'\.(com|org|net|edu|gov|co\.uk|co\.in|de|fr|jp)$', '', domain1)
        base_domain2 = re.sub(r'\.(com|org|net|edu|gov|co\.uk|co\.in|de|fr|jp)$', '', domain2)
        
        if base_domain1 == base_domain2:
            return 0.7
        
        return 0.0
    
    def select_best_entity(self, entities: List[Dict[str, Any]], company: CompanyRecord) -> Tuple[Dict[str, Any], str]:
        """
        Select the best matching entity based on website and other criteria.
        
        Args:
            entities: List of entities from search results
            company: Company record with search criteria
            
        Returns:
            tuple: (selected_entity, matching_logic)
        """
        if not entities:
            return None, "No entities found"
        
        if len(entities) == 1:
            return entities[0], f"Single entity match: {entities[0].get('internationalName', 'Unknown')}"
        
        logger.info(f"Multiple entities found for {company.name}. Using website matching.")
        
        # Score each entity
        scored_entities = []
        
        for entity in entities:
            score = 0
            reasons = []
            
            entity_website = entity.get('entityWebsite', '') or ''
            
            # Website matching is the primary criteria
            if company.website and entity_website:
                url_similarity = self._calculate_url_similarity(company.website, entity_website)
                if url_similarity >= 0.9:
                    score += 20
                    reasons.append(f"Website exact match: {entity_website}")
                elif url_similarity >= 0.7:
                    score += 15
                    reasons.append(f"Website domain match: {entity_website}")
                elif url_similarity >= 0.5:
                    score += 10
                    reasons.append(f"Website similar: {entity_website}")
                else:
                    # Heavy penalty for completely mismatched domains
                    score -= 15
                    reasons.append(f"Website mismatch penalty: {entity_website}")
            elif company.website and not entity_website:
                # Moderate penalty for missing website when we expect one
                score -= 5
                reasons.append("Missing website (expected one)")
            
            # Secondary criteria for tie-breaking
            
            # Prefer US-based entities (strong preference)
            entity_country = entity.get('entityCountryName', '') or entity.get('countryName', '')
            if entity_country == "United States of America":
                score += 8
                reasons.append("US-based entity")
            
            # Geographic matching (if available)
            if company.city and company.state:
                entity_city = (entity.get('entityContactCity', '') or entity.get('contactCity', '')).upper().strip()
                entity_state = (entity.get('entityContactStateProvince', '') or entity.get('contactStateProvince', '')).upper().strip()
                
                if entity_city == company.city.upper().strip():
                    score += 5
                    reasons.append(f"City match: {entity_city}")
                
                if entity_state == company.state.upper().strip():
                    score += 3
                    reasons.append(f"State match: {entity_state}")
            
            # Prefer entities with financial data (strong preference)
            has_financials = entity.get('hasFinancials', '')
            if 'Full' in has_financials:
                score += 10
                reasons.append("Has full financials")
            elif has_financials and 'Insufficient' not in has_financials:
                score += 5
                reasons.append("Has some financials")
            elif has_financials == "Insufficient Financials":
                score -= 2
                reasons.append("Insufficient financials (penalty)")
            
            # Prefer larger entities (more likely to be the main company)
            size = entity.get('entitySize', '')
            if '4 - Very Large' in size:
                score += 2
                reasons.append(f"Very large entity: {size}")
            elif '3 - Large' in size:
                score += 1
                reasons.append(f"Large entity: {size}")
            
            # Prefer active entities
            entity_status = entity.get('entityStatus', '').upper()
            if 'ACTIVE' in entity_status or not entity_status:  # Empty status often means active
                score += 1
                reasons.append("Active entity")
            
            scored_entities.append({
                'entity': entity,
                'score': score,
                'reasons': reasons,
                'website': entity_website
            })
        
        # Sort by score (descending)
        scored_entities.sort(key=lambda x: x['score'], reverse=True)
        
        best_match = scored_entities[0]
        
        # If the best match has a very low score, it's likely not a good match
        if best_match['score'] <= 0:
            return None, f"No suitable entity found. Best match scored only {best_match['score']} points (likely unrelated company)"
        
        best_entity = best_match['entity']
        
        # Create detailed matching logic explanation
        logic_parts = [
            f"Selected from {len(entities)} options",
            f"Score: {best_match['score']}",
            f"Website: {best_match['website']}",
            f"Reasons: {', '.join(best_match['reasons']) if best_match['reasons'] else 'Default first match'}"
        ]
        
        matching_logic = " | ".join(logic_parts)
        
        logger.info(f"Selected entity: {best_entity.get('internationalName')} ({matching_logic})")
        
        return best_entity, matching_logic
    
    def _generate_search_variations(self, company_name: str) -> List[str]:
        """
        Generate variations of company name for searching.
        
        Args:
            company_name: Original company name
            
        Returns:
            List of name variations to try
        """
        variations = [company_name]  # Start with original name
        
        # Clean base name (remove existing suffixes)
        base_name = company_name.strip()
        
        # Remove common suffixes to get clean base name
        suffixes_to_remove = [
            r'\s+Inc\.?$', r'\s+LLC\.?$', r'\s+Corp\.?$', r'\s+Corporation\.?$',
            r'\s+Ltd\.?$', r'\s+Limited\.?$', r'\s+Co\.?$', r'\s+Company\.?$',
            r'\s+LP\.?$', r'\s+LLP\.?$'
        ]
        
        clean_base = base_name
        for suffix_pattern in suffixes_to_remove:
            clean_base = re.sub(suffix_pattern, '', clean_base, flags=re.IGNORECASE)
        
        # If we cleaned something, add the clean version
        if clean_base != base_name:
            variations.append(clean_base)
        
        # Add common corporate suffixes
        corporate_suffixes = ['Inc', 'Corp', 'Corporation', 'LLC', 'Ltd', 'Company', 'Co']
        
        for suffix in corporate_suffixes:
            # Add with period
            variation_with_period = f"{clean_base} {suffix}."
            if variation_with_period not in variations:
                variations.append(variation_with_period)
            
            # Add without period
            variation_without_period = f"{clean_base} {suffix}"
            if variation_without_period not in variations:
                variations.append(variation_without_period)
        
        # Also try with .com for web companies
        if 'website' in clean_base.lower() or any(web_term in clean_base.lower() 
                                                   for web_term in ['tech', 'software', 'digital', 'online']):
            variations.append(f"{clean_base}.com Inc")
        
        return variations[:8]  # Limit to 8 variations to avoid too many API calls

    def _translate_confidence_code(self, confidence_code: str) -> str:
        """
        Translate EDF-X confidence code into human-readable explanation.
        
        Args:
            confidence_code: EDF-X confidence code (e.g., "P-G-R", "PF-G-R-HQ")
            
        Returns:
            Human-readable explanation of the confidence code
        """
        if not confidence_code:
            return "No confidence information available"
            
        # Handle special bankruptcy case
        if confidence_code == "BKRPT":
            return "Entity is bankrupt or dissolved"
            
        parts = confidence_code.split('-')
        if len(parts) < 3:
            return f"Unknown confidence format: {confidence_code}"
            
        model_type = parts[0]
        data_quality = parts[1]
        data_age = parts[2]
        warnings = parts[3:] if len(parts) > 3 else []
        
        # Model Type translation
        model_desc = {
            'P': 'Public firm using CreditEdge model',
            'PF': 'Private firm with full financials using RiskCalc model',
            'PP': 'Private firm with partial financials using RiskCalc model',
            'PY': 'Private firm using Payment model (trade-payment data, no financials)',
            'PN': 'Private firm using Benchmark model (minimal/no financial information)'
        }.get(model_type, f'Unknown model ({model_type})')
        
        # Data Quality translation
        quality_desc = {
            'G': 'good quality financial data',
            'E': 'estimated financial data',
            'I': 'financial data that failed some quality checks',
            'M': 'minimal information (total assets/liabilities only)',
            'P': 'peer-driven benchmark model',
            'X': 'quality not applicable'
        }.get(data_quality, f'unknown quality ({data_quality})')
        
        # Data Age translation
        age_desc = {
            'R': 'recent financial statements (less than 18 months old)',
            'O': 'old financial statements (18-27 months old)',
            'S': 'stale financial statements (older than 27 months)',
            'X': 'age not applicable'
        }.get(data_age, f'unknown age ({data_age})')
        
        # Build base description
        description = f"{model_desc} with {quality_desc} and {age_desc}"
        
        # Add warning descriptions
        warning_descriptions = []
        for warning in warnings:
            warning_desc = {
                'ACT_IMP': 'entity is active but has experienced distress (default, rescue plan, or insolvency)',
                'NOT_ACT': 'entity is not active (inactive or dissolved)',
                'NOT_ACT_LIQ': 'entity is in liquidation',
                'HQ': 'entity is a branch - PD reflects headquarter\'s rating',
                'DUO': 'subsidiary PD inherited from domestic ultimate owner',
                'FLAG_L': 'legal form not included in model development sample',
                'FLAG_T': 'entity type not included in model development sample',
                'FLAG_S': 'industry sector not specific to model (NBFS or real estate)',
                'NN': 'no industry information available',
                'NR': 'industry proxy assigned from entity type'
            }.get(warning, f'unknown warning ({warning})')
            warning_descriptions.append(warning_desc)
        
        if warning_descriptions:
            description += f". Additional notes: {', '.join(warning_descriptions)}"
            
        return description

    async def enrich_company(self, company: CompanyRecord) -> CreditInfo:
        """
        Enrich a single company with credit information.
        Uses multiple search variations if initial search fails.
        
        Args:
            company: Company record to enrich
            
        Returns:
            CreditInfo object with enrichment results
        """
        self._ensure_initialized()
        logger.info(f"Processing company: {company.name}")
        
        # Generate search variations
        search_variations = self._generate_search_variations(company.name)
        logger.info(f"Will try {len(search_variations)} search variations: {search_variations}")
        
        best_result = None
        best_score = -999
        all_search_attempts = []
        
        try:
            for i, search_name in enumerate(search_variations):
                logger.info(f"Attempt {i+1}/{len(search_variations)}: Searching for '{search_name}'")
                
                # Search for entity
                entities = self.client.search_entity(search_name, limit=10)
                
                search_attempt = {
                    "search_name": search_name,
                    "entities_found": len(entities) if entities else 0,
                    "selected_entity": None,
                    "score": -999,
                    "matching_logic": "No entities found"
                }
                
                if not entities:
                    logger.info(f"No entities found for: {search_name}")
                    all_search_attempts.append(search_attempt)
                    continue
                
                # Select the best matching entity for this search
                selected_entity, matching_logic = self.select_best_entity(entities, company)
                
                if not selected_entity:
                    logger.info(f"No suitable entity selected for: {search_name}")
                    search_attempt["matching_logic"] = matching_logic
                    all_search_attempts.append(search_attempt)
                    continue
                
                # Extract score from matching logic
                score = 0
                if "Score: " in matching_logic:
                    try:
                        score_part = matching_logic.split("Score: ")[1].split(" |")[0]
                        score = int(score_part)
                    except:
                        score = 0
                
                search_attempt.update({
                    "selected_entity": selected_entity,
                    "score": score,
                    "matching_logic": matching_logic
                })
                all_search_attempts.append(search_attempt)
                
                logger.info(f"Search '{search_name}' scored {score} points")
                
                # If this is better than our best so far, save it
                if score > best_score:
                    best_score = score
                    best_result = {
                        "entities": entities,
                        "selected_entity": selected_entity,
                        "matching_logic": f"{matching_logic} | Search variation: '{search_name}'",
                        "search_attempts": all_search_attempts.copy()
                    }
                
                # If we found a really good match (score > 15), stop searching
                if score > 15:
                    logger.info(f"Found high-quality match with score {score}, stopping search")
                    break
                
                # Brief pause between searches
                await asyncio.sleep(0.2)
            
            # Use the best result we found
            if not best_result or best_score <= 0:
                logger.warning(f"No suitable entities found across all search variations for: {company.name}")
                return CreditInfo(
                    error_message=f"No suitable entities found across {len(search_variations)} search variations",
                    search_results=[],
                    matching_logic=f"Tried variations: {search_variations}. Best score: {best_score}"
                )
            
            entities = best_result["entities"]
            selected_entity = best_result["selected_entity"]
            matching_logic = best_result["matching_logic"]
            
            entity_id = selected_entity.get('entityId')
            
            if not entity_id:
                logger.warning(f"Selected entity has no ID for: {company.name}")
                return CreditInfo(
                    error_message="Selected entity has no ID",
                    search_results=entities,
                    selected_entity=selected_entity,
                    matching_logic=matching_logic
                )
            
            # Get PD values
            pd_data = self.client.get_pd_values(entity_id)
            if not pd_data:
                logger.warning(f"No PD data found for entity: {entity_id}")
                return CreditInfo(
                    entity_id=entity_id,
                    search_success=True,
                    error_message="No PD data available",
                    search_results=entities,
                    selected_entity=selected_entity,
                    matching_logic=matching_logic
                )
            
            # Extract credit information
            confidence_code = pd_data.get('confidence')
            credit_info = CreditInfo(
                entity_id=entity_id,
                pd_value=pd_data.get('pd'),
                implied_rating=pd_data.get('impliedRating'),
                confidence=confidence_code,
                confidence_translated=self._translate_confidence_code(confidence_code) if confidence_code else None,
                as_of_date=pd_data.get('asOfDate'),
                search_success=True,
                search_results=entities,
                selected_entity=selected_entity,
                matching_logic=matching_logic
            )
            
            logger.info(f"Successfully enriched: {company.name} - Rating: {credit_info.implied_rating} (Best score: {best_score})")
            return credit_info
            
        except Exception as e:
            logger.error(f"Error enriching company {company.name}: {e}")
            return CreditInfo(
                error_message=f"Error during enrichment: {str(e)}"
            )
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test EDF-X API connection.
        
        Returns:
            Dictionary with test results
        """
        try:
            self._ensure_initialized()
            # Test authentication
            token = self.authenticator.get_token()
            auth_success = bool(token)
            
            # Test PD endpoint with a known entity ID (Apple: US942404110)
            pd_test_success = False
            pd_test_data = None
            
            if auth_success:
                pd_data = self.client.get_pd_values("US942404110")
                pd_test_success = bool(pd_data)
                if pd_data:
                    pd_test_data = {
                        "entity_id": "US942404110",
                        "pd_value": pd_data.get('pd'),
                        "rating": pd_data.get('impliedRating'),
                        "confidence": pd_data.get('confidence')
                    }
            
            return {
                "success": True,
                "authentication": auth_success,
                "pd_endpoint": pd_test_success,
                "test_data": pd_test_data,
                "message": "EDF-X API connection test completed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "EDF-X API connection test failed"
            }

# Create service instance
credit_enrichment_service = CreditEnrichmentService()
