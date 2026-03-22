"""
测试监控系统
"""

import pytest
import asyncio
import time

from memorybridge.monitoring import MetricsCollector, HealthChecker, PerformanceMonitor, get_monitor


class TestMetricsCollector:
    """测试指标收集器"""
    
    def test_record_metric(self):
        collector = MetricsCollector()
        collector.record("api_latency", 150.5)
        
        avg = collector.get_average("api_latency")
        assert avg is not None
        assert avg == 150.5
    
    def test_get_average(self):
        collector = MetricsCollector()
        
        for i in range(10):
            collector.record("requests", float(i))
        
        avg = collector.get_average("requests")
        assert avg is not None
        assert 4.0 <= avg <= 5.0  # 平均值约 4.5
    
    def test_get_percentile(self):
        collector = MetricsCollector()
        
        for i in range(100):
            collector.record("latency", float(i))
        
        p95 = collector.get_percentile("latency", 95)
        assert p95 is not None
        assert 90.0 <= p95 <= 100.0
    
    def test_cleanup_old_metrics(self):
        collector = MetricsCollector(retention_hours=0)  # 立即过期
        
        collector.record("test", 1.0)
        
        # 等待清理（实际会保留至少 1 条）
        assert "test" in collector.metrics
    
    def test_get_summary(self):
        collector = MetricsCollector()
        
        for _ in range(5):
            collector.record("api_latency", 100.0)
        
        summary = collector.get_summary()
        assert "api_latency" in summary
        assert "avg" in summary["api_latency"]


class TestHealthChecker:
    """测试健康检查器"""
    
    def test_init(self):
        checker = HealthChecker()
        assert checker.checks == {}
        assert checker.last_check is None
    
    def test_get_status_empty(self):
        checker = HealthChecker()
        status = checker.get_status()
        
        assert "healthy" in status
        assert status["healthy"] is False  # 没有检查结果
    
    def test_get_status_with_checks(self):
        checker = HealthChecker()
        checker.checks["storage"] = True
        checker.checks["database"] = True
        
        status = checker.get_status()
        assert status["healthy"] is True
        assert "storage" in status["checks"]


class TestPerformanceMonitor:
    """测试性能监控器"""
    
    def test_init(self):
        monitor = PerformanceMonitor()
        assert monitor.request_count == 0
        assert monitor.error_count == 0
    
    def test_record_request(self):
        monitor = PerformanceMonitor()
        monitor.record_request(50.0, endpoint="search")
        
        assert monitor.request_count == 1
        
        status = monitor.get_status()
        assert "metrics" in status
    
    def test_record_error(self):
        monitor = PerformanceMonitor()
        
        monitor.record_request(50.0)
        monitor.record_error("ValueError")
        
        assert monitor.error_count == 1
        assert monitor.get_error_rate() == 0.5
    
    def test_get_uptime(self):
        monitor = PerformanceMonitor()
        uptime = monitor.get_uptime()
        
        assert uptime.total_seconds() >= 0
    
    def test_get_status(self):
        monitor = PerformanceMonitor()
        monitor.record_request(100.0)
        
        status = monitor.get_status()
        
        assert "uptime" in status
        assert "requests" in status
        assert "health" in status
    
    def test_export_report(self):
        monitor = PerformanceMonitor()
        monitor.record_request(50.0)
        
        report = monitor.export_report()
        
        assert "uptime" in report
        assert "requests" in report
        assert "metrics" in report


class TestGlobalMonitor:
    """测试全局监控实例"""
    
    def test_get_monitor_singleton(self):
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        
        assert monitor1 is monitor2


class TestMonitorDecorator:
    """测试监控装饰器"""
    
    def test_monitor_endpoint(self):
        from memorybridge.monitoring import monitor_endpoint
        
        @monitor_endpoint("test_endpoint")
        async def test_func():
            await asyncio.sleep(0.01)
            return "result"
        
        # 运行测试
        result = asyncio.run(test_func())
        assert result == "result"
        
        # 检查监控
        monitor = get_monitor()
        assert monitor.request_count >= 1
