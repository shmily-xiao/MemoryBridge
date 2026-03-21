"""
知识图谱 CLI 命令
"""

import typer
from typing import Optional

graph_app = typer.Typer(name="graph", help="知识图谱管理")


def get_graph():
    """获取图谱实例"""
    from ..graph.networkx_graph import NetworkXGraph
    return NetworkXGraph()


@graph_app.command()
def add_entity(
    name: str = typer.Argument(..., help="实体名称"),
    type: str = typer.Option(..., "--type", "-t", help="实体类型"),
    props: Optional[str] = typer.Option(None, "--props", "-p", help="属性，JSON 格式")
):
    """添加实体"""
    import json
    
    graph = get_graph()
    properties = json.loads(props) if props else {}
    
    entity_id = graph.add_entity(name=name, entity_type=type, properties=properties)
    
    typer.echo(f"✅ 实体添加成功！")
    typer.echo(f"   ID: {entity_id}")
    typer.echo(f"   名称：{name}")
    typer.echo(f"   类型：{type}")
    if properties:
        typer.echo(f"   属性：{properties}")


@graph_app.command()
def add_relation(
    from_entity: str = typer.Argument(..., help="起始实体 ID"),
    relation: str = typer.Argument(..., help="关系类型 (uses/knows/related_to/part_of)"),
    to_entity: str = typer.Argument(..., help="目标实体 ID")
):
    """添加关系"""
    graph = get_graph()
    
    try:
        relation_id = graph.add_relation(
            from_id=from_entity,
            to_id=to_entity,
            relation_type=relation
        )
        
        typer.echo(f"✅ 关系添加成功！")
        typer.echo(f"   ID: {relation_id}")
        typer.echo(f"   {from_entity[:8]} -[{relation}]-> {to_entity[:8]}")
    except ValueError as e:
        typer.echo(f"❌ 错误：{e}")
        raise typer.Exit(1)


@graph_app.command()
def list_entities(
    type: Optional[str] = typer.Option(None, "--type", "-t", help="实体类型过滤")
):
    """列出实体"""
    graph = get_graph()
    entities = graph.list_entities(entity_type=type)
    
    if not entities:
        typer.echo("❌ 暂无实体")
        return
    
    typer.echo(f"📊 共 {len(entities)} 个实体:\n")
    
    for i, entity in enumerate(entities, 1):
        typer.secho(f"[{i}] {entity['name']}", bold=True)
        typer.echo(f"    ID: {entity['id'][:8]}")
        typer.echo(f"    类型：{entity['entity_type']}")
        if entity['properties']:
            typer.echo(f"    属性：{entity['properties']}")
        typer.echo()


@graph_app.command()
def query(
    entity_id: str = typer.Argument(..., help="实体 ID"),
    relation_type: Optional[str] = typer.Option(None, "--type", "-t", help="关系类型过滤")
):
    """查询实体关系"""
    graph = get_graph()
    relations = graph.query_relations(entity_id, relation_type)
    
    if not relations:
        typer.echo("❌ 未找到关系")
        return
    
    typer.echo(f"📊 找到 {len(relations)} 个关系:\n")
    
    for i, rel in enumerate(relations, 1):
        direction = "→" if rel["direction"] == "out" else "←"
        typer.secho(f"[{i}] {rel['from_id'][:8]} {direction} {rel['to_id'][:8]}", bold=True)
        typer.echo(f"    关系：{rel['relation_type']}")
        if rel['properties']:
            typer.echo(f"    属性：{rel['properties']}")
        typer.echo()


@graph_app.command()
def find_path(
    from_entity: str = typer.Argument(..., help="起始实体 ID"),
    to_entity: str = typer.Argument(..., help="目标实体 ID"),
    max_depth: int = typer.Option(3, "--depth", "-d", help="最大深度")
):
    """查找实体间路径（多跳推理）"""
    graph = get_graph()
    paths = graph.find_path(from_entity, to_entity, max_depth)
    
    if not paths:
        typer.echo("❌ 未找到路径")
        return
    
    typer.echo(f"📊 找到 {len(paths)} 条路径:\n")
    
    for i, path in enumerate(paths, 1):
        typer.secho(f"[{i}] 路径长度：{path['length']}", bold=True)
        path_str = " → ".join([eid[:8] for eid in path['path']])
        typer.echo(f"    {path_str}")
        
        for edge in path['edges']:
            typer.echo(f"      {edge['from'][:8]} -[{edge['relation_type']}]-> {edge['to'][:8]}")
        typer.echo()


@graph_app.command()
def stats():
    """查看图谱统计"""
    graph = get_graph()
    stats = graph.get_statistics()
    
    typer.secho("📊 知识图谱统计", bold=True)
    typer.echo(f"实体数量：{stats['entity_count']}")
    typer.echo(f"关系数量：{stats['relation_count']}")
    typer.echo(f"实体类型：{stats['entity_types']}")
    typer.echo(f"关系类型：{stats['relation_types']}")


@graph_app.command()
def export(
    output: str = typer.Option("graph.graphml", "--output", "-o", help="输出文件"),
    format: str = typer.Option("graphml", "--format", "-f", help="导出格式 (graphml/gexf/json)")
):
    """导出图谱"""
    graph = get_graph()
    data = graph.export_graph(format=format)
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(data)
    
    typer.echo(f"✅ 已导出到：{output}")
