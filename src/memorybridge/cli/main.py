"""
CLI 主入口

使用 Typer 框架提供命令行界面
支持多存储后端配置
"""

import typer
from typing import Optional
import json

from ..storage.factory import create_storage, create_storage_from_env
from ..core.memory import MemoryType, MemoryPriority
from . import graph_cmds

app = typer.Typer(
    name="memorybridge",
    help="MemoryBridge - 跨 Agent 记忆共享平台",
    add_completion=True,
)

# 注册知识图谱子命令
app.add_typer(graph_cmds.graph_app, name="graph")

# 全局配置
_global_backend: Optional[str] = None
_global_config: Optional[dict] = None


def get_storage(backend: Optional[str] = None, config: Optional[dict] = None):
    """获取存储实例（支持多后端）"""
    if backend:
        return create_storage(backend, config or {})
    return create_storage_from_env()


@app.command()
def add(
    content: str = typer.Argument(..., help="记忆内容"),
    type: str = typer.Option("long_term", "--type", "-t", help="记忆类型：session/long_term"),
    priority: str = typer.Option("p1", "--priority", "-p", help="优先级：p0/p1/p2/p3"),
    tags: Optional[str] = typer.Option(None, "--tags", help="标签，逗号分隔"),
    backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端：sqlite/mongodb/tiered"),
):
    """添加一条新记忆"""
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

    tag_list = [t.strip() for t in tags.replace("，", ",").split(",") if t.strip()] if tags else []

    storage = get_storage(backend)

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
    backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端"),
):
    """搜索记忆"""
    storage = get_storage(backend)

    filters = {}
    if type:
        try:
            filters["memory_type"] = type
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
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="优先级过滤：p0/p1/p2/p3"),
    backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端"),
):
    """列出记忆"""
    storage = get_storage(backend)

    memory_type = None
    if type:
        try:
            memory_type = MemoryType(type)
        except ValueError:
            typer.echo(f"❌ 错误：无效的记忆类型 '{type}'")
            typer.echo("   有效值：session, long_term")
            raise typer.Exit(1)

    memory_priority = None
    if priority:
        try:
            memory_priority = MemoryPriority(priority)
        except ValueError:
            typer.echo(f"❌ 错误：无效的优先级 '{priority}'")
            typer.echo("   有效值：p0, p1, p2, p3")
            raise typer.Exit(1)

    import asyncio

    memories = asyncio.run(storage.list(limit=limit, memory_type=memory_type, priority=memory_priority))

    if not memories:
        typer.echo("❌ 暂无记忆")
        return

    typer.echo(f"📊 共 {len(memories)} 条记忆:\n")

    for i, memory in enumerate(memories, 1):
        typer.secho(f"[{i}] {memory.id[:8]}", bold=True)
        typer.echo(f"    内容：{memory.content[:80]}{'...' if len(memory.content) > 80 else ''}")
        typer.echo(f"    类型：{memory.memory_type.value} | 优先级：{memory.priority.value}")
        if memory.tags:
            typer.echo(f"    标签：{', '.join(memory.tags)}")
        typer.echo()


@app.command()
def get(memory_id: str = typer.Argument(..., help="记忆 ID"), backend: str = typer.Option("sqlite", "--backend", "-b")):
    """查看单条记忆详情"""
    storage = get_storage(backend)

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
    backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端"),
):
    """更新记忆"""
    storage = get_storage(backend)

    if not content and not tags:
        typer.echo("❌ 错误：至少需要提供一个更新字段 (--content 或 --tags)")
        raise typer.Exit(1)

    tag_list = [t.strip() for t in tags.replace("，", ",").split(",") if t.strip()] if tags else None

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
def delete(memory_id: str = typer.Argument(..., help="记忆 ID"), backend: str = typer.Option("sqlite", "--backend", "-b")):
    """删除记忆"""
    storage = get_storage(backend)

    import asyncio

    success = asyncio.run(storage.delete(memory_id))

    if success:
        typer.echo(f"✅ 记忆已删除：{memory_id}")
    else:
        typer.echo(f"❌ 未找到记忆：{memory_id}")
        raise typer.Exit(1)


@app.command()
def export(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径（默认导出到 ~/.memorybridge/exports/memories_TIMESTAMP.json）"),
    format: str = typer.Option("json", "--format", "-f", help="导出格式"),
    backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端"),
):
    """导出记忆到文件"""
    from pathlib import Path
    import datetime
    
    storage = get_storage(backend)

    import asyncio

    data = asyncio.run(storage.export(format=format))

    # 如果未指定输出路径，导出到默认目录
    if not output:
        export_dir = Path.home() / ".memorybridge" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = str(export_dir / f"memories_{timestamp}.json")
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(data)

    typer.echo(f"✅ 已导出到：{output}")


