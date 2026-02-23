"""
虚拟AI代理 - 模型列表
"""

from fastapi import APIRouter, Depends
from api.dependencies import get_config_manager
from core.config import ConfigManager

router = APIRouter()


@router.get("/models")
async def list_models(config_manager: ConfigManager = Depends(get_config_manager)):
    """
    获取可用模型列表（从配置动态读取，OpenAI兼容格式）
    """
    virtual_models = config_manager.get("ai-gateway.virtual_models", {})
    
    models = []
    for name, config in virtual_models.items():
        # 只返回启用的模型
        if config.get("use", True):
            models.append({
                "id": name,
                "object": "model",
                "created": 1704067200,
                "owned_by": "ai-gateway"
            })
    
    return {
        "object": "list",
        "data": models
    }
