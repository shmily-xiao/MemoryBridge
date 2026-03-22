"""
Agent Integrations - Agent 框架集成

支持的 Agent 框架:
- OpenClaw Skill
- LangChain Memory
- CrewAI Memory
- Claude Code Integration
- AutoGen Memory
"""

__all__ = []

# OpenClaw Skill (always available)
from .. import skill_tools

# LangChain (optional)
try:
    from .langchain_memory import MemoryBridgeMemory
    __all__.append("MemoryBridgeMemory")
except ImportError:
    pass

# CrewAI (optional)
try:
    from .crewai_memory import CrewAIMemory
    __all__.append("CrewAIMemory")
except ImportError:
    pass

# Claude Code (always available)
try:
    from .claude_code import ClaudeCodeIntegration
    __all__.append("ClaudeCodeIntegration")
except ImportError:
    pass

# AutoGen (optional)
try:
    from .autogen_memory import AutoGenMemory
    __all__.append("AutoGenMemory")
except ImportError:
    pass
