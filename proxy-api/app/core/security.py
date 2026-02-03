"""
安全模块 - 认证授权
提供API Key认证、JWT认证、速率限制等功能
"""
import hashlib
import hmac
import time
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request
from collections import defaultdict
from threading import Lock


# API Key认证头
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# JWT Bearer认证
bearer_scheme = HTTPBearer(auto_error=False)


class RateLimiter:
    """滑动窗口速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def _cleanup_old(self, key: str, current_time: float) -> None:
        """清理旧请求记录"""
        cutoff = current_time - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
    
    def is_allowed(self, key: str) -> Tuple[bool, int, int]:
        """检查是否允许请求"""
        with self.lock:
            current_time = time.time()
            self._cleanup_old(key, current_time)
            
            count = len(self.requests[key])
            if count >= self.max_requests:
                return False, count, self.max_requests
            
            self.requests[key].append(current_time)
            return True, count + 1, self.max_requests
    
    def get_remaining(self, key: str) -> int:
        """获取剩余请求数"""
        with self.lock:
            current_time = time.time()
            self._cleanup_old(key, current_time)
            return max(0, self.max_requests - len(self.requests[key]))


# 全局速率限制器
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


class SecurityManager:
    """安全管理器"""
    
    # 密钥缓存
    _key_cache: Dict[str, Dict] = {}
    _cache_lock = Lock()
    _cache_ttl = 300  # 5分钟缓存
    
    # 外部引用 connections_db (由 main.py 设置)
    _connections_ref: Optional[List[Dict]] = None
    
    @classmethod
    def set_connections_ref(cls, connections: List[Dict]):
        """设置 connections_db 引用"""
        cls._connections_ref = connections
        cls.clear_key_cache()  # 清除缓存
    
    @classmethod
    def generate_proxy_key(cls) -> str:
        """生成Proxy Key"""
        return f"tw-{secrets.token_hex(12)}"
    
    @classmethod
    def hash_api_key(cls, api_key: str) -> str:
        """哈希API Key"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @classmethod
    def verify_api_key(cls, api_key: str, stored_hash: str) -> bool:
        """验证API Key"""
        return hmac.compare_digest(cls.hash_api_key(api_key), stored_hash)
    
    @classmethod
    def validate_proxy_key_format(cls, proxy_key: str) -> bool:
        """验证Proxy Key格式"""
        if not proxy_key:
            return False
        if not proxy_key.startswith("tw-"):
            return False
        if len(proxy_key) != 27:  # tw- + 24 hex chars
            return False
        try:
            bytes.fromhex(proxy_key[3:])
            return True
        except ValueError:
            return False
    
    @classmethod
    def get_connection_by_key(cls, proxy_key: str) -> Optional[Dict]:
        """
        根据Proxy Key获取连接信息
        实际项目中应该查询数据库
        """
        with cls._cache_lock:
            # 检查缓存
            if proxy_key in cls._key_cache:
                cached = cls._key_cache[proxy_key]
                if time.time() - cached["cached_at"] < cls._cache_ttl:
                    return cached["data"]
        
        # 模拟从数据库查询
        # 实际实现应该查询MongoDB
        connection = cls._simulate_db_lookup(proxy_key)
        
        if connection:
            with cls._cache_lock:
                cls._key_cache[proxy_key] = {
                    "data": connection,
                    "cached_at": time.time()
                }
        
        return connection
    
    @classmethod
    def _simulate_db_lookup(cls, proxy_key: str) -> Optional[Dict]:
        """从 connections_db 查找连接"""
        if cls._connections_ref is None:
            return None
        
        for conn in cls._connections_ref:
            if conn.get("proxy_key") == proxy_key:
                return conn
        return None
    
    @classmethod
    def clear_key_cache(cls, proxy_key: str = None):
        """清除Key缓存"""
        with cls._cache_lock:
            if proxy_key:
                cls._key_cache.pop(proxy_key, None)
            else:
                cls._key_cache.clear()


class JWTAuth:
    """JWT认证管理器"""
    
    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    @classmethod
    def create_access_token(cls, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @classmethod
    def decode_token(cls, token: str) -> Optional[Dict]:
        """解码令牌"""
        return cls.verify_token(token)


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header)
) -> Dict:
    """
    验证API Key
    支持两种格式：
    1. Bearer token: Authorization: Bearer tw-xxx
    2. Direct key: Authorization: tw-xxx
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 提取key
    if api_key.startswith("Bearer "):
        proxy_key = api_key[7:]
    else:
        proxy_key = api_key
    
    # 验证格式
    if not SecurityManager.validate_proxy_key_format(proxy_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 获取连接信息
    connection = SecurityManager.get_connection_by_key(proxy_key)
    if not connection:
        raise HTTPException(
            status_code=401,
            detail="Invalid or disabled API Key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查状态
    if connection.get("status") != "enabled":
        raise HTTPException(
            status_code=403,
            detail="API Key is disabled"
        )
    
    return connection


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> Dict:
    """验证JWT Token"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = JWTAuth.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload


async def verify_auth(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    jwt_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Dict:
    """
    综合认证 - 优先使用API Key
    """
    # 优先尝试API Key认证
    if api_key:
        try:
            return await verify_api_key(request, api_key)
        except HTTPException:
            pass
    
    # 尝试JWT认证
    if jwt_token:
        try:
            return await verify_jwt_token(jwt_token)
        except HTTPException:
            pass
    
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"}
    )


class AuditLogger:
    """审计日志"""
    
    logs: list = []
    max_logs = 1000
    
    @classmethod
    def log(cls, event: str, user_id: str, ip: str, details: Dict = None):
        """记录审计日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "user_id": user_id,
            "ip": ip,
            "details": details or {}
        }
        
        cls.logs.append(log_entry)
        
        # 保持日志数量
        if len(cls.logs) > cls.max_logs:
            cls.logs = cls.logs[-cls.max_logs:]
    
    @classmethod
    def get_logs(cls, event: str = None, user_id: str = None, limit: int = 100) -> list:
        """获取审计日志"""
        logs = cls.logs
        
        if event:
            logs = [log for log in logs if log["event"] == event]
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]
        
        return logs[-limit:]
    
    @classmethod
    def clear(cls):
        """清除日志"""
        cls.logs = []


async def check_rate_limit(request: Request) -> None:
    """检查速率限制"""
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 检查速率限制
    allowed, current, max_requests = rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Maximum {max_requests} requests per minute.",
                "retry_after": 60
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Current": str(current)
            }
        )


def get_rate_limit_headers(request: Request) -> Dict[str, str]:
    """获取速率限制头"""
    client_ip = request.client.host if request.client else "unknown"
    remaining = rate_limiter.get_remaining(client_ip)
    return {
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Current": str(100 - remaining)
    }
