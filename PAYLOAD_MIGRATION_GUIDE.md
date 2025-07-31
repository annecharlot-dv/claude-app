# Payload CMS Migration Guide

## Overview

This guide covers the migration from MongoDB to PostgreSQL with Payload CMS integration for the Claude multi-tenant space management platform.

## Architecture Changes

### Before (MongoDB + FastAPI)
- MongoDB with Motor async driver
- Custom API endpoints for all operations
- Manual tenant isolation in application code
- Basic caching with Redis

### After (PostgreSQL + Payload CMS)
- PostgreSQL with optimized connection pooling
- Payload CMS for content management with GraphQL/REST APIs
- Row-Level Security (RLS) for tenant isolation
- Multi-layer caching with intelligent invalidation
- Industry-specific customizations through hooks and fields

## Migration Steps

### 1. Database Schema Migration

The PostgreSQL schema has been designed to match your existing MongoDB structure while adding performance optimizations:

```sql
-- Key improvements:
-- 1. Proper indexing for tenant-aware queries
-- 2. Materialized views for analytics
-- 3. Partitioning for high-volume tables
-- 4. Row-Level Security for tenant isolation
```

### 2. Payload CMS Configuration

#### Core Collections

**Users Collection**
- Multi-tenant with automatic tenant_id injection
- Industry-specific role management
- Performance tracking hooks
- Cache invalidation on changes

**Pages Collection**
- Rich content management with industry templates
- Full-text search optimization
- Automatic SEO field generation
- Version control and publishing workflow

**Leads Collection**
- Industry-specific lead sources and custom fields
- Automated lead scoring and routing
- Integration with tour scheduling
- Conversion funnel analytics

**Forms Collection**
- Dynamic form builder with industry templates
- Automated lead creation from submissions
- Performance-optimized submission handling

### 3. Performance Optimizations

#### Database Level
- **Connection Pooling**: Separate pools for different workload types
- **Query Optimization**: Automatic tenant filtering and index usage
- **Materialized Views**: Pre-computed analytics for dashboards
- **Partitioning**: Time-based partitioning for high-volume tables

#### Application Level
- **Multi-layer Caching**: L1 (hot), L2 (warm), L3 (cold) with intelligent promotion
- **Request Deduplication**: Prevent duplicate API calls
- **Lazy Loading**: On-demand resource loading
- **Bundle Optimization**: Code splitting and tree shaking

#### Payload CMS Level
- **Field-level Access Control**: Reduce query complexity
- **Bulk Operations**: Optimized batch processing
- **Custom Hooks**: Performance tracking and optimization
- **GraphQL Optimization**: Efficient query resolution

## Industry Customization

### Hook System

The platform uses a comprehensive hook system for industry customization:

```typescript
// Automatic tenant context injection
export const setTenantContext: CollectionBeforeChangeHook = async ({
  data, req, operation
}) => {
  if (req.user?.tenantId && operation === 'create') {
    data.tenantId = req.user.tenantId;
  }
  return data;
};

// Industry-specific validation
export const applyIndustryValidation: CollectionBeforeChangeHook = async ({
  data, req, collection
}) => {
  const tenant = await getTenant(req);
  const industryConfig = INDUSTRY_CONFIGS[tenant.industryModule];
  
  // Apply industry-specific business rules
  return validateForIndustry(data, industryConfig, collection.slug);
};
```

### Custom Fields

Industry-specific fields adapt based on tenant configuration:

```typescript
// Dynamic role field based on industry
export const industryRoleField: Field = {
  name: 'role',
  type: 'select',
  options: async ({ req }) => {
    const tenant = await getTenant(req);
    return getIndustryRoles(tenant.industryModule);
  },
};

// Industry-specific custom fields
export const industryCustomFields: Field = {
  name: 'customFields',
  type: 'json',
  validate: async (value, { req }) => {
    const tenant = await getTenant(req);
    return validateRequiredFields(value, tenant.industryModule);
  },
};
```

## Performance Monitoring

### Payload-Specific Metrics

The system tracks Payload CMS operations for optimization:

- **Operation Performance**: Create, read, update, delete times
- **Collection Statistics**: Document counts, query performance
- **Cache Performance**: Hit rates, invalidation patterns
- **Database Integration**: Connection pool utilization, slow queries

### Real-time Dashboard

Access performance metrics at `/admin/performance`:

