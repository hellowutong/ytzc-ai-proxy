"""
模型路由引擎 - 根据输入决定使用大模型还是小模型
"""

import logging
import threading
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
            keyword_result = await self._try_keyword_router(user_input, config, virtual_model)
            if keyword_result:
                logger.info(f"关键词路由匹配成功: {keyword_result.matched_rule}")
                return keyword_result
            
            # 4. 尝试意图识别路由（传递 model_config 以读取 routing.skill）
            intent_result = await self._try_intent_router(user_input, context, config)
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
    
    async def _try_keyword_router(self, user_input: str, model_config: Dict[str, Any], virtual_model: str) -> Optional[RouteResult]:
        """
        尝试关键词路由（从虚拟模型的 routing 配置读取）
        
        优先级：
        1. routing.keywords 配置（虚拟模型独立配置）
        2. keyword_switching 配置（旧格式，兼容）
        3. Skill 路由作为后备
        
        Args:
            user_input: 用户输入内容
            model_config: 模型配置
            virtual_model: 虚拟模型名称
            
        Returns:
            Optional[RouteResult]: 路由结果，未匹配时返回None
        """
        try:
            user_input_lower = user_input.lower()
            
            # 1. 首先检查 routing.keywords 配置（虚拟模型独立配置）
            routing_config = model_config.get("routing", {})
            keywords_config = routing_config.get("keywords", {})
            if keywords_config.get("enable", False):
                for rule in keywords_config.get("rules", []):
                    pattern = rule.get("pattern", "")
                    target = rule.get("target", "")  # "big" 或 "small"
                    
                    if pattern.lower() in user_input_lower:
                        logger.info(f"关键词路由匹配: '{pattern}' -> {target}")
                        
                        # 持久化切换：更新 current 值
                        current_model = model_config.get("current", "small")
                        if current_model != target:
                            logger.info(f"持久化切换模型: {virtual_model} {current_model} -> {target}")
                            # 更新内存中的配置
                            model_config["current"] = target
                            # 同步保存到配置文件（确保立即生效）
                            threading.Thread(
                                target=self._sync_persist_model_switch,
                                args=(virtual_model, target),
                                daemon=True
                            ).start()
                        
                        return RouteResult(
                            model_type=target,
                            matched_rule=f"keyword:{pattern}",
                            reason=f"关键词匹配: {pattern} -> 切换到{target}模型",
                            confidence=1.0
                        )
            
            # 2. 兼容旧格式 keyword_switching
            keyword_config = model_config.get("keyword_switching", {})
            if keyword_config.get("enabled", False):
                user_input_lower = user_input.lower()
                
                # 检查小模型关键词
                for keyword in keyword_config.get("small_keywords", []):
                    if keyword.lower() in user_input_lower:
                        logger.info(f"关键字切换匹配: 小模型关键词 '{keyword}'")
                        return RouteResult(
                            model_type="small",
                            matched_rule=f"keyword:{keyword}",
                            reason=f"关键字切换匹配: {keyword}",
                            confidence=1.0
                        )
                
                # 检查大模型关键词
                for keyword in keyword_config.get("big_keywords", []):
                    if keyword.lower() in user_input_lower:
                        logger.info(f"关键字切换匹配: 大模型关键词 '{keyword}'")
                        return RouteResult(
                            model_type="big",
                            matched_rule=f"keyword:{keyword}",
                            reason=f"关键字切换匹配: {keyword}",
                            confidence=1.0
                        )
            
            # 2. 未启用或未匹配，调用 Skill 路由作为后备
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
        context: str,
        model_config: Optional[Dict[str, Any]] = None
    ) -> Optional[RouteResult]:
        """
        尝试意图识别路由（从虚拟模型的 routing.skill 配置读取）
        
        Args:
            user_input: 用户输入内容
            context: 会话上下文
            model_config: 模型配置（可选，用于读取 routing.skill）
            
        Returns:
            Optional[RouteResult]: 路由结果，未匹配时返回None
        """
        try:
            # 检查是否启用 routing.skill
            if model_config:
                routing_config = model_config.get("routing", {})
                skill_config = routing_config.get("skill", {})
                if not skill_config.get("enabled", True):
                    logger.info("[ROUTER] routing.skill 已禁用，跳过意图识别")
                    return None
            
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
    
    async def _persist_model_switch(self, virtual_model: str, target: str):
        """
        异步触发持久化（使用后台线程避免阻塞）
        
        Args:
            virtual_model: 虚拟模型名称
            target: 目标模型 ("small" 或 "big")
        """
        import threading
        threading.Thread(
            target=self._sync_persist_model_switch,
            args=(virtual_model, target),
            daemon=True
        ).start()

    def _sync_persist_model_switch(self, virtual_model: str, target: str):
        """
        同步持久化模型切换到配置文件（在后台线程执行）
        """
        import time
        import yaml
        
        # 延迟执行，避免阻塞主请求
        time.sleep(0.5)
        
        try:
            config_path = "/app/config.yml"
            
            logger.info(f"[PERSIST] 开始持久化: {virtual_model} -> {target}")
            
            # 读取当前配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查并更新 current 值
            if ('ai-gateway' in config and 
                'virtual_models' in config['ai-gateway'] and
                virtual_model in config['ai-gateway']['virtual_models']):
                
                old_current = config['ai-gateway']['virtual_models'][virtual_model].get('current', 'small')
                config['ai-gateway']['virtual_models'][virtual_model]['current'] = target
                
                # 写回文件 - 使用安全的方式避免编码问题
                yaml_content = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
                with open(config_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(yaml_content)
                
                logger.info(f"✅ 已持久化: {virtual_model}.current {old_current} -> {target}")
            else:
                logger.warning(f"[PERSIST] 配置路径不存在: {virtual_model}")
                
        except Exception as e:
            logger.error(f"❌ 持久化失败: {e}", exc_info=True)
    
    def get_router_config(self, model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取路由配置（已从虚拟模型的 routing 配置读取）
        
        Args:
            model_config: 虚拟模型配置（可选）
            
        Returns:
            Dict[str, Any]: 路由配置信息
        """
        # 优先从虚拟模型的 routing 配置读取
        if model_config:
            routing_config = model_config.get("routing", {})
            return {
                "keyword_priority": True,
                "intent_threshold": 0.8,
                "context_window": 3,
                "routing": routing_config
            }
        
        # 兼容旧代码
        return {
            "keyword_priority": True,
            "intent_threshold": 0.8,
            "context_window": 3
        }
