"""
VectorStore - 向量存储实现

基于 Ollama embedding 的向量搜索，支持：
- 向量检索（余弦相似度）
- BM25 全文检索
- 混合检索（向量 + BM25）
- 过滤条件支持
"""

import asyncio
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import aiohttp

from ..core.memory import Memory, MemoryType, MemoryPriority


class OllamaEmbedding:
    """Ollama Embedding 客户端"""
    
    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def embed(self, text: str) -> List[float]:
        """生成文本的向量嵌入"""
        session = await self._get_session()
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text,
        }
        
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                raise RuntimeError(f"Ollama API error: {response.status}")
            data = await response.json()
            return data.get("embedding", [])
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        return await asyncio.gather(*[self.embed(text) for text in texts])
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class BM25Index:
    """BM25 全文检索索引"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0
        self.idf: Dict[str, float] = {}
    
    def index(self, doc_id: str, text: str) -> None:
        """索引文档"""
        self.documents[doc_id] = text
        words = self._tokenize(text)
        self.doc_lengths[doc_id] = len(words)
        
        # 更新平均文档长度
        total_docs = len(self.documents)
        total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / total_docs if total_docs > 0 else 0
        
        # 更新 IDF
        for word in set(words):
            doc_count = sum(1 for doc in self.documents.values() if word in self._tokenize(doc))
            self.idf[word] = math.log((total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """搜索文档"""
        query_words = self._tokenize(query)
        scores: Dict[str, float] = {}
        
        for doc_id, text in self.documents.items():
            doc_words = self._tokenize(text)
            doc_len = self.doc_lengths[doc_id]
            
            score = 0.0
            for word in query_words:
                if word in doc_words:
                    tf = doc_words.count(word)
                    idf = self.idf.get(word, 0)
                    
                    # BM25 公式
                    numerator = idf * tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                    score += numerator / denominator
            
            scores[doc_id] = score
        
        # 排序返回
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_k]
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词（中文按字符，英文按单词）"""
        # 简化实现，实际可用 jieba 等
        return list(text.lower())


class VectorStore:
    """向量存储
    
    功能：
    - 向量检索（余弦相似度）
    - BM25 全文检索
    - 混合检索
    - 完整的 CRUD 操作
    """
    
    def __init__(
        self,
        db_path: str = "~/.memorybridge/vector.db",
        ollama_model: str = "nomic-embed-text",
        ollama_base_url: str = "http://localhost:11434",
        hybrid_alpha: float = 0.7,  # 向量权重
    ):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.embedding = OllamaEmbedding(model=ollama_model, base_url=ollama_base_url)
        self.bm25 = BM25Index()
        self.hybrid_alpha = hybrid_alpha
        
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vectors (
                    memory_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding JSON,
                    memory_type TEXT,
                    priority TEXT,
                    tags JSON,
                    metadata JSON,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON vectors(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON vectors(priority)")
            conn.commit()
    
    async def initialize(self) -> None:
        """初始化（加载 BM25 索引）"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT memory_id, content FROM vectors")
            for row in cursor:
                self.bm25.index(row[0], row[1])
    
    async def add(self, memory: Memory) -> None:
        """添加记忆"""
        # 生成向量
        embedding = await self.embedding.embed(memory.content)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vectors 
                (memory_id, content, embedding, memory_type, priority, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.content,
                    json.dumps(embedding),
                    memory.memory_type.value,
                    memory.priority.value,
                    json.dumps(memory.tags),
                    json.dumps(memory.metadata),
                    memory.created_at.isoformat(),
                    memory.updated_at.isoformat() if memory.updated_at else None,
                )
            )
            conn.commit()
        
        # 更新 BM25 索引
        self.bm25.index(memory.id, memory.content)
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM vectors WHERE memory_id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_memory(row)
        return None
    
    async def update(self, memory: Memory) -> None:
        """更新记忆"""
        embedding = await self.embedding.embed(memory.content)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                UPDATE vectors SET 
                content=?, embedding=?, priority=?, tags=?, metadata=?, updated_at=?
                WHERE memory_id=?
                """,
                (
                    memory.content,
                    json.dumps(embedding),
                    memory.priority.value,
                    json.dumps(memory.tags),
                    json.dumps(memory.metadata),
                    datetime.now(timezone.utc).isoformat(),
                    memory.id,
                )
            )
            conn.commit()
        
        self.bm25.index(memory.id, memory.content)
    
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        with sqlite3.connect(str(self.db_path)) as conn:
            result = conn.execute("DELETE FROM vectors WHERE memory_id = ?", (memory_id,))
            conn.commit()
        return result.rowcount > 0
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> List[Memory]:
        """搜索记忆
        
        Args:
            query: 搜索关键词
            limit: 返回数量
            filters: 过滤条件
            use_hybrid: 是否使用混合检索
        
        Returns:
            Memory 列表
        """
        # 生成查询向量
        query_embedding = await self.embedding.embed(query)
        
        # 获取所有候选
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            # 构建过滤条件
            where_clause = []
            params = []
            if filters:
                if "memory_type" in filters:
                    where_clause.append("memory_type = ?")
                    params.append(filters["memory_type"])
                if "priority" in filters:
                    where_clause.append("priority = ?")
                    params.append(filters["priority"])
            
            where_sql = "WHERE " + " AND ".join(where_clause) if where_clause else ""
            query_sql = f"SELECT * FROM vectors {where_sql}"
            
            cursor = conn.execute(query_sql, params)
            rows = cursor.fetchall()
        
        if not rows:
            return []
        
        # 计算分数
        scores: Dict[str, float] = {}
        
        for row in rows:
            memory_id = row["memory_id"]
            content = row["content"]
            embedding = json.loads(row["embedding"])
            
            # 向量相似度
            vector_score = cosine_similarity(query_embedding, embedding)
            
            # BM25 分数
            bm25_results = self.bm25.search(query, top_k=limit)
            bm25_score = 0.0
            for mid, score in bm25_results:
                if mid == memory_id:
                    bm25_score = score
                    break
            
            # 归一化 BM25 分数
            bm25_score = min(1.0, bm25_score / 10.0)
            
            # 混合分数
            if use_hybrid:
                score = self.hybrid_alpha * vector_score + (1 - self.hybrid_alpha) * bm25_score
            else:
                score = vector_score
            
            scores[memory_id] = score
        
        # 排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:limit]
        
        # 返回 Memory 对象
        results = []
        for row in rows:
            if row["memory_id"] in sorted_ids:
                results.append(self._row_to_memory(row))
        
        # 按分数排序
        results.sort(key=lambda m: scores[m.id], reverse=True)
        return results
    
    async def list_memories(self, limit: int = 20) -> List[Memory]:
        """列出所有记忆"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM vectors ORDER BY created_at DESC LIMIT ?", (limit,))
            return [self._row_to_memory(row) for row in cursor]
    
    async def count(self) -> int:
        """统计记忆数量"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM vectors")
            return cursor.fetchone()[0]
    
    async def rebuild_index(self) -> None:
        """重建 BM25 索引"""
        self.bm25 = BM25Index()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT memory_id, content FROM vectors")
            for row in cursor:
                self.bm25.index(row[0], row[1])
    
    async def close(self) -> None:
        """关闭连接"""
        await self.embedding.close()
    
    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        """将数据库行转换为 Memory 对象"""
        return Memory(
            id=row["memory_id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            priority=MemoryPriority(row["priority"]),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            embedding=json.loads(row["embedding"]) if row["embedding"] else None,
        )


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)
