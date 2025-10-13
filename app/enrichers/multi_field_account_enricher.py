#!/usr/bin/env python3
"""
Multi-Field Salesforce Account Enricher with OpenAI Search

This script enriches Salesforce account records with comprehensive information
across multiple fields using OpenAI's search capabilities. It safely updates
only empty fields by default, with an optional overwrite flag.

Usage:
    python multi_field_account_enricher.py "RECORD_ID" [--overwrite]
    python multi_field_account_enricher.py "001VR00000UhXucYAF" --overwrite
"""

import os
import sys
import logging
import json
import argparse
from typing import Optional, Dict, Any, List
from simple_salesforce import Salesforce
from dotenv import load_dotenv
import openai

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiFieldAccountEnricher:
    """Class to enrich Salesforce accounts with multi-field OpenAI-powered information."""
    
    # Field mapping from priority fields to Salesforce API names
    # Note: These field names need to match exactly what exists in Salesforce
    FIELD_MAPPING = {
        'company_description': 'General_Company_Description__c',
        'credit_quality': 'Company_Credit_Quality__c',
        'credit_quality_detailed': 'Company_Credit_Quality_Detailed__c',
        'wacc': 'Weighted_average_cost_of_capital__c',
        'debt_appetite': 'Debt_appetite_constraints__c',
        'financial_outlook': 'Long_term_financial_outlook__c',
        'capital_history': 'Capital_and_project_history__c',
        'future_capital': 'Past_future_capital_uses__c',
        'infrastructure_upgrades': 'Infrastructure_upgrades__c',
        'energy_projects': 'Energy_efficiency_projects__c',
        'facility_type': 'Facility_ies_Type__c',
        'square_footage': 'Site_Portfolio_total_square_footage__c',
        'sustainability_commitments': 'Owned_Leased_Managed__c',
        'recent_disclosures': 'Recent_disclosures__c',
        # Removed fields that don't exist yet:
        # 'offbalance_appetite': 'Off_balance_sheet_appetite_summary__c',
    }
    
    def __init__(self):
        """Initialize the enricher with Salesforce and OpenAI connections."""
        self.sf = None
        
        # Load environment variables from .env file
        load_dotenv()
        
        self._connect_to_salesforce()
        self._setup_openai()
    
    def _connect_to_salesforce(self) -> None:
        """Connect to Salesforce using environment variables."""
        try:
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'login')
            
            if not username or not password:
                raise ValueError("Missing required Salesforce credentials in environment variables")
            
            logger.info("🔗 Connecting to Salesforce...")
            
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
    
    def _setup_openai(self) -> None:
        """Setup OpenAI client."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in environment variables")
            
            openai.api_key = api_key
            logger.info("✅ OpenAI API key configured")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI: {str(e)}")
            raise
    
    def get_account_with_all_fields(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get account record with all relevant fields for checking what's empty.
        
        Args:
            record_id: The Salesforce record ID
            
        Returns:
            Account record dict with all fields or None if not found
        """
        try:
            logger.info(f"🔍 Retrieving account with all enrichment fields: {record_id}")
            
            # Build SOQL query with all fields we might update
            fields = ['Id', 'Name', 'Website', 'Industry'] + list(self.FIELD_MAPPING.values())
            query_fields = ', '.join(fields)
            
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
    
    def check_empty_fields(self, account: Dict[str, Any], overwrite: bool = False) -> List[str]:
        """
        Check which fields are empty and can be updated.
        
        Args:
            account: Account record
            overwrite: If True, include all fields; if False, only empty fields
            
        Returns:
            List of field keys that can be updated
        """
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
            
            # Show preview of existing data
            preview = ""
            if current_value and isinstance(current_value, str):
                preview = f" (current: {current_value[:50]}{'...' if len(current_value) > 50 else ''})"
            
            logger.info(f"   {field_key}: {status}{preview}")
        
        logger.info(f"📊 Summary: {len(updatable_fields)}/{len(self.FIELD_MAPPING)} fields can be updated")
        return updatable_fields
    
    def generate_multi_field_data_with_openai(self, company_name: str, website: str = None, 
                                            updatable_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI to generate data for multiple fields in JSON format.
        
        Args:
            company_name: Name of the company/hospital
            website: Optional website URL
            updatable_fields: List of fields that can be updated
            
        Returns:
            Dictionary with field data or None if failed
        """
        try:
            logger.info(f"🤖 Generating multi-field data using OpenAI for: {company_name}")
            
            # Create field descriptions for the prompt
            field_descriptions = {
                'company_description': 'Comprehensive company description (150-250 words)',
                'credit_quality': 'Credit rating/quality if publicly available (e.g., "Aa2 / 0.0234")',
                'credit_quality_detailed': 'Detailed credit information with confidence and source',
                'wacc': 'Weighted Average Cost of Capital estimate with rationale',
                'debt_appetite': 'Debt capacity and borrowing constraints summary',
                'financial_outlook': 'Long-term financial stability and outlook',
                'capital_history': 'Recent capital projects and spending history',
                'future_capital': 'Planned or anticipated capital expenditures',
                'infrastructure_upgrades': 'Energy-related infrastructure improvements',
                'energy_projects': 'Energy efficiency and sustainability projects',
                'facility_type': 'Type of healthcare facility (e.g., "Acute Care Hospital")',
                'square_footage': 'Total facility square footage estimate',
                'sustainability_commitments': 'Energy/emissions goals and commitments',
                'recent_disclosures': 'Recent financial filings or significant announcements'
            }
            
            # Filter to only updatable fields
            relevant_fields = {k: v for k, v in field_descriptions.items() if k in updatable_fields}
            
            # Create the comprehensive search prompt
            prompt = f"""
            Please research and provide comprehensive information about {company_name}, a healthcare organization.
            
            {f'Website: {website}' if website else ''}
            
            Provide your response as a JSON object with the following fields. Only include fields where you have reliable information. Use "null" for fields where information is not available or cannot be reliably estimated.
            
            Fields to research:
            {json.dumps(relevant_fields, indent=2)}
            
            Requirements:
            - Be factual and professional
            - Include confidence levels for estimates (High/Medium/Low)
            - Cite sources when possible
            - Use "Not Available" if information cannot be found
            - For financial estimates, provide ranges and mark as estimates
            - Focus on publicly available information
            
            Response format:
            {{
                "field_name": "value or estimate with confidence",
                "another_field": "value",
                ...
            }}
            """
            
            # Make the OpenAI API call
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a healthcare industry research analyst providing accurate, factual information about healthcare organizations. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                field_data = json.loads(response_content)
                logger.info(f"✅ Generated data for {len(field_data)} fields")
                
                # Log preview of each field
                for field, value in field_data.items():
                    if value and value != "null":
                        preview = str(value)[:80] + "..." if len(str(value)) > 80 else str(value)
                        logger.info(f"   {field}: {preview}")
                
                return field_data
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error calling OpenAI API: {str(e)}")
            return None
    
    def update_account_fields(self, account_id: str, field_data: Dict[str, Any], 
                            updatable_fields: List[str]) -> bool:
        """
        Update multiple account fields in Salesforce.
        
        Args:
            account_id: Salesforce account ID
            field_data: Dictionary with field data from OpenAI
            updatable_fields: List of fields that can be updated
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"💾 Updating account {account_id} with multi-field data...")
            
            # Build update data mapping field keys to Salesforce field names
            update_data = {}
            
            for field_key in updatable_fields:
                if field_key in field_data and field_data[field_key] and field_data[field_key] != "null":
                    value = field_data[field_key]
                    
                    # Skip "Not Available" values as they're not useful
                    if value == "Not Available":
                        logger.info(f"   ⚠️ Skipping {field_key} - value is 'Not Available'")
                        continue
                    
                    salesforce_field = self.FIELD_MAPPING[field_key]
                    update_data[salesforce_field] = value
                    logger.info(f"   ✅ Will update {field_key} -> {salesforce_field}")
            
            if not update_data:
                logger.warning("⚠️ No fields to update")
                return False
            
            # Update the account
            self.sf.Account.update(account_id, update_data)
            logger.info(f"✅ Successfully updated {len(update_data)} fields")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update account: {str(e)}")
            logger.error("💡 This might be due to field permissions or incorrect field names.")
            return False
    
    def process_multi_field_enrichment(self, record_id: str, overwrite: bool = False) -> bool:
        """
        Main method to enrich account with multiple fields.
        
        Args:
            record_id: Salesforce record ID
            overwrite: If True, update all fields; if False, only empty fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Starting multi-field enrichment for record ID: {record_id}")
            logger.info(f"🔧 Overwrite mode: {'ON' if overwrite else 'OFF (empty fields only)'}")
            
            # 1. Get the account with all fields
            account = self.get_account_with_all_fields(record_id)
            if not account:
                logger.error(f"❌ Cannot proceed: Account not found for {record_id}")
                return False
            
            company_name = account.get('Name', '')
            website = account.get('Website', '')
            
            logger.info(f"📋 Account details:")
            logger.info(f"   Name: {company_name}")
            logger.info(f"   Website: {website}")
            
            # 2. Check which fields can be updated
            updatable_fields = self.check_empty_fields(account, overwrite)
            
            if not updatable_fields:
                logger.info("✅ All fields already have data. Use --overwrite to update anyway.")
                return True
            
            # 3. Generate data for updatable fields using OpenAI
            field_data = self.generate_multi_field_data_with_openai(company_name, website, updatable_fields)
            if not field_data:
                logger.error("❌ Failed to generate field data")
                return False
            
            # 4. Show preview and confirm
            logger.info("📝 Generated field data:")
            logger.info("-" * 60)
            for field_key in updatable_fields:
                if field_key in field_data:
                    value = field_data[field_key]
                    preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    logger.info(f"{field_key}: {preview}")
            logger.info("-" * 60)
            
            # Confirm before updating
            try:
                user_input = input(f"Update {len(updatable_fields)} fields in Salesforce? (Y/n): ")
                if user_input.lower() in ['n', 'no']:
                    logger.info("✅ Enrichment cancelled per user request")
                    return True
            except EOFError:
                logger.info("🤖 Automated mode: Proceeding with update")
            
            # 5. Update the account
            success = self.update_account_fields(account['Id'], field_data, updatable_fields)
            
            if success:
                logger.info("✅ Multi-field account enrichment completed successfully")
            else:
                logger.error("❌ Failed to update account fields")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error processing multi-field enrichment: {str(e)}")
            return False


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Multi-field Salesforce Account Enricher')
    parser.add_argument('record_id', help='Salesforce Account Record ID')
    parser.add_argument('--overwrite', action='store_true', 
                       help='Update all fields including those with existing data')
    
    args = parser.parse_args()
    
    try:
        enricher = MultiFieldAccountEnricher()
        success = enricher.process_multi_field_enrichment(args.record_id, args.overwrite)
        
        if success:
            print(f"\n✅ Successfully processed account: {args.record_id}")
            if args.overwrite:
                print("🔧 Used overwrite mode - updated all fields")
            else:
                print("🛡️ Safe mode - only updated empty fields")
        else:
            print(f"\n❌ Failed to process account: {args.record_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
