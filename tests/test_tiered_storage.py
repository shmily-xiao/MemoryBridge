"""
测试分层存储
"""

import pytest
import asyncio
from pathlib import Path
import tempfile

from memorybridge.core.memory import Memory, MemoryType, MemoryPriority
from memorybridge.storage.sqlite import SQLiteStorage
from memorybridge.storage.tiered_storage import TieredStorage


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def tiered_storage(temp_db):
    """创建分层存储（使用两个 SQLite 模拟热/温存储）"""
    hot_storage = SQLiteStorage(db_path=temp_db.replace(".db", "_hot.db"))
    warm_storage = SQLiteStorage(db_path=temp_db)
    
    storage = TieredStorage(
        hot_storage=hot_storage,
        warm_storage=warm_storage,
    )
    
    yield storage
    
    # 清理
    Path(temp_db.replace(".db", "_hot.db")).unlink(missing_ok=True)


class TestTieredStorage:
    """测试分层存储"""

    def test_add_p1_memory(self, tiered_storage):
        """测试添加 P1 优先级记忆（应该到热存储）"""
        memory = asyncio.run(
            tiered_storage.add(
                content="重要记忆",
                priority=MemoryPriority.P1,
                memory_type=MemoryType.LONG_TERM,
            )
        )
        
        assert memory.content == "重要记忆"
        assert memory.priority == MemoryPriority.P1

    def test_add_p2_memory(self, tiered_storage):
        """测试添加 P2 优先级记忆（应该到温存储）"""
        memory = asyncio.run(
            tiered_storage.add(
                content="普通记忆",
                priority=MemoryPriority.P2,
                memory_type=MemoryType.LONG_TERM,
            )
        )
        
        assert memory.content == "普通记忆"
        assert memory.priority == MemoryPriority.P2

    def test_add_session_memory(self, tiered_storage):
        """测试添加 Session 记忆（应该到热存储）"""
        memory = asyncio.run(
            tiered_storage.add(
                content="Session 记忆",
                memory_type=MemoryType.SESSION,
            )
        )
        
        assert memory.memory_type == MemoryType.SESSION

    def test_get_memory(self, tiered_storage):
        """测试获取记忆"""
        # 添加记忆
        memory = asyncio.run(
            tiered_storage.add(
                content="测试记忆",
                priority=MemoryPriority.P1,
            )
        )
        
        # 获取记忆
        retrieved = asyncio.run(tiered_storage.get(memory.id))
        
        assert retrieved is not None
        assert retrieved.content == "测试记忆"

    def test_search_memories(self, tiered_storage):
        """测试搜索记忆"""
        # 添加多条记忆
        asyncio.run(tiered_storage.add(content="Python 编程", tags=["python"]))
        asyncio.run(tiered_storage.add(content="Java 编程", tags=["java"]))
        asyncio.run(tiered_storage.add(content="Python 框架", tags=["python", "framework"]))
        
        # 搜索
        results = asyncio.run(tiered_storage.search("Python"))
        
        assert len(results) >= 2
        assert all("Python" in m.content for m in results)

    def test_delete_memory(self, tiered_storage):
        """测试删除记忆"""
        memory = asyncio.run(
            tiered_storage.add(content="待删除记忆")
        )
        
        success = asyncio.run(tiered_storage.delete(memory.id))
        assert success is True
        
        # 验证已删除
        deleted = asyncio.run(tiered_storage.get(memory.id))
        assert deleted is None

    def test_update_memory(self, tiered_storage):
        """测试更新记忆"""
        memory = asyncio.run(
            tiered_storage.add(content="原始内容")
        )
        
        # 更新
        updated = asyncio.run(
            tiered_storage.update(
                memory_id=memory.id,
                content="更新后的内容",
            )
        )
        
        assert updated.content == "更新后的内容"

    def test_list_memories(self, tiered_storage):
        """测试列出记忆"""
        # 添加多条记忆
        for i in range(5):
            asyncio.run(tiered_storage.add(content=f"记忆{i}"))
        
        # 列出
        memories = asyncio.run(tiered_storage.list(limit=10))
        
        assert len(memories) == 5

    def test_count_memories(self, tiered_storage):
        """测试统计记忆数量"""
        # 添加记忆
        asyncio.run(tiered_storage.add(content="记忆 1"))
        asyncio.run(tiered_storage.add(content="记忆 2"))
        
        # 统计
        count = asyncio.run(tiered_storage.count())
        
        assert count == 2

    def test_export_import(self, tiered_storage):
        """测试导出导入"""
        # 添加记忆
        asyncio.run(tiered_storage.add(content="记忆 1", tags=["test"]))
        asyncio.run(tiered_storage.add(content="记忆 2", tags=["test"]))
        
        # 导出
        data = asyncio.run(tiered_storage.export(format="json"))
        
        # 导入到新存储
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            new_storage = SQLiteStorage(db_path=f.name)
        
        count = asyncio.run(new_storage.import_memories(data, format="json"))
        
        assert count == 2
        
        # 清理
        Path(f.name).unlink(missing_ok=True)

    def test_tiering_report(self, tiered_storage):
        """测试分层报告"""
        # 添加不同优先级的记忆
        asyncio.run(tiered_storage.add(content="P1 记忆", priority=MemoryPriority.P1))
        asyncio.run(tiered_storage.add(content="P2 记忆", priority=MemoryPriority.P2))
        
        # 获取报告
        report = asyncio.run(tiered_storage.tiering_report())
        
        assert "hot_count" in report
        assert "warm_count" in report
        assert "total_count" in report
        assert report["total_count"] == 2
