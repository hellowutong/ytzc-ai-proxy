"""
MongoDB connection with Motor async driver.

Features:
- Async connection pooling
- Connection retry logic
- Health check support
- Auto-reconnection
"""

import asyncio
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from core.config_manager import get_config
from core.exceptions import MongoDBConnectionError
from core.logger import get_logger

logger = get_logger("mongodb")


class MongoDBClient:
    """MongoDB client with connection pooling and retry logic."""
    
    _instance: Optional['MongoDBClient'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls) -> 'MongoDBClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._config: Optional[Dict[str, Any]] = None
    
    async def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to MongoDB with retry logic.
        
        Args:
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        if self._client is not None:
            return
        
        # Load config
        self._config = get_config("storage.mongodb", {})
        
        host = self._config.get("host", "localhost")
        port = self._config.get("port", 27017)
        username = self._config.get("username")
        password = self._config.get("password")
        database = self._config.get("database", "ai_gateway")
        
        # Build connection string
        if username and password:
            uri = f"mongodb://{username}:{password}@{host}:{port}/{database}"
        else:
            uri = f"mongodb://{host}:{port}/{database}"
        
        # Connect with retry
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to MongoDB at {host}:{port} (attempt {attempt + 1}/{max_retries})")
                
                self._client = AsyncIOMotorClient(
                    uri,
                    serverSelectionTimeoutMS=5000,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=45000,
                )
                
                # Verify connection
                await self._client.admin.command('ping')
                
                self._db = self._client[database]
                
                # Create collections if they don't exist
                await self._ensure_collections()
                
                logger.info("MongoDB connected successfully")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise MongoDBConnectionError(f"Failed to connect to MongoDB after {max_retries} attempts: {e}")
    
    async def _ensure_collections(self):
        """Ensure required collections exist."""
        if self._db is None:
            return
        
        collections = await self._db.list_collection_names()
        
        # Create system_logs collection
        if "system_logs" not in collections:
            await self._db.create_collection("system_logs")
            await self._db.system_logs.create_index("timestamp")
            await self._db.system_logs.create_index("level")
            await self._db.system_logs.create_index("source")
            logger.info("Created system_logs collection")
        
        # Create operation_logs collection
        if "operation_logs" not in collections:
            await self._db.create_collection("operation_logs")
            await self._db.operation_logs.create_index("timestamp")
            await self._db.operation_logs.create_index("level")
            await self._db.operation_logs.create_index("operation")
            await self._db.operation_logs.create_index("user_id")
            logger.info("Created operation_logs collection")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB disconnected")
    
    async def health_check(self) -> bool:
        """Check if MongoDB connection is healthy."""
        if not self._client:
            return False
        
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """Get MongoDB client."""
        return self._client
    
    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        """Get MongoDB database."""
        return self._db
    
    @property
    def system_logs(self):
        """Get system_logs collection."""
        if self._db:
            return self._db.system_logs
        return None
    
    @property
    def operation_logs(self):
        """Get operation_logs collection."""
        if self._db:
            return self._db.operation_logs
        return None


# Global instance accessor
async def get_mongodb_client() -> MongoDBClient:
    """Get MongoDB client instance."""
    client = MongoDBClient()
    if client.client is None:
        await client.connect()
    return client


async def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    client = await get_mongodb_client()
    return client.db
