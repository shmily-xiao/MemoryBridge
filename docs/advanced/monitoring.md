# 监控与性能

MemoryBridge 提供完整的性能监控和健康检查系统。

## 性能监控

```python
from memorybridge.monitoring import get_monitor, monitor_endpoint

monitor = get_monitor()

# 记录请求
monitor.record_request(latency_ms=50.0, endpoint="search")

# 记录错误
monitor.record_error("ValueError")

# 获取状态
status = monitor.get_status()
print(f"运行时间：{status['uptime']}")
print(f"请求数：{status['requests']}")
print(f"错误率：{status['error_rate']}")
```

## 健康检查

```python
from memorybridge.monitoring import HealthChecker

checker = HealthChecker()

# 检查存储健康
await checker.check_storage(storage)

# 检查向量搜索
await checker.check_vector_search(vector_store)

# 获取健康状态
health = checker.get_status()
print(f"健康：{health['healthy']}")
print(f"检查项：{health['checks']}")
```

## 性能优化

### LRU 缓存

```python
from memorybridge.optimization import LRUCache, cached

# 使用缓存装饰器
@cached(ttl=300, key_prefix="search")
async def search_with_cache(query: str):
    return await storage.search(query, limit=10)

# 手动缓存
cache = LRUCache(max_size=1000, ttl_seconds=300)
cache.set("key", "value")
value = cache.get("key")
```

### 批量处理

```python
from memorybridge.optimization import BatchProcessor

class MemoryBatchProcessor(BatchProcessor):
    async def _flush(self):
        # 批量写入数据库
        for item in self.queue:
            await storage.add(item)
        self.queue.clear()

processor = MemoryBatchProcessor(batch_size=100, flush_interval=1.0)
await processor.add(memory)
```

## 导出报告

```python
# 导出监控报告
report = monitor.export_report()
print(report)  # JSON 格式
```

---

**相关**: [向量搜索](vector-search.md) | [性能基准](../tests/benchmarks/README.md)
