"""
Salesforce Enrichment Service

This service provides enrichment capabilities for Salesforce accounts and contacts
through FastAPI endpoints.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# Import enrichers from the enrichers module
from app.enrichers.web_search_account_enricher import WebSearchAccountEnricher
from app.enrichers.web_search_contact_enricher import WebSearchContactEnricher

logger = logging.getLogger(__name__)


# Request/Response Models
class AccountEnrichmentRequest(BaseModel):
    """Request model for account enrichment"""
    account_id: str = Field(..., description="Salesforce Account ID")
    overwrite: bool = Field(False, description="Overwrite existing field data")
    include_financial: bool = Field(False, description="Include financial data analysis")


class ContactEnrichmentRequest(BaseModel):
    """Request model for contact enrichment"""
    contact_id: str = Field(..., description="Salesforce Contact ID")
    overwrite: bool = Field(False, description="Overwrite existing field data")
    include_linkedin: bool = Field(False, description="Include LinkedIn profile scraping")


class EnrichmentResponse(BaseModel):
    """Response model for enrichment operations"""
    status: str = Field(..., description="Status of the enrichment operation")
    record_id: str = Field(..., description="Salesforce record ID")
    message: str = Field(..., description="Human-readable message")
    enriched_fields: Optional[Dict[str, Any]] = Field(None, description="Fields that were enriched")
    errors: Optional[Dict[str, Any]] = Field(None, description="Any errors encountered")


class EnrichmentService:
    """Service for managing Salesforce enrichment operations"""

    def __init__(self):
        """Initialize the enrichment service"""
        self.account_enricher = None
        self.contact_enricher = None

    def _get_account_enricher(self) -> WebSearchAccountEnricher:
        """Get or create account enricher instance"""
        if self.account_enricher is None:
            logger.info("Initializing WebSearchAccountEnricher...")
            self.account_enricher = WebSearchAccountEnricher()
        return self.account_enricher

    def _get_contact_enricher(self) -> WebSearchContactEnricher:
        """Get or create contact enricher instance"""
        if self.contact_enricher is None:
            logger.info("Initializing WebSearchContactEnricher...")
            self.contact_enricher = WebSearchContactEnricher()
        return self.contact_enricher

    async def enrich_account(
        self,
        account_id: str,
        overwrite: bool = False,
        include_financial: bool = False
    ) -> Dict[str, Any]:
        """
        Enrich a Salesforce account with web search data
        
        Args:
            account_id: Salesforce Account ID
            overwrite: Whether to overwrite existing data
            include_financial: Whether to include financial analysis
            
        Returns:
            Dict with enrichment results
        """
        try:
            logger.info(f"Starting account enrichment for {account_id}")
            logger.info(f"Options: overwrite={overwrite}, include_financial={include_financial}")

            enricher = self._get_account_enricher()
            
            # Run the enrichment process
            success = enricher.process_web_search_enrichment(
                record_id=account_id,
                overwrite=overwrite,
                include_financial=include_financial
            )

            if success:
                # Get the enriched account to see what was updated
                account = enricher.get_account_details(account_id)
                
                return {
                    "status": "success",
                    "record_id": account_id,
                    "message": f"Successfully enriched account {account_id}",
                    "enriched_fields": {
                        "account_name": account.get('Name'),
                        "overwrite_mode": overwrite,
                        "financial_included": include_financial
                    }
                }
            else:
                return {
                    "status": "failed",
                    "record_id": account_id,
                    "message": "Account enrichment failed - check logs for details",
                    "errors": {"enrichment": "Process returned failure status"}
                }

        except Exception as e:
            logger.error(f"Error enriching account {account_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "record_id": account_id,
                "message": f"Error during account enrichment: {str(e)}",
                "errors": {"exception": str(e)}
            }

    async def enrich_contact(
        self,
        contact_id: str,
        overwrite: bool = False,
        include_linkedin: bool = False
    ) -> Dict[str, Any]:
        """
        Enrich a Salesforce contact with web search data
        
        Args:
            contact_id: Salesforce Contact ID
            overwrite: Whether to overwrite existing data
            include_linkedin: Whether to include LinkedIn enrichment
            
        Returns:
            Dict with enrichment results
        """
        try:
            logger.info(f"Starting contact enrichment for {contact_id}")
            logger.info(f"Options: overwrite={overwrite}, include_linkedin={include_linkedin}")

            enricher = self._get_contact_enricher()
            
            # Run the enrichment process (it's async)
            success = await enricher.process_contact_enrichment(
                record_id=contact_id,
                overwrite=overwrite,
                include_linkedin=include_linkedin
            )

            if success:
                # Get the enriched contact to see what was updated
                contact = enricher.get_contact_details(contact_id)
                
                return {
                    "status": "success",
                    "record_id": contact_id,
                    "message": f"Successfully enriched contact {contact_id}",
                    "enriched_fields": {
                        "contact_name": f"{contact.get('FirstName', '')} {contact.get('LastName', '')}".strip(),
                        "company": contact.get('account_name'),
                        "overwrite_mode": overwrite,
                        "linkedin_included": include_linkedin
                    }
                }
            else:
                return {
                    "status": "failed",
                    "record_id": contact_id,
                    "message": "Contact enrichment failed - check logs for details",
                    "errors": {"enrichment": "Process returned failure status"}
                }

        except Exception as e:
            logger.error(f"Error enriching contact {contact_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "record_id": contact_id,
                "message": f"Error during contact enrichment: {str(e)}",
                "errors": {"exception": str(e)}
            }


# Create a singleton instance
enrichment_service = EnrichmentService()

