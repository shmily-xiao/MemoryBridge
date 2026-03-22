"""
Agent Integrations 测试
"""

import unittest
import tempfile
from pathlib import Path


class TestCrewAIMemory(unittest.TestCase):
    """CrewAI Memory 测试"""

    def setUp(self):
        try:
            from memorybridge.integrations.crewai_memory import CrewAIMemory
        except ImportError:
            self.skipTest("CrewAI not available")
        self.CrewAIMemory = CrewAIMemory

    def test_init(self):
        """测试初始化"""
        memory = self.CrewAIMemory(
            crew_id="test_crew",
            agent_id="agent_1",
        )
        
        self.assertEqual(memory.crew_id, "test_crew")
        self.assertEqual(memory.agent_id, "agent_1")

    def test_save(self):
        """测试保存记忆"""
        memory = self.CrewAIMemory(crew_id="test_crew")
        
        memory_id = memory.save(
            content="Test content",
            metadata={"key": "value"},
        )
        
        self.assertIsNotNone(memory_id)

    def test_save_task_result(self):
        """测试保存任务结果"""
        memory = self.CrewAIMemory(crew_id="test_crew")
        
        memory_id = memory.save_task_result(
            task_description="Research topic",
            result="Found interesting information",
            agent_role="Researcher",
        )
        
        self.assertIsNotNone(memory_id)

    def test_save_agent_interaction(self):
        """测试保存 Agent 交互"""
        memory = self.CrewAIMemory(crew_id="test_crew")
        
        memory_id = memory.save_agent_interaction(
            agent_role="Writer",
            action="Write article",
            observation="Article completed",
        )
        
        self.assertIsNotNone(memory_id)

    def test_search(self):
        """测试搜索记忆"""
        memory = self.CrewAIMemory(crew_id="test_crew")
        
        # 先保存
        memory.save(content="Python programming", metadata={})
        
        # 搜索
        results = memory.search("Python", limit=5)
        
        self.assertIsInstance(results, list)

    def test_get_context(self):
        """测试获取上下文"""
        memory = self.CrewAIMemory(crew_id="test_crew")
        
        context = memory.get_context("test", max_results=3)
        
        self.assertIsInstance(context, str)


class TestClaudeCodeIntegration(unittest.TestCase):
    """Claude Code 集成测试"""

    def setUp(self):
        from memorybridge.integrations.claude_code import ClaudeCodeIntegration
        self.ClaudeCodeIntegration = ClaudeCodeIntegration
        self.project_id = "test_project"

    def test_init(self):
        """测试初始化"""
        integration = self.ClaudeCodeIntegration(
            project_id=self.project_id,
        )
        
        self.assertEqual(integration.project_id, self.project_id)

    def test_save_code_context(self):
        """测试保存代码上下文"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        code = """
def hello():
    print("Hello, World!")
"""
        memory_id = integration.save_code_context(
            file_path="src/hello.py",
            content=code,
            description="Hello World function",
        )
        
        self.assertIsNotNone(memory_id)

    def test_save_code_context_detects_language(self):
        """测试自动检测语言"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        code = "console.log('Hello');"
        
        memory_id = integration.save_code_context(
            file_path="src/hello.js",
            content=code,
        )
        
        self.assertIsNotNone(memory_id)

    def test_save_architecture_decision(self):
        """测试保存架构决策"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        memory_id = integration.save_architecture_decision(
            title="Use SQLite for storage",
            context="Need simple local storage",
            decision="Chose SQLite over MongoDB",
            consequences="Easier deployment, limited scalability",
        )
        
        self.assertIsNotNone(memory_id)

    def test_save_development_note(self):
        """测试保存开发笔记"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        memory_id = integration.save_development_note(
            note="Remember to update dependencies weekly",
            category="todo",
        )
        
        self.assertIsNotNone(memory_id)

    def test_get_relevant_context(self):
        """测试获取相关上下文"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        # 先保存一些内容
        integration.save_code_context(
            file_path="src/api.py",
            content="def create_user(): pass",
            description="User creation API",
        )
        
        # 获取上下文
        context = integration.get_relevant_context("user API")
        
        self.assertIsInstance(context, str)

    def test_get_project_summary(self):
        """测试获取项目摘要"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        # 先保存一些内容
        integration.save_code_context(
            file_path="src/main.py",
            content="print('hello')",
        )
        
        summary = integration.get_project_summary()
        
        self.assertIn("project_id", summary)
        self.assertEqual(summary["project_id"], self.project_id)
        self.assertIn("total_memories", summary)
        self.assertIn("code_files", summary)

    def test_export_project(self):
        """测试导出项目"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        # 先保存一些内容
        integration.save_code_context(
            file_path="src/test.py",
            content="test",
        )
        
        # 导出
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name
        
        try:
            result_path = integration.export_project(output_path)
            
            self.assertTrue(Path(result_path).exists())
            
            import json
            with open(result_path) as f:
                data = json.load(f)
            
            self.assertIn("project_id", data)
            self.assertIn("memories", data)
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_detect_language(self):
        """测试语言检测"""
        integration = self.ClaudeCodeIntegration(project_id=self.project_id)
        
        # 测试各种扩展名
        self.assertEqual(
            integration._detect_language("test.py"),
            "python"
        )
        self.assertEqual(
            integration._detect_language("test.js"),
            "javascript"
        )
        self.assertEqual(
            integration._detect_language("test.ts"),
            "typescript"
        )
        self.assertEqual(
            integration._detect_language("test.unknown"),
            "text"
        )


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
        if not self.langchain_available:
            self.skipTest("LangChain not installed")
        
        from memorybridge.integrations.langchain_memory import MemoryBridgeMemory
        self.MemoryBridgeMemory = MemoryBridgeMemory

    def test_init(self):
        """测试初始化"""
        memory = self.MemoryBridgeMemory()
        
        self.assertEqual(memory.backend, "sqlite")
        self.assertEqual(memory.memory_key, "history")

    def test_memory_variables(self):
        """测试记忆变量"""
        memory = self.MemoryBridgeMemory()
        self.assertEqual(memory.memory_variables, ["history"])

    def test_save_context(self):
        """测试保存上下文"""
        memory = self.MemoryBridgeMemory()
        
        inputs = {"input": "Hello"}
        outputs = {"output": "Hi there!"}
        
        # 应该不抛出异常
        memory.save_context(inputs, outputs)

    def test_search_memories(self):
        """测试搜索记忆"""
        memory = self.MemoryBridgeMemory()
        
        results = memory.search_memories("test", limit=5)
        
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
