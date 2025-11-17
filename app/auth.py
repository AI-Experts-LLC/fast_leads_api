"""
Authentication module for FastAPI

Provides two types of authentication:
1. API Key authentication (X-API-Key header) for programmatic access
2. Session-based authentication (cookies) for web dashboard access
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Cookie, status
from fastapi.security import APIKeyHeader

# API Key header scheme
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Session storage (in-memory, replace with Redis in production)
active_sessions = {}


def get_api_key() -> str:
    """Get the API key from environment variables."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        # Fallback for development - use a default key if not set
        api_key = os.getenv("METRUS_API_KEY", "dev-key-change-in-production")
    return api_key


def get_dashboard_password() -> str:
    """Get the dashboard password from environment variables."""
    return os.getenv("DASHBOARD_PASSWORD", os.getenv("LOGS_PASSWORD", "changeme"))


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


def verify_dashboard_password(password: str) -> bool:
    """Verify password against environment variable."""
    correct_password = get_dashboard_password()
    return password == correct_password


def create_session_token() -> str:
    """Create a secure random session token."""
    return secrets.token_urlsafe(32)


def verify_session_token(token: Optional[str]) -> bool:
    """
    Verify session token is valid and not expired.

    Args:
        token: Session token from cookie

    Returns:
        True if token is valid and not expired, False otherwise
    """
    if not token or token not in active_sessions:
        return False

    expiry = active_sessions[token]
    if datetime.utcnow() > expiry:
        del active_sessions[token]
        return False

    return True


async def verify_dashboard_session(dashboard_session: Optional[str] = Cookie(None)) -> str:
    """
    Verify dashboard session from cookie.

    Args:
        dashboard_session: Session token from cookie

    Raises:
        HTTPException: If session is invalid or expired

    Returns:
        The validated session token
    """
    if not verify_session_token(dashboard_session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please login at /dashboard/login"
        )

    return dashboard_session
