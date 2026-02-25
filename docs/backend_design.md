# 后端详细设计文档

**项目名称**: ytzc-ai-proxy (AI网关系统)  
**技术栈**: Python 3.11 + FastAPI  
**文档版本**: 1.0  
**最后更新**: 2026-02-24

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

### 2.6 存储层实现状态

**状态**: ✅ **已实现** (2026-02-14)

存储层抽象架构已按照第2.1-2.5节的设计完整实现，代码位于 `backend/core/repositories/` 目录。

**实现的文件结构**:
```
backend/core/repositories/
├── __init__.py          # 模块导出和适配器自动注册
├── interfaces.py        # 抽象接口定义（IDocumentRepository, IVectorRepository, ICacheRepository）
├── factory.py           # RepositoryFactory 工厂类
├── mongodb_adapter.py   # MongoDB适配器实现
├── qdrant_adapter.py    # Qdrant向量存储适配器实现
└── redis_adapter.py     # Redis缓存适配器实现
```

**实现的功能**:
1. ✅ 完整的抽象接口定义（interfaces.py）
   - StorageType, VectorDBType, CacheType 枚举
   - IDocumentRepository: 6个抽象方法
   - IVectorRepository: 6个抽象方法
   - ICacheRepository: 7个抽象方法

2. ✅ 工厂模式实现（factory.py）
   - RepositoryFactory 类
   - 自动注册机制
   - 配置驱动的仓库创建

3. ✅ 具体适配器实现
   - MongoDBAdapter: 使用 Motor 实现异步 MongoDB 操作
   - QdrantAdapter: 使用 Qdrant 客户端实现向量存储
   - RedisAdapter: 使用 Redis-py 实现缓存和队列

4. ✅ 自动注册
   - 在 `__init__.py` 中自动注册所有默认适配器
   - 支持通过配置切换存储后端

**使用示例**:
```python
from core.repositories import RepositoryFactory

# 创建文档存储仓库
doc_repo = RepositoryFactory.create_document_repository({
    "type": "mongodb",
    "host": "localhost",
    "port": 27017,
    "database": "ai_gateway"
})

# 连接并使用
await doc_repo.connect()
doc_id = await doc_repo.insert_one("users", {"name": "Alice"})
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
        
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证配置（占位实现）
        
        此方法为技能配置验证的占位实现，待技能系统完善后再实现具体逻辑。
        当前直接返回验证通过。
        
        Args:
            config: 配置字典
            
        Returns:
            Tuple[bool, List[str]]: (是否通过, 错误信息列表)
        """
        # 占位实现：待技能系统完善后实现具体验证逻辑
        return True, []
        
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

class ModelConfig(BaseModel):
    """单个模型配置（可扩展）"""
    name: str  # 模型名称（如 deepseek-ai/DeepSeek-V3）
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: str = "siliconflow"  # 提供商
    priority: int = 1  # 显示优先级

class KeywordRule(BaseModel):
    """关键词规则"""
    pattern: str  # 匹配模式
    target: str  # 目标模型ID（任意字符串，不限于small/big）

class KeywordSwitchingConfig(BaseModel):
    """关键词切换配置"""
    enabled: bool = False
    rules: List[KeywordRule] = Field(default_factory=list)

class RoutingConfig(BaseModel):
    """路由配置（核心可扩展部分）"""
    current: str = "small"  # 当前默认模型ID（任意字符串）
    force_current: bool = False  # 是否强制
    models: Dict[str, ModelConfig] = Field(default_factory=dict)  # 动态模型列表
    keyword_switching: KeywordSwitchingConfig = Field(default_factory=KeywordSwitchingConfig)

class KeywordConfig(BaseModel):
    """关键词模型切换配置（传统方式）"""
    enabled: bool = False
    small_keywords: List[str] = Field(default_factory=list, max_length=50)
    big_keywords: List[str] = Field(default_factory=list, max_length=50)


class RoutingKeywordsConfig(BaseModel):
    """路由关键词配置（新方式）"""
    enable: bool = False  # 注意：使用enable不是enabled
    rules: List[KeywordRule] = Field(default_factory=list)


class RoutingSkillConfig(BaseModel):
    """路由Skill配置"""
    enabled: bool = True
    version: str = "v1"
    custom: Dict[str, Any] = Field(default_factory=lambda: {"enabled": False, "version": "v2"})


class RoutingConfig(BaseModel):
    """虚拟模型路由配置（替代全局router）"""
    keywords: RoutingKeywordsConfig = Field(default_factory=RoutingKeywordsConfig)
    skill: RoutingSkillConfig = Field(default_factory=RoutingSkillConfig)


class VirtualModelConfig(BaseModel):
    """虚拟模型配置 - 对应实际代码实现"""
    name: str
    proxy_key: str
    base_url: Optional[str] = None
    current: Literal["small", "big"] = "small"  # 当前默认模型
    force_current: bool = False  # 是否强制使用当前模型
    stream_support: bool = True  # 是否支持流式返回
    use: bool = True  # 是否启用
    
    # 模型配置（固定small/big两个模型）
    small: ModelConfig = Field(default_factory=ModelConfig)
    big: ModelConfig = Field(default_factory=ModelConfig)
    
    # 新增：虚拟模型独立路由配置
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    
    # 传统关键词切换配置（与routing.keywords并存）
    keyword_switching: KeywordConfig = Field(default_factory=KeywordConfig)
    
    # 功能配置
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)

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

**职责**: Skill的发现、加载、验证、执行、重载；支持多Skill管理和多版本控制

**目录结构**:
```
skills/
├── system/
│   └── router/
│       └── v1/
│           ├── 关键词路由/
│           │   └── SKILL.md
│           └── 意图识别/
│               └── SKILL.md
├── custom/
│   └── router/
│       ├── v1/
│       │   └── X_skill/
│       │       └── SKILL.md
│       └── v2/
│           └── X_skill/
│               └── SKILL.md
│       └── v1/
│           └── Y_skill/
│               └── SKILL.md
```

**类设计**:
```python
class SkillManager:
    _skills: Dict[str, Dict[str, SkillVersions]] = {}  # category -> {name -> versions}
    _config_manager: ConfigManager
    
    def __init__(self, config_manager: ConfigManager):
        self._config_manager = config_manager
        self._load_all_skills()
    
    def _load_all_skills(self):
        # 遍历skill/system/和skill/custom/目录
        # 加载所有分类、所有Skill、所有版本
        # 结构: category -> skill_name -> {version -> SkillInfo}
        
    def _load_skill(self, category: str, name: str, 
                    is_custom: bool, version: str) -> Optional[SkillInfo]:
        # 加载单个Skill的特定版本
        # 1. 读取SKILL.md
        # 2. 验证YAML frontmatter
        # 3. 如果有.py文件，动态导入
        
    def get_skill(self, category: str, name: str, 
                  version: Optional[str] = None) -> Optional[SkillInfo]:
        # 获取Skill信息
        # 如果不指定version，返回当前激活版本
        
    def get_skills_by_category(self, category: str) -> List[SkillSummary]:
        # 获取某分类下所有Skill列表
        # 包括系统默认和自定义Skills
        
    def get_skill_versions(self, category: str, name: str,
                          is_custom: bool) -> List[str]:
        # 获取指定Skill的所有可用版本
        
    async def execute(self, category: str, name: str, 
                     version: Optional[str] = None,
                     **kwargs) -> Dict[str, Any]:
        # 执行Skill
        # 1. 验证输入参数（JSON Schema）
        # 2. 调用执行函数
        # 3. 验证输出结果（JSON Schema）
        # 4. 记录执行日志
        # 5. 返回结果
        
    def create_skill(self, category: str, name: str,
                     version: str, content: str,
                     copy_from: Optional[str] = None) -> bool:
        # 创建新的自定义Skill
        # 1. 检查名称是否已存在（同一分类）
        # 2. 创建目录结构
        # 3. 写入SKILL.md
        # 4. 加载并验证
        
    def create_version(self, category: str, name: str,
                       new_version: str, copy_from: str) -> bool:
        # 为现有Skill创建新版本
        # 1. 复制指定版本内容
        # 2. 更新版本号
        # 3. 保存到新目录
        
    def update_skill(self, category: str, name: str,
                     version: str, content: str) -> bool:
        # 更新指定版本的Skill内容
        # 1. 验证内容格式
        # 2. 备份原文件
        # 3. 写入新内容
        # 4. 重新加载
        
    def delete_skill(self, category: str, name: str,
                     is_custom: bool) -> bool:
        # 删除整个Skill（所有版本）
        # 仅允许删除自定义Skill
        
    def delete_version(self, category: str, name: str,
                       version: str) -> bool:
        # 删除指定版本
        # 不能删除当前激活版本
        
    def reload_skill(self, category: str, name: str) -> bool:
        # 重载单个Skill的所有版本
        
    def reload_all(self) -> Dict[str, int]:
        # 重载所有Skill
        # 返回统计信息：成功数、失败数
        
    def validate_skill(self, content: str) -> ValidationResult:
        # 校验Skill内容
        # 返回：是否通过、错误列表、警告列表
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
    created_at: datetime
    updated_at: datetime

