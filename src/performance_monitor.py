"""
Performance Monitoring Module for Symbiosis v1.2

Tracks metrics across all system components, identifies bottlenecks,
and ensures <100ms API response times.
"""

import time
import psutil
import os
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import json
import functools
import traceback

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Types of system components we monitor."""
    API_ENDPOINT = "api_endpoint"
    TOKEN_GENERATION = "token_generation"
    DATABASE = "database"
    TRANSCRIPTION = "transcription"
    SPECTRAL_ANALYSIS = "spectral_analysis"
    FILE_IO = "file_io"
    MEMORY = "memory"
    CPU = "cpu"
    WEBSOCKET = "websocket"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    component: str
    component_type: ComponentType
    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_msg: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Benchmark:
    """Performance benchmark target."""
    component: str
    operation: str
    target_ms: float
    warning_threshold_ms: float
    critical_threshold_ms: float


@dataclass
class Alert:
    """Performance alert."""
    level: AlertLevel
    component: str
    operation: str
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for all system components.

    Features:
    - Real-time metric collection
    - Benchmark comparison
    - Slow query detection
    - Memory leak detection
    - CPU spike detection
    - Alert generation
    """

    def __init__(self,
                 history_size: int = 1000,
                 memory_window_seconds: int = 300,
                 check_interval_seconds: int = 10,
                 start_background_monitor: bool = True):
        """
        Initialize performance monitor.

        Args:
            history_size: Number of metrics to keep in memory
            memory_window_seconds: Window for memory trend analysis
            check_interval_seconds: Interval for background monitoring
            start_background_monitor: Whether to start background monitoring thread
        """
        self.history_size = history_size
        self.memory_window_seconds = memory_window_seconds
        self.check_interval_seconds = check_interval_seconds

        # Metrics storage
        self.metrics: deque = deque(maxlen=history_size)
        self.slow_queries: List[PerformanceMetric] = []
        self.alerts: deque = deque(maxlen=100)

        # Component tracking
        self.component_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'error_count': 0,
            'last_update': None
        })

        # Benchmarks
        self.benchmarks: Dict[str, Benchmark] = {}
        self._setup_default_benchmarks()

        # Memory tracking
        self.memory_samples: deque = deque(maxlen=memory_window_seconds // 2)
        self.initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        # Background monitoring
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()

        # Start background monitor if requested
        if start_background_monitor:
            self.start_monitoring()

    def _setup_default_benchmarks(self):
        """Setup standard performance benchmarks."""
        benchmarks = [
            Benchmark(
                component="token_generator",
                operation="generate_tokens",
                target_ms=50,
                warning_threshold_ms=75,
                critical_threshold_ms=150
            ),
            Benchmark(
                component="api",
                operation="endpoint_response",
                target_ms=100,
                warning_threshold_ms=150,
                critical_threshold_ms=300
            ),
            Benchmark(
                component="session",
                operation="load_session",
                target_ms=200,
                warning_threshold_ms=300,
                critical_threshold_ms=500
            ),
            Benchmark(
                component="database",
                operation="write_query",
                target_ms=10,
                warning_threshold_ms=25,
                critical_threshold_ms=100
            ),
            Benchmark(
                component="database",
                operation="read_query",
                target_ms=5,
                warning_threshold_ms=15,
                critical_threshold_ms=50
            ),
            Benchmark(
                component="transcriber",
                operation="process_audio",
                target_ms=500,
                warning_threshold_ms=750,
                critical_threshold_ms=2000
            ),
            Benchmark(
                component="spectral",
                operation="analyze_signal",
                target_ms=100,
                warning_threshold_ms=150,
                critical_threshold_ms=500
            ),
            Benchmark(
                component="file_io",
                operation="write_file",
                target_ms=50,
                warning_threshold_ms=100,
                critical_threshold_ms=500
            ),
            Benchmark(
                component="websocket",
                operation="broadcast_message",
                target_ms=20,
                warning_threshold_ms=50,
                critical_threshold_ms=200
            ),
        ]

        for bench in benchmarks:
            key = f"{bench.component}:{bench.operation}"
            self.benchmarks[key] = bench

    def record_metric(self,
                     component: str,
                     component_type: ComponentType,
                     operation: str,
                     duration_ms: float,
                     success: bool = True,
                     error_msg: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Record a performance metric.

        Args:
            component: Component name
            component_type: Type of component
            operation: Operation performed
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            error_msg: Error message if failed
            metadata: Additional metadata
        """
        metric = PerformanceMetric(
            component=component,
            component_type=component_type,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_msg=error_msg,
            metadata=metadata or {}
        )

        with self.lock:
            self.metrics.append(metric)

            # Update component statistics
            stats = self.component_stats[component]
            stats['count'] += 1
            stats['total_time'] += duration_ms
            stats['min_time'] = min(stats['min_time'], duration_ms)
            stats['max_time'] = max(stats['max_time'], duration_ms)
            if not success:
                stats['error_count'] += 1
            stats['last_update'] = datetime.now()

            # Check against benchmarks
            self._check_benchmark(component, operation, duration_ms)

            # Detect slow queries
            if duration_ms > 500:  # Slow query threshold
                self.slow_queries.append(metric)
                self.slow_queries = self.slow_queries[-100:]  # Keep last 100

    def _check_benchmark(self, component: str, operation: str, duration_ms: float):
        """Check metric against benchmarks and generate alerts."""
        key = f"{component}:{operation}"
        if key not in self.benchmarks:
            return

        bench = self.benchmarks[key]

        if duration_ms >= bench.critical_threshold_ms:
            self._add_alert(
                AlertLevel.CRITICAL,
                component,
                operation,
                f"Critical: {operation} took {duration_ms:.2f}ms (threshold: {bench.critical_threshold_ms}ms)",
                duration_ms,
                bench.critical_threshold_ms
            )
        elif duration_ms >= bench.warning_threshold_ms:
            self._add_alert(
                AlertLevel.WARNING,
                component,
                operation,
                f"Warning: {operation} took {duration_ms:.2f}ms (threshold: {bench.warning_threshold_ms}ms)",
                duration_ms,
                bench.warning_threshold_ms
            )

    def _add_alert(self,
                   level: AlertLevel,
                   component: str,
                   operation: str,
                   message: str,
                   metric_value: float,
                   threshold: float):
        """Add a performance alert."""
        with self.lock:
            alert = Alert(
                level=level,
                component=component,
                operation=operation,
                message=message,
                metric_value=metric_value,
                threshold=threshold
            )
            self.alerts.append(alert)

            # Log alert
            log_func = getattr(logger, level.value)
            log_func(f"[{component}] {message}")

    def timing_decorator(self, component: str, component_type: ComponentType):
        """
        Decorator to automatically time function execution.

        Usage:
            @monitor.timing_decorator("token_gen", ComponentType.TOKEN_GENERATION)
            def generate_tokens(data):
                # function body
                pass
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                operation = func.__name__
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    self.record_metric(
                        component=component,
                        component_type=component_type,
                        operation=operation,
                        duration_ms=duration_ms,
                        success=True,
                        metadata={'args_count': len(args), 'kwargs_count': len(kwargs)}
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    self.record_metric(
                        component=component,
                        component_type=component_type,
                        operation=operation,
                        duration_ms=duration_ms,
                        success=False,
                        error_msg=str(e)
                    )

                    raise

            return wrapper
        return decorator

    def get_component_stats(self, component: Optional[str] = None) -> Dict:
        """
        Get statistics for component(s).

        Args:
            component: Specific component or None for all

        Returns:
            Dictionary of component statistics
        """
        with self.lock:
            if component:
                if component not in self.component_stats:
                    return {}

                stats = self.component_stats[component].copy()
                count = stats['count']
                if count > 0:
                    stats['avg_time'] = stats['total_time'] / count
                    stats['error_rate'] = (stats['error_count'] / count) * 100
                return stats

            else:
                result = {}
                for comp, stats in self.component_stats.items():
                    stats_copy = stats.copy()
                    count = stats_copy['count']
                    if count > 0:
                        stats_copy['avg_time'] = stats_copy['total_time'] / count
                        stats_copy['error_rate'] = (stats_copy['error_count'] / count) * 100
                    result[comp] = stats_copy
                return result

    def get_system_performance(self) -> Dict:
        """Get overall system performance metrics."""
        with self.lock:
            process = psutil.Process(os.getpid())

            # Memory info
            mem_info = process.memory_info()
            current_memory_mb = mem_info.rss / 1024 / 1024
            memory_increase = current_memory_mb - self.initial_memory

            # CPU info
            cpu_percent = process.cpu_percent(interval=0.1)

            # Get recent metrics (last minute)
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_metrics = [m for m in self.metrics
                            if m.timestamp >= one_minute_ago]

            # Calculate success rate
            success_count = sum(1 for m in recent_metrics if m.success)
            total_count = len(recent_metrics)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 100

            # Average response time
            avg_response_time = 0
            if recent_metrics:
                avg_response_time = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)

            return {
                'timestamp': now.isoformat(),
                'memory_mb': round(current_memory_mb, 2),
                'memory_increase_mb': round(memory_increase, 2),
                'cpu_percent': round(cpu_percent, 2),
                'metrics_count': len(self.metrics),
                'recent_metrics_count': total_count,
                'success_rate': round(success_rate, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'slow_queries_count': len(self.slow_queries),
                'active_alerts': len(self.alerts)
            }

    def get_slow_queries(self, limit: int = 50) -> List[Dict]:
        """Get slow queries (>500ms operations)."""
        with self.lock:
            queries = self.slow_queries[-limit:]
            return [asdict(q) for q in queries]

    def get_alerts(self, level: Optional[AlertLevel] = None, limit: int = 50) -> List[Dict]:
        """
        Get recent alerts.

        Args:
            level: Filter by alert level or None for all
            limit: Maximum alerts to return

        Returns:
            List of alert dictionaries
        """
        with self.lock:
            alerts = list(self.alerts)

            if level:
                alerts = [a for a in alerts if a.level == level]

            # Convert to dict and handle datetime serialization
            result = []
            for alert in alerts[-limit:]:
                alert_dict = asdict(alert)
                alert_dict['level'] = alert.level.value
                alert_dict['timestamp'] = alert.timestamp.isoformat()
                result.append(alert_dict)

            return result

    def get_benchmarks(self) -> Dict:
        """Get all defined benchmarks."""
        result = {}
        for key, bench in self.benchmarks.items():
            result[key] = {
                'component': bench.component,
                'operation': bench.operation,
                'target_ms': bench.target_ms,
                'warning_threshold_ms': bench.warning_threshold_ms,
                'critical_threshold_ms': bench.critical_threshold_ms
            }
        return result

    def check_memory_leak(self) -> Optional[Dict]:
        """
        Detect potential memory leaks.

        Returns:
            Dict with leak info or None if no leak detected
        """
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / 1024 / 1024

        with self.lock:
            self.memory_samples.append({
                'timestamp': datetime.now(),
                'memory_mb': mem_mb
            })

            # Need at least 10 samples (5 minutes)
            if len(self.memory_samples) < 10:
                return None

            # Calculate trend
            samples_list = list(self.memory_samples)
            early_avg = sum(s['memory_mb'] for s in samples_list[:len(samples_list)//2]) / (len(samples_list)//2)
            late_avg = sum(s['memory_mb'] for s in samples_list[len(samples_list)//2:]) / (len(samples_list)//2)

            increase_percent = ((late_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0

            # Alert if >50% increase over window
            if increase_percent > 50:
                return {
                    'detected': True,
                    'early_avg_mb': round(early_avg, 2),
                    'late_avg_mb': round(late_avg, 2),
                    'increase_percent': round(increase_percent, 2),
                    'current_memory_mb': round(mem_mb, 2)
                }

        return None

    def check_cpu_spike(self, threshold_percent: float = 80) -> Optional[Dict]:
        """
        Check for CPU spikes.

        Args:
            threshold_percent: Alert if CPU usage exceeds this

        Returns:
            Dict with spike info or None if no spike
        """
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=1.0)

        if cpu_percent > threshold_percent:
            return {
                'detected': True,
                'cpu_percent': round(cpu_percent, 2),
                'threshold_percent': threshold_percent,
                'timestamp': datetime.now().isoformat()
            }

        return None

    def start_monitoring(self):
        """Start background monitoring thread."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring thread."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                # Check for memory leaks
                leak_info = self.check_memory_leak()
                if leak_info and leak_info['detected']:
                    self._add_alert(
                        AlertLevel.WARNING,
                        "system",
                        "memory_leak_detection",
                        f"Potential memory leak detected: {leak_info['increase_percent']:.1f}% increase",
                        leak_info['increase_percent'],
                        50.0
                    )

                # Check for CPU spikes
                cpu_spike = self.check_cpu_spike(threshold_percent=80)
                if cpu_spike and cpu_spike['detected']:
                    self._add_alert(
                        AlertLevel.CRITICAL,
                        "system",
                        "cpu_spike",
                        f"CPU usage spike: {cpu_spike['cpu_percent']:.1f}%",
                        cpu_spike['cpu_percent'],
                        80.0
                    )

                time.sleep(self.check_interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval_seconds)

    def get_report(self) -> str:
        """Generate a performance report."""
        stats = self.get_component_stats()
        performance = self.get_system_performance()
        slow_queries = self.get_slow_queries(limit=10)
        alerts = self.get_alerts(limit=10)

        report = []
        report.append("=" * 80)
        report.append("SYMBIOSIS V1.2 PERFORMANCE REPORT")
        report.append("=" * 80)

        # System metrics
        report.append("\nSYSTEM METRICS:")
        report.append(f"  Timestamp: {performance['timestamp']}")
        report.append(f"  Memory: {performance['memory_mb']}MB (+{performance['memory_increase_mb']}MB)")
        report.append(f"  CPU Usage: {performance['cpu_percent']}%")
        report.append(f"  Success Rate: {performance['success_rate']}%")
        report.append(f"  Avg Response Time: {performance['avg_response_time_ms']:.2f}ms")

        # Component statistics
        report.append("\nCOMPONENT STATISTICS:")
        for component, comp_stats in sorted(stats.items()):
            report.append(f"  {component}:")
            report.append(f"    Calls: {comp_stats['count']}")
            report.append(f"    Avg Time: {comp_stats.get('avg_time', 0):.2f}ms")
            report.append(f"    Min/Max: {comp_stats['min_time']:.2f}ms / {comp_stats['max_time']:.2f}ms")
            if comp_stats['error_count'] > 0:
                report.append(f"    Errors: {comp_stats['error_count']} ({comp_stats.get('error_rate', 0):.1f}%)")

        # Slow queries
        if slow_queries:
            report.append("\nSLOW QUERIES (>500ms):")
            for query in slow_queries[-5:]:
                report.append(f"  {query['component']}.{query['operation']}: {query['duration_ms']:.2f}ms")

        # Recent alerts
        if alerts:
            report.append("\nRECENT ALERTS:")
            for alert in alerts[-5:]:
                report.append(f"  [{alert['level'].upper()}] {alert['component']}: {alert['message']}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)

    def reset_metrics(self):
        """Reset all collected metrics."""
        with self.lock:
            self.metrics.clear()
            self.slow_queries.clear()
            self.alerts.clear()
            self.component_stats.clear()
            self.memory_samples.clear()
            self.initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        logger.info("Performance metrics reset")


# Global monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor
