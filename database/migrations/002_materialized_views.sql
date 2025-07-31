-- Materialized Views for Performance Optimization
-- These views pre-compute expensive queries for the performance dashboard

-- Tenant performance summary view
CREATE MATERIALIZED VIEW tenant_performance_summary AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    t.subdomain,
    t.industry_module,
    
    -- User metrics
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT CASE WHEN u.is_active THEN u.id END) as active_users,
    COUNT(DISTINCT CASE WHEN u.last_login > NOW() - INTERVAL '30 days' THEN u.id END) as monthly_active_users,
    
    -- Page metrics
    COUNT(DISTINCT p.id) as total_pages,
    COUNT(DISTINCT CASE WHEN p.status = 'published' THEN p.id END) as published_pages,
    
    -- Lead metrics
    COUNT(DISTINCT l.id) as total_leads,
    COUNT(DISTINCT CASE WHEN l.created_at > NOW() - INTERVAL '30 days' THEN l.id END) as monthly_leads,
    COUNT(DISTINCT CASE WHEN l.status = 'converted' THEN l.id END) as converted_leads,
    
    -- Form metrics
    COUNT(DISTINCT f.id) as total_forms,
    COUNT(DISTINCT CASE WHEN f.is_active THEN f.id END) as active_forms,
    
    -- Tour metrics
    COUNT(DISTINCT tour.id) as total_tours,
    COUNT(DISTINCT CASE WHEN tour.scheduled_at > NOW() - INTERVAL '30 days' THEN tour.id END) as monthly_tours,
    
    -- Performance metrics
    COALESCE(perf.avg_response_time, 0) as avg_response_time_ms,
    COALESCE(perf.p95_response_time, 0) as p95_response_time_ms,
    
    -- Last updated
    NOW() as last_updated
    
FROM tenants t
LEFT JOIN users u ON t.id = u.tenant_id
LEFT JOIN pages p ON t.id = p.tenant_id
LEFT JOIN leads l ON t.id = l.tenant_id
LEFT JOIN forms f ON t.id = f.tenant_id
LEFT JOIN tours tour ON t.id = tour.tenant_id
LEFT JOIN (
    SELECT 
        tenant_id,
        AVG(value) as avg_response_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_response_time
    FROM performance_metrics 
    WHERE metric_type = 'response_time' 
    AND recorded_at > NOW() - INTERVAL '24 hours'
    GROUP BY tenant_id
) perf ON t.id = perf.tenant_id
WHERE t.is_active = true
GROUP BY t.id, t.name, t.subdomain, t.industry_module, perf.avg_response_time, perf.p95_response_time;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX idx_tenant_performance_summary_tenant_id 
ON tenant_performance_summary(tenant_id);

