"""
Tests for Agent 36: Performance Monitoring & Benchmarking

Tests cover:
- Metric recording and tracking
- Benchmark comparisons
- Slow query detection
- Memory leak detection
- CPU spike detection
- Alert generation
- Performance reporting
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from performance_monitor import (
    PerformanceMonitor,
    ComponentType,
    AlertLevel,
    PerformanceMetric,
    Benchmark,
    Alert,
    get_performance_monitor
)


class TestPerformanceMetricRecording:
    """Test basic metric recording functionality."""

    def test_record_metric_success(self):
        """Test recording successful operation metric."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor.record_metric(
            component="test_component",
            component_type=ComponentType.API_ENDPOINT,
            operation="test_op",
            duration_ms=50.0,
            success=True
        )

        assert len(monitor.metrics) == 1
        metric = list(monitor.metrics)[0]
        assert metric.component == "test_component"
        assert metric.operation == "test_op"
        assert metric.duration_ms == 50.0
        assert metric.success is True

    def test_record_metric_failure(self):
        """Test recording failed operation metric."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor.record_metric(
            component="test_component",
            component_type=ComponentType.DATABASE,
            operation="failed_op",
            duration_ms=100.0,
            success=False,
            error_msg="Connection timeout"
        )

        metric = list(monitor.metrics)[0]
        assert metric.success is False
        assert metric.error_msg == "Connection timeout"

    def test_record_metric_with_metadata(self):
        """Test recording metric with metadata."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        metadata = {'table': 'users', 'rows': 100}
        monitor.record_metric(
            component="database",
            component_type=ComponentType.DATABASE,
            operation="read_query",
            duration_ms=25.0,
            metadata=metadata
        )

        metric = list(monitor.metrics)[0]
        assert metric.metadata == metadata

    def test_history_size_limit(self):
        """Test that metric history respects size limit."""
        monitor = PerformanceMonitor(history_size=100)

        # Add more metrics than history size
        for i in range(150):
            monitor.record_metric(
                component="test",
                component_type=ComponentType.API_ENDPOINT,
                operation="op",
                duration_ms=i
            )

        assert len(monitor.metrics) == 100


