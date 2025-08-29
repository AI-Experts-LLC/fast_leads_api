"""
Salesforce API integration service
"""
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from simple_salesforce import Salesforce
from requests_oauthlib import OAuth2Session
import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SalesforceService:
    """Async Salesforce API client service"""
    
    def __init__(self):
        self.settings = settings
        self.access_token: Optional[str] = None
        self.instance_url: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Salesforce using OAuth 2.0
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Determine Salesforce domain
            # Support for production, sandbox, and custom domains
            if self.settings.salesforce_domain:
                domain_lower = self.settings.salesforce_domain.lower()
                if 'test.salesforce.com' in domain_lower or 'sandbox' in domain_lower:
                    # Sandbox environment
                    domain = 'test'
                elif 'salesforce.com' in domain_lower:
                    # Standard Production account
                    domain = 'login'
                else:
                    # Custom domain (e.g., company.my.salesforce.com)
                    domain = self.settings.salesforce_domain.replace('https://', '').replace('http://', '')
            else:
                # Default to standard production login
                domain = 'login'
            
            logger.info(f"Authenticating with Salesforce using domain: {domain}")
            
            # Use simple-salesforce for initial authentication
            sf = Salesforce(
                username=self.settings.salesforce_username,
                password=self.settings.salesforce_password,
                security_token=self.settings.salesforce_security_token,
                domain=domain
            )
            
            self.access_token = sf.session_id
            self.instance_url = sf.sf_instance
            self.token_expires_at = datetime.utcnow() + timedelta(hours=2)  # Tokens typically expire in 2 hours
            
            # Create async HTTP client
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            self._client = httpx.AsyncClient(
                base_url=f"https://{self.instance_url}",
                headers=headers,
                timeout=30.0
            )
            
            logger.info("Successfully authenticated with Salesforce")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Salesforce: {e}")
            return False
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid authentication token"""
        if not self.access_token or not self.token_expires_at:
            await self.authenticate()
        elif datetime.utcnow() >= self.token_expires_at - timedelta(minutes=5):
            # Refresh token 5 minutes before expiry
            await self.authenticate()
    
    async def query_accounts(self, query: str) -> List[Dict[str, Any]]:
        """
        Query Salesforce accounts
        
        Args:
            query: SOQL query string
            
        Returns:
            List of account records
        """
        await self._ensure_authenticated()
        
        try:
            response = await self._client.get(
                f"/services/data/v58.0/query",
                params={'q': query}
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('records', [])
            
        except Exception as e:
            logger.error(f"Failed to query accounts: {e}")
            raise
    
    async def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get account by Salesforce ID
        
        Args:
            account_id: Salesforce Account ID
            
        Returns:
            Account record or None if not found
        """
        await self._ensure_authenticated()
        
        try:
            response = await self._client.get(
                f"/services/data/v58.0/sobjects/Account/{account_id}"
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get account {account_id}: {e}")
            raise
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """
        Create a new Lead record in Salesforce
        
        Args:
            lead_data: Lead field data
            
        Returns:
            Created Lead ID
        """
        await self._ensure_authenticated()
        
        try:
            response = await self._client.post(
                "/services/data/v58.0/sobjects/Lead",
                json=lead_data
            )
            response.raise_for_status()
            
            result = response.json()
            lead_id = result.get('id')
            
            logger.info(f"Created Salesforce Lead: {lead_id}")
            return lead_id
            
        except Exception as e:
            logger.error(f"Failed to create lead: {e}")
            raise
    
    async def create_leads_bulk(self, leads_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple Lead records using Bulk API
        
        Args:
            leads_data: List of lead field data
            
        Returns:
            List of creation results with IDs and success status
        """
        await self._ensure_authenticated()
        
        if not leads_data:
            return []
        
        try:
            # Use composite API for bulk operations
            composite_request = {
                "allOrNone": False,
                "compositeRequest": []
            }
            
            for i, lead_data in enumerate(leads_data):
                composite_request["compositeRequest"].append({
                    "method": "POST",
                    "url": "/services/data/v58.0/sobjects/Lead",
                    "referenceId": f"lead_{i}",
                    "body": lead_data
                })
            
            response = await self._client.post(
                "/services/data/v58.0/composite",
                json=composite_request
            )
            response.raise_for_status()
            
            result = response.json()
            results = []
            
            for composite_response in result.get("compositeResponse", []):
                if composite_response["httpStatusCode"] in [200, 201]:
                    results.append({
                        "success": True,
                        "id": composite_response["body"]["id"],
                        "reference_id": composite_response["referenceId"]
                    })
                else:
                    results.append({
                        "success": False,
                        "error": composite_response["body"],
                        "reference_id": composite_response["referenceId"]
                    })
            
            successful_creates = len([r for r in results if r["success"]])
            logger.info(f"Bulk created {successful_creates}/{len(leads_data)} leads")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to bulk create leads: {e}")
            raise
    
    async def update_account(self, account_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update account record
        
        Args:
            account_id: Salesforce Account ID
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        await self._ensure_authenticated()
        
        try:
            response = await self._client.patch(
                f"/services/data/v58.0/sobjects/Account/{account_id}",
                json=updates
            )
            response.raise_for_status()
            
            logger.info(f"Updated account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update account {account_id}: {e}")
            return False
    
    def map_prospect_to_lead(self, prospect: Dict[str, Any], account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map enriched prospect data to Salesforce Lead fields
        
        Args:
            prospect: Enriched prospect data
            account: Source account data
            
        Returns:
            Salesforce Lead field mapping
        """
        lead_data = {
            "FirstName": prospect.get("first_name"),
            "LastName": prospect.get("last_name"),
            "Title": prospect.get("title"),
            "Company": prospect.get("company") or account.get("Name"),
            "Email": prospect.get("email"),
            "Phone": prospect.get("phone"),
            "City": prospect.get("location"),
            "LeadSource": "AI Enrichment",
            "Status": "Open - Not Contacted",
            
            # Custom fields (adjust based on your Salesforce schema)
            "LinkedIn_Profile_URL__c": prospect.get("linkedin_url"),
            "Persona_Type__c": prospect.get("persona_type"),
            "Persona_Match_Score__c": prospect.get("persona_match_score"),
            "AI_Qualification_Score__c": prospect.get("qualification_score"),
            "AI_Generated_Message__c": prospect.get("ai_generated_message"),
            "Source_Enrichment_Job__c": prospect.get("enrichment_job_id"),
            "Email_Verification_Status__c": prospect.get("email_verification_status"),
            "Pain_Points_Identified__c": ";".join(prospect.get("pain_points", [])),
            "Personalization_Elements__c": json.dumps(prospect.get("personalization_elements", []))
        }
        
        # Remove None values
        lead_data = {k: v for k, v in lead_data.items() if v is not None}
        
        return lead_data
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Salesforce connection health check
        
        Returns:
            Health status information
        """
        try:
            await self._ensure_authenticated()
            
            # Simple query to test connection
            response = await self._client.get("/services/data/v58.0/limits")
            response.raise_for_status()
            
            limits = response.json()
            
            return {
                "status": "healthy",
                "instance_url": self.instance_url,
                "api_version": "v58.0",
                "daily_api_requests_used": limits.get("DailyApiRequests", {}).get("Remaining"),
                "daily_api_requests_limit": limits.get("DailyApiRequests", {}).get("Max"),
                "authenticated": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "authenticated": False
            }


# Global Salesforce service instance
salesforce_service = SalesforceService()


async def get_salesforce_service() -> SalesforceService:
    """Get Salesforce service instance"""
    return salesforce_service
