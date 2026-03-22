"""
LangChain Memory 集成测试

需要安装 langchain:
    pip install langchain langchain-core
"""

import unittest
from unittest.mock import Mock, patch

import pytest


class TestMemoryBridgeMemory(unittest.TestCase):
    """MemoryBridge LangChain Memory 测试"""

    @classmethod
    def setUpClass(cls):
        """检查 langchain 是否安装"""
        try:
            import langchain
            cls.langchain_available = True
        except ImportError:
            cls.langchain_available = False

    def setUp(self):
        """每个测试前检查"""
        if not self.langchain_available:
            self.skipTest("LangChain not installed")
        
        from memorybridge.integrations.langchain_memory import MemoryBridgeMemory
        self.MemoryBridgeMemory = MemoryBridgeMemory

    def test_init_default(self):
        """测试默认初始化"""
        memory = self.MemoryBridgeMemory()
        
        self.assertEqual(memory.backend, "sqlite")
        self.assertEqual(memory.memory_key, "history")
        self.assertEqual(memory.input_key, "input")
        self.assertFalse(memory.return_messages)
        self.assertEqual(memory.human_prefix, "Human")
        self.assertEqual(memory.ai_prefix, "AI")

    def test_init_with_params(self):
        """测试带参数初始化"""
        memory = self.MemoryBridgeMemory(
            backend="sqlite",
            memory_key="chat_history",
            input_key="question",
            return_messages=True,
            max_memory_limit=100,
        )
        
        self.assertEqual(memory.memory_key, "chat_history")
        self.assertEqual(memory.input_key, "question")
        self.assertTrue(memory.return_messages)
        self.assertEqual(memory.max_memory_limit, 100)

    def test_memory_variables(self):
        """测试记忆变量"""
        memory = self.MemoryBridgeMemory(memory_key="history")
        self.assertEqual(memory.memory_variables, ["history"])

    def test_load_memory_variables(self):
        """测试加载记忆变量"""
        memory = self.MemoryBridgeMemory()
        
        result = memory.load_memory_variables({})
        
        self.assertIn("history", result)
        self.assertIsInstance(result["history"], str)

    def test_load_memory_variables_return_messages(self):
        """测试返回消息列表"""
        memory = self.MemoryBridgeMemory(return_messages=True)
        
        result = memory.load_memory_variables({})
        
        self.assertIn("history", result)
        self.assertIsInstance(result["history"], list)

    def test_save_context(self):
        """测试保存上下文"""
        memory = self.MemoryBridgeMemory()
        
        inputs = {"input": "你好，我叫小明"}
        outputs = {"output": "你好小明，很高兴认识你！"}
        
        # 应该不抛出异常
        memory.save_context(inputs, outputs)

    def test_save_context_missing_input(self):
        """测试缺少输入时不保存"""
        memory = self.MemoryBridgeMemory()
        
        inputs = {}  # 没有 input
        outputs = {"output": "回复"}
        
        # 应该不抛出异常
        memory.save_context(inputs, outputs)

    def test_clear(self):
        """测试清除记忆"""
        memory = self.MemoryBridgeMemory()
        
        # 应该不抛出异常
        memory.clear()

    def test_search_memories(self):
        """测试搜索记忆"""
        memory = self.MemoryBridgeMemory()
        
        # 先添加一些记忆
        inputs = {"input": "Python 是一种编程语言"}
        outputs = {"output": "是的，Python 是高级编程语言"}
        memory.save_context(inputs, outputs)
        
        # 搜索
        results = memory.search_memories("Python", limit=5)
        
        self.assertIsInstance(results, list)
        # 可能找到也可能找不到，取决于存储

    def test_get_knowledge_context(self):
        """测试获取知识上下文"""
        memory = self.MemoryBridgeMemory()
        
        context = memory.get_knowledge_context("Python", max_results=3)
        
        # 返回字符串（可能为空）
        self.assertIsInstance(context, str)

    def test_integration_with_conversation_chain(self):
        """测试与 LangChain ConversationChain 集成"""
        try:
            from langchain.chains import ConversationChain
            from langchain.llms import FakeListLLM
        except ImportError:
            self.skipTest("LangChain chains not available")
        
        memory = self.MemoryBridgeMemory()
        
        # 使用 FakeLLM 进行测试
        llm = FakeListLLM(responses=["你好！", "我很好，谢谢"])
        
        chain = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=False,
        )
        
        # 运行对话
        response = chain.run("你好")
        self.assertIn(response, ["你好！", "我很好，谢谢"])
        
        # 第二次对话
        response = chain.run("你怎么样")
        self.assertIn(response, ["你好！", "我很好，谢谢"])


class TestMemoryBridgeMemoryMongoDB(unittest.TestCase):
    """MemoryBridge MongoDB 后端测试"""

    @classmethod
    def setUpClass(cls):
        """检查依赖"""
        try:
            import langchain
            from pymongo import MongoClient
            client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            cls.all_available = True
        except Exception:
            cls.all_available = False

    def setUp(self):
        if not self.all_available:
            self.skipTest("LangChain or MongoDB not available")
        
        from memorybridge.integrations.langchain_memory import MemoryBridgeMemory
        self.MemoryBridgeMemory = MemoryBridgeMemory

    def test_init_mongodb_backend(self):
        """测试 MongoDB 后端初始化"""
        memory = self.MemoryBridgeMemory(
            backend="mongodb",
            config={
                "connection_string": "mongodb://localhost:27017",
                "database": "memorybridge_test"
            }
        )
        
        self.assertEqual(memory.backend, "mongodb")

    def test_save_context_mongodb(self):
        """测试 MongoDB 后端保存上下文"""
        memory = self.MemoryBridgeMemory(
            backend="mongodb",
            config={
                "connection_string": "mongodb://localhost:27017",
                "database": "memorybridge_test"
            }
        )
        
        inputs = {"input": "Test message"}
        outputs = {"output": "Test response"}
        
        memory.save_context(inputs, outputs)
        
        # 清理
        memory._storage.collection.delete_many({})


if __name__ == "__main__":
    unittest.main()
