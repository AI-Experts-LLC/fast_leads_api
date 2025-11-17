from fastapi import FastAPI, HTTPException, Depends, Header, Cookie
from fastapi.responses import HTMLResponse, FileResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import os
import secrets
from typing import Optional
from dotenv import load_dotenv

# Load environment variables BEFORE importing services
load_dotenv()

# Import services AFTER loading environment variables
from app.services.salesforce import salesforce_service
from app.services.prospect_discovery import prospect_discovery_service
from app.services.improved_prospect_discovery import improved_prospect_discovery_service
from app.services.three_step_prospect_discovery import three_step_prospect_discovery_service
from app.services.zoominfo_validation import zoominfo_validation_service
from app.services.search import serper_service
from app.services.linkedin import linkedin_service
from app.services.ai_qualification import ai_qualification_service
from app.services.credit_enrichment import credit_enrichment_service, CompanyRecord
from app.services.enrichment import enrichment_service, AccountEnrichmentRequest, ContactEnrichmentRequest
from app.auth import (
    verify_api_key,
    verify_dashboard_session,
    check_dashboard_session,
    verify_dashboard_password,
    create_session_token,
    active_sessions
)

# Import database and models
from app.database import init_db, get_db
from app.models import APILog
from app.services.logging_middleware import APILoggingMiddleware

app = FastAPI(
    title="Metrus Energy - Account Enrichment API",
    description="""
    Automated prospect discovery and lead enrichment system for Salesforce accounts.

    **Recommended Pipeline**: Three-Step Prospect Discovery
    - Step 1: Search & Filter LinkedIn profiles
    - Step 2: Scrape & Validate employment/company
    - Step 3: AI Ranking & Qualification

    **Optional**: ZoomInfo validation for contact enrichment

    See /docs for interactive API documentation.
    """,
    version="1.0.0"
)

# Add logging middleware
app.add_middleware(APILoggingMiddleware)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize database: {e}")

@app.get("/")
async def root():
    return {
        "service": "Metrus Energy Account Enrichment API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "dashboards": {
            "main": "/dashboard",
            "login": "/dashboard/login",
            "enrichment": "/enrich",
            "logs": "/logs/view",
            "api_docs": "/docs"
        },
        "note": "Access web dashboards at /dashboard (password required)"
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

@app.get("/favicon.ico")
async def favicon():
    """
    Serve favicon - redirects to Metrus Energy logo
    Prevents 404 errors in logs from browser favicon requests
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="https://cdn.prod.website-files.com/6645c7ede4572bff5e1bcfd5/6646259b5e59ac14d6e515e2_metrus-bolt-image-01-664624137b786.webp",
        status_code=302
    )

@app.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "build_date": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

########################################
# SALESFORCE INTEGRATION ENDPOINTS
########################################
# These endpoints handle authentication and data operations with Salesforce CRM.
# Used for creating leads, querying accounts, and syncing enrichment data.

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

########################################
# PROSPECT DISCOVERY PIPELINES
########################################
# Three different pipeline implementations for discovering LinkedIn prospects.
#
# 1. ORIGINAL PIPELINE (DEPRECATED) - /discover-prospects
#    Issue: AI creates/modifies data before LinkedIn scraping
#    Use Case: Legacy compatibility only
#
# 2. IMPROVED PIPELINE (DEPRECATED) - /discover-prospects-improved
#    Issue: Times out on Railway (5-minute limit)
#    Use Case: Local development only
#
# 3. THREE-STEP PIPELINE (RECOMMENDED) - /discover-prospects-step1/2/3
#    Benefits: Avoids timeouts, accurate data, production-tested
#    Use Case: All production workloads
#
# 4. ZOOMINFO VALIDATION (OPTIONAL) - /discover-prospects-zoominfo
#    Benefits: Validates contact info (email, phone)
#    Use Case: Optional enhancement after Step 3

@app.post("/discover-prospects")
async def discover_prospects(request: dict):
    """
    ⚠️ DEPRECATED - Use /discover-prospects-step1 instead

    Original prospect discovery pipeline for a company.
    Searches LinkedIn, qualifies with AI, scrapes profiles.

    **Issue**: AI creates/modifies data before scraping, causing accuracy problems.
    **Recommendation**: Use the three-step pipeline instead (/discover-prospects-step1).
    **Status**: Maintained for backward compatibility only.
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
    ⚠️ DEPRECATED - Use /discover-prospects-step1 instead

    Improved prospect discovery pipeline with better accuracy.
    Pipeline: Search → Basic Filter → LinkedIn Scrape → AI Rank

    **Issue**: Times out on Railway (5-minute deployment limit).
    **Recommendation**: Use the three-step pipeline instead (/discover-prospects-step1).
    **Status**: Maintained for local development and backward compatibility.

    **Improvement over original**: AI only ranks real data, doesn't create/modify data.
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

