"""
RSS抓取器 - RSS订阅管理、抓取、内容提取
"""

import uuid
import feedparser
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from readability import Document
import html2text


class RSSFetcher:
    """RSS抓取器类"""
    
    def __init__(
        self,
        mongodb: AsyncIOMotorClient,
        knowledge_manager=None,
        timeout: float = 30.0
    ):
        """
        初始化RSS抓取器
        
        Args:
            mongodb: MongoDB客户端
            knowledge_manager: 知识管理器实例
            timeout: HTTP请求超时时间（秒）
        """
        self._mongodb = mongodb
        self._knowledge_manager = knowledge_manager
        self._timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # 数据库集合
        self._db = mongodb["ai_gateway"]
        self._subscriptions_collection = self._db["rss_subscriptions"]
        self._articles_collection = self._db["rss_articles"]
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取或创建HTTP客户端"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._http_client
    
    async def fetch_feed(self, subscription_id: str) -> Dict[str, Any]:
        """
        抓取单个RSS订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            抓取结果字典
        """
        # 获取订阅信息
        subscription = await self._subscriptions_collection.find_one(
            {"_id": subscription_id}
        )
        if not subscription:
            raise ValueError(f"订阅不存在: {subscription_id}")
        
        if not subscription.get("enabled", True):
            return {
                "subscription_id": subscription_id,
                "articles_fetched": 0,
                "message": "订阅已禁用"
            }
        
        # 解析RSS feed
        try:
            feed = feedparser.parse(subscription["url"])
        except Exception as e:
            raise RuntimeError(f"解析RSS失败: {e}")
        
        articles_fetched = 0
        articles_skipped = 0
        
        # 遍历文章
        for entry in feed.entries:
            # 检查文章是否已存在
            existing = await self._articles_collection.find_one({
                "subscription_id": subscription_id,
                "url": entry.link
            })
            
            if existing:
                articles_skipped += 1
                continue
            
            try:
                # 访问原文链接，爬取完整内容
                article_content = await self._fetch_full_content(entry.link)
                
                # 解析发布时间
                published_at = self._parse_date(entry.get("published", ""))
                
                # 保存到MongoDB
                article_id = str(uuid.uuid4())
                article = {
                    "_id": article_id,
                    "subscription_id": subscription_id,
                    "title": entry.get("title", "无标题"),
                    "url": entry.link,
                    "content": article_content["cleaned"],
                    "raw_content": article_content["raw"],
                    "content_format": "markdown",
                    "published_at": published_at,
                    "fetched_at": datetime.utcnow(),
                    "is_read": False,
                    "knowledge_extracted": False,
                    "knowledge_doc_ids": [],
                    "fetch_status": article_content["status"],
                    "fetch_method": "readability"
                }
                
                await self._articles_collection.insert_one(article)
                articles_fetched += 1
                
                # 触发知识提取
                if subscription.get("auto_extract", True) and self._knowledge_manager:
                    try:
                        await self._extract_article_knowledge(
                            article_id,
                            subscription.get("virtual_model")
                        )
                    except Exception as e:
                        print(f"知识提取失败: {e}")
                
            except Exception as e:
                print(f"处理文章失败 {entry.link}: {e}")
                continue
        
        # 更新最后抓取时间和文章计数
        await self._subscriptions_collection.update_one(
            {"_id": subscription_id},
            {
                "$set": {
                    "last_fetch_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"article_count": articles_fetched}
            }
        )
        
        return {
            "subscription_id": subscription_id,
            "subscription_name": subscription.get("name"),
            "articles_fetched": articles_fetched,
            "articles_skipped": articles_skipped,
            "feed_title": feed.feed.get("title", "") if "rsshub.app" not in url else name,
            "fetch_time": datetime.utcnow()
        }
    
    async def _fetch_full_content(self, url: str) -> Dict[str, str]:
        """
        爬取完整文章内容
        
        Args:
            url: 文章URL
            
        Returns:
            包含原始HTML、清理后内容和Markdown的字典
        """
        client = await self._get_http_client()
        
        try:
            # 发送HTTP请求获取HTML
            response = await client.get(url)
            response.raise_for_status()
            raw_html = response.text
            
            # 使用readability-lxml提取正文
            doc = Document(raw_html)
            cleaned_content = doc.summary()
            title = doc.short_title()
            
            # 转换为Markdown
            markdown_content = html2text.html2text(cleaned_content)
            
            return {
                "raw": raw_html,
                "cleaned": cleaned_content,
                "markdown": markdown_content,
                "title": title,
                "status": "full_content"
            }
            
        except httpx.HTTPError as e:
            # HTTP请求失败，返回摘要信息
            return {
                "raw": "",
                "cleaned": f"无法获取完整内容: {e}",
                "markdown": f"无法获取完整内容: {e}",
                "title": "",
                "status": "failed"
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串
            
        Returns:
            datetime对象或None
        """
        if not date_str:
            return None
        
        try:
            # feedparser可以解析多种日期格式
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6])
        except Exception:
            pass
        
        return datetime.utcnow()
    
    async def _extract_article_knowledge(self, article_id: str, virtual_model: Optional[str]):
        """
        从文章中提取知识
        
        Args:
            article_id: 文章ID
            virtual_model: 虚拟模型名称
        """
        if not self._knowledge_manager:
            return
        
        article = await self._articles_collection.find_one({"_id": article_id})
        if not article:
            return
        
        # TODO: 调用知识管理器进行知识提取
        # 这里可以根据实际需求实现知识提取逻辑
        
        # 更新文章状态
        await self._articles_collection.update_one(
            {"_id": article_id},
            {
                "$set": {
                    "knowledge_extracted": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def create_subscription(
        self,
        name: str,
        url: str,
        virtual_model: str,
        fetch_interval: int = 30,
        retention_days: int = 30,
        auto_extract: bool = True,
        default_permanent: bool = False
    ) -> Dict[str, Any]:
        """
        创建RSS订阅
        
        Args:
            name: 订阅名称
            url: RSS URL
            virtual_model: 关联的虚拟模型
            fetch_interval: 抓取间隔（分钟）
            retention_days: 保留天数
            auto_extract: 是否自动提取知识
            default_permanent: 默认是否永久保存
            
        Returns:
            订阅信息字典
        """
        # 转换 RSSHub URL
        if url.startswith("rsshub://"):
            url = url.replace("rsshub://", "https://rsshub.app/")
        
        # 验证URL格式
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL必须以http://或https://开头")
        
        # 对非RSSHub URL进行严格验证
        # RSSHub URL经常被Cloudflare保护，无法直接验证
        if "rsshub.app" not in url:
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    raise ValueError("无效的RSS URL或无法解析")
            except Exception as e:
                raise ValueError(f"验证RSS URL失败: {e}")
        
        subscription_id = str(uuid.uuid4())
        subscription = {
            "_id": subscription_id,
            "name": name,
            "url": url,
            "enabled": True,
            "fetch_interval": fetch_interval,
            "retention_days": retention_days,
            "default_permanent": default_permanent,
            "auto_extract": auto_extract,
            "virtual_model": virtual_model,
            "article_count": 0,
            "last_fetch_time": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self._subscriptions_collection.insert_one(subscription)
        
        
        # 获取feed标题
        if "rsshub.app" in url:
            feed_title = name
        else:
            feed_title = feed.feed.get("title", name)
        
        return {
            "id": subscription_id,
            "name": name,
            "url": url,
            "enabled": True,
            "feed_title": feed_title,
            "created_at": subscription["created_at"]
        }
    
    async def list_subscriptions(
        self,
        virtual_model: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        列出RSS订阅
        
        Args:
            virtual_model: 虚拟模型筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            包含订阅列表和总数的字典
        """
        query = {}
        if virtual_model:
            query["virtual_model"] = virtual_model
        
        cursor = self._subscriptions_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        subscriptions = []
        
        async for doc in cursor:
            subscriptions.append({
                "id": doc["_id"],
                "name": doc["name"],
                "url": doc["url"],
                "enabled": doc.get("enabled", True),
                "fetch_interval": doc.get("fetch_interval", 30),
                "article_count": doc.get("article_count", 0),
                "last_fetch_time": doc.get("last_fetch_time"),
                "virtual_model": doc.get("virtual_model"),
                "created_at": doc["created_at"]
            })
        
        total = await self._subscriptions_collection.count_documents(query)
        
        return {
            "subscriptions": subscriptions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        获取订阅详情
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            订阅详情字典，不存在则返回None
        """
        doc = await self._subscriptions_collection.find_one({"_id": subscription_id})
        if not doc:
            return None
        
        return {
            "id": doc["_id"],
            "name": doc["name"],
            "url": doc["url"],
            "enabled": doc.get("enabled", True),
            "fetch_interval": doc.get("fetch_interval", 30),
            "retention_days": doc.get("retention_days", 30),
            "article_count": doc.get("article_count", 0),
            "last_fetch_time": doc.get("last_fetch_time"),
            "virtual_model": doc.get("virtual_model"),
            "auto_extract": doc.get("auto_extract", True),
            "created_at": doc["created_at"]
        }
    
    async def update_subscription(
        self,
        subscription_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        更新订阅
        
        Args:
            subscription_id: 订阅ID
            updates: 更新字段
            
        Returns:
            是否成功更新
        """
        # 不允许修改的字段
        forbidden_fields = {"_id", "created_at", "article_count"}
        update_data = {k: v for k, v in updates.items() if k not in forbidden_fields}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self._subscriptions_collection.update_one(
            {"_id": subscription_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        删除订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            是否成功删除
        """
        # 先删除关联的文章
        await self._articles_collection.delete_many({"subscription_id": subscription_id})
        
        # 删除订阅
        result = await self._subscriptions_collection.delete_one({"_id": subscription_id})
        
        return result.deleted_count > 0
    
    async def list_articles(
        self,
        subscription_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        列出文章
        
        Args:
            subscription_id: 订阅ID筛选
            is_read: 已读状态筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            包含文章列表和总数的字典
        """
        query = {}
        if subscription_id:
            query["subscription_id"] = subscription_id
        if is_read is not None:
            query["is_read"] = is_read
        
        cursor = self._articles_collection.find(query).sort("fetched_at", -1).skip(offset).limit(limit)
        articles = []
        
        async for doc in cursor:
            articles.append({
                "id": doc["_id"],
                "subscription_id": doc["subscription_id"],
                "title": doc["title"],
                "url": doc["url"],
                "is_read": doc.get("is_read", False),
                "knowledge_extracted": doc.get("knowledge_extracted", False),
                "published_at": doc.get("published_at"),
                "fetched_at": doc["fetched_at"]
            })
        
        total = await self._articles_collection.count_documents(query)
        
        return {
            "articles": articles,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文章详情
        
        Args:
            article_id: 文章ID
            
        Returns:
            文章详情字典，不存在则返回None
        """
        doc = await self._articles_collection.find_one({"_id": article_id})
        if not doc:
            return None
        
        return {
            "id": doc["_id"],
            "subscription_id": doc["subscription_id"],
            "title": doc["title"],
            "url": doc["url"],
            "content": doc["content"],
            "is_read": doc.get("is_read", False),
            "knowledge_extracted": doc.get("knowledge_extracted", False),
            "knowledge_doc_ids": doc.get("knowledge_doc_ids", []),
            "fetch_status": doc.get("fetch_status"),
            "published_at": doc.get("published_at"),
            "fetched_at": doc["fetched_at"]
        }
    
    async def mark_article_read(self, article_id: str, is_read: bool = True) -> bool:
        """
        标记文章已读/未读
        
        Args:
            article_id: 文章ID
            is_read: 是否已读
            
        Returns:
            是否成功更新
        """
        result = await self._articles_collection.update_one(
            {"_id": article_id},
            {
                "$set": {
                    "is_read": is_read,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
