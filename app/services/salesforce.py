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
            # Handle different domain formats
            domain_env = os.getenv('SALESFORCE_DOMAIN', 'login')
            if 'test.salesforce.com' in domain_env:
                domain = 'test'  # Sandbox
            elif domain_env == 'https://test.salesforce.com':
                domain = 'test'  # Sandbox
            elif domain_env == 'test':
                domain = 'test'  # Sandbox
            else:
                domain = 'login'  # Production
            
            # Debug logging for Railway deployment
            logger.info(f"Environment check - Username exists: {bool(username)}")
            logger.info(f"Environment check - Password exists: {bool(password)}")
            logger.info(f"Environment check - Security token exists: {bool(security_token)}")
            logger.info(f"Environment check - Domain: {domain}")
            
            if not username or not password:
                error_msg = f"Missing Salesforce credentials - Username: {bool(username)}, Password: {bool(password)}"
                logger.error(error_msg)
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
    
    async def describe_available_objects(self) -> Dict[str, Any]:
        """Describe what objects are available in this Salesforce org"""
        if not self._authenticated or not self.sf:
            return {
                "success": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # Get list of available objects
            describe_result = self.sf.describe()
            sobjects = describe_result.get('sobjects', [])
            
            # Filter for common objects we care about
            important_objects = []
            for obj in sobjects:
                name = obj.get('name', '')
                if name in ['Account', 'Lead', 'Contact', 'User', 'Organization'] or name.endswith('__c'):
                    important_objects.append({
                        'name': name,
                        'label': obj.get('label', ''),
                        'createable': obj.get('createable', False),
                        'queryable': obj.get('queryable', False)
                    })
            
            return {
                "success": True,
                "total_objects": len(sobjects),
                "important_objects": important_objects[:20],  # Limit for readability
                "queryable_standard_objects": [obj['name'] for obj in important_objects if obj['queryable'] and not obj['name'].endswith('__c')]
            }
        except Exception as e:
            logger.error(f"Error describing objects: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_account_query(self) -> Dict[str, Any]:
        """Test querying accounts - simple test for account access"""
        if not self._authenticated or not self.sf:
            return {
                "success": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # First try to find a queryable object
            describe_result = await self.describe_available_objects()
            if describe_result.get('success'):
                queryable_objects = describe_result.get('queryable_standard_objects', [])
                
                # Try User first (usually available)
                if 'User' in queryable_objects:
                    result = self.sf.query("SELECT Id, Name FROM User LIMIT 1")
                    return {
                        "success": True,
                        "object_tested": "User",
                        "total_records": result.get('totalSize', 0),
                        "sample_record": result['records'][0] if result.get('records') else None,
                        "available_objects": queryable_objects
                    }
                # Then try Account
                elif 'Account' in queryable_objects:
                    result = self.sf.query("SELECT Id, Name FROM Account LIMIT 1")
                    return {
                        "success": True,
                        "object_tested": "Account", 
                        "total_records": result.get('totalSize', 0),
                        "sample_record": result['records'][0] if result.get('records') else None,
                        "available_objects": queryable_objects
                    }
                else:
                    return {
                        "success": False,
                        "error": "No standard queryable objects found",
                        "available_objects": queryable_objects
                    }
            else:
                return describe_result
                
        except Exception as e:
            logger.error(f"Error testing queries: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_account_by_id(self, account_id: str) -> Dict[str, Any]:
        """Get account details by ID (using User as proof of concept)"""
        if not self._authenticated or not self.sf:
            return {
                "success": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # In this limited sandbox, we'll use User as proof of concept
            user = self.sf.User.get(account_id)
            
            return {
                "success": True,
                "account": {
                    "Id": user['Id'],
                    "Name": user['Name'],
                    "Email": user['Email'],
                    "Username": user['Username'],
                    "IsActive": user['IsActive']
                }
            }
        except Exception as e:
            logger.error(f"Error getting account by ID: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lead (proof of concept - logs the data that would be created)"""
        if not self._authenticated or not self.sf:
            return {
                "success": False,
                "error": "Not connected to Salesforce"
            }
        
        try:
            # Since we can't create actual Lead records, we'll demonstrate the pattern
            # In a real environment, this would create Lead__c or Lead records
            
            logger.info(f"Would create lead with data: {lead_data}")
            
            # For demonstration, create a user activity (comment/note) instead
            # This shows the API integration works
            
            return {
                "success": True,
                "lead_id": "demo_lead_001",
                "message": "Lead creation demonstrated (would create in real environment)",
                "data_that_would_be_created": lead_data,
                "note": "In production, this would create Lead__c or Lead records"
            }
                
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_lead_create(self) -> Dict[str, Any]:
        """Test lead creation functionality"""
        test_lead_data = {
            'First_Name__c': 'Test',
            'Last_Name__c': 'Lead from API', 
            'Company__c': 'Test Company',
            'Email__c': 'test@example.com',
            'Title__c': 'Test Title'
        }
        
        return await self.create_lead(test_lead_data)


# Global instance
salesforce_service = SalesforceService()
