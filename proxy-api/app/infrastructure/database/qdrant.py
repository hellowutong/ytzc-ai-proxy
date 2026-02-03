"""
Qdrant 向量数据库连接模块
"""
from typing import Optional, List, Dict
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.core.config import get_config


class Qdrant:
    """Qdrant 向量数据库管理类"""
    
    client: Optional[AsyncQdrantClient] = None
    
    VECTOR_SIZE = 1024
    COLLECTION_SESSIONS = "sessions"
    COLLECTION_SKILLS = "skills"
    
    @classmethod
    async def connect(cls) -> None:
        """建立Qdrant连接"""
        config = get_config()
        
        cls.client = AsyncQdrantClient(
            url=f"http://{config.qdrant.host}:{config.qdrant.port}",
            check_compatibility=False
        )
        
        await cls._create_collections()
    
    @classmethod
    async def disconnect(cls) -> None:
        """断开Qdrant连接"""
        if cls.client:
            await cls.client.close()
            cls.client = None
    
    @classmethod
    async def _create_collections(cls) -> None:
        """创建必要的集合"""
        if cls.client is None:
            return
        
        try:
            await cls.client.create_collection(
                collection_name=cls.COLLECTION_SESSIONS,
                vectors_config=VectorParams(
                    size=cls.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
        except Exception:
            pass
        
        try:
            await cls.client.create_collection(
                collection_name=cls.COLLECTION_SKILLS,
                vectors_config=VectorParams(
                    size=cls.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
        except Exception:
            pass
    
    @classmethod
    async def search_sessions(
        cls,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """搜索会话向量"""
        if cls.client is None:
            return []
        
        results = await cls.client.search(
            collection_name=cls.COLLECTION_SESSIONS,
            query=query_vector,
            limit=limit
        )
        
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]
    
    @classmethod
    async def search_skills(
        cls,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """搜索Skill向量"""
        if cls.client is None:
            return []
        
        results = await cls.client.search(
            collection_name=cls.COLLECTION_SKILLS,
            query=query_vector,
            limit=limit
        )
        
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]
    
    @classmethod
    async def add_session_vector(
        cls,
        session_id: str,
        proxy_key: str,
        summary: str,
        vector: List[float]
    ) -> str:
        """添加会话向量"""
        if cls.client is None:
            return ""
        
        point_id = f"session_{session_id}"
        
        await cls.client.upsert(
            collection_name=cls.COLLECTION_SESSIONS,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "session_id": session_id,
                        "proxy_key": proxy_key,
                        "summary": summary
                    }
                )
            ]
        )
        
        return point_id
    
    @classmethod
    async def add_skill_vector(
        cls,
        base_id: str,
        version_id: int,
        content: str,
        vector: List[float]
    ) -> str:
        """添加Skill向量"""
        if cls.client is None:
            return ""
        
        point_id = f"skill_{base_id}_{version_id}"
        
        await cls.client.upsert(
            collection_name=cls.COLLECTION_SKILLS,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "base_id": base_id,
                        "version_id": version_id,
                        "content": content
                    }
                )
            ]
        )
        
        return point_id
    
    @classmethod
    async def delete_session_vector(cls, session_id: str) -> bool:
        """删除会话向量"""
        if cls.client is None:
            return False
        
        point_id = f"session_{session_id}"
        
        try:
            await cls.client.delete(
                collection_name=cls.COLLECTION_SESSIONS,
                points_selector=[point_id]
            )
            return True
        except Exception:
            return False
    
    @classmethod
    async def delete_skill_vector(cls, base_id: str, version_id: int) -> bool:
        """删除Skill向量"""
        if cls.client is None:
            return False
        
        point_id = f"skill_{base_id}_{version_id}"
        
        try:
            await cls.client.delete(
                collection_name=cls.COLLECTION_SKILLS,
                points_selector=[point_id]
            )
            return True
        except Exception:
            return False
    
    @classmethod
    async def get_collections(cls) -> List[str]:
        """获取所有集合"""
        if cls.client is None:
            return []
        
        try:
            collections = await cls.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception:
            return []


async def get_qdrant() -> Qdrant:
    """获取Qdrant实例"""
    return Qdrant
