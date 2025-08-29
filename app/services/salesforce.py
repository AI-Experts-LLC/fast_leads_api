"""
Simple Salesforce integration service
Handles authentication and basic operations with Salesforce
"""

import os
from typing import Optional, Dict, Any
from simple_salesforce import Salesforce
import logging

logger = logging.getLogger(__name__)


class SalesforceService:
    """Simple Salesforce service for basic operations"""
    
    def __init__(self):
        self.sf = None
        self._authenticated = False
    
    async def connect(self) -> bool:
        """
        Connect to Salesforce using environment variables
        Returns True if successful, False otherwise
        """
        try:
            # Try different authentication methods based on available env vars
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'login')  # 'test' for sandbox
            
            if not username or not password:
                logger.error("Missing Salesforce username or password in environment variables")
                return False
            
            # Connect to Salesforce
            if security_token:
                # Username/password + security token method
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    security_token=security_token,
                    domain=domain
                )
            else:
                # Just username/password (for some environments)
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    domain=domain
                )
            
            # Test the connection with a simple query
            test_result = self.sf.query("SELECT Id FROM User LIMIT 1")
            
            if test_result and test_result.get('totalSize', 0) > 0:
                self._authenticated = True
                logger.info("Successfully connected to Salesforce")
                return True
            else:
                logger.error("Connected to Salesforce but test query failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            self.sf = None
            self._authenticated = False
            return False
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current Salesforce connection"""
        if not self._authenticated or not self.sf:
            return {
                "connected": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # Get basic org info
            org_info = self.sf.Organization.get(self.sf.query("SELECT Id FROM Organization LIMIT 1")['records'][0]['Id'])
            
            return {
                "connected": True,
                "org_name": org_info.get('Name', 'Unknown'),
                "org_id": org_info.get('Id', 'Unknown'),
                "instance_url": self.sf.sf_instance,
                "api_version": self.sf.api_version
            }
        except Exception as e:
            logger.error(f"Error getting connection info: {str(e)}")
            return {
                "connected": self._authenticated,
                "error": str(e),
                "instance_url": getattr(self.sf, 'sf_instance', 'Unknown') if self.sf else 'Unknown'
            }
    
    async def test_account_query(self) -> Dict[str, Any]:
        """Test querying accounts - simple test for account access"""
        if not self._authenticated or not self.sf:
            return {
                "success": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # Query for one account
            result = self.sf.query("SELECT Id, Name, Industry FROM Account LIMIT 1")
            
            return {
                "success": True,
                "total_accounts": result.get('totalSize', 0),
                "sample_account": result['records'][0] if result.get('records') else None
            }
        except Exception as e:
            logger.error(f"Error querying accounts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_lead_create(self) -> Dict[str, Any]:
        """Test creating a simple lead - verify write permissions"""
        if not self._authenticated or not self.sf:
            return {
                "success": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # Create a test lead
            test_lead = {
                'FirstName': 'Test',
                'LastName': 'Lead from API',
                'Company': 'Test Company',
                'Status': 'Open - Not Contacted',
                'Email': 'test@example.com'
            }
            
            result = self.sf.Lead.create(test_lead)
            
            if result.get('success'):
                # Clean up - delete the test lead
                self.sf.Lead.delete(result['id'])
                
                return {
                    "success": True,
                    "test_lead_id": result['id'],
                    "message": "Successfully created and deleted test lead"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create test lead: {result}"
                }
                
        except Exception as e:
            logger.error(f"Error testing lead creation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
salesforce_service = SalesforceService()
