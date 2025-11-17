#!/usr/bin/env python3
"""
Web Search Account Enricher for Salesforce

Uses OpenAI's web_search tool to find real information about hospitals.
Splits into focused sections with separate web searches for better results.

Usage:
    python web_search_account_enricher.py "RECORD_ID" [--overwrite] [--include-financial]
"""

import os
import sys
import logging
import json
import re
import argparse
from typing import Optional, Dict, Any, List
from simple_salesforce import Salesforce
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time

# Import field validator for data quality
try:
    from .field_validator import FieldValidator
except ImportError:
    try:
        from field_validator import FieldValidator
    except ImportError:
        from enrichers.field_validator import FieldValidator

try:
    from .financial_enricher import FinancialEnricher
except ImportError:
    try:
        from financial_enricher import FinancialEnricher
    except ImportError:
        from enrichers.financial_enricher import FinancialEnricher

try:
    from .salesforce_credit_enricher import SalesforceAccountEnricher as CreditEnricher
except ImportError:
    try:
        from salesforce_credit_enricher import SalesforceAccountEnricher as CreditEnricher
    except ImportError:
        from enrichers.salesforce_credit_enricher import SalesforceAccountEnricher as CreditEnricher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI Configuration
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini-search-preview")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
WEB_TOOL_TYPE = os.getenv("OPENAI_WEB_SEARCH_TOOL_TYPE", "web_search")


class RecoverableHTTPError(Exception):
    pass


