"""
性能优化模块

提供：
- 缓存层
- 连接池
- 批量操作
- 查询优化
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps
import hashlib

T = TypeVar('T')


class LRUCache:
    """LRU 缓存"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict] = {}
        self.access_order: List[str] = []
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # 检查 TTL
        if datetime.now(timezone.utc) > entry["expires_at"]:
            self.delete(key)
            return None
        
        # 更新访问顺序
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return entry["value"]
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        # 清理超出大小的缓存
        while len(self.cache) >= self.max_size and self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
        }
        
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        now = datetime.now(timezone.utc)
        valid_entries = sum(
            1 for entry in self.cache.values()
            if now <= entry["expires_at"]
        )
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = LRUCache(max_size=100, ttl_seconds=ttl)
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            key = f"{key_prefix}{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # 缓存结果
            cache.set(key, result)
            return result
        
        return wrapper
    return decorator


class BatchProcessor:
    """批量处理器"""
    
    def __init__(
        self,
        batch_size: int = 100,
        flush_interval: float = 1.0,
    ):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue: List[Any] = []
        self.last_flush = datetime.now(timezone.utc)
        self._lock = asyncio.Lock()
    
    async def add(self, item: Any):
        """添加项目到队列"""
        async with self._lock:
            self.queue.append(item)
            
            # 检查是否需要刷新
            if len(self.queue) >= self.batch_size:
                await self._flush()
            elif (datetime.now(timezone.utc) - self.last_flush).total_seconds() > self.flush_interval:
                await self._flush()
    
    async def _flush(self):
        """刷新队列（子类实现）"""
        if not self.queue:
            return
        
        # 子类重写此方法
        self.queue.clear()
        self.last_flush = datetime.now(timezone.utc)
    
    async def flush(self):
        """强制刷新"""
        async with self._lock:
            await self._flush()
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return len(self.queue)


class ConnectionPool:
    """连接池（简化版）"""
    
    def __init__(
        self,
        max_connections: int = 10,
        min_connections: int = 2,
    ):
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connections: List[Any] = []
        self.in_use: set = set()
        self._lock = asyncio.Lock()
    
    async def initialize(self, create_connection: Callable):
        """初始化连接池"""
        async with self._lock:
            for _ in range(self.min_connections):
                conn = await create_connection()
                self.connections.append(conn)
    
    async def acquire(self) -> Any:
        """获取连接"""
        async with self._lock:
            # 尝试获取空闲连接
            for conn in self.connections:
                if conn not in self.in_use:
                    self.in_use.add(conn)
                    return conn
            
            # 创建新连接（如果未达上限）
            if len(self.connections) < self.max_connections:
                # 需要外部提供创建连接的函数
                raise RuntimeError("No available connections")
            
            # 等待连接释放
            await asyncio.sleep(0.1)
            return await self.acquire()
    
    async def release(self, conn: Any):
        """释放连接"""
        async with self._lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
    
    async def close(self):
        """关闭连接池"""
        async with self._lock:
            self.connections.clear()
            self.in_use.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        return {
            "total_connections": len(self.connections),
            "in_use": len(self.in_use),
            "available": len(self.connections) - len(self.in_use),
            "max_connections": self.max_connections,
        }


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def optimize_search_query(query: str) -> str:
        """优化搜索查询"""
        # 移除多余空格
        query = " ".join(query.split())
        
        # 移除特殊字符
        query = "".join(c for c in query if c.isalnum() or c.isspace())
        
        return query.strip()
    
    @staticmethod
    def build_composite_index_fields(fields: List[str]) -> str:
        """构建复合索引字段"""
        return "_".join(sorted(fields))
    
    @staticmethod
    def suggest_indexes(usage_stats: Dict[str, int]) -> List[str]:
        """根据使用统计建议索引"""
        suggestions = []
        
        # 分析查询模式
        for field, count in usage_stats.items():
            if count > 100:  # 高频字段
                suggestions.append(f"CREATE INDEX IF NOT EXISTS idx_{field} ON vectors({field})")
        
        return suggestions
