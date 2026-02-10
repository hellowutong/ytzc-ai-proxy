# 后端详细设计文档

**项目名称**: ytzc-ai-proxy (AI网关系统)  
**技术栈**: Python 3.11 + FastAPI  
**文档版本**: 1.0  
**最后更新**: 2026-02-09

---

## 1. 系统架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层                                  │
│  - ChatBox AI (配置proxy_key)                                   │
│  - frontend WebChat测试页                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI后端 (Port 8000)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────┐        ┌──────────────────┐             │
│   │  /proxy/ai/v1/*  │        │  /admin/ai/v1/*  │             │
│   │  虚拟AI代理API    │        │  后台管理API      │             │
│   ├──────────────────┤        ├──────────────────┤             │
│   │  • chat          │        │  • config        │             │
│   │  • models        │        │  • models        │             │
│   │  • embeddings    │        │  • skills        │             │
│   │                  │        │  • knowledge     │             │
│   │  认证: proxy_key │        │  • media         │             │
│   │  流式: SSE       │        │  • rss           │             │
│   │                  │        │  • logs          │             │
│   │                  │        │  • raw-data      │             │
│   └──────────────────┘        └──────────────────┘             │
│           │                            │                       │
│           ▼                            ▼                       │
│   ┌──────────────────┐        ┌──────────────────┐             │
│   │   模型路由引擎    │        │   Skill管理器    │             │
│   │                  │        │                  │             │
│   │  • 关键词匹配    │        │  • 动态加载      │             │
│   │  • 意图识别      │        │  • 版本管理      │             │
│   │  • 强制模式      │        │  • 热重载        │             │
│   └──────────────────┘        └──────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
│   外部API     │    │    数据存储层     │   │   服务组件    │
├──────────────┤    ├──────────────────┤   ├──────────────┤
│ SiliconFlow  │    │ MongoDB          │   │ Redis        │
│ OpenAI       │    │  - 对话历史      │   │  - 会话缓存  │
│ Ollama       │    │  - 配置数据      │   │  - 配置缓存  │
│              │    │  - 操作日志      │   │  - 任务队列  │
│              │    │                  │   │              │
│              │    │ Qdrant           │   │ Whisper      │
│              │    │  - 向量库        │   │  - 音频转录  │
│              │    │  - 知识检索      │   │  - 视频转录  │
└──────────────┘    └──────────────────┘   └──────────────┘
```

### 1.2 核心组件职责

| 组件 | 职责 | 技术实现 |
|------|------|----------|
| **API Router** | 路由分发、请求验证 | FastAPI APIRouter |
| **Auth Middleware** | proxy_key验证 | 自定义中间件 |
| **Model Router** | 智能路由决策 | Skill驱动 |
| **Skill Manager** | Skill加载、执行、重载 | 动态导入 + 缓存 |
| **Config Manager** | 配置读取、热重载 | YAML + Watchdog |
| **Conversation Manager** | 对话CRUD、持久化 | MongoDB |
| **Knowledge Manager** | 知识提取、向量存储 | Qdrant + Embedding |
| **Media Processor** | 音视频转录 | Whisper + Redis队列 |
| **RSS Fetcher** | RSS抓取、内容提取 | Feedparser + Readability |
| **Logger** | 日志记录、查询 | MongoDB + 文件 |

---

## 2. 存储层抽象架构（可替换设计）

### 2.1 设计目标

**问题**: MongoDB/Qdrant/Redis 未来可能被同类型产品替换

**解决方案**: 使用 Repository + Adapter + Factory 模式进行抽象封装

**优势**:
- 业务代码与存储实现解耦
- 通过配置文件切换存储类型
- 新增存储支持只需实现接口

### 2.2 抽象接口层

#### 2.2.1 文档存储接口（替代MongoDB）

```python
# core/repositories/interfaces.py

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

class StorageType(str, Enum):
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    DYNAMODB = "dynamodb"

class IDocumentRepository(ABC):
    """文档存储抽象接口"""
    
    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """关闭连接"""
        pass
    
    @abstractmethod
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """插入单条文档，返回ID"""
        pass
    
    @abstractmethod
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查询单条"""
        pass
    
    @abstractmethod
    async def find_many(
        self, 
        collection: str, 
        query: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """查询多条，返回数据和总数"""
        pass
    
    @abstractmethod
    async def update_one(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        update: Dict[str, Any]
    ) -> bool:
        """更新单条"""
        pass
    
    @abstractmethod
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """删除单条"""
        pass
```

#### 2.2.2 向量存储接口（替代Qdrant）

```python
class VectorDBType(str, Enum):
    QDRANT = "qdrant"
    MILVUS = "milvus"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"

class IVectorRepository(ABC):
    """向量存储抽象接口"""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def create_collection(
        self, 
        name: str, 
        dimension: int, 
        distance: str = "cosine"
    ) -> None:
        """创建集合"""
        pass
    
    @abstractmethod
    async def upsert(
        self, 
        collection: str, 
        vectors: List[Dict[str, Any]]
    ) -> None:
        """
        插入/更新向量
        vectors: [{"id": "uuid", "vector": [0.1, ...], "payload": {...}}]
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        pass
    
    @abstractmethod
    async def delete(self, collection: str, ids: List[str]) -> None:
        """删除向量"""
        pass
```

#### 2.2.3 缓存接口（替代Redis）

```python
class CacheType(str, Enum):
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"

class ICacheRepository(ABC):
    """缓存抽象接口"""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        """设置缓存"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存"""
        pass
    
    @abstractmethod
    async def lpush(self, queue: str, value: str) -> None:
        """队列-左侧推入"""
        pass
    
    @abstractmethod
    async def rpop(self, queue: str, timeout: int = 0) -> Optional[str]:
        """队列-右侧弹出（阻塞）"""
        pass
```

### 2.3 工厂模式实现

```python
# core/repositories/factory.py

class RepositoryFactory:
    """存储仓库工厂 - 根据配置创建对应实现"""
    
    _document_impls = {}
    _vector_impls = {}
    _cache_impls = {}
    
    @classmethod
    def register_document(cls, storage_type: StorageType, impl_class: type):
        """注册文档存储实现"""
        cls._document_impls[storage_type] = impl_class
    
    @classmethod
    def create_document_repository(cls, config: Dict[str, Any]) -> IDocumentRepository:
        """创建文档存储仓库"""
        storage_type = StorageType(config["type"])
        impl_class = cls._document_impls.get(storage_type)
        
        if not impl_class:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        
        return impl_class(**{k: v for k, v in config.items() if k != "type"})
    
    @classmethod
    def create_vector_repository(cls, config: Dict[str, Any]) -> IVectorRepository:
        """创建向量存储仓库"""
        vector_type = VectorDBType(config["type"])
        impl_class = cls._vector_impls.get(vector_type)
        
        if not impl_class:
            raise ValueError(f"不支持的向量数据库: {vector_type}")
        
        return impl_class(**{k: v for k, v in config.items() if k != "type"})
    
    @classmethod
    def create_cache_repository(cls, config: Dict[str, Any]) -> ICacheRepository:
        """创建缓存仓库"""
        cache_type = CacheType(config["type"])
        impl_class = cls._cache_impls.get(cache_type)
        
        if not impl_class:
            raise ValueError(f"不支持的缓存类型: {cache_type}")
        
        return impl_class(**{k: v for k, v in config.items() if k != "type"})

# 注册默认实现
from .mongodb_adapter import MongoDBAdapter
from .qdrant_adapter import QdrantAdapter
from .redis_adapter import RedisAdapter

RepositoryFactory.register_document(StorageType.MONGODB, MongoDBAdapter)
RepositoryFactory.register_vector(VectorDBType.QDRANT, QdrantAdapter)
RepositoryFactory.register_cache(CacheType.REDIS, RedisAdapter)
```

### 2.4 配置驱动的存储切换

```yaml
# config.yml 中的存储配置

storage:
  document:
    type: mongodb           # 可选: postgresql, mysql, dynamodb
    host: "mongo"
    port: 27017
    database: "ai_gateway"
    username: "admin"
    password: "password"
    
  vector:
    type: qdrant            # 可选: milvus, pinecone, weaviate
    host: "qdrant"
    port: 6333
    collection: "knowledge_base"
    
  cache:
    type: redis             # 可选: rabbitmq, kafka
    host: "redis"
    port: 6379
    db: 0
```

```python
# 初始化代码示例

from core.repositories.factory import RepositoryFactory
from core.config import config_manager

# 读取配置并创建仓库
doc_repo = RepositoryFactory.create_document_repository(
    config_manager.get("storage.document")
)
vector_repo = RepositoryFactory.create_vector_repository(
    config_manager.get("storage.vector")
)
cache_repo = RepositoryFactory.create_cache_repository(
    config_manager.get("storage.cache")
)

# 连接
await doc_repo.connect()
await vector_repo.connect()
await cache_repo.connect()
```

### 2.5 知识提取抽象（预留OpenClaw扩展）

```python
# core/extraction/interfaces.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class ExtractorType(str, Enum):
    SKILL = "skill"           # 当前实现
    OPENCLAW = "openclaw"     # 未来扩展
    HYBRID = "hybrid"         # 混合模式

@dataclass
class KnowledgeChunk:
    """知识片段"""
    id: str
    content: str
    source: str
    confidence: float
    entities: List[Dict]
    relationships: List[Dict]      # 预留：知识图谱关系
    created_at: str
    metadata: Dict[str, Any]

@dataclass
class ExtractionResult:
    """提取结果"""
    chunks: List[KnowledgeChunk]
    total_chunks: int
    extracted_at: str
    extractor_type: ExtractorType
    processing_time_ms: int
    # 预留OpenClaw字段
    knowledge_graph_updated: bool = False
    conflicts_detected: Optional[List[Dict]] = None

class IKnowledgeExtractor(ABC):
    """知识提取器抽象接口"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化"""
        pass
    
    @abstractmethod
    async def extract(
        self, 
        text: str, 
        context: Dict[str, Any]
    ) -> ExtractionResult:
        """从文本中提取知识"""
        pass
    
    @abstractmethod
    async def classify_topic(
        self,
        text: str,
        topics: List[str]
    ) -> Optional[str]:
        """主题分类"""
        pass

# 当前Skill实现
class SkillKnowledgeExtractor(IKnowledgeExtractor):
    """基于Skill的知识提取器"""
    
    def __init__(self, skill_manager: SkillManager):
        self.skill_manager = skill_manager
    
    async def initialize(self) -> None:
        pass
    
    async def extract(self, text: str, context: Dict[str, Any]) -> ExtractionResult:
        # 调用Skill执行知识提取
        result = await self.skill_manager.execute(
            "knowledge", "简单提取",
            text=text, **context
        )
        
        return ExtractionResult(
            chunks=[KnowledgeChunk(**chunk) for chunk in result.get("chunks", [])],
            total_chunks=len(result.get("chunks", [])),
            extracted_at=datetime.now().isoformat(),
            extractor_type=ExtractorType.SKILL,
            processing_time_ms=result.get("duration_ms", 0)
        )
    
    async def classify_topic(self, text: str, topics: List[str]) -> Optional[str]:
        result = await self.skill_manager.execute(
            "knowledge", "主题分类",
            text=text, topics=topics
        )
        return result.get("topic")

# 工厂
class KnowledgeExtractorFactory:
    """知识提取器工厂"""
    
    _extractors = {
        ExtractorType.SKILL: SkillKnowledgeExtractor,
        # ExtractorType.OPENCLAW: OpenClawExtractor,  # 未来扩展
    }
    
    @classmethod
    def create(cls, extractor_type: ExtractorType, **kwargs) -> IKnowledgeExtractor:
        impl_class = cls._extractors.get(extractor_type)
        if not impl_class:
            raise ValueError(f"未知的提取器类型: {extractor_type}")
        return impl_class(**kwargs)
    
    @classmethod
    def register(cls, extractor_type: ExtractorType, impl_class: type):
        """注册新的提取器（扩展点）"""
        cls._extractors[extractor_type] = impl_class
```

---

## 3. 目录结构

```
backend/
├── main.py                      # FastAPI应用入口
├── requirements.txt             # 依赖列表
├── pyproject.toml              # 项目配置（可选）
│
├── api/                        # API路由层
│   ├── __init__.py
│   ├── dependencies.py         # 依赖注入（数据库连接等）
│   ├── proxy/                  # 虚拟AI代理API
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── chat.py         # POST /chat/completions
│   │       ├── models.py       # GET /models
│   │       └── embeddings.py   # POST /embeddings
│   │
│   └── admin/                  # 后台管理API
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── dashboard.py    # 看板统计/健康检查
│           ├── config.py       # 配置管理
│           ├── models.py       # 虚拟模型CRUD
│           ├── skills.py       # Skill管理
│           ├── conversations.py # 对话历史
│           ├── knowledge.py    # 知识库管理
│           ├── media.py        # 媒体处理
│           ├── rss.py          # RSS订阅
│           ├── logs.py         # 日志查询
│           └── raw_data.py     # 原始数据
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   ├── config.py              # 配置管理器
│   ├── security.py            # 安全工具（proxy_key验证）
│   │
│   ├── repositories/          # 存储层抽象（新增）
│   │   ├── __init__.py
│   │   ├── interfaces.py      # 抽象接口定义
│   │   ├── factory.py         # 仓库工厂
│   │   ├── mongodb_adapter.py # MongoDB适配器
│   │   ├── qdrant_adapter.py  # Qdrant适配器
│   │   ├── redis_adapter.py   # Redis适配器
│   │   └── postgresql_adapter.py  # PostgreSQL适配器（预留）
│   │
│   ├── extraction/            # 知识提取抽象（新增）
│   │   ├── __init__.py
│   │   ├── interfaces.py      # 抽象接口定义
│   │   ├── factory.py         # 提取器工厂
│   │   └── skill_extractor.py # Skill提取器实现
│   │
│   ├── skill_manager.py       # Skill管理器
│   ├── skill_validator.py     # Skill验证器
│   ├── skill_executor.py      # Skill执行器
│   ├── skill_logger.py        # Skill日志记录
│   ├── model_router.py        # 模型路由引擎
│   ├── conversation_manager.py # 对话管理器
│   ├── knowledge_manager.py   # 知识库管理器
│   ├── media_processor.py     # 媒体处理器
│   ├── rss_fetcher.py         # RSS抓取器
│   └── exceptions.py          # 自定义异常
│
├── models/                     # 数据模型（Pydantic）
│   ├── __init__.py
│   ├── base.py                # 基础模型
│   ├── conversation.py        # 对话模型
│   ├── document.py            # 知识文档模型
│   ├── media.py               # 媒体文件模型
│   ├── rss.py                 # RSS模型
│   ├── log.py                 # 日志模型
│   └── config.py              # 配置模型
│
├── services/                   # 服务层（外部API调用）
│   ├── __init__.py
│   ├── llm_service.py         # LLM API调用（SiliconFlow等）
│   ├── embedding_service.py   # Embedding服务
│   ├── whisper_service.py     # Whisper服务
│   └── search_service.py      # 搜索服务（Searxng等）
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── yaml_loader.py         # YAML加载工具
│   ├── file_utils.py          # 文件操作工具
│   ├── text_utils.py          # 文本处理工具
│   └── datetime_utils.py      # 时间处理工具
│
└── tests/                      # 测试（实际在../test/backend/）
    └── conftest.py            # pytest配置
```

---

## 4. 核心模块设计

### 4.1 配置管理器 (ConfigManager)
│   │       └── embeddings.py   # POST /embeddings
│   │
│   └── admin/                  # 后台管理API
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── dashboard.py    # 看板统计/健康检查
│           ├── config.py       # 配置管理
│           ├── models.py       # 虚拟模型CRUD
│           ├── skills.py       # Skill管理
│           ├── conversations.py # 对话历史
│           ├── knowledge.py    # 知识库管理
│           ├── media.py        # 媒体处理
│           ├── rss.py          # RSS订阅
│           ├── logs.py         # 日志查询
│           └── raw_data.py     # 原始数据
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   ├── config.py              # 配置管理器
│   ├── security.py            # 安全工具（proxy_key验证）
│   ├── database.py            # 数据库连接管理
│   ├── skill_manager.py       # Skill管理器
│   ├── skill_validator.py     # Skill验证器
│   ├── skill_executor.py      # Skill执行器
│   ├── skill_logger.py        # Skill日志记录
│   ├── model_router.py        # 模型路由引擎
│   ├── conversation_manager.py # 对话管理器
│   ├── knowledge_manager.py   # 知识库管理器
│   ├── media_processor.py     # 媒体处理器
│   ├── rss_fetcher.py         # RSS抓取器
│   └── exceptions.py          # 自定义异常
│
├── models/                     # 数据模型（Pydantic）
│   ├── __init__.py
│   ├── base.py                # 基础模型
│   ├── conversation.py        # 对话模型
│   ├── document.py            # 知识文档模型
│   ├── media.py               # 媒体文件模型
│   ├── rss.py                 # RSS模型
│   ├── log.py                 # 日志模型
│   └── config.py              # 配置模型
│
├── services/                   # 服务层（外部API调用）
│   ├── __init__.py
│   ├── llm_service.py         # LLM API调用（SiliconFlow等）
│   ├── embedding_service.py   # Embedding服务
│   ├── whisper_service.py     # Whisper服务
│   └── search_service.py      # 搜索服务（Searxng等）
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── yaml_loader.py         # YAML加载工具
│   ├── file_utils.py          # 文件操作工具
│   ├── text_utils.py          # 文本处理工具
│   └── datetime_utils.py      # 时间处理工具
│
└── tests/                      # 测试（实际在../test/backend/）
    └── conftest.py            # pytest配置
```

---

### 4.1 配置管理器 (ConfigManager)

**职责**: 管理config.yml的读取、验证、热重载

**类设计**:
```python
class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}
    _file_path: str = "./config.yml"
    _last_modified: float = 0
    
    def __new__(cls):
        # 单例模式
        
    def load_config(self) -> Dict[str, Any]:
        # 加载YAML文件
        
    def validate_config(self, config: Dict) -> Tuple[bool, List[str]]:
        # 使用Pydantic模型验证配置
        
    def reload_config(self) -> bool:
        # 热重载配置
        
    def get(self, key: str, default=None) -> Any:
        # 获取配置项（支持点号路径）
        # 如: get("ai-gateway.virtual_models.demo1.small.api_key")
        
    def set(self, key: str, value: Any) -> bool:
        # 设置配置项并保存到文件
        
    def watch_config(self):
        # 使用watchdog监听文件变化
```

**配置结构** (对应config.yml):
```python
class AppConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

class StorageConfig(BaseModel):
    mongodb: MongoDBConfig
    qdrant: QdrantConfig
    redis: RedisConfig

class VirtualModelConfig(BaseModel):
    proxy_key: str
    base_url: str
    current: str  # "small" | "big"
    force_current: bool
    use: bool
    small: ModelEndpointConfig
    big: ModelEndpointConfig
    knowledge: KnowledgeFeatureConfig
    web_search: WebSearchFeatureConfig

class AIGatewayConfig(BaseModel):
    router: RouterConfig
    virtual_models: Dict[str, VirtualModelConfig]
    knowledge: KnowledgeConfig
    rss: RSSConfig
    media: MediaConfig
    log: LogConfig
```

---

### 3.2 Skill管理器 (SkillManager)

**职责**: Skill的发现、加载、验证、执行、重载

**类设计**:
```python
class SkillManager:
    _skills: Dict[str, SkillInfo] = {}  # category/name -> SkillInfo
    _config_manager: ConfigManager
    
    def __init__(self, config_manager: ConfigManager):
        self._config_manager = config_manager
        self._load_all_skills()
    
    def _load_all_skills(self):
        # 遍历skill/system/和skill/custom/目录
        # 根据config.yml中的配置决定加载哪些版本
        
    def _load_skill(self, category: str, name: str, 
                    is_custom: bool, version: str) -> Optional[SkillInfo]:
        # 加载单个Skill
        # 1. 读取SKILL.md
        # 2. 验证YAML frontmatter
        # 3. 如果有.py文件，动态导入
        
    def get_skill(self, category: str, name: str) -> Optional[SkillInfo]:
        # 获取Skill信息
        
    async def execute(self, category: str, name: str, 
                     **kwargs) -> Dict[str, Any]:
        # 执行Skill
        # 1. 验证输入参数（JSON Schema）
        # 2. 调用执行函数
        # 3. 验证输出结果（JSON Schema）
        # 4. 记录执行日志
        # 5. 返回结果
        
    def reload_skill(self, category: str, name: str) -> bool:
        # 重载单个Skill
        
    def reload_all(self) -> Dict[str, int]:
        # 重载所有Skill
        # 返回统计信息：成功数、失败数
        
    def get_skill_list(self) -> List[SkillListItem]:
        # 获取Skill列表（用于前端展示）
```

**Skill信息结构**:
```python
class SkillMetadata(BaseModel):
    name: str
    description: str
    type: Literal["rule-based", "llm-based", "hybrid"]
    priority: int = 1
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    # LLM-based特有
    model: Optional[str] = None
    # Rule-based特有
    rules: Optional[List[Dict]] = None

class SkillInfo:
    category: str
    name: str
    metadata: SkillMetadata
    is_custom: bool
    version: str
    file_path: str
    has_py_file: bool
    execute_func: Optional[Callable] = None
```

---

### 3.3 模型路由引擎 (ModelRouter)

**职责**: 根据输入决定使用大模型还是小模型

**类设计**:
```python
class ModelRouter:
    _skill_manager: SkillManager
    _config_manager: ConfigManager
    _redis: Redis
    
    def __init__(self, skill_manager, config_manager, redis):
        self._skill_manager = skill_manager
        self._config_manager = config_manager
        self._redis = redis
    
    async def route(self, virtual_model: str, 
                   user_input: str,
                   conversation_id: Optional[str] = None) -> RouteResult:
        # 模型路由决策
        # 1. 检查是否强制模式
        config = self._config_manager.get(f"ai-gateway.virtual_models.{virtual_model}")
        if config.get("force_current"):
            return RouteResult(model_type=config["current"], reason="强制模式")
        
        # 2. 获取会话上下文
        context = await self._get_conversation_context(conversation_id)
        
        # 3. 尝试关键词路由（最高优先级）
        keyword_result = await self._try_keyword_router(user_input)
        if keyword_result:
            return keyword_result
        
        # 4. 尝试意图识别路由
        intent_result = await self._try_intent_router(user_input, context)
        if intent_result and intent_result.confidence > 0.8:
            return intent_result
        
        # 5. 使用默认模型
        return RouteResult(
            model_type=config["current"],
            reason=f"置信度{intent_result.confidence if intent_result else 'N/A'}过低，使用默认模型"
        )
    
    async def _try_keyword_router(self, user_input: str) -> Optional[RouteResult]:
        # 执行关键词路由Skill
        result = await self._skill_manager.execute(
            "router", "关键词路由",
            user_input=user_input
        )
        if result.get("target"):
            return RouteResult(
                model_type=result["target"],
                matched_rule=result.get("matched_rule"),
                reason=f"关键词匹配: {result.get('matched_rule')}"
            )
        return None
    
    async def _try_intent_router(self, user_input: str, 
                                 context: str) -> Optional[RouteResult]:
        # 执行意图识别Skill
        result = await self._skill_manager.execute(
            "router", "意图识别",
            user_input=user_input,
            context=context
        )
        if result.get("model_type") and not result.get("fallback"):
            return RouteResult(
                model_type=result["model_type"],
                confidence=result.get("confidence", 0),
                reason=result.get("reason", "")
            )
        return None
```

---

### 3.4 对话管理器 (ConversationManager)

**职责**: 对话的创建、查询、保存、删除

**类设计**:
```python
class ConversationManager:
    _mongodb: AsyncIOMotorClient
    _redis: Redis
    _config_manager: ConfigManager
    
    def __init__(self, mongodb, redis, config_manager):
        self._mongodb = mongodb
        self._redis = redis
        self._config_manager = config_manager
        self._db = mongodb[config_manager.get("storage.mongodb.database")]
        self._collection = self._db["conversations"]
    
    async def create_conversation(self, virtual_model: str) -> str:
        # 创建新会话
        conversation_id = generate_uuid()
        doc = {
            "_id": conversation_id,
            "virtual_model": virtual_model,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0
        }
        await self._collection.insert_one(doc)
        return conversation_id
    
    async def add_message(self, conversation_id: str, 
                         role: str, 
                         content: str,
                         metadata: Optional[Dict] = None) -> bool:
        # 添加消息到会话
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        await self._collection.update_one(
            {"_id": conversation_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {"message_count": 1}
            }
        )
        return True
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        # 获取会话详情
        doc = await self._collection.find_one({"_id": conversation_id})
        if doc:
            return Conversation(**doc)
        return None
    
    async def list_conversations(self, 
                                 virtual_model: Optional[str] = None,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None,
                                 keyword: Optional[str] = None,
                                 limit: int = 20,
                                 offset: int = 0) -> Tuple[List[Conversation], int]:
        # 列表查询（支持筛选、分页）
        query = {}
        if virtual_model:
            query["virtual_model"] = virtual_model
        if start_time or end_time:
            query["updated_at"] = {}
            if start_time:
                query["updated_at"]["$gte"] = start_time
            if end_time:
                query["updated_at"]["$lte"] = end_time
        if keyword:
            query["$text"] = {"$search": keyword}  # 需要文本索引
        
        cursor = self._collection.find(query).sort("updated_at", -1).skip(offset).limit(limit)
        conversations = [Conversation(**doc) async for doc in cursor]
        total = await self._collection.count_documents(query)
        return conversations, total
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        # 删除会话
        result = await self._collection.delete_one({"_id": conversation_id})
        return result.deleted_count > 0
```

---

### 3.5 知识库管理器 (KnowledgeManager)

**职责**: 文档管理、向量化、检索

**类设计**:
```python
class KnowledgeManager:
    _mongodb: AsyncIOMotorClient
    _qdrant: QdrantClient
    _embedding_service: EmbeddingService
    _config_manager: ConfigManager
    
    def __init__(self, mongodb, qdrant, embedding_service, config_manager):
        self._mongodb = mongodb
        self._qdrant = qdrant
        self._embedding_service = embedding_service
        self._config_manager = config_manager
        self._db = mongodb[config_manager.get("storage.mongodb.database")]
        self._docs_collection = self._db["knowledge_docs"]
    
    async def upload_document(self, 
                             file: UploadFile,
                             virtual_model: str,
                             is_shared: bool,
                             chunk_size: int = 500,
                             overlap: int = 50,
                             language: str = "zh") -> Document:
        # 上传文档流程
        # 1. 保存文件到upload/textfile/
        # 2. 提取文本内容
        # 3. 分段处理
        # 4. 向量化并存储到Qdrant
        # 5. 保存元数据到MongoDB
        
    async def vectorize_document(self, document_id: str) -> bool:
        # 重新向量化文档
        
    async def search(self, 
                    query: str, 
                    virtual_model: Optional[str] = None,
                    threshold: float = 0.76,
                    top_k: int = 5) -> List[SearchResult]:
        # 向量检索
        # 1. 获取query的embedding
        # 2. 在Qdrant中搜索
        # 3. 过滤threshold
        # 4. 返回结果
        
    async def extract_knowledge(self, text: str, virtual_model: str) -> List[KnowledgeChunk]:
        # 执行知识提取Skill
        skill_result = await skill_manager.execute(
            "knowledge", "简单提取",
            text=text,
            virtual_model=virtual_model
        )
        return skill_result.get("chunks", [])
```

---

### 3.6 媒体处理器 (MediaProcessor)

**职责**: 音视频上传、转录、知识提取

**类设计**:
```python
class MediaProcessor:
    _mongodb: AsyncIOMotorClient
    _redis: Redis
    _whisper_service: WhisperService
    _knowledge_manager: KnowledgeManager
    
    def __init__(self, mongodb, redis, whisper_service, knowledge_manager):
        self._mongodb = mongodb
        self._redis = redis
        self._whisper_service = whisper_service
        self._knowledge_manager = knowledge_manager
        self._db = mongodb["ai_gateway"]
        self._collection = self._db["media_files"]
    
    async def upload_file(self, 
                         file: UploadFile,
                         media_type: str,  # video/audio/text
                         processor: str = "whisper",
                         model: str = "base",
                         language: str = "zh",
                         auto_transcribe: bool = True) -> MediaFile:
        # 上传文件
        # 1. 保存到upload/{media_type}/
        # 2. 创建MongoDB记录
        # 3. 如果auto_transcribe，提交转录任务到Redis队列
        
    async def submit_transcription_task(self, media_id: str) -> bool:
        # 提交转录任务到Redis队列
        await self._redis.lpush("queue:transcription", media_id)
        await self._collection.update_one(
            {"_id": media_id},
            {"$set": {"status": "pending", "updated_at": datetime.utcnow()}}
        )
        return True
    
    async def process_transcription(self, media_id: str):
        # 转录工作进程执行
        # 1. 获取媒体文件信息
        # 2. 调用Whisper转录
        # 3. 保存转录文本
        # 4. 如果配置了自动知识提取，调用KnowledgeManager
        # 5. 更新状态为completed
        
    async def download_from_url(self, 
                               url: str,
                               media_type: str,
                               **transcription_options) -> MediaFile:
        # 从URL下载并处理
```

---

### 3.7 RSS抓取器 (RSSFetcher)

**职责**: RSS订阅管理、抓取、内容提取、知识提取

**类设计**:
```python
class RSSFetcher:
    _mongodb: AsyncIOMotorClient
    _knowledge_manager: KnowledgeManager
    _http_client: httpx.AsyncClient
    
    def __init__(self, mongodb, knowledge_manager):
        self._mongodb = mongodb
        self._knowledge_manager = knowledge_manager
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._db = mongodb["ai_gateway"]
        self._subscriptions_collection = self._db["rss_subscriptions"]
        self._articles_collection = self._db["rss_articles"]
    
    async def fetch_feed(self, subscription_id: str) -> FetchResult:
        # 抓取单个RSS订阅
        # 1. 获取订阅信息
        sub = await self._subscriptions_collection.find_one({"_id": subscription_id})
        
        # 2. 解析RSS feed
        feed = feedparser.parse(sub["url"])
        
        # 3. 遍历文章
        for entry in feed.entries:
            # 4. 访问原文链接，爬取完整内容
            article_content = await self._fetch_full_content(entry.link)
            
            # 5. 保存到MongoDB
            article = {
                "_id": generate_uuid(),
                "subscription_id": subscription_id,
                "title": entry.title,
                "url": entry.link,
                "content": article_content["cleaned"],
                "raw_content": article_content["raw"],
                "published_at": parse_date(entry.published),
                "fetched_at": datetime.utcnow(),
                "fetch_status": article_content["status"],
                "is_read": False,
                "knowledge_extracted": False
            }
            await self._articles_collection.insert_one(article)
            
            # 6. 触发知识提取
            if sub.get("auto_extract", True):
                await self._extract_article_knowledge(article["_id"], sub["virtual_model"])
        
        # 7. 更新最后抓取时间
        await self._subscriptions_collection.update_one(
            {"_id": subscription_id},
            {"$set": {"last_fetch_time": datetime.utcnow()}}
        )
        
        return FetchResult(articles_fetched=len(feed.entries))
    
    async def _fetch_full_content(self, url: str) -> Dict[str, str]:
        # 爬取完整文章内容
        # 1. 发送HTTP请求获取HTML
        response = await self._http_client.get(url)
        raw_html = response.text
        
        # 2. 使用readability-lxml提取正文
        doc = Document(raw_html)
        cleaned_content = doc.summary()
        title = doc.short_title()
        
        # 3. 转换为Markdown（可选）
        markdown_content = html2text.html2text(cleaned_content)
        
        return {
            "raw": raw_html,
            "cleaned": cleaned_content,
            "markdown": markdown_content,
            "title": title,
            "status": "full_content"
        }
```

---

## 5. 数据库设计

### 4.1 MongoDB Collections

#### conversations - 对话集合
```javascript
{
  "_id": "conv_uuid",
  "virtual_model": "demo1",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": ISODate("2026-02-09T14:00:00Z"),
      "metadata": {}
    },
    {
      "role": "assistant", 
      "content": "你好！",
      "timestamp": ISODate("2026-02-09T14:00:05Z"),
      "metadata": {
        "model_used": "small",
        "knowledge_references": [...],
        "routing_decision": {...}
      }
    }
  ],
  "message_count": 10,
  "created_at": ISODate("2026-02-09T14:00:00Z"),
  "updated_at": ISODate("2026-02-09T14:30:00Z"),
  "has_knowledge_reference": true
}

// 索引
// - { virtual_model: 1, updated_at: -1 }
// - { updated_at: -1 }
// - { has_knowledge_reference: 1 }
// - 文本索引: { "messages.content": "text" }
```

#### knowledge_docs - 知识文档集合
```javascript
{
  "_id": "doc_uuid",
  "filename": "设计文档.pdf",
  "type": "pdf",  // pdf/txt/doc/jpg
  "source": "upload",  // upload/rss/conversation
  "virtual_model": "demo1",
  "is_shared": true,
  "vectorized": true,
  "chunk_count": 5,
  "file_path": "./upload/textfile/xxx.pdf",
  "file_size": 1024000,
  "upload_time": ISODate("2026-02-09T10:00:00Z"),
  "chunks": [
    {
      "index": 0,
      "content": "第一段内容...",
      "vector_id": "uuid_in_qdrant",
      "vectorized": true
    }
  ]
}

// 索引
// - { virtual_model: 1, source: 1 }
// - { vectorized: 1 }
// - { upload_time: -1 }
```

#### media_files - 媒体文件集合
```javascript
{
  "_id": "media_uuid",
  "filename": "会议录音.mp3",
  "type": "audio",  // video/audio/text
  "status": "completed",  // pending/processing/completed/failed
  "file_path": "./upload/audio/xxx.mp3",
  "file_size": 5242880,
  "transcription": {
    "processor": "whisper",
    "model": "base",
    "language": "zh",
    "text": "完整转录文本...",
    "segments": [...],
    "completed_at": ISODate("2026-02-09T14:30:00Z")
  },
  "knowledge_extracted": true,
  "knowledge_doc_ids": ["doc_uuid_1", "doc_uuid_2"],
  "upload_time": ISODate("2026-02-09T14:00:00Z"),
  "updated_at": ISODate("2026-02-09T14:30:00Z")
}

// 索引
// - { type: 1, status: 1 }
// - { status: 1, upload_time: -1 }
```

#### rss_subscriptions - RSS订阅集合
```javascript
{
  "_id": "rss_uuid",
  "name": "AI新闻",
  "url": "https://news.ai.com/feed.xml",
  "enabled": true,
  "fetch_interval": 30,  // 分钟
  "retention_days": 30,
  "default_permanent": false,
  "virtual_model": "demo1",
  "article_count": 150,
  "last_fetch_time": ISODate("2026-02-09T14:00:00Z"),
  "created_at": ISODate("2026-01-01T00:00:00Z")
}
```

#### rss_articles - RSS文章集合
```javascript
{
  "_id": "article_uuid",
  "subscription_id": "rss_uuid",
  "title": "AI最新进展",
  "url": "https://news.ai.com/article/1",
  "content": "完整的文章内容...",
  "raw_content": "原始HTML...",
  "content_format": "markdown",
  "published_at": ISODate("2026-02-09T10:00:00Z"),
  "fetched_at": ISODate("2026-02-09T14:00:00Z"),
  "is_read": false,
  "knowledge_extracted": true,
  "knowledge_doc_ids": [...],
  "fetch_status": "full_content",  // full_content/summary_only/failed
  "fetch_method": "readability"
}

// 索引
// - { subscription_id: 1, fetched_at: -1 }
// - { is_read: 1 }
```

#### operation_logs - 操作日志集合
```javascript
{
  "_id": "log_uuid",
  "timestamp": ISODate("2026-02-09T14:30:00Z"),
  "type": "config",  // config/skill/model/media/rss
  "action": "更新虚拟模型配置",
  "details": {
    "model_name": "demo1",
    "changes": [...]
  },
  "status": "success",  // success/failed
  "operator": "admin",
  "ip_address": "127.0.0.1",
  "user_agent": "..."
}

// 索引
// - { timestamp: -1 }
// - { type: 1, timestamp: -1 }
// - { status: 1 }
```

### 4.2 Qdrant Collection

**Collection名称**: `knowledge_base`

**向量配置**:
- 向量维度: 1024 (BAAI/bge-m3)
- 距离度量: Cosine

**Payload字段**:
```javascript
{
  "document_id": "doc_uuid",
  "chunk_index": 0,
  "virtual_model": "demo1",
  "is_shared": true,
  "source": "upload",
  "created_at": "2026-02-09T10:00:00Z",
  "text_preview": "内容前100字..."
}
```

**索引**:
- `virtual_model` - keyword索引
- `is_shared` - bool索引
- `source` - keyword索引

### 4.3 Redis Keys

```
# 配置缓存
config:hash                    # config.yml的hash缓存

# 虚拟模型
virtual_model:{name}:current   # 当前模型（small/big）
virtual_model:{name}:force     # 是否强制

# 会话
conversation:{id}:messages     # 活跃会话消息缓存（TTL: 1小时）

# 任务队列
queue:transcription            # 转录任务队列
queue:knowledge_extraction     # 知识提取任务队列
queue:rss_fetch                # RSS抓取任务队列

# Skill执行缓存（防止重复执行）
skill:execution:{log_id}       # Skill执行结果缓存

# 速率限制（预留）
rate_limit:proxy_key:{key}     # proxy_key请求计数
```

---

## 6. API实现规划

### 5.1 路由注册 (main.py)

```python
from fastapi import FastAPI
from api.proxy.v1 import chat, models, embeddings
from api.admin.v1 import (
    dashboard, config, models as admin_models,
    skills, conversations, knowledge, media, rss, logs, raw_data
)

app = FastAPI(title="AI Gateway", version="1.0.0")

# 虚拟AI代理API
app.include_router(chat.router, prefix="/proxy/ai/v1", tags=["proxy"])
app.include_router(models.router, prefix="/proxy/ai/v1", tags=["proxy"])
app.include_router(embeddings.router, prefix="/proxy/ai/v1", tags=["proxy"])

# 后台管理API
app.include_router(dashboard.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(config.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(admin_models.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(skills.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(conversations.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(knowledge.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(media.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(rss.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(logs.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(raw_data.router, prefix="/admin/ai/v1", tags=["admin"])
```

### 5.2 依赖注入 (dependencies.py)

```python
from fastapi import Request

# 数据库连接依赖
async def get_mongodb():
    # 返回MongoDB连接
    
async def get_redis():
    # 返回Redis连接
    
async def get_qdrant():
    # 返回Qdrant连接

# 管理器依赖
async def get_config_manager():
    # 返回ConfigManager单例
    
async def get_skill_manager(config_manager=Depends(get_config_manager)):
    # 返回SkillManager单例
    
async def get_conversation_manager(mongodb=Depends(get_mongodb)):
    # 返回ConversationManager

# 代理认证依赖（仅用于/proxy/ai/*）
async def verify_proxy_key(request: Request):
    # 从Authorization头提取proxy_key
    # 验证是否存在于config.yml中
    # 返回virtual_model配置
```

### 5.3 关键API实现示例

**POST /proxy/ai/v1/chat/completions**:
```python
@router.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    virtual_model_config: dict = Depends(verify_proxy_key),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    model_router: ModelRouter = Depends(get_model_router),
    llm_service: LLMService = Depends(get_llm_service)
):
    # 1. 获取或创建会话
    conversation_id = extract_conversation_id(request.messages)
    if not conversation_id:
        conversation_id = await conversation_manager.create_conversation(
            virtual_model_config["name"]
        )
    
    # 2. 保存用户消息
    await conversation_manager.add_message(
        conversation_id, 
        "user", 
        request.messages[-1].content
    )
    
    # 3. 模型路由决策
    route_result = await model_router.route(
        virtual_model_config["name"],
        request.messages[-1].content,
        conversation_id
    )
    
    # 4. 知识库检索（如果启用）
    knowledge_chunks = []
    if virtual_model_config.get("knowledge", {}).get("enabled"):
        knowledge_chunks = await search_knowledge(
            request.messages[-1].content,
            virtual_model_config["name"]
        )
    
    # 5. 构建增强的prompt
    enhanced_messages = build_messages_with_context(
        request.messages,
        knowledge_chunks
    )
    
    # 6. 选择实际模型配置
    target_model = virtual_model_config[route_result.model_type]
    
    # 7. 调用LLM（流式或非流式）
    if request.stream:
        return StreamingResponse(
            stream_chat_response(
                target_model,
                enhanced_messages,
                conversation_id,
                conversation_manager
            ),
            media_type="text/event-stream"
        )
    else:
        response = await llm_service.chat(
            target_model,
            enhanced_messages
        )
        
        # 保存AI回复
        await conversation_manager.add_message(
            conversation_id,
            "assistant",
            response.content,
            metadata={
                "model_used": route_result.model_type,
                "routing_reason": route_result.reason
            }
        )
        
        return response
```

---

## 7. 关键流程设计

### 6.1 对话流程

```
1. 客户端发送 POST /proxy/ai/v1/chat/completions
   - Header: Authorization: Bearer {proxy_key}
   - Body: {model, messages, stream, ...}

2. 中间件验证proxy_key
   - 从config.yml查找对应的虚拟模型配置
   - 如果找不到，返回401错误

3. 创建或获取会话
   - 如果是新会话，创建conversation_id
   - 保存用户消息到MongoDB

4. 模型路由决策
   a. 检查是否强制模式
   b. 尝试关键词路由
   c. 尝试意图识别路由
   d. 使用默认模型

5. 知识库检索（如果启用）
   - 将用户查询embedding
   - 在Qdrant中搜索相似向量
   - 返回相关知识片段

6. 构建增强prompt
   - 系统提示 + 知识片段 + 历史消息 + 用户输入

7. 调用实际LLM API
   - 根据路由结果选择small/big模型配置
   - 调用SiliconFlow/OpenAI/Ollama

8. 流式响应（如果stream=true）
   - 使用SSE逐字返回
   - 保存完整回复到MongoDB

9. 记录日志
   - 记录到operation_logs
   - 记录到skill execution logs
```

### 6.2 Skill执行流程

```
1. 调用 skill_manager.execute(category, name, **kwargs)

2. 查找Skill
   - 根据config.yml决定使用system还是custom版本
   - 加载Skill元数据

3. 验证输入
   - 使用JSON Schema验证kwargs
   - 如果不通过，返回ValidationError

4. 执行Skill
   a. 如果是rule-based:
      - 直接执行规则逻辑
   b. 如果是llm-based:
      - 构建prompt
      - 调用LLM
      - 解析Tool Call结果

5. 验证输出
   - 使用JSON Schema验证result

6. 记录执行日志
   - 记录输入、输出、耗时、状态
   - 保存到MongoDB和文件

7. 返回结果
```

### 6.3 配置热重载流程

```
1. 用户调用 POST /admin/ai/v1/config/reload
   或 Watchdog检测到config.yml变化

2. 读取config.yml文件

3. 验证配置
   - 使用Pydantic模型验证结构
   - 检查必填字段
   - 检查格式正确性

4. 如果验证失败
   - 记录错误日志
   - 返回错误响应
   - 保持旧配置运行

5. 如果验证通过
   - 更新ConfigManager内部缓存
   - 通知所有依赖组件
   - 记录操作日志

6. 组件收到通知后
   - SkillManager: 重载受影响的Skill
   - ModelRouter: 更新路由规则
   - 其他组件: 刷新配置引用
```

---

## 8. 错误处理

### 7.1 异常类定义

```python
# core/exceptions.py

class AIGatewayException(Exception):
    """基础异常"""
    status_code = 500
    error_code = "internal_error"
    
class ProxyKeyInvalid(AIGatewayException):
    """proxy_key无效"""
    status_code = 401
    error_code = "authentication_error"
    
class VirtualModelNotFound(AIGatewayException):
    """虚拟模型不存在"""
    status_code = 404
    error_code = "model_not_found"
    
class SkillNotFound(AIGatewayException):
    """Skill不存在"""
    status_code = 404
    error_code = "skill_not_found"
    
class SkillValidationError(AIGatewayException):
    """Skill验证失败"""
    status_code = 400
    error_code = "skill_validation_error"
    
class ConfigValidationError(AIGatewayException):
    """配置验证失败"""
    status_code = 400
    error_code = "config_validation_error"
    
class LLMServiceError(AIGatewayException):
    """LLM服务调用失败"""
    status_code = 502
    error_code = "llm_service_error"
```

### 7.2 全局异常处理器

```python
@app.exception_handler(AIGatewayException)
async def ai_gateway_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": str(exc),
                "details": getattr(exc, "details", None)
            }
        }
    )
```

---

## 9. 日志设计

### 8.1 日志分类

| 日志类型 | 存储位置 | 内容 | 保留策略 |
|----------|----------|------|----------|
| **系统日志** | ./logs/skill/system.log | Skill加载、执行、错误 | 轮转，5个备份 |
| **执行日志** | ./logs/skill/execution_YYYYMMDD.log | 详细JSON执行记录 | 30天 |
| **操作日志** | MongoDB | 配置变更、Skill更新 | 30天 |

### 8.2 日志格式

**系统日志** (结构化):
```
2026-02-09 14:30:00 [INFO] skill.manager: Skill加载成功: router/意图识别@v1
2026-02-09 14:30:05 [ERROR] skill.executor: Skill执行失败: router/意图识别 - Connection timeout
```

**执行日志** (JSON Lines):
```json
{"timestamp":"2026-02-09T14:30:00Z","skill_category":"router","skill_name":"意图识别","duration_ms":120,"status":"success"}
```

---

## 10. 测试策略（TDD + 100%覆盖率）

### 10.1 测试驱动开发（TDD）流程

**必须严格遵循TDD红绿重构循环：**

```
1. 编写测试案例（JSON文件） → 2. 运行测试（失败/红色） → 3. 编写最小实现 → 4. 运行测试（通过/绿色） → 5. 重构优化
```

**开发流程：**
1. **需求分析** - 理解功能需求
2. **编写测试案例** - 将测试案例保存到JSON文件
3. **生成测试代码** - 根据JSON生成pytest测试函数
4. **运行测试** - 确保测试失败（红色）
5. **编写实现** - 编写最小代码使测试通过
6. **运行测试** - 确保测试通过（绿色）
7. **重构优化** - 优化代码结构和质量
8. **覆盖率检查** - 确保100%覆盖

### 10.2 测试案例JSON格式

**文件位置**: `test/backend/cases/{模块}/{功能}.test.json`

**JSON Schema:**
```json
{
  "test_suite": "skill_manager",
  "description": "Skill管理器测试套件",
  "author": "developer",
  "created_at": "2026-02-09",
  "test_cases": [
    {
      "id": "TC001",
      "name": "test_load_valid_skill",
      "description": "测试加载有效的Skill文件",
      "category": "unit",
      "priority": "P0",
      "tags": ["skill", "loading", "positive"],
      "preconditions": [
        "Skill文件存在于 skill/system/router/v1/关键词路由/SKILL.md"
      ],
      "inputs": {
        "category": "router",
        "name": "关键词路由",
        "version": "v1",
        "is_custom": false
      },
      "expected": {
        "success": true,
        "skill_name": "关键词路由",
        "skill_type": "rule-based",
        "has_py_file": false
      },
      "assertions": [
        "assert result.metadata.name == '关键词路由'",
        "assert result.metadata.type == 'rule-based'",
        "assert result.file_path is not None"
      ]
    },
    {
      "id": "TC002",
      "name": "test_load_invalid_skill_missing_required_field",
      "description": "测试加载缺少必填字段的Skill",
      "category": "unit",
      "priority": "P0",
      "tags": ["skill", "loading", "negative", "validation"],
      "preconditions": [
        "创建一个临时无效的SKILL.md文件"
      ],
      "inputs": {
        "category": "router",
        "name": "无效Skill",
        "skill_content": "---\nname: 无效\n# 缺少description和type字段\n---"
      },
      "expected": {
        "success": false,
        "error_type": "SkillValidationError",
        "error_message_contains": "description"
      },
      "assertions": [
        "assert not result.success",
        "assert 'description' in result.error_message"
      ]
    },
    {
      "id": "TC003",
      "name": "test_execute_skill_with_valid_input",
      "description": "测试使用有效输入执行Skill",
      "category": "unit",
      "priority": "P0",
      "tags": ["skill", "execution", "positive"],
      "preconditions": [
        "Skill已成功加载"
      ],
      "inputs": {
        "category": "router",
        "name": "关键词路由",
        "input_params": {
          "user_input": "请写一段Python代码"
        }
      },
      "expected": {
        "success": true,
        "output": {
          "target": "big",
          "matched_rule": "代码",
          "reason": "关键词匹配: 代码"
        }
      },
      "assertions": [
        "assert result.model_type == 'big'",
        "assert '代码' in result.reason"
      ]
    },
    {
      "id": "TC004",
      "name": "test_execute_skill_with_invalid_input_schema",
      "description": "测试使用不符合schema的输入执行Skill",
      "category": "unit",
      "priority": "P1",
      "tags": ["skill", "execution", "negative", "validation"],
      "preconditions": [
        "Skill已成功加载"
      ],
      "inputs": {
        "category": "knowledge",
        "name": "简单提取",
        "input_params": {
          "text": "短文本"  # 缺少必填字段
        }
      },
      "expected": {
        "success": false,
        "error_type": "SkillValidationError",
        "error_message_contains": "required"
      },
      "assertions": [
        "assert not result.success",
        "assert result.input_valid == false"
      ]
    },
    {
      "id": "TC005",
      "name": "test_skill_execution_performance",
      "description": "测试Skill执行性能（边界测试）",
      "category": "performance",
      "priority": "P1",
      "tags": ["skill", "performance", "boundary"],
      "preconditions": [
        "Skill已加载"
      ],
      "inputs": {
        "category": "knowledge",
        "name": "简单提取",
        "input_params": {
          "text": "a" * 100000  # 10万字长文本（边界测试）
        }
      },
      "expected": {
        "success": true,
        "max_duration_ms": 5000
      },
      "assertions": [
        "assert result.duration_ms <= 5000",
        "assert len(result.chunks) > 0"
      ]
    },
    {
      "id": "TC006",
      "name": "test_concurrent_skill_execution",
      "description": "测试并发执行Skill（压力测试）",
      "category": "performance",
      "priority": "P2",
      "tags": ["skill", "concurrency", "stress"],
      "preconditions": [
        "Skill已加载"
      ],
      "inputs": {
        "concurrent_requests": 100,
        "input_params": {
          "user_input": "测试输入"
        }
      },
      "expected": {
        "success_rate": 1.0,
        "max_duration_ms": 10000
      },
      "assertions": [
        "assert success_rate == 1.0",
        "assert avg_duration_ms <= 100"
      ]
    }
  ]
}
```

### 10.3 测试案例管理脚本

**文件**: `test/backend/generate_tests.py`

```python
#!/usr/bin/env python3
"""
测试代码生成器
根据JSON测试案例生成pytest测试代码
"""

import json
import os
from pathlib import Path
from jinja2 import Template

TEST_TEMPLATE = '''
# Auto-generated from {{ json_file }}
# Generated at: {{ generated_at }}

import pytest
import asyncio
from datetime import datetime
{% for import_stmt in imports %}
{{ import_stmt }}
{% endfor %}

{% for case in test_cases %}
@pytest.mark.{{ case.category }}
@pytest.mark.priority("{{ case.priority }}")
{% for tag in case.tags %}
@pytest.mark.{{ tag }}
{% endfor %}
async def {{ case.name }}():
    """
    {{ case.description }}
    
    Test Case ID: {{ case.id }}
    Preconditions:
    {% for pre in case.preconditions %}
    - {{ pre }}
    {% endfor %}
    """
    # Arrange
    {% for key, value in case.inputs.items() %}
    {{ key }} = {{ value | repr }}
    {% endfor %}
    
    # Act
    {% if 'expected' in case and 'error_type' in case.expected %}
    with pytest.raises({{ case.expected.error_type }}):
        result = await {{ test_suite }}({{ case.inputs.keys() | join(', ') }})
    {% else %}
    result = await {{ test_suite }}({{ case.inputs.keys() | join(', ') }})
    {% endif %}
    
    # Assert
    {% for assertion in case.assertions %}
    {{ assertion }}
    {% endfor %}
{% endfor %}
'''

def generate_test_file(json_path: str, output_path: str):
    """根据JSON生成测试文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    template = Template(TEST_TEMPLATE)
    content = template.render(
        json_file=json_path,
        generated_at=datetime.now().isoformat(),
        test_suite=data['test_suite'],
        test_cases=data['test_cases'],
        imports=data.get('imports', [])
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    # 遍历所有JSON测试案例
    cases_dir = Path(__file__).parent / "cases"
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    
    for json_file in cases_dir.rglob("*.test.json"):
        relative_path = json_file.relative_to(cases_dir)
        output_file = output_dir / relative_path.with_suffix(".py")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        generate_test_file(str(json_file), str(output_file))
```

### 10.4 测试类型矩阵

| 测试类型 | 目标覆盖率 | 测试重点 | 文件命名 |
|---------|-----------|---------|---------|
| **单元测试** | 100% | 函数/类级别，边界条件 | `test_{module}.py` |
| **集成测试** | 90% | API端点，数据库交互 | `test_integration_{feature}.py` |
| **边界测试** | 100% | 空值、极值、越界、长文本 | 在JSON中标记`boundary`标签 |
| **异常测试** | 100% | 错误处理，异常路径 | 在JSON中标记`negative`标签 |
| **性能测试** | 关键路径 | 响应时间，并发处理 | `test_performance_{feature}.py` |
| **完整度测试** | 100% | 所有分支，所有代码路径 | 通过coverage工具验证 |

### 10.5 边界测试案例（示例）

**文件**: `test/backend/cases/config_manager/boundary.test.json`

```json
{
  "test_suite": "config_manager",
  "test_cases": [
    {
      "id": "B001",
      "name": "test_config_with_empty_yaml",
      "description": "测试空YAML文件",
      "category": "boundary",
      "inputs": {"config_content": ""},
      "expected": {"success": false, "error_type": "ConfigValidationError"}
    },
    {
      "id": "B002",
      "name": "test_config_with_very_long_key",
      "description": "测试超长配置键名（1000字符）",
      "category": "boundary",
      "inputs": {"key": "a" * 1000, "value": "test"},
      "expected": {"success": false}
    },
    {
      "id": "B003",
      "name": "test_config_with_special_characters",
      "description": "测试包含特殊字符的配置值",
      "category": "boundary",
      "inputs": {"key": "test", "value": "<script>alert('xss')</script>"},
      "expected": {"success": true, "value": "<script>alert('xss')</script>"}
    },
    {
      "id": "B004",
      "name": "test_config_with_unicode",
      "description": "测试Unicode字符（中文、emoji）",
      "category": "boundary",
      "inputs": {"key": "测试", "value": "Hello 👋 世界"},
      "expected": {"success": true}
    },
    {
      "id": "B005",
      "name": "test_config_with_nested_deep_structure",
      "description": "测试深层嵌套结构（20层）",
      "category": "boundary",
      "inputs": {"depth": 20},
      "expected": {"success": true}
    },
    {
      "id": "B006",
      "name": "test_config_file_size_limit",
      "description": "测试超大配置文件（10MB）",
      "category": "boundary",
      "inputs": {"file_size_mb": 10},
      "expected": {"success": true}
    }
  ]
}
```

### 10.6 代码质量与复杂度测试

**工具配置**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["test/backend"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=backend",
    "--cov-report=term-missing",
    "--cov-report=html:reports/coverage",
    "--cov-report=xml:reports/coverage.xml",
    "--cov-fail-under=100",  # 100%覆盖率要求
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "performance: Performance tests",
    "boundary: Boundary tests",
    "P0: Priority 0 (critical)",
    "P1: Priority 1 (high)",
    "P2: Priority 2 (medium)",
]

[tool.coverage.run]
source = ["backend"]
omit = [
    "*/tests/*",
    "*/test/*",
    "backend/main.py",  # 入口文件可以排除
]
branch = true  # 分支覆盖率

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 100  # 必须100%覆盖

[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true

[tool.pylint.messages_control]
disable = [
    "C0103",  # 常量命名（我们使用UPPER_SNAKE_CASE）
    "R0903",  # 类方法太少（数据类允许）
]

[tool.pylint.format]
max-line-length = 100

[tool.pylint.design]
max-args = 8
max-attributes = 15
max-branches = 15
max-statements = 50
max-parents = 7
max-complexity = 10  # 圈复杂度限制
```

**代码质量检查脚本**: `scripts/quality_check.sh`

```bash
#!/bin/bash
set -e

echo "=== 代码质量检查 ==="

echo "1. 代码格式化检查 (Black)..."
black --check backend/

echo "2. 导入排序检查 (isort)..."
isort --check-only backend/

echo "3. 类型检查 (mypy)..."
mypy backend/

echo "4. 代码风格检查 (pylint)..."
pylint backend/ --rcfile=pyproject.toml

echo "5. 圈复杂度检查 (xenon)..."
xenon backend/ --max-absolute B --max-modules A --max-average A

echo "6. 安全漏洞检查 (bandit)..."
bandit -r backend/ -f json -o reports/security.json || true

echo "7. 测试覆盖率检查..."
pytest test/backend/ --cov=backend --cov-fail-under=100

echo "=== 所有检查通过 ==="
```

**圈复杂度监控**:

```python
# 在CI中集成
# .github/workflows/quality.yml

name: Code Quality
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install black isort mypy pylint xenon bandit pytest pytest-cov
      
      - name: Run quality checks
        run: |
          black --check backend/
          isort --check-only backend/
          mypy backend/
          pylint backend/ --fail-under=9.0  # pylint评分必须>=9.0
          xenon backend/ --max-absolute B --max-modules A --max-average A
      
      - name: Run tests with coverage
        run: |
          pytest test/backend/ --cov=backend --cov-fail-under=100 --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### 10.7 测试数据管理

**文件**: `test/backend/data/`

```
test/backend/data/
├── config/
│   ├── valid/
│   │   ├── minimal.yml          # 最小配置
│   │   ├── full.yml             # 完整配置
│   │   └── chinese_characters.yml  # 中文配置
│   └── invalid/
│       ├── empty.yml            # 空文件
│       ├── syntax_error.yml     # YAML语法错误
│       ├── missing_required.yml # 缺少必填字段
│       └── invalid_value.yml    # 无效值
├── documents/
│   ├── sample.pdf               # 测试PDF
│   ├── sample.txt               # 测试文本
│   ├── sample_with_bom.txt      # 带BOM的文本（边界测试）
│   └── large_file_10mb.txt      # 大文件（边界测试）
├── audio/
│   ├── sample_5s.mp3            # 5秒音频
│   ├── sample_5min.mp3          # 5分钟音频
│   └── sample_chinese.mp3       # 中文音频
└── skills/
    ├── valid/
    │   ├── router_rule_based.md
    │   └── router_llm_based.md
    └── invalid/
        ├── missing_frontmatter.md
        ├── invalid_yaml.md
        └── missing_required_field.md
```

### 10.8 测试执行命令

```bash
# 运行所有测试
pytest test/backend/

# 运行特定模块测试
pytest test/backend/core/test_skill_manager.py

# 运行特定优先级测试
pytest test/backend/ -m "P0"

# 运行边界测试
pytest test/backend/ -m "boundary"

# 生成测试报告
pytest test/backend/ --html=reports/report.html --self-contained-html

# 检查覆盖率（必须100%）
pytest test/backend/ --cov=backend --cov-fail-under=100

# 生成覆盖率HTML报告
pytest test/backend/ --cov=backend --cov-report=html:reports/coverage

# 代码质量检查
black backend/
isort backend/
mypy backend/
pylint backend/
```

### 10.9 测试案例清单（部分示例）

**必须编写的测试案例数量**: 
- 单元测试: 每个函数至少3个案例（正常、边界、异常）
- 集成测试: 每个API端点至少5个案例
- 边界测试: 每个模块至少10个案例
- 性能测试: 关键路径至少3个案例

**预计总测试案例数**: 500-800个

**测试案例编写规范**:
1. **命名规范**: `test_{被测对象}_{场景}_{预期结果}`
2. **注释规范**: 必须包含测试目的、前置条件、测试步骤
3. **断言规范**: 每个测试至少3个断言
4. **数据规范**: 测试数据与代码分离，使用JSON或fixture

---

## 11. 开发顺序

按照以下顺序实现后端模块:

```
Phase 1: 基础设施
  1.1 项目结构搭建
  1.2 数据库连接 (MongoDB/Redis/Qdrant)
  1.3 配置管理器
  1.4 日志系统

Phase 2: 核心功能
  2.1 API路由框架
  2.2 代理认证中间件
  2.3 虚拟模型管理API
  2.4 对话接口 (/proxy/ai/v1/chat)
  2.5 对话历史管理

Phase 3: Skill系统
  3.1 Skill管理器
  3.2 Skill验证器
  3.3 Skill执行器
  3.4 模型路由引擎
  3.5 Skill管理API

Phase 4: 知识库
  4.1 Embedding服务
  4.2 文档上传/分段
  4.3 向量存储/检索
  4.4 知识提取Skill
  4.5 知识库管理API

Phase 5: 媒体处理
  5.1 Whisper服务集成
  5.2 文件上传/下载
  5.3 转录任务队列
  5.4 媒体处理API

Phase 6: RSS
  6.1 RSS解析器
  6.2 内容提取 (readability)
  6.3 定时抓取任务
  6.4 RSS管理API

Phase 7: 其他
  7.1 看板统计API
  7.2 日志查询API
  7.3 原始数据API
  7.4 系统配置API
```

---

## 12. 依赖清单

**requirements.txt**:
```
# Web框架
fastapi==0.109.0
uvicorn[standard]==0.27.0

# 数据验证
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库
motor==3.3.0              # MongoDB异步驱动
redis==5.0.0              # Redis客户端
qdrant-client==1.7.0      # Qdrant客户端

# HTTP客户端
httpx==0.26.0

# YAML处理
pyyaml==6.0.1

# 文件监控（热重载）
watchdog==3.0.0

# RSS解析
feedparser==6.0.10

# HTML内容提取
readability-lxml==0.8.1
html2text==2020.1.16

# 日志
python-json-logger==2.0.7

# 工具
python-multipart==0.0.6   # 文件上传
python-jose[cryptography]==3.3.0  # JWT（预留）

# 测试
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
httpx==0.26.0
```

---

**文档版本**: 1.0  
**状态**: 待审核  
**审核人**: 用户确认后实施开发
