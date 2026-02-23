"""
虚拟AI代理 - 对话接口（使用Chat Pipeline职责链模式）
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import json
import time
import logging
import asyncio
from datetime import datetime

from api.dependencies import (
    get_config_manager,
    get_model_router,
    get_conversation_manager,
    get_skill_manager,
    verify_proxy_key
)
from core.chat_pipeline import (
    ChatPipeline,
    ChatContext
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def handle_stream_response(context, pipeline, virtual_model_name):
    """处理流式响应"""
    
    async def generate():
        # 执行pipeline获取结果
        result = await pipeline.process(context)
        
        if result.error_occurred:
            error_chunk = {
                "error": {"message": result.response_content or "处理请求时发生错误"}
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            return
        
        content = result.response_content
        request_id = result.request_id
        
        # 发送开始标记
        start_chunk = {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": virtual_model_name,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(start_chunk)}\n\n"
        
        # 分段发送内容
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            chunk_text = content[i:i+chunk_size]
            chunk = {
                "id": f"chatcmpl-{request_id}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": virtual_model_name,
                "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.03)  # 小延迟模拟打字效果
        
        # 发送结束标记
        end_chunk = {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": virtual_model_name,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(end_chunk)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    model_info: dict = Depends(verify_proxy_key)
):
    """
    对话接口（OpenAI兼容格式）- 使用Chat Pipeline职责链模式
    统一使用非流式响应
    """
    # 调试：记录完整请求信息
    body_str = ""
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        print(f"\n\n{'='*60}")
        print(f"[CHATBOX DEBUG] Request received at {datetime.now().isoformat()}")
        print(f"[CHATBOX DEBUG] Method: {request.method}")
        print(f"[CHATBOX DEBUG] URL: {request.url}")
        print(f"[CHATBOX DEBUG] Headers: {dict(request.headers)}")
        print(f"[CHATBOX DEBUG] Body: {body_str[:1000]}")
        print(f"{'='*60}\n\n")
    except Exception as e:
        print(f"[CHATBOX DEBUG] Error reading body: {e}")
    
    # 重新构建请求体用于后续处理（避免重复读取body）
    try:
        body = json.loads(body_str) if body_str else {}
    except:
        body = {}
    
    try:
        # 1. 解析请求体（使用已解析的body）
        # body 已经在上面从body_str解析好了
        
        # 详细日志：记录原始请求
        logger.info(f"[ChatBox Debug] Raw request: {json.dumps(body, ensure_ascii=False)[:500]}")
        logger.info(f"[ChatBox Debug] Headers: {dict(request.headers)}")
        logger.info(f"[ChatBox Debug] Messages count: {len(body.get('messages', []))}")
        if body.get('messages'):
            last_msg = body['messages'][-1]
            logger.info(f"[ChatBox Debug] Last message: {last_msg}")
        
        # 获取客户端类型
        user_agent = request.headers.get('user-agent', '').lower()
        is_chatbox = 'chatbox' in user_agent or 'electron' in user_agent
        
        # 转换消息格式（支持ChatBox的数组格式content）- 提前解析以便后续使用
        def normalize_content(content):
            """将content统一转换为字符串"""
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # 处理OpenAI新格式 [{"type": "text", "text": "..."}]
                texts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            texts.append(item.get("text", ""))
                        elif "text" in item:
                            texts.append(item["text"])
                return "\n".join(texts)
            else:
                return str(content) if content else ""
        
        # 转换所有消息的content（提前解析）
        raw_messages = body.get("messages", [])
        messages = []
        for msg in raw_messages:
            if isinstance(msg, dict):
                normalized_msg = dict(msg)
                normalized_msg["content"] = normalize_content(msg.get("content"))
                messages.append(normalized_msg)
            else:
                messages.append(msg)
        
        conversation_id = body.get("conversation_id")
        virtual_model_name = model_info["name"]
        
        # 提前获取依赖（用于指纹逻辑）
        conversation_manager = get_conversation_manager(request)
        
        # 对于ChatBox类客户端，使用消息指纹管理对话连续性
        if not conversation_id and is_chatbox and messages:
            import hashlib
            
            # 生成消息指纹（基于前2条用户消息）
            user_msgs = [msg for msg in messages if msg.get('role') == 'user'][:2]
            if user_msgs:
                fingerprint_data = json.dumps(user_msgs, sort_keys=True, ensure_ascii=False)
                fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
                
                # 使用指纹获取或创建对话
                conversation_id = await conversation_manager.get_or_create_by_fingerprint(
                    fingerprint, 
                    virtual_model_name,
                    ttl_minutes=30
                )
                logger.info(f"[ChatBox] 使用消息指纹管理对话: {fingerprint[:8]}... -> {conversation_id}")
        
        # 改进的user_message提取逻辑（支持ChatBox和WebChat）
        user_message = ""
        
        if messages:
            # 方法1：优先找最后一条用户消息
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    if user_message:
                        break
            
            # 方法2：如果没找到，用最后一条消息的内容
            if not user_message:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    user_message = last_msg.get("content", "")
        
        # 确保是字符串
        if not isinstance(user_message, str):
            user_message = str(user_message) if user_message else ""
        
        # 记录详细日志
        logger.info(f"[{virtual_model_name}] 收到对话请求: '{user_message[:50]}...' from {len(messages)} messages")
        
        # 验证user_message不能为空（方案B：返回400而不是500）
        if not user_message or not user_message.strip():
            logger.warning(f"[{virtual_model_name}] 请求验证失败: 消息内容为空")
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": "消息内容不能为空。请检查：1.messages数组是否正确 2.最后一条消息是否有content 3.是否有用户消息",
                        "type": "validation_error"
                    }
                }
            )
        
        # 2. 构建ChatContext（使用转换后的messages）
        context = ChatContext(
            conversation_id=conversation_id,
            virtual_model=virtual_model_name,
            messages=messages,
            user_message=user_message,
            stream=False,  # 强制非流式
            temperature=body.get("temperature", 0.7),
            max_tokens=body.get("max_tokens", 2000),
            metadata={
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        # 3. 获取依赖
        config_manager = get_config_manager()
        conversation_manager = get_conversation_manager(request)
        skill_manager = get_skill_manager()
        model_router = get_model_router(request)
        
        # 4. 创建ChatPipeline
        pipeline = ChatPipeline(
            conversation_manager=conversation_manager,
            skill_manager=skill_manager,
            config_manager=config_manager,
            model_router=model_router
        )
        
        # 5. 获取虚拟模型的流式支持配置
        virtual_models = config_manager.get("ai-gateway.virtual_models", {})
        model_config = virtual_models.get(virtual_model_name, {})
        stream_support = model_config.get("stream_support", False)
        
        # 检查客户端是否请求流式
        client_wants_stream = body.get("stream", False)
        
        if client_wants_stream and stream_support:
            # 客户端要求流式且模型支持
            logger.info(f"[{virtual_model_name}] Using stream mode")
            return await handle_stream_response(context, pipeline, virtual_model_name)
        elif client_wants_stream and not stream_support:
            # 客户端要求流式但模型不支持
            logger.warning(f"[{virtual_model_name}] Client requested stream but model doesn't support it")
            # 继续非流式处理
        
        # 5. 执行处理（带错误恢复）- 直接使用职责链
        result = await pipeline.process(context)
        
        # 6. 返回响应
        if result.error_occurred:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": result.response_content or "处理请求时发生错误",
                        "type": "processing_error",
                        "request_id": result.request_id
                    }
                }
            )
        
        # 返回成功响应（兼容OpenAI API格式）
        # 确保响应中包含conversation_id用于多轮对话跟踪
        if result.final_response:
            response_data = result.final_response
            # 确保conversation_id存在
            if "conversation_id" not in response_data and result.conversation_id:
                response_data["conversation_id"] = result.conversation_id
        else:
            response_data = {
                "id": f"chatcmpl-{result.request_id}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": virtual_model_name,
                "conversation_id": result.conversation_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": result.metadata.get("prompt_tokens", 0),
                    "completion_tokens": result.metadata.get("completion_tokens", 0),
                    "total_tokens": result.metadata.get("total_tokens", 0)
                }
            }
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        body_str = "N/A"
        try:
            body_str = json.dumps(body, ensure_ascii=False)[:500] if 'body' in locals() else "N/A"
        except:
            body_str = "N/A"
        logger.error(f"[ChatBox Debug] Error: {str(e)}")
        logger.error(f"[ChatBox Debug] Request body: {body_str}")
        logger.error(f"对话接口错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: Request,
    model_info: dict = Depends(verify_proxy_key)
):
    """
    对话接口（流式响应）- 兼容旧版端点
    注意：实际仍使用非流式处理，但模拟流式输出
    """
    body = await request.json()
    virtual_model_name = model_info["name"]
    
    async def generate():
        try:
            # 使用Chat Pipeline处理（非流式）
            user_message = body.get("messages", [])[-1].get("content", "") if body.get("messages") else ""
            conversation_id = body.get("conversation_id")
            
            context = ChatContext(
                conversation_id=conversation_id,
                virtual_model=virtual_model_name,
                messages=body.get("messages", []),
                user_message=user_message,
                stream=True,
                temperature=body.get("temperature", 0.7),
                max_tokens=body.get("max_tokens", 2000),
                metadata={
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            # 获取依赖
            config_manager = get_config_manager()
            conversation_manager = get_conversation_manager(request)
            skill_manager = get_skill_manager()
            model_router = get_model_router(request)
            
            # 创建并执行Pipeline
            pipeline = ChatPipeline(
                conversation_manager=conversation_manager,
                skill_manager=skill_manager,
                config_manager=config_manager,
                model_router=model_router
            )
            
            # 直接使用职责链处理
            result = await pipeline.process(context)
            
            # 如果出错，输出错误信息
            if result.error_occurred:
                error_data = {
                    "id": f"chatcmpl-{result.request_id}",
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": result.response_content},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(error_data)}\n\n".encode('utf-8')
            else:
                # 模拟逐字输出
                content = result.response_content
                chunk_size = 10  # 每10个字符一个chunk
                
                for i in range(0, len(content), chunk_size):
                    chunk_text = content[i:i+chunk_size]
                    chunk_data = {
                        "id": f"chatcmpl-{result.request_id}",
                        "object": "chat.completion.chunk",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk_text}
                        }]
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n".encode('utf-8')
                
                # 结束标记
                done_data = {
                    "id": f"chatcmpl-{result.request_id}",
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(done_data)}\n\n".encode('utf-8')
            
            yield b'data: [DONE]\n\n'
            
        except Exception as e:
            logger.error(f"流式接口错误: {e}")
            error_data = {
                "error": {
                    "message": str(e),
                    "type": "stream_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n".encode('utf-8')
            yield b'data: [DONE]\n\n'
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
