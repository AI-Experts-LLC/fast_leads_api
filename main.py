"""
Metrus Energy Account Enrichment System
FastAPI application with async Salesforce integration and background processing
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.core.config import get_settings
from app.models.database import init_db
from app.api.webhooks import router as webhook_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Metrus Account Enrichment System")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Metrus Account Enrichment System")


# Create FastAPI app
app = FastAPI(
    title="Metrus Account Enrichment System",
    description="Automated lead enrichment and qualification system for Salesforce accounts",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://metrusenergy.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time and request ID to response headers"""
    start_time = time.time()
    request_id = f"req_{int(time.time() * 1000)}"
    request.state.request_id = request_id
    request.state.timestamp = start_time
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        request_id=getattr(request.state, 'request_id', 'unknown')
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )


# Include routers
app.include_router(webhook_router, prefix="/webhook", tags=["webhooks"])


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Metrus Account Enrichment System",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.app_env,
        "endpoints": {
            "webhook": "/webhook/salesforce-account",
            "job_status": "/webhook/job/{job_id}/status",
            "health": "/webhook/health",
            "docs": "/docs" if settings.debug else "disabled",
            "queue_stats": "/webhook/queue/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "Metrus Account Enrichment System",
        "environment": settings.app_env,
        "timestamp": time.time()
    }