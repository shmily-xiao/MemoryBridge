# 向量搜索指南

MemoryBridge 提供基于 Ollama 的向量搜索，支持混合检索（向量 + BM25）。

## 架构

```
Query → Ollama Embedding → Vector Search + BM25 → Hybrid Rank → Results
```

## 快速开始

```python
from memorybridge.storage.vector_store import VectorStore

store = VectorStore(
    ollama_model="nomic-embed-text",
    hybrid_alpha=0.7,  # 向量权重 70%
)
await store.initialize()

# 添加记忆
memory = Memory(content="机器学习是 AI 的核心", memory_type=MemoryType.LONG_TERM)
await store.add(memory)

# 搜索
results = await store.search("人工智能", limit=5, use_hybrid=True)
```

## 配置选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ollama_model` | nomic-embed-text | Embedding 模型 |
| `hybrid_alpha` | 0.7 | 向量权重 (0-1) |
| `db_path` | ~/.memorybridge/vector.db | 数据库路径 |

## 性能优化

1. **调整混合权重**: `hybrid_alpha=0.9` (更多语义) 或 `0.5` (更多关键词)
2. **批量添加**: 批量插入后重建索引
3. **使用缓存**: `@cached(ttl=300)`

## 故障排查

```bash
# 检查 Ollama
ollama list
curl http://localhost:11434/api/tags

# 重建索引
await store.rebuild_index()
```

---

**相关**: [知识图谱](knowledge-graph.md) | [性能优化](performance.md)
