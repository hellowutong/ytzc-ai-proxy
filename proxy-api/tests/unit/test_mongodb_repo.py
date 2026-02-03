"""
MongoDB Repository 单元测试
测试 SessionRepositoryImpl 和 SkillRepositoryImpl
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.repositories.mongodb_repo import (
    SessionRepositoryImpl,
    SkillRepositoryImpl
)


class TestSessionRepositoryImpl:
    """SessionRepositoryImpl 测试类"""

    @pytest.fixture
    def mock_collection(self):
        """创建模拟的MongoDB集合"""
        collection = MagicMock()
        collection.insert_one = AsyncMock()
        collection.find_one = AsyncMock()
        collection.find = MagicMock()
        collection.update_one = AsyncMock()
        collection.delete_one = AsyncMock()
        collection.delete_many = AsyncMock()
        collection.count_documents = AsyncMock()
        return collection

    @pytest.fixture
    def repo(self, mock_collection):
        """创建仓储实例"""
        repo = SessionRepositoryImpl.__new__(SessionRepositoryImpl)
        repo.collection = mock_collection
        return repo

    @pytest.fixture
    def sample_session(self):
        """示例会话数据"""
        return {
            "session_id": "test-session-001",
            "proxy_key": "tw-test-key",
            "title": "测试会话",
            "status": "active",
            "messages": []
        }

    @pytest.mark.asyncio
    async def test_create_session(self, repo, sample_session):
        """测试创建会话"""
        mock_result = MagicMock()
        mock_result.inserted_id = "mock_id_123"

        repo.collection.insert_one = AsyncMock(return_value=mock_result)

        result = await repo.create(sample_session)

        assert result == "mock_id_123"
        repo.collection.insert_one.assert_called_once()
        call_args = repo.collection.insert_one.call_args[0][0]
        assert "created_at" in call_args
        assert "updated_at" in call_args

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_session):
        """测试获取存在的会话"""
        repo.collection.find_one = AsyncMock(return_value=sample_session)

        result = await repo.get_by_id("test-session-001")

        assert result == sample_session
        repo.collection.find_one.assert_called_once_with({"session_id": "test-session-001"})

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        """测试获取不存在的会话"""
        repo.collection.find_one = AsyncMock(return_value=None)

        result = await repo.get_by_id("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_no_filter(self, repo):
        """测试列出会话无筛选"""
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])

        repo.collection.find = MagicMock(return_value=mock_cursor)
        repo.collection.count_documents = AsyncMock(return_value=0)

        items, total = await repo.list()

        assert items == []
        assert total == 0
        repo.collection.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_list_with_proxy_key(self, repo):
        """测试按 proxy_key 筛选"""
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])

        repo.collection.find = MagicMock(return_value=mock_cursor)
        repo.collection.count_documents = AsyncMock(return_value=5)

        items, total = await repo.list(proxy_key="tw-test-key")

        assert total == 5
        repo.collection.count_documents.assert_called_once_with({"proxy_key": "tw-test-key"})

    @pytest.mark.asyncio
    async def test_list_with_status(self, repo):
        """测试按 status 筛选"""
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])

        repo.collection.find = MagicMock(return_value=mock_cursor)
        repo.collection.count_documents = AsyncMock(return_value=3)

        items, total = await repo.list(status="ended")

        assert total == 3
        repo.collection.count_documents.assert_called_once_with({"status": "ended"})

    @pytest.mark.asyncio
    async def test_list_pagination(self, repo):
        """测试分页"""
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])

        repo.collection.find = MagicMock(return_value=mock_cursor)
        repo.collection.count_documents = AsyncMock(return_value=100)

        items, total = await repo.list(page=3, limit=10)

        assert total == 100
        mock_cursor.skip.assert_called_with(20)
        mock_cursor.limit.assert_called_with(10)

    @pytest.mark.asyncio
    async def test_list_convert_objectid(self, repo):
        """测试转换 ObjectId"""
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": "abc123", "session_id": "s1"},
            {"session_id": "s2"},
            {"_id": None, "session_id": "s3"}
        ])

        repo.collection.find = MagicMock(return_value=mock_cursor)
        repo.collection.count_documents = AsyncMock(return_value=3)

        items, total = await repo.list()

        assert items[0]["_id"] == "abc123"
        assert items[1]["_id"] is None
        assert items[2]["_id"] is None

    @pytest.mark.asyncio
    async def test_update_success(self, repo, sample_session):
        """测试更新会话成功"""
        mock_result = MagicMock()
        mock_result.modified_count = 1

        repo.collection.update_one = AsyncMock(return_value=mock_result)
        repo.collection.find_one = AsyncMock(return_value=sample_session)

        result = await repo.update("test-session-001", {"title": "新标题"})

        assert result == sample_session

    @pytest.mark.asyncio
    async def test_update_not_found(self, repo):
        """测试更新不存在的会话"""
        mock_result = MagicMock()
        mock_result.modified_count = 0

        repo.collection.update_one = AsyncMock(return_value=mock_result)

        result = await repo.update("non-existent", {"title": "新标题"})

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_success(self, repo):
        """测试删除会话成功"""
        mock_result = MagicMock()
        mock_result.deleted_count = 1

        repo.collection.delete_one = AsyncMock(return_value=mock_result)

        result = await repo.delete("test-session-001")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo):
        """测试删除不存在的会话"""
        mock_result = MagicMock()
        mock_result.deleted_count = 0

        repo.collection.delete_one = AsyncMock(return_value=mock_result)

        result = await repo.delete("non-existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_batch_delete(self, repo):
        """测试批量删除"""
        mock_result = MagicMock()
        mock_result.deleted_count = 5

        repo.collection.delete_many = AsyncMock(return_value=mock_result)

        result = await repo.batch_delete(["s1", "s2", "s3", "s4", "s5"])

        assert result == 5
        repo.collection.delete_many.assert_called_once_with({
            "session_id": {"$in": ["s1", "s2", "s3", "s4", "s5"]}
        })

    @pytest.mark.asyncio
    async def test_add_message_success(self, repo, sample_session):
        """测试添加消息成功"""
        mock_result = MagicMock()
        mock_result.modified_count = 1

        repo.collection.update_one = AsyncMock(return_value=mock_result)
        repo.collection.find_one = AsyncMock(return_value=sample_session)

        message = {"role": "user", "content": "Hello"}
        result = await repo.add_message("test-session-001", message)

        assert result == sample_session

    @pytest.mark.asyncio
    async def test_add_message_not_found(self, repo):
        """测试向不存在的会话添加消息"""
        mock_result = MagicMock()
        mock_result.modified_count = 0

        repo.collection.update_one = AsyncMock(return_value=mock_result)

        message = {"role": "user", "content": "Hello"}
        result = await repo.add_message("non-existent", message)

        assert result is None

    @pytest.mark.asyncio
    async def test_end_session_success(self, repo, sample_session):
        """测试结束会话成功"""
        mock_result = MagicMock()
        mock_result.modified_count = 1

        repo.collection.update_one = AsyncMock(return_value=mock_result)
        repo.collection.find_one = AsyncMock(return_value={**sample_session, "status": "ended"})

        result = await repo.end_session("test-session-001")

        assert result["status"] == "ended"


class TestSkillRepositoryImpl:
    """SkillRepositoryImpl 测试类"""

    @pytest.fixture
    def mock_collection(self):
        """创建模拟的MongoDB集合"""
        collection = MagicMock()
        collection.insert_one = AsyncMock()
        collection.find_one = AsyncMock()
        collection.find = MagicMock()
        collection.update_one = AsyncMock()
        collection.delete_one = AsyncMock()
        collection.count_documents = AsyncMock()
        return collection

    @pytest.fixture
    def repo(self, mock_collection):
        """创建仓储实例"""
        repo = SkillRepositoryImpl.__new__(SkillRepositoryImpl)
        repo.collection = mock_collection
        return repo

    @pytest.fixture
    def sample_skill(self):
        """示例Skill数据"""
        return {
            "base_id": "test-skill-001",
            "name": "测试Skill",
            "status": "draft",
            "versions": [
                {"version_id": 0, "status": "draft", "prompt_template": "Hello"}
            ]
        }

    @pytest.mark.asyncio
    async def test_create_skill(self, repo):
        """测试创建Skill"""
        mock_result = MagicMock()
        mock_result.inserted_id = "mock_id_456"

        repo.collection.insert_one = AsyncMock(return_value=mock_result)

        skill = {"base_id": "new-skill", "name": "New Skill"}
        result = await repo.create(skill)

        assert result == "mock_id_456"
        call_args = repo.collection.insert_one.call_args[0][0]
        assert "created_at" in call_args
        assert "updated_at" in call_args

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, sample_skill):
        """测试获取存在的Skill"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)

        result = await repo.get_by_id("test-skill-001")

        assert result == sample_skill

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        """测试获取不存在的Skill"""
        repo.collection.find_one = AsyncMock(return_value=None)

        result = await repo.get_by_id("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_skills(self, repo, sample_skill):
        """测试列出Skill"""
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[sample_skill])

        repo.collection.find = MagicMock(return_value=mock_cursor)
        repo.collection.count_documents = AsyncMock(return_value=1)

        items, total = await repo.list()

        assert len(items) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_update_success(self, repo, sample_skill):
        """测试更新Skill成功"""
        mock_result = MagicMock()
        mock_result.modified_count = 1

        repo.collection.update_one = AsyncMock(return_value=mock_result)
        repo.collection.find_one = AsyncMock(return_value=sample_skill)

        result = await repo.update("test-skill-001", {"name": "新名称"})

        assert result == sample_skill

    @pytest.mark.asyncio
    async def test_update_not_found(self, repo):
        """测试更新不存在的Skill"""
        mock_result = MagicMock()
        mock_result.modified_count = 0

        repo.collection.update_one = AsyncMock(return_value=mock_result)

        result = await repo.update("non-existent", {"name": "新名称"})

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_success(self, repo):
        """测试删除Skill成功"""
        mock_result = MagicMock()
        mock_result.deleted_count = 1

        repo.collection.delete_one = AsyncMock(return_value=mock_result)

        result = await repo.delete("test-skill-001")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo):
        """测试删除不存在的Skill"""
        mock_result = MagicMock()
        mock_result.deleted_count = 0

        repo.collection.delete_one = AsyncMock(return_value=mock_result)

        result = await repo.delete("non-existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_create_version_not_found(self, repo):
        """测试为不存在的Skill创建版本"""
        repo.collection.find_one = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await repo.create_version("non-existent", {"prompt_template": "Hello"})

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_version_first(self, repo, sample_skill):
        """测试创建第一个版本"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)
        repo.collection.update_one = AsyncMock()

        version = {"prompt_template": "New template", "status": "draft"}
        result = await repo.create_version("test-skill-001", version)

        assert result == 1
        assert version["version_id"] == 1
        assert "created_at" in version

    @pytest.mark.asyncio
    async def test_create_version_existing(self, repo):
        """测试为已有版本的Skill创建新版本"""
        skill = {
            "base_id": "test-skill-001",
            "versions": [
                {"version_id": 0, "status": "published"},
                {"version_id": 1, "status": "draft"}
            ]
        }
        repo.collection.find_one = AsyncMock(return_value=skill)
        repo.collection.update_one = AsyncMock()

        version = {"prompt_template": "New version", "status": "draft"}
        result = await repo.create_version("test-skill-001", version)

        assert result == 2

    @pytest.mark.asyncio
    async def test_get_version_found(self, repo, sample_skill):
        """测试获取存在的版本"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)

        result = await repo.get_version("test-skill-001", 0)

        assert result == sample_skill["versions"][0]

    @pytest.mark.asyncio
    async def test_get_version_not_found(self, repo, sample_skill):
        """测试获取不存在的版本"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)

        result = await repo.get_version("test-skill-001", 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_version_success(self, repo, sample_skill):
        """测试更新版本成功"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)
        repo.collection.update_one = AsyncMock()

        result = await repo.update_version("test-skill-001", 0, {"prompt_template": "Updated"})

        assert result["prompt_template"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_version_not_found(self, repo, sample_skill):
        """测试更新不存在的版本"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)

        result = await repo.update_version("test-skill-001", 999, {"prompt_template": "Updated"})

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_version_success(self, repo, sample_skill):
        """测试删除版本成功"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)
        repo.collection.update_one = AsyncMock()

        result = await repo.delete_version("test-skill-001", 0)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_version_not_found(self, repo, sample_skill):
        """测试删除不存在的版本"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)

        result = await repo.delete_version("test-skill-001", 999)

        assert result is False

    @pytest.mark.asyncio
    async def test_publish_version(self, repo, sample_skill):
        """测试发布版本"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)
        repo.collection.update_one = AsyncMock()

        result = await repo.publish_version("test-skill-001", 0)

        assert result is not None

    @pytest.mark.asyncio
    async def test_rollback(self, repo, sample_skill):
        """测试回滚"""
        repo.collection.find_one = AsyncMock(return_value=sample_skill)
        repo.collection.update_one = AsyncMock()

        result = await repo.rollback("test-skill-001", 0)

        assert result is not None
