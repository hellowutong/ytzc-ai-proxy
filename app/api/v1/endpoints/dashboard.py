"""
Dashboard API endpoints for system metrics and overview.

Provides endpoints for:
- System overview statistics
- Service health status
- Recent activity
- Performance metrics
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.mongodb import get_mongodb_client
from db.redis import get_redis_client
from db.qdrant import get_qdrant_client
from core.config_manager import get_config_manager
from models.base import ResponseBase

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class SystemOverview(BaseModel):
    """System overview statistics."""
    total_virtual_models: int
    total_routes: int
    databases: Dict[str, str]
    services_status: Dict[str, str]


class RecentActivity(BaseModel):
    """Recent activity statistics."""
    recent_logs_24h: int
    recent_errors_24h: int
    last_error: Optional[Dict[str, Any]]


class DashboardData(BaseModel):
    """Complete dashboard data."""
    overview: SystemOverview
    activity: RecentActivity
    timestamp: datetime


class DashboardResponse(ResponseBase):
    """Dashboard response."""
    data: Dict[str, Any] = Field(default_factory=dict)


@router.get("/overview", response_model=DashboardResponse)
async def get_dashboard_overview():
    """
    Get dashboard overview with key metrics.
    
    Returns system statistics, service health, and recent activity.
    """
    try:
        # Get config manager for virtual models
        config_manager = get_config_manager()
        virtual_models = config_manager.get_virtual_models()
        
        # Count routes across all models
        total_routes = 0
        for model_name, model_config in virtual_models.items():
            if isinstance(model_config, dict):
                routes = model_config.get("routes", [])
                total_routes += len(routes)
        
        # Check service health
        services_status = {}
        databases = {}
        
        # MongoDB
        try:
            mongo_client = await get_mongodb_client()
            mongo_healthy = await mongo_client.health_check()
            services_status["mongodb"] = "healthy" if mongo_healthy else "unhealthy"
            databases["mongodb"] = "connected"
        except Exception as e:
            services_status["mongodb"] = f"error: {str(e)}"
            databases["mongodb"] = "disconnected"
        
        # Redis
        try:
            redis_client = await get_redis_client()
            redis_healthy = await redis_client.health_check()
            services_status["redis"] = "healthy" if redis_healthy else "unhealthy"
            databases["redis"] = "connected"
        except Exception as e:
            services_status["redis"] = f"error: {str(e)}"
            databases["redis"] = "disconnected"
        
        # Qdrant
        try:
            qdrant_client = get_qdrant_client()
            qdrant_healthy = qdrant_client.health_check()
            services_status["qdrant"] = "healthy" if qdrant_healthy else "unhealthy"
            databases["qdrant"] = "connected"
        except Exception as e:
            services_status["qdrant"] = f"error: {str(e)}"
            databases["qdrant"] = "disconnected"
        
        # Get recent activity from MongoDB
        mongo_client = await get_mongodb_client()
        start_time = datetime.utcnow() - timedelta(hours=24)
        time_filter = {"timestamp": {"$gte": start_time}}
        
        # Count recent logs
        recent_system_logs = await mongo_client.system_logs.count_documents(time_filter)
        recent_operation_logs = await mongo_client.operation_logs.count_documents(time_filter)
        recent_logs_24h = recent_system_logs + recent_operation_logs
        
        # Count recent errors
        error_filter = {**time_filter, "level": "ERROR"}
        recent_system_errors = await mongo_client.system_logs.count_documents(error_filter)
        recent_operation_errors = await mongo_client.operation_logs.count_documents(error_filter)
        recent_errors_24h = recent_system_errors + recent_operation_errors
        
        # Get last error
        last_error = None
        async for doc in mongo_client.system_logs.find(error_filter).sort("timestamp", -1).limit(1):
            last_error = {
                "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else str(doc["timestamp"]),
                "message": doc["message"],
                "source": doc.get("source", "unknown"),
                "level": doc.get("level", "ERROR")
            }
        
        # Build response
        overview = SystemOverview(
            total_virtual_models=len(virtual_models),
            total_routes=total_routes,
            databases=databases,
            services_status=services_status
        )
        
        activity = RecentActivity(
            recent_logs_24h=recent_logs_24h,
            recent_errors_24h=recent_errors_24h,
            last_error=last_error
        )
        
        return DashboardResponse(
            success=True,
            message="Dashboard overview retrieved successfully",
            data={
                "overview": overview.dict(),
                "activity": activity.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")


@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats():
    """
    Get detailed dashboard statistics.
    
    Returns various statistics for charts and graphs.
    """
    try:
        mongo_client = await get_mongodb_client()
        
        # Get hourly log distribution for last 24 hours
        hourly_stats = []
        for i in range(24):
            hour_start = datetime.utcnow() - timedelta(hours=i+1)
            hour_end = datetime.utcnow() - timedelta(hours=i)
            
            hour_filter = {
                "timestamp": {
                    "$gte": hour_start,
                    "$lt": hour_end
                }
            }
            
            system_count = await mongo_client.system_logs.count_documents(hour_filter)
            operation_count = await mongo_client.operation_logs.count_documents(hour_filter)
            
            hourly_stats.append({
                "hour": hour_start.strftime("%H:00"),
                "system_logs": system_count,
                "operation_logs": operation_count,
                "total": system_count + operation_count
            })
        
        # Reverse to get chronological order
        hourly_stats.reverse()
        
        # Get log level distribution
        level_pipeline = [
            {"$group": {"_id": "$level", "count": {"$sum": 1}}}
        ]
        
        level_distribution = {}
        async for doc in mongo_client.system_logs.aggregate(level_pipeline):
            level_distribution[doc["_id"]] = doc["count"]
        
        # Get top log sources
        source_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_sources = []
        async for doc in mongo_client.system_logs.aggregate(source_pipeline):
            top_sources.append({
                "source": doc["_id"],
                "count": doc["count"]
            })
        
        return DashboardResponse(
            success=True,
            message="Dashboard statistics retrieved successfully",
            data={
                "hourly_distribution": hourly_stats,
                "level_distribution": level_distribution,
                "top_sources": top_sources
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


@router.get("/services", response_model=ResponseBase)
async def get_services_status():
    """
    Get detailed status of all services.
    
    Returns health and connection status for all backend services.
    """
    try:
        services = {}
        
        # MongoDB
        try:
            mongo_client = await get_mongodb_client()
            mongo_healthy = await mongo_client.health_check()
            
            # Get database stats
            db_stats = await mongo_client.db.command("dbStats")
            
            services["mongodb"] = {
                "status": "healthy" if mongo_healthy else "unhealthy",
                "connected": True,
                "database": "ai-gateway",
                "collections": db_stats.get("collections", 0),
                "documents": db_stats.get("objects", 0),
                "data_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2)
            }
        except Exception as e:
            services["mongodb"] = {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
        
        # Redis
        try:
            redis_client = await get_redis_client()
            redis_healthy = await redis_client.health_check()
            
            # Get Redis info
            info = await redis_client.redis.info()
            
            services["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connected": True,
                "version": info.get("redis_version", "unknown"),
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            services["redis"] = {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
        
        # Qdrant
        try:
            qdrant_client = get_qdrant_client()
            qdrant_healthy = qdrant_client.health_check()
            
            services["qdrant"] = {
                "status": "healthy" if qdrant_healthy else "unhealthy",
                "connected": True,
                "host": "localhost",
                "port": 6333
            }
        except Exception as e:
            services["qdrant"] = {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
        
        return ResponseBase(
            success=True,
            message="Services status retrieved successfully",
            data=services
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services status: {str(e)}")


@router.get("/virtual-models", response_model=ResponseBase)
async def get_virtual_models_summary():
    """
    Get summary of virtual models.
    
    Returns list of virtual models with their route counts.
    """
    try:
        config_manager = get_config_manager()
        models = config_manager.get_virtual_models()
        
        model_summaries = []
        for name, config in models.items():
            if isinstance(config, dict):
                routes = config.get("routes", [])
                model_summaries.append({
                    "name": name,
                    "description": config.get("description", ""),
                    "route_count": len(routes),
                    "enabled": config.get("enabled", True),
                    "routes": [
                        {
                            "provider": r.get("provider", "unknown"),
                            "model": r.get("model", "unknown"),
                            "weight": r.get("weight", 1.0)
                        }
                        for r in routes
                    ] if routes else []
                })
        
        return ResponseBase(
            success=True,
            message="Virtual models summary retrieved successfully",
            data={
                "models": model_summaries,
                "total": len(model_summaries),
                "enabled": sum(1 for m in model_summaries if m["enabled"])
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get virtual models summary: {str(e)}")