class SkillSummary:
    # 用于列表展示
    category: str
    name: str
    is_custom: bool
    current_version: str
    all_versions: List[str]
    description: str
    enabled: bool

class ValidationResult:
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]

class ValidationError:
    line: int
    column: int
    message: str
    field: Optional[str]  # 如 "name", "input_schema.properties.x"

class ValidationWarning:
    line: int
    message: str
    suggestion: str
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

---

### 3.5 对话处理管道（Chat Pipeline）

**职责**: 使用职责链模式（Chain of Responsibility）处理对话请求，实现可扩展的对话处理流程。

**解决的问题**:
- 当前 `chat.py` 一个函数处理所有逻辑，难以维护和扩展
- 对话历史保存逻辑散落在各处，容易遗漏
- 无法灵活添加预处理（知识检索、联网搜索）和后处理（压缩、总结）

**设计决策**:
- **响应方式**: 统一非流式（一次返回完整响应），简化处理逻辑
- **错误处理**: 即使LLM调用失败，也要保存用户消息，确保数据不丢失
- **Raw数据归档**: 永久保留完整请求/响应，根据 `config.yml` 中 `log.system.retention.days` 自动清理
- **预留接口**: Knowledge和WebSearch预留，读取配置但不实现核心逻辑
- **4get搜索**: 保留空目录，代码中做空实现

#### 3.5.1 职责链执行流程

```
Phase 1: 输入处理层（必须）
  1. InputValidatorHandler       - 输入验证、安全过滤
  2. UserMessagePersistence     - 💾 保存用户原始提问（最高优先级）

Phase 2: 预处理层（预留接口）
  3. KnowledgeRetrievalHandler  - 📚 知识库检索（预留，读取配置）
  4. WebSearchHandler           - 🔍 联网搜索（预留，读取配置，4get空实现）

Phase 3: 模型层（必须）
  5. ModelRoutingHandler        - 🎯 模型路由决策
  6. LLMInvocationHandler       - 🤖 调用远程LLM（已完整实现）

Phase 4: 后处理层（必须+归档）
  7. AssistantMessagePersistence - 💾 保存助手回复
  8. RawDataArchiveHandler      - 📦 完整数据归档（永久保留）

Phase 5: 输出层（必须）
  9. ResponseFormatter          - 📤 格式化JSON响应
```

**重要说明**：
- **统一入口**: 所有客户端（WebChat/ChatBox/第三方API）都通过 `/proxy/ai/v1/chat/completions` 接口访问，统一经过职责链处理
- **自动保存**: 用户消息和助手回复在职责链中自动保存到MongoDB，前端无需手动调用保存API
- **完整实现**: LLMInvocationHandler 已完整实现，支持 OpenAI/SiliconFlow/Ollama 三种提供商

#### 3.5.2 核心类设计

```python
# core/chat_pipeline.py

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import time
import uuid


@dataclass
class ChatContext:
    """对话上下文 - 在职责链中传递"""
    # 输入
    conversation_id: Optional[str] = None
    virtual_model: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_message: str = ""
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # 处理结果
    model_type: Optional[str] = None  # "small" | "big"
    model_config: Optional[Dict] = None
    response_content: str = ""
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    start_time: float = field(default_factory=time.time)
    user_message_saved: bool = False
    error_occurred: bool = False
    skip_reason: Optional[str] = None


class PipelineHandler:
    """处理器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self._next: Optional['PipelineHandler'] = None
    
    def set_next(self, handler: 'PipelineHandler') -> 'PipelineHandler':
        """设置下一个处理器"""
        self._next = handler
        return handler
    
    async def handle(self, context: ChatContext) -> ChatContext:
        """处理逻辑"""
        context = await self._process(context)
        
        # 如果没有跳过后续处理的标记，继续执行链
        if self._next and not context.skip_reason and not context.error_occurred:
            return await self._next.handle(context)
        return context
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """子类实现具体逻辑"""
        raise NotImplementedError


class ChatPipeline:
    """对话管道 - 组装职责链"""
    
    def __init__(
        self,
        conversation_manager,
        skill_manager,
        config_manager,
        knowledge_manager=None,
        model_router=None
    ):
        self._cm = conversation_manager
        self._sm = skill_manager
        self._config = config_manager
        self._km = knowledge_manager
        self._router = model_router
        
        # 构建职责链
        self._chain = self._build_chain()
    
    def _build_chain(self) -> PipelineHandler:
        """构建处理链"""
        
        # Phase 1: 输入处理
        validator = InputValidatorHandler()
        user_persistence = UserMessagePersistence(self._cm)
        
        # Phase 2: 预处理（预留接口）
        knowledge = KnowledgeRetrievalHandler(self._config, self._sm)
        web_search = WebSearchHandler(self._config, self._sm)
        
        # Phase 3: 模型层
        routing = ModelRoutingHandler(self._router, self._config)
        llm = LLMInvocationHandler(self._config)
        
        # Phase 4: 后处理
        assistant_persistence = AssistantMessagePersistence(self._cm)
        raw_archive = RawDataArchiveHandler(self._cm)
        
        # Phase 5: 输出
        formatter = ResponseFormatter()
        
        # 组装链条
        validator.set_next(user_persistence) \
                 .set_next(knowledge) \
                 .set_next(web_search) \
                 .set_next(routing) \
                 .set_next(llm) \
                 .set_next(assistant_persistence) \
                 .set_next(raw_archive) \
                 .set_next(formatter)
        
        return validator
    
    async def process(self, context: ChatContext) -> ChatContext:
        """执行管道处理"""
        return await self._chain.handle(context)
```

