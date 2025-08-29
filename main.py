from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
from dotenv import load_dotenv
from app.services.salesforce import salesforce_service

# Load environment variables
load_dotenv()

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