- Operation response times with P95 percentiles
- Collection-specific performance breakdown
- Cache hit rates and invalidation tracking
- Database connection pool monitoring
- Slow query identification and optimization suggestions

## Security Features

### Row-Level Security (RLS)

PostgreSQL RLS ensures complete tenant isolation:

```sql
-- Automatic tenant filtering
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### Access Control

Payload access control with industry-aware permissions:

```typescript
access: {
  read: ({ req: { user } }) => {
    if (user?.role === 'platform_admin') return true;
    return {
      tenantId: { equals: user?.tenantId }
    };
  },
  create: ({ req: { user } }) => {
    const allowedRoles = getIndustryRoles(user?.tenant?.industryModule);
    return allowedRoles.includes(user?.role);
  },
}
```

## API Integration

### GraphQL API

Payload automatically generates GraphQL schema with:
- Tenant-filtered queries
- Industry-specific field types
- Performance-optimized resolvers
- Real-time subscriptions

### REST API

RESTful endpoints with:
- Automatic pagination
- Field selection for reduced payloads
- ETags for client-side caching
- Compression for large responses

### Custom Endpoints

Industry-specific endpoints for:
- Analytics and reporting
- Bulk operations
- Integration webhooks
- Performance monitoring

## Migration Checklist

### Pre-Migration
- [ ] Backup existing MongoDB data
- [ ] Set up PostgreSQL database with optimizations
- [ ] Configure Payload CMS with industry modules
- [ ] Test tenant isolation and access controls
- [ ] Validate performance benchmarks

### Data Migration
- [ ] Export MongoDB collections to JSON
- [ ] Transform data to PostgreSQL format
- [ ] Import using optimized COPY commands
- [ ] Verify data integrity and relationships
- [ ] Update search indexes and materialized views

### Application Updates
- [ ] Replace MongoDB adapter with PostgreSQL adapter
- [ ] Update API endpoints to use Payload CMS
- [ ] Implement industry-specific customizations
- [ ] Add performance monitoring hooks
- [ ] Test multi-tenant functionality

### Post-Migration
- [ ] Monitor performance metrics
- [ ] Optimize slow queries
- [ ] Tune cache configurations
- [ ] Validate industry customizations
- [ ] Train users on new admin interface

## Performance Targets

### Database Performance
- Query response time: 95% under 100ms
- Connection acquisition: Under 10ms
- Cache hit ratio: >95%
- Index usage: >90% for all queries

### Payload CMS Performance
- Create operations: <500ms
- Read operations: <100ms
- Update operations: <300ms
- Admin interface load: <2s

### System Performance
- API response time: 95% under 200ms
- Memory usage: <80% of available
- CPU usage: <80% under normal load
- Cache invalidation: <50ms

## Troubleshooting

### Common Issues

1. **Slow Queries**
   - Check pg_stat_statements for optimization opportunities
   - Verify proper index usage
   - Consider query restructuring

2. **Cache Misses**
   - Review cache TTL settings
   - Check invalidation patterns
   - Monitor cache size limits

3. **Connection Pool Exhaustion**
   - Monitor pool utilization
   - Adjust pool sizes based on load
   - Implement connection retry logic

4. **Industry Customization Issues**
   - Verify tenant industry module configuration
   - Check hook execution order
   - Validate field configurations

### Performance Debugging

```typescript
// Enable detailed logging
process.env.PAYLOAD_LOG_LEVEL = 'debug';

// Monitor specific operations
const startTime = Date.now();
const result = await payload.find({ collection: 'users' });
console.log(`Query took ${Date.now() - startTime}ms`);

// Check cache statistics
const cacheStats = await payloadPgIntegration.getCacheStats();
console.log('Cache hit rate:', cacheStats.hitRate);
```

## Best Practices

### Collection Design
1. Always include tenantId field with proper indexing
2. Use industry-specific field configurations
3. Implement proper access controls
4. Add performance tracking hooks

### Query Optimization
1. Use field selection to reduce payload size
2. Implement proper pagination
3. Leverage materialized views for analytics
4. Monitor and optimize slow queries

### Caching Strategy
1. Cache frequently accessed data in L1
2. Use appropriate TTL values
3. Implement tag-based invalidation
4. Monitor cache hit rates

### Security
1. Rely on RLS for tenant isolation
2. Implement field-level access controls
3. Validate industry-specific permissions
4. Audit all data access patterns

This migration provides enterprise-grade performance, security, and customization capabilities while maintaining the flexibility needed for multi-tenant, multi-industry SaaS applications.