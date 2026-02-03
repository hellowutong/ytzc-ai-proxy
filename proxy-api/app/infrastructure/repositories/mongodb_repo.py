"""
MongoDB 仓储实现
"""
from typing import List, Optional, Dict
from datetime import datetime
from app.domain.repositories import SessionRepository, SkillRepository
from app.infrastructure.database.mongodb import (
    get_sessions_collection,
    get_skills_collection
)


class SessionRepositoryImpl(SessionRepository):
    """会话仓储MongoDB实现"""
    
    def __init__(self):
        self.collection = get_sessions_collection()
    
    async def create(self, session: Dict) -> str:
        """创建会话"""
        session["created_at"] = datetime.now().isoformat()
        session["updated_at"] = datetime.now().isoformat()
        result = await self.collection.insert_one(session)
        return str(result.inserted_id)
    
    async def get_by_id(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        return await self.collection.find_one({"session_id": session_id})
    
    async def list(
        self,
        proxy_key: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Dict], int]:
        """列出会话"""
        query = {}
        if proxy_key:
            query["proxy_key"] = proxy_key
        if status:
            query["status"] = status
        
        total = await self.collection.count_documents(query)
        skip = (page - 1) * limit
        
        cursor = self.collection.find(query).sort("created_at", -1)
        items = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        # 转换ObjectId
        for item in items:
            item["_id"] = str(item["_id"]) if item.get("_id") else None
        
        return items, total
    
    async def update(self, session_id: str, data: Dict) -> Optional[Dict]:
        """更新会话"""
        data["updated_at"] = datetime.now().isoformat()
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": data}
        )
        if result.modified_count > 0:
            return await self.get_by_id(session_id)
        return None
    
    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        result = await self.collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0
    
    async def batch_delete(self, session_ids: List[str]) -> int:
        """批量删除"""
        result = await self.collection.delete_many({
            "session_id": {"$in": session_ids}
        })
        return result.deleted_count
    
    async def add_message(self, session_id: str, message: Dict) -> Optional[Dict]:
        """添加消息"""
        message["timestamp"] = datetime.now().isoformat()
        result = await self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now().isoformat()}
            }
        )
        if result.modified_count > 0:
            return await self.get_by_id(session_id)
        return None
    
    async def end_session(self, session_id: str) -> Optional[Dict]:
        """结束会话"""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": "ended",
                    "ended_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        if result.modified_count > 0:
            return await self.get_by_id(session_id)
        return None


class SkillRepositoryImpl(SkillRepository):
    """Skill仓储MongoDB实现"""
    
    def __init__(self):
        self.collection = get_skills_collection()
    
    async def create(self, skill: Dict) -> str:
        """创建Skill"""
        skill["created_at"] = datetime.now().isoformat()
        skill["updated_at"] = datetime.now().isoformat()
        result = await self.collection.insert_one(skill)
        return str(result.inserted_id)
    
    async def get_by_id(self, base_id: str) -> Optional[Dict]:
        """获取Skill"""
        return await self.collection.find_one({"base_id": base_id})
    
    async def list(self, page: int = 1, limit: int = 20) -> tuple[List[Dict], int]:
        """列出Skill"""
        total = await self.collection.count_documents({})
        skip = (page - 1) * limit
        
        cursor = self.collection.find().sort("created_at", -1)
        items = await cursor.skip(skip).limit(limit).to_list(length=limit)
        
        for item in items:
            item["_id"] = str(item["_id"]) if item.get("_id") else None
        
        return items, total
    
    async def update(self, base_id: str, data: Dict) -> Optional[Dict]:
        """更新Skill"""
        data["updated_at"] = datetime.now().isoformat()
        result = await self.collection.update_one(
            {"base_id": base_id},
            {"$set": data}
        )
        if result.modified_count > 0:
            return await self.get_by_id(base_id)
        return None
    
    async def delete(self, base_id: str) -> bool:
        """删除Skill"""
        result = await self.collection.delete_one({"base_id": base_id})
        return result.deleted_count > 0
    
    async def create_version(self, base_id: str, version: Dict) -> int:
        """创建版本"""
        # 获取当前最大版本号
        skill = await self.get_by_id(base_id)
        if not skill:
            raise ValueError(f"Skill {base_id} not found")
        
        max_version = max([v["version_id"] for v in skill.get("versions", [])], default=-1)
        new_version_id = max_version + 1
        
        version["version_id"] = new_version_id
        version["created_at"] = datetime.now().isoformat()
        
        await self.collection.update_one(
            {"base_id": base_id},
            {
                "$push": {"versions": version},
                "$set": {"updated_at": datetime.now().isoformat()}
            }
        )
        
        return new_version_id
    
    async def get_version(self, base_id: str, version_id: int) -> Optional[Dict]:
        """获取版本"""
        skill = await self.get_by_id(base_id)
        if not skill:
            return None
        
        for v in skill.get("versions", []):
            if v["version_id"] == version_id:
                return v
        return None
    
    async def update_version(self, base_id: str, version_id: int, data: Dict) -> Optional[Dict]:
        """更新版本"""
        skill = await self.get_by_id(base_id)
        if not skill:
            return None
        
        for i, v in enumerate(skill["versions"]):
            if v["version_id"] == version_id:
                skill["versions"][i].update(data)
                await self.collection.update_one(
                    {"base_id": base_id},
                    {"$set": {"versions": skill["versions"]}}
                )
                return skill["versions"][i]
        return None
    
    async def delete_version(self, base_id: str, version_id: int) -> bool:
        """删除版本"""
        skill = await self.get_by_id(base_id)
        if not skill:
            return False
        
        versions = [v for v in skill["versions"] if v["version_id"] != version_id]
        if len(versions) == len(skill["versions"]):
            return False
        
        await self.collection.update_one(
            {"base_id": base_id},
            {"$set": {"versions": versions}}
        )
        return True
    
    async def publish_version(self, base_id: str, version_id: int) -> Optional[Dict]:
        """发布版本"""
        skill = await self.get_by_id(base_id)
        if not skill:
            return None
        
        # 更新所有版本状态
        for v in skill["versions"]:
            if v["version_id"] == version_id:
                v["status"] = "published"
            elif v["version_id"] != version_id:
                v["status"] = "deprecated"
        
        await self.collection.update_one(
            {"base_id": base_id},
            {
                "$set": {
                    "versions": skill["versions"],
                    "active_version_id": version_id,
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        
        return await self.get_by_id(base_id)
    
    async def rollback(self, base_id: str, version_id: int) -> Optional[Dict]:
        """回滚版本"""
        return await self.publish_version(base_id, version_id)
