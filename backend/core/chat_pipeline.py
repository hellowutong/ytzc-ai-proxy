"""
对话处理管道 - 使用职责链模式处理对话请求
"""

import logging
import time
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ChatContext:
    """对话上下文 - 在职责链中传递"""
    # 输入
    conversation_id: Optional[str] = None
    virtual_model: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_message: str = ""
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # 处理结果
    model_type: Optional[str] = None  # "small" | "big"
    model_config: Optional[Dict] = None
    response_content: str = ""
    final_response: Optional[Dict] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    start_time: float = field(default_factory=time.time)
    user_message_saved: bool = False
    error_occurred: bool = False
    skip_reason: Optional[str] = None


class PipelineHandler:
    """处理器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self._next: Optional['PipelineHandler'] = None
    
    def set_next(self, handler: 'PipelineHandler') -> 'PipelineHandler':
        """设置下一个处理器"""
        self._next = handler
        return handler
    
    async def handle(self, context: ChatContext) -> ChatContext:
        """处理逻辑"""
        context = await self._process(context)
        
        # 如果没有跳过后续处理的标记，继续执行链
        if self._next and not context.skip_reason and not context.error_occurred:
            return await self._next.handle(context)
        return context
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """子类实现具体逻辑"""
        raise NotImplementedError


class InputValidatorHandler(PipelineHandler):
    """输入验证处理器"""
    
    def __init__(self):
        super().__init__("InputValidatorHandler")
        self.max_input_length = 10000
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """验证输入"""
        # 1. 如果user_message为空但有messages，尝试从messages提取
        if not context.user_message and context.messages:
            # 取最后一条用户消息
            for msg in reversed(context.messages):
                if isinstance(msg, dict) and msg.get("role") == "user" and msg.get("content"):
                    context.user_message = msg.get("content", "")
                    break
        
        # 2. 确保user_message是字符串类型
        if isinstance(context.user_message, list):
            if context.user_message:
                last_msg = context.user_message[-1]
                if isinstance(last_msg, dict):
                    context.user_message = last_msg.get("content", "")
                else:
                    context.user_message = str(last_msg)
            else:
                context.user_message = ""
        elif not isinstance(context.user_message, str):
            # 如果是其他类型，转为字符串
            context.user_message = str(context.user_message) if context.user_message else ""
        
        # 3. 检查空消息
        if not context.user_message or not context.user_message.strip():
            context.error_occurred = True
            context.response_content = "消息内容不能为空"
            logger.warning(f"[{context.request_id}] 输入验证失败: 空消息")
            return context
        
        # 检查长度
        if len(context.user_message) > self.max_input_length:
            context.error_occurred = True
            context.response_content = f"消息长度超过限制（最大{self.max_input_length}字符）"
            logger.warning(f"[{context.request_id}] 输入验证失败: 超长输入")
            return context
        
        # 基本安全检查（简单过滤）
        dangerous_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
        ]
        
        user_input_lower = context.user_message.lower()
        for pattern in dangerous_patterns:
            if pattern in user_input_lower:
                logger.warning(f"[{context.request_id}] 检测到潜在危险内容: {pattern}")
                # 只记录日志，不阻止（可能误伤正常内容）
                context.metadata["security_flag"] = True
                break
        
        logger.info(f"[{context.request_id}] 输入验证通过")
        return context


class UserMessagePersistence(PipelineHandler):
    """保存用户原始提问 - 最高优先级"""
    
    def __init__(self, conversation_manager):
        super().__init__("UserMessagePersistence")
        self._cm = conversation_manager
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """保存用户消息"""
        try:
            # 确保有conversation_id
            if not context.conversation_id:
                context.conversation_id = await self._cm.create_conversation(
                    context.virtual_model
                )
                logger.info(f"[{context.request_id}] 创建新会话: {context.conversation_id}")
            
            # 立即保存用户消息（不等待后续处理）
            await self._cm.add_message(
                conversation_id=context.conversation_id,
                role="user",
                content=context.user_message,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": context.request_id,
                    "source": "webchat",
                    "ip": context.metadata.get("client_ip")
                }
            )
            
            context.user_message_saved = True
            logger.info(f"💾 [{context.request_id}] 用户消息已持久化: {context.conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 保存用户消息失败: {e}")
            # 保存失败不中断流程，记录错误继续
            context.metadata["user_message_save_error"] = str(e)
        
        return context


class KnowledgeRetrievalHandler(PipelineHandler):
    """知识库检索 - 当前预留接口，读取配置但不实现核心逻辑"""
    
    def __init__(self, config_manager, skill_manager):
        super().__init__("KnowledgeRetrievalHandler")
        self._config = config_manager
        self._sm = skill_manager
    
    def _get_knowledge_config(self, virtual_model: str) -> Dict:
        """从config.yml读取知识库配置"""
        return self._config.get(
            f"ai-gateway.virtual_models.{virtual_model}.knowledge", 
            {}
        )
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """知识检索处理（预留接口）"""
        # 读取配置
        config = self._get_knowledge_config(context.virtual_model)
        
        if not config.get("enabled", False):
            return context  # 未启用，直接跳过
        
        # 预留：检查Skill配置
        skill_config = config.get("skill", {})
        if skill_config.get("enabled") and skill_config.get("version"):
            # 预留调用Skill的代码，当前不实现
            # result = await self._sm.execute(
            #     "knowledge", f"检索/{skill_config['version']}",
            #     query=context.user_message
            # )
            pass
        
        # 记录元数据
        context.metadata["knowledge_checked"] = True
        context.metadata["knowledge_enabled"] = True
        context.metadata["knowledge_skill_version"] = skill_config.get("version")
        
        logger.info(f"📚 [{context.request_id}] 知识库检索已预留（配置启用，暂未实现）")
        return context


class WebSearchHandler(PipelineHandler):
    """联网搜索 - 预留接口，4get空实现"""
    
    def __init__(self, config_manager, skill_manager):
        super().__init__("WebSearchHandler")
        self._config = config_manager
        self._sm = skill_manager
    
    def _get_web_search_config(self, virtual_model: str) -> Dict:
        """从config.yml读取联网搜索配置"""
        return self._config.get(
            f"ai-gateway.virtual_models.{virtual_model}.web_search",
            {}
        )
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """联网搜索处理（预留接口）"""
        config = self._get_web_search_config(context.virtual_model)
        
        if not config.get("enabled", False):
            return context
        
        targets = config.get("target", [])
        
        # 4get 空实现（保留目录）
        if "4get" in targets:
            logger.info(f"🔍 [{context.request_id}] 4get搜索 - 空实现（目录保留）")
        
        # LibreX 预留
        if "LibreX" in targets:
            logger.info(f"🔍 [{context.request_id}] LibreX搜索 - 预留接口")
        
        # Skill预留
        skill_config = config.get("skill", {})
        if skill_config.get("enabled"):
            logger.info(f"🔍 [{context.request_id}] WebSearch Skill预留（版本: {skill_config.get('version')}）")
        
        context.metadata["web_search_checked"] = True
        context.metadata["web_search_targets"] = targets
        
        return context


class ModelRoutingHandler(PipelineHandler):
    """模型路由决策处理器 - 包含关键词匹配和替换功能"""
    
    def __init__(self, model_router, config_manager=None):
        super().__init__("ModelRoutingHandler")
        self._router = model_router
        self._config = config_manager
    
    def _get_keyword_config(self, virtual_model: str) -> Dict:
        """从config.yml读取关键词路由配置"""
        return self._config.get(
            f"ai-gateway.virtual_models.{virtual_model}.routing.keywords",
            {}
        ) if self._config else {}
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """执行模型路由决策 + 关键词替换"""
        
        # 1. 首先尝试关键词匹配和替换
        keyword_config = self._get_keyword_config(context.virtual_model)
        
        if keyword_config.get("enabled", False):
            rules = keyword_config.get("rules", [])
            
            for rule in rules:
                pattern = rule.get("pattern", "")
                target = rule.get("target", "small")
                
                if pattern in context.user_message:
                    # 匹配成功：切换模型
                    context.model_type = target
                    context.metadata["model_type"] = target
                    context.metadata["route_reason"] = f"关键词匹配: {pattern}"
                    context.metadata["matched_keyword"] = pattern
                    
                    # 记录原始消息
                    context.metadata["original_user_message"] = context.user_message
                    
                    # 移除关键词
                    remaining_message = context.user_message.replace(pattern, "").strip()
                    context.metadata["processed_user_message"] = remaining_message
                    
                    logger.info(f"🎯 [{context.request_id}] 关键词匹配: {pattern} -> {target}")
                    logger.info(f"📝 [{context.request_id}] 消息替换: '{pattern}' -> ''")
                    logger.info(f"📝 [{context.request_id}] 剩余消息: '{remaining_message}'")
                    
                    # 检查是否为纯关键词切换（移除关键词后无内容）
                    if not remaining_message:
                        # 纯关键词切换：不调用LLM，不返回消息
                        context.user_message = ""
                        context.skip_reason = "keyword_only_switch"
                        context.response_content = ""  # 空响应
                        logger.info(f"✅ [{context.request_id}] 纯关键词切换，跳过后续处理")
                        return context
                    
                    # 有剩余内容，更新user_message继续后续处理
                    context.user_message = remaining_message
                    
                    # 匹配成功，跳过后续的ModelRouter.route()调用
                    return context
        
        # 2. 如果没有匹配关键词，继续原有ModelRouter.route()逻辑
        try:
            route_result = await self._router.route(
                virtual_model=context.virtual_model,
                user_input=context.user_message,
                conversation_id=context.conversation_id
            )
            
            context.model_type = route_result.model_type
            context.metadata["model_type"] = route_result.model_type
            context.metadata["route_reason"] = route_result.reason
            context.metadata["route_confidence"] = route_result.confidence
            context.metadata["matched_rule"] = route_result.matched_rule
            
            logger.info(f"🎯 [{context.request_id}] 路由决策: {route_result.model_type} - {route_result.reason}")
            
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 路由决策失败: {e}")
            # 路由失败时使用默认值
            context.model_type = "small"
            context.metadata["route_error"] = str(e)
            context.metadata["route_reason"] = "路由失败，使用默认模型"
        
        return context


class LLMInvocationHandler(PipelineHandler):
    """LLM调用处理器"""
    
    def __init__(self, config_manager):
        super().__init__("LLMInvocationHandler")
        self._config = config_manager
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """调用远程LLM"""
        # 检查是否需要跳过（纯关键词切换）
        if context.skip_reason == "keyword_only_switch":
            return context
        
        # 检查模型类型
        if not context.model_type:
            logger.warning(f"[{context.request_id}] model_type未设置，使用默认small模型")
            context.model_type = "small"
        
        try:
            # 动态导入以避免循环依赖
            from services.llm_service import LLMServiceFactory, ModelProvider
            from models.base import ChatCompletionRequest, Message
            
            # 获取虚拟模型配置
            vm_config = self._config.get(f"ai-gateway.virtual_models.{context.virtual_model}")
            if not vm_config:
                raise ValueError(f"虚拟模型配置不存在: {context.virtual_model}")
            
            # 获取具体模型配置
            model_config = vm_config.get(context.model_type, {})
            if not model_config:
                raise ValueError(f"模型类型配置不存在: {context.model_type}")
            
            # 确定提供商
            provider_str = model_config.get("provider", "siliconflow").lower()
            if provider_str == "openai":
                provider = ModelProvider.OPENAI
            elif provider_str == "ollama":
                provider = ModelProvider.OLLAMA
            else:
                provider = ModelProvider.SILICONFLOW
            
            # 创建LLM服务
            llm_service = LLMServiceFactory.create(
                provider=provider,
                base_url=model_config.get("base_url", "https://api.siliconflow.cn/v1"),
                api_key=model_config.get("api_key"),
                model=model_config.get("model", "Qwen/Qwen2.5-7B-Instruct"),
                temperature=context.temperature,
                max_tokens=context.max_tokens
            )
            
            # 构建请求
            chat_request = ChatCompletionRequest(
                model=model_config.get("model", "unknown"),
                messages=[
                    Message(role=msg.get("role", "user"), content=msg.get("content", ""))
                    for msg in context.messages
                ],
                stream=False,
                temperature=context.temperature,
                max_tokens=context.max_tokens
            )
            
            logger.info(f"🤖 [{context.request_id}] 调用LLM: {provider.value}/{model_config.get('model')}")
            
            # 调用LLM
            response = await llm_service.chat(chat_request)
            
            # 提取响应内容
            if response.choices:
                context.response_content = response.choices[0].message.content
            
            # 记录token使用
            if response.usage:
                context.metadata["prompt_tokens"] = response.usage.prompt_tokens
                context.metadata["completion_tokens"] = response.usage.completion_tokens
                context.metadata["total_tokens"] = response.usage.total_tokens
            
            context.metadata["model_used"] = model_config.get("model")
            context.metadata["llm_called"] = True
            
            logger.info(f"✅ [{context.request_id}] LLM调用成功，响应长度: {len(context.response_content)}字符")
            
        except ValueError as e:
            logger.error(f"❌ [{context.request_id}] LLM配置错误: {e}")
            context.error_occurred = True
            context.response_content = "抱歉，AI服务配置错误，请联系管理员。"
            context.metadata["llm_config_error"] = str(e)
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] LLM调用失败: {e}")
            context.error_occurred = True
            context.response_content = "抱歉，AI服务暂时不可用，请稍后重试。"
            context.metadata["llm_error"] = str(e)
        
        return context


class AssistantMessagePersistence(PipelineHandler):
    """保存助手回复处理器"""
    
    def __init__(self, conversation_manager):
        super().__init__("AssistantMessagePersistence")
        self._cm = conversation_manager
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """保存助手回复"""
        if not context.response_content or context.error_occurred:
            return context
        
        try:
            await self._cm.add_message(
                conversation_id=context.conversation_id,
                role="assistant",
                content=context.response_content,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": context.request_id,
                    "model_used": context.model_type,
                    "route_reason": context.metadata.get("route_reason"),
                    "has_knowledge": context.metadata.get("knowledge_enabled", False),
                    "has_web_search": bool(context.metadata.get("web_search_targets", []))
                }
            )
            
            logger.info(f"💾 [{context.request_id}] 助手回复已保存")
            
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 保存助手回复失败: {e}")
            context.metadata["assistant_message_save_error"] = str(e)
        
        return context


class RawDataArchiveHandler(PipelineHandler):
    """完整数据归档处理器 - 用于调试和审计"""
    
    def __init__(self, conversation_manager):
        super().__init__("RawDataArchiveHandler")
        self._cm = conversation_manager
        self._db = conversation_manager._db
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """归档完整请求/响应数据"""
        try:
            archive_data = {
                "conversation_id": context.conversation_id,
                "request_id": context.request_id,
                "timestamp": datetime.utcnow(),
                "request": {
                    "user_message": context.user_message,
                    "virtual_model": context.virtual_model,
                    "messages": context.messages,
                    "temperature": context.temperature,
                    "max_tokens": context.max_tokens,
                    "knowledge_enabled": context.metadata.get("knowledge_enabled", False),
                    "web_search_enabled": bool(context.metadata.get("web_search_targets", []))
                },
                "response": {
                    "content": context.response_content,
                    "model_type": context.model_type,
                    "model_used": context.metadata.get("model_used"),
                    "tokens_used": context.metadata.get("tokens_used"),
                    "error": context.error_occurred
                },
                "processing_metadata": context.metadata,
                "duration_ms": (time.time() - context.start_time) * 1000
            }
            
            # 保存到raw_conversation_logs集合
            await self._db["raw_conversation_logs"].insert_one(archive_data)
            
            logger.info(f"📦 [{context.request_id}] 原始数据已归档")
            
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 归档原始数据失败: {e}")
            # 归档失败不中断流程
            context.metadata["raw_archive_error"] = str(e)
        
        return context


class ResponseFormatter(PipelineHandler):
    """响应格式化处理器"""
    
    def __init__(self):
        super().__init__("ResponseFormatter")
    
    async def _process(self, context: ChatContext) -> ChatContext:
        """格式化最终响应"""
        if context.error_occurred:
            context.final_response = {
                "error": {
                    "message": context.response_content or "处理请求时发生错误",
                    "type": "processing_error",
                    "request_id": context.request_id
                }
            }
        else:
            context.final_response = {
                "id": f"chatcmpl-{context.request_id}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": context.virtual_model,
                "conversation_id": context.conversation_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": context.response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": context.metadata.get("prompt_tokens", 0),
                    "completion_tokens": context.metadata.get("completion_tokens", 0),
                    "total_tokens": context.metadata.get("total_tokens", 0)
                },
                "metadata": {
                    "model_type": context.model_type,
                    "route_reason": context.metadata.get("route_reason"),
                    "has_knowledge": context.metadata.get("knowledge_enabled", False),
                    "has_web_search": bool(context.metadata.get("web_search_targets", []))
                }
            }
        
        logger.info(f"📤 [{context.request_id}] 响应已格式化")
        return context


class ChatPipeline:
    """对话管道 - 组装职责链"""
    
    def __init__(
        self,
        conversation_manager,
        skill_manager,
        config_manager,
        model_router=None,
        llm_service=None
    ):
        self._cm = conversation_manager
        self._sm = skill_manager
        self._config = config_manager
        self._router = model_router
        self._llm_service = llm_service
        
        # 构建职责链
        self._chain = self._build_chain()
    
    def _build_chain(self) -> PipelineHandler:
        """构建处理链"""
        
        # Phase 1: 输入处理
        validator = InputValidatorHandler()
        user_persistence = UserMessagePersistence(self._cm)
        
        # Phase 2: 预处理（预留接口）
        knowledge = KnowledgeRetrievalHandler(self._config, self._sm)
        web_search = WebSearchHandler(self._config, self._sm)
        
        # Phase 3: 模型层
        routing = ModelRoutingHandler(self._router, self._config)
        llm = LLMInvocationHandler(self._config)
        
        # Phase 4: 后处理
        assistant_persistence = AssistantMessagePersistence(self._cm)
        raw_archive = RawDataArchiveHandler(self._cm)
        
        # Phase 5: 输出
        formatter = ResponseFormatter()
        
        # 组装链条
        validator.set_next(user_persistence) \
                 .set_next(knowledge) \
                 .set_next(web_search) \
                 .set_next(routing) \
                 .set_next(llm) \
                 .set_next(assistant_persistence) \
                 .set_next(raw_archive) \
                 .set_next(formatter)
        
        return validator
    
    async def process(self, context: ChatContext) -> ChatContext:
        """执行管道处理"""
        return await self._chain.handle(context)


class ErrorRecoveryHandler:
    """错误恢复包装器 - 确保消息不丢失"""
    
    def __init__(self, conversation_manager):
        self._cm = conversation_manager
    
    async def handle_with_recovery(self, context: ChatContext, chain: PipelineHandler):
        """带错误恢复的处理"""
        try:
            return await chain.handle(context)
        except Exception as e:
            logger.error(f"❌ [{context.request_id}] 职责链执行失败: {e}")
            
            # 确保用户消息已保存（如果没保存的话）
            if not context.user_message_saved:
                try:
                    if not context.conversation_id:
                        context.conversation_id = await self._cm.create_conversation(
                            context.virtual_model
                        )
                    
                    await self._cm.add_message(
                        context.conversation_id,
                        "user",
                        context.user_message,
                        metadata={
                            "error_occurred": True,
                            "error_message": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    logger.info(f"💾 [{context.request_id}] 紧急保存用户消息成功")
                except Exception as save_error:
                    logger.error(f"❌ [{context.request_id}] 紧急保存失败: {save_error}")
            
            # 返回友好的错误响应
            context.response_content = "抱歉，处理您的请求时出现了错误。请稍后重试。"
            context.error_occurred = True
            context.metadata["error"] = str(e)
            
            return context
