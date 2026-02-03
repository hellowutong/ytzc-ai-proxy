"""
领域模型 - 连接模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class ConnectionStatus(str, Enum):
    """连接状态"""
    ENABLED = "enabled"
    DISABLED = "disabled"


class ModelConfig(BaseModel):
    """模型配置"""
    name: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API Base URL")
    api_key: str = Field(..., description="API Key")


class ProxyConnection(BaseModel):
    """代理连接模型"""
    id: str = Field(..., description="连接 ID")
    name: str = Field(..., description="连接名称")
    proxy_key: str = Field(..., description="代理 Key")
    small_model: ModelConfig = Field(..., description="小模型配置")
    big_model: ModelConfig = Field(..., description="大模型配置")
    status: ConnectionStatus = Field(default=ConnectionStatus.ENABLED, description="状态")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConnectionCreate(BaseModel):
    """创建连接请求"""
    name: str
    small_model: ModelConfig
    big_model: ModelConfig


class ConnectionUpdate(BaseModel):
    """更新连接请求"""
    name: Optional[str] = None
    small_model: Optional[ModelConfig] = None
    big_model: Optional[ModelConfig] = None
    status: Optional[ConnectionStatus] = None
