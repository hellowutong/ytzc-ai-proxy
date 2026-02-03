"""
TDD 测试 - SessionSummarizer 自动生成会话摘要
测试日期: 2026-02-02
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSessionSummarizer:
    """SessionSummarizer 测试类"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟会话"""
        from app.domain.models.session import Session, SessionStatus, Message
        
        return Session(
            session_id="test-session-001",
            proxy_key="tw-test-key-001",
            status=SessionStatus.ACTIVE,
            messages=[
                Message(role="user", content="你好，我想了解Python的异步编程"),
                Message(role="assistant", content="Python异步编程主要使用asyncio模块..."),
                Message(role="user", content="能给我一个具体的例子吗？"),
                Message(role="assistant", content="当然，这是一个使用asyncio的示例代码..."),
                Message(role="user", content="明白了，谢谢！"),
            ],
            created_at=datetime.utcnow().isoformat()
        )

    @pytest.fixture
    def summarizer(self):
        """创建 SessionSummarizer 实例"""
        from app.services.session_summarizer import SessionSummarizer
        return SessionSummarizer()

    def test_summarizer_class_exists(self, summarizer):
        """测试 SessionSummarizer 类存在"""
        assert summarizer is not None

    def test_build_prompt_with_messages(self, summarizer, mock_session):
        """测试根据消息构建 Prompt"""
        prompt = summarizer.build_prompt(mock_session.messages)
        
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "异步编程" in prompt
        assert "user" in prompt.lower() or "你好" in prompt

    def test_build_prompt_empty_messages(self, summarizer):
        """测试空消息列表的 Prompt 构建"""
        prompt = summarizer.build_prompt([])
        
        assert prompt is not None
        assert isinstance(prompt, str)

    def test_build_prompt_single_message(self, summarizer):
        """测试单条消息的 Prompt 构建"""
        from app.domain.models.session import Message
        messages = [Message(role="user", content="简单的测试消息")]
        prompt = summarizer.build_prompt(messages)
        
        assert prompt is not None
        assert "简单的测试消息" in prompt

    @pytest.mark.asyncio
    async def test_generate_summary_success(self, summarizer, mock_session):
        """测试成功生成摘要"""
        
        with patch.object(summarizer, 'call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "这是一个关于Python异步编程的摘要。用户学习asyncio模块的使用，包括基本概念和代码示例。"
            
            summary = await summarizer.generate_summary(mock_session)
            
            assert summary is not None
            assert isinstance(summary, str)
            assert len(summary) > 0
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_summary_empty_session(self, summarizer):
        """测试空会话生成摘要"""
        from app.domain.models.session import Session, SessionStatus
        
        empty_session = Session(
            session_id="empty-session",
            proxy_key="tw-test-key-001",
            status=SessionStatus.ACTIVE,
            messages=[],
            created_at=datetime.utcnow().isoformat()
        )
        
        with patch.object(summarizer, 'call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ""
            await summarizer.generate_summary(empty_session)
            # 空会话不应调用 LLM
            mock_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_llm_with_mock(self, summarizer):
        """测试使用 mock LLM 服务"""
        from app.services.session_summarizer import SessionSummarizer
        mock_llm = AsyncMock()
        mock_llm.complete = AsyncMock(return_value="Mock摘要内容")
        
        summarizer_with_mock = SessionSummarizer(llm_service=mock_llm)
        
        result = await summarizer_with_mock.call_llm("测试 Prompt")
        
        assert result == "Mock摘要内容"
        mock_llm.complete.assert_called_once_with("测试 Prompt")

    def test_extract_message_content(self, summarizer, mock_session):
        """测试提取消息内容"""
        content = summarizer._extract_message_content(mock_session.messages)
        
        assert content is not None
        assert len(content) > 0
        assert "你好，我想了解Python的异步编程" in content

    def test_extract_message_content_empty(self, summarizer):
        """测试空消息内容提取"""
        content = summarizer._extract_message_content([])
        assert content == ""

    @pytest.mark.asyncio
    async def test_generate_summary_length_limit(self, summarizer, mock_session):
        """测试摘要长度限制"""
        long_summary = "A" * 500  # 500字符的摘要
        
        with patch.object(summarizer, 'call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = long_summary
            
            summary = await summarizer.generate_summary(mock_session, max_length=200)
            
            # 摘要应被截断到200字符以内
            assert len(summary) <= 203  # 200 + "..."

    @pytest.mark.asyncio
    async def test_generate_summary_with_custom_prompt(self, summarizer, mock_session):
        """测试使用自定义 Prompt"""
        custom_prompt = "自定义 Prompt: {content}"
        
        with patch.object(summarizer, 'call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "使用自定义 Prompt 生成的摘要"
            
            await summarizer.generate_summary(
                mock_session, 
                prompt_template=custom_prompt
            )
            
            mock_call.assert_called_once()
            call_args = mock_call.call_args[0][0]
            assert "自定义 Prompt:" in call_args


class TestSessionSummarizerIntegration:
    """SessionSummarizer 集成测试"""

    @pytest.fixture
    def mock_repository(self):
        """模拟 SessionRepository"""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_llm_service(self):
        """模拟 LLM 服务"""
        mock = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_end_session_with_summary(self, mock_repository, mock_llm_service):
        """测试结束会话时自动生成摘要"""
        from app.services.session_summarizer import SessionSummarizer
        from app.domain.models.session import Session, SessionStatus, Message
        
        # 设置 mock
        mock_repository.get_by_id = AsyncMock(return_value=Session(
            session_id="test-001",
            proxy_key="tw-key",
            status=SessionStatus.ACTIVE,
            messages=[
                Message(role="user", content="测试消息"),
                Message(role="assistant", content="测试回复")
            ]
        ))
        mock_repository.update = AsyncMock()
        
        mock_llm_service.complete = AsyncMock(return_value="自动生成的摘要")
        
        summarizer = SessionSummarizer(
            repository=mock_repository,
            llm_service=mock_llm_service
        )
        
        # 执行
        await summarizer.end_session_with_summary("test-001")
        
        # 验证
        mock_repository.get_by_id.assert_called_once_with("test-001")
        mock_repository.update.assert_called_once()
        call_args = mock_repository.update.call_args
        assert "summary" in call_args[0][1]
        assert call_args[0][1]["summary"] == "自动生成的摘要"

    @pytest.mark.asyncio
    async def test_batch_generate_summaries(self, mock_repository, mock_llm_service):
        """测试批量生成摘要"""
        from app.services.session_summarizer import SessionSummarizer
        from app.domain.models.session import Session, SessionStatus, Message
        
        session_ids = ["session-1", "session-2", "session-3"]
        
        # Mock 每个会话
        def get_session_by_id(session_id):
            return Session(
                session_id=session_id,
                proxy_key="tw-key",
                status=SessionStatus.ENDED,
                messages=[Message(role="user", content=f"消息内容 {session_id}")],
                ended_at=datetime.utcnow().isoformat()
            )
        
        mock_repository.get_by_id = lambda sid: AsyncMock(return_value=get_session_by_id(sid))()
        mock_repository.update = AsyncMock()
        mock_llm_service.complete = AsyncMock(return_value="批量摘要结果")
        
        summarizer = SessionSummarizer(
            repository=mock_repository,
            llm_service=mock_llm_service
        )
        
        results = await summarizer.batch_generate_summaries(session_ids)
        
        assert len(results) == 3
        assert all(r["success"] for r in results)


class TestSessionSummarizerEdgeCases:
    """SessionSummarizer 边界条件测试"""

    @pytest.fixture
    def summarizer(self):
        from app.services.session_summarizer import SessionSummarizer
        return SessionSummarizer()

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, summarizer):
        """测试 LLM 调用错误处理"""
        
        with patch('app.services.session_summarizer.get_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.providers = []  # 空配置
            mock_config.return_value = mock_cfg
            
            result = await summarizer.call_llm("测试 Prompt")
            # 没有配置提供商时应返回空字符串
            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_summary_with_very_long_content(self, summarizer):
        """测试超长内容的摘要生成"""
        from app.domain.models.session import Session, SessionStatus, Message
        
        # 创建包含超长消息的会话
        long_content = "这是很长的内容。 " * 1000
        session = Session(
            session_id="long-session",
            proxy_key="tw-key",
            status=SessionStatus.ACTIVE,
            messages=[Message(role="user", content=long_content)],
            created_at=datetime.utcnow().isoformat()
        )
        
        with patch.object(summarizer, 'call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "简短摘要"
            
            summary = await summarizer.generate_summary(session, max_length=100)
            
            assert len(summary) <= 100

    def test_prompt_template_variables(self, summarizer):
        """测试 Prompt 模板变量替换"""
        messages = [
            {"role": "user", "content": "测试1"},
            {"role": "assistant", "content": "回复1"}
        ]
        
        prompt = summarizer.build_prompt(
            messages,
            template="对话: {content}\n请用50字摘要:"
        )
        
        assert "对话:" in prompt
        assert "{content}" not in prompt  # 变量应被替换


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
