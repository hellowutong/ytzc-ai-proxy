"""
API v1 package.
"""

from api.v1.endpoints.health import router as health_router
from api.v1.endpoints.logs import router as logs_router
from api.v1.endpoints.config import router as config_router
from api.v1.endpoints.dashboard import router as dashboard_router
from api.v1.endpoints.virtual_models import router as virtual_models_router
from api.v1.endpoints.chat import router as chat_router
from api.v1.endpoints.models import router as models_router
from api.v1.endpoints.knowledge import router as knowledge_router
from api.v1.endpoints.media import router as media_router
from api.v1.endpoints.rss import router as rss_router

__all__ = [
    "health_router",
    "logs_router",
    "config_router",
    "dashboard_router",
    "virtual_models_router",
    "chat_router",
    "models_router",
    "knowledge_router",
    "media_router",
    "rss_router"
]
