# 修复ChatBox多轮对话问题

## 问题根因深度分析

通过日志分析发现：

1. **ChatBox不会发送conversation_id** - 标准OpenAI API客户端行为
2. **但ChatBox会发送完整messages数组** - 包含所有历史消息
3. **后端每次创建新对话** - 因为没有conversation_id就新建

### 对比WebChat和ChatBox

**WebChat**: 
- 第一轮：创建新对话，后端返回conversation_id
- 第二轮：WebChat将conversation_id存储在本地，后续请求携带它
- 结果：多轮对话在同一对话记录中

**ChatBox**:
- 第一轮：创建新对话，后端返回conversation_id
- 第二轮：ChatBox**不存储**conversation_id，只通过messages数组维护上下文
- 结果：每轮对话都创建新对话记录

## 解决方案

基于消息内容生成**确定性对话指纹**，实现对话连续性识别。

### 实现方案

**修改文件**: `backend/api/proxy/v1/chat.py`

在获取conversation_id后，添加指纹匹配逻辑：

```python
# 2. 通过消息指纹查找或创建对话
import hashlib
import json

async def get_or_create_conversation_by_fingerprint(
    messages, 
    virtual_model_name, 
    conversation_manager,
    conversation_id_from_request
):
    """
    通过消息指纹获取或创建对话
    
    策略：
    1. 如果请求中包含conversation_id，优先使用
    2. 否则基于前两条消息生成指纹，查找现有对话
    3. 如果找不到，创建新对话
    """
    
    # 优先使用请求中的conversation_id
    if conversation_id_from_request:
        existing = await conversation_manager.get_conversation(conversation_id_from_request)
        if existing:
            return conversation_id_from_request
    
    # 生成消息指纹（基于前2条用户消息）
    user_messages = [msg for msg in messages if msg.get('role') == 'user'][:2]
    if not user_messages:
        # 没有用户消息，创建新对话
        return await conversation_manager.create_conversation(virtual_model_name)
    
    # 生成确定性指纹
    fingerprint_data = json.dumps(user_messages, sort_keys=True, ensure_ascii=False)
    fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    # 查找是否有相同指纹的活跃对话（30分钟内）
    conversation_id = await conversation_manager.find_by_fingerprint(
        fingerprint, 
        virtual_model_name,
        ttl_minutes=30
    )
    
    if conversation_id:
        return conversation_id
    
    # 创建新对话并保存指纹
    conversation_id = await conversation_manager.create_conversation(virtual_model_name)
    await conversation_manager.save_fingerprint(conversation_id, fingerprint)
    
    return conversation_id
```

**修改文件**: `backend/core/conversation_manager.py`

添加指纹相关方法：

```python
async def find_by_fingerprint(self, fingerprint: str, virtual_model: str, ttl_minutes: int = 30) -> Optional[str]:
    """通过指纹查找对话"""
    if not self._redis:
        return None
    
    cache_key = f"conversation:fingerprint:{fingerprint}"
    conversation_id = await self._redis.get(cache_key)
    
    if conversation_id:
        # 验证对话是否仍然存在且属于同一模型
        conv = await self.get_conversation(conversation_id)
        if conv and conv.virtual_model == virtual_model:
            return conversation_id
    
    return None

async def save_fingerprint(self, conversation_id: str, fingerprint: str, ttl_minutes: int = 30):
    """保存对话指纹"""
    if self._redis:
        cache_key = f"conversation:fingerprint:{fingerprint}"
        await self._redis.setex(cache_key, ttl_minutes * 60, conversation_id)
```

## 简化方案

考虑到Redis可能不可用，使用更简单的方案：

**基于第一条用户消息查找最近创建的相似对话**：

```python
# 在chat.py中添加
async def find_existing_conversation(messages, virtual_model, conversation_manager):
    """
    通过第一条用户消息查找现有对话
    """
    # 获取第一条用户消息
    first_user_msg = None
    for msg in messages:
        if msg.get('role') == 'user':
            first_user_msg = msg.get('content', '')
            break
    
    if not first_user_msg or len(first_user_msg) < 5:
        return None
    
    # 查找最近30分钟内创建的、包含相同首条消息的对话
    # 这需要添加新方法到conversation_manager
    return await conversation_manager.find_recent_by_first_message(
        first_user_msg[:100],  # 取前100字符
        virtual_model,
        minutes=30
    )
```

## 推荐实施方案

**方案：客户端类型识别 + 消息指纹**

1. **识别客户端类型**（通过User-Agent）
2. **对于ChatBox类客户端**：使用消息指纹匹配
3. **对于WebChat类客户端**：使用标准的conversation_id

这样可以在不破坏WebChat行为的前提下，修复ChatBox的问题。

## 修改文件清单

1. `backend/api/proxy/v1/chat.py` - 添加指纹匹配逻辑
2. `backend/core/conversation_manager.py` - 添加指纹存储/查询方法
3. 可能需要添加索引到MongoDB

## 部署

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```
