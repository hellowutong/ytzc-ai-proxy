"""
仓储层 - 领域接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class SessionRepository(ABC):
    """会话仓储接口"""
    
    @abstractmethod
    async def create(self, session: Dict) -> str:
        """创建会话"""
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def list(
        self,
        proxy_key: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Dict], int]:
        """列出会话"""
        pass
    
    @abstractmethod
    async def update(self, session_id: str, data: Dict) -> Optional[Dict]:
        """更新会话"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    async def batch_delete(self, session_ids: List[str]) -> int:
        """批量删除"""
        pass
    
    @abstractmethod
    async def add_message(self, session_id: str, message: Dict) -> Optional[Dict]:
        """添加消息"""
        pass
    
    @abstractmethod
    async def end_session(self, session_id: str) -> Optional[Dict]:
        """结束会话"""
        pass


class SkillRepository(ABC):
    """Skill仓储接口"""
    
    @abstractmethod
    async def create(self, skill: Dict) -> str:
        """创建Skill"""
        pass
    
    @abstractmethod
    async def get_by_id(self, base_id: str) -> Optional[Dict]:
        """获取Skill"""
        pass
    
    @abstractmethod
    async def list(self, page: int = 1, limit: int = 20) -> tuple[List[Dict], int]:
        """列出Skill"""
        pass
    
    @abstractmethod
    async def update(self, base_id: str, data: Dict) -> Optional[Dict]:
        """更新Skill"""
        pass
    
    @abstractmethod
    async def delete(self, base_id: str) -> bool:
        """删除Skill"""
        pass
    
    @abstractmethod
    async def create_version(self, base_id: str, version: Dict) -> int:
        """创建版本"""
        pass
    
    @abstractmethod
    async def get_version(self, base_id: str, version_id: int) -> Optional[Dict]:
        """获取版本"""
        pass
    
    @abstractmethod
    async def update_version(self, base_id: str, version_id: int, data: Dict) -> Optional[Dict]:
        """更新版本"""
        pass
    
    @abstractmethod
    async def delete_version(self, base_id: str, version_id: int) -> bool:
        """删除版本"""
        pass
    
    @abstractmethod
    async def publish_version(self, base_id: str, version_id: int) -> Optional[Dict]:
        """发布版本"""
        pass
    
    @abstractmethod
    async def rollback(self, base_id: str, version_id: int) -> Optional[Dict]:
        """回滚版本"""
        pass


class VectorRepository(ABC):
    """向量仓储接口"""
    
    @abstractmethod
    async def search_sessions(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """搜索会话向量"""
        pass
    
    @abstractmethod
    async def search_skills(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """搜索Skill向量"""
        pass
    
    @abstractmethod
    async def add_session_vector(
        self,
        session_id: str,
        proxy_key: str,
        summary: str,
        vector: List[float]
    ) -> str:
        """添加会话向量"""
        pass
    
    @abstractmethod
    async def add_skill_vector(
        self,
        base_id: str,
        version_id: int,
        content: str,
        vector: List[float]
    ) -> str:
        """添加Skill向量"""
        pass
    
    @abstractmethod
    async def delete_session_vector(self, session_id: str) -> bool:
        """删除会话向量"""
        pass
    
    @abstractmethod
    async def delete_skill_vector(self, base_id: str, version_id: int) -> bool:
        """删除Skill向量"""
        pass
