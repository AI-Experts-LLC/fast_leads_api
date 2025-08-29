from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
from dotenv import load_dotenv
from app.services.salesforce import salesforce_service
from app.services.prospect_discovery import prospect_discovery_service
from app.services.search import serper_service
from app.services.linkedin import linkedin_service
from app.services.ai_qualification import ai_qualification_service

# Load environment variables
load_dotenv()

# Force fresh deployment - no database dependencies

app = FastAPI(
    title="Metrus Energy - Account Enrichment API",
    description="Automated lead enrichment system for Salesforce accounts",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "service": "Metrus Energy Account Enrichment API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {
            "api": "ok",
            "memory": "ok",
            "disk": "ok"
        }
    }

@app.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "build_date": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Salesforce Integration Endpoints

@app.post("/salesforce/connect")
async def connect_salesforce():
    """Connect to Salesforce and test authentication"""
    try:
        success = await salesforce_service.connect()
        
        if success:
            connection_info = await salesforce_service.get_connection_info()
            return {
                "status": "success",
                "message": "Successfully connected to Salesforce",
                "connection_info": connection_info,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=401, 
                detail="Failed to connect to Salesforce. Check credentials."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error connecting to Salesforce: {str(e)}"
        )

@app.get("/salesforce/status")
async def salesforce_status():
    """Get current Salesforce connection status"""
    try:
        connection_info = await salesforce_service.get_connection_info()
        return {
            "status": "success",
            "connection_info": connection_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/salesforce/test-account")
async def test_salesforce_account():
    """Test querying Salesforce accounts"""
    try:
        result = await salesforce_service.test_account_query()
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Successfully queried Salesforce accounts",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to query accounts: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing account query: {str(e)}"
        )

@app.get("/salesforce/test-lead")
async def test_salesforce_lead():
    """Test creating a lead in Salesforce"""
    try:
        result = await salesforce_service.test_lead_create()
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Successfully tested lead creation",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create test lead: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing lead creation: {str(e)}"
        )

@app.get("/salesforce/describe")
async def salesforce_describe():
    """Describe available Salesforce objects in this org"""
    try:
        result = await salesforce_service.describe_available_objects()
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Successfully described Salesforce objects",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to describe objects: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error describing Salesforce objects: {str(e)}"
        )

@app.get("/account/{account_id}")
async def get_account(account_id: str):
    """Get account details by ID (using User as proof of concept)"""
    try:
        result = await salesforce_service.get_account_by_id(account_id)
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Successfully retrieved account",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Account not found: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving account: {str(e)}"
        )

@app.post("/lead")
async def create_lead(lead_data: dict):
    """Create a new lead"""
    try:
        # Validate required fields
        required_fields = ['First_Name__c', 'Last_Name__c', 'Company__c']
        missing_fields = [field for field in required_fields if not lead_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        result = await salesforce_service.create_lead(lead_data)
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Successfully created lead",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create lead: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating lead: {str(e)}"
        )

@app.post("/discover-prospects")
async def discover_prospects(request: dict):
    """
    Complete prospect discovery pipeline for a company
    Searches LinkedIn, qualifies with AI, scrapes profiles
    """
    try:
        company_name = request.get("company_name")
        target_titles = request.get("target_titles", [])
        
        if not company_name:
            raise HTTPException(
                status_code=400,
                detail="company_name is required"
            )
        
        result = await prospect_discovery_service.discover_prospects(
            company_name=company_name,
            target_titles=target_titles if target_titles else None
        )
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Prospect discovery completed",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Prospect discovery failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in prospect discovery: {str(e)}"
        )

@app.get("/test-services")
async def test_prospect_services():
    """Test all prospect discovery services"""
    try:
        result = await prospect_discovery_service.test_services()
        
        return {
            "status": "success",
            "message": "Service tests completed",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing services: {str(e)}"
        )

@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check environment variables (for Railway deployment troubleshooting)"""
    env_vars = {
        "SALESFORCE_USERNAME": bool(os.getenv('SALESFORCE_USERNAME')),
        "SALESFORCE_PASSWORD": bool(os.getenv('SALESFORCE_PASSWORD')),
        "SALESFORCE_SECURITY_TOKEN": bool(os.getenv('SALESFORCE_SECURITY_TOKEN')),
        "SALESFORCE_DOMAIN": os.getenv('SALESFORCE_DOMAIN', 'not_set'),
        "ENVIRONMENT": os.getenv('ENVIRONMENT', 'not_set'),
        "PORT": os.getenv('PORT', 'not_set'),
        "total_env_vars": len(os.environ)
    }
    
    return {
        "status": "debug_info",
        "environment_variables": env_vars,
        "timestamp": datetime.utcnow().isoformat()
    }