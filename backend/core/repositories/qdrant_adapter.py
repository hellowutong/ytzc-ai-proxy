"""
Qdrant适配器 - IVectorRepository的实现

使用Qdrant作为向量数据库，支持向量存储和相似度搜索。
"""

from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter

from .interfaces import IVectorRepository


class QdrantAdapter(IVectorRepository):
    """Qdrant向量存储适配器"""

    # 距离度量方式映射
    DISTANCE_MAPPING = {
        "cosine": Distance.COSINE,
        "euclid": Distance.EUCLID,
        "dot": Distance.DOT,
        "manhattan": Distance.MANHATTAN,
    }

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection: Optional[str] = None,
        api_key: Optional[str] = None,
        https: bool = False,
        **kwargs
    ):
        """初始化Qdrant适配器

        Args:
            host: Qdrant服务器主机
            port: Qdrant服务器端口
            collection: 默认集合名称（可选）
            api_key: API密钥（用于云端Qdrant）
            https: 是否使用HTTPS
            **kwargs: 其他连接参数
        """
        self.host = host
        self.port = port
        self.default_collection = collection
        self.api_key = api_key
        self.https = https
        self.extra_config = kwargs

        self._client: Optional[QdrantClient] = None

    async def connect(self) -> None:
        """建立Qdrant连接"""
        if self.api_key:
            # 云端Qdrant
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                https=self.https,
                **self.extra_config
            )
        else:
            # 本地Qdrant
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                **self.extra_config
            )

        # 测试连接
        self._client.get_collections()

    async def disconnect(self) -> None:
        """关闭Qdrant连接

        Qdrant客户端不需要显式关闭
        """
        self._client = None

    def _get_client(self) -> QdrantClient:
        """获取客户端实例"""
        if not self._client:
            raise RuntimeError("Qdrant未连接，请先调用connect()")
        return self._client

    def _get_distance(self, distance: str) -> Distance:
        """获取距离度量方式"""
        dist = self.DISTANCE_MAPPING.get(distance.lower())
        if not dist:
            raise ValueError(f"不支持的距离度量方式: {distance}")
        return dist

    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance: str = "cosine"
    ) -> None:
        """创建向量集合

        Args:
            name: 集合名称
            dimension: 向量维度
            distance: 距离度量方式 (cosine, euclid, dot)
        """
        client = self._get_client()

        # 检查集合是否已存在
        collections = client.get_collections().collections
        exists = any(c.name == name for c in collections)

        if exists:
            return

        # 创建集合
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=self._get_distance(distance)
            )
        )

    async def upsert(
        self,
        collection: str,
        vectors: List[Dict[str, Any]]
    ) -> None:
        """插入或更新向量

        Args:
            collection: 集合名称
            vectors: 向量数据列表
                [{"id": "uuid", "vector": [0.1, ...], "payload": {...}}, ...]
        """
        client = self._get_client()

        points = []
        for v in vectors:
            point = PointStruct(
                id=v["id"],
                vector=v["vector"],
                payload=v.get("payload", {})
            )
            points.append(point)

        client.upsert(
            collection_name=collection,
            points=points
        )

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索

        Args:
            collection: 集合名称
            query_vector: 查询向量
            top_k: 返回结果数量
            threshold: 相似度阈值
            filters: 过滤条件

        Returns:
            搜索结果列表 [{"id": str, "score": float, "payload": dict}, ...]
        """
        client = self._get_client()

        # 构建过滤条件
        qdrant_filter = None
        if filters:
            # 简化处理，实际使用时可以根据需要扩展
            qdrant_filter = Filter(**filters)

        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=threshold,
            query_filter=qdrant_filter
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]

    async def delete(self, collection: str, ids: List[str]) -> None:
        """删除向量

        Args:
            collection: 集合名称
            ids: 要删除的向量ID列表
        """
        client = self._get_client()

        client.delete(
            collection_name=collection,
            points_selector=ids
        )
