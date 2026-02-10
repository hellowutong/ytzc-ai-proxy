"""
原始数据查看API
"""

from fastapi import APIRouter
from typing import Optional

router = APIRouter()


# Mock raw data
RAW_DATA = {
    "conversations": [
        {
            "_id": "conv_001",
            "model": "demo1",
            "messages": [
                {"role": "user", "content": "你好", "timestamp": "2025-01-09T10:00:00Z"},
                {"role": "assistant", "content": "你好！", "timestamp": "2025-01-09T10:00:05Z"}
            ],
            "metadata": {
                "client_ip": "127.0.0.1",
                "user_agent": "Mozilla/5.0"
            }
        },
        {
            "_id": "conv_002",
            "model": "demo2",
            "messages": [
                {"role": "user", "content": "讲个笑话", "timestamp": "2025-01-09T11:00:00Z"}
            ],
            "metadata": {
                "client_ip": "127.0.0.1",
                "user_agent": "Mozilla/5.0"
            }
        }
    ],
    "media": [
        {
            "_id": "media_001",
            "filename": "meeting.mp4",
            "type": "video",
            "path": "/upload/video/meeting.mp4",
            "metadata": {
                "duration": 3600,
                "resolution": "1920x1080"
            }
        },
        {
            "_id": "media_002",
            "filename": "interview.mp3",
            "type": "audio",
            "path": "/upload/audio/interview.mp3",
            "metadata": {
                "duration": 1800,
                "bitrate": "128kbps"
            }
        }
    ],
    "rss": [
        {
            "_id": "article_001",
            "feed_id": "feed_001",
            "title": "新技术发布",
            "raw_content": "<html><body>文章正文...</body></html>",
            "parsed_content": "文章正文...",
            "metadata": {
                "author": "Tech News",
                "category": "Technology"
            }
        }
    ]
}


@router.get("/raw-data/{data_type}")
async def get_raw_data(
    data_type: str,
    id: Optional[str] = None
):
    """获取原始数据"""
    if data_type not in RAW_DATA:
        return {
            "code": 400,
            "message": f"不支持的数据类型: {data_type}",
            "data": None
        }
    
    data = RAW_DATA[data_type]
    
    if id:
        item = next((d for d in data if d.get("_id") == id or d.get("id") == id), None)
        if item:
            return {
                "code": 200,
                "message": "success",
                "data": item
            }
        return {
            "code": 404,
            "message": "数据不存在",
            "data": None
        }
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": data,
            "total": len(data)
        }
    }


@router.get("/raw-data/stats")
async def get_raw_data_stats():
    """获取原始数据统计"""
    stats = {}
    
    for data_type, items in RAW_DATA.items():
        stats[data_type] = {
            "count": len(items),
            "size_estimate": sum(len(str(item)) for item in items)
        }
    
    return {
        "code": 200,
        "message": "success",
        "data": stats
    }
