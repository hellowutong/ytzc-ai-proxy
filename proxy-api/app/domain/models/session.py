"""
领域模型 - 会话模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    ENDED = "ended"


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    model: Optional[str] = Field(None, description="使用的模型")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="时间戳")


class Session(BaseModel):
    """会话模型"""
    session_id: str = Field(..., description="会话 ID")
    proxy_key: str = Field(..., description="关联的代理 Key")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="状态")
    messages: List[Message] = Field(default_factory=list, description="消息列表")
    summary: Optional[str] = Field(None, description="会话摘要")
    vector_id: Optional[str] = Field(None, description="向量 ID")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="创建时间")
    ended_at: Optional[str] = Field(None, description="结束时间")
    
    def add_message(self, role: str, content: str, model: Optional[str] = None):
        """添加消息"""
        message = Message(role=role, content=content, model=model)
        self.messages.append(message)
    
    def end(self):
        """结束会话"""
        self.status = SessionStatus.ENDED
        self.ended_at = datetime.utcnow().isoformat()


class SessionCreate(BaseModel):
    """创建会话请求"""
    proxy_key: str


class SessionUpdate(BaseModel):
    """更新会话请求"""
    summary: Optional[str] = None
    status: Optional[SessionStatus] = None
