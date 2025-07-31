"""
Deep Research Application - Main FastAPI Entry Point

This module serves as the main entry point for the Deep Research FastAPI application.
It configures the app with middleware, routes, and Azure service integrations.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import research, health, export, convert, sessions, orchestration
from app.api import settings as user_settings
from app.core.config import get_settings
from app.core.azure_config import AzureServiceManager
from app.core.logging_config import configure_logging


# Configure structured logging
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown tasks.
    
    Handles:
    - Azure service initialization
    - Resource cleanup
    - Health checks
    """
    settings = get_settings()
    
    # Startup tasks
    logger.info("Starting Deep Research application", version="1.0.0")
    
    try:
        # Initialize Azure services
        azure_manager = AzureServiceManager(settings)
        await azure_manager.initialize()
        
        # Store in app state for access in routes
        app.state.azure_manager = azure_manager
        
        logger.info("Azure services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    finally:
        # Cleanup tasks
        logger.info("Shutting down Deep Research application")
        if hasattr(app.state, 'azure_manager'):
            await app.state.azure_manager.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Deep Research API",
    description="AI-powered deep research application using Azure AI Foundry",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler with structured logging."""
    logger.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )


# Include API routers
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(research.router, prefix="/api/v1/research", tags=["Research"])
app.include_router(orchestration.router, prefix="/api/v1", tags=["Orchestration"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(convert.router, prefix="/api/v1/export", tags=["Convert"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(user_settings.router, prefix="/api/v1/settings", tags=["Settings"])


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Deep Research API",
        "version": "1.0.0",
        "description": "AI-powered research application using Azure AI Foundry",
        "docs": "/docs"
    }


@app.get("/api/v1/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Deep Research API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "azure_region": settings.AZURE_REGION,
        "features": {
            "multi_llm_orchestration": True,
            "bing_grounding": True,
            "pdf_export": True,
            "pptx_export": True,
            "real_time_updates": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # For development only
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )
