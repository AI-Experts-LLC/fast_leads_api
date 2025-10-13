"""
Simple API Key Authentication for FastAPI

Protects endpoints with a simple API key check via X-API-Key header.
"""

import os
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API Key header scheme
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key() -> str:
    """Get the API key from environment variables."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        # Fallback for development - use a default key if not set
        api_key = os.getenv("METRUS_API_KEY", "dev-key-change-in-production")
    return api_key


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify the API key from the request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Raises:
        HTTPException: If API key is missing or invalid
        
    Returns:
        The validated API key
    """
    expected_key = get_api_key()
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key
