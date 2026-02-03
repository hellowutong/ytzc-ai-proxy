"""
API 文档模型定义
包含所有API的请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== 通用模型 ==============

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    code: Optional[str] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页数量")


class PaginationResponse(BaseModel):
    """分页响应"""
    data: List[Any]
    total: int
    page: int
    limit: int


# ============== 连接管理模型 ==============

class ModelConfigModel(BaseModel):
    """模型配置"""
    name: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API基础URL")
    api_key: str = Field(..., description="API密钥", secret=True)


class ConnectionCreateModel(BaseModel):
    """创建连接请求"""
    name: str = Field(..., min_length=1, max_length=100, description="连接名称")
    small_model: ModelConfigModel = Field(..., description="小模型配置")
    big_model: ModelConfigModel = Field(..., description="大模型配置")


class ConnectionResponseModel(BaseModel):
    """连接响应"""
    id: str
    name: str
    proxy_key: str = Field(..., description="脱敏显示 tw-a1b2****3c4d")
    small_model: Dict[str, str]
    big_model: Dict[str, str]
    status: str = Field(..., description="enabled | disabled")
    created_at: datetime


class ConnectionUpdateModel(BaseModel):
    """更新连接请求"""
    name: Optional[str] = None
    small_model: Optional[ModelConfigModel] = None
    big_model: Optional[ModelConfigModel] = None


# ============== 供应商配置模型 ==============

class ProviderModel(BaseModel):
    """供应商配置"""
    name: str
    small_model: Dict[str, str]
    big_model: Dict[str, str]
    proxy_key: str


class ProviderTestResponse(BaseModel):
    """供应商测试响应"""
    status: str = Field(..., description="success | failed")
    message: str
    latency_ms: Optional[int] = None


# ============== 会话管理模型 ==============

class MessageModel(BaseModel):
    """消息"""
    role: str = Field(..., description="user | assistant | system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = None
    model: Optional[str] = None


class SessionCreateModel(BaseModel):
    """创建会话请求"""
    proxy_key: str = Field(..., description="代理Key")


class SessionResponseModel(BaseModel):
    """会话响应"""
    session_id: str
    proxy_key: str
    status: str = Field(..., description="active | ended")
    messages: List[MessageModel]
    summary: Optional[str] = None
    vector_id: Optional[str] = None
    created_at: datetime
    ended_at: Optional[datetime] = None


class SessionUpdateModel(BaseModel):
    """更新会话请求"""
    summary: Optional[str] = None


class MessageCreateModel(BaseModel):
    """添加消息请求"""
    role: str
    content: str


# ============== Skill管理模型 ==============

class SkillVersionModel(BaseModel):
    """Skill版本"""
    version_id: int
    status: str = Field(..., description="draft | published | deprecated")
    created_at: datetime
    created_by: str
    source_session_id: Optional[str] = None
    change_reason: Optional[str] = None


class SkillCreateModel(BaseModel):
    """创建Skill请求"""
    base_id: str = Field(..., description="Skill唯一标识")
    description: str = Field(..., description="Skill描述")


class SkillResponseModel(BaseModel):
    """Skill响应"""
    base_id: str
    active_version_id: int
    created_at: datetime
    versions: List[SkillVersionModel]


class SkillVersionCreateModel(BaseModel):
    """创建版本请求"""
    status: str = "draft"
    created_by: str = "user"
    source_session_id: Optional[str] = None
    change_reason: Optional[str] = None


class SkillPublishModel(BaseModel):
    """发布Skill请求"""
    version_id: int


class SkillRollbackModel(BaseModel):
    """回滚Skill请求"""
    version_id: int


# ============== 向量存储模型 ==============

class VectorSearchModel(BaseModel):
    """向量搜索请求"""
    query: str = Field(..., description="搜索查询")
    limit: int = Field(10, ge=1, le=100)
    score_threshold: float = Field(0.7, ge=0, le=1)


class VectorSearchResponse(BaseModel):
    """向量搜索响应"""
    data: List[Dict[str, Any]]
    total: int
    limit: int


class VectorAddModel(BaseModel):
    """添加向量请求"""
    content: str
    vector: List[float]


class CollectionInfoModel(BaseModel):
    """集合信息"""
    name: str
    points_count: int
    vectors_count: int


# ============== 文件管理模型 ==============

class FileReadResponse(BaseModel):
    """读取文件响应"""
    content: str
    path: str


class FileUpdateModel(BaseModel):
    """更新文件请求"""
    content: str


# ============== 配置管理模型 ==============

class ConfigResponseModel(BaseModel):
    """配置响应"""
    app: Dict[str, Any]
    mongodb: Dict[str, Any]
    qdrant: Dict[str, Any]
    strategy: Dict[str, Any]
    providers: List[Dict[str, Any]]


class ConfigUpdateModel(BaseModel):
    """更新配置请求"""
    config: Dict[str, Any]


# ============== 备份管理模型 ==============

class BackupCreateModel(BaseModel):
    """创建备份请求"""
    name: Optional[str] = None


class BackupResponseModel(BaseModel):
    """备份响应"""
    id: str
    name: str
    size: int
    created_at: datetime
    contents: List[str]


# ============== baseskill管理模型 ==============

class BaseSkillModel(BaseModel):
    """baseskill模板"""
    id: str
    name: str
    type: str = Field(..., description="system | custom")
    description: Optional[str] = None
    status: Optional[str] = None


class BaseSkillCreateModel(BaseModel):
    """创建baseskill请求"""
    name: str
    skill_md: str
    prompt_template: str
    rules_yaml: str


class BaseSkillUpdateModel(BaseModel):
    """更新baseskill请求"""
    skill_md: Optional[str] = None
    prompt_template: Optional[str] = None
    rules_yaml: Optional[str] = None


# ============== 代理API模型 ==============

class ChatMessageModel(BaseModel):
    """聊天消息"""
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """聊天补全请求"""
    model: str
    messages: List[ChatMessageModel]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatCompletionChoiceModel(BaseModel):
    """聊天补全选择"""
    index: int
    message: ChatMessageModel
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """聊天补全响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoiceModel]
    usage: Dict[str, int]


class EmbeddingRequest(BaseModel):
    """嵌入请求"""
    model: str = "text-embedding-3-small"
    input: List[str]


class EmbeddingDataModel(BaseModel):
    """嵌入数据"""
    embedding: List[float]
    index: int
    object: str = "embedding"


class EmbeddingResponse(BaseModel):
    """嵌入响应"""
    data: List[EmbeddingDataModel]
    model: str
    object: str = "list"
    usage: Dict[str, int]


class ModelsResponse(BaseModel):
    """模型列表响应"""
    data: List[Dict[str, str]]
    object: str = "list"


# ============== 系统API模型 ==============

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    timestamp: datetime


class VersionResponse(BaseModel):
    """版本响应"""
    version: str
    name: str = "TW AI 节能器"


class StatsResponse(BaseModel):
    """统计响应"""
    connections: int
    sessions: int
    skills: int
    backups: int


class LogEntryModel(BaseModel):
    """日志条目"""
    timestamp: datetime
    event: str
    user_id: str
    ip: str
    details: Dict[str, Any]


class LogsResponse(BaseModel):
    """日志响应"""
    data: List[LogEntryModel]
    total: int
    page: int
    limit: int
