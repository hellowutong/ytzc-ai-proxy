"""
Qdrant connection for vector database.

Features:
- Async connection
- Collection management
- Health check support
"""

import asyncio
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient as SyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from core.config_manager import get_config
from core.exceptions import QdrantConnectionError
from core.logger import get_logger

logger = get_logger("qdrant")


class QdrantClient:
    """Qdrant client wrapper for vector database operations."""
    
    _instance: Optional['QdrantClient'] = None
    _instance_lock = asyncio.Lock()
    
    def __new__(cls) -> 'QdrantClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[SyncQdrantClient] = None
        self._config: Optional[Dict[str, Any]] = None
    
    def connect(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to Qdrant with retry logic.
        
        Args:
            max_retries: Maximum number of connection retries
            retry_delay: Delay between retries in seconds
        """
        if self._client is not None:
            return
        
        # Load config
        self._config = get_config("storage.qdrant", {})
        
        host = self._config.get("host", "localhost")
        port = self._config.get("port", 6333)
        collection = self._config.get("collection", "knowledge_base")
        
        # Connect with retry
        import time
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Qdrant at {host}:{port} (attempt {attempt + 1}/{max_retries})")
                
                self._client = SyncQdrantClient(host=host, port=port)
                
                # Verify connection by getting collections
                self._client.get_collections()
                
                # Ensure collection exists
                self._ensure_collection(collection)
                
                logger.info("Qdrant connected successfully")
                return
                
            except Exception as e:
                logger.warning(f"Qdrant connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise QdrantConnectionError(f"Failed to connect to Qdrant after {max_retries} attempts: {e}")
    
    def _ensure_collection(self, collection_name: str):
        """Ensure collection exists, create if not."""
        if not self._client:
            return
        
        try:
            self._client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' exists")
        except UnexpectedResponse:
            # Collection doesn't exist, create it
            logger.info(f"Creating collection '{collection_name}'")
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info(f"Collection '{collection_name}' created")
    
    def disconnect(self):
        """Disconnect from Qdrant."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Qdrant disconnected")
    
    def health_check(self) -> bool:
        """Check if Qdrant connection is healthy."""
        if not self._client:
            return False
        
        try:
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    @property
    def client(self) -> Optional[SyncQdrantClient]:
        """Get Qdrant client."""
        return self._client
    
    def get_collection(self, collection_name: Optional[str] = None):
        """Get collection handle."""
        if not self._client:
            return None
        
        name = collection_name or self._config.get("collection", "knowledge_base")
        return name


# Global instance accessor
def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    client = QdrantClient()
    if client.client is None:
        client.connect()
    return client
