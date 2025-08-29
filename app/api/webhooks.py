"""
Webhook endpoints for Salesforce integration
"""
import json
import hashlib
import hmac
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

from app.services.queue import get_queue_service, QueueService
from app.services.salesforce import get_salesforce_service, SalesforceService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = structlog.get_logger()


class SalesforceAccountPayload(BaseModel):
    """Salesforce Account webhook payload"""
    Id: str = Field(..., description="Salesforce Account ID")
    Name: str = Field(..., description="Account Name")
    Industry: str = Field(None, description="Industry")
    AnnualRevenue: float = Field(None, description="Annual Revenue")
    NumberOfEmployees: int = Field(None, description="Number of Employees")
    BillingStreet: str = Field(None, description="Billing Address Street")
    BillingCity: str = Field(None, description="Billing City")
    BillingState: str = Field(None, description="Billing State")
    BillingPostalCode: str = Field(None, description="Billing Postal Code")
    BillingCountry: str = Field(None, description="Billing Country")
    Hospital_Type__c: str = Field(None, description="Hospital Type")
    Hospital_Bed_Count__c: int = Field(None, description="Hospital Bed Count")
    Enrichment_Status__c: str = Field(None, description="Enrichment Status")
    
    class Config:
        extra = "allow"  # Allow additional fields from Salesforce


class WebhookResponse(BaseModel):
    """Standard webhook response"""
    success: bool
    job_id: str = None
    message: str = None
    timestamp: str = None


