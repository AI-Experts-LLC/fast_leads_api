"""
Middleware for logging API requests and responses to PostgreSQL.
"""
import json
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import APILog

class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses to the database.
    """

    # Endpoints to exclude from logging (to avoid infinite loops and clutter)
    EXCLUDED_ENDPOINTS = {
        "/logs",
        "/logs/view",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    }

    async def dispatch(self, request: Request, call_next):
        # Skip logging for excluded endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in self.EXCLUDED_ENDPOINTS):
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Capture request details
        method = request.method
        endpoint = request.url.path
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Capture request body
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = body_bytes.decode("utf-8")
                    # Need to rebuild request with body for downstream processing
                    async def receive():
                        return {"type": "http.request", "body": body_bytes}
                    request._receive = receive
            except Exception as e:
                request_body = f"Error reading request body: {str(e)}"

        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code

            # Capture response body
            response_body = None
            if isinstance(response, StreamingResponse):
                # Handle streaming responses
                response_body_bytes = b""
                async for chunk in response.body_iterator:
                    response_body_bytes += chunk

                try:
                    response_body = response_body_bytes.decode("utf-8")
                except:
                    response_body = f"<binary data, {len(response_body_bytes)} bytes>"

                # Recreate response with captured body
                response = Response(
                    content=response_body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

        except Exception as e:
            status_code = 500
            response_body = json.dumps({"error": str(e)})
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log to database asynchronously
            try:
                await self._log_to_database(
                    method=method,
                    endpoint=endpoint,
                    request_body=request_body,
                    response_body=response_body,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    user_agent=user_agent
                )
            except Exception as log_error:
                # Don't fail the request if logging fails
                print(f"Failed to log API request: {log_error}")

        return response

    async def _log_to_database(
        self,
        method: str,
        endpoint: str,
        request_body: str,
        response_body: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
        user_agent: str
    ):
        """
        Save API log entry to database.
        """
        async with AsyncSessionLocal() as session:
            try:
                log_entry = APILog(
                    method=method,
                    endpoint=endpoint,
                    request_body=request_body,
                    response_body=response_body,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    user_agent=user_agent
                )
                session.add(log_entry)
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Database logging error: {e}")
                raise
