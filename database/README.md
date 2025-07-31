# PostgreSQL Database Architecture for Claude Platform

## Overview

This document outlines the PostgreSQL database architecture for the Claude multi-tenant SaaS platform, designed for enterprise-scale performance with complete tenant isolation using Row-Level Security (RLS).

## Architecture Highlights

- **Multi-tenant with RLS**: Complete data isolation using PostgreSQL's Row-Level Security
- **Performance Optimized**: Sub-100ms query times with advanced indexing strategies
- **Scalable Design**: Supports 1000+ tenants with 100GB+ data
- **Materialized Views**: Pre-computed analytics for dashboard performance
- **Connection Pooling**: Optimized connection management for high concurrency
- **Partitioning**: Time-based partitioning for large tables

## Database Schema

### Core Tables

#### Tenants
- **Purpose**: Platform-level tenant management
- **RLS**: Disabled (platform-level access)
- **Key Indexes**: subdomain, custom_domain, industry_module

#### Users
- **Purpose**: Multi-tenant user management with role-based access
- **RLS**: Enabled with tenant_id filtering
- **Key Indexes**: (tenant_id, email), (tenant_id, role), (tenant_id, is_active)

#### Pages
- **Purpose**: CMS content with full-text search
- **RLS**: Enabled with tenant_id filtering
- **Key Indexes**: (tenant_id, slug), full-text search on content

#### Leads
- **Purpose**: Lead management with conversion tracking
- **RLS**: Enabled with tenant_id filtering
- **Key Indexes**: (tenant_id, status), (tenant_id, email), conversion funnel

#### Forms & Form Submissions
- **Purpose**: Dynamic form builder with submissions
- **RLS**: Enabled (submissions inherit from forms)
- **Partitioning**: Monthly partitions for submissions

## Performance Features

### 1. Row-Level Security (RLS)
```sql
-- Automatic tenant filtering
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### 2. Advanced Indexing
```sql
-- Composite indexes for common queries
CREATE INDEX idx_users_tenant_role_active 
ON users(tenant_id, role, is_active) 
WHERE is_active = true;

-- Covering indexes to avoid table lookups
CREATE INDEX idx_users_tenant_email_covering 
ON users(tenant_id, email) 
INCLUDE (first_name, last_name, role, is_active);
```

### 3. Materialized Views
```sql
-- Pre-computed tenant performance metrics
CREATE MATERIALIZED VIEW tenant_performance_summary AS
SELECT 
    tenant_id,
    COUNT(DISTINCT users.id) as total_users,
    COUNT(DISTINCT pages.id) as total_pages,
    COUNT(DISTINCT leads.id) as total_leads
FROM tenants t
LEFT JOIN users ON t.id = users.tenant_id
-- ... additional joins and calculations
```

### 4. Partitioning
```sql
-- Time-based partitioning for high-volume tables
CREATE TABLE form_submissions (
    -- columns
) PARTITION BY RANGE (created_at);

CREATE TABLE form_submissions_2024_01 PARTITION OF form_submissions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Connection Management

### Connection Pools
- **Main Pool**: 5-20 connections for application queries
- **Analytics Pool**: 2-10 connections for reporting (longer timeouts)
- **Background Pool**: 1-5 connections for maintenance tasks

### Pool Configuration
```python
# Optimized for Vercel PostgreSQL
pool = await asyncpg.create_pool(
    database_url,
    min_size=5,
    max_size=20,
    command_timeout=30,
    server_settings={
        'shared_buffers': '256MB',
        'effective_cache_size': '1GB',
        'work_mem': '4MB',
        'statement_timeout': '30s'
    }
)
```

## Query Optimization

### 1. Tenant-Aware Queries
All queries automatically include tenant filtering:
```python
async def find_many(self, table: str, filters: Dict, tenant_id: str):
    # Automatically adds tenant_id filter
    query = f"SELECT * FROM {table} WHERE tenant_id = $1"
    # ... additional filters
```

### 2. Query Performance Monitoring
```sql
-- Automatic slow query detection
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- 100ms threshold
ORDER BY mean_exec_time DESC;
```

### 3. Index Usage Analysis
```sql
-- Monitor index effectiveness
SELECT 
    schemaname, tablename, indexname,
    idx_scan, idx_tup_read,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes;
```

## Migration Strategy

