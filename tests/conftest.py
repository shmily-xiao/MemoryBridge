"""
测试配置
"""

import pytest


@pytest.fixture
def test_db(tmp_path):
    """创建临时数据库用于测试"""
    from src.memorybridge.storage.sqlite import SQLiteStorage

    db_path = tmp_path / "test.db"
    storage = SQLiteStorage(str(db_path))
    yield storage


@pytest.fixture
def sample_memory():
    """创建示例记忆"""
    from src.memorybridge.core.memory import Memory, MemoryType, MemoryPriority

    return Memory(
        content="测试记忆内容",
        memory_type=MemoryType.LONG_TERM,
        priority=MemoryPriority.P1,
        tags=["测试", "python"],
        metadata={"source": "test"},
    )
