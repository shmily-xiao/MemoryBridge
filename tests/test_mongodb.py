"""
MongoDB 存储后端测试

需要本地 MongoDB 实例运行：
    brew install mongodb-community
    brew services start mongodb-community

或者使用 Docker:
    docker run -d -p 27017:27017 --name mongodb mongo:latest
"""

import asyncio
import os
import unittest
from datetime import datetime

import pytest

from memorybridge.core.memory import Memory, MemoryPriority, MemoryType


class TestMongoDBStorage(unittest.TestCase):
    """MongoDB 存储测试"""

    @classmethod
    def setUpClass(cls):
        """测试前检查 MongoDB 是否可用"""
        try:
            from pymongo import MongoClient
            client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            cls.mongodb_available = True
        except Exception:
            cls.mongodb_available = False

    def setUp(self):
        """每个测试前检查是否跳过"""
        if not self.mongodb_available:
            self.skipTest("MongoDB not available")
        
        from memorybridge.storage.mongodb import MongoDBStorage
        self.storage = MongoDBStorage(
            connection_string="mongodb://localhost:27017",
            database="memorybridge_test",
            collection="memories"
        )

    def tearDown(self):
        """每个测试后清理数据"""
        if self.mongodb_available:
            asyncio.run(self.storage.collection.delete_many({}))

    @classmethod
    def tearDownClass(cls):
        """测试结束后删除测试数据库"""
        if cls.mongodb_available:
            from pymongo import MongoClient
            client = MongoClient("mongodb://localhost:27017")
            client.drop_database("memorybridge_test")

    def test_add_memory(self):
        """测试添加记忆"""
        from memorybridge.storage.mongodb import MongoDBStorage
        
        async def run_test():
            memory = await self.storage.add(
                content="Python 是一种编程语言",
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P1,
                tags=["programming", "python"]
            )
            
            self.assertIsNotNone(memory.id)
            self.assertEqual(memory.content, "Python 是一种编程语言")
            self.assertEqual(memory.memory_type, MemoryType.LONG_TERM)
            self.assertEqual(memory.priority, MemoryPriority.P1)
            self.assertIn("python", memory.tags)
        
        asyncio.run(run_test())

    def test_get_memory(self):
        """测试获取记忆"""
        async def run_test():
            # 先添加
            memory = await self.storage.add(
                content="Test content",
                memory_type=MemoryType.LONG_TERM
            )
            
            # 再获取
            retrieved = await self.storage.get(memory.id)
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.id, memory.id)
            self.assertEqual(retrieved.content, "Test content")
        
        asyncio.run(run_test())

    def test_search_memory(self):
        """测试搜索记忆"""
        async def run_test():
            # 添加多条记忆
            await self.storage.add(content="Python programming", tags=["python"])
            await self.storage.add(content="Java programming", tags=["java"])
            await self.storage.add(content="Python web development", tags=["python", "web"])
            
            # 搜索
            results = await self.storage.search("Python", limit=10)
            
            self.assertGreater(len(results), 0)
            for mem in results:
                self.assertIn("Python", mem.content)
        
        asyncio.run(run_test())

    def test_update_memory(self):
        """测试更新记忆"""
        async def run_test():
            # 添加
            memory = await self.storage.add(
                content="Original content",
                tags=["test"]
            )
            
            # 更新
            updated = await self.storage.update(
                memory_id=memory.id,
                content="Updated content",
                tags=["test", "updated"]
            )
            
            self.assertEqual(updated.content, "Updated content")
            self.assertIn("updated", updated.tags)
        
        asyncio.run(run_test())

    def test_delete_memory(self):
        """测试删除记忆"""
        async def run_test():
            # 添加
            memory = await self.storage.add(content="To be deleted")
            
            # 删除
            result = await self.storage.delete(memory.id)
            self.assertTrue(result)
            
            # 验证已删除
            retrieved = await self.storage.get(memory.id)
            self.assertIsNone(retrieved)
        
        asyncio.run(run_test())

    def test_list_memories(self):
        """测试列出记忆"""
        async def run_test():
            # 添加多条
            for i in range(5):
                await self.storage.add(content=f"Memory {i}")
            
            # 列出
            memories = await self.storage.list(limit=10)
            
            self.assertEqual(len(memories), 5)
        
        asyncio.run(run_test())

    def test_count_memories(self):
        """测试统计记忆数量"""
        async def run_test():
            # 添加
            await self.storage.add(content="Memory 1", memory_type=MemoryType.LONG_TERM)
            await self.storage.add(content="Memory 2", memory_type=MemoryType.SESSION)
            await self.storage.add(content="Memory 3", memory_type=MemoryType.LONG_TERM)
            
            # 统计总数
            total = await self.storage.count()
            self.assertEqual(total, 3)
            
            # 按类型统计
            long_term = await self.storage.count(memory_type=MemoryType.LONG_TERM)
            self.assertEqual(long_term, 2)
        
        asyncio.run(run_test())

    def test_export_import(self):
        """测试导出导入"""
        async def run_test():
            # 添加
            await self.storage.add(content="Export test 1", tags=["test"])
            await self.storage.add(content="Export test 2", tags=["test"])
            
            # 导出
            exported = await self.storage.export(format="json")
            
            # 清空
            await self.storage.collection.delete_many({})
            
            # 导入
            count = await self.storage.import_memories(exported, format="json")
            
            self.assertEqual(count, 2)
            
            # 验证
            memories = await self.storage.list(limit=10)
            self.assertEqual(len(memories), 2)
        
        asyncio.run(run_test())

    def test_search_with_filters(self):
        """测试带过滤条件的搜索"""
        async def run_test():
            # 添加不同类型和优先级的记忆
            await self.storage.add(
                content="Important Python task",
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P0,
                tags=["python", "urgent"]
            )
            await self.storage.add(
                content="Normal Java task",
                memory_type=MemoryType.SESSION,
                priority=MemoryPriority.P2,
                tags=["java"]
            )
            
            # 按类型过滤
            results = await self.storage.search(
                "",
                filters={"memory_type": "long_term"}
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].memory_type, MemoryType.LONG_TERM)
            
            # 按优先级过滤
            results = await self.storage.search(
                "",
                filters={"priority": "p0"}
            )
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].priority, MemoryPriority.P0)
        
        asyncio.run(run_test())

    def test_list_with_type_filter(self):
        """测试按类型列出记忆"""
        async def run_test():
            # 添加不同类型
            await self.storage.add(content="Long term 1", memory_type=MemoryType.LONG_TERM)
            await self.storage.add(content="Long term 2", memory_type=MemoryType.LONG_TERM)
            await self.storage.add(content="Session 1", memory_type=MemoryType.SESSION)
            
            # 只列出 long_term
            memories = await self.storage.list(
                limit=10,
                memory_type=MemoryType.LONG_TERM
            )
            
            self.assertEqual(len(memories), 2)
            for mem in memories:
                self.assertEqual(mem.memory_type, MemoryType.LONG_TERM)
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