def verify_salesforce_signature(request: Request, payload: bytes) -> bool:
    """
    Verify Salesforce webhook signature
    
    Args:
        request: FastAPI request object
        payload: Raw request payload
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Skip signature verification in development
    if settings.app_env == "development":
        return True
    
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        settings.secret_key.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)


@router.post("/salesforce-account", response_model=WebhookResponse)
async def salesforce_account_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    queue_service: QueueService = Depends(get_queue_service)
) -> WebhookResponse:
    """
    Receive Salesforce account data for enrichment processing
    
    This endpoint receives account data from Salesforce outbound messages
    and queues them for background processing.
    """
    try:
        # Get raw payload for signature verification
        payload = await request.body()
        
        # Verify webhook signature
        if not verify_salesforce_signature(request, payload):
            logger.warning("Invalid webhook signature", headers=dict(request.headers))
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON payload
        try:
            data = json.loads(payload.decode())
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON payload", error=str(e))
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Extract account data from Salesforce outbound message format
        if "notifications" in data:
            # Salesforce outbound message format
            notifications = data["notifications"]
            if not notifications:
                raise HTTPException(status_code=400, detail="No notifications in payload")
            
            account_data = notifications[0]["sObject"]
        else:
            # Direct account data format
            account_data = data
        
        # Validate account data
        try:
            account = SalesforceAccountPayload(**account_data)
        except Exception as e:
            logger.error("Invalid account data", error=str(e), data=account_data)
            raise HTTPException(status_code=400, detail=f"Invalid account data: {e}")
        
        # Determine job priority based on account characteristics
        priority = "normal"
        if account.AnnualRevenue and account.AnnualRevenue > 100000000:  # $100M+
            priority = "high"
        elif account.NumberOfEmployees and account.NumberOfEmployees < 100:
            priority = "low"
        
        # Queue enrichment job
        job_id = queue_service.enqueue_enrichment_job(
            account_data=account.dict(),
            priority=priority
        )
        
        logger.info(
            "Queued account enrichment job",
            job_id=job_id,
            account_id=account.Id,
            account_name=account.Name,
            priority=priority
        )
        
        return WebhookResponse(
            success=True,
            job_id=job_id,
            message=f"Account enrichment queued with priority: {priority}",
            timestamp=str(request.state.timestamp) if hasattr(request.state, 'timestamp') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/job/{job_id}/status")
async def get_job_status(
    job_id: str,
    queue_service: QueueService = Depends(get_queue_service)
) -> Dict[str, Any]:
    """
    Check enrichment job status and progress
    
    Args:
        job_id: Job identifier from webhook response
        
    Returns:
        Current job status, progress, and results if complete
    """
    try:
        status = queue_service.get_job_status(job_id)
        
        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Job not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve job status")


@router.post("/enrich-accounts")
async def enrich_accounts_batch(
    account_ids: List[str],
    priority: str = "normal",
    queue_service: QueueService = Depends(get_queue_service),
    salesforce_service: SalesforceService = Depends(get_salesforce_service)
) -> Dict[str, Any]:
    """
    Manual batch enrichment for multiple accounts
    
    Args:
        account_ids: List of Salesforce Account IDs
        priority: Job priority (high, normal, low)
        
    Returns:
        Batch job information with individual job IDs
    """
    try:
        if not account_ids:
            raise HTTPException(status_code=400, detail="No account IDs provided")
        
        if len(account_ids) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 accounts per batch")
        
        # Fetch account data from Salesforce
        async with salesforce_service:
            job_ids = []
            failed_accounts = []
            
            for account_id in account_ids:
                try:
                    account_data = await salesforce_service.get_account_by_id(account_id)
                    if not account_data:
                        failed_accounts.append({
                            "account_id": account_id,
                            "error": "Account not found"
                        })
                        continue
                    
                    # Queue enrichment job
                    job_id = queue_service.enqueue_enrichment_job(
                        account_data=account_data,
                        priority=priority
                    )
                    
                    job_ids.append({
                        "account_id": account_id,
                        "job_id": job_id,
                        "account_name": account_data.get("Name")
                    })
                    
                except Exception as e:
                    failed_accounts.append({
                        "account_id": account_id,
                        "error": str(e)
                    })
        
        logger.info(
            "Queued batch enrichment jobs",
            total_accounts=len(account_ids),
            successful_jobs=len(job_ids),
            failed_accounts=len(failed_accounts),
            priority=priority
        )
        
        return {
            "success": True,
            "total_accounts": len(account_ids),
            "successful_jobs": len(job_ids),
            "failed_accounts": len(failed_accounts),
            "jobs": job_ids,
            "failures": failed_accounts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Batch enrichment failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch enrichment failed")


@router.get("/health")
async def health_check(
    request: Request,
    queue_service: QueueService = Depends(get_queue_service),
    salesforce_service: SalesforceService = Depends(get_salesforce_service)
) -> Dict[str, Any]:
    """
    System health check with dependency validation
    
    Returns:
        Health status of all system components
    """
    health_status = {
        "status": "healthy",
        "timestamp": str(request.state.timestamp) if hasattr(request.state, 'timestamp') else None,
        "components": {}
    }
    
    # Check Redis/Queue health
    try:
        queue_stats = queue_service.get_queue_stats()
        health_status["components"]["queue"] = {
            "status": "healthy",
            "stats": queue_stats
        }
    except Exception as e:
        health_status["components"]["queue"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Salesforce health
    try:
        sf_health = await salesforce_service.health_check()
        health_status["components"]["salesforce"] = sf_health
        if sf_health["status"] != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["salesforce"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Set overall status
    unhealthy_components = [
        comp for comp in health_status["components"].values()
        if comp["status"] == "unhealthy"
    ]
    
    if len(unhealthy_components) >= 2:
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/queue/stats")
async def get_queue_statistics(
    request: Request,
    queue_service: QueueService = Depends(get_queue_service)
) -> Dict[str, Any]:
    """
    Get detailed queue statistics and worker information
    
    Returns:
        Queue statistics including counts and worker status
    """
    try:
        stats = queue_service.get_queue_stats()
        failed_jobs = queue_service.get_failed_jobs(limit=5)
        
        return {
            "queue_stats": stats,
            "recent_failures": failed_jobs,
            "timestamp": str(request.state.timestamp) if hasattr(request.state, 'timestamp') else None
        }
        
    except Exception as e:
        logger.error("Failed to get queue statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve queue statistics")
