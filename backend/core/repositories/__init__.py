"""
存储层抽象模块

提供统一的存储接口，支持多种后端实现：
- 文档存储：MongoDB、PostgreSQL、MySQL、DynamoDB
- 向量存储：Qdrant、Milvus、Pinecone、Weaviate
- 缓存：Redis、RabbitMQ、Kafka

Usage:
    from core.repositories import RepositoryFactory

    # 创建仓库
    doc_repo = RepositoryFactory.create_document_repository({
        "type": "mongodb",
        "host": "localhost",
        "port": 27017
    })

    # 连接
    await doc_repo.connect()

    # 使用
    doc_id = await doc_repo.insert_one("users", {"name": "Alice"})
"""

# 导出接口
from .interfaces import (
    StorageType,
    VectorDBType,
    CacheType,
    IDocumentRepository,
    IVectorRepository,
    ICacheRepository,
)

# 导出工厂
from .factory import RepositoryFactory

# 导出适配器
from .mongodb_adapter import MongoDBAdapter
from .qdrant_adapter import QdrantAdapter
from .redis_adapter import RedisAdapter

# 注册默认实现
RepositoryFactory.register_document(StorageType.MONGODB, MongoDBAdapter)
RepositoryFactory.register_vector(VectorDBType.QDRANT, QdrantAdapter)
RepositoryFactory.register_cache(CacheType.REDIS, RedisAdapter)

__all__ = [
    # 枚举类型
    "StorageType",
    "VectorDBType",
    "CacheType",
    # 接口
    "IDocumentRepository",
    "IVectorRepository",
    "ICacheRepository",
    # 工厂
    "RepositoryFactory",
    # 适配器
    "MongoDBAdapter",
    "QdrantAdapter",
    "RedisAdapter",
]
