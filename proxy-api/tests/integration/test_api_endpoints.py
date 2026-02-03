"""
集成测试 - API接口测试
测试所有后端API接口的功能
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


class TestHealthAPI:
    """健康检查API测试"""
    
    def test_health_endpoint(self):
        """测试健康检查接口"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestVersionAPI:
    """版本API测试"""
    
    def test_version_endpoint(self):
        """测试版本接口"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/version")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestConnectionsAPI:
    """连接管理API测试"""
    
    def test_list_connections_empty(self):
        """测试列出连接 - 空列表"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/connections")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_connection(self):
        """测试创建连接"""
        from app.main import app
        
        client = TestClient(app)
        connection_data = {
            "name": "Test Connection",
            "small_model": {
                "name": "deepseek-8b",
                "base_url": "https://api.siliconflow.cn/v1/",
                "api_key": "sk-test"
            },
            "big_model": {
                "name": "deepseek-v3",
                "base_url": "https://api.siliconflow.cn/v1/",
                "api_key": "sk-test"
            }
        }
        
        response = client.post("/api/v1/connections", json=connection_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "proxy_key" in data
        assert data["proxy_key"].startswith("tw-")


class TestProvidersAPI:
    """供应商配置API测试"""
    
    def test_list_providers(self):
        """测试列出供应商"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_reload_providers(self):
        """测试重新加载供应商配置"""
        from app.main import app
        
        client = TestClient(app)
        response = client.post("/api/v1/providers/reload")
        
        assert response.status_code == 200


class TestSessionsAPI:
    """会话管理API测试"""
    
    def test_list_sessions_empty(self):
        """测试列出会话 - 空列表"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
    
    def test_create_session(self):
        """测试创建会话"""
        from app.main import app
        
        client = TestClient(app)
        session_data = {
            "proxy_key": "tw-test-key"
        }
        
        response = client.post("/api/v1/sessions", json=session_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "proxy_key" in data


class TestSkillsAPI:
    """Skill管理API测试"""
    
    def test_list_skills_empty(self):
        """测试列出Skill - 空列表"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/skills")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
    
    def test_create_skill(self):
        """测试创建Skill"""
        from app.main import app
        
        client = TestClient(app)
        skill_data = {
            "base_id": "test-skill",
            "description": "Test skill description"
        }
        
        response = client.post("/api/v1/skills", json=skill_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "base_id" in data


class TestVectorsAPI:
    """向量存储API测试"""
    
    def test_list_collections(self):
        """测试列出向量集合"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/vectors/collections")
        
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
    
    def test_search_sessions_empty(self):
        """测试搜索会话向量 - 空结果"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/vectors/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data


class TestConfigAPI:
    """配置管理API测试"""
    
    def test_get_config(self):
        """测试获取配置"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "app" in data


class TestBackupsAPI:
    """备份管理API测试"""
    
    def test_list_backups_empty(self):
        """测试列出备份 - 空列表"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/backups")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestBaseSkillsAPI:
    """baseskill管理API测试"""
    
    def test_list_baseskills(self):
        """测试列出baseskill模板"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/baseskills")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestProxyAPI:
    """OpenAI兼容代理API测试"""
    
    def test_list_models_with_auth(self):
        """测试列出模型 - 带认证"""
        from app.main import app
        from app.core.security import SecurityManager
        
        # 生成有效的Proxy Key
        proxy_key = SecurityManager.generate_proxy_key()
        
        client = TestClient(app)
        response = client.get(
            "/proxy/v1/models",
            headers={"Authorization": f"Bearer {proxy_key}"}
        )
        
        # 现在应该成功（模拟数据库会返回连接）
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_list_models_without_auth(self):
        """测试列出模型 - 无认证"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/proxy/v1/models")
        
        assert response.status_code == 401
    
    def test_chat_completions_with_auth(self):
        """测试聊天补全 - 带认证"""
        from app.main import app
        from app.core.security import SecurityManager
        
        proxy_key = SecurityManager.generate_proxy_key()
        
        client = TestClient(app)
        response = client.post(
            "/proxy/v1/chat/completions",
            json={"model": "deepseek-8b", "messages": [{"role": "user", "content": "Hello"}]},
            headers={"Authorization": f"Bearer {proxy_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
    
    def test_chat_completions_without_auth(self):
        """测试聊天补全 - 无认证"""
        from app.main import app
        
        client = TestClient(app)
        response = client.post(
            "/proxy/v1/chat/completions",
            json={"model": "deepseek-8b", "messages": [{"role": "user", "content": "Hello"}]}
        )
        
        assert response.status_code == 401


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_connection_id(self):
        """测试无效连接ID"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/connections/invalid-id")
        
        assert response.status_code == 404
    
    def test_invalid_session_id(self):
        """测试无效会话ID"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/sessions/invalid-id")
        
        assert response.status_code == 404
    
    def test_unauthorized_proxy_request(self):
        """测试未授权的代理请求"""
        from app.main import app
        
        client = TestClient(app)
        response = client.post(
            "/proxy/v1/chat/completions",
            json={"model": "test", "messages": []}
        )
        
        assert response.status_code == 401


class TestFilesAPI:
    """文件管理API测试"""
    
    def test_list_skills_files(self):
        """测试列出Skill文件"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/files/skills")
        
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert "files" in data
    
    def test_read_skill_file_not_found(self):
        """测试读取不存在的Skill文件"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/files/skills/test-skill/0/skill.md")
        
        assert response.status_code == 404
    
    def test_update_skill_file(self):
        """测试更新Skill文件"""
        from app.main import app
        
        client = TestClient(app)
        response = client.put(
            "/api/v1/files/skills/test-skill/0/skill.md",
            json={"content": "# Test Skill"}
        )
        
        assert response.status_code == 200
    
    def test_delete_skill_file(self):
        """测试删除Skill文件"""
        from app.main import app
        
        client = TestClient(app)
        response = client.delete("/api/v1/files/skills/test-skill/0/skill.md")
        
        assert response.status_code in [200, 404]


class TestVectorsExtendedAPI:
    """向量存储扩展API测试"""
    
    def test_update_session_vector(self):
        """测试更新会话向量"""
        from app.main import app
        
        client = TestClient(app)
        response = client.put(
            "/api/v1/vectors/sessions/test-id",
            json={"content": "updated"}
        )
        
        assert response.status_code == 200
    
    def test_batch_delete_session_vectors(self):
        """测试批量删除会话向量"""
        from app.main import app, sessions_db
        import uuid
        
        # 先创建一个会话
        session_id = str(uuid.uuid4())
        sessions_db.append({
            "session_id": session_id,
            "proxy_key": "tw-test",
            "status": "active",
            "messages": [],
            "created_at": "2026-02-02T10:00:00Z"
        })
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/vectors/sessions/batch-delete?ids=id1&id2=id2"
        )
        
        assert response.status_code == 200
    
    def test_get_collection_info(self):
        """测试获取集合信息"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/vectors/collections/sessions/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
    
    def test_rebuild_collection(self):
        """测试重建集合"""
        from app.main import app
        
        client = TestClient(app)
        response = client.post("/api/v1/vectors/collections/sessions/rebuild")
        
        assert response.status_code == 200
    
    def test_delete_collection_data(self):
        """测试清空集合数据"""
        from app.main import app
        
        client = TestClient(app)
        response = client.delete("/api/v1/vectors/collections/sessions/delete")
        
        assert response.status_code == 200
    
    def test_batch_delete_skill_vectors(self):
        """测试批量删除Skill向量"""
        from app.main import app
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/vectors/skills/batch-delete?ids=id1,id2"
        )
        
        assert response.status_code == 200


