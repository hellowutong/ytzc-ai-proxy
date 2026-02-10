"""
对话管理器 - 对话的创建、查询、保存、删除
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
import uuid


logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息模型"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """对话模型"""
    id: str
    virtual_model: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    has_knowledge_reference: bool = False


class ConversationManager:
    """对话管理器"""
    
    def __init__(self, mongodb_client, redis_client=None, config_manager=None):
        """
        初始化对话管理器
        
        Args:
            mongodb_client: MongoDB客户端实例
            redis_client: Redis客户端实例（可选）
            config_manager: 配置管理器实例（可选）
        """
        self._mongodb = mongodb_client
        self._redis = redis_client
        self._config_manager = config_manager
        
        # 获取数据库和集合
        if config_manager:
            db_name = config_manager.get('storage.mongodb.database', 'ai_gateway')
        else:
            db_name = 'ai_gateway'
        
        self._db = self._mongodb[db_name]
        self._collection = self._db["conversations"]
    
    def _generate_uuid(self) -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    async def create_conversation(self, virtual_model: str) -> str:
        """
        创建新会话
        
        Args:
            virtual_model: 虚拟模型名称
            
        Returns:
            str: 新创建的会话ID
        """
        try:
            conversation_id = self._generate_uuid()
            now = datetime.utcnow()
            
            doc = {
                "_id": conversation_id,
                "virtual_model": virtual_model,
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
                "has_knowledge_reference": False
            }
            
            await self._collection.insert_one(doc)
            logger.info(f"创建会话成功: {conversation_id}, 虚拟模型: {virtual_model}")
            
            # 同时在Redis中创建会话缓存
            if self._redis:
                cache_key = f"conversation:{conversation_id}:messages"
                await self._redis.setex(cache_key, 3600, "[]")  # 1小时过期
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
    
    async def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加消息到会话
        
        Args:
            conversation_id: 会话ID
            role: 消息角色 ("user", "assistant", "system")
            content: 消息内容
            metadata: 元数据（可选）
            
        Returns:
            bool: 是否成功
        """
        try:
            now = datetime.utcnow()
            message = {
                "role": role,
                "content": content,
                "timestamp": now,
                "metadata": metadata or {}
            }
            
            # 更新MongoDB
            result = await self._collection.update_one(
                {"_id": conversation_id},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": now},
                    "$inc": {"message_count": 1}
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"添加消息失败，会话不存在: {conversation_id}")
                return False
            
            # 更新Redis缓存
            if self._redis:
                await self._update_redis_cache(conversation_id, message)
            
            # 检查是否有知识引用
            if metadata and metadata.get("knowledge_references"):
                await self._collection.update_one(
                    {"_id": conversation_id},
                    {"$set": {"has_knowledge_reference": True}}
                )
            
            logger.debug(f"添加消息成功: {conversation_id}, role={role}")
            return True
            
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return False
    
    async def _update_redis_cache(self, conversation_id: str, message: Dict):
        """更新Redis缓存"""
        try:
            import json
            cache_key = f"conversation:{conversation_id}:messages"
            
            # 获取现有缓存
            existing = await self._redis.get(cache_key)
            if existing:
                messages = json.loads(existing)
            else:
                messages = []
            
            # 添加新消息
            messages.append(message)
            
            # 只保留最近20条消息
            if len(messages) > 20:
                messages = messages[-20:]
            
            # 更新缓存，重置过期时间
            await self._redis.setex(cache_key, 3600, json.dumps(messages))
            
        except Exception as e:
            logger.warning(f"更新Redis缓存失败: {e}")
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        获取会话详情
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            Optional[Conversation]: 会话对象，不存在时返回None
        """
        try:
            doc = await self._collection.find_one({"_id": conversation_id})
            
            if not doc:
                return None
            
            # 转换消息格式
            messages = []
            for msg_data in doc.get("messages", []):
                messages.append(Message(
                    role=msg_data.get("role", ""),
                    content=msg_data.get("content", ""),
                    timestamp=msg_data.get("timestamp", datetime.utcnow()),
                    metadata=msg_data.get("metadata", {})
                ))
            
            return Conversation(
                id=doc["_id"],
                virtual_model=doc.get("virtual_model", ""),
                messages=messages,
                created_at=doc.get("created_at", datetime.utcnow()),
                updated_at=doc.get("updated_at", datetime.utcnow()),
                message_count=doc.get("message_count", 0),
                has_knowledge_reference=doc.get("has_knowledge_reference", False)
            )
            
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    async def list_conversations(
        self,
        virtual_model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        keyword: Optional[str] = None,
        has_knowledge: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Conversation], int]:
        """
        列表查询（支持筛选、分页）
        
        Args:
            virtual_model: 虚拟模型名称筛选
            start_time: 开始时间筛选
            end_time: 结束时间筛选
            keyword: 关键词搜索（搜索消息内容）
            has_knowledge: 是否包含知识引用筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            Tuple[List[Conversation], int]: (会话列表, 总数)
        """
        try:
            # 构建查询条件
            query = {}
            
            if virtual_model:
                query["virtual_model"] = virtual_model
            
            if start_time or end_time:
                query["updated_at"] = {}
                if start_time:
                    query["updated_at"]["$gte"] = start_time
                if end_time:
                    query["updated_at"]["$lte"] = end_time
            
            if has_knowledge is not None:
                query["has_knowledge_reference"] = has_knowledge
            
            if keyword:
                # 使用文本搜索
                query["$text"] = {"$search": keyword}
            
            # 查询数据
            cursor = self._collection.find(query) \
                .sort("updated_at", -1) \
                .skip(offset) \
                .limit(limit)
            
            conversations = []
            async for doc in cursor:
                conversations.append(Conversation(
                    id=doc["_id"],
                    virtual_model=doc.get("virtual_model", ""),
                    messages=[],  # 列表查询不返回消息详情
                    created_at=doc.get("created_at", datetime.utcnow()),
                    updated_at=doc.get("updated_at", datetime.utcnow()),
                    message_count=doc.get("message_count", 0),
                    has_knowledge_reference=doc.get("has_knowledge_reference", False)
                ))
            
            # 获取总数
            total = await self._collection.count_documents(query)
            
            return conversations, total
            
        except Exception as e:
            logger.error(f"查询会话列表失败: {e}")
            return [], 0
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除会话
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        try:
            result = await self._collection.delete_one({"_id": conversation_id})
            
            if result.deleted_count > 0:
                # 同时删除Redis缓存
                if self._redis:
                    cache_key = f"conversation:{conversation_id}:messages"
                    await self._redis.delete(cache_key)
                
                logger.info(f"删除会话成功: {conversation_id}")
                return True
            else:
                logger.warning(f"删除会话失败，会话不存在: {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    async def update_conversation_metadata(
        self, 
        conversation_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        更新会话元数据
        
        Args:
            conversation_id: 会话ID
            metadata: 元数据字典
            
        Returns:
            bool: 是否成功
        """
        try:
            result = await self._collection.update_one(
                {"_id": conversation_id},
                {
                    "$set": {
                        "metadata": metadata,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新会话元数据失败: {e}")
            return False
    
    async def get_recent_messages(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """
        获取最近的N条消息
        
        Args:
            conversation_id: 会话ID
            limit: 消息数量限制
            
        Returns:
            List[Message]: 消息列表
        """
        try:
            # 先从Redis获取
            if self._redis:
                cache_key = f"conversation:{conversation_id}:messages"
                cached = await self._redis.get(cache_key)
                if cached:
                    import json
                    messages_data = json.loads(cached)
                    messages = []
                    for msg_data in messages_data[-limit:]:
                        messages.append(Message(
                            role=msg_data.get("role", ""),
                            content=msg_data.get("content", ""),
                            timestamp=datetime.fromisoformat(msg_data.get("timestamp", "")) 
                                if isinstance(msg_data.get("timestamp"), str) 
                                else datetime.utcnow(),
                            metadata=msg_data.get("metadata", {})
                        ))
                    return messages
            
            # 从MongoDB获取
            conversation = await self.get_conversation(conversation_id)
            if conversation:
                return conversation.messages[-limit:] if conversation.messages else []
            
            return []
            
        except Exception as e:
            logger.error(f"获取最近消息失败: {e}")
            return []
