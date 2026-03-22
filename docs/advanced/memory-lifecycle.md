# 记忆生命周期管理

MemoryBridge 实现完整的记忆生命周期：Context → Short-term → Long-term

## 记忆分层

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Context   │ ──→ │ Short-term   │ ──→ │  Long-term   │
│ (临时缓存)  │     │  (工作记忆)  │     │  (长期记忆)  │
│  对话结束后  │     │   保留 7 天    │     │   保留 90 天 +  │
│    清理     │     │  P2/P3 优先级 │     │  P0/P1 优先级 │
└─────────────┘     └──────────────┘     └──────────────┘
                            │                      │
                            ▼                      ▼
                    ┌─────────────────────────────────┐
                    │      知识图谱自动提取            │
                    │   实体/关系 + 时间维度追踪       │
                    └─────────────────────────────────┘
```

## 重要性评分算法

```python
score = (
    引用次数 × 0.25 +      # 被提及越多越重要
    用户指令 × 0.35 +       # "记住这个" = 1.0
    情感强度 × 0.10 +       # 情感关键词匹配
    时效性 × 0.15 +         # 新记忆优先
    时间上下文 × 0.15       # 时间相关词汇
)

# 升级阈值：score >= 0.7 → Long-term
# 降级阈值：score < 0.3 → 清理或降级
```

## 使用 MemoryManager

```python
from memorybridge.cognitive import MemoryManager

manager = MemoryManager(short_storage, long_storage)

# 处理新记忆（自动评分 + 升级）
result = await manager.process_new_memory(
    content="Python 是一种编程语言",
    user_instruction=True,  # 用户说"记住这个"
)

print(f"记忆 ID: {result['memory_id']}")
print(f"重要性评分：{result['importance_score']}")
print(f"是否升级：{result['promoted_to_long']}")
```

## 知识图谱自动提取

```python
from memorybridge.cognitive import KnowledgeGraphExtractor

extractor = KnowledgeGraphExtractor()

# 从对话提取实体和关系
entities, relations = await extractor.extract_from_memory(
    "我用 Python 开发 MemoryBridge 项目"
)

# 实体：["我", "Python", "MemoryBridge"]
# 关系：[("我", "uses", "Python"), ("我", "develops", "MemoryBridge")]

# 获取时间维度
report = extractor.get_knowledge_freshness_report()
print(f"总实体数：{report['total_entities']}")
print(f"新鲜实体：{report['fresh_entities']}")
```

## 定期清理

```python
# 执行清理和整理
result = await manager.cleanup_and_organize()

print(f"清理短期记忆：{result['short_term_cleaned']}")
print(f"清理长期记忆：{result['long_term_cleaned']}")
print(f"更新关系置信度：{result['relations_updated']}")
```

## 时间维度追踪

```python
from memorybridge.cognitive.graph_extractor import TemporalEntity

entity = TemporalEntity(
    id="python",
    name="Python",
    entity_type="language",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    expires_at=None,  # 永久知识
    temporal_context="2026-Q1",
)

# 关系置信度衰减
relation.confidence *= (1 - relation.decay_rate)  # 每月衰减 1%
```

---

**相关**: [知识图谱](knowledge-graph.md) | [监控系统](monitoring.md)
