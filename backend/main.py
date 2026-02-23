"""
AI Gateway - FastAPI后端入口
"""

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.proxy.v1 import chat, models as proxy_models, embeddings
from api.admin.v1 import (
    dashboard, config as admin_config, models as admin_models,
    skills, conversations, knowledge, media, rss, logs, raw_data
)
from core.config import ConfigManager
from core.database import DatabaseManager
from core.tasks.cleanup_task import RawDataCleanupTask


# 全局清理任务引用
cleanup_task = None


async def run_cleanup_task(db_manager, config_manager):
    """运行清理任务循环"""
    cleanup = RawDataCleanupTask(db_manager.mongodb, config_manager)
    
    while True:
        try:
            # 每天执行一次清理
            await asyncio.sleep(24 * 60 * 60)  # 24小时
            await cleanup.cleanup()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ 清理任务执行失败: {e}")
            await asyncio.sleep(60 * 60)  # 出错后1小时重试


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global cleanup_task
    
    # 启动时执行
    print("🚀 正在启动AI网关...")
    
    # 初始化配置
    config_manager = ConfigManager()
    config_manager.load_config()
    
    # 初始化数据库连接
    db_manager = DatabaseManager(config_manager)
    await db_manager.connect()
    
    # 存储到应用状态
    app.state.config_manager = config_manager
    app.state.db_manager = db_manager
    
    # 启动定时清理任务
    cleanup_task = asyncio.create_task(
        run_cleanup_task(db_manager, config_manager)
    )
    print("🧹 定时清理任务已启动（每24小时执行一次）")
    
    print("✅ AI网关启动完成！")
    
    yield
    
    # 关闭时执行
    print("🛑 正在关闭AI网关...")
    
    # 取消清理任务
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    
    await db_manager.disconnect()
    print("✅ AI网关已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AI Gateway",
    description="企业级AI网关系统 - 提供虚拟模型代理、模型路由、知识管理等功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本地部署，允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册代理API路由
app.include_router(chat.router, prefix="/proxy/ai/v1", tags=["proxy"])
app.include_router(proxy_models.router, prefix="/proxy/ai/v1", tags=["proxy"])
app.include_router(embeddings.router, prefix="/proxy/ai/v1", tags=["proxy"])

# 注册后台管理API路由
app.include_router(dashboard.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(admin_config.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(admin_models.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(skills.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(conversations.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(knowledge.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(media.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(rss.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(logs.router, prefix="/admin/ai/v1", tags=["admin"])
app.include_router(raw_data.router, prefix="/admin/ai/v1", tags=["admin"])


@app.get("/")
async def root():
    """根路径 - 服务信息"""
    return {
        "name": "AI Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "services": {
            "api": "up"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
