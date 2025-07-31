-- Advanced Performance Indexes for Multi-Tenant SaaS
-- Optimized for high-concurrency workloads with tenant isolation

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tenant_role_active 
ON users(tenant_id, role, is_active) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tenant_email_active 
ON users(tenant_id, email) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tenant_login_recent 
ON users(tenant_id, last_login DESC NULLS LAST) 
WHERE last_login > NOW() - INTERVAL '90 days';

-- Pages performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_tenant_status_updated 
ON pages(tenant_id, status, updated_at DESC) 
WHERE status = 'published';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_tenant_homepage 
ON pages(tenant_id) 
WHERE is_homepage = true;

-- Full-text search index for pages
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_search_gin 
ON pages USING gin(to_tsvector('english', coalesce(search_keywords, '')));

-- Leads performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_tenant_status_created 
ON leads(tenant_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_tenant_assigned_status 
ON leads(tenant_id, assigned_to, status) 
WHERE assigned_to IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_tenant_source_created 
ON leads(tenant_id, source, created_at DESC) 
WHERE source IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_tenant_tour_scheduled 
ON leads(tenant_id, tour_scheduled_at) 
WHERE tour_scheduled_at IS NOT NULL 
AND tour_scheduled_at > NOW() - INTERVAL '30 days';

-- Email lookup optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_email_lower 
ON leads(tenant_id, lower(email));

-- Forms and submissions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forms_tenant_active_created 
ON forms(tenant_id, is_active, created_at DESC) 
WHERE is_active = true;

-- Partitioned form submissions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_form_submissions_form_created 
ON form_submissions(form_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_form_submissions_lead_created 
ON form_submissions(lead_id, created_at DESC) 
WHERE lead_id IS NOT NULL;

-- Tours performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tours_tenant_scheduled_staff 
ON tours(tenant_id, scheduled_at, staff_user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tours_tenant_status_scheduled 
ON tours(tenant_id, status, scheduled_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tours_lead_scheduled 
ON tours(lead_id, scheduled_at DESC);

-- Performance metrics indexes (partitioned)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_type_recorded 
ON performance_metrics(metric_type, recorded_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_tenant_type_recorded 
ON performance_metrics(tenant_id, metric_type, recorded_at DESC) 
WHERE tenant_id IS NOT NULL;

-- JSON field indexes for custom data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_profile_gin 
ON users USING gin(profile) 
WHERE profile IS NOT NULL AND profile != '{}';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_custom_fields_gin 
ON leads USING gin(custom_fields) 
WHERE custom_fields IS NOT NULL AND custom_fields != '{}';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_content_blocks_gin 
ON pages USING gin(content_blocks) 
WHERE content_blocks IS NOT NULL AND content_blocks != '[]';

-- Tenant-specific statistics indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenants_industry_active 
ON tenants(industry_module, is_active) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenants_plan_active 
ON tenants(plan, is_active) 
WHERE is_active = true;

-- Time-based partitioning support indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_month 
ON users(date_trunc('month', created_at), tenant_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_created_month 
ON leads(date_trunc('month', created_at), tenant_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_updated_month 
ON pages(date_trunc('month', updated_at), tenant_id);

-- Covering indexes for common queries (PostgreSQL 11+)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_tenant_email_covering 
ON users(tenant_id, email) 
INCLUDE (first_name, last_name, role, is_active, last_login);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_tenant_status_covering 
ON leads(tenant_id, status) 
INCLUDE (first_name, last_name, email, phone, company, created_at, assigned_to);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_tenant_status_covering 
ON pages(tenant_id, status) 
INCLUDE (title, slug, meta_title, meta_description, updated_at, is_homepage);

-- Partial indexes for specific use cases
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_recent_inquiries 
ON leads(tenant_id, created_at DESC) 
WHERE status = 'new_inquiry' 
AND created_at > NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tours_upcoming 
ON tours(tenant_id, scheduled_at) 
WHERE status = 'scheduled' 
AND scheduled_at > NOW() 
AND scheduled_at < NOW() + INTERVAL '30 days';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_recent_login 
ON users(tenant_id, last_login DESC) 
WHERE is_active = true 
AND last_login > NOW() - INTERVAL '30 days';

-- Functional indexes for case-insensitive searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower 
ON users(tenant_id, lower(email));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_email_lower_unique 
ON leads(tenant_id, lower(email));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pages_slug_lower 
ON pages(tenant_id, lower(slug));

-- Indexes for analytics and reporting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_conversion_funnel 
ON leads(tenant_id, status, created_at, tour_scheduled_at, tour_completed_at, converted_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_activity_analysis 
ON users(tenant_id, role, created_at, last_login) 
WHERE is_active = true;

-- Maintenance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_form_submissions_cleanup 
ON form_submissions(created_at) 
WHERE created_at < NOW() - INTERVAL '1 year';

-- Statistics collection for query planner
ANALYZE users;
ANALYZE tenants;
ANALYZE pages;
ANALYZE leads;
ANALYZE forms;
ANALYZE form_submissions;
ANALYZE tours;
ANALYZE performance_metrics;

-- Create index usage monitoring view
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MODERATE_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Create table bloat monitoring view
CREATE OR REPLACE VIEW table_bloat_stats AS
SELECT 
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND(
        n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2
    ) as dead_row_percentage,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY dead_row_percentage DESC NULLS LAST;

-- Function to get tenant-specific performance metrics
CREATE OR REPLACE FUNCTION get_tenant_performance_summary(tenant_uuid UUID)
RETURNS TABLE(
    metric_name TEXT,
    metric_value NUMERIC,
    metric_unit TEXT,
    last_updated TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'total_users'::TEXT,
        COUNT(*)::NUMERIC,
        'count'::TEXT,
        NOW()
    FROM users 
    WHERE tenant_id = tenant_uuid AND is_active = true
    
    UNION ALL
    
    SELECT 
        'total_pages'::TEXT,
        COUNT(*)::NUMERIC,
        'count'::TEXT,
        NOW()
    FROM pages 
    WHERE tenant_id = tenant_uuid AND status = 'published'
    
    UNION ALL
    
    SELECT 
        'total_leads'::TEXT,
        COUNT(*)::NUMERIC,
        'count'::TEXT,
        NOW()
    FROM leads 
    WHERE tenant_id = tenant_uuid
    
    UNION ALL
    
    SELECT 
        'conversion_rate'::TEXT,
        ROUND(
            COUNT(CASE WHEN status = 'converted' THEN 1 END)::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100, 2
        ),
        'percentage'::TEXT,
        NOW()
    FROM leads 
    WHERE tenant_id = tenant_uuid 
    AND created_at > NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to cleanup old performance metrics
CREATE OR REPLACE FUNCTION cleanup_old_performance_metrics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete metrics older than 30 days
    DELETE FROM performance_metrics 
    WHERE recorded_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup
    INSERT INTO performance_metrics (metric_type, value, metadata)
    VALUES ('cleanup_old_metrics', deleted_count, jsonb_build_object('action', 'cleanup', 'deleted_count', deleted_count));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup job (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-performance-metrics', '0 2 * * *', 'SELECT cleanup_old_performance_metrics();');

-- Create performance monitoring alerts
CREATE OR REPLACE FUNCTION check_performance_alerts()
RETURNS TABLE(
    alert_type TEXT,
    alert_message TEXT,
    severity TEXT,
    metric_value NUMERIC
) AS $$
BEGIN
    -- Check for slow queries
    RETURN QUERY
    SELECT 
        'slow_query'::TEXT,
        'Query execution time exceeds threshold: ' || query::TEXT,
        'warning'::TEXT,
        mean_exec_time
    FROM pg_stat_statements
    WHERE mean_exec_time > 1000 -- 1 second threshold
    AND calls > 10
    ORDER BY mean_exec_time DESC
    LIMIT 5;
    
    -- Check for high dead tuple ratio
    RETURN QUERY
    SELECT 
        'table_bloat'::TEXT,
        'Table has high dead tuple ratio: ' || tablename::TEXT,
        CASE 
            WHEN n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) > 0.2 THEN 'critical'
            ELSE 'warning'
        END::TEXT,
        ROUND(n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2)
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    AND n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) > 0.1
    ORDER BY n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) DESC;
END;
$$ LANGUAGE plpgsql STABLE;