class TestSessionsMessagesAPI:
    """会话消息操作API测试"""
    
    def test_update_session_message_not_found(self):
        """测试更新不存在的会话消息"""
        from app.main import app
        
        client = TestClient(app)
        response = client.put(
            "/api/v1/sessions/test-session/messages/test-msg-id",
            json={"content": "updated content"}
        )
        
        # 返回404因为会话不存在
        assert response.status_code == 404
    
    def test_delete_session_message_not_found(self):
        """测试删除不存在的会话消息"""
        from app.main import app
        
        client = TestClient(app)
        response = client.delete(
            "/api/v1/sessions/test-session/messages/test-msg-id"
        )
        
        assert response.status_code == 404


class TestSkillsVersionsAPI:
    """Skill版本管理API测试"""
    
    def test_get_skill_version(self):
        """测试获取Skill版本"""
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/skills/test-skill/versions/0")
        
        assert response.status_code == 200
    
    def test_update_skill_version(self):
        """测试更新Skill版本"""
        from app.main import app
        
        client = TestClient(app)
        response = client.put(
            "/api/v1/skills/test-skill/versions/0",
            json={"status": "draft"}
        )
        
        assert response.status_code == 200
    
    def test_delete_skill_version(self):
        """测试删除Skill版本"""
        from app.main import app
        
        client = TestClient(app)
        response = client.delete("/api/v1/skills/test-skill/versions/0")
        
        assert response.status_code in [200, 404]
    
    def test_delete_skill(self):
        """测试删除Skill"""
        from app.main import app
        
        client = TestClient(app)
        response = client.delete("/api/v1/skills/test-skill")
        
        assert response.status_code in [200, 404]
    
    def test_update_skill(self):
        """测试更新Skill"""
        from app.main import app
        
        client = TestClient(app)
        response = client.put(
            "/api/v1/skills/test-skill",
            json={"active_version_id": 1}
        )
        
        assert response.status_code in [200, 404]


class TestLogsAPI:
    """日志API测试"""
    
    def test_get_logs_filtered(self):
        """测试过滤查询日志"""
        from app.main import app
        
        client = TestClient(app)
        response = client.post(
            "/api/v1/logs",
            json={"level": "ERROR"},
            params={"page": 1, "limit": 100}
        )
        
        assert response.status_code == 200