#### 3.5.3 核心Handler实现

**UserMessagePersistence**（最先执行，确保不丢失）:

```python
class UserMessagePersistence(PipelineHandler):
    """保存用户原始提问 - 最高优先级"""
    
    def __init__(self, conversation_manager):
        super().__init__("UserMessagePersistence")
        self._cm = conversation_manager
    
    async def _process(self, context: ChatContext) -> ChatContext:
        # 确保有conversation_id
        if not context.conversation_id:
            context.conversation_id = await self._cm.create_conversation(
                context.virtual_model
            )
        
        # 立即保存用户消息（不等待后续处理）
        await self._cm.add_message(
            conversation_id=context.conversation_id,
            role="user",
            content=context.user_message,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": context.request_id,
                "source": "webchat",
                "ip": context.metadata.get("client_ip")
            }
        )
        
        context.user_message_saved = True
        logger.info(f"💾 [{context.request_id}] 用户消息已持久化: {context.conversation_id}")
        return context
```

**KnowledgeRetrievalHandler**（预留接口）:

```python
class KnowledgeRetrievalHandler(PipelineHandler):
    """知识库检索 - 当前预留接口，读取配置但不实现核心逻辑"""
    
    def __init__(self, config_manager, skill_manager):
        super().__init__("KnowledgeRetrievalHandler")
        self._config = config_manager
        self._sm = skill_manager
    
    def _get_knowledge_config(self, virtual_model: str) -> Dict:
        """从config.yml读取知识库配置"""
        return self._config.get(
            f"ai-gateway.virtual_models.{virtual_model}.knowledge", 
            {}
        )
    
    async def _process(self, context: ChatContext) -> ChatContext:
        # 读取配置
        config = self._get_knowledge_config(context.virtual_model)
        
        if not config.get("enabled", False):
            return context  # 未启用，直接跳过
        
        # 预留：检查Skill配置
        skill_config = config.get("skill", {})
        if skill_config.get("enabled") and skill_config.get("version"):
            # 预留调用Skill的代码，当前不实现
            # result = await self._sm.execute(
            #     "knowledge", f"检索/{skill_config['version']}",
            #     query=context.user_message
            # )
            pass
        
        # 记录元数据
        context.metadata["knowledge_checked"] = True
        context.metadata["knowledge_enabled"] = True
        context.metadata["knowledge_skill_version"] = skill_config.get("version")
        
        logger.info(f"📚 [{context.request_id}] 知识库检索已预留（配置启用，暂未实现）")
        return context
```

**WebSearchHandler**（预留接口，4get空实现）:

```python
class WebSearchHandler(PipelineHandler):
    """联网搜索 - 预留接口，4get空实现"""
    
    def __init__(self, config_manager, skill_manager):
        super().__init__("WebSearchHandler")
        self._config = config_manager
        self._sm = skill_manager
    
    def _get_web_search_config(self, virtual_model: str) -> Dict:
        """从config.yml读取联网搜索配置"""
        return self._config.get(
            f"ai-gateway.virtual_models.{virtual_model}.web_search",
            {}
        )
    
    async def _process(self, context: ChatContext) -> ChatContext:
        config = self._get_web_search_config(context.virtual_model)
        
        if not config.get("enabled", False):
            return context
        
        targets = config.get("target", [])
        
        # 4get 空实现（保留目录）
        if "4get" in targets:
            logger.info(f"🔍 [{context.request_id}] 4get搜索 - 空实现（目录保留）")
        
        # LibreX 预留
        if "LibreX" in targets:
            logger.info(f"🔍 [{context.request_id}] LibreX搜索 - 预留接口")
        
        # Skill预留
        skill_config = config.get("skill", {})
        if skill_config.get("enabled"):
            logger.info(f"🔍 [{context.request_id}] WebSearch Skill预留（版本: {skill_config.get('version')}）")
        
        context.metadata["web_search_checked"] = True
        context.metadata["web_search_targets"] = targets
        
        return context
```

**ModelRoutingHandler**（模型路由 + 关键词替换）:

```python
class ModelRoutingHandler(PipelineHandler):
    """模型路由决策处理器 - 包含关键词匹配和替换功能"""
    
    def __init__(self, model_router, config_manager=None):
        super().__init__("ModelRoutingHandler")
        self._router = model_router
        self._config = config_manager
    
    def _get_keyword_config(self, virtual_model: str) -> Dict:
        """从config.yml读取关键词路由配置"""
        return self._config.get(
            f"ai-gateway.virtual_models.{virtual_model}.routing.keywords",
            {}
        )
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """执行模型路由决策 + 关键词替换"""
        
        # 1. 首先尝试关键词匹配和替换
        keyword_config = self._get_keyword_config(context.virtual_model)
        
        if keyword_config.get("enabled", False):
            rules = keyword_config.get("rules", [])
            
            for rule in rules:
                pattern = rule.get("pattern", "")
                target = rule.get("target", "small")
                
                if pattern in context.user_message:
                    # 匹配成功：切换模型
                    context.model_type = target
                    context.metadata["model_type"] = target
                    context.metadata["route_reason"] = f"关键词匹配: {pattern}"
                    context.metadata["matched_keyword"] = pattern
                    
                    # 记录原始消息
                    context.metadata["original_user_message"] = context.user_message
                    
                    # 移除关键词
                    context.user_message = context.user_message.replace(pattern, "").strip()
                    context.metadata["processed_user_message"] = context.user_message
                    
                    logger.info(f"🎯 [{context.request_id}] 关键词匹配: {pattern} -> {target}")
                    logger.info(f"📝 [{context.request_id}] 消息替换: '{pattern}' -> ''")
                    logger.info(f"📝 [{context.request_id}] 最终消息: '{context.user_message}'")
                    
                    # 匹配成功，跳过后续的ModelRouter.route()调用
                    return context
        
        # 2. 如果没有匹配关键词，继续原有ModelRouter.route()逻辑
        try:
            route_result = await self._router.route(
                virtual_model=context.virtual_model,
                user_input=context.user_message,
                conversation_id=context.conversation_id
            )
            
            context.model_type = route_result.model_type
            context.metadata["model_type"] = route_result.model_type
            context.metadata["route_reason"] = route_result.reason
            context.metadata["route_confidence"] = route_result.confidence
            context.metadata["matched_rule"] = route_result.matched_rule
            
            logger.info(f"🎯 [{context.request_id}] 路由决策: {route_result.model_type} - {route_result.reason}")
            
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 路由决策失败: {e}")
            # 路由失败时使用默认值
            context.model_type = "small"
            context.metadata["route_error"] = str(e)
            context.metadata["route_reason"] = "路由失败，使用默认模型"
        
        return context
```

