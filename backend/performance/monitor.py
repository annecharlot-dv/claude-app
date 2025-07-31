"""
Performance Monitoring System
Real-time performance tracking with alerting and metrics collection
"""
import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any]
    tenant_id: Optional[str] = None

class PerformanceMonitor:
    """Real-time performance monitoring with alerting"""
    
    def __init__(self, max_history: int = 1000):
        self.metrics_history = deque(maxlen=max_history)
        self.alerts = []
        self.thresholds = {
            "response_time": 200,  # 200ms
            "database_query": 100,  # 100ms
            "memory_usage": 80,     # 80%
            "cpu_usage": 80,        # 80%
            "cache_hit_rate": 95    # 95%
        }
        self.monitoring_active = False
        self.system_stats = {}
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        self.monitoring_active = True
        
        # Start system monitoring
        asyncio.create_task(self._monitor_system_resources())
        asyncio.create_task(self._cleanup_old_metrics())
        
        logger.info("🔍 Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("⏹️ Performance monitoring stopped")
    
    async def record_metric(self, metric_type: str, value: float, metadata: Dict = None, tenant_id: str = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            metadata=metadata or {},
            tenant_id=tenant_id
        )
        
        self.metrics_history.append(metric)
        
        # Check for threshold violations
        await self._check_thresholds(metric)
    
    async def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric violates thresholds and create alerts"""
        threshold = self.thresholds.get(metric.metric_type)
        if threshold is None:
            return
        
        # Different threshold logic for different metrics
        violation = False
        if metric.metric_type in ["response_time", "database_query"]:
            violation = metric.value > threshold
        elif metric.metric_type in ["memory_usage", "cpu_usage"]:
            violation = metric.value > threshold
        elif metric.metric_type == "cache_hit_rate":
            violation = metric.value < threshold
        
        if violation:
            alert = {
                "timestamp": metric.timestamp,
                "type": "threshold_violation",
                "metric_type": metric.metric_type,
                "value": metric.value,
                "threshold": threshold,
                "tenant_id": metric.tenant_id,
                "metadata": metric.metadata
            }
            self.alerts.append(alert)
            
            logger.warning(f"🚨 Performance alert: {metric.metric_type} = {metric.value} (threshold: {threshold})")
    
    async def _monitor_system_resources(self):
        """Monitor system resources continuously"""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                await self.record_metric("cpu_usage", cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                await self.record_metric("memory_usage", memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                await self.record_metric("disk_usage", disk.percent)
                
                # Network I/O
                network = psutil.net_io_counters()
                await self.record_metric("network_bytes_sent", network.bytes_sent)
                await self.record_metric("network_bytes_recv", network.bytes_recv)
                
                # Update system stats
                self.system_stats = {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "network_bytes_sent": network.bytes_sent,
                    "network_bytes_recv": network.bytes_recv,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics and alerts"""
        while self.monitoring_active:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Clean up old alerts
                self.alerts = [
                    alert for alert in self.alerts
                    if alert["timestamp"] > cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error cleaning up metrics: {e}")
                await asyncio.sleep(3600)
    
    async def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance metrics summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            metric for metric in self.metrics_history
            if metric.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No metrics available for the specified time period"}
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in recent_metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for metric_type, values in metrics_by_type.items():
            summary[metric_type] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "p95": self._calculate_percentile(values, 95),
                "p99": self._calculate_percentile(values, 99)
            }
        
        return {
            "time_period_hours": hours,
            "total_metrics": len(recent_metrics),
            "metrics": summary,
            "system_stats": self.system_stats,
            "alerts_count": len([a for a in self.alerts if a["timestamp"] > cutoff_time])
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        
        return sorted_values[index]
    
    async def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get slowest database queries"""
        db_metrics = [
            metric for metric in self.metrics_history
            if metric.metric_type == "database_query"
        ]
        
        # Sort by value (execution time) descending
        slow_queries = sorted(db_metrics, key=lambda x: x.value, reverse=True)[:limit]
        
        return [
            {
                "timestamp": metric.timestamp.isoformat(),
                "execution_time_ms": metric.value,
                "query": metric.metadata.get("query", "Unknown"),
                "collection": metric.metadata.get("collection", "Unknown"),
                "tenant_id": metric.tenant_id
            }
            for metric in slow_queries
        ]
    
    async def get_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alerts
            if alert["timestamp"] > cutoff_time
        ]
        
        # Convert datetime objects to strings for JSON serialization
        for alert in recent_alerts:
            alert["timestamp"] = alert["timestamp"].isoformat()
        
        return recent_alerts
    
    async def get_tenant_performance(self, tenant_id: str, hours: int = 1) -> Dict[str, Any]:
        """Get performance metrics for a specific tenant"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        tenant_metrics = [
            metric for metric in self.metrics_history
            if metric.tenant_id == tenant_id and metric.timestamp > cutoff_time
        ]
        
        if not tenant_metrics:
            return {"message": f"No metrics available for tenant {tenant_id}"}
        
        # Calculate tenant-specific statistics
        response_times = [m.value for m in tenant_metrics if m.metric_type == "response_time"]
        db_queries = [m.value for m in tenant_metrics if m.metric_type == "database_query"]
        
        return {
            "tenant_id": tenant_id,
            "time_period_hours": hours,
            "total_requests": len(response_times),
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "p95_response_time": self._calculate_percentile(response_times, 95) if response_times else 0,
            "total_db_queries": len(db_queries),
            "avg_db_query_time": sum(db_queries) / len(db_queries) if db_queries else 0,
            "p95_db_query_time": self._calculate_percentile(db_queries, 95) if db_queries else 0
        }

# Decorator for automatic performance monitoring
def monitor_performance(metric_type: str = "response_time"):
    """Decorator to automatically monitor function performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Extract tenant_id if available
                tenant_id = None
                if hasattr(args[0], 'tenant_id'):
                    tenant_id = args[0].tenant_id
                elif 'tenant_id' in kwargs:
                    tenant_id = kwargs['tenant_id']
                
                # Record metric
                await performance_monitor.record_metric(
                    metric_type=metric_type,
                    value=execution_time,
                    metadata={
                        "function": func.__name__,
                        "module": func.__module__
                    },
                    tenant_id=tenant_id
                )
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                await performance_monitor.record_metric(
                    metric_type=f"{metric_type}_error",
                    value=execution_time,
                    metadata={
                        "function": func.__name__,
                        "module": func.__module__,
                        "error": str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

async def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor