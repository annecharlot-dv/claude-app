"""
PostgreSQL Performance Optimizer
Enterprise-grade optimization for multi-tenant SaaS applications
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncpg
from .connection_pool import get_connection_manager, get_query_builder

logger = logging.getLogger(__name__)

class PostgreSQLOptimizer:
    """Advanced PostgreSQL performance optimization"""
    
    def __init__(self):
        self.query_cache = {}
        self.slow_query_threshold = 100  # 100ms
        self.performance_metrics = {
            "queries_executed": 0,
            "slow_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize_optimizations(self):
        """Initialize all performance optimizations"""
        
        conn_manager = await get_connection_manager()
        
        async with conn_manager.get_connection() as conn:
            # Enable query plan caching
            await conn.execute("SET plan_cache_mode = 'auto'")
            
            # Optimize for OLTP workloads
            await conn.execute("SET random_page_cost = 1.1")
            await conn.execute("SET effective_io_concurrency = 200")
            
            # Enable parallel query execution
            await conn.execute("SET max_parallel_workers_per_gather = 2")
            await conn.execute("SET parallel_tuple_cost = 0.1")
            
            # Optimize checkpoint behavior
            await conn.execute("SET checkpoint_completion_target = 0.9")
            
            logger.info("✅ PostgreSQL optimizations initialized")
    
    async def analyze_query_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze query performance using pg_stat_statements"""
        
        conn_manager = await get_connection_manager()
        
        query = """
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                stddev_exec_time,
                min_exec_time,
                max_exec_time,
                shared_blks_hit,
                shared_blks_read,
                shared_blks_dirtied,
                shared_blks_written,
                ROUND(
                    shared_blks_hit::NUMERIC / 
                    NULLIF(shared_blks_hit + shared_blks_read, 0) * 100, 2
                ) as cache_hit_ratio
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            AND query NOT LIKE '%REFRESH MATERIALIZED VIEW%'
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """
        
        results = await conn_manager.execute_query(query, pool_name='analytics')
        
        return {
            "slow_queries": [dict(row) for row in results],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "threshold_ms": self.slow_query_threshold
        }
    
    async def get_index_usage_stats(self) -> List[Dict[str, Any]]:
        """Get index usage statistics"""
        
        conn_manager = await get_connection_manager()
        
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_tup_read,
                idx_tup_fetch,
                idx_scan,
                CASE 
                    WHEN idx_scan = 0 THEN 'UNUSED'
                    WHEN idx_scan < 100 THEN 'LOW_USAGE'
                    WHEN idx_scan < 1000 THEN 'MODERATE_USAGE'
                    ELSE 'HIGH_USAGE'
                END as usage_category,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
        """
        
        results = await conn_manager.execute_query(query, pool_name='analytics')
        return [dict(row) for row in results]
    
    async def get_table_statistics(self) -> List[Dict[str, Any]]:
        """Get comprehensive table statistics"""
        
        conn_manager = await get_connection_manager()
        
        query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                ROUND(
                    n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2
                ) as dead_row_percentage,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                ROUND(
                    idx_scan::NUMERIC / NULLIF(seq_scan + idx_scan, 0) * 100, 2
                ) as index_usage_ratio,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_total_relation_size(schemaname||'.'||tablename) as total_size_bytes,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        
        results = await conn_manager.execute_query(query, pool_name='analytics')
        return [dict(row) for row in results]
    
    async def optimize_tenant_queries(self, tenant_id: str) -> Dict[str, Any]:
        """Optimize queries for a specific tenant"""
        
        conn_manager = await get_connection_manager()
        
        # Analyze tenant-specific query patterns
        query = """
            SELECT 
                query,
                calls,
                mean_exec_time,
                total_exec_time
            FROM pg_stat_statements
            WHERE query LIKE '%tenant_id%'
            AND query LIKE $1
            ORDER BY total_exec_time DESC
            LIMIT 10
        """
        
        tenant_pattern = f"%{tenant_id}%"
        results = await conn_manager.execute_query(
            query, tenant_pattern, pool_name='analytics'
        )
        
        # Generate optimization recommendations
        recommendations = []
        
        for row in results:
            if row['mean_exec_time'] > self.slow_query_threshold:
                recommendations.append({
                    "query": row['query'][:100] + "...",
                    "issue": "Slow execution time",
                    "current_time_ms": row['mean_exec_time'],
                    "recommendation": "Consider adding indexes or optimizing WHERE clauses"
                })
        
        return {
            "tenant_id": tenant_id,
            "slow_queries": [dict(row) for row in results],
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def create_missing_indexes(self) -> List[str]:
        """Identify and suggest missing indexes"""
        
        conn_manager = await get_connection_manager()
        
        # Find tables with high sequential scan ratios
        query = """
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                ROUND(
                    seq_scan::NUMERIC / NULLIF(seq_scan + idx_scan, 0) * 100, 2
                ) as seq_scan_ratio
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND seq_scan > 1000
            AND seq_scan::NUMERIC / NULLIF(seq_scan + idx_scan, 0) > 0.5
            ORDER BY seq_scan_ratio DESC
        """
        
        results = await conn_manager.execute_query(query, pool_name='analytics')
        
        suggestions = []
        for row in results:
            table_name = row['tablename']
            
            # Suggest common index patterns for multi-tenant tables
            if table_name in ['users', 'pages', 'leads', 'forms', 'tours']:
                suggestions.append(
                    f"CREATE INDEX CONCURRENTLY idx_{table_name}_tenant_created "
                    f"ON {table_name}(tenant_id, created_at DESC);"
                )
                
                if table_name == 'users':
                    suggestions.append(
                        f"CREATE INDEX CONCURRENTLY idx_{table_name}_tenant_email "
                        f"ON {table_name}(tenant_id, email) WHERE is_active = true;"
                    )
                elif table_name == 'leads':
                    suggestions.append(
                        f"CREATE INDEX CONCURRENTLY idx_{table_name}_tenant_status "
                        f"ON {table_name}(tenant_id, status, created_at DESC);"
                    )
        
        return suggestions
    
    async def vacuum_analyze_tables(self, table_names: List[str] = None) -> Dict[str, Any]:
        """Perform VACUUM ANALYZE on specified tables"""
        
        conn_manager = await get_connection_manager()
        
        if not table_names:
            # Get all user tables
            query = """
                SELECT tablename 
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                ORDER BY n_dead_tup DESC
            """
            results = await conn_manager.execute_query(query, pool_name='background')
            table_names = [row['tablename'] for row in results]
        
        vacuum_results = {}
        
        for table_name in table_names:
            try:
                start_time = datetime.utcnow()
                
                # Use a separate connection for VACUUM (can't be in transaction)
                async with conn_manager.get_connection('background') as conn:
                    await conn.execute(f"VACUUM ANALYZE {table_name}")
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                vacuum_results[table_name] = {
                    "status": "success",
                    "duration_seconds": duration,
                    "timestamp": end_time.isoformat()
                }
                
                logger.info(f"VACUUM ANALYZE completed for {table_name} in {duration:.2f}s")
                
            except Exception as e:
                vacuum_results[table_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.error(f"VACUUM ANALYZE failed for {table_name}: {e}")
        
        return vacuum_results
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        
        conn_manager = await get_connection_manager()
        
        query = """
            SELECT 
                state,
                COUNT(*) as connection_count,
                AVG(EXTRACT(EPOCH FROM (NOW() - state_change))) as avg_duration_seconds
            FROM pg_stat_activity
            WHERE datname = current_database()
            GROUP BY state
            ORDER BY connection_count DESC
        """
        
        results = await conn_manager.execute_query(query, pool_name='analytics')
        
        # Get pool statistics
        pool_stats = await conn_manager.get_pool_stats()
        
        return {
            "database_connections": [dict(row) for row in results],
            "connection_pools": pool_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def monitor_locks(self) -> List[Dict[str, Any]]:
        """Monitor database locks and blocking queries"""
        
        conn_manager = await get_connection_manager()
        
        query = """
            SELECT 
                blocked_locks.pid AS blocked_pid,
                blocked_activity.usename AS blocked_user,
                blocking_locks.pid AS blocking_pid,
                blocking_activity.usename AS blocking_user,
                blocked_activity.query AS blocked_statement,
                blocking_activity.query AS blocking_statement,
                blocked_activity.application_name AS blocked_application,
                blocking_activity.application_name AS blocking_application,
                blocked_locks.mode AS blocked_mode,
                blocking_locks.mode AS blocking_mode,
                blocked_locks.locktype AS blocked_locktype,
                blocking_locks.locktype AS blocking_locktype
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity 
                ON blocked_activity.pid = blocked_locks.pid
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
                AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                AND blocking_locks.pid != blocked_locks.pid
            JOIN pg_catalog.pg_stat_activity blocking_activity 
                ON blocking_activity.pid = blocking_locks.pid
            WHERE NOT blocked_locks.granted
        """
        
        results = await conn_manager.execute_query(query, pool_name='analytics')
        
        locks = [dict(row) for row in results]
        
        if locks:
            logger.warning(f"Found {len(locks)} blocking locks")
        
        return locks
    
    async def get_cache_hit_ratio(self) -> Dict[str, float]:
        """Get database cache hit ratios"""
        
        conn_manager = await get_connection_manager()
        
        # Buffer cache hit ratio
        buffer_query = """
            SELECT 
                ROUND(
                    sum(blks_hit)::NUMERIC / 
                    NULLIF(sum(blks_hit) + sum(blks_read), 0) * 100, 2
                ) as buffer_cache_hit_ratio
            FROM pg_stat_database
            WHERE datname = current_database()
        """
        
        # Index cache hit ratio
        index_query = """
            SELECT 
                ROUND(
                    sum(idx_blks_hit)::NUMERIC / 
                    NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0) * 100, 2
                ) as index_cache_hit_ratio
            FROM pg_statio_user_indexes
        """
        
        buffer_result = await conn_manager.execute_query(buffer_query, pool_name='analytics')
        index_result = await conn_manager.execute_query(index_query, pool_name='analytics')
        
        return {
            "buffer_cache_hit_ratio": float(buffer_result[0]['buffer_cache_hit_ratio'] or 0),
            "index_cache_hit_ratio": float(index_result[0]['index_cache_hit_ratio'] or 0),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global optimizer instance
postgresql_optimizer = PostgreSQLOptimizer()

async def get_postgresql_optimizer() -> PostgreSQLOptimizer:
    """Get the global PostgreSQL optimizer"""
    return postgresql_optimizer