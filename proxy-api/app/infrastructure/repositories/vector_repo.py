"""
向量仓储实现
"""
from typing import List, Dict
from app.domain.repositories import VectorRepository
from app.infrastructure.database.qdrant import Qdrant


class VectorRepositoryImpl(VectorRepository):
    """向量仓储Qdrant实现"""
    
    def __init__(self):
        self.qdrant = Qdrant
    
    async def search_sessions(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """搜索会话向量"""
        return await self.qdrant.search_sessions(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
    
    async def search_skills(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """搜索Skill向量"""
        return await self.qdrant.search_skills(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
    
    async def add_session_vector(
        self,
        session_id: str,
        proxy_key: str,
        summary: str,
        vector: List[float]
    ) -> str:
        """添加会话向量"""
        return await self.qdrant.add_session_vector(
            session_id=session_id,
            proxy_key=proxy_key,
            summary=summary,
            vector=vector
        )
    
    async def add_skill_vector(
        self,
        base_id: str,
        version_id: int,
        content: str,
        vector: List[float]
    ) -> str:
        """添加Skill向量"""
        return await self.qdrant.add_skill_vector(
            base_id=base_id,
            version_id=version_id,
            content=content,
            vector=vector
        )
    
    async def delete_session_vector(self, session_id: str) -> bool:
        """删除会话向量"""
        return await self.qdrant.delete_session_vector(session_id)
    
    async def delete_skill_vector(self, base_id: str, version_id: int) -> bool:
        """删除Skill向量"""
        return await self.qdrant.delete_skill_vector(base_id, version_id)
