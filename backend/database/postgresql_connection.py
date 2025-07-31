"""
PostgreSQL Connection Management with Async Support
Handles connection pooling, tenant context, and RLS
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text, event
from contextlib import asynccontextmanager
import os
import logging
from typing import Optional, AsyncGenerator

logger = logging.getLogger(__name__)

class PostgreSQLConnectionManager:
    """Manages PostgreSQL connections with tenant context and RLS"""
    
    def __init__(self):
        self.engine = None
        self.async_session_factory = None
        self.database_url = None
    
    async def initialize(self):
        """Initialize the PostgreSQL connection"""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            self.database_url,
            poolclass=NullPool,  # Use external connection pooling
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
            future=True
        )
        
        # Create session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ PostgreSQL connection manager initialized")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        if not self.async_session_factory:
            await self.initialize()
        
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def set_tenant_context(self, session: AsyncSession, tenant_id: str):
        """Set tenant context for Row-Level Security"""
        try:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id}
            )
            logger.debug(f"Set tenant context: {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to set tenant context: {e}")
            raise
    
    async def health_check(self) -> dict:
        """Perform database health check"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1 as health"))
                row = result.fetchone()
                
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "connection": "active",
                    "result": row[0] if row else None
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "postgresql",
                "error": str(e)
            }
    
    async def close(self):
        """Close the database engine"""
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL connection manager closed")

# Global connection manager instance
connection_manager = PostgreSQLConnectionManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with connection_manager.get_session() as session:
        yield session

async def get_connection_manager() -> PostgreSQLConnectionManager:
    """Get the global connection manager"""
    return connection_manager