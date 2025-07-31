import React, { useState, useEffect } from 'react';

/**
 * Payload CMS Performance Dashboard
 * Monitors Payload-specific operations and PostgreSQL integration performance
 */

interface PayloadMetrics {
  operations: {
    [key: string]: {
      count: number;
      avgTime: number;
      p95Time: number;
      errorRate: number;
    };
  };
  collections: {
    [key: string]: {
      documents: number;
      queries: number;
      avgQueryTime: number;
    };
  };
  cache: {
    hitRate: number;
    size: number;
    invalidations: number;
  };
  database: {
    connectionPool: {
      active: number;
      idle: number;
      total: number;
    };
    slowQueries: Array<{
      query: string;
      time: number;
      collection: string;
    }>;
  };
}

const PayloadPerformanceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PayloadMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(1); // hours
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchMetrics();
    
    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [timeRange, autoRefresh]);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`/api/payload/metrics?hours=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('payload-token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch Payload metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getPerformanceColor = (value: number, threshold: number, inverse = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading Payload metrics...</span>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-8 text-center text-gray-500">
        Failed to load performance metrics
      </div>
    );
  }

  return (
    <div className="p-6 bg-white">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Payload CMS Performance</h2>
        
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
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="mr-2"
            />
            Auto Refresh
          </label>
        </div>
      </div>

      {/* Operation Performance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Create Operations</h3>
          <div className="text-3xl font-bold text-blue-600">
            {metrics.operations.create ? formatTime(metrics.operations.create.avgTime) : 'N/A'}
          </div>
          <div className="text-sm text-blue-700 mt-1">
            P95: {metrics.operations.create ? formatTime(metrics.operations.create.p95Time) : 'N/A'}
          </div>
          <div className="text-sm text-blue-700">
            Count: {metrics.operations.create?.count || 0}
          </div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 mb-2">Read Operations</h3>
          <div className="text-3xl font-bold text-green-600">
            {metrics.operations.read ? formatTime(metrics.operations.read.avgTime) : 'N/A'}
          </div>
          <div className="text-sm text-green-700 mt-1">
            P95: {metrics.operations.read ? formatTime(metrics.operations.read.p95Time) : 'N/A'}
          </div>
          <div className="text-sm text-green-700">
            Count: {metrics.operations.read?.count || 0}
          </div>
        </div>

        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-purple-900 mb-2">Update Operations</h3>
          <div className="text-3xl font-bold text-purple-600">
            {metrics.operations.update ? formatTime(metrics.operations.update.avgTime) : 'N/A'}
          </div>
          <div className="text-sm text-purple-700 mt-1">
            P95: {metrics.operations.update ? formatTime(metrics.operations.update.p95Time) : 'N/A'}
          </div>
          <div className="text-sm text-purple-700">
            Count: {metrics.operations.update?.count || 0}
          </div>
        </div>
      </div>

      {/* Collection Performance */}
      <div className="bg-white border border-gray-200 p-4 rounded-lg mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Collection Performance</h3>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Documents
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Queries
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Query Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(metrics.collections).map(([collection, stats]) => (
                <tr key={collection}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {collection}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {stats.documents.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {stats.queries.toLocaleString()}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getPerformanceColor(stats.avgQueryTime, 100, true)}`}>
                    {formatTime(stats.avgQueryTime)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cache and Database Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white border border-gray-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Performance</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Hit Rate</span>
              <span className={`font-semibold ${getPerformanceColor(metrics.cache.hitRate, 95)}`}>
                {metrics.cache.hitRate.toFixed(1)}%
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Cache Size</span>
              <span className="font-semibold text-gray-900">
                {(metrics.cache.size / 1024 / 1024).toFixed(1)} MB
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Invalidations</span>
              <span className="font-semibold text-yellow-600">
                {metrics.cache.invalidations}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Database Connection Pool</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Active Connections</span>
              <span className="font-semibold text-blue-600">
                {metrics.database.connectionPool.active}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Idle Connections</span>
              <span className="font-semibold text-green-600">
                {metrics.database.connectionPool.idle}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Pool Size</span>
              <span className="font-semibold text-gray-900">
                {metrics.database.connectionPool.total}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Slow Queries */}
      {metrics.database.slowQueries.length > 0 && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-red-900 mb-4">Slow Queries (&gt;100ms)</h3>
          
          <div className="space-y-2">
            {metrics.database.slowQueries.slice(0, 5).map((query, index) => (
              <div key={index} className="bg-white p-3 rounded border">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="text-sm font-mono text-gray-800 truncate">
                      {query.query}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Collection: {query.collection}
                    </div>
                  </div>
                  <div className="text-sm font-semibold text-red-600 ml-4">
                    {formatTime(query.time)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-200 p-4 rounded-lg">
        <h4 className="text-md font-semibold text-blue-900 mb-2">Payload CMS Performance Tips</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Keep create/update operations under 500ms for good user experience</li>
          <li>• Read operations should complete in under 100ms</li>
          <li>• Cache hit rates above 95% indicate optimal caching strategy</li>
          <li>• Monitor connection pool utilization to prevent bottlenecks</li>
          <li>• Use field-level access control to reduce query complexity</li>
        </ul>
      </div>
    </div>
  );
};

export default PayloadPerformanceDashboard;