"""
数据库管理器 - 统一管理MongoDB、Redis、Qdrant连接
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from qdrant_client import QdrantClient


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.mongodb: Optional[AsyncIOMotorClient] = None
        self.redis: Optional[redis.Redis] = None
        self.qdrant: Optional[QdrantClient] = None
    
    async def connect(self):
        """建立所有数据库连接"""
        await self._connect_mongodb()
        await self._connect_redis()
        await self._connect_qdrant()
    
    async def disconnect(self):
        """关闭所有数据库连接"""
        if self.mongodb:
            self.mongodb.close()
        if self.redis:
            await self.redis.close()
        # Qdrant客户端不需要显式关闭
    
    async def _connect_mongodb(self):
        """连接MongoDB"""
        try:
            mongodb_config = self.config.get('storage.mongodb', {})
            host = mongodb_config.get('host', 'localhost')
            port = mongodb_config.get('port', 27017)
            username = mongodb_config.get('username', 'admin')
            password = mongodb_config.get('password', 'password')
            database = mongodb_config.get('database', 'ai_gateway')
            
            uri = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
            self.mongodb = AsyncIOMotorClient(uri)
            
            # 测试连接
            await self.mongodb.admin.command('ping')
            print(f"✅ MongoDB连接成功: {host}:{port}")
        except Exception as e:
            print(f"❌ MongoDB连接失败: {e}")
            raise
    
    async def _connect_redis(self):
        """连接Redis"""
        try:
            redis_config = self.config.get('storage.redis', {})
            host = redis_config.get('host', 'localhost')
            port = redis_config.get('port', 6379)
            db = redis_config.get('db', 0)
            
            self.redis = await redis.from_url(
                f"redis://{host}:{port}/{db}",
                decode_responses=True
            )
            
            # 测试连接
            await self.redis.ping()
            print(f"✅ Redis连接成功: {host}:{port}")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            raise
    
    async def _connect_qdrant(self):
        """连接Qdrant"""
        try:
            qdrant_config = self.config.get('storage.qdrant', {})
            host = qdrant_config.get('host', 'localhost')
            port = qdrant_config.get('port', 6333)
            
            self.qdrant = QdrantClient(host=host, port=port)
            
            # 测试连接
            self.qdrant.get_collections()
            print(f"✅ Qdrant连接成功: {host}:{port}")
        except Exception as e:
            print(f"❌ Qdrant连接失败: {e}")
            raise
    
    def get_mongodb_database(self, db_name: str = None):
        """获取MongoDB数据库实例"""
        if not db_name:
            db_name = self.config.get('storage.mongodb.database', 'ai_gateway')
        return self.mongodb[db_name]
    
    def get_redis_client(self):
        """获取Redis客户端"""
        return self.redis
    
    def get_qdrant_client(self):
        """获取Qdrant客户端"""
        return self.qdrant
