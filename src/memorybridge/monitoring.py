"""
MemoryBridge 监控系统

提供：
- 性能指标收集
- 健康检查
- 使用统计
- 告警通知
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, List[MetricPoint]] = {
            "api_latency": [],
            "requests_per_second": [],
            "memory_usage": [],
            "storage_size": [],
            "cache_hit_rate": [],
        }
    
    def record(self, metric_name: str, value: float, labels: Optional[Dict] = None):
        """记录指标"""
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            value=value,
            labels=labels or {},
        )
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(point)
        
        # 清理过期数据
        self._cleanup(metric_name)
    
    def _cleanup(self, metric_name: str):
        """清理过期指标"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        self.metrics[metric_name] = [
            p for p in self.metrics[metric_name]
            if p.timestamp > cutoff
        ]
    
    def get_average(self, metric_name: str, minutes: int = 5) -> Optional[float]:
        """获取平均值"""
        if metric_name not in self.metrics:
            return None
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent = [p for p in self.metrics[metric_name] if p.timestamp > cutoff]
        
        if not recent:
            return None
        
        return sum(p.value for p in recent) / len(recent)
    
    def get_percentile(self, metric_name: str, percentile: float, minutes: int = 5) -> Optional[float]:
        """获取百分位数"""
        if metric_name not in self.metrics:
            return None
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent = [p.value for p in self.metrics[metric_name] if p.timestamp > cutoff]
        
        if not recent:
            return None
        
        recent.sort()
        index = int(len(recent) * percentile / 100)
        return recent[min(index, len(recent) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        for metric_name in self.metrics:
            avg = self.get_average(metric_name)
            if avg is not None:
                summary[metric_name] = {
                    "avg": avg,
                    "p95": self.get_percentile(metric_name, 95),
                    "p99": self.get_percentile(metric_name, 99),
                }
        
        return summary
    
    def export(self, format: str = "json") -> str:
        """导出指标"""
        data = {
            name: [
                {"timestamp": p.timestamp.isoformat(), "value": p.value, "labels": p.labels}
                for p in points
            ]
            for name, points in self.metrics.items()
        }
        
        if format == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, bool] = {}
        self.last_check: Optional[datetime] = None
    
    async def check_storage(self, storage) -> bool:
        """检查存储健康"""
        try:
            start = time.perf_counter()
            await storage.count()
            elapsed = time.perf_counter() - start
            
            self.checks["storage"] = elapsed < 1.0  # 1 秒内响应
            return self.checks["storage"]
        except Exception:
            self.checks["storage"] = False
            return False
    
    async def check_database(self, db_connection) -> bool:
        """检查数据库连接"""
        try:
            # Ping 数据库
            await asyncio.wait_for(db_connection.ping(), timeout=5.0)
            self.checks["database"] = True
            return True
        except Exception:
            self.checks["database"] = False
            return False
    
    async def check_vector_search(self, vector_store) -> bool:
        """检查向量搜索"""
        try:
            start = time.perf_counter()
            await vector_store.search("test", limit=1)
            elapsed = time.perf_counter() - start
            
            self.checks["vector_search"] = elapsed < 2.0
            return self.checks["vector_search"]
        except Exception:
            self.checks["vector_search"] = False
            return False
    
    async def run_all_checks(self) -> Dict[str, bool]:
        """运行所有检查"""
        self.last_check = datetime.now(timezone.utc)
        return self.checks.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        all_healthy = all(self.checks.values()) if self.checks else False
        
        return {
            "healthy": all_healthy,
            "checks": self.checks,
            "last_check": self.last_check.isoformat() if self.last_check else None,
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.health = HealthChecker()
        self.start_time = datetime.now(timezone.utc)
        
        # 性能计数器
        self.request_count = 0
        self.error_count = 0
    
    def record_request(self, latency_ms: float, endpoint: str = "api"):
        """记录请求"""
        self.request_count += 1
        self.metrics.record("api_latency", latency_ms, {"endpoint": endpoint})
        self.metrics.record("requests_per_second", 1)
    
    def record_error(self, error_type: str):
        """记录错误"""
        self.error_count += 1
        self.metrics.record("errors", 1, {"type": error_type})
    
    def record_cache_hit(self, hit: bool):
        """记录缓存命中"""
        self.metrics.record("cache_hit_rate", 1 if hit else 0)
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def get_uptime(self) -> timedelta:
        """获取运行时间"""
        return datetime.now(timezone.utc) - self.start_time
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "uptime": str(self.get_uptime()),
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate": self.get_error_rate(),
            "metrics": self.metrics.get_summary(),
            "health": self.health.get_status(),
        }
    
    def export_report(self) -> str:
        """导出监控报告"""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "uptime": str(self.get_uptime()),
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate": self.get_error_rate(),
            "metrics": self.metrics.export(),
            "health": self.health.get_status(),
        }
        return json.dumps(report, indent=2, default=str)


# 全局监控实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """获取全局监控实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_endpoint(endpoint_name: str):
    """装饰器：监控端点性能"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_monitor()
            start = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.perf_counter() - start) * 1000
                monitor.record_request(latency_ms, endpoint_name)
                return result
            except Exception as e:
                monitor.record_error(type(e).__name__)
                raise
        
        return wrapper
    return decorator
