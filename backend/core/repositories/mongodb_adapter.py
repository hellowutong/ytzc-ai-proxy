"""
MongoDB适配器 - IDocumentRepository的实现

使用Motor作为异步MongoDB驱动。
"""

from typing import List, Tuple, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from .interfaces import IDocumentRepository


class MongoDBAdapter(IDocumentRepository):
    """MongoDB文档存储适配器"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27017,
        database: str = "ai_gateway",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """初始化MongoDB适配器

        Args:
            host: MongoDB主机地址
            port: MongoDB端口
            database: 数据库名称
            username: 用户名（可选）
            password: 密码（可选）
            **kwargs: 其他连接参数
        """
        self.host = host
        self.port = port
        self.database_name = database
        self.username = username
        self.password = password
        self.extra_config = kwargs

        self._client: Optional[AsyncIOMotorClient] = None
        self._database = None

    async def connect(self) -> None:
        """建立MongoDB连接"""
        if self.username and self.password:
            uri = (
                f"mongodb://{self.username}:{self.password}"
                f"@{self.host}:{self.port}/{self.database_name}"
                f"?authSource=admin"
            )
        else:
            uri = f"mongodb://{self.host}:{self.port}/{self.database_name}"

        self._client = AsyncIOMotorClient(uri)
        self._database = self._client[self.database_name]

        # 测试连接
        await self._client.admin.command('ping')

    async def disconnect(self) -> None:
        """关闭MongoDB连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None

    def _get_collection(self, collection: str):
        """获取集合对象"""
        if not self._database:
            raise RuntimeError("MongoDB未连接，请先调用connect()")
        return self._database[collection]

    @staticmethod
    def _objectid_to_str(document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """将文档中的ObjectId转换为字符串"""
        if document is None:
            return None
        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])
        return document

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """插入单条文档，返回ID

        Args:
            collection: 集合名称
            document: 文档数据

        Returns:
            插入文档的ID
        """
        coll = self._get_collection(collection)
        result = await coll.insert_one(document)
        return str(result.inserted_id)

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查询单条文档

        Args:
            collection: 集合名称
            query: 查询条件

        Returns:
            匹配的文档，未找到返回None
        """
        coll = self._get_collection(collection)
        document = await coll.find_one(query)
        return self._objectid_to_str(document)

    async def find_many(
        self,
        collection: str,
        query: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """查询多条文档

        Args:
            collection: 集合名称
            query: 查询条件
            sort: 排序规则 [(field, direction), ...]
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            (文档列表, 总数)
        """
        coll = self._get_collection(collection)

        # 构建查询
        cursor = coll.find(query)

        if sort:
            cursor = cursor.sort(sort)

        cursor = cursor.skip(skip).limit(limit)

        # 获取总数
        total = await coll.count_documents(query)

        # 获取数据
        documents = []
        async for doc in cursor:
            documents.append(self._objectid_to_str(doc))

        return documents, total

    async def update_one(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """更新单条文档

        Args:
            collection: 集合名称
            query: 查询条件
            update: 更新内容

        Returns:
            是否更新成功
        """
        coll = self._get_collection(collection)
        result = await coll.update_one(query, {"$set": update})
        return result.modified_count > 0

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """删除单条文档

        Args:
            collection: 集合名称
            query: 查询条件

        Returns:
            是否删除成功
        """
        coll = self._get_collection(collection)
        result = await coll.delete_one(query)
        return result.deleted_count > 0
