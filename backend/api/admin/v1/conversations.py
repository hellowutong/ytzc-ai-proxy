"""
对话历史管理API
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from api.dependencies import get_conversation_manager
from core.conversation_manager import ConversationManager

router = APIRouter()


class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    model: str
    metadata: Optional[Dict[str, Any]] = None  # 新增: 对话元数据


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
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat() if isinstance(msg.timestamp, datetime) else str(msg.timestamp)
                        }
                        for msg in conv.messages
                    ],
                    "message_count": conv.message_count,
                    "created_at": conv.created_at.isoformat() if isinstance(conv.created_at, datetime) else str(conv.created_at),
                    "updated_at": conv.updated_at.isoformat() if isinstance(conv.updated_at, datetime) else str(conv.updated_at),
                    "metadata": conv.metadata  # 新增: 返回metadata
                }
                for conv in conversations
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


class BatchDeleteRequest(BaseModel):
    ids: list[str]


@router.delete("/conversations/batch")
async def batch_delete_conversations(
    request: BatchDeleteRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """批量删除对话"""
    ids = request.ids
    if not ids:
        raise HTTPException(status_code=400, detail="未提供对话ID列表")
    
    success_count = 0
    failed_ids = []
    
    for conversation_id in ids:
        try:
            success = await conversation_manager.delete_conversation(conversation_id)
            if success:
                success_count += 1
            else:
                failed_ids.append(conversation_id)
        except Exception:
            failed_ids.append(conversation_id)
    
    return {
        "code": 200,
        "message": f"已删除 {success_count} 个对话",
        "data": {
            "success_count": success_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
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
            "updated_at": conv.updated_at.isoformat() if isinstance(conv.updated_at, datetime) else str(conv.updated_at),
            "metadata": conv.metadata  # 新增: 返回metadata
        }
    }


@router.post("/conversations")
async def create_conversation(
    request: CreateConversationRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """创建新对话"""
    conversation_id = await conversation_manager.create_conversation(
        virtual_model=request.model,
        metadata=request.metadata  # 新增: 传递metadata
    )
    
    return {
        "code": 200,
        "message": "对话创建成功",
        "data": {
            "id": conversation_id,
            "model": request.model,
            "metadata": request.metadata  # 返回metadata
        }
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


@router.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    body: dict,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """更新对话消息"""
    messages = body.get("messages", [])
    updated_at = body.get("updated_at")
    
    success = await conversation_manager.update_messages(
        conversation_id,
        messages,
        updated_at
    )
    
    if success:
        return {
            "code": 200,
            "message": "对话更新成功",
            "data": None
        }
    raise HTTPException(status_code=404, detail="对话不存在")
