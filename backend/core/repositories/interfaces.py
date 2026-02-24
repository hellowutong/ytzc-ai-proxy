"""
存储层抽象接口定义

提供文档存储、向量存储、缓存的抽象接口，支持多种后端实现。
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class StorageType(str, Enum):
    """文档存储类型枚举"""
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    DYNAMODB = "dynamodb"


class VectorDBType(str, Enum):
    """向量数据库类型枚举"""
    QDRANT = "qdrant"
    MILVUS = "milvus"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class CacheType(str, Enum):
    """缓存类型枚举"""
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"


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
        """插入单条文档，返回ID

        Args:
            collection: 集合/表名
            document: 文档数据

        Returns:
            插入文档的ID
        """
        pass

    @abstractmethod
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查询单条文档

        Args:
            collection: 集合/表名
            query: 查询条件

        Returns:
            匹配的文档，未找到返回None
        """
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
        """查询多条文档

        Args:
            collection: 集合/表名
            query: 查询条件
            sort: 排序规则 [(field, direction), ...]
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            (文档列表, 总数)
        """
        pass

    @abstractmethod
    async def update_one(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """更新单条文档

        Args:
            collection: 集合/表名
            query: 查询条件
            update: 更新内容

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """删除单条文档

        Args:
            collection: 集合/表名
            query: 查询条件

        Returns:
            是否删除成功
        """
        pass


class IVectorRepository(ABC):
    """向量存储抽象接口"""

    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """关闭连接"""
        pass

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance: str = "cosine"
    ) -> None:
        """创建向量集合

        Args:
            name: 集合名称
            dimension: 向量维度
            distance: 距离度量方式 (cosine, euclid, dot)
        """
        pass

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        vectors: List[Dict[str, Any]]
    ) -> None:
        """插入或更新向量

        Args:
            collection: 集合名称
            vectors: 向量数据列表
                [{"id": "uuid", "vector": [0.1, ...], "payload": {...}}, ...]
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
        """向量相似度搜索

        Args:
            collection: 集合名称
            query_vector: 查询向量
            top_k: 返回结果数量
            threshold: 相似度阈值
            filters: 过滤条件

        Returns:
            搜索结果列表 [{"id": str, "score": float, "payload": dict}, ...]
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, ids: List[str]) -> None:
        """删除向量

        Args:
            collection: 集合名称
            ids: 要删除的向量ID列表
        """
        pass


class ICacheRepository(ABC):
    """缓存抽象接口"""

    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """关闭连接"""
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存

        Args:
            key: 缓存键
        """
        pass

    @abstractmethod
    async def lpush(self, queue: str, value: str) -> None:
        """队列左侧推入（LPush）

        Args:
            queue: 队列名称
            value: 要推入的值
        """
        pass

    @abstractmethod
    async def rpop(self, queue: str, timeout: int = 0) -> Optional[str]:
        """队列右侧弹出（BRPop）

        Args:
            queue: 队列名称
            timeout: 超时时间（秒），0表示阻塞

        Returns:
            弹出的值，超时返回None
        """
        pass
