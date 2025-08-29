"""
Application configuration settings using Pydantic Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Metrus Account Enrichment System"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-change-in-production"
    
    # Database
    database_url: Optional[str] = None
    
    # Redis
    redis_url: Optional[str] = "redis://localhost:6379/0"
    
    # Salesforce
    salesforce_domain: Optional[str] = None
    salesforce_client_id: Optional[str] = None
    salesforce_client_secret: Optional[str] = None
    salesforce_username: Optional[str] = None
    salesforce_password: Optional[str] = None
    salesforce_security_token: Optional[str] = None
    
    # External APIs
    apify_api_token: Optional[str] = None
    hunter_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    openai_api_key: Optional[str] = None
    moody_api_key: Optional[str] = None
    
    # Rate Limits and Budgets
    max_concurrent_jobs: int = 5
    daily_api_budget: float = 100.00
    max_accounts_per_day: int = 100
    max_prospects_per_account: int = 10
    apify_daily_limit: int = 100
    hunter_daily_limit: int = 500
    openai_daily_limit: int = 1000000
    
    @validator("database_url", pre=True)
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if v:
            return v
        # Default to PostgreSQL if not provided
        return "postgresql+asyncpg://postgres:password@localhost:5432/metrus_enrichment"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
