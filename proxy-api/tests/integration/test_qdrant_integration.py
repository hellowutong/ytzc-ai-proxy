"""
Qdrant 向量数据库集成测试
测试真实的Qdrant向量数据库连接和操作
"""
import sys
from pathlib import Path
import pytest
import numpy as np
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestQdrantIntegration:
    """Qdrant集成测试类"""

    @pytest.fixture(scope="class")
    def qdrant(self):
        """获取Qdrant连接类"""
        try:
            from app.infrastructure.database.qdrant import Qdrant
            return Qdrant
        except ImportError:
            pytest.skip("Qdrant模块未安装")

    @pytest.fixture(scope="class")
    def test_collection_name(self):
        """测试集合名称"""
        return f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @pytest.mark.asyncio
    async def test_qdrant_connection(self, qdrant, qdrant_services):
        """测试Qdrant连接"""
        await qdrant.connect()
        assert qdrant.client is not None
        await qdrant.disconnect()

    @pytest.mark.asyncio
    async def test_collection_operations(self, qdrant, qdrant_services, test_collection_name):
        """测试集合操作"""
        await qdrant.connect()
        
        from qdrant_client.models import VectorParams, Distance

        try:
            await qdrant.client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception:
            pass

        collections = await qdrant.get_collections()
        assert test_collection_name in collections

        info = await qdrant.client.get_collection(collection_name=test_collection_name)
        assert info is not None

        try:
            await qdrant.client.delete_collection(collection_name=test_collection_name)
        except Exception:
            pass

        await qdrant.disconnect()

    @pytest.mark.asyncio
    async def test_vector_upsert_and_search(self, qdrant, qdrant_services, test_collection_name):
        """测试向量Upsert和搜索"""
        await qdrant.connect()

        from qdrant_client.models import VectorParams, Distance, PointStruct

        try:
            await qdrant.client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception:
            pass

        vectors = [
            np.random.randn(768).tolist(),
            np.random.randn(768).tolist(),
            np.random.randn(768).tolist()
        ]
        payloads = [
            {"session_id": "session-001", "content": "测试内容1"},
            {"session_id": "session-002", "content": "测试内容2"},
            {"session_id": "session-003", "content": "测试内容3"}
        ]

        points = []
        for i, (vec, payload) in enumerate(zip(vectors, payloads)):
            points.append(PointStruct(
                id=i + 1,
                vector=vec,
                payload=payload
            ))

        await qdrant.client.upsert(collection_name=test_collection_name, points=points)

        info = await qdrant.client.get_collection(collection_name=test_collection_name)
        assert info.vectors_count == 3 if hasattr(info, 'vectors_count') else info.points_count == 3

        try:
            await qdrant.client.delete_collection(collection_name=test_collection_name)
        except Exception:
            pass
        await qdrant.disconnect()

    @pytest.mark.asyncio
    async def test_vector_delete(self, qdrant, qdrant_services, test_collection_name):
        """测试向量删除"""
        await qdrant.connect()

        from qdrant_client.models import VectorParams, Distance, PointStruct

        try:
            await qdrant.client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception:
            pass

        vector = np.random.randn(768).tolist()
        await qdrant.client.upsert(
            collection_name=test_collection_name,
            points=[PointStruct(id=100, vector=vector, payload={"session_id": "to-delete"})]
        )

        await qdrant.client.delete(
            collection_name=test_collection_name,
            points_selector=[100]
        )

        info = await qdrant.client.get_collection(collection_name=test_collection_name)
        assert info.vectors_count == 0 if hasattr(info, 'vectors_count') else info.points_count == 0

        try:
            await qdrant.client.delete_collection(collection_name=test_collection_name)
        except Exception:
            pass
        await qdrant.disconnect()

    @pytest.mark.asyncio
    async def test_batch_operations(self, qdrant, qdrant_services, test_collection_name):
        """测试批量操作"""
        await qdrant.connect()

        from qdrant_client.models import VectorParams, Distance, PointStruct

        try:
            await qdrant.client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception:
            pass

        batch_size = 10
        points = []
        for i in range(batch_size):
            points.append(PointStruct(
                id=i + 1,
                vector=np.random.randn(768).tolist(),
                payload={"session_id": f"session-{i}", "index": i}
            ))

        await qdrant.client.upsert(collection_name=test_collection_name, points=points)

        info = await qdrant.client.get_collection(collection_name=test_collection_name)
        assert info.vectors_count == batch_size if hasattr(info, 'vectors_count') else info.points_count == batch_size

        ids_to_delete = list(range(1, 6))
        await qdrant.client.delete(collection_name=test_collection_name, points_selector=ids_to_delete)

        info_after = await qdrant.client.get_collection(collection_name=test_collection_name)
        assert info_after.vectors_count == 5 if hasattr(info_after, 'vectors_count') else info_after.points_count == 5

        try:
            await qdrant.client.delete_collection(collection_name=test_collection_name)
        except Exception:
            pass
        await qdrant.disconnect()

    @pytest.mark.asyncio
    async def test_scroll_points(self, qdrant, qdrant_services, test_collection_name):
        """测试滚动查询向量"""
        await qdrant.connect()

        from qdrant_client.models import VectorParams, Distance, PointStruct

        try:
            await qdrant.client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        except Exception:
            pass

        points = []
        for i in range(5):
            points.append(PointStruct(
                id=i + 1,
                vector=np.random.randn(768).tolist(),
                payload={"index": i}
            ))

        await qdrant.client.upsert(collection_name=test_collection_name, points=points)

        scroll_result = await qdrant.client.scroll(
            collection_name=test_collection_name,
            limit=5
        )
        points_result = scroll_result[0] if isinstance(scroll_result, tuple) else scroll_result.points
        assert len(points_result) >= 1

        try:
            await qdrant.client.delete_collection(collection_name=test_collection_name)
        except Exception:
            pass
        await qdrant.disconnect()


class TestQdrantVectorRepository:
    """测试向量仓储实现"""

    @pytest.fixture(scope="class")
    def repository(self):
        """获取仓储实例"""
        try:
            from app.infrastructure.repositories.vector_repo import VectorRepositoryImpl
            return VectorRepositoryImpl
        except ImportError:
            pytest.skip("向量仓储模块未安装")

    @pytest.mark.asyncio
    async def test_collections_exist(self, repository, qdrant_services):
        """测试集合存在性"""
        from app.infrastructure.database.qdrant import Qdrant
        qdrant = Qdrant()
        await qdrant.connect()

        collections = await qdrant.get_collections()
        assert "sessions" in collections
        assert "skills" in collections

        await qdrant.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
