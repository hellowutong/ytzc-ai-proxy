"""
后台管理API - 看板
"""

import time
import yaml
from fastapi import APIRouter, Request
import httpx

router = APIRouter()

# 加载配置文件
def load_config():
    """加载 config.yml 配置"""
    import os
    # 尝试多个路径
    possible_paths = [
        '../config.yml',
        '/app/config.yml',
        '../../config.yml',
        'config.yml',
        os.path.join(os.path.dirname(__file__), '../../../../config.yml'),
        os.path.join(os.path.dirname(__file__), '../../../config.yml'),
    ]
    
    for path in possible_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    print(f"成功加载配置文件: {path}")
                    return config
        except Exception as e:
            continue
    
    print("警告: 无法加载配置文件，使用空配置")
    return {}


@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """获取看板统计数据"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "virtual_models": 5,
            "today_conversations": 128,
            "knowledge_docs": 1024,
            "media_queue": 5,
            "rss_feeds": 10,
            "system_status": "healthy"
        }
    }


@router.get("/dashboard/activities")
async def get_dashboard_activities():
    """获取最近活动"""
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": "1",
                "timestamp": "2026-02-09T14:30:00Z",
                "type": "config",
                "action": "配置重载",
                "status": "success"
            },
            {
                "id": "2", 
                "timestamp": "2026-02-09T14:25:00Z",
                "type": "skill",
                "action": "Skill重载",
                "status": "success"
            },
            {
                "id": "3",
                "timestamp": "2026-02-09T14:20:00Z",
                "type": "model",
                "action": "模型切换",
                "status": "success"
            }
        ]
    }


@router.get("/dashboard/dependencies")
async def get_dependencies_status(request: Request):
    """获取第三方依赖状态"""
    dependencies = []
    
    # Check MongoDB
    try:
        start = time.time()
        db_manager = request.app.state.db_manager
        await db_manager.mongodb.admin.command('ping')
        latency = int((time.time() - start) * 1000)
        dependencies.append({
            "name": "MongoDB",
            "icon": "Coin",
            "color": "#4ec9b0",
            "status": "healthy",
            "statusText": "正常",
            "detail": "已连接",
            "latency": latency
        })
    except Exception as e:
        dependencies.append({
            "name": "MongoDB",
            "icon": "Coin", 
            "color": "#4ec9b0",
            "status": "unhealthy",
            "statusText": "异常",
            "detail": str(e),
            "latency": None
        })
    
    # Check Redis
    try:
        start = time.time()
        db_manager = request.app.state.db_manager
        await db_manager.redis.ping()
        latency = int((time.time() - start) * 1000)
        dependencies.append({
            "name": "Redis",
            "icon": "DataLine",
            "color": "#ce9178", 
            "status": "healthy",
            "statusText": "正常",
            "detail": "已连接",
            "latency": latency
        })
    except Exception as e:
        dependencies.append({
            "name": "Redis",
            "icon": "DataLine",
            "color": "#ce9178",
            "status": "unhealthy", 
            "statusText": "异常",
            "detail": str(e),
            "latency": None
        })
    
    # Check Qdrant
    try:
        start = time.time()
        db_manager = request.app.state.db_manager
        db_manager.qdrant.get_collections()
        latency = int((time.time() - start) * 1000)
        dependencies.append({
            "name": "Qdrant",
            "icon": "Grid",
            "color": "#c586c0",
            "status": "healthy",
            "statusText": "正常", 
            "detail": "已连接",
            "latency": latency
        })
    except Exception as e:
        dependencies.append({
            "name": "Qdrant",
            "icon": "Grid",
            "color": "#c586c0",
            "status": "unhealthy",
            "statusText": "异常",
            "detail": str(e),
            "latency": None
        })
    
    # Check SearXNG
    try:
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get("http://searxng:8080/healthz", timeout=5.0)
            latency = int((time.time() - start) * 1000)
            if response.status_code == 200:
                dependencies.append({
                    "name": "SearXNG",
                    "icon": "Search",
                    "color": "#dcdcaa",
                    "status": "healthy",
                    "statusText": "正常",
                    "detail": "搜索引擎就绪",
                    "latency": latency
                })
            else:
                dependencies.append({
                    "name": "SearXNG",
                    "icon": "Search",
                    "color": "#dcdcaa",
                    "status": "warning",
                    "statusText": "警告",
                    "detail": f"HTTP {response.status_code}",
                    "latency": latency
                })
    except Exception as e:
        dependencies.append({
            "name": "SearXNG",
            "icon": "Search",
            "color": "#dcdcaa",
            "status": "unhealthy",
            "statusText": "异常",
            "detail": "服务不可用",
            "latency": None
        })
    
    # ========== 检查其他 web_search 服务 (LibreX, 4get) ==========
    config = load_config()
    web_search_config = config.get('web_search', {})
    
    web_search_services = {
        'searxng': {
            'icon': 'Search',
            'color': '#dcdcaa',
            'default_url': 'http://searxng:8080',
            'health_endpoint': '/healthz'
        },
        'LibreX': {
            'icon': 'Search',
            'color': '#ce9178',
            'default_url': 'http://librex:80',
            'health_endpoint': '/'
        },
        '4get': {
            'icon': 'Search',
            'color': '#569cd6',
            'default_url': 'http://4get:80',
            'health_endpoint': '/'
        }
    }
    
    # 检查配置中的其他 web_search 服务
    for service_name in web_search_config.keys():
        if service_name in web_search_services and service_name != 'searxng':
            service_info = web_search_services[service_name]
            try:
                start = time.time()
                health_url = f"{service_info['default_url']}{service_info['health_endpoint']}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_url, timeout=5.0)
                    latency = int((time.time() - start) * 1000)
                    
                    if response.status_code == 200:
                        dependencies.append({
                            "name": service_name,
                            "icon": service_info['icon'],
                            "color": service_info['color'],
                            "status": "healthy",
                            "statusText": "正常",
                            "detail": "搜索引擎就绪",
                            "latency": latency
                        })
                    else:
                        dependencies.append({
                            "name": service_name,
                            "icon": service_info['icon'],
                            "color": service_info['color'],
                            "status": "warning",
                            "statusText": "警告",
                            "detail": f"HTTP {response.status_code}",
                            "latency": latency
                        })
            except Exception as e:
                dependencies.append({
                    "name": service_name,
                    "icon": service_info['icon'],
                    "color": service_info['color'],
                    "status": "unhealthy",
                    "statusText": "异常",
                    "detail": "服务不可用",
                    "latency": None
                })
    
    return {
        "code": 200,
        "message": "success",
        "data": dependencies
    }