########################################
# THREE-STEP PIPELINE (RECOMMENDED)
########################################
# Production-ready pipeline that avoids Railway timeout by splitting into 3 API calls.
# October 2025 Production Results: 69% success rate, 23 prospects from 13 hospitals
#
# Total Time: 50-150 seconds per hospital (~1-2.5 minutes)
# Cost: ~$0.40 per hospital
#
# Pipeline Flow:
#   Step 1 (30-90s)  → Search & Filter LinkedIn profiles
#   Step 2 (15-35s)  → Scrape profiles & validate company/employment
#   Step 3 (5-25s)   → AI ranking & qualification (score ≥65)
#
# See THREE_STEP_PIPELINE.md for complete documentation.

@app.post("/discover-prospects-step1")
async def discover_prospects_step1(request: dict):
    """
    ✅ RECOMMENDED - Step 1 of 3-Step Pipeline: Search and Filter

    **What it does:**
    - Searches LinkedIn profiles using Serper API (Google Search)
    - Applies basic filters (removes interns, students, former employees)
    - Applies AI title relevance scoring (threshold: ≥55)
    - Returns filtered prospect URLs ready for scraping

    **Expected Time:** 30-90 seconds

    **Request format:**
    ```json
    {
        "company_name": "Mayo Clinic",
        "company_city": "Rochester",
        "company_state": "Minnesota",
        "target_titles": []  // Optional - uses defaults if not provided
    }
    ```

    **Next Step:** Call /discover-prospects-step2 with the returned linkedin_urls
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

        result = await three_step_prospect_discovery_service.step1_search_and_filter(
            company_name=company_name,
            target_titles=target_titles if target_titles else None,
            company_city=company_city,
            company_state=company_state
        )

        if result.get("success"):
            return {
                "status": "success",
                "message": "Step 1: Search and filter completed",
                "data": result,
                "next_step": "Call /discover-prospects-step2 with linkedin_urls from this response",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Step 1 failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in step 1: {str(e)}"
        )

@app.post("/discover-prospects-step2")
async def discover_prospects_step2(request: dict):
    """
    ✅ RECOMMENDED - Step 2 of 3-Step Pipeline: Scrape LinkedIn Profiles

    **What it does:**
    - Takes LinkedIn URLs from Step 1
    - Scrapes full profile data via Apify (35+ fields per profile)
    - Validates company name with St/Saint normalization
    - Validates current employment status
    - Filters by location (same state as hospital)
    - Checks LinkedIn connections (≥50 required)
    - Returns enriched prospect data ready for AI ranking

    **Expected Time:** 15-35 seconds

    **Request format:**
    ```json
    {
        "linkedin_urls": ["https://linkedin.com/in/...", ...],
        "company_name": "Mayo Clinic",
        "company_city": "Rochester",
        "company_state": "Minnesota",
        "location_filter_enabled": true  // Optional, defaults to true
    }
    ```

    **Key Filters:**
    - Company matching: Handles "St." vs "Saint", state abbreviations
    - Employment: Current employees only (not former)
    - Location: Same state as hospital (if enabled)
    - Connections: ≥50 LinkedIn connections (spam prevention)

    **Next Step:** Call /discover-prospects-step3 with the returned enriched_prospects
    """
    try:
        linkedin_urls = request.get("linkedin_urls", [])
        company_name = request.get("company_name")
        company_city = request.get("company_city")
        company_state = request.get("company_state")
        location_filter_enabled = request.get("location_filter_enabled", True)

        if not linkedin_urls:
            raise HTTPException(
                status_code=400,
                detail="linkedin_urls is required"
            )

        if not company_name:
            raise HTTPException(
                status_code=400,
                detail="company_name is required"
            )

        result = await three_step_prospect_discovery_service.step2_scrape_profiles(
            linkedin_urls=linkedin_urls,
            company_name=company_name,
            company_city=company_city,
            company_state=company_state,
            location_filter_enabled=location_filter_enabled
        )

        if result.get("success"):
            return {
                "status": "success",
                "message": "Step 2: LinkedIn scraping and filtering completed",
                "data": result,
                "next_step": "Call /discover-prospects-step3 with enriched_prospects from this response",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Step 2 failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in step 2: {str(e)}"
        )

@app.post("/discover-prospects-step3")
async def discover_prospects_step3(request: dict):
    """
    ✅ RECOMMENDED - Step 3 of 3-Step Pipeline: AI Ranking

    **What it does:**
    - Takes enriched prospects from Step 2
    - Runs parallel AI ranking on each prospect using GPT-4
    - Scores 0-100 based on multiple factors
    - Filters by minimum score threshold (≥65)
    - Returns top N prospects sorted by score

    **Expected Time:** 5-25 seconds

    **Request format:**
    ```json
    {
        "enriched_prospects": [...],  // From Step 2 response
        "company_name": "Mayo Clinic",
        "min_score_threshold": 65,     // Optional, defaults to 65
        "max_prospects": 10            // Optional, defaults to 10
    }
    ```

    **AI Scoring Factors (0-100 scale):**
    - Job Title Relevance (35%) - Director of Facilities = 35-40 pts
    - Decision Authority (25%) - High authority = 20-25 pts
    - Employment Confidence (20%) - High confidence gets bonus points
    - Company Size (15%) - Large healthcare systems = 12-15 pts
    - Accessibility (5%) - Active LinkedIn profile = 8-10 pts

    **Pipeline Complete:** This is the final step. Results ready for Salesforce import.

    **Optional Next Step:** Call /discover-prospects-zoominfo for contact validation
    """
    try:
        enriched_prospects = request.get("enriched_prospects", [])
        company_name = request.get("company_name")
        min_score_threshold = request.get("min_score_threshold", 65)
        max_prospects = request.get("max_prospects", 10)

        if not enriched_prospects:
            raise HTTPException(
                status_code=400,
                detail="enriched_prospects is required"
            )

        if not company_name:
            raise HTTPException(
                status_code=400,
                detail="company_name is required"
            )

        result = await three_step_prospect_discovery_service.step3_rank_prospects(
            enriched_prospects=enriched_prospects,
            company_name=company_name,
            min_score_threshold=min_score_threshold,
            max_prospects=max_prospects
        )

        if result.get("success"):
            return {
                "status": "success",
                "message": "Step 3: AI ranking completed - Pipeline finished!",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Step 3 failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in step 3: {str(e)}"
        )

########################################
# ZOOMINFO VALIDATION (OPTIONAL)
########################################
# Optional enhancement to validate and enrich contact information using ZoomInfo.
# Can be used after Step 3 to validate email addresses and phone numbers.
#
# Note: ZoomInfo integration requires OAuth setup. If not configured, this endpoint
# will gracefully return the original data without validation.

@app.post("/discover-prospects-zoominfo")
async def discover_prospects_zoominfo(request: dict):
    """
    🔍 OPTIONAL - ZoomInfo Contact Validation

    **What it does:**
    - Takes qualified prospects from Step 3
    - Validates contact info (email, phone) with ZoomInfo API
    - Compares LinkedIn vs ZoomInfo data for accuracy
    - Uses ZoomInfo data when different (assumed more current)
    - Returns validated prospects with enriched contact information

    **Expected Time:** 10-20 seconds

    **Request format:**
    ```json
    {
        "qualified_prospects": [...],  // From Step 3 response
        "company_name": "Mayo Clinic"
    }
    ```

    **Status:** Optional enhancement. If ZoomInfo is not configured, returns
    original prospects unchanged with a graceful skip message.

    **Use Case:**
    - Validate email deliverability before sending campaigns
    - Get direct phone numbers for prospects
    - Confirm current employment status
    - Get more accurate contact information than LinkedIn provides
    """
    try:
        qualified_prospects = request.get("qualified_prospects", [])
        company_name = request.get("company_name")

        if not qualified_prospects:
            raise HTTPException(
                status_code=400,
                detail="qualified_prospects is required"
            )

        result = await zoominfo_validation_service.validate_and_enrich_prospects(
            prospects=qualified_prospects
        )

        if result.get("success"):
            return {
                "status": "success",
                "message": "ZoomInfo validation completed",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # If ZoomInfo is not configured, still return success with original data
            if "not configured" in result.get("error", ""):
                return {
                    "status": "success",
                    "message": "ZoomInfo validation skipped (not configured)",
                    "data": {
                        "success": True,
                        "prospects": qualified_prospects,
                        "stats": {"total": len(qualified_prospects), "skipped": len(qualified_prospects)},
                        "note": "ZoomInfo is not configured. Returning original prospects unchanged."
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

            raise HTTPException(
                status_code=400,
                detail=f"ZoomInfo validation failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in ZoomInfo validation: {str(e)}"
        )

########################################
# TESTING & DEBUG ENDPOINTS
########################################
# Utility endpoints for testing API integrations and debugging issues.

@app.get("/test-services")
async def test_prospect_services():
    """
    🧪 Test all prospect discovery service integrations

    Tests connectivity and authentication for:
    - Serper API (LinkedIn search)
    - OpenAI API (AI qualification)
    - Apify API (LinkedIn scraping)
    - Salesforce API (CRM integration)

    Returns status and sample responses for each service.
    """
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

########################################
# LINKEDIN SCRAPING ENDPOINTS
########################################
# Direct LinkedIn profile scraping via Apify.
# Used internally by the prospect discovery pipeline, but also available as standalone endpoints.

@app.post("/linkedin/scrape-profiles")
async def scrape_linkedin_profiles(request: dict):
    """
    🔍 Scrape LinkedIn profiles directly via Apify

    **Use Case:** Standalone LinkedIn data extraction without the full pipeline.

    **What it returns:**
    - 35+ fields per profile (name, title, company, location, etc.)
    - Full work experience history
    - Education, skills, and certifications
    - LinkedIn connections and follower count
    - Contact information (email, phone if available)

    **Rate Limits:** Maximum 10 LinkedIn URLs per request (cost control)

    **Request format:**
    ```json
    {
        "linkedin_urls": [
            "https://www.linkedin.com/in/lucaserb/",
            "https://www.linkedin.com/in/emollick/"
        ],
        "include_detailed_data": true
    }
    ```

    **Cost:** ~$0.005 per profile (~$0.05 for 10 profiles)
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
    """
    🧪 Test LinkedIn scraping service with sample profiles

    Tests Apify LinkedIn scraper integration with a few sample profiles.
    Useful for verifying API key and connectivity.
    """
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