-- Lead conversion funnel view
CREATE MATERIALIZED VIEW lead_conversion_funnel AS
SELECT 
    tenant_id,
    DATE_TRUNC('day', created_at) as date,
    
    -- Funnel metrics
    COUNT(*) as total_leads,
    COUNT(CASE WHEN status != 'new_inquiry' THEN 1 END) as engaged_leads,
    COUNT(CASE WHEN tour_scheduled_at IS NOT NULL THEN 1 END) as tours_scheduled,
    COUNT(CASE WHEN tour_completed_at IS NOT NULL THEN 1 END) as tours_completed,
    COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads,
    
    -- Conversion rates
    ROUND(
        COUNT(CASE WHEN status != 'new_inquiry' THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as engagement_rate,
    
    ROUND(
        COUNT(CASE WHEN tour_scheduled_at IS NOT NULL THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as tour_scheduling_rate,
    
    ROUND(
        COUNT(CASE WHEN status = 'converted' THEN 1 END)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) as conversion_rate,
    
    -- Source breakdown
    jsonb_object_agg(
        COALESCE(source, 'unknown'), 
        COUNT(*)
    ) as source_breakdown,
    
    NOW() as last_updated
    
FROM leads
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY tenant_id, DATE_TRUNC('day', created_at);

-- Create indexes for lead conversion funnel
CREATE INDEX idx_lead_conversion_funnel_tenant_date 
ON lead_conversion_funnel(tenant_id, date DESC);

-- Database performance metrics view
CREATE MATERIALIZED VIEW database_performance_metrics AS
SELECT 
    schemaname,
    tablename,
    
    -- Table size metrics
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_total_relation_size(schemaname||'.'||tablename) as total_size_bytes,
    
    -- Row count estimates
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    
    -- Index usage
    COALESCE(idx_usage.index_usage_ratio, 0) as index_usage_ratio,
    
    -- Last vacuum and analyze
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze,
    
    NOW() as last_updated
    
FROM pg_stat_user_tables pst
LEFT JOIN (
    SELECT 
        schemaname,
        tablename,
        ROUND(
            CASE 
                WHEN seq_scan + idx_scan = 0 THEN 0
                ELSE idx_scan::NUMERIC / (seq_scan + idx_scan) * 100
            END, 2
        ) as index_usage_ratio
    FROM pg_stat_user_tables
) idx_usage ON pst.schemaname = idx_usage.schemaname 
    AND pst.tablename = idx_usage.tablename
WHERE pst.schemaname = 'public';

-- Query performance view (requires pg_stat_statements extension)
CREATE MATERIALIZED VIEW query_performance_metrics AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    min_exec_time,
    max_exec_time,
    
    -- Performance indicators
    CASE 
        WHEN mean_exec_time > 1000 THEN 'slow'
        WHEN mean_exec_time > 100 THEN 'moderate'
        ELSE 'fast'
    END as performance_category,
    
    -- Resource usage
    shared_blks_hit,
    shared_blks_read,
    shared_blks_dirtied,
    shared_blks_written,
    
    -- Cache hit ratio
    ROUND(
        shared_blks_hit::NUMERIC / 
        NULLIF(shared_blks_hit + shared_blks_read, 0) * 100, 2
    ) as cache_hit_ratio,
    
    NOW() as last_updated
    
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
AND query NOT LIKE '%REFRESH MATERIALIZED VIEW%'
ORDER BY mean_exec_time DESC
LIMIT 100;

-- Cache performance view
CREATE MATERIALIZED VIEW cache_performance_metrics AS
SELECT 
    tenant_id,
    DATE_TRUNC('hour', recorded_at) as hour,
    
    -- Cache metrics
    COUNT(CASE WHEN metric_type = 'cache_hit' THEN 1 END) as cache_hits,
    COUNT(CASE WHEN metric_type = 'cache_miss' THEN 1 END) as cache_misses,
    COUNT(CASE WHEN metric_type = 'cache_invalidation' THEN 1 END) as cache_invalidations,
    
    -- Hit rate calculation
    ROUND(
        COUNT(CASE WHEN metric_type = 'cache_hit' THEN 1 END)::NUMERIC /
        NULLIF(
            COUNT(CASE WHEN metric_type = 'cache_hit' THEN 1 END) +
            COUNT(CASE WHEN metric_type = 'cache_miss' THEN 1 END), 0
        ) * 100, 2
    ) as hit_rate_percentage,
    
    -- Response time metrics for cached vs non-cached requests
    AVG(CASE WHEN metric_type = 'api_cache_hit' THEN value END) as avg_cached_response_time,
    AVG(CASE WHEN metric_type = 'response_time' THEN value END) as avg_response_time,
    
    NOW() as last_updated
    
FROM performance_metrics
WHERE metric_type IN ('cache_hit', 'cache_miss', 'cache_invalidation', 'api_cache_hit', 'response_time')
AND recorded_at > NOW() - INTERVAL '7 days'
GROUP BY tenant_id, DATE_TRUNC('hour', recorded_at);

-- Create indexes for cache performance
CREATE INDEX idx_cache_performance_tenant_hour 
ON cache_performance_metrics(tenant_id, hour DESC);

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS void AS $$
BEGIN
    -- Refresh views concurrently for better performance
    REFRESH MATERIALIZED VIEW CONCURRENTLY tenant_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY lead_conversion_funnel;
    REFRESH MATERIALIZED VIEW database_performance_metrics;
    REFRESH MATERIALIZED VIEW query_performance_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY cache_performance_metrics;
    
    -- Log the refresh
    INSERT INTO performance_metrics (metric_type, value, metadata)
    VALUES ('materialized_view_refresh', EXTRACT(EPOCH FROM NOW()), '{"action": "refresh_all_views"}');
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to refresh views (requires pg_cron extension)
-- SELECT cron.schedule('refresh-performance-views', '*/15 * * * *', 'SELECT refresh_performance_views();');

-- Indexes for better materialized view performance
CREATE INDEX idx_users_tenant_active_login ON users(tenant_id, is_active, last_login DESC) 
WHERE is_active = true;

CREATE INDEX idx_leads_tenant_status_created ON leads(tenant_id, status, created_at DESC);

CREATE INDEX idx_performance_metrics_type_tenant_time ON performance_metrics(metric_type, tenant_id, recorded_at DESC)
WHERE tenant_id IS NOT NULL;