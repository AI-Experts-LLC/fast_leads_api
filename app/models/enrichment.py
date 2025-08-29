"""
Database models for account enrichment system
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.models.database import Base


class EnrichmentJob(Base):
    """Track enrichment job progress and results"""
    __tablename__ = "enrichment_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True)
    salesforce_account_id = Column(String(18), index=True)
    
    # Job status and progress
    status = Column(String(50), default="queued")  # queued, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Input data
    account_data = Column(JSON)
    
    # Results
    prospects_found = Column(Integer, default=0)
    leads_created = Column(Integer, default=0)
    enrichment_results = Column(JSON)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    prospects = relationship("ProspectLead", back_populates="enrichment_job")
    api_usage_logs = relationship("APIUsageLog", back_populates="enrichment_job")


class ProspectLead(Base):
    """Store enriched prospect data before Salesforce creation"""
    __tablename__ = "prospect_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    enrichment_job_id = Column(Integer, ForeignKey("enrichment_jobs.id"))
    
    # Basic prospect info
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))
    title = Column(String(200))
    company = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    location = Column(String(200))
    
    # LinkedIn data
    linkedin_url = Column(String(500))
    linkedin_data = Column(JSON)
    
    # AI analysis
    persona_type = Column(String(100))
    persona_match_score = Column(Float)
    qualification_score = Column(Float)
    pain_points = Column(JSON)
    
    # Generated content
    ai_generated_message = Column(Text)
    personalization_elements = Column(JSON)
    
    # Salesforce integration
    salesforce_lead_id = Column(String(18), nullable=True)
    lead_created = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrichment_job = relationship("EnrichmentJob", back_populates="prospects")


class APIUsageLog(Base):
    """Track API usage and costs"""
    __tablename__ = "api_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    enrichment_job_id = Column(Integer, ForeignKey("enrichment_jobs.id"), nullable=True)
    
    # API details
    api_service = Column(String(50))  # apify, hunter, openai, google, etc.
    endpoint = Column(String(200))
    method = Column(String(10))
    
    # Request/Response
    request_data = Column(JSON)
    response_data = Column(JSON)
    
    # Metrics
    response_time_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
    
    # Cost tracking
    cost_amount = Column(Float, default=0.0)
    cost_currency = Column(String(3), default="USD")
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    enrichment_job = relationship("EnrichmentJob", back_populates="api_usage_logs")


class SystemMetrics(Base):
    """Track system performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_name = Column(String(100))
    metric_value = Column(Float)
    metric_unit = Column(String(50))
    
    # Context
    context = Column(JSON)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow)


class CostTracking(Base):
    """Track daily/monthly API costs"""
    __tablename__ = "cost_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Date and service
    date = Column(DateTime, default=datetime.utcnow)
    api_service = Column(String(50))
    
    # Usage metrics
    requests_count = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Budget tracking
    daily_budget = Column(Float)
    budget_used_percentage = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
