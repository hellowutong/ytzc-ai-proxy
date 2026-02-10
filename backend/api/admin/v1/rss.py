"""
RSS订阅管理API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class RSSFeed(BaseModel):
    id: str
    name: str
    url: str
    enabled: bool
    update_interval: str
    article_count: int
    retention_days: int
    permanent: bool
    model: str


class RSSArticle(BaseModel):
    id: str
    feed_id: str
    title: str
    link: str
    published_at: str
    content: str
    fetch_status: str
    content_length: int


# Mock data
RSS_FEEDS = [
    {
        "id": "feed_001",
        "name": "技术新闻",
        "url": "https://tech.example.com/feed.xml",
        "enabled": True,
        "update_interval": "1h",
        "article_count": 156,
        "retention_days": 30,
        "permanent": False,
        "model": "demo1"
    },
    {
        "id": "feed_002",
        "name": "AI研究",
        "url": "https://ai.example.com/rss",
        "enabled": True,
        "update_interval": "6h",
        "article_count": 42,
        "retention_days": 90,
        "permanent": True,
        "model": "demo2"
    }
]

RSS_ARTICLES = [
    {
        "id": "article_001",
        "feed_id": "feed_001",
        "title": "新技术发布",
        "link": "https://tech.example.com/article/1",
        "published_at": "2025-01-09T10:00:00Z",
        "content": "这是一篇关于新技术发布的文章...",
        "fetch_status": "full",
        "content_length": 1500
    },
    {
        "id": "article_002",
        "feed_id": "feed_001",
        "title": "行业动态",
        "link": "https://tech.example.com/article/2",
        "published_at": "2025-01-09T09:00:00Z",
        "content": "行业最新动态...",
        "fetch_status": "summary",
        "content_length": 300
    }
]


@router.get("/rss/feeds")
async def get_feeds(
    page: int = 1,
    page_size: int = 20,
    enabled: Optional[bool] = None
):
    """获取RSS订阅列表"""
    result = RSS_FEEDS
    
    if enabled is not None:
        result = [f for f in result if f["enabled"] == enabled]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": result,
            "total": len(result),
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/rss/feeds")
async def create_feed(feed: dict):
    """创建RSS订阅"""
    import uuid
    
    new_feed = {
        "id": f"feed_{uuid.uuid4().hex[:8]}",
        **feed,
        "article_count": 0
    }
    
    RSS_FEEDS.append(new_feed)
    
    return {
        "code": 200,
        "message": "订阅创建成功",
        "data": new_feed
    }


@router.put("/rss/feeds/{feed_id}")
async def update_feed(feed_id: str, feed_data: dict):
    """更新RSS订阅"""
    for i, feed in enumerate(RSS_FEEDS):
        if feed["id"] == feed_id:
            RSS_FEEDS[i].update(feed_data)
            return {
                "code": 200,
                "message": "订阅更新成功",
                "data": RSS_FEEDS[i]
            }
    
    raise HTTPException(status_code=404, detail="订阅不存在")


@router.delete("/rss/feeds/{feed_id}")
async def delete_feed(feed_id: str):
    """删除RSS订阅"""
    global RSS_FEEDS
    
    original_len = len(RSS_FEEDS)
    RSS_FEEDS = [f for f in RSS_FEEDS if f["id"] != feed_id]
    
    if len(RSS_FEEDS) < original_len:
        return {
            "code": 200,
            "message": "订阅删除成功",
            "data": None
        }
    
    raise HTTPException(status_code=404, detail="订阅不存在")


@router.post("/rss/feeds/{feed_id}/fetch")
async def fetch_feed(feed_id: str):
    """立即抓取订阅"""
    return {
        "code": 200,
        "message": "抓取任务已提交",
        "data": None
    }


@router.get("/rss/articles")
async def get_articles(
    feed_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取文章列表"""
    result = RSS_ARTICLES
    
    if feed_id:
        result = [a for a in result if a["feed_id"] == feed_id]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": result,
            "total": len(result),
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/rss/import")
async def import_opml(file: UploadFile = File(...)):
    """导入OPML文件"""
    # TODO: Parse OPML and create feeds
    
    return {
        "code": 200,
        "message": "导入成功",
        "data": {"imported": 5}
    }
