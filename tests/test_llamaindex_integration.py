"""
测试 LlamaIndex Memory 集成
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from memorybridge.integrations.llamaindex_memory import LlamaIndexMemory


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def llama_memory(temp_db):
    return LlamaIndexMemory(
        session_id="test_session_001",
        backend="sqlite",
        db_path=temp_db,
    )


class TestLlamaIndexMemory:
    """测试 LlamaIndex Memory 集成"""
    
    def test_init(self, llama_memory):
        assert llama_memory.session_id == "test_session_001"
        assert llama_memory.max_messages == 100
    
    def test_add_message(self, llama_memory):
        async def run_test():
            memory = await llama_memory.add_message(
                role="user",
                content="什么是机器学习？",
            )
            assert memory is not None
            assert memory.content == "什么是机器学习？"
            assert len(llama_memory._messages) == 1
        asyncio.run(run_test())
    
    def test_get_chat_history(self, llama_memory):
        async def run_test():
            await llama_memory.add_message("user", "问题 1")
            await llama_memory.add_message("assistant", "回答 1")
            
            history = await llama_memory.get_chat_history(limit=10)
            assert len(history) == 2
            assert history[0]["role"] == "user"
        asyncio.run(run_test())
    
    def test_retrieve_context(self, llama_memory):
        async def run_test():
            await llama_memory.add_message("user", "Python 是一种编程语言")
            await llama_memory.add_message("assistant", "是的，Python 用于数据科学")
            
            context = await llama_memory.retrieve_context("Python", top_k=2)
            assert "relevant_memories" in context
            assert "chat_history" in context
        asyncio.run(run_test())
    
    def test_clear_session(self, llama_memory):
        async def run_test():
            for i in range(5):
                await llama_memory.add_message("user", f"消息{i}")
            
            count = await llama_memory.clear_session()
            assert count == 5
            assert len(llama_memory._messages) == 0
        asyncio.run(run_test())
    
    def test_export_session_json(self, llama_memory):
        async def run_test():
            await llama_memory.add_message("user", "你好")
            await llama_memory.add_message("assistant", "有什么可以帮你")
            
            data = await llama_memory.export_session(format="json")
            assert "你好" in data
        asyncio.run(run_test())
    
    def test_export_session_markdown(self, llama_memory):
        async def run_test():
            await llama_memory.add_message("user", "问题")
            
            data = await llama_memory.export_session(format="markdown")
            assert "# Session:" in data
            assert "**user**: 问题" in data
        asyncio.run(run_test())
    
    def test_message_cache_limit(self, llama_memory):
        async def run_test():
            for i in range(150):
                await llama_memory.add_message("user", f"消息{i}")
            assert len(llama_memory._messages) <= llama_memory.max_messages
        asyncio.run(run_test())
    
    def test_repr(self, llama_memory):
        repr_str = repr(llama_memory)
        assert "LlamaIndexMemory" in repr_str
        assert "test_session_001" in repr_str


class TestLlamaIndexMemoryChatFormat:
    """测试 LlamaIndex 格式转换"""
    
    def test_get_chat_history_llama_format(self, llama_memory):
        async def run_test():
            await llama_memory.add_message("user", "问题")
            await llama_memory.add_message("assistant", "回答")
            
            history = await llama_memory.get_chat_history(as_llama_format=True)
            assert len(history) == 2
            assert "role" in history[0]
            assert "content" in history[0]
        asyncio.run(run_test())
    
    def test_get_chat_history_standard_format(self, llama_memory):
        async def run_test():
            await llama_memory.add_message("user", "问题")
            
            history = await llama_memory.get_chat_history(as_llama_format=False)
            assert "timestamp" in history[0]
        asyncio.run(run_test())
