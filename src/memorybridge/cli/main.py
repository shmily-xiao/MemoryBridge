"""
CLI 主入口

使用 Typer 框架提供命令行界面
"""

import typer
from typing import Optional

from ..storage.sqlite import SQLiteStorage
from ..core.memory import MemoryType, MemoryPriority
from . import graph_cmds

app = typer.Typer(
    name="memorybridge",
    help="MemoryBridge - 跨 Agent 记忆共享平台",
    add_completion=True,
)

# 注册知识图谱子命令
app.add_typer(graph_cmds.graph_app, name="graph")

# 全局存储实例
_storage: Optional[SQLiteStorage] = None


def get_storage() -> SQLiteStorage:
    """获取存储实例 (懒加载)"""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage()
    return _storage


@app.command()
def add(
    content: str = typer.Argument(..., help="记忆内容"),
    type: str = typer.Option("long_term", "--type", "-t", help="记忆类型：session/long_term"),
    priority: str = typer.Option("p1", "--priority", "-p", help="优先级：p0/p1/p2/p3"),
    tags: Optional[str] = typer.Option(None, "--tags", help="标签，逗号分隔"),
):
    """添加一条新记忆"""
    storage = get_storage()

    # 参数验证
    try:
        memory_type = MemoryType(type)
    except ValueError:
        typer.echo(f"❌ 错误：无效的记忆类型 '{type}'")
        typer.echo("   有效值：session, long_term")
        raise typer.Exit(1)

    try:
        priority = MemoryPriority(priority)
    except ValueError:
        typer.echo(f"❌ 错误：无效的优先级 '{priority}'")
        typer.echo("   有效值：p0, p1, p2, p3")
        raise typer.Exit(1)

    tag_list = tags.split(",") if tags else []

    import asyncio

    memory = asyncio.run(
        storage.add(
            content=content,
            memory_type=memory_type,
            priority=priority,
            tags=tag_list,
        )
    )

    typer.echo(f"✅ 记忆添加成功！")
    typer.echo(f"   ID: {memory.id}")
    typer.echo(f"   内容：{memory.content}")
    typer.echo(f"   类型：{memory.memory_type.value}")
    typer.echo(f"   优先级：{memory.priority.value}")
    if memory.tags:
        typer.echo(f"   标签：{', '.join(memory.tags)}")


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(10, "--limit", "-l", help="返回数量"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="记忆类型过滤"),
):
    """搜索记忆"""
    storage = get_storage()

    filters = {}
    if type:
        try:
            filters["memory_type"] = MemoryType(type).value
        except ValueError:
            typer.echo(f"❌ 错误：无效的记忆类型 '{type}'")
            raise typer.Exit(1)

    import asyncio

    memories = asyncio.run(storage.search(query=query, limit=limit, filters=filters))

    if not memories:
        typer.echo("❌ 未找到匹配的记忆")
        return

    typer.echo(f"📊 找到 {len(memories)} 条记忆:\n")

    for i, memory in enumerate(memories, 1):
        typer.secho(f"[{i}] {memory.id[:8]}", bold=True)
        typer.echo(f"    内容：{memory.content[:100]}{'...' if len(memory.content) > 100 else ''}")
        typer.echo(f"    类型：{memory.memory_type.value} | 优先级：{memory.priority.value}")
        if memory.tags:
            typer.echo(f"    标签：{', '.join(memory.tags)}")
        typer.echo()


@app.command(name="list")
def list_(
    limit: int = typer.Option(20, "--limit", "-l", help="返回数量"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="记忆类型过滤"),
):
    """列出记忆"""
    storage = get_storage()

    memory_type = None
    if type:
        try:
            memory_type = MemoryType(type)
        except ValueError:
            typer.echo(f"❌ 错误：无效的记忆类型 '{type}'")
            raise typer.Exit(1)

    import asyncio

    memories = asyncio.run(storage.list(limit=limit, memory_type=memory_type))

    if not memories:
        typer.echo("❌ 暂无记忆")
        return

    typer.echo(f"📊 共 {len(memories)} 条记忆:\n")

    for i, memory in enumerate(memories, 1):
        typer.secho(f"[{i}] {memory.id[:8]}", bold=True)
        typer.echo(f"    内容：{memory.content[:80]}{'...' if len(memory.content) > 80 else ''}")
        typer.echo(f"    类型：{memory.memory_type.value} | 优先级：{memory.priority.value}")
        typer.echo()