**LLMInvocationHandler**（实际调用LLM服务）:

```python
class LLMInvocationHandler(PipelineHandler):
    """LLM调用处理器"""
    
    def __init__(self, config_manager):
        super().__init__("LLMInvocationHandler")
        self._config = config_manager
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """调用远程LLM"""
        # 检查是否需要跳过（纯关键词切换）
        if context.skip_reason == "keyword_only_switch":
            return context
        
        # 检查模型类型
        if not context.model_type:
            logger.warning(f"[{context.request_id}] model_type未设置，使用默认small模型")
            context.model_type = "small"
        
        try:
            # 动态导入以避免循环依赖
            from services.llm_service import LLMServiceFactory, ModelProvider
            from models.base import ChatCompletionRequest, Message
            
            # 获取虚拟模型配置
            vm_config = self._config.get(f"ai-gateway.virtual_models.{context.virtual_model}")
            if not vm_config:
                raise ValueError(f"虚拟模型配置不存在: {context.virtual_model}")
            
            # 获取具体模型配置
            model_config = vm_config.get(context.model_type, {})
            if not model_config:
                raise ValueError(f"模型类型配置不存在: {context.model_type}")
            
            # 确定提供商
            provider_str = model_config.get("provider", "siliconflow").lower()
            if provider_str == "openai":
                provider = ModelProvider.OPENAI
            elif provider_str == "ollama":
                provider = ModelProvider.OLLAMA
            else:
                provider = ModelProvider.SILICONFLOW
            
            # 创建LLM服务
            llm_service = LLMServiceFactory.create(
                provider=provider,
                base_url=model_config.get("base_url", "https://api.siliconflow.cn/v1"),
                api_key=model_config.get("api_key"),
                model=model_config.get("model", "Qwen/Qwen2.5-7B-Instruct"),
                temperature=context.temperature,
                max_tokens=context.max_tokens
            )
            
            # 构建请求
            chat_request = ChatCompletionRequest(
                model=model_config.get("model", "unknown"),
                messages=[
                    Message(role=msg.get("role", "user"), content=msg.get("content", ""))
                    for msg in context.messages
                ],
                stream=False,
                temperature=context.temperature,
                max_tokens=context.max_tokens
            )
            
            # 调用LLM
            response = await llm_service.chat(chat_request)
            
            # 提取响应内容
            if response.choices:
                context.response_content = response.choices[0].message.content
            
            # 记录token使用
            if response.usage:
                context.metadata["prompt_tokens"] = response.usage.prompt_tokens
                context.metadata["completion_tokens"] = response.usage.completion_tokens
                context.metadata["total_tokens"] = response.usage.total_tokens
            
            context.metadata["model_used"] = model_config.get("model")
            context.metadata["llm_called"] = True
            
            await llm_service.close()
            
        except ValueError as e:
            logger.error(f"[{context.request_id}] LLM配置错误: {e}")
            context.error_occurred = True
            context.response_content = "抱歉，AI服务配置错误，请联系管理员。"
            context.metadata["llm_config_error"] = str(e)
        except Exception as e:
            logger.error(f"[{context.request_id}] LLM调用失败: {e}")
            context.error_occurred = True
            context.response_content = "抱歉，AI服务暂时不可用，请稍后重试。"
            context.metadata["llm_error"] = str(e)
        
        return context
```

**注意事项**:
- 关键词替换在 Phase 3（模型层）最先执行
- 匹配成功后直接返回，不调用后续的 ModelRouter.route()
- 替换后的消息用于发送给LLM，但原始消息保存在 metadata 中
- RawDataArchiveHandler 会将原始消息一起归档

**RawDataArchiveHandler**（永久归档，自动清理）:

```python
class RawDataArchiveHandler(PipelineHandler):
    """完整数据归档 - 用于调试和审计，根据配置自动清理"""
    
    def __init__(self, conversation_manager):
        super().__init__("RawDataArchiveHandler")
        self._cm = conversation_manager
        self._db = conversation_manager._db
    
    async def _process(self, context: ChatContext) -> ChatContext:
        archive_data = {
            "conversation_id": context.conversation_id,
            "request_id": context.request_id,
            "timestamp": datetime.utcnow(),
            "request": {
                "user_message": context.user_message,
                "virtual_model": context.virtual_model,
                "messages": context.messages,
                "temperature": context.temperature,
                "max_tokens": context.max_tokens,
                "knowledge_enabled": context.metadata.get("knowledge_enabled", False),
                "web_search_enabled": context.metadata.get("web_search_enabled", False)
            },
            "response": {
                "content": context.response_content,
                "model_type": context.model_type,
                "model_used": context.metadata.get("model_used"),
                "tokens_used": context.metadata.get("tokens_used")
            },
            "processing_metadata": context.metadata,
            "duration_ms": (time.time() - context.start_time) * 1000
        }
        
        # 保存到raw_conversation_logs集合
        await self._db["raw_conversation_logs"].insert_one(archive_data)
        
        logger.info(f"📦 [{context.request_id}] 原始数据已归档")
        return context
```

#### 3.5.4 数据清理策略

根据 `config.yml` 中的 `ai-gateway.log.system.retention.days` 配置自动清理：

```python
# core/tasks/cleanup_task.py

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RawDataCleanupTask:
    """定时清理Raw数据任务"""
    
    def __init__(self, db, config_manager):
        self._db = db
        self._config = config_manager
    
    async def cleanup(self):
        """执行清理"""
        retention_days = self._config.get(
            "ai-gateway.log.system.retention.days",
            default=30
        )
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # 删除过期数据
        result = await self._db["raw_conversation_logs"].delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        logger.info(f"🧹 Raw数据清理完成: 删除 {result.deleted_count} 条记录（保留{retention_days}天）")
        return result.deleted_count
```

#### 3.5.5 错误恢复机制

```python
class ErrorRecoveryHandler:
    """错误恢复包装器 - 确保消息不丢失"""
    
    def __init__(self, conversation_manager):
        self._cm = conversation_manager
    
    async def handle_with_recovery(self, context: ChatContext, chain: PipelineHandler):
        """带错误恢复的处理"""
        try:
            return await chain.handle(context)
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 职责链执行失败: {e}")
            
            # 确保用户消息已保存（如果没保存的话）
            if not context.user_message_saved:
                try:
                    if not context.conversation_id:
                        context.conversation_id = await self._cm.create_conversation(
                            context.virtual_model
                        )
                    
                    await self._cm.add_message(
                        context.conversation_id,
                        "user",
                        context.user_message,
                        metadata={
                            "error_occurred": True,
                            "error_message": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    logger.info(f"💾 [{context.request_id}] 紧急保存用户消息成功")
                except Exception as save_error:
                    logger.error(f"❌ [{context.request_id}] 紧急保存失败: {save_error}")
            
            # 返回友好的错误响应
            context.response_content = "抱歉，处理您的请求时出现了错误。请稍后重试。"
            context.error_occurred = True
            context.metadata["error"] = str(e)
            
            return context
```