class TestComponentStatistics:
    """Test component statistics tracking."""

    def test_component_stats_aggregation(self):
        """Test that component statistics are properly aggregated."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Record multiple metrics for same component
        for duration in [50, 75, 100, 125]:
            monitor.record_metric(
                component="token_gen",
                component_type=ComponentType.TOKEN_GENERATION,
                operation="generate",
                duration_ms=duration
            )

        stats = monitor.get_component_stats("token_gen")
        assert stats['count'] == 4
        assert stats['total_time'] == 350
        assert stats['min_time'] == 50
        assert stats['max_time'] == 125
        assert stats['avg_time'] == 87.5

    def test_component_error_tracking(self):
        """Test error rate calculation."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # 3 successful, 2 failed
        for _ in range(3):
            monitor.record_metric(
                component="api",
                component_type=ComponentType.API_ENDPOINT,
                operation="request",
                duration_ms=50,
                success=True
            )

        for _ in range(2):
            monitor.record_metric(
                component="api",
                component_type=ComponentType.API_ENDPOINT,
                operation="request",
                duration_ms=100,
                success=False,
                error_msg="Timeout"
            )

        stats = monitor.get_component_stats("api")
        assert stats['count'] == 5
        assert stats['error_count'] == 2
        assert stats['error_rate'] == 40.0

    def test_all_component_stats(self):
        """Test getting statistics for all components."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Add metrics for different components
        for i in range(3):
            monitor.record_metric(
                component="api",
                component_type=ComponentType.API_ENDPOINT,
                operation="request",
                duration_ms=50 + i
            )

        for i in range(2):
            monitor.record_metric(
                component="db",
                component_type=ComponentType.DATABASE,
                operation="query",
                duration_ms=10 + i
            )

        all_stats = monitor.get_component_stats()
        assert len(all_stats) == 2
        assert 'api' in all_stats
        assert 'db' in all_stats


class TestBenchmarking:
    """Test benchmark comparison and alert generation."""

    def test_benchmark_setup(self):
        """Test that default benchmarks are set up."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        benchmarks = monitor.get_benchmarks()
        assert len(benchmarks) > 0

        # Check specific benchmarks
        assert "token_generator:generate_tokens" in benchmarks
        assert "api:endpoint_response" in benchmarks
        assert "database:write_query" in benchmarks

    def test_benchmark_alert_warning(self):
        """Test warning alert when metric exceeds warning threshold."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # API endpoint has warning at 150ms
        monitor.record_metric(
            component="api",
            component_type=ComponentType.API_ENDPOINT,
            operation="endpoint_response",
            duration_ms=160.0  # Above warning threshold
        )

        alerts = monitor.get_alerts()
        assert len(alerts) > 0
        assert alerts[0]['level'] == 'warning'

    def test_benchmark_alert_critical(self):
        """Test critical alert when metric exceeds critical threshold."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Session load has critical at 500ms
        monitor.record_metric(
            component="session",
            component_type=ComponentType.API_ENDPOINT,
            operation="load_session",
            duration_ms=550.0  # Above critical threshold
        )

        alerts = monitor.get_alerts(level=AlertLevel.CRITICAL)
        assert len(alerts) > 0
        assert alerts[0]['level'] == 'critical'

    def test_no_alert_within_threshold(self):
        """Test that no alert is generated within threshold."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor.record_metric(
            component="token_generator",
            component_type=ComponentType.TOKEN_GENERATION,
            operation="generate_tokens",
            duration_ms=40.0  # Well below warning threshold
        )

        alerts = monitor.get_alerts()
        assert len(alerts) == 0


class TestSlowQueryDetection:
    """Test slow query detection and tracking."""

    def test_slow_query_detection(self):
        """Test that queries >500ms are tracked."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor.record_metric(
            component="database",
            component_type=ComponentType.DATABASE,
            operation="complex_query",
            duration_ms=750.0
        )

        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0]['duration_ms'] == 750.0

    def test_normal_query_not_tracked(self):
        """Test that queries <500ms are not tracked as slow."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor.record_metric(
            component="database",
            component_type=ComponentType.DATABASE,
            operation="simple_query",
            duration_ms=100.0
        )

        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 0

    def test_slow_query_limit(self):
        """Test that slow query list respects size limit."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Add more slow queries than limit
        for i in range(150):
            monitor.record_metric(
                component="db",
                component_type=ComponentType.DATABASE,
                operation="query",
                duration_ms=500 + i
            )

        slow_queries = monitor.get_slow_queries(limit=100)
        assert len(slow_queries) <= 100


class TestMemoryLeakDetection:
    """Test memory leak detection."""

    def test_memory_leak_detection_insufficient_samples(self):
        """Test that leak detection requires enough samples."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Should return None with insufficient samples
        result = monitor.check_memory_leak()
        assert result is None

    def test_memory_trend_calculation(self):
        """Test memory trend calculation."""
        monitor = PerformanceMonitor(memory_window_seconds=100)

        # Manually add memory samples to simulate trend
        for i in range(10):
            monitor.memory_samples.append({
                'timestamp': datetime.now(),
                'memory_mb': 100 + i
            })

        # Early samples: 100-104, Late samples: 105-109
        # Trend should show increase
        result = monitor.check_memory_leak()
        if result:
            assert result['increase_percent'] > 0


class TestCPUSpikeDetection:
    """Test CPU spike detection."""

    def test_cpu_spike_below_threshold(self):
        """Test that no spike is reported below threshold."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        result = monitor.check_cpu_spike(threshold_percent=99)
        # Result should be None or show no spike (depends on actual CPU usage)
        if result:
            assert result['detected'] is False or result['cpu_percent'] < 99

    def test_cpu_spike_threshold_configuration(self):
        """Test CPU spike threshold can be configured."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Test with very high threshold
        result = monitor.check_cpu_spike(threshold_percent=1000)
        # Should never trigger with unrealistic threshold
        assert result is None or result['cpu_percent'] < 1000


class TestTimingDecorator:
    """Test the timing decorator functionality."""

    def test_timing_decorator_success(self):
        """Test timing decorator on successful function."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        @monitor.timing_decorator("test", ComponentType.API_ENDPOINT)
        def slow_operation():
            time.sleep(0.05)
            return "result"

        result = slow_operation()
        assert result == "result"
        assert len(monitor.metrics) == 1

        metric = list(monitor.metrics)[0]
        assert metric.component == "test"
        assert metric.operation == "slow_operation"
        assert metric.duration_ms >= 50
        assert metric.success is True

    def test_timing_decorator_failure(self):
        """Test timing decorator on failing function."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        @monitor.timing_decorator("test", ComponentType.API_ENDPOINT)
        def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_operation()

        assert len(monitor.metrics) == 1
        metric = list(monitor.metrics)[0]
        assert metric.success is False
        assert "Test error" in metric.error_msg

    def test_timing_decorator_with_arguments(self):
        """Test timing decorator with function arguments."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        @monitor.timing_decorator("test", ComponentType.API_ENDPOINT)
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5
        assert len(monitor.metrics) == 1


