import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiService from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const PerformanceDashboard = () => {
  const [timeRange, setTimeRange] = useState(1); // hours
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // Fetch performance metrics
  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['performance-metrics', timeRange],
    queryFn: () => apiService.getPerformanceMetrics(timeRange),
    refetchInterval: refreshInterval,
    staleTime: 10000, // 10 seconds
  });

  // Fetch cache statistics
  const { data: cacheStats, isLoading: cacheLoading, refetch: refetchCache } = useQuery({
    queryKey: ['cache-stats'],
    queryFn: () => apiService.getCacheStats(),
    refetchInterval: refreshInterval,
    staleTime: 10000,
  });

  // Auto-refresh functionality
  useEffect(() => {
    const interval = setInterval(() => {
      refetchMetrics();
      refetchCache();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, refetchMetrics, refetchCache]);

  const formatTime = (ms) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getStatusColor = (value, threshold, inverse = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? 'text-green-600' : 'text-red-600';
  };

  if (metricsLoading || cacheLoading) {
    return <LoadingSpinner message="Loading performance data..." />;
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Performance Dashboard</h2>
        
        <div className="flex space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
          </select>
          
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={10000}>10s refresh</option>
            <option value={30000}>30s refresh</option>
            <option value={60000}>1m refresh</option>
            <option value={0}>Manual only</option>
          </select>
        </div>
      </div>

      {/* Core Web Vitals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Response Time</h3>
          <div className="text-3xl font-bold text-blue-600">
            {metrics?.metrics?.response_time ? formatTime(metrics.metrics.response_time.avg) : 'N/A'}
          </div>
          <div className="text-sm text-blue-700 mt-1">
            P95: {metrics?.metrics?.response_time ? formatTime(metrics.metrics.response_time.p95) : 'N/A'}
          </div>
          <div className={`text-sm mt-1 ${getStatusColor(metrics?.metrics?.response_time?.avg || 0, 200, true)}`}>
            Target: &lt;200ms
          </div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 mb-2">Cache Hit Rate</h3>
          <div className="text-3xl font-bold text-green-600">
            {cacheStats?.hit_rate ? `${cacheStats.hit_rate}%` : 'N/A'}
          </div>
          <div className="text-sm text-green-700 mt-1">
            {cacheStats?.total_entries || 0} entries
          </div>
          <div className={`text-sm mt-1 ${getStatusColor(cacheStats?.hit_rate || 0, 95)}`}>
            Target: &gt;95%
          </div>
        </div>

        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-purple-900 mb-2">Database Queries</h3>
          <div className="text-3xl font-bold text-purple-600">
            {metrics?.metrics?.database_query ? formatTime(metrics.metrics.database_query.avg) : 'N/A'}
          </div>
          <div className="text-sm text-purple-700 mt-1">
            P95: {metrics?.metrics?.database_query ? formatTime(metrics.metrics.database_query.p95) : 'N/A'}
          </div>
          <div className={`text-sm mt-1 ${getStatusColor(metrics?.metrics?.database_query?.avg || 0, 100, true)}`}>
            Target: &lt;100ms
          </div>
        </div>
      </div>

      {/* System Resources */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white border border-gray-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Resources</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">CPU Usage</span>
              <span className={`font-semibold ${getStatusColor(metrics?.system_stats?.cpu_percent || 0, 80, true)}`}>
                {metrics?.system_stats?.cpu_percent ? `${metrics.system_stats.cpu_percent.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Memory Usage</span>
              <span className={`font-semibold ${getStatusColor(metrics?.system_stats?.memory_percent || 0, 80, true)}`}>
                {metrics?.system_stats?.memory_percent ? `${metrics.system_stats.memory_percent.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Available Memory</span>
              <span className="font-semibold text-gray-900">
                {metrics?.system_stats?.memory_available ? formatBytes(metrics.system_stats.memory_available) : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Statistics</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Cache Size</span>
              <span className="font-semibold text-gray-900">
                {cacheStats?.size_mb ? `${cacheStats.size_mb} MB` : 'N/A'}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Hits</span>
              <span className="font-semibold text-green-600">
                {cacheStats?.hits || 0}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Misses</span>
              <span className="font-semibold text-red-600">
                {cacheStats?.misses || 0}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Invalidations</span>
              <span className="font-semibold text-yellow-600">
                {cacheStats?.invalidations || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Cache Layer Distribution */}
      {cacheStats?.layer_distribution && (
        <div className="bg-white border border-gray-200 p-4 rounded-lg mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Layer Distribution</h3>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {cacheStats.layer_distribution.l1}
              </div>
              <div className="text-sm text-gray-600">L1 Cache (Hot)</div>
              <div className="text-xs text-gray-500">&lt;5min TTL</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {cacheStats.layer_distribution.l2}
              </div>
              <div className="text-sm text-gray-600">L2 Cache (Warm)</div>
              <div className="text-xs text-gray-500">&lt;30min TTL</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {cacheStats.layer_distribution.l3}
              </div>
              <div className="text-sm text-gray-600">L3 Cache (Cold)</div>
              <div className="text-xs text-gray-500">&lt;24h TTL</div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Metrics Summary */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Metrics Summary</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Total Requests</span>
            <div className="font-semibold text-gray-900">
              {metrics?.total_metrics || 0}
            </div>
          </div>
          
          <div>
            <span className="text-gray-600">Time Period</span>
            <div className="font-semibold text-gray-900">
              {timeRange} hour{timeRange !== 1 ? 's' : ''}
            </div>
          </div>
          
          <div>
            <span className="text-gray-600">Alerts</span>
            <div className="font-semibold text-red-600">
              {metrics?.alerts_count || 0}
            </div>
          </div>
          
          <div>
            <span className="text-gray-600">Last Updated</span>
            <div className="font-semibold text-gray-900">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-200 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-blue-900 mb-2">Performance Tips</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Response times under 200ms provide the best user experience</li>
          <li>• Cache hit rates above 95% indicate optimal caching strategy</li>
          <li>• Database queries should complete in under 100ms for good performance</li>
          <li>• Monitor system resources to prevent performance degradation</li>
        </ul>
      </div>
    </div>
  );
};

export default PerformanceDashboard;