"""
API依赖注入模块
提供FastAPI依赖注入所需的各种管理器实例
"""

from fastapi import Request, HTTPException, Header
from typing import Optional

from core.config import ConfigManager
from core.database import DatabaseManager
from core.skill_manager import SkillManager
from core.model_router import ModelRouter
from core.conversation_manager import ConversationManager
from core.knowledge_manager import KnowledgeManager
from core.media_processor import MediaProcessor
from core.rss_fetcher import RSSFetcher
from core.skill_logger import SkillLogger
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.whisper_service import WhisperService
from services.search_service import SearchService


# 全局单例实例
_config_manager: Optional[ConfigManager] = None
_skill_manager: Optional[SkillManager] = None
_llm_service: Optional[LLMService] = None
_embedding_service: Optional[EmbeddingService] = None
_whisper_service: Optional[WhisperService] = None
_search_service: Optional[SearchService] = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.load_config()
    return _config_manager


def get_skill_manager() -> SkillManager:
    """获取Skill管理器单例"""
    global _skill_manager
    if _skill_manager is None:
        config_manager = get_config_manager()
        _skill_manager = SkillManager(config_manager)
    return _skill_manager


def get_mongodb(request: Request):
    """获取MongoDB连接"""
    return request.app.state.db_manager.mongodb


def get_redis(request: Request):
    """获取Redis连接"""
    return request.app.state.db_manager.redis


def get_qdrant(request: Request):
    """获取Qdrant连接"""
    return request.app.state.db_manager.qdrant


def get_conversation_manager(request: Request) -> ConversationManager:
    """获取对话管理器"""
    mongodb = get_mongodb(request)
    redis = get_redis(request)
    config_manager = get_config_manager()
    return ConversationManager(mongodb, redis, config_manager)


def get_knowledge_manager(request: Request) -> KnowledgeManager:
    """获取知识库管理器"""
    mongodb = get_mongodb(request)
    qdrant = get_qdrant(request)
    embedding_service = get_embedding_service()
    config_manager = get_config_manager()
    return KnowledgeManager(mongodb, qdrant, embedding_service, config_manager)


def get_media_processor(request: Request) -> MediaProcessor:
    """获取媒体处理器"""
    mongodb = get_mongodb(request)
    redis = get_redis(request)
    whisper_service = get_whisper_service()
    knowledge_manager = get_knowledge_manager(request)
    return MediaProcessor(mongodb, redis, whisper_service, knowledge_manager)


def get_rss_fetcher(request: Request) -> RSSFetcher:
    """获取RSS抓取器"""
    mongodb = get_mongodb(request)
    knowledge_manager = get_knowledge_manager(request)
    return RSSFetcher(mongodb, knowledge_manager)


def get_model_router(request: Request) -> ModelRouter:
    """获取模型路由引擎"""
    skill_manager = get_skill_manager()
    config_manager = get_config_manager()
    redis = get_redis(request)
    return ModelRouter(skill_manager, config_manager, redis)


def get_llm_service() -> LLMService:
    """获取LLM服务单例"""
    global _llm_service
    if _llm_service is None:
        config_manager = get_config_manager()
        _llm_service = LLMService(config_manager)
    return _llm_service


def get_embedding_service() -> EmbeddingService:
    """获取Embedding服务单例"""
    global _embedding_service
    if _embedding_service is None:
        config_manager = get_config_manager()
        _embedding_service = EmbeddingService(config_manager)
    return _embedding_service


def get_whisper_service() -> WhisperService:
    """获取Whisper服务单例"""
    global _whisper_service
    if _whisper_service is None:
        config_manager = get_config_manager()
        _whisper_service = WhisperService(config_manager)
    return _whisper_service


def get_search_service() -> SearchService:
    """获取搜索服务单例"""
    global _search_service
    if _search_service is None:
        config_manager = get_config_manager()
        _search_service = SearchService(config_manager)
    return _search_service


def get_skill_logger(request: Request) -> SkillLogger:
    """获取Skill日志记录器"""
    mongodb = get_mongodb(request)
    config_manager = get_config_manager()
    return SkillLogger(mongodb, config_manager)


async def verify_proxy_key(authorization: Optional[str] = Header(None)):
    """
    验证Proxy Key（用于/proxy/ai/*端点）
    
    Args:
        authorization: Authorization头，格式为 "Bearer {proxy_key}"
        
    Returns:
        dict: 虚拟模型配置
        
    Raises:
        HTTPException: 验证失败时抛出401错误
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少Authorization头")
    
    # 解析Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization格式错误，应为 'Bearer {proxy_key}'")
    
    proxy_key = parts[1]
    
    # 查找匹配的虚拟模型
    config_manager = get_config_manager()
    virtual_models = config_manager.get("ai-proxy.virtual_models", {})
    
    for model_name, model_config in virtual_models.items():
        if model_config.get("proxy_key") == proxy_key:
            if not model_config.get("use", True):
                raise HTTPException(status_code=403, detail=f"虚拟模型 {model_name} 已被禁用")
            
            return {
                "name": model_name,
                **model_config
            }
    
    raise HTTPException(status_code=401, detail="无效的proxy_key")
