"""
Health check API endpoints for Deep Research application.

Provides comprehensive health monitoring including:
- Application health status
- Azure service connectivity
- Performance metrics
- System resource usage
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.azure_config import AzureServiceManager
from app.models.schemas import HealthStatus, ErrorResponse


router = APIRouter()
logger = structlog.get_logger(__name__)


async def get_azure_manager(request: Request) -> AzureServiceManager:
    """Dependency to get Azure service manager from app state."""
    if not hasattr(request.app.state, 'azure_manager'):
        raise HTTPException(
            status_code=503,
            detail="Azure services not initialized"
        )
    return request.app.state.azure_manager


@router.get("/", response_model=HealthStatus)
async def health_check(
    request: Request,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Comprehensive health check endpoint.
    
    Returns:
        HealthStatus: Detailed health information including Azure services
    """
    start_time = time.time()
    
    try:
        # Basic application health
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
            "environment": getattr(request.app.state, 'environment', 'unknown'),
        }
        
        # Check Azure services health
        azure_health = await azure_manager.health_check()
        health_data["azure_services"] = azure_health
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Performance metrics
        health_data["performance_metrics"] = {
            "response_time_ms": round(response_time * 1000, 2),
            "azure_services_healthy": sum(azure_health.values()),
            "azure_services_total": len(azure_health),
        }
        
        # Determine overall status
        if all(azure_health.values()):
            health_data["status"] = "healthy"
        elif any(azure_health.values()):
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "unhealthy"
        
        logger.info(
            "Health check completed",
            status=health_data["status"],
            response_time_ms=health_data["performance_metrics"]["response_time_ms"]
        )
        
        return HealthStatus(**health_data)
        
    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            environment="unknown",
            azure_services={},
            performance_metrics={"response_time_ms": round((time.time() - start_time) * 1000, 2)}
        )


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(
    request: Request,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Simple ready/not ready status for container orchestration
    """
    try:
        # Check if Azure services are initialized
        if not azure_manager.is_initialized:
            return JSONResponse(
                status_code=503,
                content={"ready": False, "reason": "Azure services not initialized"}
            )
        
        # Quick health check
        azure_health = await azure_manager.health_check()
        
        # Require at least basic services to be healthy
        required_services = ["cosmos_db", "blob_storage"]
        required_healthy = all(
            azure_health.get(service, False) for service in required_services
        )
        
        if required_healthy:
            return {"ready": True, "timestamp": datetime.utcnow().isoformat()}
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "reason": "Required Azure services unhealthy",
                    "services": azure_health
                }
            )
            
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": f"Health check error: {str(e)}"}
        )


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Simple alive status for container orchestration
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time()  # This would need to be tracked from app start
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(
    request: Request,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Detailed health check with extensive service information.
    
    Returns:
        Comprehensive health and diagnostic information
    """
    start_time = time.time()
    
    try:
        # Gather detailed health information
        health_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": "Deep Research API",
                "version": "1.0.0",
                "environment": getattr(request.app.state, 'environment', 'unknown'),
                "startup_time": getattr(request.app.state, 'startup_time', 'unknown')
            },
            "system": {
                "python_version": "3.11+",
                "platform": "Azure Container Apps"
            }
        }
        
        # Azure services detailed check
        azure_health = await azure_manager.health_check()
        health_info["azure_services"] = {
            "overall_status": "healthy" if all(azure_health.values()) else "degraded",
            "services": azure_health,
            "connectivity_test_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        # Performance metrics
        response_time = time.time() - start_time
        health_info["performance"] = {
            "response_time_ms": round(response_time * 1000, 2),
            "health_check_duration_ms": round(response_time * 1000, 2)
        }
        
        # Dependencies status
        health_info["dependencies"] = {
            "azure_ai_foundry": azure_health.get("ai_services", False),
            "cosmos_db": azure_health.get("cosmos_db", False),
            "blob_storage": azure_health.get("blob_storage", False),
            "key_vault": azure_health.get("key_vault", False)
        }
        
        return health_info
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e), exc_info=True)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }


@router.get("/metrics", response_model=Dict[str, Any])
async def metrics_endpoint(
    request: Request,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Application metrics endpoint for monitoring systems.
    
    Returns:
        Key performance and usage metrics
    """
    try:
        # TODO: Implement actual metrics collection
        # This would integrate with Azure Monitor and Application Insights
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "requests": {
                "total_requests": 0,  # Track in middleware
                "requests_per_minute": 0,
                "average_response_time_ms": 0,
                "error_rate_percent": 0
            },
            "research_tasks": {
                "total_tasks": 0,
                "active_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "average_completion_time_seconds": 0
            },
            "ai_models": {
                "total_tokens_used": 0,
                "total_cost_usd": 0,
                "model_usage_breakdown": {}
            },
            "azure_services": {
                "cosmos_db_requests": 0,
                "blob_storage_operations": 0,
                "key_vault_calls": 0
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error("Metrics collection failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to collect metrics"
        )
