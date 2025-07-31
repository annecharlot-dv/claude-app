"""
Multi-Tenant Middleware
Handles subdomain-based tenant resolution and context injection
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
import re
from urllib.parse import urlparse
import logging

from models.tenant import TenantRepository, TenantModel

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to resolve tenant from subdomain and inject into request context"""
    
    def __init__(self, app, tenant_repo: TenantRepository):
        super().__init__(app)
        self.tenant_repo = tenant_repo
        self.excluded_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and inject tenant context"""
        
        # Skip tenant resolution for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extract tenant from subdomain
        tenant = await self._resolve_tenant_from_request(request)
        
        if not tenant:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Tenant not found or invalid subdomain"}
            )
        
        # Check tenant status
        if tenant.status != "active" and tenant.status != "trial":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": f"Tenant account is {tenant.status}"}
            )
        
        # Inject tenant into request state
        request.state.tenant = tenant
        request.state.tenant_id = tenant.id
        
        # Add tenant context to headers for downstream services
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant.id
        response.headers["X-Tenant-Subdomain"] = tenant.subdomain
        
        return response
    
    async def _resolve_tenant_from_request(self, request: Request) -> Optional[TenantModel]:
        """Resolve tenant from request subdomain"""
        
        # Get host from request
        host = request.headers.get("host", "")
        if not host:
            return None
        
        # Extract subdomain
        subdomain = self._extract_subdomain(host)
        if not subdomain:
            return None
        
        # Get tenant from database
        try:
            tenant = await self.tenant_repo.get_tenant_by_subdomain(subdomain)
            return tenant
        except Exception as e:
            logger.error(f"Error resolving tenant for subdomain {subdomain}: {e}")
            return None
    
    def _extract_subdomain(self, host: str) -> Optional[str]:
        """Extract subdomain from host header"""
        
        # Remove port if present
        host = host.split(':')[0]
        
        # Split by dots
        parts = host.split('.')
        
        # Need at least 3 parts for subdomain (subdomain.domain.tld)
        if len(parts) < 3:
            return None
        
        # First part is subdomain
        subdomain = parts[0]
        
        # Validate subdomain format
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', subdomain):
            return None
        
        # Check for reserved subdomains
        reserved = ['www', 'api', 'admin', 'app', 'mail', 'ftp', 'cdn', 'static']
        if subdomain in reserved:
            return None
        
        return subdomain


class TenantContextManager:
    """Helper class to manage tenant context in request handlers"""
    
    @staticmethod
    def get_tenant_from_request(request: Request) -> TenantModel:
        """Get tenant from request state"""
        if not hasattr(request.state, 'tenant'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant context not available"
            )
        return request.state.tenant
    
    @staticmethod
    def get_tenant_id_from_request(request: Request) -> str:
        """Get tenant ID from request state"""
        if not hasattr(request.state, 'tenant_id'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant context not available"
            )
        return request.state.tenant_id
    
    @staticmethod
    def validate_tenant_access(request: Request, resource_tenant_id: str) -> bool:
        """Validate that resource belongs to current tenant"""
        current_tenant_id = TenantContextManager.get_tenant_id_from_request(request)
        return current_tenant_id == resource_tenant_id


class TenantFilterMixin:
    """Mixin to add tenant filtering to database queries"""
    
    @staticmethod
    def add_tenant_filter(query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Add tenant_id filter to MongoDB query"""
        query["tenant_id"] = tenant_id
        return query
    
    @staticmethod
    def ensure_tenant_isolation(document: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Ensure document has tenant_id for isolation"""
        document["tenant_id"] = tenant_id
        return document


def get_tenant_from_request(request: Request) -> TenantModel:
    """Dependency function to get tenant from request"""
    return TenantContextManager.get_tenant_from_request(request)


def get_tenant_id_from_request(request: Request) -> str:
    """Dependency function to get tenant ID from request"""
    return TenantContextManager.get_tenant_id_from_request(request)


class TenantAwareRepository:
    """Base repository class with tenant isolation using PostgreSQL"""
    
    def __init__(self, connection_manager, model_class):
        self.connection_manager = connection_manager
        self.model_class = model_class
    
    async def find_one(self, query_conditions: list, tenant_id: str) -> Optional[Any]:
        """Find one document with tenant filtering"""
        from sqlalchemy import select
        
        async with self.connection_manager.get_session() as session:
            conditions = [self.model_class.tenant_id == tenant_id] + query_conditions
            result = await session.execute(select(self.model_class).where(*conditions))
            return result.scalar_one_or_none()
    
    async def find_many(
        self, 
        query_conditions: list, 
        tenant_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> list:
        """Find multiple documents with tenant filtering"""
        from sqlalchemy import select
        
        async with self.connection_manager.get_session() as session:
            conditions = [self.model_class.tenant_id == tenant_id] + query_conditions
            result = await session.execute(
                select(self.model_class).where(*conditions).offset(skip).limit(limit)
            )
            return result.scalars().all()
    
    async def insert_one(self, document_data: Dict[str, Any], tenant_id: str) -> Any:
        """Insert document with tenant isolation"""
        document_data["tenant_id"] = tenant_id
        
        async with self.connection_manager.get_session() as session:
            obj = self.model_class(**document_data)
            session.add(obj)
            await session.commit()
            return obj
    
    async def update_one(
        self, 
        query_conditions: list, 
        update_data: Dict[str, Any], 
        tenant_id: str
    ) -> Any:
        """Update document with tenant filtering"""
        from sqlalchemy import update
        
        async with self.connection_manager.get_session() as session:
            conditions = [self.model_class.tenant_id == tenant_id] + query_conditions
            await session.execute(
                update(self.model_class).where(*conditions).values(**update_data)
            )
            await session.commit()
    
    async def delete_one(self, query_conditions: list, tenant_id: str) -> Any:
        """Delete document with tenant filtering"""
        from sqlalchemy import delete
        
        async with self.connection_manager.get_session() as session:
            conditions = [self.model_class.tenant_id == tenant_id] + query_conditions
            await session.execute(delete(self.model_class).where(*conditions))
            await session.commit()
    
    async def count_documents(self, query_conditions: list, tenant_id: str) -> int:
        """Count documents with tenant filtering"""
        from sqlalchemy import select, func
        
        async with self.connection_manager.get_session() as session:
            conditions = [self.model_class.tenant_id == tenant_id] + query_conditions
            result = await session.execute(
                select(func.count(self.model_class.id)).where(*conditions)
            )
            return result.scalar()


class TenantSecurityValidator:
    """Security validation for multi-tenant operations"""
    
    @staticmethod
    def validate_cross_tenant_access(
        current_tenant_id: str,
        resource_tenant_id: str,
        operation: str = "access"
    ) -> bool:
        """Validate that cross-tenant access is not occurring"""
        if current_tenant_id != resource_tenant_id:
            logger.warning(
                f"Cross-tenant {operation} attempt: "
                f"current={current_tenant_id}, resource={resource_tenant_id}"
            )
            return False
        return True
    
    @staticmethod
    def sanitize_tenant_input(tenant_input: str) -> str:
        """Sanitize tenant-related input to prevent injection"""
        # Remove potentially dangerous characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        
        sanitized = tenant_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        # Only allow alphanumeric and underscore
        if not sanitized.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid tenant identifier format")
        
        return sanitized
    
    @staticmethod
    def validate_subdomain_security(subdomain: str) -> bool:
        """Validate subdomain for security issues"""
        # Check length
        if len(subdomain) < 3 or len(subdomain) > 50:
            return False
        
        # Check format
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', subdomain):
            return False
        
        # Check for reserved words
        reserved = [
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 'cdn', 'static',
            'assets', 'images', 'js', 'css', 'fonts', 'uploads', 'files'
        ]
        if subdomain in reserved:
            return False
        
        return True
