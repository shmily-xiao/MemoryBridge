"""
SQLite 存储后端测试
"""

import pytest
import asyncio

from src.memorybridge.core.memory import MemoryType, MemoryPriority


class TestSQLiteStorage:
    """SQLite 存储测试"""

    def test_init(self, test_db):
        """测试初始化"""
        assert test_db.db_path is not None
        assert "test.db" in test_db.db_path

    @pytest.mark.asyncio
    async def test_add_memory(self, test_db):
        """测试添加记忆"""
        memory = await test_db.add(
            content="测试内容",
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.P1,
            tags=["测试"],
        )

        assert memory.content == "测试内容"
        assert memory.memory_type == MemoryType.LONG_TERM
        assert memory.priority == MemoryPriority.P1
        assert memory.tags == ["测试"]
        assert memory.id is not None

    @pytest.mark.asyncio
    async def test_get_memory(self, test_db):
        """测试获取记忆"""
        # 先添加
        memory = await test_db.add(content="测试内容")

        # 再获取
        retrieved = await test_db.get(memory.id)

        assert retrieved is not None
        assert retrieved.id == memory.id
        assert retrieved.content == "测试内容"

    @pytest.mark.asyncio
    async def test_get_not_found(self, test_db):
        """测试获取不存在的记忆"""
        result = await test_db.get("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_memory(self, test_db):
        """测试更新记忆"""
        memory = await test_db.add(content="原始内容")

        updated = await test_db.update(
            memory_id=memory.id,
            content="新内容",
            tags=["更新后"],
        )

        assert updated.content == "新内容"
        assert updated.tags == ["更新后"]
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_delete_memory(self, test_db):
        """测试删除记忆"""
        memory = await test_db.add(content="待删除")

        success = await test_db.delete(memory.id)
        assert success is True

        # 验证已删除
        retrieved = await test_db.get(memory.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_search_memory(self, test_db):
        """测试搜索记忆"""
        await test_db.add(content="Python 编程语言")
        await test_db.add(content="Java 编程语言")
        await test_db.add(content="机器学习算法")

        # 搜索 Python
        results = await test_db.search(query="Python")
        assert len(results) == 1
        assert "Python" in results[0].content

        # 搜索编程语言
        results = await test_db.search(query="编程语言", limit=5)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_memories(self, test_db):
        """测试列出记忆"""
        for i in range(5):
            await test_db.add(content=f"记忆{i}")

        memories = await test_db.list(limit=10)
        assert len(memories) == 5

        # 测试 limit
        memories = await test_db.list(limit=3)
        assert len(memories) == 3

    @pytest.mark.asyncio
    async def test_list_by_type(self, test_db):
        """测试按类型列出记忆"""
        await test_db.add(content="Session 记忆", memory_type=MemoryType.SESSION)
        await test_db.add(content="长期记忆", memory_type=MemoryType.LONG_TERM)

        session_memories = await test_db.list(memory_type=MemoryType.SESSION)
        assert len(session_memories) == 1
        assert session_memories[0].memory_type == MemoryType.SESSION

    @pytest.mark.asyncio
    async def test_count(self, test_db):
        """测试统计数量"""
        await test_db.add(content="记忆 1")
        await test_db.add(content="记忆 2")

        total = await test_db.count()
        assert total == 2

    @pytest.mark.asyncio
    async def test_export_import(self, test_db):
        """测试导出导入"""
        await test_db.add(content="记忆 1", tags=["test"])
        await test_db.add(content="记忆 2")

        # 导出
        exported = await test_db.export(format="json")
        assert "记忆 1" in exported
        assert "记忆 2" in exported

        # 导入到新数据库
        import asyncio
        from src.memorybridge.storage.sqlite import SQLiteStorage
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_db = SQLiteStorage(tmp.name)

            count = await tmp_db.import_memories(exported, format="json")
            assert count == 2

            total = await tmp_db.count()
            assert total == 2

            os.unlink(tmp.name)

    @pytest.mark.asyncio
    async def test_search_with_filters(self, test_db):
        """测试带过滤的搜索"""
        await test_db.add(content="P0 重要", priority=MemoryPriority.P0)
        await test_db.add(content="P1 普通", priority=MemoryPriority.P1)

        # 按优先级过滤
        results = await test_db.search(
            query="重要",
            filters={"priority": "p0"},
        )
        assert len(results) == 1
        assert results[0].priority == MemoryPriority.P0
