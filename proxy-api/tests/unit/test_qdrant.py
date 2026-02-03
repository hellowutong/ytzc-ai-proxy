"""
Qdrant 向量数据库单元测试
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.qdrant import Qdrant


class TestQdrant:
    """Qdrant 测试类"""

    @pytest.fixture
    def mock_client(self):
        """创建模拟的Qdrant客户端"""
        client = MagicMock()
        client.search = AsyncMock()
        client.upsert = AsyncMock()
        client.delete = AsyncMock()
        client.get_collections = AsyncMock()
        client.create_collection = AsyncMock()
        client.close = AsyncMock()
        return client

    @pytest.fixture
    def qdrant_with_client(self, mock_client):
        """创建带模拟客户端的Qdrant实例"""
        Qdrant.client = mock_client
        yield Qdrant
        Qdrant.client = None

    def test_class_attributes(self):
        """测试类属性"""
        assert Qdrant.VECTOR_SIZE == 1024
        assert Qdrant.COLLECTION_SESSIONS == "sessions"
        assert Qdrant.COLLECTION_SKILLS == "skills"

    def test_client_initial_state(self):
        """测试客户端初始状态"""
        assert Qdrant.client is None

    @pytest.mark.asyncio
    async def test_connect(self, mock_client):
        """测试连接"""
        with patch('app.infrastructure.database.qdrant.get_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.qdrant.host = "localhost"
            mock_cfg.qdrant.port = 6333
            mock_config.return_value = mock_cfg
            
            with patch('app.infrastructure.database.qdrant.AsyncQdrantClient', return_value=mock_client):
                await Qdrant.connect()
                
                assert Qdrant.client is mock_client
                mock_client.create_collection.assert_called()

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_client):
        """测试断开连接"""
        Qdrant.client = mock_client
        
        await Qdrant.disconnect()
        
        mock_client.close.assert_called_once()
        assert Qdrant.client is None

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self):
        """测试无客户端时断开"""
        Qdrant.client = None
        
        await Qdrant.disconnect()
        
        assert Qdrant.client is None

    @pytest.mark.asyncio
    async def test_create_collections_no_client(self):
        """测试无客户端时创建集合"""
        Qdrant.client = None
        
        await Qdrant._create_collections()

    @pytest.mark.asyncio
    async def test_search_sessions_no_client(self):
        """测试无客户端时搜索会话"""
        Qdrant.client = None
        
        result = await Qdrant.search_sessions([0.1] * 1024)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_search_sessions_with_results(self, qdrant_with_client):
        """测试搜索会话返回结果"""
        mock_results = [
            MagicMock(id="session_1", score=0.9, payload={"session_id": "1"}),
            MagicMock(id="session_2", score=0.8, payload={"session_id": "2"})
        ]
        qdrant_with_client.client.search = AsyncMock(return_value=mock_results)
        
        result = await Qdrant.search_sessions([0.1] * 1024, limit=10)
        
        assert len(result) == 2
        assert result[0]["id"] == "session_1"
        assert result[0]["score"] == 0.9

    @pytest.mark.asyncio
    async def test_search_skills_no_client(self):
        """测试无客户端时搜索Skills"""
        Qdrant.client = None
        
        result = await Qdrant.search_skills([0.1] * 1024)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_search_skills_with_results(self, qdrant_with_client):
        """测试搜索Skills返回结果"""
        mock_results = [
            MagicMock(id="skill_1", score=0.95, payload={"base_id": "skill-1"})
        ]
        qdrant_with_client.client.search = AsyncMock(return_value=mock_results)
        
        result = await Qdrant.search_skills([0.1] * 1024)
        
        assert len(result) == 1
        assert result[0]["id"] == "skill_1"

    @pytest.mark.asyncio
    async def test_add_session_vector_no_client(self):
        """测试无客户端时添加会话向量"""
        Qdrant.client = None
        
        result = await Qdrant.add_session_vector(
            session_id="s1",
            proxy_key="pk1",
            summary="Test",
            vector=[0.1] * 1024
        )
        
        assert result == ""

    @pytest.mark.asyncio
    async def test_add_session_vector_success(self, qdrant_with_client):
        """测试添加会话向量成功"""
        qdrant_with_client.client.upsert = AsyncMock()
        
        result = await Qdrant.add_session_vector(
            session_id="test-session",
            proxy_key="pk1",
            summary="Test summary",
            vector=[0.1] * 1024
        )
        
        assert result == "session_test-session"
        qdrant_with_client.client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_skill_vector_no_client(self):
        """测试无客户端时添加Skill向量"""
        Qdrant.client = None
        
        result = await Qdrant.add_skill_vector(
            base_id="skill-1",
            version_id=1,
            content="Test content",
            vector=[0.1] * 1024
        )
        
        assert result == ""

    @pytest.mark.asyncio
    async def test_add_skill_vector_success(self, qdrant_with_client):
        """测试添加Skill向量成功"""
        qdrant_with_client.client.upsert = AsyncMock()
        
        result = await Qdrant.add_skill_vector(
            base_id="test-skill",
            version_id=2,
            content="Skill content",
            vector=[0.1] * 1024
        )
        
        assert result == "skill_test-skill_2"
        qdrant_with_client.client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_vector_no_client(self):
        """测试无客户端时删除会话向量"""
        Qdrant.client = None
        
        result = await Qdrant.delete_session_vector("s1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_session_vector_success(self, qdrant_with_client):
        """测试删除会话向量成功"""
        qdrant_with_client.client.delete = AsyncMock()
        
        result = await Qdrant.delete_session_vector("test-session")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_session_vector_exception(self, qdrant_with_client):
        """测试删除会话向量异常"""
        qdrant_with_client.client.delete = AsyncMock(side_effect=Exception("Error"))
        
        result = await Qdrant.delete_session_vector("test-session")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_skill_vector_no_client(self):
        """测试无客户端时删除Skill向量"""
        Qdrant.client = None
        
        result = await Qdrant.delete_skill_vector("skill-1", 1)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_skill_vector_success(self, qdrant_with_client):
        """测试删除Skill向量成功"""
        qdrant_with_client.client.delete = AsyncMock()
        
        result = await Qdrant.delete_skill_vector("test-skill", 1)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_skill_vector_exception(self, qdrant_with_client):
        """测试删除Skill向量异常"""
        qdrant_with_client.client.delete = AsyncMock(side_effect=Exception("Error"))
        
        result = await Qdrant.delete_skill_vector("test-skill", 1)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_collections_no_client(self):
        """测试无客户端时获取集合"""
        Qdrant.client = None
        
        result = await Qdrant.get_collections()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_collections_success(self, qdrant_with_client):
        """测试获取集合成功"""
        mock_collection1 = MagicMock()
        mock_collection1.name = "sessions"
        mock_collection2 = MagicMock()
        mock_collection2.name = "skills"
        
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection1, mock_collection2]
        qdrant_with_client.client.get_collections = AsyncMock(return_value=mock_collections)
        
        result = await Qdrant.get_collections()
        
        assert result == ["sessions", "skills"]

    @pytest.mark.asyncio
    async def test_get_collections_exception(self, qdrant_with_client):
        """测试获取集合异常"""
        qdrant_with_client.client.get_collections = AsyncMock(side_effect=Exception("Error"))
        
        result = await Qdrant.get_collections()
        
        assert result == []


class TestGetQdrant:
    """get_qdrant 函数测试"""

    @pytest.mark.asyncio
    async def test_get_qdrant(self):
        """测试获取Qdrant实例"""
        from app.infrastructure.database.qdrant import get_qdrant
        result = await get_qdrant()
        assert result is Qdrant