@app.command(name="import")
def import_(
    input: str = typer.Option(..., "--input", "-i", help="输入文件路径"),
    format: str = typer.Option("json", "--format", "-f", help="导入格式"),
    backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端"),
):
    """从文件导入记忆"""
    storage = get_storage(backend)

    with open(input, "r", encoding="utf-8") as f:
        data = f.read()

    import asyncio

    count = asyncio.run(storage.import_memories(data, format=format))

    typer.echo(f"✅ 成功导入 {count} 条记忆")


@app.command()
def status(backend: str = typer.Option("sqlite", "--backend", "-b", help="存储后端")):
    """查看系统状态"""
    storage = get_storage(backend)

    import asyncio

    total = asyncio.run(storage.count())
    session_count = asyncio.run(storage.count(MemoryType.SESSION))
    long_term_count = asyncio.run(storage.count(MemoryType.LONG_TERM))

    typer.secho("📊 MemoryBridge 状态", bold=True)
    typer.echo(f"总记忆数：{total}")
    typer.echo(f"  - Session 记忆：{session_count}")
    typer.echo(f"  - 长期记忆：{long_term_count}")
    typer.echo(f"存储后端：{backend}")
    typer.echo(f"存储路径：{getattr(storage, 'db_path', 'N/A')}")


@app.command()
def version():
    """显示版本号"""
    from .. import __version__

    typer.echo(f"MemoryBridge v{__version__}")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="显示当前配置"),
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="设置默认后端"),
    mongo_uri: Optional[str] = typer.Option(None, "--mongo-uri", help="MongoDB 连接字符串"),
    mongo_db: Optional[str] = typer.Option(None, "--mongo-db", help="MongoDB 数据库名"),
):
    """管理配置"""
    config_file = typer.get_app_dir("memorybridge") / "config.json"
    from pathlib import Path
    config_file = Path(config_file)

    if show:
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
            typer.echo(json.dumps(config, indent=2, ensure_ascii=False))
        else:
            typer.echo("❌ 配置文件不存在")
        return

    # 更新配置
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)

    if backend:
        config["backend"] = backend
    if mongo_uri:
        config["mongo_uri"] = mongo_uri
    if mongo_db:
        config["mongo_db"] = mongo_db

    # 保存配置
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    typer.echo("✅ 配置已更新")
    typer.echo(f"配置文件：{config_file}")


@app.command()
def backup(
    action: str = typer.Argument("list", help="操作：list/backup/restore"),
    target: Optional[str] = typer.Option(None, "--target", "-t", help="备份文件路径或 OSS key"),
    oss_key_id: Optional[str] = typer.Option(None, "--oss-key-id", envvar="OSS_ACCESS_KEY_ID"),
    oss_key_secret: Optional[str] = typer.Option(None, "--oss-key-secret", envvar="OSS_ACCESS_KEY_SECRET"),
    oss_bucket: Optional[str] = typer.Option(None, "--oss-bucket", envvar="OSS_BUCKET_NAME"),
):
    """备份管理（支持本地和 OSS）"""
    import asyncio

    if action == "list":
        # 列出本地备份
        from pathlib import Path
        backup_dir = Path.home() / ".memorybridge" / "backups"
        
        if not backup_dir.exists():
            typer.echo("❌ 暂无备份")
            return
        
        backups = list(backup_dir.glob("*.json"))
        if not backups:
            typer.echo("❌ 暂无备份")
            return
        
        typer.echo("📊 本地备份:\n")
        for backup in sorted(backups, reverse=True):
            stat = backup.stat()
            typer.echo(f"  {backup.name} ({stat.st_size} bytes, {backup.stat().st_mtime})")
    
    elif action == "backup":
        # 导出当前数据作为备份
        storage = get_storage()
        output = target or f"backup_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = asyncio.run(storage.export(format="json"))
        with open(output, "w", encoding="utf-8") as f:
            f.write(data)
        
        typer.echo(f"✅ 备份已创建：{output}")
    
    elif action == "restore":
        if not target:
            typer.echo("❌ 错误：restore 需要指定 --target 文件路径")
            raise typer.Exit(1)
        
        storage = get_storage()
        count = asyncio.run(storage.import_memories(open(target).read(), format="json"))
        typer.echo(f"✅ 恢复成功：{count} 条记忆")
    
    else:
        typer.echo(f"❌ 未知操作：{action}")
        raise typer.Exit(1)


def main():
    """CLI 入口点"""
    app()


if __name__ == "__main__":
    main()
