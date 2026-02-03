"""
TDD 测试框架配置
包含测试持久化、恢复机制、fixtures
"""
import sys
import json
import pytest
import signal
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试状态文件路径
TEST_STATE_FILE = project_root / ".test_state.json"
TEST_PROGRESS_FILE = project_root / ".test_progress.json"
TEST_COVERAGE_FILE = project_root / ".coverage"


class TestStateManager:
    """测试状态管理器 - 保证测试持久化"""
    
    def __init__(self):
        self.state = {
            "last_run": None,
            "completed_tests": [],
            "failed_tests": [],
            "pending_tests": [],
            "session_id": self._generate_session_id(),
            "start_time": None,
            "total_runs": 0
        }
        self._load_state()
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        import hashlib
        timestamp = str(datetime.now().timestamp()).encode()
        return hashlib.md5(timestamp).hexdigest()[:8]
    
    def _load_state(self) -> None:
        """加载上次测试状态"""
        if TEST_STATE_FILE.exists():
            try:
                with open(TEST_STATE_FILE, 'r') as f:
                    saved_state = json.load(f)
                    # 合并状态，保留未完成的测试
                    self.state.update(saved_state)
            except (json.JSONDecodeError, IOError):
                pass
    
    def save_state(self) -> None:
        """保存测试状态"""
        self.state["last_run"] = datetime.now().isoformat()
        self.state["total_runs"] += 1
        
        # 保存到文件
        TEST_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEST_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def mark_test_completed(self, test_id: str) -> None:
        """标记测试完成"""
        if test_id not in self.state["completed_tests"]:
            self.state["completed_tests"].append(test_id)
            if test_id in self.state["pending_tests"]:
                self.state["pending_tests"].remove(test_id)
            self.save_state()
    
    def mark_test_failed(self, test_id: str, error: str) -> None:
        """标记测试失败"""
        if test_id not in self.state["failed_tests"]:
            self.state["failed_tests"].append({
                "test_id": test_id,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
            if test_id in self.state["pending_tests"]:
                self.state["pending_tests"].remove(test_id)
            self.save_state()
    
    def register_pending_test(self, test_id: str) -> None:
        """注册待执行测试"""
        if test_id not in self.state["completed_tests"]:
            if test_id not in self.state["pending_tests"]:
                self.state["pending_tests"].append(test_id)
                self.save_state()
    
    def get_remaining_tests(self) -> list:
        """获取剩余待执行的测试"""
        remaining = []
        for test_id in self.state["pending_tests"]:
            if test_id not in self.state["completed_tests"]:
                remaining.append(test_id)
        return remaining
    
    def get_session_id(self) -> str:
        return self.state["session_id"]


class TestProgressTracker:
    """测试进度跟踪器"""
    
    def __init__(self):
        self.progress = {
            "session_start": None,
            "current_phase": None,
            "completed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "start_time": None,
            "last_update": None,
            "coverage_data": {}
        }
        self._load_progress()
    
    def _load_progress(self) -> None:
        """加载进度"""
        if TEST_PROGRESS_FILE.exists():
            try:
                with open(TEST_PROGRESS_FILE, 'r') as f:
                    self.progress.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
    
    def save_progress(self) -> None:
        """保存进度"""
        self.progress["last_update"] = datetime.now().isoformat()
        TEST_PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEST_PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f, indent=2, default=str)
    
    def start_session(self, phase: str) -> None:
        """开始会话"""
        self.progress["session_start"] = datetime.now().isoformat()
        self.progress["current_phase"] = phase
        self.progress["start_time"] = datetime.now().isoformat()
        self.save_progress()
    
    def update_count(self, status: str, count: int = 1) -> None:
        """更新计数"""
        if status == "completed":
            self.progress["completed_count"] += count
        elif status == "failed":
            self.progress["failed_count"] += count
        elif status == "skipped":
            self.progress["skipped_count"] += count
        self.save_progress()


# 全局实例
test_state = TestStateManager()
test_progress = TestProgressTracker()


@pytest.fixture(scope="session")
def test_state_manager():
    """测试状态管理器 fixture"""
    yield test_state
    # 会话结束时保存状态
    test_state.save_state()


@pytest.fixture(scope="session")
def test_progress_tracker():
    """测试进度跟踪器 fixture"""
    yield test_progress
    test_progress.save_progress()


@pytest.fixture(scope="session")
def session_id() -> str:
    """获取会话ID"""
    return test_state.get_session_id()


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """获取项目根目录"""
    return project_root


@pytest.fixture
def mock_settings():
    """模拟配置"""
    with patch('app.core.config.settings') as mock:
        mock.MONGODB_URL = "mongodb://localhost:27017"
        mock.MONGODB_DATABASE = "ytzc_ai_proxy"
        mock.QDRANT_URL = "http://localhost:6333"
        mock.APP_HOST = "0.0.0.0"
        mock.APP_PORT = 8080
        mock.SESSION_TIMEOUT = 1800
        mock.MODEL_TIMEOUT = 30000
        mock.FAIL_THRESHOLD = 3
        mock.SMALL_MODEL_RETRY = 0
        yield mock


@pytest.fixture
def mock_mongodb():
    """模拟 MongoDB"""
    mock_client = AsyncMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.__getitem__ = MagicMock(return_value=mock_db)
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    
    with patch('app.infrastructure.database.mongodb.MongoDB') as mock:
        instance = MagicMock()
        instance.client = mock_client
        instance.db = mock_db
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_qdrant():
    """模拟 Qdrant"""
    with patch('app.infrastructure.database.qdrant.QdrantClient') as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_connection():
    """示例连接数据"""
    return {
        "id": "test-conn-001",
        "name": "Test Connection",
        "proxy_key": "tw-test-abc123",
        "small_model": {
            "name": "test-small-model",
            "base_url": "http://localhost:8000/v1/",
            "api_key": "test-key"
        },
        "big_model": {
            "name": "test-big-model",
            "base_url": "http://localhost:8001/v1/",
            "api_key": "test-key"
        },
        "status": "enabled",
        "created_at": "2026-02-02T10:00:00Z"
    }


@pytest.fixture
def sample_session():
    """示例会话数据"""
    return {
        "session_id": "test-session-001",
        "proxy_key": "tw-test-abc123",
        "status": "active",
        "messages": [
            {
                "role": "user",
                "content": "Test message",
                "timestamp": "2026-02-02T10:00:00Z"
            }
        ],
        "summary": None,
        "vector_id": None,
        "created_at": "2026-02-02T10:00:00Z",
        "ended_at": None
    }


@pytest.fixture
def sample_skill():
    """示例 Skill 数据"""
    return {
        "base_id": "test-skill-001",
        "active_version_id": 0,
        "created_at": "2026-02-02T10:00:00Z",
        "versions": [
            {
                "version_id": 0,
                "status": "published",
                "created_at": "2026-02-02T10:00:00Z",
                "created_by": "system",
                "source_session_id": "test-session-001",
                "change_reason": "initial"
            }
        ]
    }


def pytest_configure(config):
    """pytest 配置钩子"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "tdd_test: marks a TDD test case"
    )
    config.addinivalue_line(
        "markers", "requires_service: marks tests that require running services"
    )


def pytest_collection_modifyitems(config, items):
    """根据测试状态修改测试顺序"""
    # 优先执行未完成的测试
    remaining = set(test_state.get_remaining_tests())
    
    def sort_key(item):
        # TDD 测试优先
        if item.get_closest_marker("tdd_test"):
            return 0
        # 未完成的测试优先
        if item.nodeid in remaining:
            return 1
        return 2
    
    items.sort(key=sort_key)


@pytest.fixture(scope="session")
def services_available():
    """检查服务是否可用"""
    import socket
    
    services = [
        ("localhost", 27017, "MongoDB"),
        ("localhost", 6333, "Qdrant"),
        ("localhost", 6379, "Redis")
    ]
    
    available = {}
    for host, port, name in services:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        available[name] = result == 0
    
    return available


@pytest.fixture
def mongodb_services(services_available):
    """MongoDB服务fixture - 跳过测试如果服务不可用"""
    if not services_available.get("MongoDB", False):
        pytest.skip("MongoDB服务不可用，请确保MongoDB已启动")
    return services_available


@pytest.fixture
def qdrant_services(services_available):
    """Qdrant服务fixture - 跳过测试如果服务不可用"""
    if not services_available.get("Qdrant", False):
        pytest.skip("Qdrant服务不可用，请确保Qdrant已启动")
    return services_available


@pytest.fixture
def database_services(services_available):
    """数据库服务fixture - 需要所有数据库服务"""
    missing = [name for name, available in services_available.items() if not available]
    if missing:
        pytest.skip(f"以下服务不可用: {missing}")
    return services_available


@pytest.fixture
def mongodb_config():
    """MongoDB配置"""
    return {
        "host": "localhost",
        "port": 27017,
        "username": "admin",
        "password": "password123",
        "database": "tw_ai_proxy"
    }


@pytest.fixture
def qdrant_config():
    """Qdrant配置"""
    return {
        "host": "localhost",
        "port": 6333,
        "grpc_port": 6334
    }


@pytest.fixture
def redis_config():
    """Redis配置"""
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0
    }


def pytest_sessionstart(session):
    """会话开始钩子"""
    test_progress.start_session("TDD Development")
    print(f"\n{'='*60}")
    print(f"测试会话开始 - Session ID: {test_state.get_session_id()}")
    print(f"待执行测试数: {len(test_state.get_remaining_tests())}")
    print(f"{'='*60}\n")


def pytest_sessionfinish(session, exitstatus):
    """会话结束钩子"""
    test_state.save_state()
    test_progress.save_progress()
    
    print(f"\n{'='*60}")
    print(f"测试会话结束 - Exit Status: {exitstatus}")
    print(f"已完成测试数: {test_progress.progress['completed_count']}")
    print(f"失败测试数: {test_progress.progress['failed_count']}")
    print(f"状态已保存至: {TEST_STATE_FILE}")
    print(f"{'='*60}\n")


# 信号处理 - 优雅退出时保存状态
def save_state_on_exit(signum, frame):
    test_state.save_state()
    test_progress.save_progress()
    sys.exit(0)


if sys.platform != 'win32':
    signal.signal(signal.SIGTERM, save_state_on_exit)
    signal.signal(signal.SIGINT, save_state_on_exit)