#### 3.5.6 使用示例

**简化后的 chat.py 实现**（LLM调用已整合到职责链）：

```python
# api/proxy/v1/chat.py

@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    model_info: dict = Depends(verify_proxy_key),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    skill_manager: SkillManager = Depends(get_skill_manager),
    config_manager: ConfigManager = Depends(get_config_manager),
    model_router: ModelRouter = Depends(get_model_router)
):
    """
    对话接口 - 使用职责链模式
    
    流程简化说明：
    1. LLM调用已整合到职责链中的 LLMInvocationHandler
    2. 消息保存由 UserMessagePersistence 和 AssistantMessagePersistence 自动完成
    3. 前端无需手动调用保存API
    """
    
    # 1. 解析请求
    body = await request.json()
    
    # 2. 构建上下文
    context = ChatContext(
        conversation_id=body.get("conversation_id"),
        virtual_model=model_info["name"],
        messages=body.get("messages", []),
        user_message=body.get("messages", [])[-1].get("content", "") if body.get("messages") else "",
        stream=False,
        temperature=body.get("temperature", 0.7),
        max_tokens=body.get("max_tokens", 2000),
        metadata={"client_ip": request.client.host}
    )
    
    # 3. 创建职责链
    pipeline = ChatPipeline(
        conversation_manager=conversation_manager,
        skill_manager=skill_manager,
        config_manager=config_manager,
        model_router=model_router
    )
    
    # 4. 执行处理（职责链内部完成：验证→保存用户消息→路由→调用LLM→保存助手回复→归档）
    result = await pipeline.process(context)
    
    # 5. 返回响应
    if result.error_occurred:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": result.response_content,
                    "type": "processing_error",
                    "request_id": result.request_id
                }
            }
        )
    
    # 响应包含 conversation_id，前端可用它更新对话列表
    return result.final_response
```

**关键改进**：
- ✅ LLMInvocationHandler 实际调用LLM服务，不再需要在职责链外手动调用
- ✅ 自动保存用户消息和助手回复，前端无需额外调用保存API
- ✅ 所有客户端（WebChat/ChatBox/第三方）统一通过职责链处理

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
    
    async def get_or_create_by_fingerprint(
        self, 
        fingerprint: str, 
        virtual_model: str,
        ttl_minutes: int = 30
    ) -> str:
        """
        通过指纹获取或创建对话（用于ChatBox等不发送conversation_id的客户端）
        
        Args:
            fingerprint: 消息指纹（基于前2条用户消息的MD5）
            virtual_model: 虚拟模型名称
            ttl_minutes: 指纹过期时间（分钟）
            
        Returns:
            str: 对话ID（现有或新创建）
        """
        try:
            # 1. 尝试从Redis获取现有对话
            if self._redis:
                cache_key = f"conversation:fingerprint:{fingerprint}"
                existing_id = await self._redis.get(cache_key)
                
                if existing_id:
                    # 验证对话是否仍然存在
                    existing_conv = await self.get_conversation(existing_id)
                    if existing_conv and existing_conv.virtual_model == virtual_model:
                        return existing_id
            
            # 2. 创建新对话
            conversation_id = await self.create_conversation(virtual_model)
            
            # 3. 保存指纹到Redis
            if self._redis:
                cache_key = f"conversation:fingerprint:{fingerprint}"
                await self._redis.setex(cache_key, ttl_minutes * 60, conversation_id)
            
            return conversation_id
            
        except Exception as e:
            # 失败时创建新对话
            return await self.create_conversation(virtual_model)
    
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

**职责**: RSS订阅管理、抓取、内容提取、使用MongoDB存储

