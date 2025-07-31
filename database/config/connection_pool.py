"""
PostgreSQL Connection Pool Configuration
Optimized for Vercel PostgreSQL with multi-tenant performance
"""
import asyncio
import logging
from typing import Optional, Dict, Any
import asyncpg
from asyncpg import Pool
import os
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)

class PostgreSQLConnectionManager:
    """Manages PostgreSQL connections with tenant-aware pooling"""
    
    def __init__(self):
        self.pools: Dict[str, Pool] = {}
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0
        }
        
    async def initialize_pools(self):
        """Initialize connection pools for different use cases"""
        
        # Main application pool
        self.pools['main'] = await self._create_pool(
            pool_name='main',
            min_size=5,
            max_size=20,
            command_timeout=30
        )
        
        # Analytics/reporting pool (longer timeouts)
        self.pools['analytics'] = await self._create_pool(
            pool_name='analytics',
            min_size=2,
            max_size=10,
            command_timeout=120
        )
        
        # Background tasks pool
        self.pools['background'] = await self._create_pool(
            pool_name='background',
            min_size=1,
            max_size=5,
            command_timeout=300
        )
        
        logger.info("✅ PostgreSQL connection pools initialized")
    
    async def _create_pool(self, pool_name: str, min_size: int, max_size: int, command_timeout: int) -> Pool:
        """Create optimized connection pool"""
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        pool = await asyncpg.create_pool(
            database_url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=command_timeout,
            server_settings={
                # Optimize for performance
                'jit': 'off',  # Disable JIT for faster startup
                'shared_preload_libraries': 'pg_stat_statements',
                'track_activity_query_size': '2048',
                'log_min_duration_statement': '1000',  # Log slow queries
                'log_checkpoints': 'on',
                'log_connections': 'on',
                'log_disconnections': 'on',
                'log_lock_waits': 'on',
                
                # Memory settings
                'shared_buffers': '256MB',
                'effective_cache_size': '1GB',
                'work_mem': '4MB',
                'maintenance_work_mem': '64MB',
                
                # Connection settings
                'max_connections': '100',
                'idle_in_transaction_session_timeout': '300000',  # 5 minutes
                'statement_timeout': '30000',  # 30 seconds default
            },
            init=self._init_connection
        )
        
        logger.info(f"Created {pool_name} pool: {min_size}-{max_size} connections")
        return pool
    
    async def _init_connection(self, connection):
        """Initialize each connection with optimizations"""
        
        # Set up connection-level optimizations
        await connection.execute("SET timezone = 'UTC'")
        await connection.execute("SET statement_timeout = '30s'")
        await connection.execute("SET lock_timeout = '10s'")
        await connection.execute("SET idle_in_transaction_session_timeout = '5min'")
        
        # Enable query plan caching
        await connection.execute("SET plan_cache_mode = 'auto'")
        
        # Set up tenant context function
        await connection.execute("""
            CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID)
            RETURNS void AS $$
            BEGIN
                PERFORM set_config('app.current_tenant_id', tenant_uuid::text, true);
            END;
            $$ LANGUAGE plpgsql;
        """)
    
    @asynccontextmanager
    async def get_connection(self, pool_name: str = 'main', tenant_id: Optional[str] = None):
        """Get connection from pool with tenant context"""
        
        pool = self.pools.get(pool_name)
        if not pool:
            raise ValueError(f"Pool '{pool_name}' not found")
        
        start_time = time.time()
        
        try:
            async with pool.acquire() as connection:
                self.connection_stats["active_connections"] += 1
                self.connection_stats["pool_hits"] += 1
                
                # Set tenant context if provided
                if tenant_id:
                    await connection.execute(
                        "SELECT set_tenant_context($1)", 
                        tenant_id
                    )
                
                yield connection
                
        except Exception as e:
            self.connection_stats["pool_misses"] += 1
            logger.error(f"Connection error in pool '{pool_name}': {e}")
            raise
        finally:
            self.connection_stats["active_connections"] -= 1
            
            # Log slow connection acquisitions
            acquisition_time = (time.time() - start_time) * 1000
            if acquisition_time > 100:  # 100ms threshold
                logger.warning(f"Slow connection acquisition: {acquisition_time:.2f}ms")
    
    async def execute_query(self, query: str, *args, pool_name: str = 'main', tenant_id: Optional[str] = None):
        """Execute query with performance monitoring"""
        
        start_time = time.time()
        
        async with self.get_connection(pool_name, tenant_id) as conn:
            try:
                result = await conn.fetch(query, *args)
                
                # Log performance metrics
                execution_time = (time.time() - start_time) * 1000
                
                if execution_time > 100:  # Log slow queries
                    logger.warning(f"Slow query: {execution_time:.2f}ms - {query[:100]}...")
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Query failed ({execution_time:.2f}ms): {e}")
                raise
    
    async def execute_transaction(self, queries: list, pool_name: str = 'main', tenant_id: Optional[str] = None):
        """Execute multiple queries in a transaction"""
        
        async with self.get_connection(pool_name, tenant_id) as conn:
            async with conn.transaction():
                results = []
                for query, args in queries:
                    result = await conn.fetch(query, *args)
                    results.append(result)
                return results
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        
        pool_stats = {}
        
        for name, pool in self.pools.items():
            pool_stats[name] = {
                "size": pool.get_size(),
                "min_size": pool.get_min_size(),
                "max_size": pool.get_max_size(),
                "idle_connections": pool.get_idle_size(),
                "active_connections": pool.get_size() - pool.get_idle_size()
            }
        
        return {
            "pools": pool_stats,
            "global_stats": self.connection_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all pools"""
        
        health_status = {}
        
        for name, pool in self.pools.items():
            try:
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                    health_status[name] = "healthy"
            except Exception as e:
                health_status[name] = f"unhealthy: {e}"
                logger.error(f"Health check failed for pool '{name}': {e}")
        
        return health_status
    
    async def close_all_pools(self):
        """Close all connection pools"""
        
        for name, pool in self.pools.items():
            await pool.close()
            logger.info(f"Closed pool: {name}")
        
        self.pools.clear()

# Tenant-aware query builder
class TenantQueryBuilder:
    """Builds tenant-aware queries with automatic filtering"""
    
    def __init__(self, connection_manager: PostgreSQLConnectionManager):
        self.conn_manager = connection_manager
    
    async def find_many(self, table: str, filters: Dict = None, tenant_id: str = None, 
                       limit: int = 100, offset: int = 0, order_by: str = None):
        """Find multiple records with tenant filtering"""
        
        where_clauses = []
        params = []
        param_count = 0
        
        # Always add tenant filter for tenant-aware tables
        tenant_tables = ['users', 'pages', 'leads', 'forms', 'tours']
        if table in tenant_tables and tenant_id:
            param_count += 1
            where_clauses.append(f"tenant_id = ${param_count}")
            params.append(tenant_id)
        
        # Add additional filters
        if filters:
            for key, value in filters.items():
                param_count += 1
                where_clauses.append(f"{key} = ${param_count}")
                params.append(value)
        
        # Build query
        query = f"SELECT * FROM {table}"
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        query += f" LIMIT {limit} OFFSET {offset}"
        
        return await self.conn_manager.execute_query(query, *params, tenant_id=tenant_id)
    
    async def find_one(self, table: str, filters: Dict, tenant_id: str = None):
        """Find single record with tenant filtering"""
        
        results = await self.find_many(table, filters, tenant_id, limit=1)
        return results[0] if results else None
    
    async def create(self, table: str, data: Dict, tenant_id: str = None):
        """Create record with automatic tenant_id injection"""
        
        # Add tenant_id if not present and table is tenant-aware
        tenant_tables = ['users', 'pages', 'leads', 'forms', 'tours']
        if table in tenant_tables and tenant_id and 'tenant_id' not in data:
            data['tenant_id'] = tenant_id
        
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(data.values())
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        result = await self.conn_manager.execute_query(query, *values, tenant_id=tenant_id)
        return result[0] if result else None
    
    async def update(self, table: str, record_id: str, data: Dict, tenant_id: str = None):
        """Update record with tenant filtering"""
        
        set_clauses = []
        params = []
        
        for i, (key, value) in enumerate(data.items(), 1):
            set_clauses.append(f"{key} = ${i}")
            params.append(value)
        
        # Add ID and tenant filters
        params.append(record_id)
        id_param = len(params)
        
        where_clause = f"id = ${id_param}"
        
        # Add tenant filter for tenant-aware tables
        tenant_tables = ['users', 'pages', 'leads', 'forms', 'tours']
        if table in tenant_tables and tenant_id:
            params.append(tenant_id)
            tenant_param = len(params)
            where_clause += f" AND tenant_id = ${tenant_param}"
        
        query = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE {where_clause}
            RETURNING *
        """
        
        result = await self.conn_manager.execute_query(query, *params, tenant_id=tenant_id)
        return result[0] if result else None

# Global connection manager instance
connection_manager = PostgreSQLConnectionManager()
query_builder = TenantQueryBuilder(connection_manager)

async def get_connection_manager() -> PostgreSQLConnectionManager:
    """Get the global connection manager"""
    return connection_manager

async def get_query_builder() -> TenantQueryBuilder:
    """Get the tenant-aware query builder"""
    return query_builder