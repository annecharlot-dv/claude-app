# Performance Optimization Guide

## Overview

This guide covers the enterprise-grade performance optimizations implemented for the Claude platform, targeting sub-100ms database queries, sub-2.5s page loads, and >99% cache hit rates.

## Performance Targets

### Backend Performance
- **Database Queries**: 95% under 100ms
- **API Response Time**: 95% under 200ms
- **Cache Hit Rate**: >99% for static content
- **Memory Usage**: <80% of available RAM
- **CPU Usage**: <80% under normal load

### Frontend Performance
- **Largest Contentful Paint (LCP)**: <2.5s
- **First Input Delay (FID)**: <100ms
- **Cumulative Layout Shift (CLS)**: <0.1
- **Bundle Size**: <500KB gzipped
- **Time to Interactive**: <3s

## Architecture Overview

### Multi-Layer Caching System

The platform implements a sophisticated 3-layer caching system:

1. **L1 Cache (Hot Data)**: <1MB, <5min TTL
   - Frequently accessed data
   - User sessions, active pages
   - In-memory storage

2. **L2 Cache (Warm Data)**: <10MB, <30min TTL
   - Moderately accessed data
   - Page lists, form configurations
   - In-memory storage

3. **L3 Cache (Cold Data)**: <100MB, <24h TTL
   - Rarely accessed data
   - Templates, archived content
   - In-memory storage

### Database Optimization

#### Indexes
Comprehensive indexing strategy for all collections:

```javascript
// Users collection
{ "tenant_id": 1, "email": 1 } // Unique compound index
{ "tenant_id": 1, "role": 1 }
{ "tenant_id": 1, "is_active": 1 }
{ "tenant_id": 1, "last_login": -1 }

// Pages collection
{ "tenant_id": 1, "slug": 1 } // Unique compound index
{ "tenant_id": 1, "status": 1 }
{ "searchKeywords": "text" } // Full-text search

// Leads collection
{ "tenant_id": 1, "status": 1 }
{ "tenant_id": 1, "created_at": -1 }
{ "tenant_id": 1, "assigned_to": 1 }
```

#### Query Optimization
- Automatic tenant_id filtering
- Pagination with skip/limit
- Projection to reduce data transfer
- Query performance monitoring

### API Performance

#### Middleware Stack
1. **Performance Middleware**: Request/response timing
2. **Caching Middleware**: Intelligent response caching
3. **Compression Middleware**: Gzip compression for responses
4. **Monitoring Middleware**: Real-time metrics collection

#### Response Optimization
- Automatic pagination for large datasets
- Field selection to reduce payload size
- ETags for client-side caching
- Compression for JSON responses

### Frontend Optimization

#### Bundle Optimization
- Code splitting with React.lazy()
- Vendor chunk separation
- Tree shaking for unused code
- Dynamic imports for routes

#### Performance Monitoring
- Core Web Vitals tracking
- API call performance monitoring
- Bundle size monitoring
- Memory usage tracking

## Implementation Details

### Backend Components

#### 1. Database Optimizer (`backend/performance/database_optimizer.py`)
- Automatic index creation
- Query performance monitoring
- Slow query detection and logging
- Collection performance analysis

#### 2. Cache Manager (`backend/performance/cache_manager.py`)
- Multi-layer caching with intelligent promotion
- Tag-based cache invalidation
- LRU eviction policy
- Cache statistics and monitoring

#### 3. Performance Monitor (`backend/performance/monitor.py`)
- Real-time performance metrics collection
- System resource monitoring
- Alert generation for threshold violations
- Performance analytics and reporting

#### 4. API Optimizer (`backend/performance/api_optimizer.py`)
- Response caching middleware
- Gzip compression
- Request deduplication
- Performance headers

### Frontend Components

#### 1. Performance Tracker (`frontend/src/utils/performance.js`)
- Core Web Vitals monitoring
- API call performance tracking
- Bundle size monitoring
- Memory usage tracking

#### 2. Optimized API Service (`frontend/src/services/api.js`)
- Request caching and deduplication
- Performance tracking for all API calls
- Intelligent cache invalidation
- Error handling and retry logic

#### 3. Performance Dashboard (`frontend/src/components/PerformanceDashboard.js`)
- Real-time performance metrics display
- Cache statistics visualization
- System resource monitoring
- Performance alerts and recommendations

## Configuration

### Environment Variables

#### Backend
```bash
# Performance settings
ENABLE_PERFORMANCE_MONITORING=true
CACHE_ENABLED=true
COMPRESSION_ENABLED=true
SLOW_QUERY_THRESHOLD=100  # milliseconds

# Database optimization
DB_POOL_SIZE=20
DB_POOL_MIN=2
DB_IDLE_TIMEOUT=10000
DB_ACQUIRE_TIMEOUT=60000
```

#### Frontend
```bash
# Performance settings
REACT_APP_ENABLE_PERFORMANCE_TRACKING=true
REACT_APP_API_TIMEOUT=10000
DISABLE_HOT_RELOAD=false  # Set to true for production builds
ANALYZE_BUNDLES=false     # Set to true to analyze bundle sizes
```

### Cache Configuration

