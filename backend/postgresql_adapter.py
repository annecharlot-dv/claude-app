"""
PostgreSQL Adapter for Claude Platform
Replaces MongoDB with optimized PostgreSQL operations
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import asyncpg
from fastapi import HTTPException

# Import our connection management
sys.path.append(str(Path(__file__).parent / "database" / "config"))

from connection_pool import get_connection_manager, get_query_builder
from postgresql_optimizer import get_postgresql_optimizer

logger = logging.getLogger(__name__)


class PostgreSQLAdapter:
    """High-performance PostgreSQL adapter with multi-tenant support"""

    def __init__(self):
        self.conn_manager = None
        self.query_builder = None
        self.optimizer = None

    async def initialize(self):
        """Initialize the PostgreSQL adapter"""
        self.conn_manager = await get_connection_manager()
        self.query_builder = await get_query_builder()
        self.optimizer = await get_postgresql_optimizer()

        # Initialize connection pools
        await self.conn_manager.initialize_pools()

        # Initialize optimizations
        await self.optimizer.initialize_optimizations()

        logger.info("✅ PostgreSQL adapter initialized")

    async def set_tenant_context(self, tenant_id: str):
        """Set tenant context for RLS"""
        # This will be handled by the connection manager
        pass

    # User operations
    async def create_user(
        self, user_data: Dict[str, Any], tenant_id: str
    ) -> Dict[str, Any]:
        """Create a new user with tenant isolation"""

        # Hash password if provided
        if "password" in user_data:
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user_data["password_hash"] = pwd_context.hash(user_data.pop("password"))

        # Add tenant_id and timestamps
        user_data.update(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        result = await self.query_builder.create("users", user_data, tenant_id)
        return dict(result) if result else None

    async def get_user_by_email(
        self, email: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by email with tenant filtering"""

        from models.postgresql_models import User
        from sqlalchemy import select

        async with self.conn_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.email == email, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
        return user

    async def get_user_by_id(
        self, user_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by ID with tenant filtering"""

        from models.postgresql_models import User
        from sqlalchemy import select

        async with self.conn_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
            return user

    async def update_user(
        self, user_id: str, update_data: Dict[str, Any], tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Update user with tenant filtering"""

        update_data["updated_at"] = datetime.utcnow()

        result = await self.query_builder.update(
            "users", user_id, update_data, tenant_id
        )
        return dict(result) if result else None

    async def get_users(
        self, tenant_id: str, filters: Dict = None, limit: int = 100, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get users with tenant filtering and pagination"""

        results = await self.query_builder.find_many(
            "users",
            filters or {},
            tenant_id,
            limit=limit,
            offset=skip,
            order_by="created_at DESC",
        )
        return [dict(row) for row in results]

    # Page operations
    async def create_page(
        self, page_data: Dict[str, Any], tenant_id: str
    ) -> Dict[str, Any]:
        """Create a new page with tenant isolation"""

        # Generate search keywords from content
        if "content_blocks" in page_data:
            content_text = self._extract_text_from_content(page_data["content_blocks"])
            page_data["search_keywords"] = content_text.lower()

        page_data.update(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        result = await self.query_builder.create("pages", page_data, tenant_id)
        return dict(result) if result else None

    async def get_page_by_slug(
        self, slug: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get page by slug with tenant filtering"""

        from models.postgresql_models import Page
        from sqlalchemy import select

        async with self.conn_manager.get_session() as session:
            result = await session.execute(
                select(Page).where(Page.slug == slug, Page.tenant_id == tenant_id)
            )
            page = result.scalar_one_or_none()
            return page

    async def get_pages(
        self, tenant_id: str, filters: Dict = None, limit: int = 100, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get pages with tenant filtering and pagination"""

        results = await self.query_builder.find_many(
            "pages",
            filters or {},
            tenant_id,
            limit=limit,
            offset=skip,
            order_by="updated_at DESC",
        )
        return [dict(row) for row in results]

    async def update_page(
        self, page_id: str, update_data: Dict[str, Any], tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Update page with tenant filtering"""

        # Update search keywords if content changed
        if "content_blocks" in update_data:
            content_text = self._extract_text_from_content(
                update_data["content_blocks"]
            )
            update_data["search_keywords"] = content_text.lower()

        update_data["updated_at"] = datetime.utcnow()

        result = await self.query_builder.update(
            "pages", page_id, update_data, tenant_id
        )
        return dict(result) if result else None

    async def search_pages(
        self, query: str, tenant_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search pages"""

        sql = """
            SELECT *, ts_rank(to_tsvector('english', search_keywords), plainto_tsquery('english', $1)) as rank
            FROM pages 
            WHERE tenant_id = $2 
            AND to_tsvector('english', search_keywords) @@ plainto_tsquery('english', $1)
            AND status = 'published'
            ORDER BY rank DESC, updated_at DESC
            LIMIT $3
        """

        results = await self.conn_manager.execute_query(
            sql, query, tenant_id, limit, tenant_id=tenant_id
        )
        return [dict(row) for row in results]

    # Lead operations
    async def create_lead(
        self, lead_data: Dict[str, Any], tenant_id: str
    ) -> Dict[str, Any]:
        """Create a new lead with tenant isolation"""

        lead_data.update(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        result = await self.query_builder.create("leads", lead_data, tenant_id)
        return dict(result) if result else None

    async def get_lead_by_email(
        self, email: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get lead by email with tenant filtering"""

        from models.postgresql_models import Lead
        from sqlalchemy import select

        async with self.conn_manager.get_session() as session:
            result = await session.execute(
                select(Lead).where(Lead.email == email, Lead.tenant_id == tenant_id)
            )
            lead = result.scalar_one_or_none()
            return lead

    async def get_leads(
        self, tenant_id: str, filters: Dict = None, limit: int = 100, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get leads with tenant filtering and pagination"""

        results = await self.query_builder.find_many(
            "leads",
            filters or {},
            tenant_id,
            limit=limit,
            offset=skip,
            order_by="created_at DESC",
        )
        return [dict(row) for row in results]

    async def update_lead(
        self, lead_id: str, update_data: Dict[str, Any], tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Update lead with tenant filtering"""

        update_data["updated_at"] = datetime.utcnow()

        result = await self.query_builder.update(
            "leads", lead_id, update_data, tenant_id
        )
        return dict(result) if result else None

    # Form operations
    async def create_form(
        self, form_data: Dict[str, Any], tenant_id: str
    ) -> Dict[str, Any]:
        """Create a new form with tenant isolation"""

        form_data.update(
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        result = await self.query_builder.create("forms", form_data, tenant_id)
        return dict(result) if result else None

    async def get_forms(
        self, tenant_id: str, filters: Dict = None
    ) -> List[Dict[str, Any]]:
        """Get forms with tenant filtering"""

        results = await self.query_builder.find_many(
            "forms", filters or {}, tenant_id, order_by="created_at DESC"
        )
        return [dict(row) for row in results]

    async def create_form_submission(
        self, submission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create form submission"""

        submission_data.update(
            {"id": str(uuid.uuid4()), "created_at": datetime.utcnow()}
        )

        # Form submissions don't need tenant_id directly as they're linked through forms
        sql = """
            INSERT INTO form_submissions (id, form_id, lead_id, data, source_url, ip_address, user_agent, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """

        result = await self.conn_manager.execute_query(
            sql,
            submission_data["id"],
            submission_data["form_id"],
            submission_data.get("lead_id"),
            json.dumps(submission_data["data"]),
            submission_data.get("source_url"),
            submission_data.get("ip_address"),
            submission_data.get("user_agent"),
            submission_data["created_at"],
        )

        return dict(result[0]) if result else None

    # Tenant operations
    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """Get tenant by subdomain"""

        sql = "SELECT * FROM tenants WHERE subdomain = $1 AND is_active = true"
        results = await self.conn_manager.execute_query(sql, subdomain)
        return dict(results[0]) if results else None

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""

        sql = "SELECT * FROM tenants WHERE id = $1"
        results = await self.conn_manager.execute_query(sql, tenant_id)
        return dict(results[0]) if results else None

    # Performance monitoring
    async def record_performance_metric(
        self,
        metric_type: str,
        value: float,
        metadata: Dict = None,
        tenant_id: str = None,
    ):
        """Record performance metric"""

        sql = """
            INSERT INTO performance_metrics (id, tenant_id, metric_type, value, metadata, recorded_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """

        await self.conn_manager.execute_query(
            sql,
            str(uuid.uuid4()),
            tenant_id,
            metric_type,
            value,
            json.dumps(metadata or {}),
            datetime.utcnow(),
            pool_name="background",
        )

    async def get_performance_metrics(
        self, tenant_id: str = None, hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics summary"""

        # Use materialized view for better performance
        sql = (
            """
            SELECT 
                metric_type,
                COUNT(*) as count,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value
            FROM performance_metrics
            WHERE recorded_at > NOW() - INTERVAL '%s hours'
        """
            % hours
        )

        if tenant_id:
            sql += " AND tenant_id = $1 GROUP BY metric_type"
            results = await self.conn_manager.execute_query(
                sql, tenant_id, pool_name="analytics"
            )
        else:
            sql += " GROUP BY metric_type"
            results = await self.conn_manager.execute_query(sql, pool_name="analytics")

        metrics = {}
        for row in results:
            metrics[row["metric_type"]] = {
                "count": row["count"],
                "avg": float(row["avg_value"]),
                "min": float(row["min_value"]),
                "max": float(row["max_value"]),
                "p95": float(row["p95_value"]),
            }

        return {
            "metrics": metrics,
            "time_period_hours": hours,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics from materialized view"""

        sql = """
            SELECT 
                hit_rate_percentage,
                cache_hits,
                cache_misses,
                cache_invalidations
            FROM cache_performance_metrics
            WHERE hour > NOW() - INTERVAL '1 hour'
            ORDER BY hour DESC
            LIMIT 1
        """

        results = await self.conn_manager.execute_query(sql, pool_name="analytics")

        if results:
            row = results[0]
            return {
                "hit_rate": float(row["hit_rate_percentage"] or 0),
                "hits": int(row["cache_hits"] or 0),
                "misses": int(row["cache_misses"] or 0),
                "invalidations": int(row["cache_invalidations"] or 0),
                "total_entries": int(row["cache_hits"] or 0)
                + int(row["cache_misses"] or 0),
            }

        return {
            "hit_rate": 0,
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "total_entries": 0,
        }

    # Utility methods
    def _extract_text_from_content(self, content_blocks: List[Dict]) -> str:
        """Extract searchable text from content blocks"""

        text_parts = []

        for block in content_blocks:
            if block.get("type") == "text" and block.get("content"):
                text_parts.append(block["content"])
            elif block.get("config", {}).get("title"):
                text_parts.append(block["config"]["title"])
            elif block.get("config", {}).get("subtitle"):
                text_parts.append(block["config"]["subtitle"])

        return " ".join(text_parts)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""

        try:
            # Check connection pools
            pool_health = await self.conn_manager.health_check()

            # Check database connectivity
            sql = "SELECT 1 as health_check"
            await self.conn_manager.execute_query(sql)

            # Get basic stats
            stats = await self.conn_manager.get_pool_stats()

            return {
                "status": "healthy",
                "pools": pool_health,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def close(self):
        """Close all connections"""
        if self.conn_manager:
            await self.conn_manager.close_all_pools()


# Global adapter instance
postgresql_adapter = PostgreSQLAdapter()


async def get_postgresql_adapter() -> PostgreSQLAdapter:
    """Get the global PostgreSQL adapter"""
    return postgresql_adapter
