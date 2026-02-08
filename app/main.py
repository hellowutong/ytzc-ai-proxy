"""
AI Gateway FastAPI Application Entry Point.

This is the main entry point for the FastAPI application.
It initializes all components including:
- Configuration Manager with hot reload
- Dual logging system (MongoDB + file)
- Database connections (MongoDB, Redis, Qdrant)
- API routes and middleware
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core import (
    get_config_manager,
    initialize_logger,
    shutdown_logger,
    setup_middleware,
    get_logger,
)
from db.mongodb import get_mongodb_client
from db.redis import get_redis_client
from db.qdrant import get_qdrant_client
from api.v1 import health_router, logs_router, config_router, dashboard_router, virtual_models_router, chat_router, models_router, knowledge_router, media_router, rss_router

# Get logger
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up AI Gateway...")
    
    try:
        # Initialize ConfigManager
        config_path = os.getenv("CONFIG_PATH", "config.yml")
        config_manager = get_config_manager(config_path, enable_watch=False)
        logger.info(f"Configuration loaded from {config_path}")
        
        # Get log configuration
        log_config = config_manager.get_log_config("system")
        log_level = log_config.get("level", "INFO")
        log_path = log_config.get("storage", {}).get("path", "./logs")
        
        # Connect to MongoDB first (needed for logging)
        mongo_client = await get_mongodb_client()
        logger.info("MongoDB connection established")
        
        # Initialize logger with MongoDB
        initialize_logger(
            mongodb_client=mongo_client,
            log_dir=log_path,
            system_level=log_level,
            operation_level="INFO"
        )
        logger.info("Dual logging system initialized")
        
        # Connect to Redis
        redis_client = await get_redis_client()
        logger.info("Redis connection established")
        
        # Connect to Qdrant
        qdrant_client = get_qdrant_client()
        logger.info("Qdrant connection established")
        
        logger.info("AI Gateway startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Gateway...")
    
    try:
        # Disconnect from databases
        mongo_client = MongoDBClient()
        await mongo_client.disconnect()
        logger.info("MongoDB disconnected")
        
        redis_client = RedisClient()
        await redis_client.disconnect()
        logger.info("Redis disconnected")
        
        qdrant_client = QdrantClient()
        qdrant_client.disconnect()
        logger.info("Qdrant disconnected")
        
        # Shutdown logger
        shutdown_logger()
        
        # Shutdown ConfigManager
        config_manager = get_config_manager()
        config_manager.shutdown()
        
        logger.info("AI Gateway shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI Gateway",
    description="AI Gateway with Template Pattern Configuration Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/proxy/admin")
app.include_router(config_router, prefix="/proxy/admin")
app.include_router(dashboard_router, prefix="/proxy/admin")
app.include_router(virtual_models_router, prefix="/proxy/admin")
app.include_router(knowledge_router, prefix="/proxy/admin")
app.include_router(media_router, prefix="/proxy/admin")
app.include_router(rss_router, prefix="/proxy/admin")
app.include_router(chat_router, prefix="/proxy/api/v1")
app.include_router(models_router, prefix="/proxy/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/config")
async def get_current_config():
    """Get current configuration (for admin purposes)."""
    from core import get_config_manager
    config_manager = get_config_manager()
    return config_manager.config


# Import at end to avoid circular imports
from db.mongodb import MongoDBClient
from db.redis import RedisClient
from db.qdrant import QdrantClient


if __name__ == "__main__":
    import uvicorn
    
    # Get app config
    config_manager = get_config_manager()
    app_config = config_manager.get_app_config()
    
    host = app_config.get("host", "0.0.0.0")
    port = app_config.get("port", 8000)
    debug = app_config.get("debug", False)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
