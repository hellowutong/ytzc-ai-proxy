"""
领域模型 - Skill 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class SkillStatus(str, Enum):
    """Skill 状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class SkillVersion(BaseModel):
    """Skill 版本模型"""
    version_id: int = Field(..., description="版本号")
    status: SkillStatus = Field(default=SkillStatus.DRAFT, description="状态")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="创建时间")
    created_by: str = Field(default="system", description="创建者: system/user")
    source_session_id: Optional[str] = Field(None, description="来源会话 ID")
    change_reason: Optional[str] = Field(None, description="变更原因")


class Skill(BaseModel):
    """Skill 模型"""
    base_id: str = Field(..., description="Skill 唯一标识")
    active_version_id: int = Field(default=0, description="当前活动版本号")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="创建时间")
    versions: List[SkillVersion] = Field(default_factory=list, description="版本列表")
    
    def add_version(self, version: SkillVersion):
        """添加版本"""
        self.versions.append(version)
    
    def get_version(self, version_id: int) -> Optional[SkillVersion]:
        """获取指定版本"""
        for v in self.versions:
            if v.version_id == version_id:
                return v
        return None
    
    def publish_version(self, version_id: int):
        """发布版本"""
        # 将所有版本标记为 deprecated
        for v in self.versions:
            if v.status == SkillStatus.PUBLISHED:
                v.status = SkillStatus.DEPRECATED
        
        # 找到目标版本并发布
        for v in self.versions:
            if v.version_id == version_id:
                v.status = SkillStatus.PUBLISHED
                self.active_version_id = version_id
                break
    
    def rollback(self, version_id: int) -> bool:
        """回滚到指定版本"""
        target_version = self.get_version(version_id)
        if target_version and target_version.status == SkillStatus.DRAFT:
            self.publish_version(version_id)
            return True
        return False


class SkillCreate(BaseModel):
    """创建 Skill 请求"""
    source_session_id: Optional[str] = None
    change_reason: Optional[str] = "initial"


class SkillFile(BaseModel):
    """Skill 文件模型"""
    base_id: str
    version_id: int
    skill_md: str
    examples: List[str] = Field(default_factory=list)
    assets: List[str] = Field(default_factory=list)
