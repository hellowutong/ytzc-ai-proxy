"""
会话摘要生成服务
自动根据会话消息生成摘要
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from app.core.config import get_config
from app.domain.models.session import Message


class SessionSummarizer:
    """会话摘要生成器"""
    
    DEFAULT_PROMPT_TEMPLATE = """请对以下AI对话进行摘要，要求：
1. 简洁明了，不超过200字
2. 提取核心主题和关键结论
3. 保持客观中立

对话内容：
{content}

摘要："""

    def __init__(
        self,
        repository: Optional[Any] = None,
        llm_service: Optional[Any] = None,
        prompt_template: Optional[str] = None
    ):
        """
        初始化 SessionSummarizer
        
        Args:
            repository: 会话仓储实例（可选，用于直接操作数据库）
            llm_service: LLM服务实例（可选，用于调用模型）
            prompt_template: 自定义Prompt模板
        """
        self.repository = repository
        self.llm_service = llm_service
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT_TEMPLATE
        self.config = get_config()
    
    def build_prompt(
        self,
        messages: List[Message],
        template: Optional[str] = None
    ) -> str:
        """
        根据消息构建摘要 Prompt
        
        Args:
            messages: 消息列表
            template: Prompt模板（可选）
            
        Returns:
            构建好的 Prompt 字符串
        """
        template = template or self.prompt_template
        
        content = self._extract_message_content(messages)
        
        return template.format(content=content)
    
    def _extract_message_content(self, messages: List[Message]) -> str:
        """
        提取消息内容
        
        Args:
            messages: 消息列表
            
        Returns:
            格式化后的消息内容
        """
        if not messages:
            return ""
        
        lines = []
        for msg in messages:
            role = msg.role.upper() if hasattr(msg, 'role') else str(msg.get('role', '')).upper()
            content = msg.content if hasattr(msg, 'content') else str(msg.get('content', ''))
            lines.append(f"[{role}]: {content}")
        
        return "\n".join(lines)
    
    async def generate_summary(
        self,
        session,
        max_length: int = 200,
        prompt_template: Optional[str] = None
    ) -> str:
        """
        生成会话摘要
        
        Args:
            session: 会话对象
            max_length: 摘要最大长度
            prompt_template: 自定义Prompt模板
            
        Returns:
            生成的摘要内容
        """
        messages = session.messages if hasattr(session, 'messages') else []
        
        if not messages:
            return ""
        
        prompt = self.build_prompt(messages, prompt_template)
        
        try:
            summary = await self.call_llm(prompt)
            
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            return summary.strip()
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return ""
    
    async def call_llm(self, prompt: str) -> str:
        """
        调用 LLM 生成摘要
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM 生成的摘要
        """
        if self.llm_service:
            return await self.llm_service.complete(prompt)
        
        config = get_config()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            providers = config.providers if hasattr(config, 'providers') else []
            
            provider_config = None
            for p in providers:
                if p.get("small_model"):
                    provider_config = p["small_model"]
                    break
            
            if not provider_config:
                return ""
            
            response = await client.post(
                f"{provider_config.get('api_base', '')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider_config.get('api_key', '')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": provider_config.get("id", "gpt-3.5-turbo"),
                    "messages": [
                        {"role": "system", "content": "你是一个专业的对话摘要助手。请简洁总结对话内容。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 300
                }
            )
            response.raise_for_status()
            
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            
            return ""
    
    async def end_session_with_summary(self, session_id: str) -> Dict:
        """
        结束会话并生成摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            操作结果
        """
        if not self.repository:
            return {"success": False, "message": "Repository not configured"}
        
        try:
            session = await self.repository.get_by_id(session_id)
            
            if not session:
                return {"success": False, "message": "Session not found"}
            
            summary = await self.generate_summary(session)
            
            await self.repository.update(
                session_id,
                {
                    "summary": summary,
                    "status": "ended",
                    "ended_at": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "summary": summary
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def batch_generate_summaries(
        self,
        session_ids: List[str],
        max_length: int = 200
    ) -> List[Dict]:
        """
        批量生成摘要
        
        Args:
            session_ids: 会话ID列表
            max_length: 摘要最大长度
            
        Returns:
            每个会话的摘要生成结果
        """
        if not self.repository:
            return [{"success": False, "message": "Repository not configured"} for _ in session_ids]
        
        results = []
        for session_id in session_ids:
            result = await self.end_session_with_summary(session_id)
            result["session_id"] = session_id
            results.append(result)
        
        return results
    
    def extract_topics(self, summary: str) -> List[str]:
        """
        从摘要中提取主题关键词
        
        Args:
            summary: 摘要内容
            
        Returns:
            主题关键词列表
        """
        if not summary:
            return []
        
        topics = []
        words = summary.replace(",", " ").replace("。", " ").split()
        
        for word in words:
            if len(word) >= 2:
                topics.append(word)
        
        return topics[:10]
    
    def calculate_summary_length_score(
        self,
        original_content: str,
        summary: str
    ) -> float:
        """
        计算摘要长度得分
        
        Args:
            original_content: 原始内容
            summary: 摘要
            
        Returns:
            压缩比得分
        """
        if not original_content or not summary:
            return 0.0
        
        original_length = len(original_content)
        summary_length = len(summary)
        
        if original_length == 0:
            return 0.0
        
        compression_ratio = summary_length / original_length
        
        if compression_ratio > 0.5:
            return 0.3  # 摘要太长
        elif compression_ratio < 0.05:
            return 0.5  # 摘要太短
        else:
            return 1.0  # 合适


async def generate_session_summary(
    session_id: str,
    repository
) -> Dict:
    """
    便捷函数：生成会话摘要
    
    Args:
        session_id: 会话ID
        repository: 会话仓储实例
        
    Returns:
        摘要生成结果
    """
    summarizer = SessionSummarizer(repository=repository)
    return await summarizer.end_session_with_summary(session_id)
