"""
MongoDB 集成测试
测试真实的MongoDB数据库连接和操作
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMongoDBIntegration:
    """MongoDB集成测试类"""

    @pytest.fixture(scope="class")
    def mongodb(self):
        """获取MongoDB连接类"""
        try:
            from app.infrastructure.database.mongodb import MongoDB
            return MongoDB
        except ImportError:
            pytest.skip("MongoDB模块未安装")

    @pytest.mark.asyncio
    async def test_mongodb_connection(self, mongodb, mongodb_services):
        """测试MongoDB连接"""
        await mongodb.connect()

        # 验证连接状态
        assert mongodb.client is not None
        assert mongodb.db is not None

        await mongodb.disconnect()

    @pytest.mark.asyncio
    async def test_session_crud_operations(self, mongodb, mongodb_services):
        """测试会话CRUD操作"""
        await mongodb.connect()

        collection = mongodb.get_collection("test_sessions")

        # 创建会话
        session_data = {
            "proxy_key": "test-key-mongodb-001",
            "status": "active",
            "messages": [
                {"role": "user", "content": "测试消息", "timestamp": datetime.now().isoformat()}
            ],
            "summary": "测试会话",
            "created_at": datetime.now().isoformat()
        }

        result = await collection.insert_one(session_data)
        session_id = result.inserted_id
        assert session_id is not None

        # 读取会话
        found_session = await collection.find_one({"_id": session_id})
        assert found_session is not None
        assert found_session["proxy_key"] == session_data["proxy_key"]
        assert found_session["status"] == session_data["status"]

        # 更新会话
        update_data = {"status": "completed", "updated_at": datetime.now().isoformat()}
        await collection.update_one({"_id": session_id}, {"$set": update_data})
        updated_session = await collection.find_one({"_id": session_id})
        assert updated_session["status"] == "completed"

        # 删除会话
        await collection.delete_one({"_id": session_id})
        deleted_session = await collection.find_one({"_id": session_id})
        assert deleted_session is None

        await mongodb.disconnect()

    @pytest.mark.asyncio
    async def test_skill_crud_operations(self, mongodb, mongodb_services):
        """测试Skill CRUD操作"""
        await mongodb.connect()

        collection = mongodb.get_collection("test_skills")

        # 创建Skill
        skill_data = {
            "base_id": f"test-skill-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "测试技能",
            "active_version_id": 1,
            "versions": [
                {
                    "version_id": 1,
                    "status": "published",
                    "created_at": datetime.now().isoformat(),
                    "created_by": "test-user",
                    "source_session_id": "session-001",
                    "change_reason": "初始版本",
                    "content": "# 测试技能\n\n这是一个测试技能"
                }
            ],
            "created_at": datetime.now().isoformat()
        }

        result = await collection.insert_one(skill_data)
        skill_id = result.inserted_id
        assert skill_id is not None

        # 读取Skill
        found_skill = await collection.find_one({"_id": skill_id})
        assert found_skill is not None
        assert found_skill["base_id"] == skill_data["base_id"]

        # 更新Skill版本
        new_version = {
            "version_id": 2,
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "created_by": "test-user",
            "source_session_id": "session-002",
            "change_reason": "更新内容",
            "content": "# 测试技能 v2\n\n这是更新后的内容"
        }
        await collection.update_one(
            {"_id": skill_id},
            {"$push": {"versions": new_version}, "$set": {"active_version_id": 2}}
        )
        updated_skill = await collection.find_one({"_id": skill_id})
        assert len(updated_skill["versions"]) == 2
        assert updated_skill["active_version_id"] == 2

        # 删除Skill
        await collection.delete_one({"_id": skill_id})
        deleted_skill = await collection.find_one({"_id": skill_id})
        assert deleted_skill is None

        await mongodb.disconnect()

    @pytest.mark.asyncio
    async def test_collection_listing(self, mongodb, mongodb_services):
        """测试集合列表查询"""
        await mongodb.connect()

        collections = await mongodb.client.list_database_names()
        assert isinstance(collections, list)

        await mongodb.disconnect()

    @pytest.mark.asyncio
    async def test_index_creation(self, mongodb, mongodb_services):
        """测试索引创建"""
        await mongodb.connect()

        collection = mongodb.get_collection("test_indexes")

        # 创建索引
        await collection.create_index("proxy_key")
        await collection.create_index("created_at")

        # 验证索引存在
        indexes = await collection.index_information()
        index_names = list(indexes.keys())
        assert "proxy_key_1" in index_names
        assert "created_at_1" in index_names

        # 清理
        await collection.drop()
        await mongodb.disconnect()


class TestMongoDBSessionRepository:
    """测试会话仓储实现"""

    @pytest.fixture(scope="class")
    def repository(self):
        """获取仓储类（仅用于参考，实际测试需要MongoDB）"""
        return None  # 由于需要真实MongoDB，返回None并跳过

    @pytest.mark.skip(reason="需要真实的MongoDB服务")
    @pytest.mark.asyncio
    async def test_create_session(self, repository, mongodb_services):
        """测试创建会话 - 已跳过"""
        pass

    @pytest.mark.skip(reason="需要真实的MongoDB服务")
    @pytest.mark.asyncio
    async def test_get_session(self, repository, mongodb_services):
        """测试获取会话 - 已跳过"""
        pass

    @pytest.mark.skip(reason="需要真实的MongoDB服务")
    @pytest.mark.asyncio
    async def test_list_sessions(self, repository, mongodb_services):
        """测试列出会话 - 已跳过"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
