"""
MongoDB 数据库连接模块
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_config


class MongoDB:
    """MongoDB 连接管理类"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """建立MongoDB连接"""
        config = get_config()
        mongodb_url = f"mongodb://{config.mongodb.host}:{config.mongodb.port}"
        
        cls.client = AsyncIOMotorClient(mongodb_url)
        cls.db = cls.client[config.mongodb.database]
        
        # 创建索引
        await cls._create_indexes()
    
    @classmethod
    async def disconnect(cls) -> None:
        """断开MongoDB连接"""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
    
    @classmethod
    async def _create_indexes(cls) -> None:
        """创建必要的索引"""
        if cls.db is None:
            return
        
        # connections 集合索引
        await cls.db["connections"].create_index("proxy_key", unique=True)
        await cls.db["connections"].create_index("created_at")
        
        # sessions 集合索引
        await cls.db["sessions"].create_index("session_id", unique=True)
        await cls.db["sessions"].create_index("proxy_key")
        await cls.db["sessions"].create_index("created_at")
        await cls.db["sessions"].create_index("status")
        
        # skills 集合索引
        await cls.db["skills"].create_index("base_id", unique=True)
        await cls.db["skills"].create_index("created_at")
        
        # backups 集合索引
        await cls.db["backups"].create_index("name", unique=True)
        await cls.db["backups"].create_index("created_at")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if cls.db is None:
            raise RuntimeError("MongoDB not connected. Call MongoDB.connect() first.")
        return cls.db
    
    @classmethod
    def get_collection(cls, name: str):
        """获取集合"""
        return cls.get_db()[name]


async def get_mongodb() -> MongoDB:
    """获取MongoDB实例"""
    return MongoDB


# 便捷函数
def get_connections_collection():
    """获取connections集合"""
    return MongoDB.get_collection("connections")

def get_sessions_collection():
    """获取sessions集合"""
    return MongoDB.get_collection("sessions")

def get_skills_collection():
    """获取skills集合"""
    return MongoDB.get_collection("skills")

def get_backups_collection():
    """获取backups集合"""
    return MongoDB.get_collection("backups")