########################################
# CREDIT ENRICHMENT ENDPOINTS (EDF-X)
########################################
# Company credit rating and probability of default (PD) enrichment via EDF-X.
# Provides financial risk assessment for healthcare facilities.

@app.post("/credit/test-connection")
async def test_credit_connection():
    """
    🧪 Test EDF-X API connection and authentication

    Verifies EDF-X credentials and API connectivity.
    Returns sample entity search to confirm integration is working.
    """
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
    💰 Enrich a company with credit rating and PD data from EDF-X

    **What it returns:**
    - Credit rating (AAA to D scale)
    - Probability of Default (PD) percentage
    - Confidence score (0-100%)
    - Company size and industry classification
    - As-of date for credit data

    **Use Case:** Financial risk assessment for healthcare facility prospects.

    **Request format:**
    ```json
    {
        "company_name": "Mayo Clinic",
        "website": "mayoclinic.org",  // Optional but recommended for better matching
        "city": "Rochester",           // Optional
        "state": "Minnesota",          // Optional
        "country": "USA"               // Optional
    }
    ```

    **Matching Logic:**
    - Exact name + website match (highest confidence)
    - Fuzzy name match with location (medium confidence)
    - Name-only match (lower confidence)
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
    💰 Batch enrich multiple companies with credit data

    **Rate Limits:** Maximum 50 companies per batch request

    **Use Case:** Enrich multiple healthcare facilities with financial risk data in one call.

    **Request format:**
    ```json
    {
        "companies": [
            {
                "company_name": "Mayo Clinic",
                "website": "mayoclinic.org",
                "city": "Rochester",
                "state": "Minnesota"
            },
            {
                "company_name": "Cleveland Clinic",
                "website": "clevelandclinic.org"
            }
        ]
    }
    ```

    **Returns:** Array of credit enrichment results with summary statistics.
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

