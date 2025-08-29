"""
Main account enrichment pipeline
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import structlog

from app.services.queue import get_queue_service
from app.services.salesforce import get_salesforce_service
from app.models.database import AsyncSessionLocal
from app.models.enrichment import EnrichmentJob, ProspectLead, APIUsageLog
from app.core.config import get_settings

# Healthcare buyer personas mapping
HEALTHCARE_BUYER_PERSONAS = [
    "Director of Facilities",
    "Chief Financial Officer", 
    "Sustainability Manager",
    "Chief Operating Officer",
    "Compliance Manager",
    "Energy Manager",
    "Procurement Manager"
]

logger = structlog.get_logger()
settings = get_settings()


async def process_account_enrichment(account_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Main enrichment pipeline for a single account
    
    Args:
        account_data: Salesforce account data
        job_id: Unique job identifier
        
    Returns:
        Enrichment results
    """
    queue_service = get_queue_service()
    
    try:
        logger.info(
            "Starting account enrichment",
            job_id=job_id,
            account_id=account_data.get("Id"),
            account_name=account_data.get("Name")
        )
        
        # Update job progress
        queue_service.update_job_progress(job_id, 5, "Initializing enrichment pipeline")
        
        # Create enrichment job record
        async with AsyncSessionLocal() as db:
            job_record = EnrichmentJob(
                job_id=job_id,
                salesforce_account_id=account_data.get("Id"),
                status="processing",
                account_data=account_data,
                progress_percentage=5
            )
            db.add(job_record)
            await db.commit()
            await db.refresh(job_record)
        
        # Step 1: Validate and filter account
        queue_service.update_job_progress(job_id, 10, "Validating account data")
        
        if not await validate_account_for_enrichment(account_data):
            logger.warning("Account failed validation", job_id=job_id)
            await update_job_status(job_id, "failed", "Account failed validation criteria")
            return {"success": False, "error": "Account validation failed"}
        
        # Step 2: Credit screening (if enabled)
        queue_service.update_job_progress(job_id, 20, "Performing credit screening")
        
        credit_qualified = True
        if settings.moody_api_key:
            credit_qualified = await perform_credit_screening(account_data, job_id)
        
        if not credit_qualified:
            logger.warning("Account failed credit screening", job_id=job_id)
            await update_job_status(job_id, "completed", "Account disqualified - credit screening")
            return {"success": True, "qualified": False, "reason": "credit_screening"}
        
        # Step 3: Find LinkedIn prospects
        queue_service.update_job_progress(job_id, 30, "Searching for LinkedIn prospects")
        
        linkedin_prospects = await find_linkedin_prospects(account_data, job_id)
        
        if not linkedin_prospects:
            logger.warning("No LinkedIn prospects found", job_id=job_id)
            await update_job_status(job_id, "completed", "No prospects found")
            return {"success": True, "prospects_found": 0}
        
        # Step 4: Enrich prospects with LinkedIn data
        queue_service.update_job_progress(job_id, 50, f"Enriching {len(linkedin_prospects)} prospects")
        
        enriched_prospects = await enrich_prospects_data(linkedin_prospects, job_id)
        
        # Step 5: AI qualification and scoring
        queue_service.update_job_progress(job_id, 70, "AI qualification and persona matching")
        
        qualified_prospects = await qualify_prospects_with_ai(enriched_prospects, account_data, job_id)
        
        # Step 6: Create Salesforce leads
        queue_service.update_job_progress(job_id, 85, "Creating Salesforce leads")
        
        created_leads = await create_salesforce_leads(qualified_prospects, account_data, job_id)
        
        # Step 7: Update job completion
        queue_service.update_job_progress(job_id, 100, "Enrichment completed")
        
        await update_job_status(
            job_id, 
            "completed", 
            f"Successfully created {len(created_leads)} leads",
            prospects_found=len(linkedin_prospects),
            leads_created=len(created_leads),
            enrichment_results={
                "prospects_found": len(linkedin_prospects),
                "prospects_enriched": len(enriched_prospects),
                "prospects_qualified": len(qualified_prospects),
                "leads_created": len(created_leads),
                "success_rate": len(created_leads) / len(linkedin_prospects) if linkedin_prospects else 0
            }
        )
        
        logger.info(
            "Account enrichment completed",
            job_id=job_id,
            prospects_found=len(linkedin_prospects),
            leads_created=len(created_leads)
        )
        
        return {
            "success": True,
            "prospects_found": len(linkedin_prospects),
            "leads_created": len(created_leads),
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error("Enrichment pipeline failed", job_id=job_id, error=str(e))
        await update_job_status(job_id, "failed", str(e))
        raise


async def validate_account_for_enrichment(account_data: Dict[str, Any]) -> bool:
    """
    Validate account meets enrichment criteria
    
    Args:
        account_data: Salesforce account data
        
    Returns:
        True if account should be enriched, False otherwise
    """
    # Check required fields
    if not account_data.get("Name"):
        return False
    
    # Industry filtering (focus on healthcare for now)
    industry = account_data.get("Industry", "").lower()
    hospital_type = account_data.get("Hospital_Type__c")
    
    if not (
        "healthcare" in industry or 
        "hospital" in industry or
        hospital_type or
        "hospital" in account_data.get("Name", "").lower()
    ):
        return False
    
    # Revenue filtering (optional)
    revenue = account_data.get("AnnualRevenue")
    if revenue and revenue < 10000000:  # $10M minimum
        return False
    
    # Employee count filtering (optional)
    employees = account_data.get("NumberOfEmployees")
    if employees and employees < 100:  # 100+ employees
        return False
    
    return True


async def perform_credit_screening(account_data: Dict[str, Any], job_id: str) -> bool:
    """
    Perform credit screening using Moody's or similar service
    
    Args:
        account_data: Account information
        job_id: Job identifier for logging
        
    Returns:
        True if credit qualified, False otherwise
    """
    # Placeholder for credit screening logic
    # In a real implementation, this would call Moody's API
    
    company_name = account_data.get("Name")
    
    # Log API usage (placeholder)
    await log_api_usage(
        job_id=job_id,
        api_service="moody",
        endpoint="/credit-rating",
        cost=1.0,
        success=True,
        response_data={"credit_rating": "A", "qualified": True}
    )
    
    # For now, assume all accounts are credit qualified
    # In production, implement actual credit screening logic
    logger.info("Credit screening completed", job_id=job_id, company=company_name, qualified=True)
    
    return True


async def find_linkedin_prospects(account_data: Dict[str, Any], job_id: str) -> List[Dict[str, Any]]:
    """
    Find LinkedIn prospects using Google Search API
    
    Args:
        account_data: Account information
        job_id: Job identifier
        
    Returns:
        List of LinkedIn profile URLs and basic info
    """
    # Placeholder implementation
    # In production, this would use Google Search API to find LinkedIn profiles
    
    company_name = account_data.get("Name")
    
    # Define target personas based on hospital buyer personas
    target_personas = [
        "Director of Facilities",
        "CFO", 
        "Chief Financial Officer",
        "Sustainability Manager",
        "Energy Manager",
        "Chief Operating Officer",
        "Director of Engineering",
        "Facilities Manager"
    ]
    
    # Mock LinkedIn prospects for testing
    mock_prospects = [
        {
            "linkedin_url": f"https://linkedin.com/in/mock-cfo-{company_name.replace(' ', '').lower()}",
            "name": f"John Smith",
            "title": "CFO",
            "company": company_name,
            "persona_type": "CFO"
        },
        {
            "linkedin_url": f"https://linkedin.com/in/mock-facilities-{company_name.replace(' ', '').lower()}",
            "name": f"Sarah Johnson", 
            "title": "Director of Facilities",
            "company": company_name,
            "persona_type": "Director of Facilities"
        },
        {
            "linkedin_url": f"https://linkedin.com/in/mock-sustainability-{company_name.replace(' ', '').lower()}",
            "name": f"Mike Davis",
            "title": "Sustainability Manager", 
            "company": company_name,
            "persona_type": "Sustainability Manager"
        }
    ]
    
    # Log API usage (placeholder)
    await log_api_usage(
        job_id=job_id,
        api_service="google_search",
        endpoint="/customsearch/v1",
        cost=0.15,  # 3 searches × $0.05 each
        success=True,
        response_data={"profiles_found": len(mock_prospects)}
    )
    
    logger.info(
        "LinkedIn prospects found",
        job_id=job_id,
        company=company_name,
        prospects_found=len(mock_prospects)
    )
    
    return mock_prospects


async def enrich_prospects_data(prospects: List[Dict[str, Any]], job_id: str) -> List[Dict[str, Any]]:
    """
    Enrich prospects with LinkedIn data and email discovery
    
    Args:
        prospects: List of prospect information
        job_id: Job identifier
        
    Returns:
        List of enriched prospect data
    """
    enriched_prospects = []
    
    for prospect in prospects:
        try:
            # Mock LinkedIn data enrichment (would use Apify in production)
            linkedin_data = {
                "fullName": prospect.get("name"),
                "headline": prospect.get("title"),
                "company": prospect.get("company"),
                "location": "New York, NY",
                "summary": f"Experienced {prospect.get('title')} with expertise in healthcare operations",
                "experience": [
                    {
                        "title": prospect.get("title"),
                        "company": prospect.get("company"),
                        "duration": "2+ years"
                    }
                ],
                "skills": ["Healthcare Operations", "Energy Management", "Cost Optimization"]
            }
            
            # Mock email discovery (would use Hunter.io in production)
            company_domain = f"{prospect.get('company', '').replace(' ', '').lower()}.com"
            first_name = prospect.get("name", "").split(" ")[0].lower()
            last_name = prospect.get("name", "").split(" ")[-1].lower()
            email = f"{first_name}.{last_name}@{company_domain}"
            
            enriched_prospect = {
                **prospect,
                "first_name": first_name.title(),
                "last_name": last_name.title(),
                "full_name": prospect.get("name"),
                "email": email,
                "email_verification_status": "verified",
                "phone": "+1-555-123-4567",  # Mock phone
                "location": "New York, NY",
                "linkedin_data": linkedin_data,
                "enrichment_job_id": job_id
            }
            
            enriched_prospects.append(enriched_prospect)
            
        except Exception as e:
            logger.error("Failed to enrich prospect", job_id=job_id, prospect=prospect, error=str(e))
            continue
    
    # Log API usage
    await log_api_usage(
        job_id=job_id,
        api_service="apify",
        endpoint="/actor/linkedin-scraper",
        cost=len(prospects) * 0.15,  # $0.15 per profile
        success=True,
        response_data={"profiles_enriched": len(enriched_prospects)}
    )
    
    await log_api_usage(
        job_id=job_id,
        api_service="hunter",
        endpoint="/domain-search",
        cost=len(prospects) * 0.10,  # $0.10 per email lookup
        success=True,
        response_data={"emails_found": len(enriched_prospects)}
    )
    
    logger.info(
        "Prospects enriched",
        job_id=job_id,
        input_prospects=len(prospects),
        enriched_prospects=len(enriched_prospects)
    )
    
    return enriched_prospects


async def qualify_prospects_with_ai(
    prospects: List[Dict[str, Any]], 
    account_data: Dict[str, Any], 
    job_id: str
) -> List[Dict[str, Any]]:
    """
    Use AI to qualify prospects and generate personalized messages
    
    Args:
        prospects: Enriched prospect data
        account_data: Account context
        job_id: Job identifier
        
    Returns:
        List of qualified prospects with AI-generated content
    """
    qualified_prospects = []
    
    for prospect in prospects:
        try:
            # Mock AI qualification (would use OpenAI in production)
            persona_type = prospect.get("persona_type", "Unknown")
            
            # Persona-specific scoring
            persona_scores = {
                "CFO": 85,
                "Director of Facilities": 90,
                "Sustainability Manager": 75,
                "Energy Manager": 80,
                "Chief Operating Officer": 85
            }
            
            qualification_score = persona_scores.get(persona_type, 70)
            persona_match_score = 88 if persona_type in persona_scores else 60
            
            # Generate pain points based on persona
            pain_points_map = {
                "CFO": ["Capital Constraints", "Cash Flow Issues", "ROI Requirements"],
                "Director of Facilities": ["Deferred Maintenance", "Infrastructure Costs", "Operational Efficiency"],
                "Sustainability Manager": ["Energy Efficiency", "Sustainability Goals", "Regulatory Compliance"],
                "Energy Manager": ["Energy Efficiency", "Cost Optimization", "Infrastructure Costs"],
                "Chief Operating Officer": ["Operational Efficiency", "Cost Optimization", "Regulatory Compliance"]
            }
            
            pain_points = pain_points_map.get(persona_type, ["Cost Optimization"])
            
            # Generate personalized message
            ai_message = generate_persona_message(prospect, persona_type, pain_points)
            
            # Personalization elements
            personalization_elements = [
                f"{persona_type} role focus",
                "Healthcare industry context",
                "Company-specific messaging"
            ]
            
            qualified_prospect = {
                **prospect,
                "qualification_score": qualification_score,
                "persona_match_score": persona_match_score,
                "pain_points": pain_points,
                "ai_generated_message": ai_message,
                "personalization_elements": personalization_elements
            }
            
            # Only include prospects with score above threshold
            if qualification_score >= 70:
                qualified_prospects.append(qualified_prospect)
            
        except Exception as e:
            logger.error("Failed to qualify prospect", job_id=job_id, prospect=prospect, error=str(e))
            continue
    
    # Log AI API usage
    await log_api_usage(
        job_id=job_id,
        api_service="openai",
        endpoint="/chat/completions",
        cost=len(prospects) * 0.05,  # $0.05 per analysis
        success=True,
        response_data={"prospects_qualified": len(qualified_prospects)}
    )
    
    logger.info(
        "Prospects qualified with AI",
        job_id=job_id,
        input_prospects=len(prospects),
        qualified_prospects=len(qualified_prospects)
    )
    
    return qualified_prospects


def generate_persona_message(prospect: Dict[str, Any], persona_type: str, pain_points: List[str]) -> str:
    """Generate personalized message based on persona type"""
    
    name = prospect.get("first_name", "")
    company = prospect.get("company", "")
    title = prospect.get("title", "")
    
    if persona_type == "CFO":
        return f"Hi {name}, As {title} at {company}, you understand the impact of operational costs on the bottom line. Healthcare facilities face unique energy challenges, and I specialize in helping organizations like yours reduce energy costs through off-balance sheet financing solutions. Would you be interested in a brief conversation about how we might help optimize your energy expenses while improving cash flow?"
    
    elif persona_type == "Director of Facilities":
        return f"Hi {name}, In your role as {title}, you likely deal with deferred maintenance and infrastructure challenges at {company}. I help healthcare facilities upgrade their central utility plants and energy systems without upfront capital investment. Our solutions address infrastructure needs while delivering immediate operational savings. Would you be open to discussing how this might benefit {company}?"
    
    elif persona_type == "Sustainability Manager":
        return f"Hi {name}, I noticed your focus on sustainability at {company}. Healthcare facilities have tremendous opportunities for emissions reduction and energy efficiency improvements. I specialize in helping organizations like yours achieve sustainability goals while reducing costs through innovative financing. Would you be interested in learning how we might support {company}'s environmental initiatives?"
    
    else:
        return f"Hi {name}, I hope this message finds you well. As {title} at {company}, you're likely always looking for ways to improve efficiency and reduce costs. I help healthcare organizations optimize their energy infrastructure and achieve significant operational savings. Would you be interested in a brief conversation about how we might help {company}?"


async def create_salesforce_leads(
    prospects: List[Dict[str, Any]], 
    account_data: Dict[str, Any], 
    job_id: str
) -> List[str]:
    """
    Create Lead records in Salesforce
    
    Args:
        prospects: Qualified prospect data
        account_data: Source account data
        job_id: Job identifier
        
    Returns:
        List of created Lead IDs
    """
    created_leads = []
    
    try:
        salesforce_service = await get_salesforce_service()
        
        async with salesforce_service:
            # Prepare lead data for bulk creation
            leads_data = []
            
            for prospect in prospects:
                lead_data = salesforce_service.map_prospect_to_lead(prospect, account_data)
                leads_data.append(lead_data)
            
            # Create leads in bulk
            if leads_data:
                results = await salesforce_service.create_leads_bulk(leads_data)
                
                # Process results and update database
                async with AsyncSessionLocal() as db:
                    for i, result in enumerate(results):
                        if result["success"]:
                            lead_id = result["id"]
                            created_leads.append(lead_id)
                            
                            # Create prospect lead record
                            prospect_lead = ProspectLead(
                                enrichment_job_id=None,  # Will be linked later
                                first_name=prospects[i].get("first_name"),
                                last_name=prospects[i].get("last_name"),
                                full_name=prospects[i].get("full_name"),
                                title=prospects[i].get("title"),
                                company=prospects[i].get("company"),
                                email=prospects[i].get("email"),
                                phone=prospects[i].get("phone"),
                                location=prospects[i].get("location"),
                                linkedin_url=prospects[i].get("linkedin_url"),
                                linkedin_data=prospects[i].get("linkedin_data"),
                                persona_type=prospects[i].get("persona_type"),
                                persona_match_score=prospects[i].get("persona_match_score"),
                                qualification_score=prospects[i].get("qualification_score"),
                                pain_points=prospects[i].get("pain_points"),
                                ai_generated_message=prospects[i].get("ai_generated_message"),
                                salesforce_lead_id=lead_id,
                                lead_created=True
                            )
                            
                            db.add(prospect_lead)
                        else:
                            logger.error(
                                "Failed to create Salesforce lead",
                                job_id=job_id,
                                prospect=prospects[i],
                                error=result.get("error")
                            )
                    
                    await db.commit()
        
        logger.info(
            "Salesforce leads created",
            job_id=job_id,
            total_prospects=len(prospects),
            leads_created=len(created_leads)
        )
        
    except Exception as e:
        logger.error("Failed to create Salesforce leads", job_id=job_id, error=str(e))
        raise
    
    return created_leads


async def update_job_status(
    job_id: str, 
    status: str, 
    message: str = None,
    prospects_found: int = 0,
    leads_created: int = 0,
    enrichment_results: Dict[str, Any] = None
):
    """Update enrichment job status in database"""
    try:
        async with AsyncSessionLocal() as db:
            # Find job record
            result = await db.execute(
                "SELECT * FROM enrichment_jobs WHERE job_id = :job_id",
                {"job_id": job_id}
            )
            job = result.fetchone()
            
            if job:
                # Update job record
                update_data = {
                    "status": status,
                    "updated_at": datetime.utcnow(),
                    "prospects_found": prospects_found,
                    "leads_created": leads_created
                }
                
                if status in ["completed", "failed"]:
                    update_data["completed_at"] = datetime.utcnow()
                
                if enrichment_results:
                    update_data["enrichment_results"] = enrichment_results
                
                if message:
                    update_data["error_message"] = message
                
                await db.execute(
                    """UPDATE enrichment_jobs 
                       SET status = :status, updated_at = :updated_at,
                           prospects_found = :prospects_found, leads_created = :leads_created,
                           completed_at = :completed_at, enrichment_results = :enrichment_results,
                           error_message = :error_message
                       WHERE job_id = :job_id""",
                    {**update_data, "job_id": job_id}
                )
                
                await db.commit()
                
    except Exception as e:
        logger.error("Failed to update job status", job_id=job_id, error=str(e))


async def log_api_usage(
    job_id: str,
    api_service: str,
    endpoint: str,
    cost: float,
    success: bool,
    response_data: Dict[str, Any] = None,
    error_message: str = None
):
    """Log API usage for cost tracking"""
    try:
        async with AsyncSessionLocal() as db:
            api_log = APIUsageLog(
                enrichment_job_id=None,  # Will be linked later
                api_service=api_service,
                endpoint=endpoint,
                method="POST",
                request_data={},
                response_data=response_data or {},
                response_time_ms=100,  # Mock response time
                success=success,
                error_message=error_message,
                cost_amount=cost,
                cost_currency="USD"
            )
            
            db.add(api_log)
            await db.commit()
            
    except Exception as e:
        logger.error("Failed to log API usage", job_id=job_id, error=str(e))


def determine_buyer_personas(account_data: Dict[str, Any]) -> List[str]:
    """
    Determine relevant buyer personas based on account data
    
    Args:
        account_data: Salesforce account information
        
    Returns:
        List of relevant buyer persona titles
    """
    personas = []
    
    # Base personas for healthcare
    if account_data.get("Industry") == "Healthcare":
        personas.extend([
            "Director of Facilities",
            "Chief Financial Officer",
            "Sustainability Manager"
        ])
        
        # Add based on size
        revenue = account_data.get("AnnualRevenue", 0)
        employees = account_data.get("NumberOfEmployees", 0)
        
        if revenue and revenue > 100000000:  # $100M+
            personas.extend([
                "Chief Operating Officer",
                "Energy Manager"
            ])
        
        if employees and employees > 500:
            personas.extend([
                "Compliance Manager",
                "Procurement Manager"
            ])
    
    # Remove duplicates and return
    return list(set(personas))


class EnrichmentPipeline:
    """Main enrichment pipeline orchestrator"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def enrich_account(self, account_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Run the complete enrichment pipeline for an account"""
        return await process_account_enrichment(account_data, job_id)
    
    async def validate_account(self, account_data: Dict[str, Any]) -> bool:
        """Validate if account is suitable for enrichment"""
        return await validate_account_for_enrichment(account_data)
    
    def get_buyer_personas(self, account_data: Dict[str, Any]) -> List[str]:
        """Get buyer personas for account"""
        return determine_buyer_personas(account_data)
