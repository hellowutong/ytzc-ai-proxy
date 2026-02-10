"""
日志查询API
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime

router = APIRouter()


# Mock log data
SYSTEM_LOGS = [
    {
        "id": "log_001",
        "timestamp": "2025-01-09T10:00:00Z",
        "level": "INFO",
        "module": "config",
        "message": "配置加载成功"
    },
    {
        "id": "log_002",
        "timestamp": "2025-01-09T10:05:00Z",
        "level": "WARNING",
        "module": "database",
        "message": "数据库连接池接近上限"
    },
    {
        "id": "log_003",
        "timestamp": "2025-01-09T10:10:00Z",
        "level": "ERROR",
        "module": "skill",
        "message": "Skill执行失败: router"
    }
]

OPERATION_LOGS = [
    {
        "id": "op_001",
        "timestamp": "2025-01-09T10:00:00Z",
        "user": "admin",
        "action": "创建虚拟模型",
        "target": "demo1",
        "status": "success"
    },
    {
        "id": "op_002",
        "timestamp": "2025-01-09T11:00:00Z",
        "user": "admin",
        "action": "上传文档",
        "target": "manual.pdf",
        "status": "success"
    }
]

SKILL_LOGS = [
    {
        "id": "skill_log_001",
        "timestamp": "2025-01-09T10:00:00Z",
        "skill": "router",
        "input": "用户查询",
        "output": "路由到大模型",
        "duration": 120,
        "success": True
    },
    {
        "id": "skill_log_002",
        "timestamp": "2025-01-09T10:05:00Z",
        "skill": "knowledge_retrieval",
        "input": "搜索查询",
        "output": "找到3个相关文档",
        "duration": 250,
        "success": True
    }
]


@router.get("/logs/system")
async def get_system_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    module: Optional[str] = Query(None, description="模块过滤"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = 1,
    page_size: int = 50
):
    """获取系统日志"""
    result = SYSTEM_LOGS
    
    if level:
        levels = level.split(",")
        result = [l for l in result if l["level"] in levels]
    
    if module:
        result = [l for l in result if module.lower() in l["module"].lower()]
    
    if keyword:
        result = [l for l in result if keyword.lower() in l["message"].lower()]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": result,
            "total": len(result),
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/logs/operation")
async def get_operation_logs(
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 50
):
    """获取操作日志"""
    result = OPERATION_LOGS
    
    if keyword:
        result = [l for l in result if keyword.lower() in str(l).lower()]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": result,
            "total": len(result),
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/logs/skill")
async def get_skill_logs(
    skill: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 50
):
    """获取Skill执行日志"""
    result = SKILL_LOGS
    
    if skill:
        result = [l for l in result if l["skill"] == skill]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": result,
            "total": len(result),
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/logs/{log_type}/export")
async def export_logs(
    log_type: str,
    format: str = "json"
):
    """导出日志"""
    from fastapi.responses import StreamingResponse
    import json
    import csv
    import io
    
    if log_type == "system":
        data = SYSTEM_LOGS
    elif log_type == "operation":
        data = OPERATION_LOGS
    elif log_type == "skill":
        data = SKILL_LOGS
    else:
        return {
            "code": 400,
            "message": "不支持的日志类型",
            "data": None
        }
    
    if format == "json":
        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={log_type}_logs.json"}
        )
    
    elif format == "csv":
        if not data:
            return {"code": 400, "message": "没有数据可导出"}
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={log_type}_logs.csv"}
        )
    
    return {
        "code": 400,
        "message": "不支持的格式",
        "data": None
    }