**类设计**:
```python
class RSSFetcher:
    _mongodb: AsyncIOMotorClient
    _http_client: httpx.AsyncClient
    _config: Dict[str, Any]
    
    def __init__(self, mongodb, config: Dict[str, Any] = None):
        self._mongodb = mongodb
        self._config = config or {}
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._db = mongodb["ai_gateway"]
        self._feeds_collection = self._db["rss_feeds"]
        self._articles_collection = self._db["rss_articles"]
    
    async def create_feed(self, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建RSS订阅源"""
        feed_doc = {
            "_id": ObjectId(),
            "name": feed_data["name"],
            "url": feed_data["url"],
            "enabled": feed_data.get("enabled", True),
            "fetch_interval": feed_data.get("fetch_interval", 30),
            "retention_days": feed_data.get("retention_days", 30),
            "default_permanent": feed_data.get("default_permanent", False),
            "last_fetch_time": None,
            "article_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await self._feeds_collection.insert_one(feed_doc)
        return self._doc_to_feed(feed_doc)
    
    async def get_feeds(self, enabled: Optional[bool] = None, 
                       page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """获取订阅源列表（支持分页和筛选）"""
        query = {}
        if enabled is not None:
            query["enabled"] = enabled
        
        skip = (page - 1) * page_size
        cursor = self._feeds_collection.find(query).skip(skip).limit(page_size)
        feeds = [self._doc_to_feed(doc) async for doc in cursor]
        total = await self._feeds_collection.count_documents(query)
        return feeds, total
    
    async def update_feed(self, feed_id: str, update_data: Dict[str, Any]) -> Optional[Dict]:
        """更新订阅源"""
        update_doc = {"updated_at": datetime.utcnow()}
        for key in ["name", "enabled", "fetch_interval", "retention_days", "default_permanent"]:
            if key in update_data:
                update_doc[key] = update_data[key]
        
        result = await self._feeds_collection.find_one_and_update(
            {"_id": ObjectId(feed_id)},
            {"$set": update_doc},
            return_document=True
        )
        return self._doc_to_feed(result) if result else None
    
    async def delete_feed(self, feed_id: str) -> bool:
        """删除订阅源及其文章"""
        # 删除关联文章
        await self._articles_collection.delete_many({"feed_id": feed_id})
        # 删除订阅源
        result = await self._feeds_collection.delete_one({"_id": ObjectId(feed_id)})
        return result.deleted_count > 0
    
    async def fetch_feed(self, feed_id: str) -> Dict[str, Any]:
        """立即抓取单个RSS订阅源"""
        feed = await self._feeds_collection.find_one({"_id": ObjectId(feed_id)})
        if not feed:
            raise ValueError(f"Feed not found: {feed_id}")
        
        # 解析RSS feed
        parsed = feedparser.parse(feed["url"])
        fetched_count = 0
        
        for entry in parsed.entries:
            # 检查文章是否已存在
            existing = await self._articles_collection.find_one({
                "feed_id": feed_id,
                "url": entry.link
            })
            if existing:
                continue
            
            # 抓取完整内容
            article_content = await self._fetch_full_content(entry.link)
            
            # 保存文章
            article_doc = {
                "_id": ObjectId(),
                "feed_id": feed_id,
                "title": entry.get("title", "无标题"),
                "url": entry.link,
                "content": article_content["markdown"],
                "content_length": len(article_content["markdown"]),
                "published_at": self._parse_date(entry.get("published_parsed") or entry.get("updated_parsed")),
                "fetched_at": datetime.utcnow(),
                "is_read": False
            }
            await self._articles_collection.insert_one(article_doc)
            fetched_count += 1
        
        # 更新最后抓取时间和文章数
        await self._feeds_collection.update_one(
            {"_id": ObjectId(feed_id)},
            {"$set": {
                "last_fetch_time": datetime.utcnow(),
                "article_count": await self._articles_collection.count_documents({"feed_id": feed_id})
            }}
        )
        
        return {
            "success": True,
            "message": f"成功抓取 {fetched_count} 篇文章",
            "fetch_id": str(ObjectId()),
            "feed_id": feed_id,
            "articles_fetched": fetched_count
        }
    
    async def _fetch_full_content(self, url: str) -> Dict[str, str]:
        """爬取完整文章内容（使用readability + html2text）"""
        try:
            response = await self._http_client.get(url, follow_redirects=True)
            raw_html = response.text
            
            # 使用readability提取正文
            doc = Document(raw_html)
            cleaned_html = doc.summary()
            
            # 转换为Markdown
            markdown_content = html2text.html2text(cleaned_html)
            
            return {
                "markdown": markdown_content,
                "html": cleaned_html,
                "raw": raw_html[:10000],  # 限制原始HTML大小
                "status": "success"
            }
        except Exception as e:
            return {
                "markdown": f"抓取失败: {str(e)}",
                "html": "",
                "raw": "",
                "status": "failed"
            }
    
    async def get_articles(self, feed_id: Optional[str] = None,
                          is_read: Optional[bool] = None,
                          page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """获取文章列表（支持feed_id和is_read筛选）"""
        query = {}
        if feed_id:
            query["feed_id"] = feed_id
        if is_read is not None:
            query["is_read"] = is_read
        
        skip = (page - 1) * page_size
        cursor = self._articles_collection.find(query) \
            .sort("published_at", -1) \
            .skip(skip).limit(page_size)
        
        articles = [self._doc_to_article(doc) async for doc in cursor]
        total = await self._articles_collection.count_documents(query)
        return articles, total
    
    async def get_article(self, article_id: str) -> Optional[Dict]:
        """获取文章详情"""
        article = await self._articles_collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            return None
        
        # 获取订阅源名称
        feed = await self._feeds_collection.find_one({"_id": ObjectId(article["feed_id"])})
        article["feed_name"] = feed["name"] if feed else "未知来源"
        
        return self._doc_to_article(article)
    
    async def mark_article_read(self, article_id: str, is_read: bool = True) -> Optional[Dict]:
        """标记文章已读/未读"""
        result = await self._articles_collection.find_one_and_update(
            {"_id": ObjectId(article_id)},
            {"$set": {"is_read": is_read}},
            return_document=True
        )
        return self._doc_to_article(result) if result else None
    
    def _doc_to_feed(self, doc: Dict) -> Dict:
        """将MongoDB文档转换为Feed对象"""
        return {
            "id": str(doc["_id"]),
            "name": doc["name"],
            "url": doc["url"],
            "enabled": doc["enabled"],
            "fetch_interval": doc["fetch_interval"],
            "retention_days": doc["retention_days"],
            "default_permanent": doc["default_permanent"],
            "last_fetch_time": doc["last_fetch_time"].isoformat() if doc.get("last_fetch_time") else None,
            "article_count": doc.get("article_count", 0),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None
        }
    
    def _doc_to_article(self, doc: Dict) -> Dict:
        """将MongoDB文档转换为Article对象"""
        return {
            "id": str(doc["_id"]),
            "feed_id": doc["feed_id"],
            "feed_name": doc.get("feed_name", ""),
            "title": doc["title"],
            "url": doc["url"],
            "content": doc["content"],
            "content_length": doc.get("content_length", 0),
            "published_at": doc["published_at"].isoformat() if doc.get("published_at") else None,
            "fetched_at": doc["fetched_at"].isoformat() if doc.get("fetched_at") else None,
            "is_read": doc.get("is_read", False)
        }
```

**热门订阅源预设数据**:
```python
POPULAR_RSS_SOURCES = [
    {"name": "少数派", "url": "https://sspai.com/feed", "description": "高品质数字消费指南", "subscriber_count": "31.5K"},
    {"name": "36氪", "url": "https://36kr.com/feed", "description": "科技创投商业资讯", "subscriber_count": "12.5K"},
    {"name": "阮一峰的网络日志", "url": "http://www.ruanyifeng.com/blog/atom.xml", "description": "科技爱好者周刊", "subscriber_count": "8.9K"},
    {"name": "知乎日报", "url": "https://www.zhihu.com/rss", "description": "知乎精选内容", "subscriber_count": "6.2K"},
    {"name": "GitHub Trending", "url": "https://github.com/trending", "description": "GitHub热门项目", "subscriber_count": "5.8K"},
    {"name": "InfoQ", "url": "https://www.infoq.cn/feed", "description": "企业级技术社区", "subscriber_count": "4.5K"},
    {"name": "稀土掘金", "url": "https://juejin.cn/rss", "description": "开发者技术社区", "subscriber_count": "3.2K"},
    {"name": "V2EX", "url": "https://www.v2ex.com/index.xml", "description": "创意工作者社区", "subscriber_count": "2.1K"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "description": "人工智能媒体", "subscriber_count": "1.8K"},
    {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "description": "数字公民媒体", "subscriber_count": "1.5K"}
]
```

**Config.yml RSS配置**:
```yaml
rss:
  max_concurrent: 5          # 最大并发抓取数
  auto_fetch: true           # 是否自动抓取
  fetch_interval: 30         # 抓取间隔（分钟）
  retention_days: 30         # 文章保留天数
  default_permanent: false   # 默认是否永久保存
  skill:                     # RSS Skill配置
    enabled: true
    version: "v1"
    custom:
      enabled: true
      version: "v1"
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
      "timestamp": ISODate("2026-02-24T14:00:00Z"),
      "metadata": {}
    },
    {
      "role": "assistant", 
      "content": "你好！",
      "timestamp": ISODate("2026-02-24T14:00:05Z"),
      "metadata": {
        "model_used": "small",
        "knowledge_references": [...],
        "routing_decision": {...}
      }
    }
  ],
  "message_count": 10,
  "created_at": ISODate("2026-02-24T14:00:00Z"),
  "updated_at": ISODate("2026-02-24T14:30:00Z"),
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
  "upload_time": ISODate("2026-02-24T10:00:00Z"),
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
    "completed_at": ISODate("2026-02-24T14:30:00Z")
  },
  "knowledge_extracted": true,
  "knowledge_doc_ids": ["doc_uuid_1", "doc_uuid_2"],
  "upload_time": ISODate("2026-02-24T14:00:00Z"),
  "updated_at": ISODate("2026-02-24T14:30:00Z")
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
  "last_fetch_time": ISODate("2026-02-24T14:00:00Z"),
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
  "published_at": ISODate("2026-02-24T10:00:00Z"),
  "fetched_at": ISODate("2026-02-24T14:00:00Z"),
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
  "timestamp": ISODate("2026-02-24T14:30:00Z"),
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
  "created_at": "2026-02-24T10:00:00Z",
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
2026-02-24 14:30:00 [INFO] skill.manager: Skill加载成功: router/意图识别@v1
2026-02-24 14:30:05 [ERROR] skill.executor: Skill执行失败: router/意图识别 - Connection timeout
```

