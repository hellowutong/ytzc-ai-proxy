"""
Redis 缓存服务
提供会话缓存、配置缓存、速率限制等缓存功能
"""
import json
import redis
from typing import Optional


class RedisCache:
    """Redis 缓存客户端"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False

    def _get_config(self):
        """延迟获取配置"""
        from app.core.config import get_config
        return get_config()

    def connect(self) -> bool:
        """建立 Redis 连接"""
        try:
            config = self._get_config()
            redis_config = getattr(config, 'redis', None)
            
            host = getattr(redis_config, 'host', 'localhost') if redis_config else 'localhost'
            port = int(getattr(redis_config, 'port', 6379)) if redis_config else 6379
            db = int(getattr(redis_config, 'db', 0)) if redis_config else 0
            password = getattr(redis_config, 'password', None) if redis_config else None
            
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self._client.ping()
            self._connected = True
            return True
        except redis.ConnectionError:
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self._connected:
            return None
        return self._client.get(key)

    def set(
        self,
        key: str,
        value: str,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        if not self._connected:
            return False
        if expire_seconds:
            return self._client.setex(key, expire_seconds, value)
        return self._client.set(key, value)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected:
            return False
        return self._client.delete(key) > 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected:
            return False
        return self._client.exists(key) > 0

    def incr(self, key: str) -> int:
        """自增"""
        if not self._connected:
            return 0
        return self._client.incr(key)

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._connected:
            return False
        return self._client.expire(key, seconds)

    def get_json(self, key: str) -> Optional[dict]:
        """获取 JSON 缓存"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(
        self,
        key: str,
        value: dict,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """设置 JSON 缓存"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return self.set(key, json_str, expire_seconds)
        except (TypeError, ValueError):
            return False

    def hset(self, name: str, key: str, value: str) -> bool:
        """哈希表设置"""
        if not self._connected:
            return False
        return self._client.hset(name, key, value)

    def hget(self, name: str, key: str) -> Optional[str]:
        """哈希表获取"""
        if not self._connected:
            return None
        return self._client.hget(name, key)

    def hgetall(self, name: str) -> dict:
        """获取哈希表所有字段"""
        if not self._connected:
            return {}
        return self._client.hgetall(name)

    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._connected = False


class SessionCache:
    """会话缓存管理器"""

    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.prefix = "session:"
        self.default_ttl = 3600  # 1小时

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话缓存"""
        key = f"{self.prefix}{session_id}"
        return self.cache.get_json(key)

    def set_session(self, session_id: str, data: dict, ttl: int = None) -> bool:
        """设置会话缓存"""
        key = f"{self.prefix}{session_id}"
        return self.cache.set_json(key, data, ttl or self.default_ttl)

    def delete_session(self, session_id: str) -> bool:
        """删除会话缓存"""
        key = f"{self.prefix}{session_id}"
        return self.cache.delete(key)

    def invalidate_session(self, session_id: str) -> bool:
        """使会话缓存失效"""
        return self.delete_session(session_id)


class ConfigCache:
    """配置缓存管理器"""

    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.prefix = "config:"
        self.default_ttl = 300  # 5分钟

    def get(self, config_key: str) -> Optional[str]:
        """获取配置"""
        key = f"{self.prefix}{config_key}"
        return self.cache.get(key)

    def set(self, config_key: str, value: str, ttl: int = None) -> bool:
        """设置配置"""
        key = f"{self.prefix}{config_key}"
        return self.cache.set(key, value, ttl or self.default_ttl)

    def invalidate(self, config_key: str) -> bool:
        """使配置缓存失效"""
        key = f"{self.prefix}{config_key}"
        return self.cache.delete(key)


class RateLimitCache:
    """速率限制缓存"""

    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.prefix = "ratelimit:"

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        检查速率限制

        Returns:
            (是否允许, 剩余请求数)
        """
        key = f"{self.prefix}{identifier}"

        if not self.cache.is_connected:
            return True, max_requests

        current = self.cache.incr(key)

        if current == 1:
            self.cache.expire(key, window_seconds)

        remaining = max(0, max_requests - current)

        if current > max_requests:
            return False, 0

        return True, remaining

    def get_remaining(self, identifier: str, max_requests: int) -> int:
        """获取剩余请求数"""
        key = f"{self.prefix}{identifier}"
        if not self.cache.exists(key):
            return max_requests

        current = int(self.cache.get(key) or 0)
        return max(0, max_requests - current)


class ProviderCache:
    """AI 提供商缓存"""

    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.prefix = "provider:"
        self.default_ttl = 600  # 10分钟

    def get_providers(self) -> Optional[dict]:
        """获取提供商配置缓存"""
        return self.cache.get_json(f"{self.prefix}all")

    def set_providers(self, providers: dict) -> bool:
        """缓存提供商配置"""
        return self.cache.set_json(f"{self.prefix}all", providers, self.default_ttl)

    def invalidate_providers(self) -> bool:
        """使提供商缓存失效"""
        return self.cache.delete(f"{self.prefix}all")

    def get_model_list(self, provider: str) -> Optional[list]:
        """获取模型列表缓存"""
        return self.cache.get_json(f"{self.prefix}{provider}:models")

    def set_model_list(self, provider: str, models: list) -> bool:
        """缓存模型列表"""
        key = f"{self.prefix}{provider}:models"
        return self.cache.set_json(key, models, self.default_ttl)


cache = RedisCache()
session_cache = SessionCache(cache)
config_cache = ConfigCache(cache)
rate_limit_cache = RateLimitCache(cache)
provider_cache = ProviderCache(cache)


def init_cache() -> bool:
    """初始化缓存连接"""
    return cache.connect()


def close_cache():
    """关闭缓存连接"""
    cache.close()
