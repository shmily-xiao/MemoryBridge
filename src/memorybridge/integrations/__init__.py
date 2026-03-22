"""
Agent Integrations - Agent 框架集成模块

支持的集成:
- LangChain Memory
- CrewAI Memory  
- Claude Code Integration
"""

from .claude_code import ClaudeCodeIntegration
from .crewai_memory import CrewAIMemory, CrewAIMemoryAdapter
from .langchain_memory import MemoryBridgeMemory

__all__ = [
    "MemoryBridgeMemory",
    "CrewAIMemory",
    "CrewAIMemoryAdapter",
    "ClaudeCodeIntegration",
]
