"""
Redis connection with async support.

Features:
- Connection pooling
- Connection retry logic
- Health check support
"""

import asyncio
from typing import Any, Dict, Optional
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError

from core.config_manager import get_config
from core.exceptions import RedisConnectionError as CustomRedisConnectionError
from core.logger import get_logger

logger = get_logger("redis")


class RedisClient:
    """Redis client with connection pooling and retry logic."""
    
    _instance: Optional['RedisClient'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls) -> 'RedisClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[aioredis.Redis] = None
        self._config: Optional[Dict[str, Any]] = None
    
    async def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to Redis with retry logic.
        
        Args:
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        if self._client is not None:
            return
        
        # Load config
        self._config = get_config("storage.redis", {})

        host = self._config.get("host", "localhost")
        port = self._config.get("port", 6379)
        password = self._config.get("password")

        # Connect with retry
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Redis at {host}:{port} (attempt {attempt + 1}/{max_retries})")

                self._client = aioredis.Redis(
                    host=host,
                    port=port,
                    password=password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30,
                    max_connections=50,
                )
                
                # Verify connection
                await self._client.ping()
                
                logger.info("Redis connected successfully")
                return
                
            except (RedisConnectionError, TimeoutError) as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise CustomRedisConnectionError(f"Failed to connect to Redis after {max_retries} attempts: {e}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis disconnected")
    
    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        if not self._client:
            return False
        
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    @property
    def client(self) -> Optional[aioredis.Redis]:
        """Get Redis client."""
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self._client:
            return None
        return await self._client.get(key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """Set key-value pair with optional expiration."""
        if not self._client:
            return
        await self._client.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """Delete key."""
        if not self._client:
            return
        await self._client.delete(key)


# Global instance accessor
async def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    client = RedisClient()
    if client.client is None:
        await client.connect()
    return client
