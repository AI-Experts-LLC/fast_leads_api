from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing services
load_dotenv()

# Import services AFTER loading environment variables
from app.services.salesforce import salesforce_service
from app.services.prospect_discovery import prospect_discovery_service
from app.services.improved_prospect_discovery import improved_prospect_discovery_service
from app.services.search import serper_service
from app.services.linkedin import linkedin_service
from app.services.ai_qualification import ai_qualification_service
from app.services.credit_enrichment import credit_enrichment_service, CompanyRecord

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

@app.post("/discover-prospects-improved")
async def discover_prospects_improved(request: dict):
    """
    IMPROVED prospect discovery pipeline with better accuracy
    1. Search → 2. Basic Filter → 3. LinkedIn Scrape → 4. AI Rank
    AI only ranks real data, doesn't create/modify data
    """
    try:
        company_name = request.get("company_name")
        target_titles = request.get("target_titles", [])
        company_city = request.get("company_city")
        company_state = request.get("company_state")
        
        if not company_name:
            raise HTTPException(
                status_code=400,
                detail="company_name is required"
            )
        
        result = await improved_prospect_discovery_service.discover_prospects(
            company_name=company_name,
            target_titles=target_titles if target_titles else None,
            company_city=company_city,
            company_state=company_state
        )
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Improved prospect discovery completed",
                "data": result,
                "improvements": {
                    "pipeline_order": "Search → Filter → Scrape → AI Rank",
                    "data_accuracy": "AI only ranks real LinkedIn data",
                    "filtering": "Rule-based filtering before AI involvement"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Improved prospect discovery failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in improved prospect discovery: {str(e)}"
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

# LinkedIn Scraping Endpoints

@app.post("/linkedin/scrape-profiles")
async def scrape_linkedin_profiles(request: dict):
    """
    Scrape LinkedIn profiles directly
    
    Expected request format:
    {
        "linkedin_urls": [
            "https://www.linkedin.com/in/lucaserb/",
            "https://www.linkedin.com/in/emollick/"
        ],
        "include_detailed_data": true
    }
    """
    try:
        linkedin_urls = request.get("linkedin_urls", [])
        if not linkedin_urls:
            raise HTTPException(
                status_code=400,
                detail="linkedin_urls is required"
            )
        
        if len(linkedin_urls) > 10:  # Limit for cost control
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 LinkedIn URLs per request"
            )
        
        result = await linkedin_service.scrape_profiles(linkedin_urls)
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "LinkedIn profiles scraped successfully",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"LinkedIn scraping failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping LinkedIn profiles: {str(e)}"
        )

@app.get("/linkedin/test")
async def test_linkedin_service():
    """Test LinkedIn scraping service with sample profiles"""
    try:
        result = await linkedin_service.test_scraping()
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "LinkedIn service test completed",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "LinkedIn service test failed",
                "error": result.get("error", "Unknown error"),
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "message": "LinkedIn service test error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Credit Enrichment Endpoints

@app.post("/credit/test-connection")
async def test_credit_connection():
    """Test EDF-X API connection and authentication"""
    try:
        result = await credit_enrichment_service.test_connection()
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "EDF-X API connection successful",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"EDF-X connection failed: {result.get('error', 'Unknown error')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing EDF-X connection: {str(e)}"
        )

