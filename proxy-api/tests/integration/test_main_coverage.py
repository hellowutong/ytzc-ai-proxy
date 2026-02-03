"""
app.main.py 补充测试 - 提升覆盖率
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """健康检查端点测试"""

    def test_health_endpoint(self):
        """测试健康检查端点"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_version_endpoint(self):
        """测试版本端点"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data or "data" in data


class TestProviderManagement:
    """供应商管理测试"""

    def test_list_providers(self):
        """测试列出供应商"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/providers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_reload_providers(self):
        """测试重载供应商配置"""
        from app.main import app
        client = TestClient(app)
        
        response = client.post("/api/v1/providers/reload")
        assert response.status_code == 200


class TestSessionManagementExtended:
    """会话管理扩展测试"""

    def test_list_sessions_empty(self):
        """测试空会话列表"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.sessions_db', []):
            response = client.get("/api/v1/sessions")
            assert response.status_code == 200

    def test_list_sessions_with_data(self):
        """测试带数据的会话列表"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.sessions_db', [
            {"id": "test-1", "title": "Test Session"}
        ]):
            response = client.get("/api/v1/sessions")
            assert response.status_code == 200

    def test_list_sessions_with_params(self):
        """测试带参数查询会话"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/sessions?page=1&size=10")
        assert response.status_code == 200

    def test_create_session_with_title(self):
        """测试创建带标题的会话"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.sessions_db', []):
            response = client.post("/api/v1/sessions", json={"proxy_key": "test-key"})
            assert response.status_code == 200

    def test_get_session_not_found(self):
        """测试获取不存在的会话"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.sessions_db', []):
            response = client.get("/api/v1/sessions/non-existent-id")
            assert response.status_code == 404

    def test_delete_session_not_found(self):
        """测试删除不存在的会话"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.sessions_db', []):
            response = client.delete("/api/v1/sessions/non-existent-id")
            assert response.status_code == 404


class TestSkillManagementExtended:
    """技能管理扩展测试"""

    def test_list_skills_empty(self):
        """测试空技能列表"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.get("/api/v1/skills")
            assert response.status_code == 200

    def test_list_skills_with_data(self):
        """测试带数据的技能列表"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', [
            {"id": "skill-1", "name": "Test Skill"}
        ]):
            response = client.get("/api/v1/skills")
            assert response.status_code == 200

    def test_list_skills_with_params(self):
        """测试带参数查询技能"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/skills?page=1&size=10")
        assert response.status_code == 200

    def test_create_skill_with_data(self):
        """测试创建技能"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.post("/api/v1/skills", json={
                "base_id": "test-skill",
                "description": "Test description"
            })
            assert response.status_code == 200

    def test_get_skill_not_found(self):
        """测试获取不存在的技能"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.get("/api/v1/skills/non-existent")
            assert response.status_code == 404

    def test_update_skill_not_found(self):
        """测试更新不存在的技能"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.put("/api/v1/skills/non-existent", json={"title": "Updated"})
            assert response.status_code == 404

    def test_delete_skill_not_found(self):
        """测试删除不存在的技能"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.delete("/api/v1/skills/non-existent")
            assert response.status_code == 404


class TestConfigManagement:
    """配置管理测试"""

    def test_get_config(self):
        """测试获取配置"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/config")
        assert response.status_code == 200


class TestBackupManagement:
    """备份管理测试"""

    def test_list_backups_empty(self):
        """测试列出空备份"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.backups_db', []):
            response = client.get("/api/v1/backups")
            assert response.status_code == 200

    def test_list_backups_with_data(self):
        """测试列出带数据的备份"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.backups_db', [
            {"id": "backup-1", "name": "backup.zip"}
        ]):
            response = client.get("/api/v1/backups")
            assert response.status_code == 200


class TestBaseSkillsManagement:
    """BaseSkills管理测试"""

    def test_list_baseskills(self):
        """测试列出模板"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/baseskills")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestConnectionsManagement:
    """连接管理测试"""

    def test_list_connections_empty(self):
        """测试列出空连接"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.connections_db', []):
            response = client.get("/api/v1/connections")
            assert response.status_code == 200

    def test_list_connections_with_data(self):
        """测试列出带数据的连接"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.connections_db', [
            {"id": "conn-1", "name": "Test Connection"}
        ]):
            response = client.get("/api/v1/connections")
            assert response.status_code == 200


class TestErrorHandling:
    """错误处理测试"""

    def test_404_handler(self):
        """测试 404 错误处理"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/non-existent-endpoint")
        assert response.status_code == 404

    def test_validation_error(self):
        """测试验证错误处理"""
        from app.main import app
        client = TestClient(app)
        
        response = client.post("/api/v1/sessions", json={"invalid_field": "value"})
        assert response.status_code == 422


class TestVectorEndpoints:
    """向量存储端点测试"""

    def test_list_collections(self):
        """测试列出集合"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/vectors/collections")
        assert response.status_code == 200


class TestSkillVersions:
    """技能版本测试"""

    def test_get_skill_versions(self):
        """测试获取技能版本"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', [
            {"base_id": "test-skill", "versions": [{"version_id": 0, "status": "draft"}]}
        ]):
            response = client.get("/api/v1/skills/test-skill/versions")
            assert response.status_code == 200

    def test_get_skill_version_not_found(self):
        """测试获取不存在的技能版本"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.get("/api/v1/skills/non-existent/versions/999")
            assert response.status_code == 404

    def test_publish_skill_version_not_found(self):
        """测试发布不存在的技能版本"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.post("/api/v1/skills/non-existent/versions/999/publish")
            assert response.status_code == 404

    def test_rollback_skill_version_not_found(self):
        """测试回滚不存在的技能版本"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.main.skills_db', []):
            response = client.post("/api/v1/skills/non-existent/versions/999/rollback")
            assert response.status_code == 404


class TestBaseSkillsExtended:
    """BaseSkills扩展测试"""

    def test_get_baseskill_not_found(self):
        """测试获取不存在的模板"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/baseskills/non-existent")
        assert response.status_code == 404

    def test_reload_baseskills(self):
        """测试重载模板"""
        from app.main import app
        client = TestClient(app)
        
        response = client.post("/api/v1/baseskills/reload")
        assert response.status_code == 200
