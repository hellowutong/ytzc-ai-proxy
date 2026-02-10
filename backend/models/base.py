"""
基础模型 - 所有Pydantic模型的基类
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_serializer
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ModelProvider(str, Enum):
    """模型提供商"""
    SILICONFLOW = "siliconflow"
    OPENAI = "openai"
    OLLAMA = "ollama"


class MediaType(str, Enum):
    """媒体类型"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"


class MediaStatus(str, Enum):
    """媒体处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchProvider(str, Enum):
    """搜索提供商"""
    SEARXNG = "searxng"
    LIBREX = "librex"
    FOURGET = "4get"


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseRequest(BaseModel):
    """基础请求模型"""
    pass


class Message(BaseModel):
    """对话消息模型"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """聊天完成请求"""
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = False
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)


class ChatCompletionChoice(BaseModel):
    """聊天完成选择"""
    index: int
    message: Message
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token使用情况"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


class ChatCompletionStreamChoice(BaseModel):
    """流式聊天完成选择"""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    """流式聊天完成响应"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]


class EmbeddingRequest(BaseModel):
    """嵌入请求"""
    input: str | List[str]
    model: Optional[str] = "BAAI/bge-m3"
    encoding_format: Optional[str] = "float"


class EmbeddingData(BaseModel):
    """嵌入数据"""
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    """嵌入响应"""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Usage


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelListResponse(BaseModel):
    """模型列表响应"""
    object: str = "list"
    data: List[ModelInfo]


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: ModelProvider
    base_url: str
    api_key: Optional[str] = None
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60


class EmbeddingConfig(BaseModel):
    """嵌入配置"""
    provider: ModelProvider
    base_url: str
    api_key: Optional[str] = None
    model: str = "BAAI/bge-m3"
    dimension: int = 1024
    timeout: int = 30


class WhisperConfig(BaseModel):
    """Whisper配置"""
    mode: Literal["local", "api"] = "local"
    model: str = "base"
    language: str = "zh"
    device: Optional[str] = None
    # API模式配置
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 300


class TranscriptionSegment(BaseModel):
    """转录片段"""
    id: int
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class TranscriptionResult(BaseModel):
    """转录结果"""
    text: str
    language: str
    segments: Optional[List[TranscriptionSegment]] = None
    duration: Optional[float] = None


class SearchResult(BaseModel):
    """搜索结果"""
    title: str
    url: str
    content: Optional[str] = None
    engine: str
    score: Optional[float] = None


class SearchConfig(BaseModel):
    """搜索配置"""
    provider: SearchProvider
    base_url: str
    timeout: int = 30
    categories: Optional[List[str]] = None
    language: str = "zh-CN"


class RouteResult(BaseModel):
    """路由结果"""
    model_type: Literal["small", "big"]
    confidence: Optional[float] = None
    matched_rule: Optional[str] = None
    reason: str


class KnowledgeChunk(BaseModel):
    """知识片段"""
    id: str
    content: str
    source: str
    confidence: float
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_serializer('created_at')
    def serialize_datetime(self, v: datetime) -> str:
        return v.isoformat()


class ExtractionResult(BaseModel):
    """提取结果"""
    chunks: List[KnowledgeChunk]
    total_chunks: int
    extracted_at: datetime
    extractor_type: str
    processing_time_ms: int
    knowledge_graph_updated: bool = False
    conflicts_detected: Optional[List[Dict[str, Any]]] = None

    @field_serializer('extracted_at')
    def serialize_datetime(self, v: datetime) -> str:
        return v.isoformat()


class ErrorResponse(BaseModel):
    """错误响应"""
    error: Dict[str, Any]

    @classmethod
    def create(cls, message: str, code: str = "internal_error", 
               type: str = "api_error") -> "ErrorResponse":
        return cls(error={
            "message": message,
            "type": type,
            "code": code
        })


# 通用类型别名
JsonDict = Dict[str, Any]
