"""
测试 AutoGen Memory 集成
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from memorybridge.integrations.autogen_memory import AutoGenMemory


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def autogen_memory(temp_db):
    return AutoGenMemory(
        conversation_id="test_conv_001",
        agent_name="test_agent",
        backend="sqlite",
        db_path=temp_db,
    )


class TestAutoGenMemory:
    def test_init(self, autogen_memory):
        assert autogen_memory.conversation_id == "test_conv_001"
        assert autogen_memory.agent_name == "test_agent"
    
    def test_save_message(self, autogen_memory):
        async def run_test():
            memory = await autogen_memory.save_message(
                sender="user",
                content="你好，帮我写个 Python 脚本",
                role="user",
            )
            assert memory is not None
            assert memory.content == "你好，帮我写个 Python 脚本"
            assert memory.metadata["conversation_id"] == "test_conv_001"
        asyncio.run(run_test())
    
    def test_get_context(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "消息 1", "user")
            await autogen_memory.save_message("assistant", "回复 1", "assistant")
            context = await autogen_memory.get_context(limit=2)
            assert "messages" in context
            assert len(context["messages"]) <= 2
        asyncio.run(run_test())
    
    def test_get_conversation_history(self, autogen_memory):
        async def run_test():
            for i in range(5):
                await autogen_memory.save_message("user", f"消息{i}", "user")
            history = await autogen_memory.get_conversation_history(limit=10)
            assert len(history) == 5
            assert history[0]["content"] == "消息 4"
        asyncio.run(run_test())
    
    def test_clear_history(self, autogen_memory):
        async def run_test():
            for i in range(3):
                await autogen_memory.save_message("user", f"消息{i}", "user")
            count = await autogen_memory.clear_history()
            assert count == 3
            history = await autogen_memory.get_conversation_history()
            assert len(history) == 0
        asyncio.run(run_test())
    
    def test_export_conversation_json(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "你好", "user")
            await autogen_memory.save_message("assistant", "有什么可以帮你", "assistant")
            data = await autogen_memory.export_conversation(format="json")
            assert "你好" in data
        asyncio.run(run_test())
    
    def test_export_conversation_markdown(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "问题", "user")
            data = await autogen_memory.export_conversation(format="markdown")
            assert "# Conversation:" in data
            assert "**user** (user): 问题" in data
        asyncio.run(run_test())
    
    def test_share_memory_with_agent(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "Python 是一种编程语言", "user")
            shared = await autogen_memory.share_memory_with_agent(
                target_agent_name="researcher_agent",
                memory_query="Python",
                limit=1,
            )
            assert isinstance(shared, list)
        asyncio.run(run_test())
    
    def test_get_shared_memories(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "共享内容", "user")
            shared = await autogen_memory.get_shared_memories()
            assert isinstance(shared, list)
        asyncio.run(run_test())
    
    def test_multiple_messages_order(self, autogen_memory):
        async def run_test():
            for i in range(10):
                await autogen_memory.save_message("user", f"消息{i}", "user")
            history = await autogen_memory.get_conversation_history(limit=20)
            assert len(history) == 10
            assert history[0]["content"] == "消息 9"
            assert history[-1]["content"] == "消息 0"
        asyncio.run(run_test())
    
    def test_message_cache_limit(self, autogen_memory):
        async def run_test():
            for i in range(150):
                await autogen_memory.save_message("user", f"消息{i}", "user")
            assert len(autogen_memory._message_cache) <= autogen_memory.max_history
        asyncio.run(run_test())
    
    def test_repr(self, autogen_memory):
        repr_str = repr(autogen_memory)
        assert "AutoGenMemory" in repr_str
        assert "test_conv_001" in repr_str


class TestAutoGenMemorySearch:
    def test_search_context(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "Python 是一种编程语言，用于数据科学", "user")
            await autogen_memory.save_message("user", "JavaScript 用于 Web 开发", "user")
            context = await autogen_memory.get_context(query="Python", limit=5)
            assert len(context["messages"]) > 0
        asyncio.run(run_test())
    
    def test_get_context_no_query(self, autogen_memory):
        async def run_test():
            await autogen_memory.save_message("user", "重要知识点", "user")
            context = await autogen_memory.get_context()
            assert "messages" in context
        asyncio.run(run_test())
