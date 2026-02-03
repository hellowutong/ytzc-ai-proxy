"""
TDD 测试用例 - 核心配置模块
验证配置加载功能和模型定义
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestConfigLoader:
    """配置加载器测试类"""
    
    def test_config_class_exists(self):
        """测试 1.1: Config 类是否存在"""
        try:
            from app.core.config import Config
            assert Config is not None
        except ImportError:
            pytest.fail("Config 类不存在，需要实现")
    
    def test_config_load_from_yaml(self):
        """测试 1.2: 配置从 YAML 文件加载"""
        from app.core.config import Config
        import tempfile
        import os
        
        config_content = """
app:
  host: "0.0.0.0"
  port: 8080
  data_path: "./data"
  session_timeout: 1800
  model_timeout: 30000

mongodb:
  host: "localhost"
  port: 27017
  username: ""
  password: ""
  database: "ytzc_ai_proxy"
  auth_source: "admin"

qdrant:
  host: "localhost"
  port: 6333
  api_key: null
  https: false

strategy:
  fail_threshold: 3
  small_model_retry: 0

providers: []

theme:
  light:
    primary: "#409EFF"
    bg: "#F5F7FA"
    card: "#FFFFFF"
    text: "#303133"
  dark:
    primary: "#409EFF"
    bg: "#141414"
    card: "#1D1D1D"
    text: "#E5EAF3"

logging:
  level: "INFO"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name
        
        try:
            with patch('app.core.config.CONFIG_FILE', temp_path):
                Config._instance = None
                config = Config()
                assert config.app.host == "0.0.0.0"
                assert config.app.port == 8080
                assert config.mongodb.host == "localhost"
                assert config.mongodb.port == 27017
                assert config.strategy.fail_threshold == 3
                assert len(config.providers) == 0
        finally:
            os.unlink(temp_path)
            Config._instance = None
    
    def test_config_singleton_pattern(self):
        """测试 1.3: Config 使用单例模式"""
        from app.core.config import Config
        
        Config._instance = None
        config1 = Config()
        config2 = Config()
        assert config1 is config2, "Config 应该使用单例模式"
    
    def test_config_environment_override(self):
        """测试 1.4: 环境变量覆盖配置"""
        from app.core.config import Config
        
        import os
        os.environ["APP_PORT"] = "9999"
        
        try:
            Config._instance = None
            config = Config()
            assert config.app.port == 9999
        finally:
            del os.environ["APP_PORT"]
            Config._instance = None
    
    def test_config_validation(self):
        """测试 1.5: 配置验证"""
        from app.core.config import Config
        import tempfile
        import os
        
        invalid_config = """
app:
  host: ""
  port: -1
  session_timeout: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(invalid_config)
            temp_path = f.name
        
        try:
            with patch('app.core.config.CONFIG_FILE', temp_path):
                Config._instance = None
                config = Config()
                assert config.app.port > 0, "端口应该为正值"
                assert config.app.session_timeout > 0, "会话超时应该为正值"
        finally:
            os.unlink(temp_path)
            Config._instance = None


class TestProxyConnectionModel:
    """代理连接模型测试类"""
    
    def test_connection_model_exists(self):
        """测试 2.1: ProxyConnection 模型存在"""
        from app.domain.models.connection import ProxyConnection, ModelConfig
        assert ProxyConnection is not None
        assert ModelConfig is not None
    
    def test_connection_model_create(self):
        """测试 2.2: 创建连接模型实例"""
        from app.domain.models.connection import ProxyConnection, ModelConfig
        
        connection = ProxyConnection(
            id="test-conn-001",
            name="Test Connection",
            proxy_key="tw-test-abc123",
            small_model=ModelConfig(
                name="test-small-model",
                base_url="http://localhost:8000/v1/",
                api_key="test-key"
            ),
            big_model=ModelConfig(
                name="test-big-model",
                base_url="http://localhost:8001/v1/",
                api_key="test-key"
            ),
            status="enabled",
            created_at="2026-02-02T10:00:00Z"
        )
        
        assert connection.id == "test-conn-001"
        assert connection.name == "Test Connection"
        assert connection.proxy_key == "tw-test-abc123"
        assert connection.small_model.name == "test-small-model"
        assert connection.big_model.name == "test-big-model"


class TestSessionModel:
    """会话模型测试类"""
    
    def test_session_model_exists(self):
        """测试 3.1: Session 模型存在"""
        from app.domain.models.session import Session, Message, SessionStatus
        assert Session is not None
        assert Message is not None
        assert SessionStatus is not None
    
    def test_session_model_create(self):
        """测试 3.2: 创建会话模型实例"""
        from app.domain.models.session import Session, Message
        
        session = Session(
            session_id="test-session-001",
            proxy_key="tw-test-abc123",
            status="active",
            messages=[
                Message(
                    role="user",
                    content="Test message",
                    timestamp="2026-02-02T10:00:00Z"
                )
            ],
            created_at="2026-02-02T10:00:00Z"
        )
        
        assert session.session_id == "test-session-001"
        assert session.proxy_key == "tw-test-abc123"
        assert len(session.messages) == 1
        assert session.messages[0].role == "user"


class TestSkillModel:
    """Skill 模型测试类"""
    
    def test_skill_model_exists(self):
        """测试 4.1: Skill 模型存在"""
        from app.domain.models.skill import Skill, SkillVersion, SkillStatus
        assert Skill is not None
        assert SkillVersion is not None
        assert SkillStatus is not None
    
    def test_skill_model_create(self):
        """测试 4.2: 创建 Skill 模型实例"""
        from app.domain.models.skill import Skill, SkillVersion
        
        skill = Skill(
            base_id="test-skill-001",
            active_version_id=0,
            created_at="2026-02-02T10:00:00Z",
            versions=[
                SkillVersion(
                    version_id=0,
                    status="published",
                    created_at="2026-02-02T10:00:00Z",
                    created_by="system",
                    source_session_id="test-session-001",
                    change_reason="initial"
                )
            ]
        )
        
        assert skill.base_id == "test-skill-001"
        assert skill.active_version_id == 0
        assert len(skill.versions) == 1