########################################
# SALESFORCE ENRICHMENT ENDPOINTS
########################################
# AI-powered enrichment of Salesforce accounts and contacts.
# Requires API key authentication (X-API-Key header).
#
# Account Enrichment: Company data, financials, credit ratings
# Contact Enrichment: Personalized rapport, role analysis, campaign content

@app.post("/enrich/account")
async def enrich_account(
    request: AccountEnrichmentRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    🏢 Enrich a Salesforce account with comprehensive company data

    **Authentication Required:** Include `X-API-Key` header

    **What it enriches:**
    - Company description, HQ location, employee count
    - Geographic footprint and recent news
    - Capital project history and infrastructure upgrades
    - Energy efficiency projects
    - Financial data (if include_financial is True)
    - Credit rating/PD (if credit_only is True, runs ONLY EDFx enrichment)

    **Request format:**
    ```json
    {
        "account_id": "001VR00000UhY3oYAF",
        "overwrite": false,           // Skip if already enriched
        "include_financial": true,    // Include credit rating
        "credit_only": false          // Only run EDFx credit enrichment
    }
    ```

    **Headers:**
    ```
    X-API-Key: your-api-key
    ```

    **Use Case:** Enrich healthcare facility accounts before outreach campaigns.
    """
    try:
        result = await enrichment_service.enrich_account(
            account_id=request.account_id,
            overwrite=request.overwrite,
            include_financial=request.include_financial,
            credit_only=request.credit_only
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": result["message"],
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Account enrichment failed: {result.get('message', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enriching account: {str(e)}"
        )


@app.post("/enrich/contact")
async def enrich_contact(
    request: ContactEnrichmentRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    👤 Enrich a Salesforce contact with personalized outreach data

    **Authentication Required:** Include `X-API-Key` header

    **What it enriches:**
    - Personalized rapport summaries (4 variations)
    - Local sports teams and personal interests
    - Role description and work experience
    - Energy project history
    - Why their role is relevant to Metrus Energy
    - Custom email campaign subject lines (4 variations)
    - LinkedIn profile data (if include_linkedin is True)

    **Request format:**
    ```json
    {
        "contact_id": "003VR00000YLIzRYAX",
        "overwrite": false,        // Skip if already enriched
        "include_linkedin": true   // Scrape LinkedIn profile
    }
    ```

    **Headers:**
    ```
    X-API-Key: your-api-key
    ```

    **Use Case:** Personalize outreach to decision-makers at healthcare facilities.
    """
    try:
        result = await enrichment_service.enrich_contact(
            contact_id=request.contact_id,
            overwrite=request.overwrite,
            include_linkedin=request.include_linkedin
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": result["message"],
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Contact enrichment failed: {result.get('message', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enriching contact: {str(e)}"
        )


########################################
# PENDING SALESFORCE UPDATES
########################################
# Approval workflow for Salesforce updates from enrichment

@app.get("/pending-updates")
async def get_pending_updates(
    record_type: Optional[str] = None,
    limit: int = 100,
    dashboard_session: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    📋 Get pending Salesforce updates awaiting approval

    **Authentication Required:** Session cookie from /dashboard/login

    **Parameters:**
    - `record_type`: Filter by "Account" or "Contact" (optional)
    - `limit`: Maximum number of updates to return (default: 100)

    **Returns:**
    - List of pending updates with field details
    - Each update shows: record info, fields to update, enrichment type

    **Use Case:** Dashboard displays pending updates for user review
    """
    # Check authentication
    if not check_dashboard_session(dashboard_session):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        from app.services.pending_updates import PendingUpdatesService
        from app.models import RecordType, UpdateStatus

        # Ensure Salesforce is connected
        if not salesforce_service._authenticated:
            await salesforce_service.connect()

        # Create pending updates service
        pending_service = PendingUpdatesService(db, salesforce_service.sf)

        # Filter by record type if specified
        filter_type = None
        if record_type:
            if record_type.lower() == "account":
                filter_type = RecordType.ACCOUNT
            elif record_type.lower() == "contact":
                filter_type = RecordType.CONTACT

        # Get pending updates
        updates = await pending_service.get_pending_updates(
            record_type=filter_type,
            status=UpdateStatus.PENDING,
            limit=limit
        )

        # Convert to JSON-serializable format
        updates_data = []
        for update in updates:
            updates_data.append({
                "id": update.id,
                "created_at": update.created_at.isoformat(),
                "record_type": update.record_type.value,
                "record_id": update.record_id,
                "record_name": update.record_name,
                "field_updates": update.field_updates,
                "enrichment_type": update.enrichment_type,
                "status": update.status.value
            })

        return {
            "status": "success",
            "count": len(updates_data),
            "updates": updates_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving pending updates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pending updates: {str(e)}"
        )


@app.post("/pending-updates/{update_id}/approve")
async def approve_pending_update(
    update_id: int,
    dashboard_session: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Approve and execute a pending Salesforce update

    **Authentication Required:** Session cookie from /dashboard/login

    **Parameters:**
    - `update_id`: ID of the pending update to approve

    **Returns:**
    - Success/failure status
    - Details of the approved update

    **What happens:**
    1. Validates update exists and is pending
    2. Executes the Salesforce update
    3. Marks update as approved in database
    4. Returns confirmation

    **Use Case:** User clicks green checkmark on pending update
    """
    # Check authentication
    if not check_dashboard_session(dashboard_session):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        from app.services.pending_updates import PendingUpdatesService

        # Ensure Salesforce is connected
        if not salesforce_service._authenticated:
            await salesforce_service.connect()

        # Create pending updates service
        pending_service = PendingUpdatesService(db, salesforce_service.sf)

        # Approve the update
        success = await pending_service.approve_update(
            update_id=update_id,
            approved_by="dashboard_user"  # TODO: Track actual user
        )

        if success:
            return {
                "status": "success",
                "message": f"Update {update_id} approved and applied to Salesforce",
                "update_id": update_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to approve update {update_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error approving update {update_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error approving update: {str(e)}"
        )


@app.post("/pending-updates/approve-all")
async def approve_all_pending_updates(
    record_type: Optional[str] = None,
    dashboard_session: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Approve and execute ALL pending Salesforce updates

    **Authentication Required:** Session cookie from /dashboard/login

    **Parameters:**
    - `record_type`: Filter by "Account" or "Contact" (optional)

    **Returns:**
    - Counts of successful and failed approvals
    - Total number of updates processed

    **What happens:**
    1. Retrieves all pending updates (filtered by type if specified)
    2. Executes each Salesforce update
    3. Marks each as approved in database
    4. Returns summary statistics

    **Use Case:** User clicks "Update All" button for bulk approval
    """
    # Check authentication
    if not check_dashboard_session(dashboard_session):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        from app.services.pending_updates import PendingUpdatesService
        from app.models import RecordType

        # Ensure Salesforce is connected
        if not salesforce_service._authenticated:
            await salesforce_service.connect()

        # Create pending updates service
        pending_service = PendingUpdatesService(db, salesforce_service.sf)

        # Filter by record type if specified
        filter_type = None
        if record_type:
            if record_type.lower() == "account":
                filter_type = RecordType.ACCOUNT
            elif record_type.lower() == "contact":
                filter_type = RecordType.CONTACT

        # Approve all pending updates
        result = await pending_service.approve_all_pending(
            record_type=filter_type,
            approved_by="dashboard_user"  # TODO: Track actual user
        )

        return {
            "status": "success",
            "message": f"Processed {result['total']} updates",
            "successful": result['success'],
            "failed": result['failed'],
            "total": result['total'],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error approving all updates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error approving all updates: {str(e)}"
        )


@app.post("/pending-updates/{update_id}/reject")
async def reject_pending_update(
    update_id: int,
    dashboard_session: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    ❌ Reject a pending Salesforce update

    **Authentication Required:** Session cookie from /dashboard/login

    **Parameters:**
    - `update_id`: ID of the pending update to reject

    **Returns:**
    - Success/failure status
    - Details of the rejected update

    **What happens:**
    1. Validates update exists and is pending
    2. Marks update as rejected (NO Salesforce update)
    3. Returns confirmation

    **Use Case:** User rejects a pending update (red X button)
    """
    # Check authentication
    if not check_dashboard_session(dashboard_session):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        from app.services.pending_updates import PendingUpdatesService

        # Create pending updates service (no SF connection needed for rejection)
        pending_service = PendingUpdatesService(db, None)

        # Reject the update
        success = await pending_service.reject_update(update_id)

        if success:
            return {
                "status": "success",
                "message": f"Update {update_id} rejected",
                "update_id": update_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to reject update {update_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error rejecting update {update_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error rejecting update: {str(e)}"
        )


@app.get("/debug/environment")
async def debug_environment():
    """
    🐛 Debug endpoint to check environment variables

    **Use Case:** Railway deployment troubleshooting

    Returns boolean flags for whether each required environment variable is set,
    plus total count of all environment variables.

    **Does NOT** return actual credential values (security).
    """
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


########################################
# DASHBOARD AUTHENTICATION
########################################
# Unified authentication system for all web dashboards

@app.post("/dashboard/auth")
async def authenticate_dashboard(password: str):
    """
    🔐 Authenticate for dashboard access

    **Parameters:**
    - password: The dashboard password (set in DASHBOARD_PASSWORD env var)

    **Returns:**
    - Session token cookie that expires in 24 hours
    """
    if verify_dashboard_password(password):
        token = create_session_token()
        expiry = datetime.utcnow() + timedelta(hours=24)
        active_sessions[token] = expiry

        response = Response(content='{"status":"authenticated"}', media_type="application/json")
        response.set_cookie(
            key="dashboard_session",
            value=token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="strict"
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid password")


@app.get("/dashboard/login", response_class=HTMLResponse)
async def dashboard_login():
    """
    🔐 Dashboard login page

    **Purpose:** Login form for accessing all web dashboards
    """
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metrus Energy - Dashboard Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        .login-container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 420px;
            width: 100%;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo img {
            width: 80px;
            height: 80px;
            margin-bottom: 16px;
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1));
        }
        .logo h1 {
            font-size: 26px;
            color: #1a365d;
            margin-bottom: 8px;
            font-weight: 700;
        }
        .logo p {
            color: #4a5568;
            font-size: 14px;
            line-height: 1.5;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        input[type="password"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        .error.show {
            display: block;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <img src="https://cdn.prod.website-files.com/6645c7ede4572bff5e1bcfd5/6646259b5e59ac14d6e515e2_metrus-bolt-image-01-664624137b786.webp" alt="Metrus Energy">
            <h1>Metrus Energy</h1>
            <p>Dashboard Login</p>
        </div>

        <div id="error" class="error">Invalid password. Please try again.</div>

        <form id="loginForm" onsubmit="return handleLogin(event)">
            <div class="form-group">
                <label for="password">Password</label>
                <input
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Enter dashboard password"
                    autocomplete="off"
                    required
                    autofocus
                >
            </div>
            <button type="submit" class="btn">Access Dashboard</button>
        </form>

        <div class="footer">
            Metrus Energy &copy; 2025
        </div>
    </div>

    <script>
        async function handleLogin(event) {
            event.preventDefault();

            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('error');
            const submitBtn = event.target.querySelector('button');

            // Show loading state
            submitBtn.textContent = 'Authenticating...';
            submitBtn.disabled = true;
            errorDiv.classList.remove('show');

            try {
                const response = await fetch('/dashboard/auth?password=' + encodeURIComponent(password), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    // Redirect to main dashboard
                    window.location.href = '/dashboard';
                } else {
                    // Show error
                    errorDiv.classList.add('show');
                    submitBtn.textContent = 'Access Dashboard';
                    submitBtn.disabled = false;
                    document.getElementById('password').value = '';
                    document.getElementById('password').focus();
                }
            } catch (error) {
                errorDiv.textContent = 'Connection error. Please try again.';
                errorDiv.classList.add('show');
                submitBtn.textContent = 'Access Dashboard';
                submitBtn.disabled = false;
            }

            return false;
        }
    </script>
</body>
</html>
    """)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(dashboard_session: Optional[str] = Cookie(None)):
    """
    🏠 Main Dashboard - Landing page with links to all tools

    **Features:**
    - System status overview
    - Links to all dashboards
    - Salesforce connection status
    - Quick access to enrichment and logs

    **Authentication Required:** Session cookie from /dashboard/login
    """
    # Check authentication and redirect if needed
    if not check_dashboard_session(dashboard_session):
        return RedirectResponse(url="/dashboard/login", status_code=302)

    try:
        with open("app/templates/dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Dashboard template not found"
        )


########################################
# ENRICHMENT DASHBOARD
########################################
# Web UI for manual enrichment operations

@app.get("/enrich", response_class=HTMLResponse)
async def enrichment_dashboard(dashboard_session: Optional[str] = Cookie(None)):
    """
    🎯 Enrichment Dashboard - Manual UI for enriching Salesforce records

    **Features:**
    - Paste Salesforce Account/Contact URLs
    - Automatic ID extraction from URLs
    - Configure enrichment options
    - Real-time status updates

    **Authentication Required:** Session cookie from /dashboard/login
    **Access:** Navigate to /enrich in your browser (after login)
    """
    # Check authentication and redirect if needed
    if not check_dashboard_session(dashboard_session):
        return RedirectResponse(url="/dashboard/login", status_code=302)

    try:
        with open("app/templates/enrichment.html", "r") as f:
            html_content = f.read()
            # Inject the API key from environment into the HTML
            api_key = os.getenv("API_KEY", "dev-key-change-in-production")
            html_content = html_content.replace(
                "'X-API-Key': 'dev-key-change-in-production'",
                f"'X-API-Key': '{api_key}'"
            )
            return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Enrichment dashboard template not found"
        )


########################################
# API LOGGING ENDPOINTS
########################################
# These endpoints provide a password-protected web UI for viewing API request/response logs
# stored in PostgreSQL database.

@app.get("/logs/view", response_class=HTMLResponse)
async def view_logs(dashboard_session: Optional[str] = Cookie(None)):
    """
    📊 Password-protected web UI for viewing API request/response logs

    **Features:**
    - Real-time log monitoring with auto-refresh
    - Expandable rows to see full request/response JSON
    - Statistics: total requests, avg response time, success rate
    - Password protected with session-based authentication

    **Authentication Required:** Session cookie from /dashboard/login
    **Access:** Navigate to /logs/view in your browser (after login)
    """
    # Check authentication and redirect if needed
    if not check_dashboard_session(dashboard_session):
        return RedirectResponse(url="/dashboard/login", status_code=302)

    try:
        with open("app/templates/logs.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Logs template not found"
        )


@app.get("/logs/data")
async def get_logs_data(
    limit: int = 100,
    dashboard_session: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    📊 Get API logs data in JSON format (password protected)

    **Parameters:**
    - `limit`: Maximum number of logs to return (default: 100)

    **Returns:**
    - List of log entries with request/response details
    - Statistics: total count, average duration, success rate

    **Authentication Required:** Session cookie from /dashboard/login

    **Used by:** /logs/view frontend for dynamic log display
    """
    # Check authentication
    if not check_dashboard_session(dashboard_session):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    try:
        # Get logs ordered by most recent first
        query = select(APILog).order_by(APILog.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()

        # Calculate statistics
        total_query = select(func.count(APILog.id))
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()

        avg_duration_query = select(func.avg(APILog.duration_ms))
        avg_duration_result = await db.execute(avg_duration_query)
        avg_duration = avg_duration_result.scalar()

        success_query = select(func.count(APILog.id)).where(
            APILog.status_code >= 200,
            APILog.status_code < 300
        )
        success_result = await db.execute(success_query)
        success_count = success_result.scalar()

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        # Convert logs to dict
        logs_data = [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "method": log.method,
                "endpoint": log.endpoint,
                "request_body": log.request_body,
                "response_body": log.response_body,
                "status_code": log.status_code,
                "duration_ms": log.duration_ms,
                "client_ip": log.client_ip,
                "user_agent": log.user_agent
            }
            for log in logs
        ]

        return {
            "logs": logs_data,
            "stats": {
                "total_count": total_count,
                "avg_duration": avg_duration,
                "success_rate": success_rate,
                "displayed_count": len(logs_data)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching logs: {str(e)}"
        )