class WebSearchAccountEnricher:
    """Web search-enabled account enricher for Salesforce."""

    # Field mapping discovered from Salesforce
    FIELD_MAPPING = {
        'company_description': 'General_Company_Description__c',
        'hq_location': 'HQ_location__c',
        'employee_count': 'Employee_count__c',
        'geographic_footprint': 'Geographic_footprint__c',
        'company_news': 'General_Company_News__c',
        'capital_history': 'Capital_and_project_history__c',
        'future_capital': 'Past_future_capital_uses__c',
        'infrastructure_upgrades': 'Infrastructure_upgrades__c',
        'energy_projects': 'Energy_efficiency_projects__c',
        # Financial fields
        'recent_disclosures': 'Recent_disclosures__c',
        'wacc': 'Weighted_average_cost_of_capital__c',
        'debt_appetite': 'Debt_appetite_constraints__c',
        'other_debt': 'Debt__c',
        'financial_outlook': 'Long_term_financial_outlook__c',
        'off_balance_appetite': 'Off_balance_sheet_financing__c',  # Raw search data
        'off_balance_appetite_summary': 'Off_balance_sheet_financing__c',  # Synthesized summary (same field)
        'revenue': 'Revenue__c',
        'credit_quality': 'Company_Credit_Quality__c',
        'credit_quality_detailed': 'Company_Credit_Quality_Detailed__c',
    }
    
    def __init__(self, db_session=None, pending_updates_service=None):
        """Initialize the enricher with Salesforce and OpenAI connections."""
        self.sf = None
        self.openai_client = None
        self.financial_enricher = None
        self.credit_enricher = None
        self.db_session = db_session
        self.pending_updates_service = pending_updates_service

        # Load environment variables
        load_dotenv()

        self._connect_to_salesforce()
        self._setup_openai_client()
        self._setup_financial_enricher()
        self._setup_credit_enricher()
    
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
            
            test_result = self.sf.query("SELECT Id FROM User LIMIT 1")
            if test_result and test_result.get('totalSize', 0) > 0:
                logger.info("✅ Successfully connected to Salesforce")
            else:
                raise Exception("Connected but test query failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Salesforce: {str(e)}")
            raise
    
    def _setup_openai_client(self) -> None:
        """Setup OpenAI client with web search capabilities."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in environment variables")
            
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI web search client configured")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI: {str(e)}")
            raise

    def _setup_financial_enricher(self) -> None:
        """Setup the financial enricher module."""
        try:
            self.financial_enricher = FinancialEnricher()
            logger.info("✅ Financial enricher module configured")
        except Exception as e:
            logger.error(f"❌ Failed to setup financial enricher: {str(e)}")
            raise

    def _setup_credit_enricher(self) -> None:
        """Setup the credit enricher module."""
        try:
            # Credit enricher already initializes its own Salesforce connection
            self.credit_enricher = CreditEnricher()
            logger.info("✅ Credit enricher module configured")
        except Exception as e:
            logger.error(f"❌ Failed to setup credit enricher: {str(e)}")
            raise
    
    def get_account_details(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get account record with details."""
        try:
            logger.info(f"🔍 Retrieving account details: {record_id}")
            
            account = self.sf.Account.get(record_id)
            if account:
                logger.info(f"✅ Found account: {account.get('Name', 'Unknown')}")
                return account
            else:
                logger.warning(f"❌ No account found for ID: {record_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving account: {str(e)}")
            return None
    
    def check_updatable_fields(self, account: Dict[str, Any], overwrite: bool = False) -> List[str]:
        """Check which fields can be updated."""
        updatable_fields = []
        
        logger.info("📋 Checking field status:")
        
        for field_key, salesforce_field in self.FIELD_MAPPING.items():
            current_value = account.get(salesforce_field, '')
            is_empty = not current_value or (isinstance(current_value, str) and len(current_value.strip()) == 0)
            
            if overwrite or is_empty:
                updatable_fields.append(field_key)
                status = "🟢 WILL UPDATE" if overwrite else "🟡 EMPTY - WILL UPDATE"
            else:
                status = "🔴 HAS DATA - SKIP"
            
            preview = ""
            if current_value and isinstance(current_value, str):
                preview = f" (current: {current_value[:50]}{'...' if len(current_value) > 50 else ''})"
            
            logger.info(f"   {field_key}: {status}{preview}")
        
        logger.info(f"📊 Summary: {len(updatable_fields)}/{len(self.FIELD_MAPPING)} fields can be updated")
        return updatable_fields
    
    def web_search_company_info(self, hospital_name: str, location: str, website: str = None) -> Optional[Dict[str, str]]:
        """Search for general company information using web search."""
        
        try:
            logger.info(f"🌐 Searching for general company info: {hospital_name}")
            
            # Enhanced prompt for comprehensive company information
            enhanced_prompt = f"""Research comprehensive information about {hospital_name} in {location}.

Search for and provide the following information in JSON format:

1. Company Description: A brief 100-150 word professional description
2. HQ Location: Main headquarters address or location
3. Employee Count: Number of employees (approximate if exact not available)
4. Geographic Footprint: Primary service area as a concise regional description (MAX 200 chars - e.g., "Northwest Montana", "Boise metro area and surrounding counties", "Eastern Idaho and Western Wyoming")
5. General Company News: Recent significant news, achievements, or developments

Return a JSON object with these exact keys:
- company_description: Brief professional description (100-150 words, NO source citations)
- hq_location: Headquarters location/address
- employee_count: Number of employees (as number or range)
- geographic_footprint: Concise regional service area description (MUST be under 200 characters)
- company_news: Recent news or developments as bullet points (e.g., "• Achievement in 2024\n• Award received in 2023")

Use empty string "" for any field where reliable information cannot be found."""
            
            resp = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,  # gpt-4o-mini-search-preview
                web_search_options={},
                messages=[
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=1000
            )
            
            text = resp.choices[0].message.content.strip()
            
            # Extract citations from annotations (for logging but not including in results)
            citations = []
            if hasattr(resp.choices[0].message, 'annotations'):
                for annotation in resp.choices[0].message.annotations:
                    if annotation.type == 'url_citation':
                        citations.append({
                            'url': annotation.url_citation.url,
                            'title': annotation.url_citation.title,
                            'start': annotation.url_citation.start_index,
                            'end': annotation.url_citation.end_index
                        })
            
            logger.info(f"   ✅ Found {len(citations)} sources for company information")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.S)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    result = {}
                    
                    # Extract each field safely
                    for field_key in ['company_description', 'hq_location', 'employee_count', 'geographic_footprint', 'company_news']:
                        value = data.get(field_key, '')
                        
                        # Special handling for company_news to format as human-readable text
                        if field_key == 'company_news':
                            if isinstance(value, list):
                                # Convert list of news items to human-readable format
                                news_items = []
                                for item in value:
                                    if isinstance(item, dict):
                                        date = item.get('date', '')
                                        headline = item.get('headline', '')
                                        description = item.get('description', '')
                                        if headline:
                                            if date:
                                                news_items.append(f"• {headline} ({date})")
                                            else:
                                                news_items.append(f"• {headline}")
                                            if description:
                                                news_items.append(f"  {description}")
                                    elif isinstance(item, str):
                                        # Check if item already starts with bullet, if not add one
                                        if item.strip().startswith('•'):
                                            news_items.append(item)
                                        else:
                                            news_items.append(f"• {item}")
                                result[field_key] = '\n'.join(news_items)
                            elif isinstance(value, str):
                                # Remove source citations and format as bullets if needed
                                value = re.sub(r'\(Source:.*?\)', '', value).strip()
                                value = re.sub(r'\([^)]*\.com[^)]*\)', '', value).strip()
                                # Clean up any existing bullet formatting issues
                                if value:
                                    # Remove any "• •" double bullets at the start of lines
                                    value = re.sub(r'(^|\n)•\s*•\s*', r'\1• ', value)
                                    # If it doesn't start with a bullet, add one
                                    if not value.startswith('•'):
                                        value = f"• {value}"
                                result[field_key] = value
                            else:
                                result[field_key] = str(value).strip() if value else ''
                        else:
                            # Standard handling for other fields
                            if isinstance(value, str):
                                # Remove source citations in parentheses
                                value = re.sub(r'\(Source:.*?\)', '', value).strip()
                                # Remove inline citations
                                value = re.sub(r'\([^)]*\.com[^)]*\)', '', value).strip()
                                result[field_key] = value
                            else:
                                result[field_key] = str(value).strip() if value else ''
                    
                    found_fields = [k for k, v in result.items() if v]
                    logger.info(f"   ✅ Found company data for {len(found_fields)} fields: {found_fields}")
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"   ⚠️ Invalid JSON in company response")
                    return None
            else:
                logger.warning(f"   ⚠️ No JSON found in company response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in web search for company info: {str(e)}")
            return None
    
    def web_search_capital_projects(self, hospital_name: str, location: str, website: str = None) -> Optional[Dict[str, str]]:
        """Search for capital projects and infrastructure information using web search."""
        
        try:
            logger.info(f"🌐 Web searching for capital outlays: {hospital_name}")
            
            # Expert-crafted prompt for reasoning through capital outlays research
            search_prompt = f"""Research capital outlays for {hospital_name} in {location}. Think systematically:

1. Consider typical hospital capital outlays:
   - Facility expansions and new construction
   - Major equipment purchases
   - Infrastructure upgrades (HVAC, energy, IT)
   - Energy efficiency and sustainability projects

2. Look for concrete details with dollar amounts and timelines.

Note: Focus on projects funded by the hospital itself, not city-wide infrastructure or utility projects.

Return a JSON object with these exact keys:
- capital_history: Recent capital outlays in last 5 years (bullet points with sources)
- future_capital: Past and future capital outlays (bullet points with sources)
- infrastructure_upgrades: Building/infrastructure improvements (bullet points with sources)
- energy_projects: Energy and emissions reduction commitments (bullet points with sources)

Format each field as bullet points:
"• Description with $ amount if available (Source: full-url)"

If no good information found for that category, format as EMPTY STRING "" in the JSON object.

"""
            
            # Use gpt-4o-mini-search-preview with web search capabilities
            resp = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,  # gpt-4o-mini-search-preview
                web_search_options={},
                messages=[
                    {"role": "user", "content": search_prompt}
                ],
                max_tokens=1500
            )
            
            # Get the response content
            text = resp.choices[0].message.content.strip()
            
            # Extract citations from annotations if available
            citations = []
            if hasattr(resp.choices[0].message, 'annotations'):
                for annotation in resp.choices[0].message.annotations:
                    if annotation.type == 'url_citation':
                        citations.append({
                            'url': annotation.url_citation.url,
                            'title': annotation.url_citation.title,
                            'start': annotation.url_citation.start_index,
                            'end': annotation.url_citation.end_index
                        })
            
            logger.info(f"   ✅ Found {len(citations)} sources for capital outlays research")
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.S)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    result = {}
                    
                    # Safely extract each field and handle different data types
                    for field_key in ['capital_history', 'future_capital', 'infrastructure_upgrades', 'energy_projects']:
                        value = data.get(field_key, '')
                        
                        # Handle different data types that might be returned
                        if isinstance(value, list):
                            # If it's a list, join the items
                            result[field_key] = '\n'.join(str(item) for item in value if item)
                        elif isinstance(value, str):
                            # If it's a string, use it directly
                            result[field_key] = value.strip()
                        else:
                            # If it's something else, convert to string
                            result[field_key] = str(value).strip() if value else ''
                    
                    # Enhance results with citations from annotations
                    result = self._enhance_with_citations(result, citations)
                    
                    found_fields = [k for k, v in result.items() if v]
                    logger.info(f"   ✅ Found capital/infrastructure data for {len(found_fields)} fields: {found_fields}")
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"   ⚠️ Invalid JSON in response")
                    return None
            else:
                logger.warning(f"   ⚠️ No JSON found in response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in web search for capital outlays: {str(e)}")
            return None
    
    def _enhance_with_citations(self, result: Dict[str, str], citations: List[Dict]) -> Dict[str, str]:
        """Enhance field results with URL citations from OpenAI annotations."""
        if not citations:
            return result
        
        enhanced_result = {}
        
        for field_key, content in result.items():
            if content and content.strip():
                # Check if content already has source citations
                has_source = '(Source:' in content
                
                if not has_source and citations:
                    # Add the most relevant citation for this field
                    # For now, use the first citation, but could be enhanced to match content
                    primary_citation = citations[0]
                    
                    # If content has multiple bullet points, add citation to the last one
                    if '•' in content:
                        lines = content.split('\n')
                        if lines:
                            # Add citation to the last bullet point
                            last_line = lines[-1].strip()
                            if last_line and not last_line.endswith(')'):
                                lines[-1] = last_line + f" (Source: {primary_citation['url']})"
                            content = '\n'.join(lines)
                    else:
                        # Single content, add citation at the end
                        if not content.endswith(')'):
                            content += f" (Source: {primary_citation['url']})"
                
                enhanced_result[field_key] = content
            else:
                enhanced_result[field_key] = content
        
        return enhanced_result

    def _truncate_field_value(self, value: str, max_length: int = 32000) -> str:
        """Truncate field values to fit Salesforce field limits."""
        if not value:
            return value

        # Special handling for specific field types
        if max_length <= 255:  # Short text fields
            if len(value) > max_length:
                # For geographic footprint, try to extract just the essential region info
                if 'county' in value.lower() or 'counties' in value.lower():
                    # Extract state and simplify to regional description
                    # Try to find a state abbreviation
                    state_match = re.search(r'\b([A-Z]{2})\b', value)
                    if state_match:
                        state = state_match.group(1)
                        # Return simplified version
                        return f"Regional service area in {state} and surrounding areas"
                    
                # Default truncation
                return value[:max_length-3] + "..."
        elif len(value) > max_length:  # Long text fields
            return value[:max_length-10] + "...[truncated]"

        return value

    def _extract_json_result(self, response_text: str, key: str) -> Optional[str]:
        """Extract JSON result from the end of a response."""
        import json
        import re

        try:
            # Look for JSON at the end of the response
            json_pattern = r'\{[^{}]*"' + key + r'"[^{}]*\}'
            json_matches = re.findall(json_pattern, response_text, re.DOTALL)

            if json_matches:
                # Try to parse the last JSON match
                json_str = json_matches[-1]
                data = json.loads(json_str)
                return data.get(key, "")

            return None
        except (json.JSONDecodeError, KeyError, AttributeError):
            return None

    def run_credit_enricher(self, account_id: str, hospital_name: str, website: str = None) -> bool:
        """
        Run credit enricher to populate credit quality fields before financial enricher.

        Args:
            account_id: Salesforce Account ID
            hospital_name: Hospital/company name
            website: Optional website URL

        Returns:
            True if credit enrichment succeeded or fields already populated, False otherwise
        """
        try:
            logger.info(f"💳 Running credit enricher for: {hospital_name}")

            # Get the account details to check if credit fields are empty
            account = self.sf.Account.get(account_id)

            credit_fields_to_check = [
                'Company_Credit_Quality__c',
                'Company_Credit_Quality_Detailed__c'
            ]

            # Check if credit fields are already populated
            has_credit_data = False
            for field in credit_fields_to_check:
                if field in account and account[field]:
                    has_credit_data = True
                    logger.info(f"✅ Credit field already populated: {field}")
                    break

            if has_credit_data:
                logger.info("✅ Credit quality data already exists - skipping credit enricher")
                return True

            # Credit fields are empty, so run the enricher
            logger.info("🔍 Credit fields empty - calling EDF-X via credit enricher...")

            # Call EDF-X enrichment service
            credit_data = self.credit_enricher.enrich_with_edfx(hospital_name, website)
            if not credit_data:
                logger.warning("⚠️ No credit data returned from EDF-X")
                return False

            # Update Salesforce with credit data
            success = self.credit_enricher.update_account_credit_data(account_id, credit_data, account)

            if success:
                logger.info("✅ Credit enrichment completed successfully")
            else:
                logger.warning("⚠️ Credit enrichment update failed")

            return success

        except Exception as e:
            logger.error(f"❌ Error running credit enricher: {str(e)}")
            return False

    def web_search_financial_data(self, hospital_name: str, location: str, website: str = None, skip_credit_fields: bool = False) -> Optional[Dict[str, str]]:
        """
        Search for comprehensive financial data using enhanced financial enricher.

        Args:
            hospital_name: Name of the hospital/organization
            location: Location of the organization
            website: Optional website URL
            skip_credit_fields: If True, skip credit quality fields (already populated by credit enricher)

        Returns:
            Dict of financial data fields
        """
        try:
            logger.info(f"💰 Using enhanced financial enricher for: {hospital_name}")
            if skip_credit_fields:
                logger.info("⚠️ Skipping credit quality fields in financial enricher (already populated)")
            return self.financial_enricher.search_all_financial_data(hospital_name, location, website, skip_credit_fields)
        except Exception as e:
            logger.error(f"❌ Error in enhanced financial data search: {str(e)}")
            return None







    async def update_account_fields(self, account_id: str, field_data: Dict[str, str], updatable_fields: List[str] = None, queue_mode: bool = False) -> bool:
        """
        Update account fields in Salesforce with field validation.

        Args:
            account_id: Salesforce Account ID
            field_data: Dictionary of field keys to values
            updatable_fields: Optional list of field keys that can be updated
            queue_mode: If True, queue update for approval instead of direct update

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"💾 Updating account {account_id} with web search data...")
            if queue_mode:
                logger.info("📋 Queue mode: Updates will require approval before applying to Salesforce")

            # First, clean the field data using our validator
            logger.info(f"🧹 Validating {len(field_data)} fields before Salesforce update...")
            cleaned_field_data = FieldValidator.clean_field_data(field_data, self.FIELD_MAPPING)

            if len(cleaned_field_data) < len(field_data):
                removed_count = len(field_data) - len(cleaned_field_data)
                logger.warning(f"🛑 Filtered out {removed_count} invalid fields before update")

            update_data = {}

            for field_key, value in cleaned_field_data.items():
                # Only update if field has data AND is in the updatable_fields list (or no restriction if updatable_fields is None)
                if value and value.strip() and field_key in self.FIELD_MAPPING:
                    if updatable_fields is None or field_key in updatable_fields:
                        # Final validation before adding to update_data
                        if FieldValidator.is_valid_field_value(value, field_key):
                            salesforce_field = self.FIELD_MAPPING[field_key]

                            # Apply field-specific length limits
                            if field_key in ['wacc', 'credit_quality', 'revenue', 'hq_location', 'geographic_footprint']:
                                truncated_value = self._truncate_field_value(value, 255)  # Short text fields
                            else:
                                truncated_value = self._truncate_field_value(value, 32000)  # Default long text limit

                            update_data[salesforce_field] = truncated_value
                            logger.info(f"   ✅ Will update {field_key} -> {salesforce_field}")
                        else:
                            logger.warning(f"   🛑 BLOCKED {field_key}: Failed final validation")
                    else:
                        logger.info(f"   🔴 Skipping {field_key} (not in updatable fields list)")

            if not update_data:
                logger.warning("⚠️ No valid fields to update after validation")
                return True  # Not an error, just no valid data found

            # Final safety check on the Salesforce update data
            validated_update_data = FieldValidator.validate_salesforce_update_data(update_data)

            if len(validated_update_data) < len(update_data):
                blocked_count = len(update_data) - len(validated_update_data)
                logger.warning(f"🛑 Final safety check blocked {blocked_count} additional fields")

            if not validated_update_data:
                logger.warning("⚠️ No fields passed final validation - skipping Salesforce update")
                return True

            # Queue or directly update based on mode
            if queue_mode and self.pending_updates_service:
                # Get account name for display
                try:
                    account = self.sf.Account.get(account_id)
                    account_name = account.get('Name', account_id)
                except:
                    account_name = account_id

                # Queue the update for approval
                from app.models import RecordType
                await self.pending_updates_service.queue_update(
                    record_type=RecordType.ACCOUNT,
                    record_id=account_id,
                    field_updates=validated_update_data,
                    record_name=account_name,
                    enrichment_type="web_search_account"
                )
                logger.info(f"✅ Queued {len(validated_update_data)} fields for approval (Account: {account_name})")
                return True
            else:
                # Direct update to Salesforce
                self.sf.Account.update(account_id, validated_update_data)
                logger.info(f"✅ Successfully updated {len(validated_update_data)} validated fields")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to update account: {str(e)}")
            return False
    
    async def process_web_search_enrichment(self, record_id: str, overwrite: bool = False, include_financial: bool = False, credit_only: bool = False) -> bool:
        """Main method to perform web search enrichment."""
        try:
            logger.info(f"🚀 Starting web search enrichment for record ID: {record_id}")
            logger.info(f"🔧 Overwrite mode: {'ON' if overwrite else 'OFF (empty fields only)'}")
            
            # Handle credit-only mode (EDFx only, no AI)
            if credit_only:
                logger.info("💳 CREDIT-ONLY MODE: Running EDFx enrichment only (skipping AI)")
                
                # 1. Get account details
                account = self.get_account_details(record_id)
                if not account:
                    logger.error(f"❌ Cannot proceed: Account not found for {record_id}")
                    return False
                
                hospital_name = account.get('Name', '')
                website = account.get('Website', '')
                
                logger.info(f"📋 Account: {hospital_name}")
                logger.info(f"📋 Website: {website}")
                
                # Run ONLY the credit enricher (EDFx)
                credit_enriched = self.run_credit_enricher(account['Id'], hospital_name, website)
                
                if credit_enriched:
                    logger.info("✅ Credit-only enrichment completed successfully")
                    return True
                else:
                    logger.warning("⚠️ Credit enrichment did not succeed")
                    return False
            
            # Normal mode: Continue with full enrichment
            # 1. Get account details
            account = self.get_account_details(record_id)
            if not account:
                logger.error(f"❌ Cannot proceed: Account not found for {record_id}")
                return False
            
            hospital_name = account.get('Name', '')
            website = account.get('Website', '')
            city = account.get('ShippingCity', '') or account.get('BillingCity', '')
            state = account.get('ShippingState', '') or account.get('BillingState', '')
            zip_code = account.get('ShippingPostalCode', '') or account.get('BillingPostalCode', '')
            
            location = f"{city}, {state} {zip_code}"
            
            logger.info(f"📋 Account details:")
            logger.info(f"   Name: {hospital_name}")
            logger.info(f"   Location: {location}")
            logger.info(f"   Website: {website}")
            
            # 2. Check which fields can be updated
            updatable_fields = self.check_updatable_fields(account, overwrite)
            
            if not updatable_fields:
                logger.info("✅ All fields already have data. Use --overwrite to update anyway.")
                return True
            
            # 3. Perform targeted web searches
            all_field_data = {}
            
            # Search for company information if needed
            company_fields = [f for f in updatable_fields if f in ['company_description', 'hq_location', 'employee_count', 'geographic_footprint', 'company_news']]
            if company_fields:
                company_data = self.web_search_company_info(hospital_name, location, website)
                if company_data:
                    all_field_data.update(company_data)
                time.sleep(1)  # Rate limiting
            
            # Search for capital/infrastructure information if needed
            capital_fields = [f for f in updatable_fields if f in ['capital_history', 'future_capital', 'infrastructure_upgrades', 'energy_projects']]
            if capital_fields:
                capital_data = self.web_search_capital_projects(hospital_name, location, website)
                if capital_data:
                    all_field_data.update(capital_data)
                time.sleep(1)  # Rate limiting

            # Search for financial information if requested
            if include_financial:
                # Step 1: Run credit enricher FIRST to populate credit quality fields with EDFx data
                logger.info("\n📊 Step 1: Running credit enricher (EDFx) before financial enricher...")
                credit_enriched = self.run_credit_enricher(account['Id'], hospital_name, website)

                if credit_enriched:
                    logger.info("✅ Credit enrichment completed - credit fields populated with EDFx data")
                    # Refresh account details to get the updated credit fields
                    account = self.get_account_details(record_id)
                    
                    # CRITICAL: Remove credit fields from updatable_fields to prevent AI from overwriting EDFx data
                    logger.info("🔒 Locking credit quality fields to preserve EDFx data (AI will not overwrite)")
                    updatable_fields = [f for f in updatable_fields if f not in ['credit_quality', 'credit_quality_detailed']]
                else:
                    logger.warning("⚠️ Credit enrichment did not succeed - financial enricher will use AI for credit quality")

                time.sleep(1)  # Rate limiting between enrichers

                # Step 2: Run financial enricher, skipping credit fields if they were already populated by EDFx
                logger.info("\n💰 Step 2: Running financial enricher...")
                financial_fields = [f for f in updatable_fields if f in ['recent_disclosures', 'wacc', 'debt_appetite', 'other_debt', 'financial_outlook', 'off_balance_appetite', 'off_balance_appetite_summary', 'revenue', 'credit_quality', 'credit_quality_detailed']]
                if financial_fields:
                    # Pass skip_credit_fields=True if credit enricher succeeded
                    skip_credit = credit_enriched
                    financial_data = self.web_search_financial_data(hospital_name, location, website, skip_credit_fields=skip_credit)
                    if financial_data:
                        all_field_data.update(financial_data)
                    time.sleep(1)  # Rate limiting
            
            if not all_field_data:
                logger.warning("⚠️ No data found from web searches")
                return True  # Not an error, just no data available
            
            # 4. Synthesize off-balance appetite summary AFTER all data is collected
            if include_financial and 'off_balance_appetite_summary' in updatable_fields:
                # Remove the raw off_balance_appetite if it exists to avoid duplication
                if 'off_balance_appetite' in all_field_data:
                    del all_field_data['off_balance_appetite']
                
                synthesis_result = self.synthesize_off_balance_appetite_summary(hospital_name, location, all_field_data)
                if synthesis_result:
                    all_field_data['off_balance_appetite_summary'] = synthesis_result
                    logger.info("   ✅ Added synthesized off-balance appetite summary")
                else:
                    logger.info("   ⚠️ Off-balance appetite synthesis skipped (low confidence or error)")
            
            # 5. Validate and clean all field data before preview
            logger.info(f"🧹 Validating {len(all_field_data)} enriched fields...")
            validated_field_data = FieldValidator.clean_field_data(all_field_data, self.FIELD_MAPPING)
            
            if len(validated_field_data) < len(all_field_data):
                removed_count = len(all_field_data) - len(validated_field_data)
                logger.warning(f"🛑 Validation removed {removed_count} fields with invalid data")
            
            if not validated_field_data:
                logger.warning("⚠️ No valid data found from web searches after validation")
                return True  # Not an error, just no valid data available
            
            # 5. Show preview and confirm
            logger.info("📝 Validated web search results:")
            logger.info("-" * 60)
            for field_key, value in validated_field_data.items():
                if value:
                    preview = value[:100] + "..." if len(value) > 100 else value
                    logger.info(f"{field_key}: {preview}")
            logger.info("-" * 60)
            
            # Confirm before updating
            try:
                user_input = input(f"Update {len([v for v in validated_field_data.values() if v])} validated fields in Salesforce? (Y/n): ")
                if user_input.lower() in ['n', 'no']:
                    logger.info("✅ Enrichment cancelled per user request")
                    return True
            except EOFError:
                logger.info("🤖 Automated mode: Proceeding with update")
            
            # 6. Update the account with validated data (queue if service available, otherwise direct update)
            queue_mode = self.pending_updates_service is not None
            success = await self.update_account_fields(
                account['Id'],
                validated_field_data,
                updatable_fields,
                queue_mode=queue_mode
            )
            
            if success:
                logger.info("✅ Web search account enrichment completed successfully")
            else:
                logger.error("❌ Failed to update account fields")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error processing web search enrichment: {str(e)}")
            return False

    def synthesize_off_balance_appetite_summary(self, hospital_name: str, location: str, all_field_data: Dict[str, str]) -> Optional[str]:
        """
        Synthesize off-balance sheet appetite summary based on all collected financial data.
        
        This is a subjective analysis that considers multiple inputs:
        - Credit quality and rating
        - WACC and debt appetite/constraints  
        - Capital project history and future plans
        - Energy/infrastructure project history
        - Revenue and financial outlook
        
        Returns a sales-oriented summary with confidence indicator.
        """
        try:
            logger.info(f"🔬 Synthesizing off-balance appetite summary for: {hospital_name}")
            
            # Extract relevant data for synthesis
            credit_quality = all_field_data.get('credit_quality', '')
            credit_detailed = all_field_data.get('credit_quality_detailed', '')
            wacc = all_field_data.get('wacc', '')
            debt_appetite = all_field_data.get('debt_appetite', '')
            other_debt = all_field_data.get('other_debt', '')
            financial_outlook = all_field_data.get('financial_outlook', '')
            capital_history = all_field_data.get('capital_history', '')
            future_capital = all_field_data.get('future_capital', '')
            infrastructure_upgrades = all_field_data.get('infrastructure_upgrades', '')
            energy_projects = all_field_data.get('energy_projects', '')
            revenue = all_field_data.get('revenue', '')
            recent_disclosures = all_field_data.get('recent_disclosures', '')
            
            # Create comprehensive synthesis prompt
            synthesis_prompt = f"""You are a senior healthcare finance analyst synthesizing off-balance sheet appetite for {hospital_name} in {location}.

