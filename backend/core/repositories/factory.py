"""
存储仓库工厂 - 根据配置创建对应实现

提供统一的工厂方法来创建文档存储、向量存储、缓存的仓库实例。
"""

from typing import Dict, Any

from .interfaces import (
    StorageType,
    VectorDBType,
    CacheType,
    IDocumentRepository,
    IVectorRepository,
    ICacheRepository
)


class RepositoryFactory:
    """存储仓库工厂 - 根据配置创建对应实现"""

    _document_impls: Dict[StorageType, type] = {}
    _vector_impls: Dict[VectorDBType, type] = {}
    _cache_impls: Dict[CacheType, type] = {}

    @classmethod
    def register_document(cls, storage_type: StorageType, impl_class: type) -> None:
        """注册文档存储实现

        Args:
            storage_type: 存储类型枚举
            impl_class: 实现类（必须继承IDocumentRepository）
        """
        cls._document_impls[storage_type] = impl_class

    @classmethod
    def register_vector(cls, vector_type: VectorDBType, impl_class: type) -> None:
        """注册向量存储实现

        Args:
            vector_type: 向量数据库类型枚举
            impl_class: 实现类（必须继承IVectorRepository）
        """
        cls._vector_impls[vector_type] = impl_class

    @classmethod
    def register_cache(cls, cache_type: CacheType, impl_class: type) -> None:
        """注册缓存实现

        Args:
            cache_type: 缓存类型枚举
            impl_class: 实现类（必须继承ICacheRepository）
        """
        cls._cache_impls[cache_type] = impl_class

    @classmethod
    def create_document_repository(cls, config: Dict[str, Any]) -> IDocumentRepository:
        """创建文档存储仓库

        Args:
            config: 配置字典，必须包含"type"字段
                {
                    "type": "mongodb",
                    "host": "localhost",
                    "port": 27017,
                    ...
                }

        Returns:
            IDocumentRepository实现实例

        Raises:
            ValueError: 不支持的存储类型
        """
        storage_type = StorageType(config["type"])
        impl_class = cls._document_impls.get(storage_type)

        if not impl_class:
            raise ValueError(f"不支持的存储类型: {storage_type}")

        # 过滤掉type字段，其余作为构造参数
        return impl_class(**{k: v for k, v in config.items() if k != "type"})

    @classmethod
    def create_vector_repository(cls, config: Dict[str, Any]) -> IVectorRepository:
        """创建向量存储仓库

        Args:
            config: 配置字典，必须包含"type"字段
                {
                    "type": "qdrant",
                    "host": "localhost",
                    "port": 6333,
                    ...
                }

        Returns:
            IVectorRepository实现实例

        Raises:
            ValueError: 不支持的向量数据库类型
        """
        vector_type = VectorDBType(config["type"])
        impl_class = cls._vector_impls.get(vector_type)

        if not impl_class:
            raise ValueError(f"不支持的向量数据库: {vector_type}")

        # 过滤掉type字段，其余作为构造参数
        return impl_class(**{k: v for k, v in config.items() if k != "type"})

    @classmethod
    def create_cache_repository(cls, config: Dict[str, Any]) -> ICacheRepository:
        """创建缓存仓库

        Args:
            config: 配置字典，必须包含"type"字段
                {
                    "type": "redis",
                    "host": "localhost",
                    "port": 6379,
                    ...
                }

        Returns:
            ICacheRepository实现实例

        Raises:
            ValueError: 不支持的缓存类型
        """
        cache_type = CacheType(config["type"])
        impl_class = cls._cache_impls.get(cache_type)

        if not impl_class:
            raise ValueError(f"不支持的缓存类型: {cache_type}")

        # 过滤掉type字段，其余作为构造参数
        return impl_class(**{k: v for k, v in config.items() if k != "type"})
