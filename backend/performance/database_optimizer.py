"""
Database Performance Optimizer
Implements enterprise-grade database optimizations for PostgreSQL
"""
import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from database.postgresql_connection import PostgreSQLConnectionManager
from sqlalchemy import text, select, func
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimizes database performance with indexes, query optimization, and monitoring"""
    
    def __init__(self, connection_manager: PostgreSQLConnectionManager):
        self.connection_manager = connection_manager
        self.query_metrics = {}
        self.slow_query_threshold = 100  # 100ms threshold
        self.optimization_cache = {}
        self.index_recommendations = []
        
    async def initialize(self):
        """Initialize the optimizer with database analysis"""
        logger.info("Initializing database optimizer...")
        
        await self._analyze_existing_indexes()
        
        await self._setup_query_monitoring()
        
        await self._generate_optimization_recommendations()
        
        logger.info("Database optimizer initialized successfully")
    
    async def _analyze_existing_indexes(self):
        """Analyze existing database indexes"""
        try:
            async with self.connection_manager.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """))
                
                indexes = result.fetchall()
                self.existing_indexes = {
                    f"{idx.tablename}": idx.indexdef 
                    for idx in indexes
                }
                
                logger.info(f"Analyzed {len(indexes)} existing indexes")
            
        except Exception as e:
            logger.error(f"Failed to analyze indexes: {e}")
    
    async def _setup_query_monitoring(self):
        """Set up query performance monitoring"""
        try:
            async with self.connection_manager.get_session() as session:
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
                logger.info("Query monitoring enabled")
        except Exception as e:
            logger.warning(f"Could not enable pg_stat_statements: {e}")
    
    async def _generate_optimization_recommendations(self):
        """Generate database optimization recommendations"""
        recommendations = []
        
        try:
            async with self.connection_manager.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        t.table_name,
                        c.column_name
                    FROM information_schema.table_constraints t
                    JOIN information_schema.constraint_column_usage c 
                        ON t.constraint_name = c.constraint_name
                    WHERE t.constraint_type = 'FOREIGN KEY'
                        AND t.table_schema = 'public'
                """))
                
                foreign_keys = result.fetchall()
                for fk in foreign_keys:
                    table_name = fk.table_name
                    column_name = fk.column_name
                    
                    index_check = await session.execute(text(f"""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE tablename = '{table_name}' 
                            AND indexdef LIKE '%{column_name}%'
                    """))
                    
                    if not index_check.fetchone():
                        recommendations.append({
                            "type": "missing_index",
                            "table": table_name,
                            "column": column_name,
                            "reason": "Foreign key without index",
                            "impact": "high",
                            "sql": f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name})"
                        })
                
                self.index_recommendations = recommendations
                logger.info(f"Generated {len(recommendations)} optimization recommendations")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
    
    async def optimize_query(self, table_name: str, query_filter: Dict[str, Any], options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Optimize and execute a query with performance monitoring"""
        start_time = time.time()
        
        try:
            async with self.connection_manager.get_session() as session:
                if table_name == "pages":
                    from models.postgresql_models import Page
                    from sqlalchemy import select
                    
                    query = select(Page)
                    if query_filter.get("tenant_id"):
                        query = query.where(Page.tenant_id == query_filter["tenant_id"])
                    if query_filter.get("status"):
                        query = query.where(Page.status == query_filter["status"])
                    
                    if options:
                        if options.get("limit"):
                            query = query.limit(options["limit"])
                        if options.get("skip"):
                            query = query.offset(options["skip"])
                    
                    result = await session.execute(query)
                    data = result.scalars().all()
                    
                elif table_name == "leads":
                    from models.postgresql_models import Lead
                    from sqlalchemy import select
                    
                    query = select(Lead)
                    if query_filter.get("tenant_id"):
                        query = query.where(Lead.tenant_id == query_filter["tenant_id"])
                    if query_filter.get("status"):
                        query = query.where(Lead.status == query_filter["status"])
                    
                    if options:
                        if options.get("limit"):
                            query = query.limit(options["limit"])
                        if options.get("skip"):
                            query = query.offset(options["skip"])
                    
                    result = await session.execute(query)
                    data = result.scalars().all()
                
                else:
                    result = await session.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
                    data = result.fetchall()
                
                if hasattr(data[0], '__dict__') if data else False:
                    data = [item.__dict__ for item in data]
                
                execution_time = (time.time() - start_time) * 1000
                await self.log_query_performance(table_name, "select", len(data), execution_time)
                
                return data
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            await self.log_query_performance(table_name, "select", 0, execution_time, str(e))
            logger.error(f"Query optimization failed for {table_name}: {e}")
            return []
    
    async def log_query_performance(self, table_name: str, operation: str, result_count: int, execution_time: float = None, error: str = None):
        """Log query performance metrics"""
        if execution_time is None:
            execution_time = 0
            
        metric_key = f"{table_name}_{operation}"
        
        if metric_key not in self.query_metrics:
            self.query_metrics[metric_key] = {
                "total_queries": 0,
                "total_time": 0,
                "avg_time": 0,
                "slow_queries": 0,
                "errors": 0,
                "last_execution": None
            }
        
        metrics = self.query_metrics[metric_key]
        metrics["total_queries"] += 1
        metrics["total_time"] += execution_time
        metrics["avg_time"] = metrics["total_time"] / metrics["total_queries"]
        metrics["last_execution"] = datetime.utcnow().isoformat()
        
        if error:
            metrics["errors"] += 1
        
        if execution_time > self.slow_query_threshold:
            metrics["slow_queries"] += 1
            logger.warning(f"Slow query detected: {table_name}.{operation} took {execution_time:.2f}ms")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "query_metrics": self.query_metrics,
            "slow_query_threshold": self.slow_query_threshold,
            "total_queries": sum(m["total_queries"] for m in self.query_metrics.values()),
            "total_slow_queries": sum(m["slow_queries"] for m in self.query_metrics.values()),
            "recommendations": self.index_recommendations
        }
    
    async def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get list of slow queries"""
        slow_queries = []
        
        for key, metrics in self.query_metrics.items():
            if metrics["slow_queries"] > 0:
                table_name, operation = key.split("_", 1)
                slow_queries.append({
                    "table": table_name,
                    "operation": operation,
                    "avg_time": metrics["avg_time"],
                    "slow_count": metrics["slow_queries"],
                    "total_queries": metrics["total_queries"]
                })
        
        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with self.connection_manager.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """))
                
                tables = result.fetchall()
                
                # Get connection stats
                conn_result = await session.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                """))
                
                conn_stats = conn_result.fetchone()
                
                return {
                    "tables": [
                        {
                            "name": table.tablename,
                            "size": table.size,
                            "size_bytes": table.size_bytes
                        }
                        for table in tables
                    ],
                    "connections": {
                        "total": conn_stats.total_connections,
                        "active": conn_stats.active_connections,
                        "idle": conn_stats.idle_connections
                    },
                    "recommendations": self.index_recommendations
                }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    async def analyze_collection_performance(self, table_name: str) -> Dict[str, Any]:
        """Analyze performance of a specific table"""
        try:
            async with self.connection_manager.get_session() as session:
                result = await session.execute(text(f"""
                    SELECT 
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables 
                    WHERE relname = '{table_name}'
                """))
                
                stats = result.fetchone()
                
                if not stats:
                    return {"error": f"Table {table_name} not found"}
                
                # Get index usage
                index_result = await session.execute(text(f"""
                    SELECT 
                        indexrelname as index_name,
                        idx_scan as scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes 
                    WHERE relname = '{table_name}'
                """))
                
                indexes = index_result.fetchall()
                
                return {
                    "table_name": table_name,
                    "statistics": {
                        "inserts": stats.inserts,
                        "updates": stats.updates,
                        "deletes": stats.deletes,
                        "live_tuples": stats.live_tuples,
                        "dead_tuples": stats.dead_tuples,
                        "last_vacuum": stats.last_vacuum.isoformat() if stats.last_vacuum else None,
                        "last_analyze": stats.last_analyze.isoformat() if stats.last_analyze else None
                    },
                    "indexes": [
                        {
                            "name": idx.index_name,
                            "scans": idx.scans,
                            "tuples_read": idx.tuples_read,
                            "tuples_fetched": idx.tuples_fetched
                        }
                        for idx in indexes
                    ]
                }
            
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self) -> Dict[str, Any]:
        """Clean up old data and optimize database"""
        try:
            async with self.connection_manager.get_session() as session:
                result = await session.execute(text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """))
                
                tables = result.fetchall()
                cleaned_tables = []
                
                for table in tables:
                    table_name = table.tablename
                    try:
                        await session.execute(text(f"VACUUM ANALYZE {table_name}"))
                        cleaned_tables.append(table_name)
                    except Exception as e:
                        logger.warning(f"Failed to vacuum table {table_name}: {e}")
                
                return {
                    "message": "Database cleanup completed",
                    "cleaned_tables": cleaned_tables,
                    "total_tables": len(tables)
                }
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return {"error": str(e)}
    
    async def get_tenant_queries(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get query performance metrics for a specific tenant"""
        tenant_metrics = []
        
        for key, metrics in self.query_metrics.items():
            if "tenant" in key.lower():
                table_name, operation = key.split("_", 1)
                tenant_metrics.append({
                    "table": table_name,
                    "operation": operation,
                    "metrics": metrics
                })
        
        return tenant_metrics

# Global optimizer instance
db_optimizer = None

async def get_db_optimizer(connection_manager: PostgreSQLConnectionManager) -> DatabaseOptimizer:
    """Get or create database optimizer instance"""
    global db_optimizer
    if db_optimizer is None:
        db_optimizer = DatabaseOptimizer(connection_manager)
        await db_optimizer.initialize()
    return db_optimizer