SYNTHESIS TASK: Based on all the financial data collected, provide a sales-oriented assessment of whether this organization would likely benefit from Energy-as-a-Service (EaaS) off-balance sheet financing and why.

AVAILABLE DATA FOR ANALYSIS:
1. Credit Quality: {credit_quality or 'Not available'}
2. Credit Details: {credit_detailed or 'Not available'}
3. Revenue: {revenue or 'Not available'}
4. WACC: {wacc or 'Not available'}
5. Debt Appetite/Constraints: {debt_appetite or 'Not available'}
6. Other Debt: {other_debt or 'Not available'}
7. Financial Outlook: {financial_outlook or 'Not available'}
8. Capital History: {capital_history or 'Not available'}
9. Future Capital Plans: {future_capital or 'Not available'}
10. Infrastructure Upgrades: {infrastructure_upgrades or 'Not available'}
11. Energy Projects: {energy_projects or 'Not available'}
12. Recent Disclosures: {recent_disclosures or 'Not available'}

ANALYSIS FRAMEWORK:
1. Credit Context Assessment:
   - Strong credit (AA/A ratings): May still have appetite if capex constrained or strategic preference
   - Moderate credit (BBB/Ba): Likely benefits from preserving debt capacity
   - Weak credit (B or below): May have limited financing options, EaaS could be attractive

