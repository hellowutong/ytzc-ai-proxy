"""
RSS订阅管理API - 连接MongoDB实现
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ...dependencies import get_mongodb
from core.rss_fetcher import RSSFetcher

router = APIRouter()


class RSSFeedCreate(BaseModel):
    name: str
    url: str
    virtual_model: str = "demo1"
    fetch_interval: int = 30
    retention_days: int = 30
    auto_extract: bool = True


class RSSFeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    fetch_interval: Optional[int] = None
    retention_days: Optional[int] = None
    auto_extract: Optional[bool] = None


class MarkReadRequest(BaseModel):
    is_read: bool = True


# 热门订阅源预设数据
POPULAR_FEEDS = [
    {"name": "少数派", "url": "https://sspai.com/feed", "icon": "sspai", "subscribers": "31.5K"},
    {"name": "36氪", "url": "https://36kr.com/feed", "icon": "36kr", "subscribers": "12.5K"},
    {"name": "阮一峰的网络日志", "url": "https://ruanyifeng.com/blog/atom.xml", "icon": "ruanyf", "subscribers": "8.9K"},
    {"name": "知乎日报", "url": "https://zhihurss.miantiao.me/daily", "icon": "zhihu", "subscribers": "6.2K"},
    {"name": "GitHub Trending", "url": "https://github.com/trending/rss", "icon": "github", "subscribers": "5.8K"},
    {"name": "InfoQ", "url": "https://www.infoq.cn/feed", "icon": "infoq", "subscribers": "4.5K"},
    {"name": "稀土掘金", "url": "https://juejin.cn/rss", "icon": "juejin", "subscribers": "3.2K"},
    {"name": "V2EX", "url": "https://www.v2ex.com/feed/tab/tech", "icon": "v2ex", "subscribers": "2.1K"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "icon": "jiqizhixin", "subscribers": "1.8K"},
    {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "icon": "ifanr", "subscribers": "1.5K"}
]


def get_rss_fetcher(mongodb=Depends(get_mongodb)):
    """获取RSS Fetcher实例"""
    return RSSFetcher(mongodb)


@router.get("/rss/feeds")
async def get_feeds(
    page: int = 1,
    page_size: int = 20,
    enabled: Optional[bool] = None,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """获取RSS订阅列表"""
    try:
        offset = (page - 1) * page_size
        result = await fetcher.list_subscriptions(
            limit=page_size,
            offset=offset
        )
        
        # 如果有过滤条件，手动过滤
        subscriptions = result["subscriptions"]
        if enabled is not None:
            subscriptions = [s for s in subscriptions if s.get("enabled", True) == enabled]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": subscriptions,
                "total": result["total"],
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订阅列表失败: {str(e)}")


@router.post("/rss/feeds")
async def create_feed(
    feed: RSSFeedCreate,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """创建RSS订阅"""
    try:
        result = await fetcher.create_subscription(
            name=feed.name,
            url=feed.url,
            virtual_model=feed.virtual_model,
            fetch_interval=feed.fetch_interval,
            retention_days=feed.retention_days,
            auto_extract=feed.auto_extract
        )
        return {
            "code": 200,
            "message": "订阅创建成功",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建订阅失败: {str(e)}")


@router.put("/rss/feeds/{feed_id}")
async def update_feed(
    feed_id: str,
    feed_data: RSSFeedUpdate,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """更新RSS订阅"""
    try:
        updates = feed_data.dict(exclude_unset=True)
        success = await fetcher.update_subscription(feed_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="订阅不存在")
        
        # 获取更新后的订阅信息
        subscription = await fetcher.get_subscription(feed_id)
        
        return {
            "code": 200,
            "message": "订阅更新成功",
            "data": subscription
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新订阅失败: {str(e)}")


@router.delete("/rss/feeds/{feed_id}")
async def delete_feed(
    feed_id: str,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """删除RSS订阅"""
    try:
        success = await fetcher.delete_subscription(feed_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="订阅不存在")
        
        return {
            "code": 200,
            "message": "订阅删除成功",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除订阅失败: {str(e)}")


@router.post("/rss/feeds/{feed_id}/fetch")
async def fetch_feed(
    feed_id: str,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """立即抓取订阅"""
    try:
        result = await fetcher.fetch_feed(feed_id)
        return {
            "code": 200,
            "message": "抓取任务已完成",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")


@router.get("/rss/articles")
async def get_articles(
    feed_id: Optional[str] = None,
    is_read: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """获取文章列表"""
    try:
        offset = (page - 1) * page_size
        result = await fetcher.list_articles(
            subscription_id=feed_id,
            is_read=is_read,
            limit=page_size,
            offset=offset
        )
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": result["articles"],
                "total": result["total"],
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文章列表失败: {str(e)}")


@router.get("/rss/articles/{article_id}")
async def get_article(
    article_id: str,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """获取文章详情"""
    try:
        article = await fetcher.get_article(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        return {
            "code": 200,
            "message": "success",
            "data": article
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文章详情失败: {str(e)}")


@router.post("/rss/articles/{article_id}/read")
async def mark_article_read(
    article_id: str,
    request: MarkReadRequest,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """标记文章已读/未读"""
    try:
        success = await fetcher.mark_article_read(article_id, request.is_read)
        
        if not success:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        return {
            "code": 200,
            "message": "标记成功",
            "data": {"is_read": request.is_read}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记失败: {str(e)}")


# ⚠️ 注意：batch路由必须在/{article_id}路由之前定义
@router.delete("/rss/articles/batch")
async def delete_articles_batch(
    ids: str = Query(..., description="逗号分隔的文章ID列表"),
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """批量删除文章"""
    try:
        # 解析逗号分隔的ID列表
        article_ids = [aid.strip() for aid in ids.split(",") if aid.strip()]
        
        if not article_ids:
            raise HTTPException(status_code=400, detail="未提供有效的文章ID")
        
        result = await fetcher.delete_articles(article_ids)
        
        message = f"已删除 {result['success_count']} 篇文章"
        
        return {
            "code": 200,
            "message": message,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


@router.delete("/rss/articles/{article_id}")
async def delete_article(
    article_id: str,
    fetcher: RSSFetcher = Depends(get_rss_fetcher)
):
    """删除单篇文章"""
    try:
        success = await fetcher.delete_article(article_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        return {
            "code": 200,
            "message": "文章已删除",
            "data": {"article_id": article_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文章失败: {str(e)}")


@router.get("/rss/discover")
async def discover_feeds():
    """获取热门推荐订阅源（10个）"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": POPULAR_FEEDS,
            "total": len(POPULAR_FEEDS)
        }
    }
