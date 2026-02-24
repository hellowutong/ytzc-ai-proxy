# 修复ChatBox多轮对话问题

## 问题描述
ChatBox多轮对话时每次都会生成新的对话记录，而WebChat正常。这是因为后端在响应中移除了 `conversation_id` 字段。

## 根因
在 `backend/api/proxy/v1/chat.py` 第287-288行：
```python
# 移除非OpenAI标准字段，确保兼容性
response_data.pop("conversation_id", None)
response_data.pop("metadata", None)
```

这导致客户端无法获取对话ID，无法在多轮对话中保持连续性。

## 修复方案

### 修改文件: backend/api/proxy/v1/chat.py

找到第286-307行，替换为：

```python
        # 保留conversation_id用于多轮对话跟踪（ChatBox等客户端需要）
        # 注意：不移除conversation_id，确保客户端可以跟踪对话
        # response_data.pop("conversation_id", None)
        # response_data.pop("metadata", None)
        
        logger.info(f"[{result.request_id}] 对话响应完成: {result.conversation_id}")

        # 详细日志：记录响应
        logger.info(f"[ChatBox Debug] Response: {json.dumps(response_data, ensure_ascii=False)[:500]}")
        logger.info(f"[ChatBox Debug] Content-Type: application/json; charset=utf-8")

        # 调试：记录响应信息
        print(f"\n\n{'='*60}")
        print(f"[CHATBOX DEBUG] Response prepared at {datetime.now().isoformat()}")
        print(f"[CHATBOX DEBUG] Response: {json.dumps(response_data, ensure_ascii=False)[:500]}")
        print(f"{'='*60}\n\n")

        # 使用JSONResponse确保正确的Content-Type和字符编码
        # 添加自定义header返回conversation_id，便于客户端跟踪
        headers = {
            "X-Conversation-Id": str(result.conversation_id) if result.conversation_id else ""
        }
        return JSONResponse(
            status_code=200,
            content=response_data,
            media_type="application/json; charset=utf-8",
            headers=headers
        )
```

## 关键变更
1. **保留conversation_id**: 不再从响应中移除conversation_id字段
2. **添加HTTP Header**: 通过 `X-Conversation-Id` header 返回对话ID，双重保障
3. **保留metadata**: 不移除metadata字段，包含路由信息等有用数据

## 测试验证
1. 使用ChatBox进行多轮对话
2. 检查对话历史是否只生成一条记录
3. 验证所有消息都在同一会话中

## 部署
修改后需要重新部署：
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```
