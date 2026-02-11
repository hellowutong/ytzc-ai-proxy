"""
对话历史管理API
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
from datetime import datetime

from api.dependencies import get_conversation_manager
from core.conversation_manager import ConversationManager

router = APIRouter()


@router.get("/conversations")
async def get_conversations(
    page: int = 1,
    page_size: int = 20,
    model: Optional[str] = None,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """获取对话列表"""
    conversations, total = await conversation_manager.list_conversations(
        virtual_model=model,
        limit=page_size,
        offset=(page - 1) * page_size
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": conv.id,
                    "model": conv.virtual_model,
                    "messages": [],  # 列表不返回详细消息
                    "created_at": conv.created_at.isoformat() if isinstance(conv.created_at, datetime) else str(conv.created_at),
                    "updated_at": conv.updated_at.isoformat() if isinstance(conv.updated_at, datetime) else str(conv.updated_at)
                }
                for conv in conversations
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """获取单个对话详情"""
    conv = await conversation_manager.get_conversation(conversation_id)
    
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": conv.id,
            "model": conv.virtual_model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if isinstance(msg.timestamp, datetime) else str(msg.timestamp)
                }
                for msg in conv.messages
            ],
            "created_at": conv.created_at.isoformat() if isinstance(conv.created_at, datetime) else str(conv.created_at),
            "updated_at": conv.updated_at.isoformat() if isinstance(conv.updated_at, datetime) else str(conv.updated_at)
        }
    }


@router.post("/conversations")
async def create_conversation(
    body: dict,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """创建新对话"""
    model = body.get("model", "")
    conversation_id = await conversation_manager.create_conversation(model)
    return {
        "code": 200,
        "message": "对话创建成功",
        "data": {"id": conversation_id}
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """删除对话"""
    success = await conversation_manager.delete_conversation(conversation_id)
    if success:
        return {
            "code": 200,
            "message": "对话删除成功",
            "data": None
        }
    raise HTTPException(status_code=404, detail="对话不存在")