class TestSystemPerformance:
    """Test system-level performance metrics."""

    def test_system_performance_metrics(self):
        """Test retrieval of system performance metrics."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Record some metrics
        for _ in range(5):
            monitor.record_metric(
                component="api",
                component_type=ComponentType.API_ENDPOINT,
                operation="request",
                duration_ms=50.0
            )

        perf = monitor.get_system_performance()

        assert 'timestamp' in perf
        assert 'memory_mb' in perf
        assert 'cpu_percent' in perf
        assert 'metrics_count' in perf
        assert perf['metrics_count'] == 5
        assert 'success_rate' in perf

    def test_success_rate_calculation(self):
        """Test success rate calculation in system metrics."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Add 3 successful, 1 failed
        for _ in range(3):
            monitor.record_metric(
                component="api",
                component_type=ComponentType.API_ENDPOINT,
                operation="request",
                duration_ms=50.0,
                success=True
            )

        monitor.record_metric(
            component="api",
            component_type=ComponentType.API_ENDPOINT,
            operation="request",
            duration_ms=100.0,
            success=False
        )

        perf = monitor.get_system_performance()
        # Success rate should be 75%
        assert 74 <= perf['success_rate'] <= 76  # Allow for timing variations


class TestAlertSystem:
    """Test alert generation and retrieval."""

    def test_alert_creation(self):
        """Test that alerts are properly created."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor._add_alert(
            AlertLevel.WARNING,
            "test_component",
            "test_op",
            "Test message",
            100.0,
            50.0
        )

        alerts = monitor.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]['level'] == 'warning'
        assert alerts[0]['component'] == 'test_component'

    def test_alert_filtering_by_level(self):
        """Test filtering alerts by level."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor._add_alert(AlertLevel.INFO, "comp", "op", "msg", 1, 1)
        monitor._add_alert(AlertLevel.WARNING, "comp", "op", "msg", 1, 1)
        monitor._add_alert(AlertLevel.CRITICAL, "comp", "op", "msg", 1, 1)

        critical_alerts = monitor.get_alerts(level=AlertLevel.CRITICAL)
        assert len(critical_alerts) == 1
        assert critical_alerts[0]['level'] == 'critical'

    def test_alert_limit(self):
        """Test that alert retrieval respects limit."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        for i in range(30):
            monitor._add_alert(
                AlertLevel.INFO,
                "comp",
                "op",
                f"Alert {i}",
                i,
                i
            )

        alerts = monitor.get_alerts(limit=10)
        assert len(alerts) <= 10


class TestReporting:
    """Test performance reporting functionality."""

    def test_performance_report_generation(self):
        """Test that performance report can be generated."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Add some data
        for _ in range(5):
            monitor.record_metric(
                component="api",
                component_type=ComponentType.API_ENDPOINT,
                operation="request",
                duration_ms=75.0
            )

        report = monitor.get_report()

        assert "SYMBIOSIS V1.2 PERFORMANCE REPORT" in report
        assert "SYSTEM METRICS" in report
        assert "COMPONENT STATISTICS" in report
        assert "Memory:" in report
        assert "CPU Usage:" in report

    def test_report_with_slow_queries(self):
        """Test that report includes slow queries."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor.record_metric(
            component="db",
            component_type=ComponentType.DATABASE,
            operation="query",
            duration_ms=1000.0
        )

        report = monitor.get_report()
        assert "SLOW QUERIES" in report
        assert "1000.00" in report

    def test_report_with_alerts(self):
        """Test that report includes recent alerts."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        monitor._add_alert(
            AlertLevel.CRITICAL,
            "api",
            "request",
            "Test critical alert",
            200.0,
            100.0
        )

        report = monitor.get_report()
        assert "RECENT ALERTS" in report
        assert "CRITICAL" in report


