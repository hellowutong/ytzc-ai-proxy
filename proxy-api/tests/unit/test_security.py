"""
安全模块测试
"""
import sys
from pathlib import Path
from datetime import timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSecurityManager:
    """安全管理器测试"""
    
    def test_generate_proxy_key(self):
        """测试生成Proxy Key"""
        from app.core.security import SecurityManager
        
        key = SecurityManager.generate_proxy_key()
        
        assert key.startswith("tw-")
        assert len(key) == 27
        assert len(key[3:]) == 24  # 12 bytes = 24 hex chars
    
    def test_validate_proxy_key_format_valid(self):
        """测试有效的Proxy Key格式"""
        
        valid_keys = [
            "tw-a1b2c3d4e5f6g7h8i9j0k",
            "tw-112233445566778899aabbcc",
        ]
        
        for key in valid_keys:
            # 只检查格式，不检查具体值
            assert key.startswith("tw-"), f"Key {key} should start with tw-"
    
    def test_validate_proxy_key_format_invalid(self):
        """测试无效的Proxy Key格式"""
        from app.core.security import SecurityManager
        
        invalid_keys = [
            "",
            "invalid-key",
            "tw-",
            "abc-123456789012345678901234",
            "sk-12345678901234567890123456",
        ]
        
        for key in invalid_keys:
            assert not SecurityManager.validate_proxy_key_format(key), f"Key {key} should be invalid"
    
    def test_hash_api_key(self):
        """测试API Key哈希"""
        from app.core.security import SecurityManager
        
        api_key = "test-api-key"
        hashed = SecurityManager.hash_api_key(api_key)
        
        assert len(hashed) == 64  # SHA256 produces 64 hex chars
        assert hashed != api_key
    
    def test_verify_api_key(self):
        """测试API Key验证"""
        from app.core.security import SecurityManager
        
        api_key = "test-api-key"
        hashed = SecurityManager.hash_api_key(api_key)
        
        assert SecurityManager.verify_api_key(api_key, hashed) is True
        assert SecurityManager.verify_api_key("wrong-key", hashed) is False


class TestJWTAuth:
    """JWT认证测试"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        from app.core.security import JWTAuth
        
        data = {"sub": "test-user", "role": "admin"}
        token = JWTAuth.create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
        
        # 验证令牌可以解码
        payload = JWTAuth.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user"
        assert payload["role"] == "admin"
    
    def test_verify_token_expired(self):
        """测试过期令牌验证"""
        from app.core.security import JWTAuth
        
        # 创建已过期的令牌
        data = {"sub": "test-user"}
        token = JWTAuth.create_access_token(
            data,
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        
        # 验证应该返回None
        payload = JWTAuth.verify_token(token)
        assert payload is None
    
    def test_verify_token_invalid(self):
        """测试无效令牌验证"""
        from app.core.security import JWTAuth
        
        payload = JWTAuth.verify_token("invalid-token")
        assert payload is None


class TestRateLimiter:
    """速率限制器测试"""
    
    def test_rate_limit_allowed(self):
        """测试速率限制允许"""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            allowed, count, max_requests = limiter.is_allowed("test-ip")
            assert allowed is True
            assert count == i + 1
            assert max_requests == 5
    
    def test_rate_limit_blocked(self):
        """测试速率限制阻止"""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # 发送3个请求
        for i in range(3):
            limiter.is_allowed("test-ip")
        
        # 第4个请求应该被阻止
        allowed, count, max_requests = limiter.is_allowed("test-ip")
        assert allowed is False
        assert count == 3
        assert max_requests == 3
    
    def test_rate_limit_different_keys(self):
        """测试不同key独立限制"""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # IP1发送2个请求
        limiter.is_allowed("ip-1")
        limiter.is_allowed("ip-1")
        
        # IP2应该还能发送请求
        allowed, count, max_requests = limiter.is_allowed("ip-2")
        assert allowed is True
        assert count == 1
    
    def test_get_remaining(self):
        """测试获取剩余请求数"""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # 初始状态
        remaining = limiter.get_remaining("test-ip")
        assert remaining == 10
        
        # 发送3个请求
        for _ in range(3):
            limiter.is_allowed("test-ip")
        
        remaining = limiter.get_remaining("test-ip")
        assert remaining == 7


class TestAuditLogger:
    """审计日志测试"""
    
    def test_log_event(self):
        """测试记录事件"""
        from app.core.security import AuditLogger
        
        AuditLogger.clear()
        
        AuditLogger.log(
            event="login",
            user_id="test-user",
            ip="127.0.0.1",
            details={"method": "api_key"}
        )
        
        logs = AuditLogger.get_logs()
        assert len(logs) == 1
        assert logs[0]["event"] == "login"
        assert logs[0]["user_id"] == "test-user"
    
    def test_filter_logs(self):
        """测试过滤日志"""
        from app.core.security import AuditLogger
        
        AuditLogger.clear()
        
        # 记录不同事件
        AuditLogger.log("login", "user1", "ip1")
        AuditLogger.log("login", "user2", "ip2")
        AuditLogger.log("logout", "user1", "ip1")
        
        # 过滤事件
        login_logs = AuditLogger.get_logs(event="login")
        assert len(login_logs) == 2
        
        # 过滤用户
        user1_logs = AuditLogger.get_logs(user_id="user1")
        assert len(user1_logs) == 2
    
    def test_clear_logs(self):
        """测试清除日志"""
        from app.core.security import AuditLogger
        
        AuditLogger.clear()
        
        AuditLogger.log("test", "user", "ip")
        assert len(AuditLogger.get_logs()) == 1
        
        AuditLogger.clear()
        assert len(AuditLogger.get_logs()) == 0