@app.command()
def get(memory_id: str = typer.Argument(..., help="记忆 ID")):
    """查看单条记忆详情"""
    storage = get_storage()

    import asyncio

    memory = asyncio.run(storage.get(memory_id))

    if not memory:
        typer.echo(f"❌ 未找到记忆：{memory_id}")
        raise typer.Exit(1)

    typer.secho(f"📝 记忆详情", bold=True)
    typer.echo(f"ID: {memory.id}")
    typer.echo(f"内容：{memory.content}")
    typer.echo(f"类型：{memory.memory_type.value}")
    typer.echo(f"优先级：{memory.priority.value}")
    typer.echo(f"创建时间：{memory.created_at}")
    if memory.updated_at:
        typer.echo(f"更新时间：{memory.updated_at}")
    if memory.tags:
        typer.echo(f"标签：{', '.join(memory.tags)}")
    if memory.metadata:
        typer.echo(f"元数据：{memory.metadata}")


@app.command()
def update(
    memory_id: str = typer.Argument(..., help="记忆 ID"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="新内容"),
    tags: Optional[str] = typer.Option(None, "--tags", help="新标签，逗号分隔"),
):
    """更新记忆"""
    storage = get_storage()

    if not content and not tags:
        typer.echo("❌ 错误：至少需要提供一个更新字段 (--content 或 --tags)")
        raise typer.Exit(1)

    tag_list = tags.split(",") if tags else None

    import asyncio

    try:
        memory = asyncio.run(
            storage.update(
                memory_id=memory_id,
                content=content,
                tags=tag_list,
            )
        )

        typer.echo(f"✅ 记忆更新成功！")
        typer.echo(f"   ID: {memory.id}")
        typer.echo(f"   内容：{memory.content}")
        if memory.tags:
            typer.echo(f"   标签：{', '.join(memory.tags)}")
    except ValueError as e:
        typer.echo(f"❌ 错误：{e}")
        raise typer.Exit(1)


@app.command()
def delete(memory_id: str = typer.Argument(..., help="记忆 ID")):
    """删除记忆"""
    storage = get_storage()

    import asyncio

    success = asyncio.run(storage.delete(memory_id))

    if success:
        typer.echo(f"✅ 记忆已删除：{memory_id}")
    else:
        typer.echo(f"❌ 未找到记忆：{memory_id}")
        raise typer.Exit(1)


@app.command()
def export(
    output: str = typer.Option("memories.json", "--output", "-o", help="输出文件路径"),
    format: str = typer.Option("json", "--format", "-f", help="导出格式"),
):
    """导出记忆到文件"""
    storage = get_storage()

    import asyncio

    data = asyncio.run(storage.export(format=format))

    with open(output, "w", encoding="utf-8") as f:
        f.write(data)

    typer.echo(f"✅ 已导出到：{output}")


@app.command(name="import")
def import_(
    input: str = typer.Option(..., "--input", "-i", help="输入文件路径"),
    format: str = typer.Option("json", "--format", "-f", help="导入格式"),
):
    """从文件导入记忆"""
    storage = get_storage()

    with open(input, "r", encoding="utf-8") as f:
        data = f.read()

    import asyncio

    count = asyncio.run(storage.import_memories(data, format=format))

    typer.echo(f"✅ 成功导入 {count} 条记忆")


@app.command()
def status():
    """查看系统状态"""
    storage = get_storage()

    import asyncio

    total = asyncio.run(storage.count())
    session_count = asyncio.run(storage.count(MemoryType.SESSION))
    long_term_count = asyncio.run(storage.count(MemoryType.LONG_TERM))

    typer.secho("📊 MemoryBridge 状态", bold=True)
    typer.echo(f"总记忆数：{total}")
    typer.echo(f"  - Session 记忆：{session_count}")
    typer.echo(f"  - 长期记忆：{long_term_count}")
    typer.echo(f"存储路径：{storage.db_path}")


@app.command()
def version():
    """显示版本号"""
    from .. import __version__

    typer.echo(f"MemoryBridge v{__version__}")


def main():
    """CLI 入口点"""
    app()


if __name__ == "__main__":
    main()
