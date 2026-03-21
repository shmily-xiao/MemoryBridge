"""
MemoryBridge Skill Tools - OpenClaw 集成工具

提供 9 个记忆管理工具，支持跨 Agent 记忆共享
"""

import sys
from pathlib import Path
from typing import Optional

# 动态导入 MemoryBridge
memorybridge_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(memorybridge_path))

from memorybridge.storage.sqlite import SQLiteStorage
from memorybridge.core.memory import MemoryType, MemoryPriority
import asyncio


def get_storage(db_path: Optional[str] = None) -> SQLiteStorage:
    """获取存储实例
    
    Args:
        db_path: 数据库路径（可选，默认 ~/.memorybridge/memories.db）
    
    Returns:
        SQLiteStorage 实例
    """
    if db_path:
        return SQLiteStorage(db_path)
    return SQLiteStorage()


def memory_add(
    content: str,
    type: str = "long_term",
    priority: str = "p1",
    tags: Optional[str] = None,
    db_path: Optional[str] = None
) -> dict:
    """添加记忆
    
    Args:
        content: 记忆内容（必填）
        type: 记忆类型 session/long_term（默认 long_term）
        priority: 优先级 p0/p1/p2/p3（默认 p1）
        tags: 标签，逗号分隔（可选）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "memory": dict, "message": str}
    """
    storage = get_storage(db_path)
    memory = asyncio.run(
        storage.add(
            content=content,
            memory_type=MemoryType(type),
            priority=MemoryPriority(priority),
            tags=tags.split(",") if tags else []
        )
    )
    return {
        "success": True,
        "memory": memory.to_dict(),
        "message": f"记忆添加成功：{memory.id[:8]}"
    }


def memory_search(
    query: str,
    limit: int = 10,
    type: Optional[str] = None,
    db_path: Optional[str] = None
) -> dict:
    """搜索记忆
    
    Args:
        query: 搜索关键词（必填）
        limit: 返回数量（默认 10）
        type: 类型过滤 session/long_term（可选）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "count": int, "memories": [dict]}
    """
    storage = get_storage(db_path)
    filters = {"memory_type": type} if type else {}
    memories = asyncio.run(storage.search(query=query, limit=limit, filters=filters))
    return {
        "success": True,
        "count": len(memories),
        "memories": [m.to_dict() for m in memories]
    }


def memory_list(
    limit: int = 20,
    type: Optional[str] = None,
    db_path: Optional[str] = None
) -> dict:
    """列出记忆
    
    Args:
        limit: 返回数量（默认 20）
        type: 类型过滤（可选）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "count": int, "memories": [dict]}
    """
    storage = get_storage(db_path)
    memory_type = MemoryType(type) if type else None
    memories = asyncio.run(storage.list(limit=limit, memory_type=memory_type))
    return {
        "success": True,
        "count": len(memories),
        "memories": [m.to_dict() for m in memories]
    }


def memory_get(memory_id: str, db_path: Optional[str] = None) -> dict:
    """获取记忆详情
    
    Args:
        memory_id: 记忆 ID（必填）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "memory": dict} or {"success": False, "error": str}
    """
    storage = get_storage(db_path)
    memory = asyncio.run(storage.get(memory_id))
    if memory:
        return {"success": True, "memory": memory.to_dict()}
    return {"success": False, "error": f"未找到记忆：{memory_id}"}


def memory_update(
    memory_id: str,
    content: Optional[str] = None,
    tags: Optional[str] = None,
    db_path: Optional[str] = None
) -> dict:
    """更新记忆
    
    Args:
        memory_id: 记忆 ID（必填）
        content: 新内容（可选）
        tags: 新标签，逗号分隔（可选）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "memory": dict, "message": str} or {"success": False, "error": str}
    """
    storage = get_storage(db_path)
    try:
        memory = asyncio.run(
            storage.update(
                memory_id=memory_id,
                content=content,
                tags=tags.split(",") if tags else None
            )
        )
        return {
            "success": True,
            "memory": memory.to_dict(),
            "message": f"记忆更新成功：{memory.id[:8]}"
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def memory_delete(memory_id: str, db_path: Optional[str] = None) -> dict:
    """删除记忆
    
    Args:
        memory_id: 记忆 ID（必填）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    storage = get_storage(db_path)
    success = asyncio.run(storage.delete(memory_id))
    return {
        "success": success,
        "message": f"记忆已删除：{memory_id[:8]}" if success else f"未找到记忆：{memory_id}"
    }


def memory_export(
    output: Optional[str] = None,
    db_path: Optional[str] = None
) -> dict:
    """导出记忆
    
    Args:
        output: 输出文件路径（可选，不提供则返回 JSON 字符串）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "file": str, "message": str} or {"success": True, "data": str}
    """
    storage = get_storage(db_path)
    data = asyncio.run(storage.export(format="json"))
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(data)
        return {"success": True, "file": output, "message": f"已导出到：{output}"}
    return {"success": True, "data": data}


def memory_import(input: str, db_path: Optional[str] = None) -> dict:
    """导入记忆
    
    Args:
        input: 输入文件路径（必填）
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "count": int, "message": str}
    """
    storage = get_storage(db_path)
    with open(input, "r", encoding="utf-8") as f:
        data = f.read()
    count = asyncio.run(storage.import_memories(data, format="json"))
    return {"success": True, "count": count, "message": f"成功导入 {count} 条记忆"}


def memory_status(db_path: Optional[str] = None) -> dict:
    """查看系统状态
    
    Args:
        db_path: 数据库路径（可选）
    
    Returns:
        dict: {"success": bool, "total": int, "session_count": int, "long_term_count": int, "db_path": str}
    """
    storage = get_storage(db_path)
    total = asyncio.run(storage.count())
    session_count = asyncio.run(storage.count(MemoryType.SESSION))
    long_term_count = asyncio.run(storage.count(MemoryType.LONG_TERM))
    return {
        "success": True,
        "total": total,
        "session_count": session_count,
        "long_term_count": long_term_count,
        "db_path": storage.db_path
    }


# 工具注册表（用于动态加载）
TOOLS = {
    "memory_add": memory_add,
    "memory_search": memory_search,
    "memory_list": memory_list,
    "memory_get": memory_get,
    "memory_update": memory_update,
    "memory_delete": memory_delete,
    "memory_export": memory_export,
    "memory_import": memory_import,
    "memory_status": memory_status,
}


if __name__ == "__main__":
    # 命令行测试
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tools.py <tool_name> [args...]")
        print("\nAvailable tools:")
        for tool_name in TOOLS:
            print(f"  - {tool_name}")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    if tool_name in TOOLS:
        result = TOOLS[tool_name]()
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Unknown tool: {tool_name}")
        sys.exit(1)
