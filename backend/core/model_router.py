"""
模型路由引擎 - 根据输入决定使用大模型还是小模型
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """路由结果"""
    model_type: str  # "small" 或 "big"
    reason: str
    confidence: float = 0.0
    matched_rule: Optional[str] = None


class ModelRouter:
    """模型路由引擎"""
    
    def __init__(self, skill_manager, config_manager, redis_client=None):
        """
        初始化模型路由引擎
        
        Args:
            skill_manager: Skill管理器实例
            config_manager: 配置管理器实例
            redis_client: Redis客户端（可选）
        """
        self._skill_manager = skill_manager
        self._config_manager = config_manager
        self._redis = redis_client
    
    async def route(
        self, 
        virtual_model: str, 
        user_input: str,
        conversation_id: Optional[str] = None
    ) -> RouteResult:
        """
        模型路由决策
        
        路由流程：
        1. 检查是否强制模式
        2. 获取会话上下文
        3. 尝试关键词路由（最高优先级）
        4. 尝试意图识别路由
        5. 使用默认模型
        
        Args:
            virtual_model: 虚拟模型名称
            user_input: 用户输入内容
            conversation_id: 会话ID（可选）
            
        Returns:
            RouteResult: 路由决策结果
        """
        try:
            # 1. 检查是否强制模式
            config = self._config_manager.get(f"ai-gateway.virtual_models.{virtual_model}")
            if not config:
                logger.warning(f"虚拟模型配置不存在: {virtual_model}")
                return RouteResult(
                    model_type="small",
                    reason="虚拟模型配置不存在，使用默认小模型"
                )
            
            # 检查是否强制使用当前模型
            if config.get("force_current", False):
                current_model = config.get("current", "small")
                logger.info(f"强制模式: 使用 {current_model} 模型")
                return RouteResult(
                    model_type=current_model,
                    reason="强制模式",
                    confidence=1.0
                )
            
            # 2. 获取会话上下文
            context = await self._get_conversation_context(conversation_id)
            
            # 3. 尝试关键词路由（最高优先级）
            keyword_result = await self._try_keyword_router(user_input)
            if keyword_result:
                logger.info(f"关键词路由匹配成功: {keyword_result.matched_rule}")
                return keyword_result
            
            # 4. 尝试意图识别路由
            intent_result = await self._try_intent_router(user_input, context)
            if intent_result and intent_result.confidence > 0.8:
                logger.info(f"意图识别路由成功: {intent_result.reason}")
                return intent_result
            
            # 5. 使用默认模型
            current_model = config.get("current", "small")
            confidence_str = f"{intent_result.confidence:.2f}" if intent_result else "N/A"
            reason = f"置信度{confidence_str}过低，使用默认模型"
            
            logger.info(f"使用默认模型: {current_model}, 原因: {reason}")
            return RouteResult(
                model_type=current_model,
                reason=reason,
                confidence=intent_result.confidence if intent_result else 0.0
            )
            
        except Exception as e:
            logger.error(f"路由决策失败: {e}")
            # 出错时使用小模型作为安全默认值
            return RouteResult(
                model_type="small",
                reason=f"路由异常: {str(e)}"
            )
    
    async def _get_conversation_context(self, conversation_id: Optional[str]) -> str:
        """
        获取会话上下文
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            str: 会话上下文文本
        """
        if not conversation_id or not self._redis:
            return ""
        
        try:
            # 从Redis获取最近的消息历史
            cache_key = f"conversation:{conversation_id}:messages"
            messages_json = await self._redis.get(cache_key)
            
            if messages_json:
                import json
                messages = json.loads(messages_json)
                # 取最近3条消息作为上下文
                recent_messages = messages[-3:] if len(messages) > 3 else messages
                context_parts = []
                for msg in recent_messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    context_parts.append(f"{role}: {content[:100]}...")
                return "\n".join(context_parts)
            
            return ""
        except Exception as e:
            logger.warning(f"获取会话上下文失败: {e}")
            return ""
    
    async def _try_keyword_router(self, user_input: str) -> Optional[RouteResult]:
        """
        尝试关键词路由
        
        调用 router/关键词路由 Skill 进行匹配
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            Optional[RouteResult]: 路由结果，未匹配时返回None
        """
        try:
            # 调用Skill管理器执行关键词路由
            result = await self._skill_manager.execute(
                "router", "关键词路由",
                user_input=user_input
            )
            
            if result and result.get("target"):
                return RouteResult(
                    model_type=result["target"],
                    matched_rule=result.get("matched_rule"),
                    reason=f"关键词匹配: {result.get('matched_rule', 'unknown')}",
                    confidence=1.0
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"关键词路由执行失败: {e}")
            return None
    
    async def _try_intent_router(
        self, 
        user_input: str, 
        context: str
    ) -> Optional[RouteResult]:
        """
        尝试意图识别路由
        
        调用 router/意图识别 Skill 进行分析
        
        Args:
            user_input: 用户输入内容
            context: 会话上下文
            
        Returns:
            Optional[RouteResult]: 路由结果，未匹配时返回None
        """
        try:
            # 调用Skill管理器执行意图识别
            result = await self._skill_manager.execute(
                "router", "意图识别",
                user_input=user_input,
                context=context
            )
            
            if result and result.get("model_type") and not result.get("fallback"):
                return RouteResult(
                    model_type=result["model_type"],
                    confidence=result.get("confidence", 0),
                    reason=result.get("reason", "")
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"意图识别路由执行失败: {e}")
            return None
    
    def get_router_config(self) -> Dict[str, Any]:
        """
        获取路由配置
        
        Returns:
            Dict[str, Any]: 路由配置信息
        """
        return self._config_manager.get("ai-gateway.router", {
            "keyword_priority": True,
            "intent_threshold": 0.8,
            "context_window": 3
        })