class TestMetricsReset:
    """Test metrics reset functionality."""

    def test_reset_metrics(self):
        """Test that reset clears all metrics."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        # Add some data
        monitor.record_metric(
            component="api",
            component_type=ComponentType.API_ENDPOINT,
            operation="request",
            duration_ms=50.0
        )

        monitor._add_alert(
            AlertLevel.WARNING,
            "api",
            "request",
            "Test",
            100.0,
            50.0
        )

        assert len(monitor.metrics) > 0
        assert len(monitor.alerts) > 0

        monitor.reset_metrics()

        assert len(monitor.metrics) == 0
        assert len(monitor.alerts) == 0
        assert len(monitor.slow_queries) == 0


class TestGlobalMonitor:
    """Test global monitor singleton."""

    def test_global_monitor_singleton(self):
        """Test that global monitor is a singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2

    def test_global_monitor_functional(self):
        """Test that global monitor works correctly."""
        monitor = get_performance_monitor()

        monitor.record_metric(
            component="test",
            component_type=ComponentType.API_ENDPOINT,
            operation="test_op",
            duration_ms=50.0
        )

        stats = monitor.get_component_stats("test")
        assert stats['count'] >= 1


class TestBackgroundMonitoring:
    """Test background monitoring functionality."""

    def test_start_stop_monitoring(self):
        """Test starting and stopping background monitoring."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        assert monitor.monitoring is False

        monitor.start_monitoring()
        assert monitor.monitoring is True

        monitor.stop_monitoring()
        assert monitor.monitoring is False

    def test_monitor_thread_daemon(self):
        """Test that monitor thread is daemon."""
        monitor = PerformanceMonitor(start_background_monitor=False)
        monitor.start_monitoring()

        assert monitor.monitor_thread.daemon is True

        monitor.stop_monitoring()


class TestThreadSafety:
    """Test thread safety of monitoring."""

    def test_concurrent_metric_recording(self):
        """Test recording metrics from multiple threads."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        def record_metrics():
            for i in range(100):
                monitor.record_metric(
                    component="api",
                    component_type=ComponentType.API_ENDPOINT,
                    operation="request",
                    duration_ms=50 + i
                )

        threads = [threading.Thread(target=record_metrics) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have recorded 500 metrics without issues
        assert len(monitor.metrics) == 500

    def test_concurrent_stat_retrieval(self):
        """Test retrieving stats while recording."""
        monitor = PerformanceMonitor(start_background_monitor=False)

        def record_metrics():
            for i in range(100):
                monitor.record_metric(
                    component="api",
                    component_type=ComponentType.API_ENDPOINT,
                    operation="request",
                    duration_ms=50 + i
                )
                time.sleep(0.001)

        def get_stats():
            for _ in range(50):
                monitor.get_component_stats()
                monitor.get_system_performance()
                time.sleep(0.01)

        record_thread = threading.Thread(target=record_metrics)
        stats_thread = threading.Thread(target=get_stats)

        record_thread.start()
        stats_thread.start()

        record_thread.join()
        stats_thread.join()

        # Should not crash
        assert len(monitor.metrics) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
