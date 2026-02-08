"""
Example usage of AI Gateway components.

This script demonstrates how to use the ConfigManager,
Logger, and database connections.
"""

import asyncio
from core import get_config_manager, get_logger, initialize_logger
from db.mongodb import get_mongodb_client
from db.redis import get_redis_client
from db.qdrant import get_qdrant_client


async def example_config_manager():
    """Example: ConfigManager usage."""
    print("\n=== ConfigManager Example ===")
    
    # Get config manager
    cm = get_config_manager()
    
    # Get values
    print(f"App host: {cm.get('app.host')}")
    print(f"App port: {cm.get('app.port')}")
    
    # Get virtual models
    vmodels = cm.get_virtual_models()
    print(f"Virtual models: {list(vmodels.keys())}")
    
    # Get specific model
    model = cm.get_virtual_model("demo1")
    if model:
        print(f"demo1 current model: {model.get('current')}")
    
    # Try to set value (allowed - changing existing key)
    success, error = cm.set("app.port", 8001)
    print(f"Set app.port: {success}")
    
    # Try to add key to fixed node (blocked)
    success, error = cm.set("app.new_field", "value")
    print(f"Add to fixed node: {success}, Error: {error}")


async def example_logger():
    """Example: Logger usage."""
    print("\n=== Logger Example ===")
    
    # Get logger
    logger = get_logger("example")
    
    # Log messages
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    print("Logged messages to MongoDB and file")


async def example_databases():
    """Example: Database connections."""
    print("\n=== Database Connections Example ===")
    
    # MongoDB
    try:
        mongo = await get_mongodb_client()
        healthy = await mongo.health_check()
        print(f"MongoDB health: {'healthy' if healthy else 'unhealthy'}")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    
    # Redis
    try:
        redis = await get_redis_client()
        healthy = await redis.health_check()
        print(f"Redis health: {'healthy' if healthy else 'unhealthy'}")
    except Exception as e:
        print(f"Redis connection failed: {e}")
    
    # Qdrant
    try:
        qdrant = get_qdrant_client()
        healthy = qdrant.health_check()
        print(f"Qdrant health: {'healthy' if healthy else 'unhealthy'}")
    except Exception as e:
        print(f"Qdrant connection failed: {e}")


async def main():
    """Main example runner."""
    print("AI Gateway Component Examples")
    print("=" * 50)
    
    try:
        # ConfigManager examples
        await example_config_manager()
        
        # Database examples
        await example_databases()
        
        # Logger examples (after MongoDB is connected)
        mongo = await get_mongodb_client()
        initialize_logger(mongodb_client=mongo)
        await example_logger()
        
    except Exception as e:
        print(f"Example failed: {e}")
    
    print("\n" + "=" * 50)
    print("Examples complete!")


if __name__ == "__main__":
    asyncio.run(main())
