#!/usr/bin/env python3
"""
Simple Salesforce Account Credit Enrichment Script

This script searches for a Salesforce account by company name, checks if it has
credit quality information, and if missing, uses the Fast Leads API to enrich it.

Requirements:
- .env file with Salesforce credentials (see .env.example)
- Or environment variables: SALESFORCE_USERNAME, SALESFORCE_PASSWORD, etc.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
import requests
from simple_salesforce import Salesforce
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SalesforceAccountEnricher:
    """Simple class to enrich Salesforce accounts with credit data."""
    
    def __init__(self):
        """Initialize the enricher with Salesforce connection."""
        self.sf = None
        self.fast_leads_api_url = "https://fast-leads-api.up.railway.app"
        
        # Load environment variables from .env file
        load_dotenv()
        
        self._connect_to_salesforce()
    
    def _connect_to_salesforce(self) -> None:
        """Connect to Salesforce using environment variables."""
        try:
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'login')
            
            if not username or not password:
                raise ValueError("Missing required Salesforce credentials in environment variables")
            
            logger.info("Connecting to Salesforce...")
            
            # Connect to Salesforce
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
            
            # Test the connection
            test_result = self.sf.query("SELECT Id FROM User LIMIT 1")
            if test_result and test_result.get('totalSize', 0) > 0:
                logger.info("✅ Successfully connected to Salesforce")
            else:
                raise Exception("Connected but test query failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Salesforce: {str(e)}")
            raise
    
    def find_account_by_name(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Find Salesforce account by company name.
        
        Args:
            company_name: The company name to search for
            
        Returns:
            Account record dict or None if not found
        """
        try:
            logger.info(f"🔍 Searching for account: {company_name}")
            
            # Search standard Account object 
            query = f"SELECT Id, Name, Website, Industry FROM Account WHERE Name LIKE '%{company_name}%' LIMIT 5"
            
            try:
                result = self.sf.query(query)
                if result.get('totalSize', 0) > 0:
                    accounts = result['records']
                    logger.info(f"Found {len(accounts)} account(s)")
                    
                    # Show options to user
                    for i, account in enumerate(accounts):
                        logger.info(f"  {i+1}. {account.get('Name', 'Unknown')} (ID: {account['Id']})")
                    
                    return accounts[0]  # Return first match for now
                    
            except Exception as e:
                logger.error(f"Query failed: {query} - {str(e)}")
            
            logger.warning(f"❌ No account found for: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for account: {str(e)}")
            return None
    
    def check_credit_quality_missing(self, account: Dict[str, Any]) -> bool:
        """
        Check if the account is missing credit quality information.
        
        Note: You'll need to specify the exact field name for "Company Credit Quality"
        Common possibilities: Credit_Quality__c, Company_Credit_Quality__c, etc.
        
        Args:
            account: Salesforce account record
            
        Returns:
            True if credit quality data is missing, False otherwise
        """
        try:
            account_id = account['Id']
            
            # Check for the Company Credit Quality fields and Industry
            credit_fields_to_check = [
                'Company_Credit_Quality__c',          # Simple format field
                'Company_Credit_Quality_Detailed__c'  # Full JSON field
            ]
            
            industry_field = 'Industry'  # Standard Salesforce field
            
            # Get full account record from standard Account object
            try:
                account_detail = self.sf.Account.get(account_id)
                object_type = "Account"
            except Exception as e:
                logger.error(f"❌ Could not retrieve account details for {account_id}: {str(e)}")
                return True  # Assume missing if we can't check
            
            logger.info(f"📋 Checking credit fields in {object_type} object...")
            
            # Check if credit quality data is missing
            has_credit_data = False
            for field in credit_fields_to_check:
                if field in account_detail and account_detail[field]:
                    logger.info(f"✅ Found credit data in field: {field} = {account_detail[field]}")
                    has_credit_data = True
                    break
            
            # Check if industry data is missing
            has_industry_data = False
            if industry_field in account_detail and account_detail[industry_field]:
                logger.info(f"✅ Found industry data: {account_detail[industry_field]}")
                has_industry_data = True
            else:
                logger.info("❌ No industry data found")
            
            # Return True if either credit OR industry data is missing
            if not has_credit_data:
                logger.info("❌ No credit quality data found")
                return True
            elif not has_industry_data:
                logger.info("❌ No industry data found - will enrich")
                return True
            else:
                logger.info("✅ Both credit quality and industry data already exist")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking credit quality: {str(e)}")
            return True  # Assume missing if error
    
    def enrich_with_fast_leads_api(self, company_name: str, website: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Call the Fast Leads API to get credit enrichment data.
        
        Args:
            company_name: Company name to enrich
            website: Optional website URL
            
        Returns:
            Credit data dict or None if failed
        """
        try:
            logger.info(f"🌐 Calling Fast Leads API for: {company_name}")
            
            payload = {
                "company_name": company_name
            }
            if website:
                payload["website"] = website
                logger.info(f"   Including website: {website}")
            
            url = f"{self.fast_leads_api_url}/credit/enrich-company"
            logger.info(f"   API URL: {url}")
            logger.info(f"   Payload: {payload}")
            
            logger.info("   Making API request...")
            response = requests.post(url, json=payload, timeout=30)
            
            logger.info(f"   Response status: {response.status_code}")
            logger.info(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                api_response = response.json()
                logger.info(f"   Full API response: {api_response}")
                
                # Extract credit data from nested structure
                if api_response.get('status') in ['success', 'partial'] and 'data' in api_response:
                    credit_data = api_response['data']
                    search_success = credit_data.get('search_success', False)
                    logger.info(f"   Search success: {search_success}")
                    
                    if search_success:
                        logger.info(f"✅ Successfully enriched: {company_name}")
                        logger.info(f"   Rating: {credit_data.get('implied_rating', 'N/A')}")
                        logger.info(f"   PD Value: {credit_data.get('pd_value', 'N/A')}")
                        logger.info(f"   Confidence: {credit_data.get('confidence_translated', 'N/A')}")
                        logger.info(f"   Entity ID: {credit_data.get('entity_id', 'N/A')}")
                        logger.info(f"   Search results count: {credit_data.get('search_results_count', 0)}")
                    else:
                        logger.warning(f"⚠️ No credit data found for: {company_name}")
                        logger.warning(f"   Error message: {credit_data.get('error_message', 'No error message')}")
                        logger.warning(f"   Matching logic: {credit_data.get('matching_logic', 'No matching info')}")
                    
                    return credit_data
                else:
                    logger.error(f"❌ Unexpected API response structure: {api_response}")
                    return None
            else:
                logger.error(f"❌ API call failed: {response.status_code}")
                logger.error(f"   Response text: {response.text}")
                try:
                    error_json = response.json()
                    logger.error(f"   Error details: {error_json}")
                except:
                    logger.error("   Could not parse error response as JSON")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ API call timed out after 30 seconds")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error calling Fast Leads API: {str(e)}")
            logger.error(f"   Exception type: {type(e).__name__}")
            return None
    
    def update_account_credit_data(self, account_id: str, credit_data: Dict[str, Any], current_account: Dict[str, Any]) -> bool:
        """
        Update the Salesforce account with credit data.
        
        Args:
            account_id: Salesforce account ID
            credit_data: Credit data from Fast Leads API
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"💾 Updating account {account_id} with credit data...")
            
            # Map API response to Salesforce fields
            update_data = {}
            
            # Only proceed if we have successful search results
            if credit_data.get('search_success'):
                # 1. Company_Credit_Quality__c - Simple format: "Rating / PD_Value"
                rating = credit_data.get('implied_rating')
                pd_value = credit_data.get('pd_value')
                
                if rating and pd_value is not None:  # pd_value could be 0, so check for None specifically
                    simple_format = f"{rating} / {pd_value}"
                    update_data['Company_Credit_Quality__c'] = simple_format
                    logger.info(f"   Will update Company_Credit_Quality__c: {simple_format}")
                
                # 2. Company_Credit_Quality_Detailed__c - Readable format
                try:
                    # Create a readable, structured format
                    detailed_parts = []
                    
                    if credit_data.get('company_name'):
                        detailed_parts.append(f"company_name: {credit_data['company_name']}")
                    
                    if credit_data.get('entity_id'):
                        detailed_parts.append(f"entity_id: {credit_data['entity_id']}")
                    
                    if credit_data.get('pd_value') is not None:
                        detailed_parts.append(f"pd_value: {credit_data['pd_value']}")
                    
                    if credit_data.get('implied_rating'):
                        detailed_parts.append(f"implied_rating: {credit_data['implied_rating']}")
                    
                    if credit_data.get('confidence'):
                        detailed_parts.append(f"confidence: {credit_data['confidence']}")
                    
                    if credit_data.get('confidence_translated'):
                        detailed_parts.append(f"confidence_translated: {credit_data['confidence_translated']}")
                    
                    if credit_data.get('as_of_date'):
                        detailed_parts.append(f"as_of_date: {credit_data['as_of_date']}")
                    
                    if credit_data.get('matching_logic'):
                        detailed_parts.append(f"matching_logic: {credit_data['matching_logic']}")
                    
                    if detailed_parts:
                        detailed_text = "\n".join(detailed_parts)
                        update_data['Company_Credit_Quality_Detailed__c'] = detailed_text
                        logger.info(f"   Will update Company_Credit_Quality_Detailed__c: Readable format ({len(detailed_text)} characters)")
                        
                except Exception as e:
                    logger.warning(f"   Could not format detailed field: {str(e)}")
                
                # 3. Industry if available from API AND current Industry field is blank
                selected_entity = credit_data.get('selected_entity', {})
                api_industry = selected_entity.get('industry')
                current_industry = current_account.get('Industry')
                
                if api_industry and not current_industry:
                    # Map API industry to Salesforce picklist values
                    industry_mapping = {
                        'TRANSPORTATION': 'Transportation',
                        'TECHNOLOGY': 'Technology',
                        'HEALTHCARE': 'Healthcare',
                        'MANUFACTURING': 'Manufacturing',
                        'ENERGY': 'Energy',
                        'CONSTRUCTION': 'Construction',
                        'FINANCE': 'Banking',
                        'RETAIL': 'Retail',
                        'EDUCATION': 'Education',
                        'REAL ESTATE': 'Real Estate'
                    }
                    
                    # Use mapping or fall back to cleaned version of API value
                    salesforce_industry = industry_mapping.get(api_industry, api_industry.title())
                    update_data['Industry'] = salesforce_industry
                    logger.info(f"   Will update Industry: {api_industry} → {salesforce_industry}")
                elif api_industry and current_industry:
                    logger.info(f"   Industry already exists ({current_industry}), skipping update")
                elif not api_industry:
                    logger.info(f"   No industry data from API, skipping update")
            else:
                logger.info("   No successful API results - leaving all fields blank")
            
            if not update_data:
                logger.warning("⚠️ No credit data to update")
                return False
            
            # Update the standard Account object
            try:
                self.sf.Account.update(account_id, update_data)
                logger.info("✅ Successfully updated Account")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to update account: {str(e)}")
                logger.info("💡 This might be due to field permissions or API limits.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating account: {str(e)}")
            return False
    
    def process_single_account(self, company_name: str) -> bool:
        """
        Main method to process a single account safely.
        
        Args:
            company_name: Company name to search and enrich
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Starting credit enrichment for: {company_name}")
            
            # 1. Find the account
            account = self.find_account_by_name(company_name)
            if not account:
                logger.error(f"❌ Cannot proceed: Account not found for {company_name}")
                return False
            
            # 2. Check if credit quality data is missing
            if not self.check_credit_quality_missing(account):
                logger.info("✅ Account already has credit quality data. Skipping enrichment.")
                return True
            
            # 3. Get website if available
            website = account.get('Website')
            if website:
                logger.info(f"🌐 Found website: {website}")
            else:
                logger.info("ℹ️ No website found for account")
            
            # 4. Call Fast Leads API
            credit_data = self.enrich_with_fast_leads_api(company_name, website)
            if not credit_data:
                logger.error("❌ Failed to get credit data from API")
                return False
            
            # 5. Update the account (in test mode, just log what would be updated)
            logger.info("🧪 TEST MODE: Would update account with the following data:")
            logger.info(f"   Account ID: {account['Id']}")
            
            if credit_data.get('search_success'):
                # Show simple format
                rating = credit_data.get('implied_rating')
                pd_value = credit_data.get('pd_value')
                if rating and pd_value is not None:
                    logger.info(f"   Company_Credit_Quality__c: {rating} / {pd_value}")
                
                # Show detailed readable format (first 200 chars)
                try:
                    # Create preview of the readable format
                    detailed_parts = []
                    
                    if credit_data.get('company_name'):
                        detailed_parts.append(f"company_name: {credit_data['company_name']}")
                    if credit_data.get('entity_id'):
                        detailed_parts.append(f"entity_id: {credit_data['entity_id']}")
                    if credit_data.get('pd_value') is not None:
                        detailed_parts.append(f"pd_value: {credit_data['pd_value']}")
                    if credit_data.get('implied_rating'):
                        detailed_parts.append(f"implied_rating: {credit_data['implied_rating']}")
                    
                    preview_text = "\n".join(detailed_parts[:4])  # Show first 4 fields
                    if len(detailed_parts) > 4:
                        preview_text += "\n..."
                    
                    logger.info(f"   Company_Credit_Quality_Detailed__c:\n{preview_text}")
                except:
                    logger.info(f"   Company_Credit_Quality_Detailed__c: [Readable format available]")
                
                # Show industry update if available and current industry is blank
                selected_entity = credit_data.get('selected_entity', {})
                api_industry = selected_entity.get('industry')
                current_industry = account.get('Industry')
                
                if api_industry and not current_industry:
                    logger.info(f"   Industry: {api_industry} (will update since current is blank)")
                elif api_industry and current_industry:
                    logger.info(f"   Industry: Current='{current_industry}', API='{api_industry}' (will NOT update since current exists)")
                elif not api_industry:
                    logger.info(f"   Industry: No industry data from API")
            else:
                logger.info("   All fields would be left BLANK (no successful API results)")
            
            # Actually update Salesforce:
            success = self.update_account_credit_data(account['Id'], credit_data, account)
            
            logger.info("✅ Test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing account {company_name}: {str(e)}")
            return False


def main():
    """Main function to run the script."""
    if len(sys.argv) != 2:
        print("Usage: python salesforce_credit_enricher.py \"Company Name\"")
        print("Example: python salesforce_credit_enricher.py \"Apple Inc\"")
        sys.exit(1)
    
    company_name = sys.argv[1]
    
    try:
        enricher = SalesforceAccountEnricher()
        success = enricher.process_single_account(company_name)
        
        if success:
            print(f"\n✅ Successfully processed: {company_name}")
        else:
            print(f"\n❌ Failed to process: {company_name}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
