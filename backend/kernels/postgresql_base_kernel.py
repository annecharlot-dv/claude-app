"""
PostgreSQL Base Kernel
Replaces MongoDB-based base kernel with SQLAlchemy operations
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.postgresql_connection import get_connection_manager
from models.postgresql_models import Base

logger = logging.getLogger(__name__)


class PostgreSQLBaseKernel(ABC):
    """Base kernel for PostgreSQL operations with tenant isolation"""

    def __init__(self, db_session: AsyncSession = None):
        self.db = db_session
        self.connection_manager = None

    async def _get_session(self) -> AsyncSession:
        """Get database session"""
        if self.db:
            return self.db

        if not self.connection_manager:
            self.connection_manager = await get_connection_manager()

        return self.connection_manager.get_session()

    async def set_tenant_context(self, tenant_id: str):
        """Set tenant context for RLS"""
        session = await self._get_session()
        await self.connection_manager.set_tenant_context(session, tenant_id)

    # Generic CRUD operations
    async def create_record(
        self,
        model_class: Type[Base],
        data: Dict[str, Any],
        tenant_id: str = None,
    ) -> Optional[Base]:
        """Generic record creation with tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Add tenant_id to data if model has it and not provided
            if (
                hasattr(model_class, "tenant_id")
                and "tenant_id" not in data
                and tenant_id
            ):
                data["tenant_id"] = tenant_id

            # Add timestamps
            if hasattr(model_class, "created_at") and "created_at" not in data:
                data["created_at"] = datetime.utcnow()
            if hasattr(model_class, "updated_at") and "updated_at" not in data:
                data["updated_at"] = datetime.utcnow()

            # Create record
            record = model_class(**data)
            session.add(record)
            await session.commit()
            await session.refresh(record)

            logger.debug(f"Created {model_class.__name__} record: {record.id}")
            return record

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create {model_class.__name__}: {e}")
            raise

    async def get_by_id(
        self,
        model_class: Type[Base],
        record_id: str,
        tenant_id: str = None,
    ) -> Optional[Base]:
        """Generic record retrieval by ID with tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Convert string ID to UUID if needed
            if isinstance(record_id, str):
                record_id = uuid.UUID(record_id)

            result = await session.execute(
                select(model_class).where(model_class.id == record_id)
            )
            record = result.scalar_one_or_none()

            logger.debug(f"Retrieved {model_class.__name__} by ID: {record_id}")
            return record

        except Exception as e:
            logger.error(f"Failed to get {model_class.__name__} by ID {record_id}: {e}")
            raise

    async def get_by_field(
        self,
        model_class: Type[Base],
        field_name: str,
        field_value: Any,
        tenant_id: str = None,
    ) -> Optional[Base]:
        """Generic record retrieval by field with tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            field = getattr(model_class, field_name)
            result = await session.execute(
                select(model_class).where(field == field_value)
            )
            record = result.scalar_one_or_none()

            logger.debug(
                f"Retrieved {model_class.__name__} by " f"{field_name}: {field_value}"
            )
            return record

        except Exception as e:
            logger.error(f"Failed to get {model_class.__name__} by {field_name}: {e}")
            raise

    async def list_records(
        self,
        model_class: Type[Base],
        filters: Dict[str, Any] = None,
        tenant_id: str = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = None,
        relationships: List[str] = None,
    ) -> List[Base]:
        """Generic record listing with filtering and tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Build query
            query = select(model_class)

            # Add relationships if specified
            if relationships:
                for rel in relationships:
                    if hasattr(model_class, rel):
                        query = query.options(selectinload(getattr(model_class, rel)))

            # Apply filters
            if filters:
                for field_name, field_value in filters.items():
                    if hasattr(model_class, field_name):
                        field = getattr(model_class, field_name)
                        if isinstance(field_value, dict):
                            # Handle complex filters like {"$gte": value}
                            for op, val in field_value.items():
                                if op == "$gte":
                                    query = query.where(field >= val)
                                elif op == "$lte":
                                    query = query.where(field <= val)
                                elif op == "$ne":
                                    query = query.where(field != val)
                                elif op == "$in":
                                    query = query.where(field.in_(val))
                        else:
                            query = query.where(field == field_value)

            # Apply ordering
            if order_by:
                if order_by.endswith(" DESC"):
                    field_name = order_by.replace(" DESC", "")
                    if hasattr(model_class, field_name):
                        query = query.order_by(getattr(model_class, field_name).desc())
                else:
                    if hasattr(model_class, order_by):
                        query = query.order_by(getattr(model_class, order_by))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            records = result.scalars().all()

            logger.debug(f"Listed {len(records)} {model_class.__name__} records")
            return list(records)

        except Exception as e:
            logger.error(f"Failed to list {model_class.__name__}: {e}")
            raise

    async def update_record(
        self,
        model_class: Type[Base],
        record_id: str,
        updates: Dict[str, Any],
        tenant_id: str = None,
    ) -> Optional[Base]:
        """Generic record update with tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Convert string ID to UUID if needed
            if isinstance(record_id, str):
                record_id = uuid.UUID(record_id)

            # Add updated timestamp
            if hasattr(model_class, "updated_at"):
                updates["updated_at"] = datetime.utcnow()

            # Update record
            await session.execute(
                update(model_class).where(model_class.id == record_id).values(**updates)
            )
            await session.commit()

            # Return updated record
            result = await session.execute(
                select(model_class).where(model_class.id == record_id)
            )
            record = result.scalar_one_or_none()

            logger.debug(f"Updated {model_class.__name__} record: {record_id}")
            return record

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update {model_class.__name__} {record_id}: {e}")
            raise

    async def delete_record(
        self,
        model_class: Type[Base],
        record_id: str,
        tenant_id: str = None,
    ) -> bool:
        """Generic record deletion with tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Convert string ID to UUID if needed
            if isinstance(record_id, str):
                record_id = uuid.UUID(record_id)

            result = await session.execute(
                delete(model_class).where(model_class.id == record_id)
            )
            await session.commit()

            deleted = result.rowcount > 0
            logger.debug(
                f"Deleted {model_class.__name__} record: {record_id} - "
                f"Success: {deleted}"
            )
            return deleted

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete {model_class.__name__} {record_id}: {e}")
            raise

    async def count_records(
        self,
        model_class: Type[Base],
        filters: Dict[str, Any] = None,
        tenant_id: str = None,
    ) -> int:
        """Count records with filtering and tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Build query
            query = select(func.count(model_class.id))

            # Apply filters
            if filters:
                for field_name, field_value in filters.items():
                    if hasattr(model_class, field_name):
                        field = getattr(model_class, field_name)
                        query = query.where(field == field_value)

            result = await session.execute(query)
            count = result.scalar()

            logger.debug(f"Counted {count} {model_class.__name__} records")
            return count

        except Exception as e:
            logger.error(f"Failed to count {model_class.__name__}: {e}")
            raise

    async def execute_raw_query(
        self, query: str, params: Dict[str, Any] = None, tenant_id: str = None
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query with tenant context"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            result = await session.execute(text(query), params or {})
            rows = result.fetchall()

            # Convert to list of dictionaries
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to execute raw query: {e}")
            raise

    # Search operations
    async def full_text_search(
        self,
        model_class: Type[Base],
        search_query: str,
        search_field: str = "search_vector",
        tenant_id: str = None,
        limit: int = 20,
    ) -> List[Base]:
        """Full-text search using PostgreSQL tsvector"""
        try:
            session = await self._get_session()

            # Set tenant context if provided
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            # Build full-text search query
            if hasattr(model_class, search_field):
                search_vector = getattr(model_class, search_field)
                query = (
                    select(model_class)
                    .where(
                        search_vector.op("@@")(
                            func.plainto_tsquery("english", search_query)
                        )
                    )
                    .order_by(
                        func.ts_rank(
                            search_vector,
                            func.plainto_tsquery("english", search_query),
                        ).desc()
                    )
                    .limit(limit)
                )

                result = await session.execute(query)
                records = result.scalars().all()

                logger.debug(
                    f"Full-text search returned {len(records)} results for: "
                    f"{search_query}"
                )
                return list(records)
            else:
                logger.warning(
                    f"{model_class.__name__} does not have " f"{search_field} field"
                )
                return []

        except Exception as e:
            logger.error(f"Failed to perform full-text search: {e}")
            raise

    # Health check
    async def get_kernel_health(self) -> Dict[str, Any]:
        """Get kernel health status"""
        try:
            session = await self._get_session()

            # Test database connectivity
            await session.execute(text("SELECT 1"))

            return {
                "status": "healthy",
                "database": "postgresql",
                "kernel": self.__class__.__name__,
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "postgresql",
                "kernel": self.__class__.__name__,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

    @abstractmethod
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user access to tenant resources"""
        pass
