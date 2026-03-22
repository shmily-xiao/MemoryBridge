"""
Claude Code 集成

将 MemoryBridge 集成到 Claude Code (Anthropic 的 CLI 工具) 中，支持:
- 项目上下文记忆
- 代码知识库
- 跨会话记忆

Usage:
    # 在 Claude Code 会话中使用
    from memorybridge.integrations import ClaudeCodeIntegration
    
    integration = ClaudeCodeIntegration(project_id="my_project")
    
    # 保存代码上下文
    integration.save_code_context(
        file_path="src/main.py",
        content=code_content,
        description="主入口文件"
    )
    
    # 获取相关上下文
    context = integration.get_relevant_context("如何添加新的 API 端点？")
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.memory import MemoryType, MemoryPriority
from ..storage.factory import create_storage


class ClaudeCodeIntegration:
    """Claude Code 集成
    
    为 Claude Code 提供项目级别的记忆能力，支持：
    - 代码文件上下文存储
    - 项目结构记忆
    - 开发决策记录
    - 跨会话知识共享
    
    Attributes:
        project_id: 项目标识符
        backend: 存储后端类型
        config: 存储后端配置
        auto_index: 是否自动索引代码文件
        
    Examples:
        # 基础使用
        integration = ClaudeCodeIntegration(project_id="my_app")
        
        # 保存代码上下文
        integration.save_code_context(
            file_path="src/api.py",
            content=open("src/api.py").read(),
            description="API 路由定义"
        )
        
        # 获取相关上下文
        context = integration.get_relevant_context("添加新的用户端点")
    """
    
    def __init__(
        self,
        project_id: str,
        backend: str = "sqlite",
        config: Optional[Dict[str, Any]] = None,
        auto_index: bool = False,
    ):
        """初始化 Claude Code 集成
        
        Args:
            project_id: 项目标识符
            backend: 存储后端类型
            config: 存储后端配置
            auto_index: 是否自动索引代码文件
        """
        self.project_id = project_id
        self.backend = backend
        self.config = config or {}
        self.auto_index = auto_index
        
        self._storage = create_storage(backend, config)
        self._ensure_project_metadata()
    
    def _ensure_project_metadata(self):
        """确保项目元数据存在"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 检查是否已有项目元数据
        memories = loop.run_until_complete(
            self._storage.search(
                query=f"project:{self.project_id}",
                limit=1,
                filters={},
            )
        )
        
        if not memories:
            # 创建项目元数据
            loop.run_until_complete(
                self._storage.add(
                    content=f"Project: {self.project_id}",
                    metadata={
                        "type": "project_metadata",
                        "project_id": self.project_id,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                    memory_type=MemoryType.LONG_TERM,
                    priority=MemoryPriority.P1,
                    tags=["project", "metadata", self.project_id],
                )
            )
    
    def save_code_context(
        self,
        file_path: str,
        content: str,
        description: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """保存代码上下文
        
        Args:
            file_path: 文件路径
            content: 文件内容
            description: 文件描述
            language: 编程语言
            
        Returns:
            记忆 ID
        """
        # 检测语言
        if not language:
            language = self._detect_language(file_path)
        
        # 生成文件哈希（用于去重）
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        metadata = {
            "type": "code_context",
            "project_id": self.project_id,
            "file_path": file_path,
            "language": language,
            "content_hash": content_hash,
            "lines": len(content.splitlines()),
        }
        if description:
            metadata["description"] = description
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 检查是否已存在
        existing = loop.run_until_complete(
            self._storage.search(
                query=f"file:{file_path}",
                limit=1,
                filters={},
            )
        )
        
        if existing and existing[0].metadata.get("content_hash") == content_hash:
            # 内容未变化，返回现有 ID
            return existing[0].id
        
        # 保存代码上下文
        memory = loop.run_until_complete(
            self._storage.add(
                content=f"File: {file_path}\nLanguage: {language}\n\n{content}",
                metadata=metadata,
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P2,
                tags=["code", language, self.project_id, file_path],
            )
        )
        
        return memory.id
    
    def save_architecture_decision(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
    ) -> str:
        """保存架构决策记录 (ADR)
        
        Args:
            title: 决策标题
            context: 背景上下文
            decision: 决策内容
            consequences: 后果/影响
            
        Returns:
            记忆 ID
        """
        content = f"""# ADR: {title}

## Context
{context}

## Decision
{decision}

## Consequences
{consequences}
"""
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        memory = loop.run_until_complete(
            self._storage.add(
                content=content,
                metadata={
                    "type": "adr",
                    "project_id": self.project_id,
                    "title": title,
                },
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P1,
                tags=["adr", "architecture", "decision", self.project_id],
            )
        )
        
        return memory.id
    
    def save_development_note(
        self,
        note: str,
        category: str = "general",
    ) -> str:
        """保存开发笔记
        
        Args:
            note: 笔记内容
            category: 分类 (general/todo/issue/solution)
            
        Returns:
            记忆 ID
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        memory = loop.run_until_complete(
            self._storage.add(
                content=note,
                metadata={
                    "type": "dev_note",
                    "project_id": self.project_id,
                    "category": category,
                },
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P3,
                tags=["note", category, self.project_id],
            )
        )
        
        return memory.id
    
    def get_relevant_context(
        self,
        query: str,
        max_results: int = 5,
        include_code: bool = True,
        include_adr: bool = True,
        include_notes: bool = True,
    ) -> str:
        """获取相关上下文（用于 Claude Code 提示）
        
        Args:
            query: 查询关键词
            max_results: 最大结果数
            include_code: 是否包含代码上下文
            include_adr: 是否包含架构决策
            include_notes: 是否包含开发笔记
            
        Returns:
            上下文字符串
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        memories = loop.run_until_complete(
            self._storage.search(
                query=query,
                limit=max_results * 2,  # 获取双倍，过滤后可能不足
                filters={},
            )
        )
        
        # 过滤出当前项目的记忆
        project_memories = [
            m for m in memories
            if m.metadata and m.metadata.get("project_id") == self.project_id
        ]
        
        # 按类型过滤
        filtered = []
        for m in project_memories:
            mem_type = m.metadata.get("type", "")
            if mem_type == "code_context" and include_code:
                filtered.append(m)
            elif mem_type == "adr" and include_adr:
                filtered.append(m)
            elif mem_type == "dev_note" and include_notes:
                filtered.append(m)
            elif not mem_type:
                filtered.append(m)
        
        # 构建上下文
        context_parts = []
        for mem in filtered[:max_results]:
            mem_type = mem.metadata.get("type", "unknown")
            
            if mem_type == "code_context":
                file_path = mem.metadata.get("file_path", "unknown")
                language = mem.metadata.get("language", "unknown")
                context_parts.append(
                    f"```{language} # File: {file_path}\n{mem.content[:500]}..."
                )
            elif mem_type == "adr":
                title = mem.metadata.get("title", "ADR")
                context_parts.append(f"## {title}\n{mem.content[:300]}...")
            else:
                context_parts.append(mem.content[:300])
        
        if not context_parts:
            return ""
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_project_summary(self) -> Dict[str, Any]:
        """获取项目摘要
        
        Returns:
            项目摘要字典
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 获取所有项目相关的记忆
        memories = loop.run_until_complete(
            self._storage.search(
                query=self.project_id,
                limit=100,
                filters={},
            )
        )
        
        # 统计
        stats = {
            "project_id": self.project_id,
            "total_memories": 0,
            "code_files": 0,
            "adrs": 0,
            "notes": 0,
            "languages": set(),
            "total_lines": 0,
        }
        
        for mem in memories:
            if not mem.metadata or mem.metadata.get("project_id") != self.project_id:
                continue
            
            stats["total_memories"] += 1
            mem_type = mem.metadata.get("type", "")
            
            if mem_type == "code_context":
                stats["code_files"] += 1
                stats["total_lines"] += mem.metadata.get("lines", 0)
                lang = mem.metadata.get("language")
                if lang:
                    stats["languages"].add(lang)
            elif mem_type == "adr":
                stats["adrs"] += 1
            elif mem_type == "dev_note":
                stats["notes"] += 1
        
        # 转换集合为列表
        stats["languages"] = list(stats["languages"])
        
        return stats
    
    def export_project(self, output_path: str) -> str:
        """导出项目记忆
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 获取所有项目相关的记忆
        memories = loop.run_until_complete(
            self._storage.search(
                query=self.project_id,
                limit=1000,
                filters={},
            )
        )
        
        # 过滤
        project_memories = [
            m.to_dict() for m in memories
            if m.metadata and m.metadata.get("project_id") == self.project_id
        ]
        
        # 导出
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, "w", encoding="utf-8") as f:
            json.dump({
                "project_id": self.project_id,
                "exported_at": datetime.utcnow().isoformat(),
                "memories": project_memories,
                "summary": self.get_project_summary(),
            }, f, indent=2, ensure_ascii=False)
        
        return str(output)
    
    def _detect_language(self, file_path: str) -> str:
        """检测文件语言
        
        Args:
            file_path: 文件路径
            
        Returns:
            语言名称
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "cpp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".cs": "csharp",
            ".fs": "fsharp",
            ".ex": "elixir",
            ".erl": "erlang",
            ".hs": "haskell",
            ".clj": "clojure",
            ".exs": "elixir",
            ".vue": "vue",
            ".svelte": "svelte",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".less": "less",
            ".sql": "sql",
            ".sh": "bash",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".xml": "xml",
        }
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "text")
