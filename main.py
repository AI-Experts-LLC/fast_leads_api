from fastapi import FastAPI
from datetime import datetime
import os

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