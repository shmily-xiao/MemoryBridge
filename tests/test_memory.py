"""
Memory 数据模型测试
"""

import pytest
from datetime import datetime

from src.memorybridge.core.memory import Memory, MemoryType, MemoryPriority


class TestMemoryModel:
    """Memory 模型测试"""

    def test_create_memory(self):
        """测试创建记忆"""
        memory = Memory(
            content="测试内容",
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.P1,
        )

        assert memory.content == "测试内容"
        assert memory.memory_type == MemoryType.LONG_TERM
        assert memory.priority == MemoryPriority.P1
        assert memory.id is not None
        assert isinstance(memory.created_at, datetime)

    def test_memory_to_dict(self, sample_memory):
        """测试转换为字典"""
        mem_dict = sample_memory.to_dict()

        assert mem_dict["content"] == "测试记忆内容"
        assert mem_dict["memory_type"] == "long_term"
        assert mem_dict["priority"] == "p1"
        assert "id" in mem_dict
        assert "created_at" in mem_dict

    def test_memory_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test-123",
            "content": "测试内容",
            "memory_type": "long_term",
            "priority": "p1",
            "metadata": {"key": "value"},
            "tags": ["tag1", "tag2"],
            "created_at": "2026-03-21T10:00:00",
            "updated_at": None,
            "embedding": None,
        }

        memory = Memory.from_dict(data)

        assert memory.id == "test-123"
        assert memory.content == "测试内容"
        assert memory.memory_type == MemoryType.LONG_TERM
        assert memory.priority == MemoryPriority.P1
        assert memory.metadata == {"key": "value"}
        assert memory.tags == ["tag1", "tag2"]

    def test_memory_update(self, sample_memory):
        """测试更新记忆"""
        sample_memory.update(content="新内容", tags=["new", "tags"])

        assert sample_memory.content == "新内容"
        assert sample_memory.tags == ["new", "tags"]
        assert sample_memory.updated_at is not None

    def test_memory_str(self, sample_memory):
        """测试字符串表示"""
        str_repr = str(sample_memory)
        assert "Memory" in str_repr
        assert "long_term" in str_repr

    def test_memory_repr(self, sample_memory):
        """测试详细字符串表示"""
        repr_str = repr(sample_memory)
        assert "Memory" in repr_str
        assert "测试记忆内容" in repr_str
