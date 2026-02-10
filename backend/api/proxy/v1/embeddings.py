"""
虚拟AI代理 - 向量嵌入
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/embeddings")
async def create_embeddings():
    """
    创建向量嵌入（OpenAI兼容格式）
    """
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.0023064255, -0.009327292, 0.0152341],
                "index": 0
            }
        ],
        "model": "text-embedding-ada-002",
        "usage": {
            "prompt_tokens": 8,
            "total_tokens": 8
        }
    }