**执行日志** (JSON Lines):
```json
{"timestamp":"2026-02-24T14:30:00Z","skill_category":"router","skill_name":"意图识别","duration_ms":120,"status":"success"}
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
  "created_at": "2026-02-24",
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

## 11. 可扩展路由架构设计

### 11.1 设计理念

当前版本支持 **small/big** 两个模型，但架构必须支持未来扩展到 **N 个模型**（model_1, model_2, ... model_n）。

**设计原则**:
1. **向后兼容**: 现有 small/big 配置继续工作
2. **渐进扩展**: 未来可添加任意数量的模型
3. **配置驱动**: 通过 YAML 配置动态定义模型
4. **统一抽象**: 所有模型使用相同的配置结构

### 11.2 配置结构（可扩展版）

```yaml
ai-gateway:
  virtual_models:
    demo1:
      proxy_key: "xxx"
      base_url: "http://..."
      
      # ========== 路由配置（核心）==========
      routing:
        current: "small"              # 当前默认模型ID
        force_current: false          # 是否强制使用current
        
        # 关键词切换配置
        keyword_switching:
          enabled: true
          rules:                      # 关键词规则列表（可扩展）
            - pattern: "@大哥"
              target: "big"          # 目标模型ID
            - pattern: "@小弟" 
              target: "small"
            - pattern: "@code"
              target: "coding"       # 未来可扩展到其他模型
        
        # 模型列表（可扩展，当前2个，未来N个）
        models:
          small:                      # 模型ID
            name: "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"
            api_key: "sk-xxx"
            base_url: "https://api.siliconflow.cn/v1"
            provider: "siliconflow"
            priority: 1               # 优先级（用于排序显示）
          big:
            name: "Pro/deepseek-ai/DeepSeek-V3.2"
            api_key: "sk-xxx"
            base_url: "https://api.siliconflow.cn/v1"
            provider: "siliconflow"
            priority: 2
          # coding:                  # 未来可添加第3、4、N个模型
          #   name: "codellama/CodeLlama-70b-Instruct-hf"
          #   api_key: "sk-xxx"
          #   base_url: "https://api.siliconflow.cn/v1"
          #   provider: "siliconflow"
          #   priority: 3
      
      # 其他配置保持不变
      knowledge:
        enabled: true
      web_search:
        enabled: true
```

### 11.3 关键设计点

#### 1. 使用 `models` 对象替代固定的 `small/big`

**当前版本（2个模型）**:
```yaml
small: { ... }
big: { ... }
```

**未来版本（N个模型）**:
```yaml
models:
  small: { ... }
  big: { ... }
  coding: { ... }
  vision: { ... }
  # ... 任意数量
```

#### 2. 路由目标使用模型ID（字符串）而非枚举

```python
# 当前
model_type: Literal["small", "big"]

# 未来（可扩展）
target_model: str  # 可以是 "small", "big", "coding", "vision" 等任意ID
```

### 11.4 Pydantic 模型设计

```python
# 可扩展模型配置
class ModelConfig(BaseModel):
    """单个模型配置（可扩展）"""
    name: str                    # 模型名称（如 deepseek-ai/DeepSeek-V3）
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    provider: str = "siliconflow"  # 提供商
    priority: int = 1            # 显示优先级

class KeywordRule(BaseModel):
    """关键词规则"""
    pattern: str                 # 匹配模式
    target: str                  # 目标模型ID（任意字符串，不限于small/big）

class KeywordSwitchingConfig(BaseModel):
    """关键词切换配置"""
    enabled: bool = False
    rules: List[KeywordRule] = Field(default_factory=list)

class RoutingConfig(BaseModel):
    """路由配置（核心可扩展部分）"""
    current: str = "small"       # 当前默认模型ID（任意字符串）
    force_current: bool = False  # 是否强制
    models: Dict[str, ModelConfig] = Field(default_factory=dict)  # 动态模型列表
    keyword_switching: KeywordSwitchingConfig = Field(default_factory=KeywordSwitchingConfig)

class VirtualModel(BaseModel):
    """虚拟模型（包含可扩展的路由配置）"""
    name: str
    proxy_key: str
    base_url: Optional[str] = None
    use: bool = True
    
    # 新的可扩展路由配置
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    
    # 向后兼容：保留旧的 small/big 配置
    # 迁移时自动转换到 routing.models
    
    # 其他配置
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
```

### 11.5 路由引擎（支持动态模型）

```python
# model_router.py
class ModelRouter:
    async def route(
        self, 
        virtual_model: str, 
        user_input: str,
        conversation_id: Optional[str] = None
    ) -> RouteResult:
        """
        模型路由决策（支持动态模型）
        """
        vm_config = self._config_manager.get(f"ai-gateway.virtual_models.{virtual_model}")
        if not vm_config:
            return RouteResult(model_type="small", reason="配置不存在")
        
        routing = vm_config.get("routing", {})
        
        # 1. 检查强制模式
        if routing.get("force_current", False):
            current = routing.get("current", "small")
            return RouteResult(
                model_type=current,
                reason="强制模式",
                confidence=1.0
            )
        
        # 2. 检查关键词切换
        keyword_config = routing.get("keyword_switching", {})
        if keyword_config.get("enabled", False):
            user_input_lower = user_input.lower()
            
            for rule in keyword_config.get("rules", []):
                pattern = rule.get("pattern", "")
                target = rule.get("target", "")
                
                if pattern.lower() in user_input_lower:
                    # 验证目标模型是否存在
                    available_models = routing.get("models", {})
                    if target in available_models:
                        return RouteResult(
                            model_type=target,  # 返回动态模型ID
                            matched_rule=f"keyword:{pattern}",
                            reason=f"关键词匹配: {pattern}",
                            confidence=1.0
                        )
        
        # 3. 使用默认模型
        current = routing.get("current", "small")
        return RouteResult(
            model_type=current,
            reason="使用默认模型"
        )
```

### 11.6 迁移策略（向后兼容）

#### 方案 A：自动迁移（推荐）

在读取配置时自动将旧格式转换为新格式：

```python
def migrate_virtual_model_config(config: dict) -> dict:
    """自动迁移旧配置到新格式"""
    if "routing" in config:
        return config  # 已经是新格式
    
    # 旧格式转换
    routing = {
        "current": config.get("current", "small"),
        "force_current": config.get("force-current", False),
        "models": {
            "small": config.get("small", {}),
            "big": config.get("big", {})
        },
        "keyword_switching": config.get("keyword_switching", {
            "enabled": False,
            "rules": []
        })
    }
    
    config["routing"] = routing
    return config
