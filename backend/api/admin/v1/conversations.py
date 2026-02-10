"""
对话历史管理API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class Conversation(BaseModel):
    id: str
    model: str
    messages: List[Message]
    created_at: str
    updated_at: str


# Mock conversations
CONVERSATIONS = [
    {
        "id": "conv_001",
        "model": "demo1",
        "messages": [
            {"role": "user", "content": "你好", "timestamp": "2025-01-09T10:00:00Z"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？", "timestamp": "2025-01-09T10:00:05Z"}
        ],
        "created_at": "2025-01-09T10:00:00Z",
        "updated_at": "2025-01-09T10:00:05Z"
    },
    {
        "id": "conv_002",
        "model": "demo2",
        "messages": [
            {"role": "user", "content": "讲个笑话", "timestamp": "2025-01-09T11:00:00Z"},
            {"role": "assistant", "content": "为什么程序员总是分不清圣诞节和万圣节？因为 31 OCT = 25 DEC", "timestamp": "2025-01-09T11:00:05Z"}
        ],
        "created_at": "2025-01-09T11:00:00Z",
        "updated_at": "2025-01-09T11:00:05Z"
    }
]


@router.get("/conversations")
async def get_conversations(
    page: int = 1,
    page_size: int = 20,
    model: Optional[str] = None
):
    """获取对话列表"""
    result = CONVERSATIONS
    
    if model:
        result = [c for c in result if c["model"] == model]
    
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


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取单个对话详情"""
    for conv in CONVERSATIONS:
        if conv["id"] == conversation_id:
            return {
                "code": 200,
                "message": "success",
                "data": conv
            }
    
    raise HTTPException(status_code=404, detail="对话不存在")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除对话"""
    global CONVERSATIONS
    
    original_len = len(CONVERSATIONS)
    CONVERSATIONS = [c for c in CONVERSATIONS if c["id"] != conversation_id]
    
    if len(CONVERSATIONS) < original_len:
        return {
            "code": 200,
            "message": "对话删除成功",
            "data": None
        }
    
    raise HTTPException(status_code=404, detail="对话不存在")
