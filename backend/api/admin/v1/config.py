"""
Config管理API - 系统配置模块
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Optional

router = APIRouter()


class ConfigUpdateRequest(BaseModel):
    path: str
    value: Any


class ConfigRawRequest(BaseModel):
    yaml: str


@router.get("/config")
async def get_config(request: Request):
    """获取完整配置"""
    config_manager = request.app.state.config_manager
    config = config_manager.config
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            **config,
            "_raw": config_manager.get_raw_yaml()
        }
    }


@router.put("/config")
async def update_config(request: Request, body: ConfigUpdateRequest):
    """更新配置项"""
    config_manager = request.app.state.config_manager
    
    try:
        config_manager.set(body.path, body.value)
        config_manager.save_config()
        
        return {
            "code": 200,
            "message": "配置更新成功",
            "data": None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/config/raw")
async def update_raw_config(request: Request, body: ConfigRawRequest):
    """直接更新YAML配置"""
    config_manager = request.app.state.config_manager
    
    try:
        config_manager.load_from_yaml(body.yaml)
        config_manager.save_config()
        
        return {
            "code": 200,
            "message": "配置保存成功",
            "data": None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/config/reload")
async def reload_config(request: Request):
    """重新加载配置"""
    config_manager = request.app.state.config_manager
    
    try:
        config_manager.load_config()
        
        return {
            "code": 200,
            "message": "配置重载成功",
            "data": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
