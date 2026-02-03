"""
Redis 缓存单元测试
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.infrastructure.cache.redis_cache import (
    RedisCache,
    SessionCache,
    ConfigCache,
    RateLimitCache,
    ProviderCache
)


class TestRedisCache:
    """Redis 缓存测试"""

    def setup_method(self):
        self.cache = RedisCache()
        self.cache._client = MagicMock()
        self.cache._connected = True

    def test_get_returns_value(self):
        """测试获取缓存值"""
        self.cache._client.get.return_value = "test_value"
        result = self.cache.get("test_key")
        assert result == "test_value"
        self.cache._client.get.assert_called_once_with("test_key")

    def test_set_with_ttl(self):
        """测试设置缓存值（含过期时间）"""
        self.cache.set("test_key", "test_value", 300)
        self.cache._client.setex.assert_called_once_with("test_key", 300, "test_value")

    def test_set_without_ttl(self):
        """测试设置缓存值（无过期时间）"""
        self.cache.set("test_key", "test_value")
        self.cache._client.set.assert_called_once_with("test_key", "test_value")

    def test_delete(self):
        """测试删除缓存"""
        self.cache._client.delete.return_value = 1
        result = self.cache.delete("test_key")
        assert result is True
        self.cache._client.delete.assert_called_once_with("test_key")

    def test_exists(self):
        """测试键存在检查"""
        self.cache._client.exists.return_value = 1
        result = self.cache.exists("test_key")
        assert result is True

    def test_get_json_valid(self):
        """测试获取 JSON 缓存（有效）"""
        self.cache._client.get.return_value = '{"key": "value"}'
        result = self.cache.get_json("test_key")
        assert result == {"key": "value"}

    def test_get_json_invalid(self):
        """测试获取 JSON 缓存（无效）"""
        self.cache._client.get.return_value = "invalid json"
        result = self.cache.get_json("test_key")
        assert result is None

    def test_set_json(self):
        """测试设置 JSON 缓存"""
        self.cache._client.set.return_value = True
        result = self.cache.set_json("test_key", {"key": "value"})
        assert result is True
        self.cache._client.set.assert_called_once()

    def test_hset(self):
        """测试哈希表设置"""
        self.cache.hset("hash_name", "field", "value")
        self.cache._client.hset.assert_called_once_with("hash_name", "field", "value")

    def test_hget(self):
        """测试哈希表获取"""
        self.cache._client.hget.return_value = "value"
        result = self.cache.hget("hash_name", "field")
        assert result == "value"

    def test_hgetall(self):
        """测试获取哈希表所有字段"""
        self.cache._client.hgetall.return_value = {"f1": "v1", "f2": "v2"}
        result = self.cache.hgetall("hash_name")
        assert result == {"f1": "v1", "f2": "v2"}

    def test_not_connected_get(self):
        """测试未连接时的获取操作"""
        self.cache._connected = False
        result = self.cache.get("test_key")
        assert result is None

    def test_not_connected_set(self):
        """测试未连接时的设置操作"""
        self.cache._connected = False
        result = self.cache.set("test_key", "value")
        assert result is False


class TestSessionCache:
    """会话缓存测试"""

    def setup_method(self):
        self.mock_cache = MagicMock()
        self.session_cache = SessionCache(self.mock_cache)

    def test_get_session(self):
        """测试获取会话"""
        self.mock_cache.get_json.return_value = {"id": "test", "title": "Test"}
        result = self.session_cache.get_session("test_session")
        assert result == {"id": "test", "title": "Test"}
        self.mock_cache.get_json.assert_called_once_with("session:test_session")

    def test_set_session(self):
        """测试设置会话"""
        self.mock_cache.set_json.return_value = True
        result = self.session_cache.set_session("test_session", {"title": "Test"})
        assert result is True

    def test_delete_session(self):
        """测试删除会话"""
        self.mock_cache.delete.return_value = True
        result = self.session_cache.delete_session("test_session")
        assert result is True


class TestConfigCache:
    """配置缓存测试"""

    def setup_method(self):
        self.mock_cache = MagicMock()
        self.config_cache = ConfigCache(self.mock_cache)

    def test_get_config(self):
        """测试获取配置"""
        self.mock_cache.get.return_value = "config_value"
        result = self.config_cache.get("test_config")
        assert result == "config_value"

    def test_set_config(self):
        """测试设置配置"""
        self.mock_cache.set.return_value = True
        result = self.config_cache.set("test_config", "value")
        assert result is True


class TestRateLimitCache:
    """速率限制缓存测试"""

    def setup_method(self):
        self.mock_cache = MagicMock()
        self.rate_limit_cache = RateLimitCache(self.mock_cache)

    def test_allow_first_request(self):
        """测试首次请求允许"""
        self.mock_cache.incr.return_value = 1
        self.mock_cache.expire.return_value = True

        allowed, remaining = self.rate_limit_cache.check_rate_limit("user1", 10, 60)

        assert allowed is True
        assert remaining == 9

    def test_block_exceeded_requests(self):
        """测试超出限制阻止"""
        self.mock_cache.incr.return_value = 11

        allowed, remaining = self.rate_limit_cache.check_rate_limit("user1", 10, 60)

        assert allowed is False
        assert remaining == 0

    def test_get_remaining(self):
        """测试获取剩余请求数"""
        self.mock_cache.exists.return_value = True
        self.mock_cache.get.return_value = "5"

        remaining = self.rate_limit_cache.get_remaining("user1", 10)

        assert remaining == 5


class TestProviderCache:
    """提供商缓存测试"""

    def setup_method(self):
        self.mock_cache = MagicMock()
        self.provider_cache = ProviderCache(self.mock_cache)

    def test_get_providers(self):
        """测试获取提供商"""
        self.mock_cache.get_json.return_value = {"openai": {}, "deepseek": {}}
        result = self.provider_cache.get_providers()
        assert result == {"openai": {}, "deepseek": {}}

    def test_set_providers(self):
        """测试设置提供商"""
        self.mock_cache.set_json.return_value = True
        result = self.provider_cache.set_providers({"openai": {}})
        assert result is True

    def test_get_model_list(self):
        """测试获取模型列表"""
        self.mock_cache.get_json.return_value = ["gpt-4o", "gpt-3.5-turbo"]
        result = self.provider_cache.get_model_list("openai")
        assert result == ["gpt-4o", "gpt-3.5-turbo"]