2. Debt Sensitivity Indicators:
   - Evidence of debt capacity constraints or covenant concerns
   - Recent debt issuance patterns and timing
   - Management commentary on capital allocation preferences

3. Capital Investment Patterns:
   - Size and timing of recent infrastructure projects
   - Evidence of deferred maintenance or large replacement cycles
   - Energy/HVAC/boiler/chiller upgrade history and needs

4. Energy/Sustainability Context:
   - Explicit energy or emissions reduction goals
   - History of energy efficiency investments
   - Infrastructure age and replacement needs

5. Strategic Considerations:
   - Preference for operational vs capital risk
   - Balance sheet optimization priorities
   - Multi-year capital planning constraints

CONFIDENCE SCORING (0-100):
- 90-100: Multiple recent sources, consistent signals, clear credit/debt context
- 70-89: Good data quality, some recent sources, reasonable confidence in assessment
- 50-69: Mixed data quality, some uncertainty, moderate confidence
- Below 50: Limited or outdated data, low confidence

OUTPUT REQUIREMENTS:
- If confidence ≥70: Provide synthesis summary
- If confidence <70: Return "Low confidence - insufficient recent data for reliable assessment"

Provide your analysis then end with this exact JSON format:

{{"off_balance_summary": "Off-balance appetite: [High/Moderate/Low] - [2-3 sentence rationale based on credit context, debt sensitivity, and capital needs]. Confidence: [XX]% based on [key data sources/limitations]." or "Low confidence - insufficient recent data for reliable assessment", "confidence_score": XX}}"""

            # Use the same model as financial searches for consistency
            if "search" in DEFAULT_MODEL:
                # For search models, don't use temperature parameter
                resp = self.openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    web_search_options={},
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    max_tokens=800
                )
            else:
                # For regular models, use temperature
                resp = self.openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    max_tokens=800,
                    temperature=0.1
                )
            
            text = resp.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.S)
            if json_match:
                try:
                    import json
                    data = json.loads(json_match.group(0))
                    summary = data.get('off_balance_summary', '')
                    confidence = data.get('confidence_score', 0)
                    
                    logger.info(f"   📊 Synthesis confidence score: {confidence}%")
                    
                    # Only return summary if confidence is adequate
                    if confidence >= 70 and summary and FieldValidator.is_valid_field_value(summary, 'off_balance_appetite_summary'):
                        logger.info(f"   ✅ High confidence synthesis: {summary[:100]}...")
                        return summary
                    elif confidence < 70:
                        logger.info(f"   ⚠️ Low confidence ({confidence}%) - marking as attempted but not filling field")
                        # Could optionally return a marker like "Attempted - low confidence" to prevent re-searching
                        return None
                    else:
                        logger.info(f"   🛑 Synthesis failed validation: {summary[:50]}...")
                        return None
                        
                except json.JSONDecodeError:
                    logger.warning("   🛑 Failed to parse synthesis JSON response")
                    return None
            else:
                logger.warning("   🛑 No JSON found in synthesis response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error synthesizing off-balance appetite summary: {str(e)}")
            return None


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Web Search Salesforce Account Enricher')
    parser.add_argument('record_id', help='Salesforce Account Record ID')
    parser.add_argument('--overwrite', action='store_true',
                       help='Update all fields including those with existing data')
    parser.add_argument('--include-financial', action='store_true',
                       help='Include financial data analysis (WACC, debt, disclosures, etc.)')
    
    args = parser.parse_args()
    
    try:
        enricher = WebSearchAccountEnricher()
        success = enricher.process_web_search_enrichment(args.record_id, args.overwrite, args.include_financial)
        
        if success:
            print(f"\n✅ Successfully processed account: {args.record_id}")
            if args.overwrite:
                print("🔧 Used overwrite mode - updated all fields")
            else:
                print("🛡️ Safe mode - only updated empty fields")
            if args.include_financial:
                print("💰 Included financial data analysis")
        else:
            print(f"\n❌ Failed to process account: {args.record_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
