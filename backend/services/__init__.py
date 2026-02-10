"""
服务层 - 外部API调用封装
"""

from .llm_service import (
    LLMService,
    LLMServiceFactory,
    LLMError,
    create_siliconflow_service,
    create_openai_service,
    create_ollama_service,
)

from .embedding_service import (
    EmbeddingService,
    EmbeddingServiceFactory,
    EmbeddingError,
    create_siliconflow_embedding_service,
    create_openai_embedding_service,
    create_ollama_embedding_service,
)

from .whisper_service import (
    WhisperService,
    WhisperServiceFactory,
    WhisperError,
    create_local_whisper_service,
    create_api_whisper_service,
)

from .search_service import (
    SearchService,
    SearchServiceFactory,
    SearchError,
    create_searxng_service,
    create_librex_service,
    create_4get_service,
)

__all__ = [
    # LLM Service
    "LLMService",
    "LLMServiceFactory",
    "LLMError",
    "create_siliconflow_service",
    "create_openai_service",
    "create_ollama_service",
    # Embedding Service
    "EmbeddingService",
    "EmbeddingServiceFactory",
    "EmbeddingError",
    "create_siliconflow_embedding_service",
    "create_openai_embedding_service",
    "create_ollama_embedding_service",
    # Whisper Service
    "WhisperService",
    "WhisperServiceFactory",
    "WhisperError",
    "create_local_whisper_service",
    "create_api_whisper_service",
    # Search Service
    "SearchService",
    "SearchServiceFactory",
    "SearchError",
    "create_searxng_service",
    "create_librex_service",
    "create_4get_service",
]
