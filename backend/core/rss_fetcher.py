"""
RSS抓取器 - RSS订阅管理、抓取、内容提取
"""

import uuid
import os
import logging
import feedparser
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from readability import Document
import html2text


import feedparser
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from readability import Document
import html2text


class RSSFetcher:
    """RSS抓取器类"""
    
    # RSSHub 服务地址列表（按优先级排序，已测试可用）
    # 优先使用稳定的公共实例
    RSS_HUB_URLS = [
        "http://rsshub:1200",  # 私有实例（需自行部署）
        "https://rsshub.rssforever.com",  # 公共实例 - 阿联酋
        "https://rsshub.ktachibana.party",  # 公共实例 - 美国
        "https://rsshub.rss.tips",  # 公共实例 - 美国
        "https://rss.owo.nz",  # 公共实例 - 德国
        "https://rsshub.henry.wang",  # 公共实例 - 英国
        "https://rsshub.app",  # 官方实例（Cloudflare保护）
    ]
    
    # 兼容旧配置
    RSS_HUB_URL = os.environ.get("RSS_HUB_URL", "http://rsshub:1200")
    RSS_HUB_PUBLIC = "rsshub.app"
    
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
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
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
    
    def _is_rsshub_url(self, url: str) -> bool:
        """检查是否是RSSHub URL"""
        for rsshub_base in RSSFetcher.RSS_HUB_URLS:
            base = rsshub_base.replace("http://", "").replace("https://", "")
            if base in url:
                return True
        return False
    
    async def _fetch_rss_with_fallback(self, url: str) -> Any:
        """
        尝试从多个RSSHub实例获取内容
        
        Args:
            url: RSS URL（可能是rsshub://或http(s)://）
            
        Returns:
            feedparser解析结果
        """
        client = await self._get_http_client()
        
        # 提取RSSHub路径
        if url.startswith("rsshub://"):
            path = url.replace("rsshub://", "")
            urls_to_try = [base + "/" + path for base in RSSFetcher.RSS_HUB_URLS]
        else:
            # 对于完整URL，提取路径并尝试所有实例
            # 找出URL中的RSSHub路径
            path = None
            for base in RSSFetcher.RSS_HUB_URLS:
                base_domain = base.replace("http://", "").replace("https://", "")
                if base_domain in url:
                    # 提取路径部分
                    path = url.split(base_domain, 1)[-1]
                    break
            
            if path:
                # 尝试所有实例
                urls_to_try = [base + path for base in RSSFetcher.RSS_HUB_URLS]
            else:
                # 非RSSHub URL，直接使用
                urls_to_try = [url]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://rsshub.app/"
        }
        
        last_error = None
        for attempt_url in urls_to_try:
            try:
                response = await client.get(attempt_url, headers=headers, follow_redirects=True, timeout=30.0)
                response.raise_for_status()
                feed = feedparser.parse(response.text)
                if feed.entries:
                    return feed
                # 如果没有entries，记录一下但继续尝试下一个
                print(f"[RSSHub] {attempt_url} 返回空内容，尝试下一个...")
            except Exception as e:
                print(f"[RSSHub] {attempt_url} 失败: {e}")
                last_error = e
                continue
        
        raise RuntimeError(f"所有RSSHub实例均获取失败: {last_error}")
    
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
        subscription_url = subscription["url"]
        is_rsshub = self._is_rsshub_url(subscription_url) or subscription_url.startswith("rsshub://")
        
        try:
            if is_rsshub:
                # 使用fallback机制获取RSSHub内容
                feed = await self._fetch_rss_with_fallback(subscription_url)
            else:
                feed = feedparser.parse(subscription_url)
        except Exception as e:
            raise RuntimeError(f"获取RSS失败: {e}")
        
        # 检查是否获取到文章
        if not feed.entries:
            return {
                "subscription_id": subscription_id,
                "subscription_name": subscription.get("name"),
                "articles_fetched": 0,
                "articles_skipped": 0,
                "feed_title": subscription.get("name", ""),
                "message": "未获取到任何文章，可能是RSS源为空或URL无效"
            }
        
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
                # 检查是否是微信文章，微信文章直接使用RSS内容避免被反爬虫
                is_wechat = "mp.weixin.qq.com" in entry.link
                
                if is_wechat:
                    # 微信文章：直接使用RSS提供的完整内容
                    # feedparser将 content_encoded 解析为 content 列表
                    content_list = entry.get("content")
                    if content_list and isinstance(content_list, list):
                        rss_content = content_list[0].get("value", "")
                    else:
                        rss_content = entry.get("description", "")
                    
                    if rss_content and len(rss_content) > 100:
                        import re
                        text = re.sub(r'<br\s*/?>', '\n', rss_content)
                        text = re.sub(r'<[^>]+>', '', text)
                        text = text.strip()
                        article_content = {
                            "raw": rss_content,
                            "cleaned": rss_content,
                            "markdown": text,
                            "title": entry.get("title", ""),
                            "status": "rss_summary"
                        }
                    else:
                        article_content = await self._fetch_full_content(entry.link)
                else:
                    # 普通文章：尝试爬取完整内容
                    article_content = await self._fetch_full_content(entry.link)
                    
                    # 如果获取失败，使用RSS摘要作为后备
                    content_status = article_content.get("status")
                    content_length = len(article_content.get("cleaned", ""))
                    
                    if content_status in ["blocked", "failed"] or content_length < 200:
                        rss_content = (
                            entry.get("content_encoded") or 
                            entry.get("description") or 
                            ""
                        )
                        if rss_content and len(rss_content) > 100:
                            import re
                            text = re.sub(r'<br\s*/?>', '\n', rss_content)
                            text = re.sub(r'<[^>]+>', '', text)
                            text = text.strip()
                            article_content = {
                                "raw": rss_content,
                                "cleaned": rss_content,
                                "markdown": text,
                                "title": entry.get("title", ""),
                                "status": "rss_summary"
                            }
                
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
            "feed_title": feed.feed.get("title", "") if is_rsshub else subscription.get("name"),
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
        
        # 检测是否是微信文章
        is_wechat = "mp.weixin.qq.com" in url
        
        # 根据网站类型设置不同的请求头
        headers = {}
        if is_wechat:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://mp.weixin.qq.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        
        try:
            # 发送HTTP请求获取HTML
            if headers:
                response = await client.get(url, headers=headers)
            else:
                response = await client.get(url)
            response.raise_for_status()
            raw_html = response.text
            
            # 检查是否被反爬虫阻止
            if is_wechat:
                # 微信文章特殊处理
                if "var msgTs =" in raw_html or "id=" in raw_html and len(raw_html) < 5000:
                    # 内容被简化，可能需要从RSS摘要获取
                    return {
                        "raw": raw_html,
                        "cleaned": "<p>微信文章内容无法获取（反爬虫保护）</p>",
                        "markdown": "微信文章内容无法获取（反爬虫保护）\n\n可能原因：\n1. 微信反爬虫机制\n2. 需要登录微信\n3. 文章已删除或不可见",
                        "title": "",
                        "status": "blocked"
                    }
            
            # 使用readability-lxml提取正文
            doc = Document(raw_html)
            cleaned_content = doc.summary()
            title = doc.short_title()
            
            # 检查是否成功提取内容
            if not cleaned_content or len(cleaned_content) < 100:
                return {
                    "raw": raw_html,
                    "cleaned": "<p>无法提取文章内容</p>",
                    "markdown": "无法提取文章内容",
                    "title": title,
                    "status": "failed"
                }
            
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
        # 转换 RSSHub URL - 保留rsshub://协议，在抓取时自动转换
        # 用户可以输入 rsshub://xueqiu/hots 或完整的 https://rsshub.app/... 格式
        is_rsshub_url = url.startswith("rsshub://")
        
        # 验证URL格式
        if not url.startswith(("http://", "https://", "rsshub://")):
            raise ValueError("URL必须以http://、https://或rsshub://开头")
        
        # 对非RSSHub URL进行严格验证
        # RSSHub URL会使用fallback机制获取，跳过验证
        if not is_rsshub_url and "rsshub" not in url:
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
        if is_rsshub_url:
            feed_title = name
        else:
            try:
                feed_title = feed.feed.get("title", name) if 'feed' in locals() else name
            except:
                feed_title = name
        
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
                "content": doc.get("content", ""),
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
    
    async def delete_article(self, article_id: str) -> bool:
        """
        删除单篇文章
        
        Args:
            article_id: 文章ID
            
        Returns:
            是否删除成功
        """
        # 先获取文章信息，以便更新订阅源的计数
        article = await self._articles_collection.find_one({"_id": article_id})
        if not article:
            self.logger.warning(f"文章不存在: {article_id}")
            return False
        
        subscription_id = article.get("subscription_id")
        
        # 删除文章
        result = await self._articles_collection.delete_one({"_id": article_id})
        
        if result.deleted_count > 0:
            # 更新订阅源的 article_count
            if subscription_id:
                await self._subscriptions_collection.update_one(
                    {"_id": subscription_id},
                    {
                        "$inc": {"article_count": -1},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            self.logger.info(f"文章已删除: {article_id}")
            return True
        
        return False
    
    async def delete_articles(self, article_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除文章
        
        Args:
            article_ids: 文章ID列表
            
        Returns:
            包含成功数、失败数和失败ID的字典
        """
        success_count = 0
        failed_ids = []
        
        for article_id in article_ids:
            try:
                success = await self.delete_article(article_id)
                if success:
                    success_count += 1
                else:
                    failed_ids.append(article_id)
            except Exception as e:
                self.logger.error(f"删除文章失败 {article_id}: {e}")
                failed_ids.append(article_id)
        
        failed_count = len(failed_ids)
        
        self.logger.info(f"批量删除完成: 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids
        }

    async def close(self):
        """关闭HTTP客户端"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