```

#### 方案 B：双轨支持

同时支持新旧两种配置格式：

```python
# 读取时优先使用新格式， fallback 到旧格式
models = routing.get("models", {
    "small": config.get("small"),
    "big": config.get("big")
})
```

### 11.7 实施阶段

**阶段 1**（当前版本）：
1. 实现新的 `routing` 配置结构
2. 保持只支持 small/big 两个模型
3. 确保代码架构支持未来扩展
4. 添加自动迁移逻辑

**阶段 2**（未来版本）：
1. 添加 "+ 添加模型" 功能
2. 支持任意数量的模型
3. 添加模型优先级排序
4. 更新前端UI支持动态模型

---

## 12. 开发顺序

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

ZS|---
XK|
JN|## 12. RSS模块设计 (RSS Fetcher)
TK|
TV|**文件位置**: `backend/core/rss_fetcher.py`
QT|
MZ|**职责**: RSS订阅管理、文章抓取、内容提取、文章管理
MZ|
HB|### 12.1 数据模型
RT|
HM|```python
@dataclass
class RSSSubscription:
    """RSS订阅源"""
    id: str
    name: str
    url: str
    enabled: bool = True
    update_interval: int = 30  # 分钟
    retention_days: int = 30
    default_permanent: bool = False
    article_count: int = 0
    last_fetch_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class RSSArticle:
    """RSS文章"""
    id: str
    subscription_id: str
    title: str
    url: str
    content: str
    raw_content: str
    content_format: str = "markdown"
    published_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    is_read: bool = False
    knowledge_extracted: bool = False
    knowledge_doc_ids: List[str] = field(default_factory=list)
    fetch_status: str = "summary"  # full_content/rss_summary/blocked/failed
    fetch_method: str = "rss_only"
```

XS|
HB|### 12.2 RSSFetcher类设计
RT|
HM|```python
class RSSFetcher:
    """RSS抓取器 - 管理订阅和文章"""
    
    def __init__(self, db, config_manager):
        self._db = db
        self._config = config_manager
    
    # === 订阅源管理 ===
    
    async def create_subscription(self, data: Dict) -> str:
        """创建订阅源"""
        
    async def list_subscriptions(self, enabled_only: bool = False) -> List[RSSSubscription]:
        """列出所有订阅源"""
        
    async def get_subscription(self, feed_id: str) -> Optional[RSSSubscription]:
        """获取订阅源详情"""
        
    async def update_subscription(self, feed_id: str, data: Dict) -> bool:
        """更新订阅源"""
        
    async def delete_subscription(self, feed_id: str) -> bool:
        """删除订阅源（级联删除所有文章）"""
        
    async def fetch_feed(self, feed_id: str) -> Dict:
        """立即抓取订阅源内容"""
    
    # === 文章管理 ===
    
    async def list_articles(
        self, 
        feed_id: Optional[str] = None, 
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[RSSArticle], int]:
        """列出文章，支持筛选和分页"""
        
    async def get_article(self, article_id: str) -> Optional[RSSArticle]:
        """获取单篇文章详情"""
        
    async def mark_article_read(self, article_id: str, is_read: bool = True) -> bool:
        """标记文章已读/未读状态"""
        
    async def delete_article(self, article_id: str) -> bool:
        """
        删除单篇文章
        
        Args:
            article_id: 文章ID
            
        Returns:
            bool: 是否删除成功
            
        删除操作：
        1. 从 MongoDB 删除文章记录
        2. 如果文章有关联的知识库文档，保留（由知识库管理）
        3. 更新订阅源的文章计数
        """
        
    async def delete_articles(self, article_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除文章
        
        Args:
            article_ids: 文章ID列表
            
        Returns:
            Dict: {
                "success_count": 成功删除数量,
                "failed_count": 失败数量,
                "failed_ids": 失败的文章ID列表
            }
            
        说明：
        - 即使部分删除失败，也会继续处理其他ID
        - 返回详细的删除结果
        """
    
    # === 内容抓取 ===
    
    async def _fetch_full_content(self, url: str) -> Tuple[str, str]:
        """抓取文章完整内容"""
        
    async def _extract_with_readability(self, html: str) -> str:
        """使用readability提取正文"""
```

XS|
HB|### 12.3 API端点设计
RT|
HB|**订阅源端点**:
HM|| 端点 | 方法 | 功能 |
QT||------|------|------|
MZ|| `/admin/ai/v1/rss/feeds` | GET | 获取订阅源列表 |
MZ|| `/admin/ai/v1/rss/feeds` | POST | 创建订阅源 |
MZ|| `/admin/ai/v1/rss/feeds/{id}` | PUT | 更新订阅源 |
MZ|| `/admin/ai/v1/rss/feeds/{id}` | DELETE | 删除订阅源 |
MZ|| `/admin/ai/v1/rss/feeds/{id}/fetch` | POST | 立即抓取 |

XS|
HB|**文章端点**:
HM|| 端点 | 方法 | 功能 |
QT||------|------|------|
MZ|| `/admin/ai/v1/rss/articles` | GET | 获取文章列表 |
MZ|| `/admin/ai/v1/rss/articles/{id}` | GET | 获取文章详情 |
MZ|| `/admin/ai/v1/rss/articles/{id}/read` | POST | 标记已读/未读 |
MZ|| `/admin/ai/v1/rss/articles/{id}` | DELETE | **删除单篇文章** |
MZ|| `/admin/ai/v1/rss/articles/batch` | DELETE | **批量删除文章** |

XS|
HB|### 12.4 删除文章实现细节
RT|
HB|**单篇删除流程**:
HM|```
1. 验证文章ID是否存在
2. 从 MongoDB rss_articles 集合删除文档
3. 更新对应订阅源的 article_count（减1）
4. 返回删除结果
```

XS|
HB|**批量删除流程**:
HM|```
1. 遍历文章ID列表
2. 对每个ID执行删除操作
3. 记录成功和失败的ID
4. 批量更新订阅源文章计数
5. 返回统计结果：成功数、失败数、失败ID列表
```

XS|
HB|### 12.5 错误处理
RT|
HB|| 错误场景 | HTTP状态码 | 错误信息 |
QT||----------|------------|----------|
MZ|| 文章不存在 | 404 | "文章不存在" |
MZ|| 删除失败 | 500 | "删除操作失败: {detail}" |
MZ|| 部分批量删除失败 | 200 | 返回失败列表 |

XS|
XP|**文档版本**: 1.1

**文档版本**: 1.1  
**状态**: 已更新  
**审核人**: 用户确认后实施开发

---

## 文档更新记录

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| 1.1 | 2026-02-14 | 新增第11章：可扩展路由架构设计 | AI Assistant |
| 1.0 | 2026-02-24 | 初始版本 | 开发团队 |
