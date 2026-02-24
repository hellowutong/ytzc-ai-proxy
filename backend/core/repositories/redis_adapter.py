"""
Redis适配器 - ICacheRepository的实现

使用Redis作为缓存和队列服务。
"""

from typing import Optional
import redis.asyncio as redis

from .interfaces import ICacheRepository


class RedisAdapter(ICacheRepository):
    """Redis缓存适配器"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        **kwargs
    ):
        """初始化Redis适配器

        Args:
            host: Redis主机地址
            port: Redis端口
            db: 数据库编号
            password: 密码（可选）
            decode_responses: 是否自动解码响应
            **kwargs: 其他连接参数
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.extra_config = kwargs

        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """建立Redis连接"""
        connection_params = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "decode_responses": self.decode_responses,
            **self.extra_config
        }

        if self.password:
            connection_params["password"] = self.password

        self._client = await redis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            **connection_params
        )

        # 测试连接
        await self._client.ping()

    async def disconnect(self) -> None:
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None

    def _get_client(self) -> redis.Redis:
        """获取客户端实例"""
        if not self._client:
            raise RuntimeError("Redis未连接，请先调用connect()")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        client = self._get_client()
        return await client.get(key)

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
        """
        client = self._get_client()
        await client.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        """删除缓存

        Args:
            key: 缓存键
        """
        client = self._get_client()
        await client.delete(key)

    async def lpush(self, queue: str, value: str) -> None:
        """队列左侧推入（LPush）

        Args:
            queue: 队列名称
            value: 要推入的值
        """
        client = self._get_client()
        await client.lpush(queue, value)

    async def rpop(self, queue: str, timeout: int = 0) -> Optional[str]:
        """队列右侧弹出（BRPop）

        使用BRPop实现阻塞式弹出

        Args:
            queue: 队列名称
            timeout: 超时时间（秒），0表示永久阻塞

        Returns:
            弹出的值，超时返回None
        """
        client = self._get_client()
        result = await client.brpop(queue, timeout=timeout)

        if result is None:
            return None

        # brpop返回 (queue_name, value) 元组
        if isinstance(result, tuple) and len(result) == 2:
            return result[1]

        return result