@app.post("/credit/enrich-company")
async def enrich_company_credit(request: dict):
    """
    Enrich a company with credit rating and PD data from EDF-X
    
    Expected request format:
    {
        "company_name": "Apple Inc",
        "website": "apple.com",  # Optional but recommended for better matching
        "city": "Cupertino",     # Optional
        "state": "CA",           # Optional
        "country": "USA"         # Optional
    }
    """
    try:
        company_name = request.get("company_name")
        if not company_name:
            raise HTTPException(
                status_code=400,
                detail="company_name is required"
            )
        
        # Create company record
        company = CompanyRecord(
            name=company_name,
            website=request.get("website"),
            city=request.get("city"),
            state=request.get("state"),
            country=request.get("country")
        )
        
        # Enrich with credit data
        credit_info = await credit_enrichment_service.enrich_company(company)
        
        # Format response
        response_data = {
            "company_name": company_name,
            "entity_id": credit_info.entity_id,
            "pd_value": credit_info.pd_value,
            "implied_rating": credit_info.implied_rating,
            "confidence": credit_info.confidence,
            "confidence_translated": credit_info.confidence_translated,
            "as_of_date": credit_info.as_of_date,
            "search_success": credit_info.search_success,
            "error_message": credit_info.error_message,
            "matching_logic": credit_info.matching_logic,
            "search_results_count": len(credit_info.search_results) if credit_info.search_results else 0
        }
        
        # Add selected entity info if available
        if credit_info.selected_entity:
            response_data["selected_entity"] = {
                "name": credit_info.selected_entity.get("internationalName"),
                "website": credit_info.selected_entity.get("entityWebsite"),
                "city": credit_info.selected_entity.get("entityContactCity"),
                "state": credit_info.selected_entity.get("entityContactStateProvince"),
                "size": credit_info.selected_entity.get("entitySize"),
                "industry": credit_info.selected_entity.get("primaryIndustryNDYDescription")
            }
        
        return {
            "status": "success" if credit_info.search_success else "partial",
            "message": "Credit enrichment completed",
            "data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enriching company credit: {str(e)}"
        )

@app.post("/credit/batch-enrich")
async def batch_enrich_companies(request: dict):
    """
    Batch enrich multiple companies with credit data
    
    Expected request format:
    {
        "companies": [
            {
                "company_name": "Apple Inc",
                "website": "apple.com",
                "city": "Cupertino",
                "state": "CA"
            },
            {
                "company_name": "Microsoft Corporation", 
                "website": "microsoft.com"
            }
        ]
    }
    """
    try:
        companies_data = request.get("companies", [])
        if not companies_data:
            raise HTTPException(
                status_code=400,
                detail="companies array is required"
            )
        
        if len(companies_data) > 50:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 companies per batch request"
            )
        
        results = []
        
        for company_data in companies_data:
            company_name = company_data.get("company_name")
            if not company_name:
                results.append({
                    "company_name": "Unknown",
                    "error": "Missing company_name"
                })
                continue
            
            # Create company record
            company = CompanyRecord(
                name=company_name,
                website=company_data.get("website"),
                city=company_data.get("city"),
                state=company_data.get("state"),
                country=company_data.get("country")
            )
            
            # Enrich with credit data
            credit_info = await credit_enrichment_service.enrich_company(company)
            
            # Format result
            result = {
                "company_name": company_name,
                "entity_id": credit_info.entity_id,
                "pd_value": credit_info.pd_value,
                "implied_rating": credit_info.implied_rating,
                "confidence": credit_info.confidence,
                "confidence_translated": credit_info.confidence_translated,
                "as_of_date": credit_info.as_of_date,
                "search_success": credit_info.search_success,
                "error_message": credit_info.error_message,
                "matching_logic": credit_info.matching_logic
            }
            
            results.append(result)
        
        # Calculate summary stats
        successful = sum(1 for r in results if r.get("search_success"))
        total = len(results)
        
        return {
            "status": "success",
            "message": f"Batch credit enrichment completed: {successful}/{total} successful",
            "summary": {
                "total_companies": total,
                "successful_enrichments": successful,
                "success_rate": round(successful / total * 100, 1) if total > 0 else 0
            },
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch credit enrichment: {str(e)}"
        )

@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check environment variables (for Railway deployment troubleshooting)"""
    env_vars = {
        "SALESFORCE_USERNAME": bool(os.getenv('SALESFORCE_USERNAME')),
        "SALESFORCE_PASSWORD": bool(os.getenv('SALESFORCE_PASSWORD')),
        "SALESFORCE_SECURITY_TOKEN": bool(os.getenv('SALESFORCE_SECURITY_TOKEN')),
        "SALESFORCE_DOMAIN": os.getenv('SALESFORCE_DOMAIN', 'not_set'),
        "EDFX_USERNAME": bool(os.getenv('EDFX_USERNAME')),
        "EDFX_PASSWORD": bool(os.getenv('EDFX_PASSWORD')),
        "ENVIRONMENT": os.getenv('ENVIRONMENT', 'not_set'),
        "PORT": os.getenv('PORT', 'not_set'),
        "total_env_vars": len(os.environ)
    }
    
    return {
        "status": "debug_info",
        "environment_variables": env_vars,
        "timestamp": datetime.utcnow().isoformat()
    }