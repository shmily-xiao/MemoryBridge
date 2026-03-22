"""
存储性能基准测试

测试 SQLite 和 MongoDB 的存储性能
"""

import pytest
import asyncio
import time
from pathlib import Path
import tempfile

from memorybridge.storage.sqlite import SQLiteStorage
from memorybridge.core.memory import Memory, MemoryType, MemoryPriority


@pytest.fixture
def temp_sqlite():
    """创建临时 SQLite 存储"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    storage = SQLiteStorage(db_path=db_path)
    yield storage
    Path(db_path).unlink(missing_ok=True)


class TestStorageBenchmark:
    """存储性能基准测试"""
    
    BENCHMARK_ITERATIONS = 50
    BENCHMARK_LIMIT = 1000  # ops/sec
    
    def test_single_write_performance(self, temp_sqlite):
        """测试单次写入性能"""
        async def run_benchmark():
            times = []
            for i in range(self.BENCHMARK_ITERATIONS):
                start = time.perf_counter()
                await temp_sqlite.add(
                    content=f"测试记忆{i}",
                    memory_type=MemoryType.LONG_TERM,
                    priority=MemoryPriority.P1,
                )
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            ops_per_sec = 1.0 / avg_time
            
            print(f"\n单次写入性能:")
            print(f"  平均耗时：{avg_time*1000:.3f}ms")
            print(f"  操作/秒：{ops_per_sec:.0f} ops/sec")
            
            assert ops_per_sec > self.BENCHMARK_LIMIT * 0.5  # 至少 500 ops/sec
        
        asyncio.run(run_benchmark())
    
    def test_single_read_performance(self, temp_sqlite):
        """测试单次读取性能"""
        async def run_benchmark():
            # 先写入
            memory = await temp_sqlite.add(
                content="测试记忆",
                memory_type=MemoryType.LONG_TERM,
            )
            
            # 测试读取
            times = []
            for _ in range(self.BENCHMARK_ITERATIONS):
                start = time.perf_counter()
                await temp_sqlite.get(memory.id)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            ops_per_sec = 1.0 / avg_time
            
            print(f"\n单次读取性能:")
            print(f"  平均耗时：{avg_time*1000:.3f}ms")
            print(f"  操作/秒：{ops_per_sec:.0f} ops/sec")
            
            assert ops_per_sec > self.BENCHMARK_LIMIT  # 至少 1000 ops/sec
        
        asyncio.run(run_benchmark())
    
    def test_search_performance(self, temp_sqlite):
        """测试搜索性能"""
        async def run_benchmark():
            # 先写入测试数据
            for i in range(100):
                await temp_sqlite.add(
                    content=f"Python 测试记忆{i}",
                    memory_type=MemoryType.LONG_TERM,
                    tags=["python", "test"],
                )
            
            # 测试搜索
            times = []
            for _ in range(self.BENCHMARK_ITERATIONS):
                start = time.perf_counter()
                await temp_sqlite.search("Python", limit=10)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            ops_per_sec = 1.0 / avg_time
            
            print(f"\n搜索性能:")
            print(f"  平均耗时：{avg_time*1000:.3f}ms")
            print(f"  操作/秒：{ops_per_sec:.0f} ops/sec")
        
        asyncio.run(run_benchmark())
