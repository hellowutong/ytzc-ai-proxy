"""
核心配置模块
"""
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache
import yaml
import os

# 配置文件路径常量 - 供测试使用
CONFIG_FILE = Path(__file__).parent.parent.parent / "config.yml"


class AppConfig:
    """应用配置"""
    def __init__(self, data: Dict[str, Any]):
        self.host: str = data.get("host", "0.0.0.0")
        self.port: int = data.get("port", 8080)
        self.data_path: str = data.get("data_path", "./data")
        self.session_timeout: int = data.get("session_timeout", 1800)
        self.model_timeout: int = data.get("model_timeout", 30000)


class MongoDBConfig:
    """MongoDB 配置"""
    def __init__(self, data: Dict[str, Any]):
        self.host: str = data.get("host", "localhost")
        self.port: int = data.get("port", 27017)
        self.username: str = data.get("username", "")
        self.password: str = data.get("password", "")
        self.database: str = data.get("database", "ytzc_ai_proxy")
        self.auth_source: str = data.get("auth_source", "admin")
    
    @property
    def url(self) -> str:
        """生成 MongoDB 连接 URL"""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"mongodb://{self.host}:{self.port}"


class QdrantConfig:
    """Qdrant 配置"""
    def __init__(self, data: Dict[str, Any]):
        self.host: str = data.get("host", "localhost")
        self.port: int = data.get("port", 6333)
        self.api_key: Optional[str] = data.get("api_key")
        self.https: bool = data.get("https", False)
    
    @property
    def url(self) -> str:
        """生成 Qdrant 连接 URL"""
        protocol = "https" if self.https else "http"
        return f"{protocol}://{self.host}:{self.port}"


class RedisConfig:
    """Redis 配置"""
    def __init__(self, data: Dict[str, Any]):
        self.host: str = data.get("host", "localhost")
        self.port: int = data.get("port", 6379)
        self.db: int = data.get("db", 0)
        self.password: Optional[str] = data.get("password")
        self.key_prefix: str = data.get("key_prefix", "tw_ai_saver:")
        self.session_ttl: int = data.get("session_ttl", 3600)
        self.config_ttl: int = data.get("config_ttl", 300)
        self.provider_ttl: int = data.get("provider_ttl", 600)


class StrategyConfig:
    """调度策略配置"""
    def __init__(self, data: Dict[str, Any]):
        self.fail_threshold: int = data.get("fail_threshold", 3)
        self.small_model_retry: int = data.get("small_model_retry", 0)


class ProviderConfig:
    """供应商配置"""
    def __init__(self, data: Dict[str, Any]):
        self.name: str = data.get("name", "")
        self.small_model: Dict[str, str] = data.get("small_model", {})
        self.big_model: Dict[str, str] = data.get("big_model", {})
        self.proxy_key: str = data.get("proxy_key", "")


class ThemeConfig:
    """主题配置"""
    def __init__(self, data: Dict[str, Any]):
        self.light: Dict[str, str] = data.get("light", {
            "primary": "#409EFF",
            "bg": "#F5F7FA",
            "card": "#FFFFFF",
            "text": "#303133"
        })
        self.dark: Dict[str, str] = data.get("dark", {
            "primary": "#409EFF",
            "bg": "#141414",
            "card": "#1D1D1D",
            "text": "#E5EAF3"
        })


class LoggingConfig:
    """日志配置"""
    def __init__(self, data: Dict[str, Any]):
        self.level: str = data.get("level", "INFO")
        self.format: str = data.get("format", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class Config:
    """
    全局配置类 - 单例模式
    
    从 config.yml 文件加载配置，支持环境变量覆盖
    """
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """从 YAML 文件加载配置"""
        config_path = self._find_config_file()
        
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        
        # 应用环境变量覆盖
        data = self._apply_env_overrides(data)
        
        # 初始化各配置类
        self.app = AppConfig(data.get("app", {}))
        self.mongodb = MongoDBConfig(data.get("mongodb", {}))
        self.qdrant = QdrantConfig(data.get("qdrant", {}))
        self.redis = RedisConfig(data.get("redis", {}))
        self.strategy = StrategyConfig(data.get("strategy", {}))
        self.providers = [ProviderConfig(p) for p in data.get("providers", [])]
        self.theme = ThemeConfig(data.get("theme", {}))
        self.logging = LoggingConfig(data.get("logging", {}))
    
    def _find_config_file(self) -> Optional[Path]:
        """查找配置文件"""
        # 依次检查可能的路径
        paths = [
            Path("config.yml"),
            Path("data/config.yml"),
            Path("../config.yml"),
            Path(__file__).parent.parent.parent / "config.yml"
        ]
        
        for path in paths:
            if path.exists():
                return path
        return None
    
    def _apply_env_overrides(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        # 环境变量覆盖
        if "APP_PORT" in os.environ:
            if "app" not in data:
                data["app"] = {}
            try:
                data["app"]["port"] = int(os.environ["APP_PORT"])
            except ValueError:
                pass
        
        if "MONGODB_HOST" in os.environ:
            if "mongodb" not in data:
                data["mongodb"] = {}
            data["mongodb"]["host"] = os.environ["MONGODB_HOST"]
        
        if "QDRANT_HOST" in os.environ:
            if "qdrant" not in data:
                data["qdrant"] = {}
            data["qdrant"]["host"] = os.environ["QDRANT_HOST"]
        
        if "FAIL_THRESHOLD" in os.environ:
            if "strategy" not in data:
                data["strategy"] = {}
            try:
                data["strategy"]["fail_threshold"] = int(os.environ["FAIL_THRESHOLD"])
            except ValueError:
                pass
        
        return data
    
    def reload(self):
        """重新加载配置"""
        self._initialized = False
        self._load_config()
    
    def get_provider_by_key(self, proxy_key: str) -> Optional[ProviderConfig]:
        """根据 proxy_key 获取供应商配置"""
        for provider in self.providers:
            if provider.proxy_key == proxy_key:
                return provider
        return None


@lru_cache()
def get_config() -> Config:
    """获取配置单例（缓存）"""
    return Config()


settings = get_config()
