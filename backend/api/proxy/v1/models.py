"""
虚拟AI代理 - 模型列表
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/models")
async def list_models():
    """
    获取可用模型列表（OpenAI兼容格式）
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "demo1",
                "object": "model",
                "created": 1704067200,
                "owned_by": "ai-gateway"
            },
            {
                "id": "demo2",
                "object": "model",
                "created": 1704067200,
                "owned_by": "ai-gateway"
            }
        ]
    }