### Phase 1: Schema Creation
1. Run initial schema migration (`001_initial_schema.sql`)
2. Create materialized views (`002_materialized_views.sql`)
3. Add performance indexes (`003_performance_indexes.sql`)

### Phase 2: Data Migration
1. Export MongoDB data to JSON
2. Transform data to PostgreSQL format
3. Import using COPY commands for performance
4. Verify data integrity

### Phase 3: Application Updates
1. Replace MongoDB adapter with PostgreSQL adapter
2. Update queries to use SQL instead of MongoDB syntax
3. Implement tenant context setting
4. Test performance benchmarks

## Performance Targets

### Database Performance
- **Query Response Time**: 95% under 100ms
- **Connection Acquisition**: Under 10ms
- **Cache Hit Ratio**: >95% for buffer cache
- **Index Usage**: >90% for all queries

### Scalability Targets
- **Concurrent Connections**: 100+ simultaneous
- **Tenant Capacity**: 1000+ active tenants
- **Data Volume**: 100GB+ with consistent performance
- **Query Throughput**: 10,000+ queries/second

## Monitoring & Alerting

### Key Metrics
1. **Query Performance**: Slow query detection and analysis
2. **Connection Health**: Pool utilization and wait times
3. **Index Usage**: Unused index identification
4. **Table Bloat**: Dead tuple monitoring
5. **Cache Performance**: Buffer and index cache hit ratios

### Automated Maintenance
```sql
-- Scheduled maintenance tasks
SELECT cron.schedule('refresh-performance-views', '*/15 * * * *', 
    'SELECT refresh_performance_views();');

SELECT cron.schedule('cleanup-performance-metrics', '0 2 * * *', 
    'SELECT cleanup_old_performance_metrics();');
```

## Security Features

### 1. Row-Level Security
- Complete tenant data isolation
- Automatic policy enforcement
- No application-level filtering required

### 2. Connection Security
- SSL/TLS encryption for all connections
- Connection pooling with authentication
- Prepared statements to prevent SQL injection

### 3. Audit Trail
- All data changes tracked with timestamps
- Performance metrics for compliance
- User activity logging

## Payload CMS Integration

### Multi-tenant Collections
```typescript
// Automatic tenant filtering in Payload
access: {
  read: ({ req: { user } }) => ({
    tenantId: { equals: user?.tenantId }
  })
}
```

### Performance Optimizations
- Connection pool sharing with main application
- Materialized view integration for admin dashboards
- Optimized webhook handling

## Deployment Considerations

### Vercel PostgreSQL
- Optimized for serverless environments
- Connection pooling essential for performance
- Materialized view refresh scheduling

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
POSTGRES_POOL_MIN=5
POSTGRES_POOL_MAX=20
POSTGRES_STATEMENT_TIMEOUT=30000
```

### Scaling Strategies
1. **Read Replicas**: For analytics and reporting
2. **Connection Pooling**: PgBouncer for additional optimization
3. **Caching**: Redis for application-level caching
4. **Partitioning**: Automatic partition management

## Troubleshooting

### Common Issues
1. **Slow Queries**: Check pg_stat_statements for optimization
2. **Connection Exhaustion**: Monitor pool utilization
3. **Lock Contention**: Analyze pg_locks for blocking queries
4. **High Memory Usage**: Tune work_mem and shared_buffers

### Performance Debugging
```sql
-- Identify performance bottlenecks
SELECT * FROM check_performance_alerts();

-- Analyze table statistics
SELECT * FROM table_bloat_stats;

-- Monitor index usage
SELECT * FROM index_usage_stats;
```

## Best Practices

### Query Optimization
1. Always include tenant_id in WHERE clauses
2. Use prepared statements for repeated queries
3. Implement proper pagination with LIMIT/OFFSET
4. Use covering indexes to avoid table lookups

### Connection Management
1. Use connection pooling for all database access
2. Set appropriate timeouts for different query types
3. Monitor connection pool utilization
4. Implement proper error handling and retries

### Maintenance
1. Regular VACUUM ANALYZE on high-update tables
2. Monitor and refresh materialized views
3. Clean up old performance metrics
4. Review and optimize slow queries regularly

This PostgreSQL architecture provides enterprise-grade performance, security, and scalability for the Claude platform while maintaining the flexibility needed for multi-tenant SaaS applications.