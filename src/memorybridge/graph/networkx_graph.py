"""
NetworkX 知识图谱实现

使用 NetworkX 进行图操作，SQLite 持久化
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx


class NetworkXGraph:
    """基于 NetworkX 的知识图谱
    
    特点:
    - 内存图操作（快速）
    - SQLite 持久化（不丢失）
    - 支持实体和关系管理
    - 支持图谱查询和多跳推理
    """
    
    # 预定义的关系类型
    VALID_RELATIONS = {"uses", "knows", "related_to", "part_of"}
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化知识图谱
        
        Args:
            db_path: SQLite 数据库路径（默认 ~/.memorybridge/graph.db）
        """
        if db_path is None:
            db_dir = Path.home() / ".memorybridge"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "graph.db")
        
        self.db_path = db_path
        self.graph = nx.DiGraph()  # 有向图
        self._init_db()
        self._load_from_db()
    
    def _init_db(self) -> None:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    entity_type TEXT NOT NULL,
                    properties JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    from_entity_id TEXT NOT NULL,
                    to_entity_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    properties JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_entity_id) REFERENCES entities(id),
                    FOREIGN KEY (to_entity_id) REFERENCES entities(id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relation_type ON relations(relation_type)")
            conn.commit()
    
    def _load_from_db(self) -> None:
        """从数据库加载图"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 加载实体
            cursor = conn.execute("SELECT * FROM entities")
            for row in cursor:
                self.graph.add_node(
                    row["id"],
                    name=row["name"],
                    entity_type=row["entity_type"],
                    properties=json.loads(row["properties"]) if row["properties"] else {},
                    created_at=row["created_at"]
                )
            
            # 加载关系
            cursor = conn.execute("SELECT * FROM relations")
            for row in cursor:
                self.graph.add_edge(
                    row["from_entity_id"],
                    row["to_entity_id"],
                    relation_type=row["relation_type"],
                    properties=json.loads(row["properties"]) if row["properties"] else {},
                    created_at=row["created_at"]
                )
    
    def _save_entity(self, entity_id: str, name: str, entity_type: str, properties: Dict) -> None:
        """保存实体到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO entities (id, name, entity_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entity_id, name, entity_type, json.dumps(properties), 
                 self.graph.nodes[entity_id].get("created_at", datetime.now(timezone.utc).isoformat()))
            )
            conn.commit()
    
    def _save_relation(self, relation_id: str, from_id: str, to_id: str, 
                       relation_type: str, properties: Dict) -> None:
        """保存关系到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO relations (id, from_entity_id, to_entity_id, relation_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (relation_id, from_id, to_id, relation_type, json.dumps(properties),
                 self.graph[from_id][to_id].get("created_at", datetime.now(timezone.utc).isoformat()))
            )
            conn.commit()
    
    def add_entity(self, name: str, entity_type: str, properties: Optional[Dict] = None) -> str:
        """添加实体
        
        Args:
            name: 实体名称
            entity_type: 实体类型
            properties: 实体属性
        
        Returns:
            实体 ID
        """
        import uuid
        entity_id = str(uuid.uuid4())
        
        self.graph.add_node(
            entity_id,
            name=name,
            entity_type=entity_type,
            properties=properties or {},
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        self._save_entity(entity_id, name, entity_type, properties or {})
        
        return entity_id
    
    def add_relation(self, from_id: str, to_id: str, relation_type: str, 
                     properties: Optional[Dict] = None) -> str:
        """添加关系
        
        Args:
            from_id: 起始实体 ID
            to_id: 目标实体 ID
            relation_type: 关系类型（uses/knows/related_to/part_of）
            properties: 关系属性
        
        Returns:
            关系 ID
        """
        if relation_type not in self.VALID_RELATIONS:
            raise ValueError(f"无效的关系类型：{relation_type}。有效值：{self.VALID_RELATIONS}")
        
        if from_id not in self.graph or to_id not in self.graph:
            raise ValueError("实体不存在")
        
        import uuid
        relation_id = str(uuid.uuid4())
        
        self.graph.add_edge(
            from_id,
            to_id,
            relation_type=relation_type,
            properties=properties or {},
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        self._save_relation(relation_id, from_id, to_id, relation_type, properties or {})
        
        return relation_id
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """获取实体
        
        Args:
            entity_id: 实体 ID
        
        Returns:
            实体信息，不存在返回 None
        """
        if entity_id in self.graph:
            node = self.graph.nodes[entity_id]
            return {
                "id": entity_id,
                "name": node["name"],
                "entity_type": node["entity_type"],
                "properties": node.get("properties", {}),
                "created_at": node.get("created_at")
            }
        return None
    
    def get_entity_by_name(self, name: str) -> Optional[Dict]:
        """通过名称获取实体
        
        Args:
            name: 实体名称
        
        Returns:
            实体信息，不存在返回 None
        """
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("name") == name:
                return {
                    "id": node_id,
                    "name": node_data["name"],
                    "entity_type": node_data["entity_type"],
                    "properties": node_data.get("properties", {}),
                    "created_at": node_data.get("created_at")
                }
        return None
    
    def query_relations(self, entity_id: str, relation_type: Optional[str] = None) -> List[Dict]:
        """查询实体的关系
        
        Args:
            entity_id: 实体 ID
            relation_type: 关系类型过滤（可选）
        
        Returns:
            关系列表
        """
        relations = []
        
        # 出边（该实体指向其他实体）
        for target_id in self.graph.successors(entity_id):
            edge_data = self.graph.edges[entity_id, target_id]
            if relation_type is None or edge_data.get("relation_type") == relation_type:
                relations.append({
                    "from_id": entity_id,
                    "to_id": target_id,
                    "relation_type": edge_data["relation_type"],
                    "properties": edge_data.get("properties", {}),
                    "direction": "out"
                })
        
        # 入边（其他实体指向该实体）
        for source_id in self.graph.predecessors(entity_id):
            edge_data = self.graph.edges[source_id, entity_id]
            if relation_type is None or edge_data.get("relation_type") == relation_type:
                relations.append({
                    "from_id": source_id,
                    "to_id": entity_id,
                    "relation_type": edge_data["relation_type"],
                    "properties": edge_data.get("properties", {}),
                    "direction": "in"
                })
        
        return relations
    
    def find_path(self, from_id: str, to_id: str, max_depth: int = 3) -> List[Dict]:
        """查找两个实体之间的路径（多跳推理）
        
        Args:
            from_id: 起始实体 ID
            to_id: 目标实体 ID
            max_depth: 最大深度
        
        Returns:
            路径列表
        """
        try:
            paths = nx.all_simple_paths(self.graph, from_id, to_id, cutoff=max_depth)
            result = []
            
            for path in paths:
                path_info = {
                    "path": path,
                    "length": len(path) - 1,
                    "edges": []
                }
                
                # 获取路径上的关系
                for i in range(len(path) - 1):
                    edge_data = self.graph.edges[path[i], path[i+1]]
                    path_info["edges"].append({
                        "from": path[i],
                        "to": path[i+1],
                        "relation_type": edge_data["relation_type"]
                    })
                
                result.append(path_info)
            
            return result
        except nx.NetworkXNoPath:
            return []
    
    def list_entities(self, entity_type: Optional[str] = None) -> List[Dict]:
        """列出所有实体
        
        Args:
            entity_type: 类型过滤（可选）
        
        Returns:
            实体列表
        """
        entities = []
        for node_id, node_data in self.graph.nodes(data=True):
            if entity_type is None or node_data.get("entity_type") == entity_type:
                entities.append({
                    "id": node_id,
                    "name": node_data["name"],
                    "entity_type": node_data["entity_type"],
                    "properties": node_data.get("properties", {}),
                    "created_at": node_data.get("created_at")
                })
        return entities
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息
        
        Returns:
            统计信息
        """
        return {
            "entity_count": self.graph.number_of_nodes(),
            "relation_count": self.graph.number_of_edges(),
            "entity_types": len(set(d.get("entity_type") for _, d in self.graph.nodes(data=True))),
            "relation_types": len(set(d.get("relation_type") for _, _, d in self.graph.edges(data=True)))
        }
    
    def export_graph(self, format: str = "graphml") -> str:
        """导出图谱
        
        Args:
            format: 导出格式（graphml/gexf/json）
        
        Returns:
            导出的数据字符串
        """
        import tempfile
        import os
        
        # 对于 GraphML 和 GEXF，需要序列化 dict 属性为字符串
        if format in ("graphml", "gexf"):
            # 创建临时图，将 dict 属性序列化为 JSON 字符串
            temp_graph = nx.DiGraph()
            
            # 复制节点，序列化 properties
            for node_id, node_data in self.graph.nodes(data=True):
                new_data = node_data.copy()
                if "properties" in new_data and isinstance(new_data["properties"], dict):
                    new_data["properties"] = json.dumps(new_data["properties"], ensure_ascii=False)
                temp_graph.add_node(node_id, **new_data)
            
            # 复制边，序列化 properties
            for from_id, to_id, edge_data in self.graph.edges(data=True):
                new_data = edge_data.copy()
                if "properties" in new_data and isinstance(new_data["properties"], dict):
                    new_data["properties"] = json.dumps(new_data["properties"], ensure_ascii=False)
                temp_graph.add_edge(from_id, to_id, **new_data)
            
            export_graph = temp_graph
        else:
            export_graph = self.graph
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=f".{format}") as f:
            temp_path = f.name
            
            if format == "graphml":
                nx.write_graphml(export_graph, temp_path)
            elif format == "gexf":
                nx.write_gexf(export_graph, temp_path)
            elif format == "json":
                data = nx.node_link_data(export_graph)
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            f.seek(0)
            content = f.read()
        
        os.unlink(temp_path)
        
        return content
    
    def __len__(self) -> int:
        """返回实体数量"""
        return len(self.graph)
    
    def __repr__(self) -> str:
        return f"NetworkXGraph(entities={len(self.graph)}, relations={self.graph.number_of_edges()})"
