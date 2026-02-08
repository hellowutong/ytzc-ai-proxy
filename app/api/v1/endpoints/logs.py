"""
Logs API endpoints for querying and managing logs.

Provides endpoints for:
- Querying system logs and operation logs
- Filtering by level, time range, source
- Exporting logs
- Log statistics
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from db.mongodb import get_mongodb_client
from models.base import ResponseBase
from models.log import LogLevel

router = APIRouter(prefix="/logs", tags=["logs"])


class LogQueryParams(BaseModel):
    """Log query parameters."""
    log_type: str = Field(default="all", description="Log type: all, system, operation")
    level: Optional[str] = Field(default=None, description="Log level filter")
    source: Optional[str] = Field(default=None, description="Source component filter")
    start_time: Optional[datetime] = Field(default=None, description="Start time (ISO format)")
    end_time: Optional[datetime] = Field(default=None, description="End time (ISO format)")
    search: Optional[str] = Field(default=None, description="Search in message")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class LogEntryResponse(BaseModel):
    """Log entry response model."""
    id: str
    timestamp: datetime
    level: str
    message: str
    source: str
    log_type: str
    metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    status: Optional[str] = None


class LogsListResponse(ResponseBase):
    """Logs list response."""
    data: Dict[str, Any] = Field(default_factory=dict)


@router.get("", response_model=LogsListResponse)
async def query_logs(
    log_type: str = Query(default="all", description="Log type: all, system, operation"),
    level: Optional[str] = Query(default=None, description="Log level filter"),
    source: Optional[str] = Query(default=None, description="Source component filter"),
    start_time: Optional[datetime] = Query(default=None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(default=None, description="End time (ISO format)"),
    search: Optional[str] = Query(default=None, description="Search in message"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """
    Query logs with filtering and pagination.
    
    Returns paginated list of logs matching the criteria.
    """
    try:
        mongo_client = await get_mongodb_client()
        
        # Build query filter
        query_filter = {}
        
        if level:
            query_filter["level"] = level.upper()
        
        if source:
            query_filter["source"] = {"$regex": source, "$options": "i"}
        
        # Time range filter
        time_filter = {}
        if start_time:
            time_filter["$gte"] = start_time
        if end_time:
            time_filter["$lte"] = end_time
        if time_filter:
            query_filter["timestamp"] = time_filter
        
        # Text search in message
        if search:
            query_filter["message"] = {"$regex": search, "$options": "i"}
        
        # Determine collections to query
        collections = []
        if log_type in ["all", "system"]:
            collections.append(("system_logs", "system"))
        if log_type in ["all", "operation"]:
            collections.append(("operation_logs", "operation"))
        
        # Query each collection
        all_logs = []
        total_count = 0
        
        skip = (page - 1) * page_size
        
        for coll_name, coll_type in collections:
            collection = mongo_client[coll_name]
            
            # Count total matching documents
            count = await collection.count_documents(query_filter)
            total_count += count
            
            # Query documents with pagination
            cursor = collection.find(query_filter) \
                .sort("timestamp", -1) \
                .skip(skip) \
                .limit(page_size)
            
            async for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                doc["log_type"] = coll_type
                all_logs.append(doc)
        
        # Sort combined results by timestamp
        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply pagination to combined results
        paginated_logs = all_logs[:page_size]
        
        return LogsListResponse(
            success=True,
            message="Logs retrieved successfully",
            data={
                "logs": paginated_logs,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query logs: {str(e)}")


@router.get("/system", response_model=LogsListResponse)
async def get_system_logs(
    level: Optional[str] = Query(default=None),
    component: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Get system logs only."""
    return await query_logs(
        log_type="system",
        level=level,
        source=component,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )


@router.get("/operation", response_model=LogsListResponse)
async def get_operation_logs(
    level: Optional[str] = Query(default=None),
    operation: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start_time: Optional[datetime] = Query(default=None),
    end_time: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Get operation logs only."""
    query_filter = {}
    
    if level:
        query_filter["level"] = level.upper()
    if operation:
        query_filter["operation"] = {"$regex": operation, "$options": "i"}
    if status:
        query_filter["status"] = status.lower()
    
    # Time range
    time_filter = {}
    if start_time:
        time_filter["$gte"] = start_time
    if end_time:
        time_filter["$lte"] = end_time
    if time_filter:
        query_filter["timestamp"] = time_filter
    
    try:
        mongo_client = await get_mongodb_client()
        collection = mongo_client.operation_logs
        
        total = await collection.count_documents(query_filter)
        skip = (page - 1) * page_size
        
        cursor = collection.find(query_filter) \
            .sort("timestamp", -1) \
            .skip(skip) \
            .limit(page_size)
        
        logs = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            doc["log_type"] = "operation"
            logs.append(doc)
        
        return LogsListResponse(
            success=True,
            message="Operation logs retrieved successfully",
            data={
                "logs": logs,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query operation logs: {str(e)}")


@router.get("/stats", response_model=ResponseBase)
async def get_log_statistics(
    hours: int = Query(default=24, ge=1, le=168, description="Statistics for last N hours")
):
    """
    Get log statistics for the specified time period.
    
    Returns counts by level, source, and hourly distribution.
    """
    try:
        mongo_client = await get_mongodb_client()
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query_filter = {"timestamp": {"$gte": start_time}}
        
        stats = {
            "period_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "system_logs": {},
            "operation_logs": {}
        }
        
        # System logs stats
        system_coll = mongo_client.system_logs
        system_pipeline = [
            {"$match": query_filter},
            {"$group": {"_id": "$level", "count": {"$sum": 1}}}
        ]
        
        system_by_level = {}
        async for doc in system_coll.aggregate(system_pipeline):
            system_by_level[doc["_id"]] = doc["count"]
        stats["system_logs"]["by_level"] = system_by_level
        stats["system_logs"]["total"] = sum(system_by_level.values())
        
        # Operation logs stats
        operation_coll = mongo_client.operation_logs
        operation_pipeline = [
            {"$match": query_filter},
            {"$group": {"_id": "$level", "count": {"$sum": 1}}}
        ]
        
        operation_by_level = {}
        async for doc in operation_coll.aggregate(operation_pipeline):
            operation_by_level[doc["_id"]] = doc["count"]
        stats["operation_logs"]["by_level"] = operation_by_level
        stats["operation_logs"]["total"] = sum(operation_by_level.values())
        
        # Recent errors
        error_filter = {**query_filter, "level": "ERROR"}
        recent_errors = []
        
        async for doc in system_coll.find(error_filter).sort("timestamp", -1).limit(5):
            recent_errors.append({
                "id": str(doc["_id"]),
                "timestamp": doc["timestamp"].isoformat(),
                "message": doc["message"],
                "source": doc.get("source", "unknown")
            })
        
        stats["recent_errors"] = recent_errors
        
        return ResponseBase(
            success=True,
            message="Log statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log statistics: {str(e)}")


@router.delete("", response_model=ResponseBase)
async def clear_old_logs(
    days: int = Query(default=30, ge=1, le=365, description="Delete logs older than N days")
):
    """
    Clear logs older than the specified number of days.
    
    This operation cannot be undone. Use with caution.
    """
    try:
        mongo_client = await get_mongodb_client()
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        query_filter = {"timestamp": {"$lt": cutoff_time}}
        
        # Delete from system_logs
        system_result = await mongo_client.system_logs.delete_many(query_filter)
        system_deleted = system_result.deleted_count
        
        # Delete from operation_logs
        operation_result = await mongo_client.operation_logs.delete_many(query_filter)
        operation_deleted = operation_result.deleted_count
        
        total_deleted = system_deleted + operation_deleted
        
        return ResponseBase(
            success=True,
            message=f"Cleared {total_deleted} old log entries",
            data={
                "deleted_count": total_deleted,
                "system_logs_deleted": system_deleted,
                "operation_logs_deleted": operation_deleted,
                "older_than_days": days,
                "cutoff_time": cutoff_time.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")
