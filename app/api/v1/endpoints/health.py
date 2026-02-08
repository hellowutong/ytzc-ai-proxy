"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from models.base import HealthStatus, ResponseBase
from db.mongodb import get_mongodb_client
from db.redis import get_redis_client
from db.qdrant import get_qdrant_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def health_check():
    """
    Overall health check endpoint.
    Returns status of all services.
    """
    services = {}
    overall_status = "healthy"
    
    # Check MongoDB
    try:
        mongo_client = await get_mongodb_client()
        mongo_healthy = await mongo_client.health_check()
        services["mongodb"] = "healthy" if mongo_healthy else "unhealthy"
        if not mongo_healthy:
            overall_status = "degraded"
    except Exception as e:
        services["mongodb"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Check Redis
    try:
        redis_client = await get_redis_client()
        redis_healthy = await redis_client.health_check()
        services["redis"] = "healthy" if redis_healthy else "unhealthy"
        if not redis_healthy:
            overall_status = "degraded"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Check Qdrant
    try:
        qdrant_client = get_qdrant_client()
        qdrant_healthy = qdrant_client.health_check()
        services["qdrant"] = "healthy" if qdrant_healthy else "unhealthy"
        if not qdrant_healthy:
            overall_status = "degraded"
    except Exception as e:
        services["qdrant"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        services=services
    )


@router.get("/ready", response_model=ResponseBase)
async def readiness_check():
    """
    Readiness probe for Kubernetes.
    Returns 200 when application is ready to serve traffic.
    """
    return ResponseBase(
        success=True,
        message="Application is ready"
    )


@router.get("/live", response_model=ResponseBase)
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    Returns 200 when application is alive.
    """
    return ResponseBase(
        success=True,
        message="Application is alive"
    )


@router.get("/mongodb", response_model=ResponseBase)
async def mongodb_health():
    """MongoDB specific health check."""
    try:
        client = await get_mongodb_client()
        healthy = await client.health_check()
        return ResponseBase(
            success=healthy,
            message="MongoDB is healthy" if healthy else "MongoDB is unhealthy"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"MongoDB health check failed: {str(e)}"
        )


@router.get("/redis", response_model=ResponseBase)
async def redis_health():
    """Redis specific health check."""
    try:
        client = await get_redis_client()
        healthy = await client.health_check()
        return ResponseBase(
            success=healthy,
            message="Redis is healthy" if healthy else "Redis is unhealthy"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"Redis health check failed: {str(e)}"
        )


@router.get("/qdrant", response_model=ResponseBase)
async def qdrant_health():
    """Qdrant specific health check."""
    try:
        client = get_qdrant_client()
        healthy = client.health_check()
        return ResponseBase(
            success=healthy,
            message="Qdrant is healthy" if healthy else "Qdrant is unhealthy"
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"Qdrant health check failed: {str(e)}"
        )
