"""
SQLite 存储后端实现

使用 SQLite 作为主存储，支持零配置和本地持久化
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.memory import Memory, MemoryPriority, MemoryType
from ..core.service import MemoryService


class SQLiteStorage(MemoryService):
    """SQLite 存储后端实现

    特点:
    - 零配置
    - 本地文件存储
    - 支持全文搜索
    - 事务安全
    """

    def __init__(self, db_path: Optional[str] = None):
        """初始化 SQLite 存储

        Args:
            db_path: 数据库文件路径 (默认 ~/.memorybridge/memories.db)
        """
        if db_path is None:
            db_dir = Path.home() / ".memorybridge"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "memories.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # 创建 memories 表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL CHECK (memory_type IN ('session', 'long_term')),
                    priority TEXT NOT NULL CHECK (priority IN ('p0', 'p1', 'p2', 'p3')),
                    metadata JSON,
                    tags JSON,
                    embedding JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON memories(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)")

            conn.commit()

    async def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        priority: MemoryPriority = MemoryPriority.P1,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """添加记忆"""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            priority=priority,
            metadata=metadata or {},
            tags=tags or [],
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO memories (id, content, memory_type, priority, metadata, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.content,
                    memory.memory_type.value,
                    memory.priority.value,
                    json.dumps(memory.metadata),
                    json.dumps(memory.tags),
                    memory.created_at.isoformat(),
                ),
            )
            conn.commit()

        return memory

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """搜索记忆 (支持全文搜索)"""
        filters = filters or {}

        # 构建 WHERE 子句
        where_clauses = []
        params = []

        # 全文搜索 (content 字段)
        where_clauses.append("content LIKE ?")
        params.append(f"%{query}%")

        # 类型过滤
        if "memory_type" in filters:
            where_clauses.append("memory_type = ?")
            params.append(filters["memory_type"])

        # 优先级过滤
        if "priority" in filters:
            where_clauses.append("priority = ?")
            params.append(filters["priority"])

        where_sql = " AND ".join(where_clauses)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"""
                SELECT * FROM memories
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params + [limit],
            )

            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取单条记忆"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_memory(row)
            return None

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE id = ?", (memory_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """更新记忆"""
        # 先获取现有记忆
        memory = await self.get(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        # 更新字段
        if content is not None:
            memory.content = content
        if metadata is not None:
            memory.metadata = metadata
        if tags is not None:
            memory.tags = tags
        memory.updated_at = datetime.utcnow()

        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE memories
                SET content = ?, metadata = ?, tags = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    memory.content,
                    json.dumps(memory.metadata),
                    json.dumps(memory.tags),
                    memory.updated_at.isoformat(),
                    memory_id,
                ),
            )
            conn.commit()

        return memory

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        memory_type: Optional[MemoryType] = None,
    ) -> List[Memory]:
        """列出记忆"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if memory_type:
                cursor = conn.execute(
                    """
                    SELECT * FROM memories
                    WHERE memory_type = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (memory_type.value, limit, offset),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM memories
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )

            rows = cursor.fetchall()
            return [self._row_to_memory(row) for row in rows]

    async def export(self, format: str = "json") -> str:
        """导出记忆"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM memories ORDER BY created_at")
            rows = cursor.fetchall()

            memories = [self._row_to_memory(row).to_dict() for row in rows]

            if format == "json":
                return json.dumps(memories, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

    async def import_memories(self, data: str, format: str = "json") -> int:
        """导入记忆"""
        if format != "json":
            raise ValueError(f"Unsupported format: {format}")

        memories_data = json.loads(data)
        count = 0

        with sqlite3.connect(self.db_path) as conn:
            for mem_dict in memories_data:
                try:
                    memory = Memory.from_dict(mem_dict)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO memories
                        (id, content, memory_type, priority, metadata, tags, embedding, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            memory.id,
                            memory.content,
                            memory.memory_type.value,
                            memory.priority.value,
                            json.dumps(memory.metadata),
                            json.dumps(memory.tags),
                            json.dumps(memory.embedding) if memory.embedding else None,
                            memory.created_at.isoformat(),
                            memory.updated_at.isoformat() if memory.updated_at else None,
                        ),
                    )
                    count += 1
                except Exception as e:
                    print(f"Failed to import memory: {e}")
                    continue

            conn.commit()

        return count

    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """统计记忆数量"""
        with sqlite3.connect(self.db_path) as conn:
            if memory_type:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE memory_type = ?",
                    (memory_type.value,),
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM memories")

            return cursor.fetchone()[0]

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """将数据库行转换为 Memory 对象"""
        return Memory(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            priority=MemoryPriority(row["priority"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            tags=json.loads(row["tags"]) if row["tags"] else [],
            embedding=json.loads(row["embedding"]) if row["embedding"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=(
                datetime.fromisoformat(row["updated_at"])
                if row["updated_at"]
                else None
            ),
        )

    def __repr__(self) -> str:
        return f"SQLiteStorage(db_path='{self.db_path}')"