#### TTL Settings
```python
# Cache TTL configuration (seconds)
TTL_CONFIG = {
    "l1": 300,    # 5 minutes
    "l2": 1800,   # 30 minutes
    "l3": 86400   # 24 hours
}

# Size limits (bytes)
SIZE_LIMITS = {
    "l1": 1024 * 1024,      # 1MB
    "l2": 10 * 1024 * 1024, # 10MB
    "l3": 100 * 1024 * 1024 # 100MB
}
```

#### Cache Tags
```python
# Cache tagging for intelligent invalidation
CACHE_TAGS = {
    "tenant_data": ["tenant:{tenant_id}"],
    "user_data": ["tenant:{tenant_id}", "user:{user_id}"],
    "page_data": ["tenant:{tenant_id}", "pages"],
    "form_data": ["tenant:{tenant_id}", "forms"],
    "lead_data": ["tenant:{tenant_id}", "leads"]
}
```

## Monitoring and Alerting

### Performance Metrics

#### Database Metrics
- Query execution time (avg, p95, p99)
- Slow query count and details
- Connection pool utilization
- Index usage statistics

#### API Metrics
- Response time (avg, p95, p99)
- Request rate and error rate
- Cache hit/miss ratios
- Payload sizes

#### System Metrics
- CPU usage percentage
- Memory usage and availability
- Disk I/O and usage
- Network throughput

### Alert Thresholds

```python
ALERT_THRESHOLDS = {
    "response_time": 200,      # 200ms
    "database_query": 100,     # 100ms
    "memory_usage": 80,        # 80%
    "cpu_usage": 80,          # 80%
    "cache_hit_rate": 95,     # 95%
    "error_rate": 5           # 5%
}
```

### Performance Dashboard

Access the performance dashboard at `/performance` (admin users only):

- Real-time performance metrics
- Cache statistics and layer distribution
- System resource utilization
- Performance alerts and recommendations
- Historical performance trends

## Best Practices

### Database Queries
1. Always include `tenant_id` in queries for multi-tenant isolation
2. Use indexes for all frequently queried fields
3. Implement pagination for large result sets
4. Use projection to limit returned fields
5. Monitor slow queries and optimize regularly

### API Design
1. Implement proper caching headers (ETags, Cache-Control)
2. Use compression for all text-based responses
3. Implement request deduplication for identical requests
4. Add performance monitoring to all endpoints
5. Use appropriate HTTP status codes

### Frontend Optimization
1. Implement code splitting for large applications
2. Use lazy loading for images and components
3. Minimize bundle sizes with tree shaking
4. Implement proper error boundaries
5. Monitor Core Web Vitals continuously

### Caching Strategy
1. Cache frequently accessed data in L1 cache
2. Use appropriate TTL values based on data volatility
3. Implement tag-based cache invalidation
4. Monitor cache hit rates and adjust strategy
5. Use cache warming for critical data

## Performance Testing

### Running Performance Tests

```bash
# Backend performance tests
cd backend
python -m pytest performance/test_suite.py -v

# Frontend performance tests
cd frontend
npm run test:performance

# Load testing with artillery
npm install -g artillery
artillery run performance/load-test.yml
```

### Test Scenarios

1. **Database Performance**: Query execution times under various loads
2. **API Performance**: Response times for all endpoints
3. **Cache Performance**: Hit rates and invalidation efficiency
4. **Frontend Performance**: Core Web Vitals under various conditions
5. **Load Testing**: System behavior under 10x normal traffic

## Troubleshooting

### Common Performance Issues

#### Slow Database Queries
1. Check if appropriate indexes exist
2. Analyze query execution plans
3. Review query complexity and joins
4. Consider data archiving for large collections

#### Low Cache Hit Rates
1. Review cache TTL settings
2. Check cache invalidation logic
3. Analyze cache key generation
4. Monitor cache size limits

#### High Memory Usage
1. Review cache size limits
2. Check for memory leaks in application code
3. Analyze object retention patterns
4. Consider garbage collection tuning

#### Poor Frontend Performance
1. Analyze bundle sizes and optimize
2. Check for unnecessary re-renders
3. Optimize image loading and sizing
4. Review third-party library usage

### Performance Debugging

#### Backend Debugging
```python
# Enable detailed performance logging
import logging
logging.getLogger('performance').setLevel(logging.DEBUG)

# Monitor specific queries
from performance.monitor import monitor_performance

@monitor_performance("custom_operation")
async def my_operation():
    # Your code here
    pass
```

#### Frontend Debugging
```javascript
// Access performance tracker
console.log(window.performanceTracker.getMetrics());

// Monitor specific operations
import performanceTracker from './utils/performance';
performanceTracker.recordMetric('CUSTOM_OPERATION', duration, metadata);
```

## Deployment Considerations

### Production Optimizations
1. Enable all performance middleware
2. Set appropriate cache TTL values
3. Configure database connection pooling
4. Enable response compression
5. Set up performance monitoring alerts

### Scaling Considerations
1. Implement horizontal scaling for API servers
2. Use database read replicas for read-heavy workloads
3. Consider CDN for static assets
4. Implement proper load balancing
5. Monitor resource utilization continuously

## Conclusion

This performance optimization implementation provides enterprise-grade performance monitoring and optimization for the Claude platform. Regular monitoring and tuning based on the metrics collected will ensure optimal performance as the platform scales.

For questions or issues, refer to the performance monitoring dashboard or check the application logs for detailed performance metrics and alerts.