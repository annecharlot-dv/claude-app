"""
Identity & Authentication Kernel
Manages users, roles, permissions, and authentication across all tenants
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from kernels.base_kernel import BaseKernel
from models.postgresql_models import User, UserPassword, Tenant
from sqlalchemy import select, update


class IdentityKernel(BaseKernel):
    """Universal identity and authentication management"""

    def __init__(self, connection_manager, secret_key: str, algorithm: str = "HS256"):
        super().__init__(connection_manager)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def _initialize_kernel(self):
        """Initialize identity kernel"""
        pass

    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
            return user is not None

    # User Management
    async def create_user(
        self, tenant_id: str, user_data: Dict[str, Any], password: str
    ) -> Dict[str, Any]:
        """Create a new user in the system"""
        # Hash password
        hashed_password = self.pwd_context.hash(password)

        async with self.connection_manager.get_session() as session:
            # Create user
            user_obj = User(
                **user_data,
                tenant_id=tenant_id,
                is_active=True,
                created_at=datetime.utcnow(),
                last_login=None,
            )
            session.add(user_obj)

            password_obj = UserPassword(
                user_id=user_obj.id, hashed_password=hashed_password
            )
            session.add(password_obj)

            await session.commit()

            return {
                "id": user_obj.id,
                "tenant_id": user_obj.tenant_id,
                "email": user_obj.email,
                "role": user_obj.role,
                "is_active": user_obj.is_active,
                "created_at": user_obj.created_at,
                "last_login": user_obj.last_login,
            }

    async def authenticate_user(
        self, tenant_subdomain: str, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data if valid"""
        async with self.connection_manager.get_session() as session:
            # Find tenant
            tenant_result = await session.execute(
                select(Tenant).where(Tenant.subdomain == tenant_subdomain)
            )
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                return None

            # Find user
            user_result = await session.execute(
                select(User).where(
                    User.email == email,
                    User.tenant_id == tenant.id,
                    User.is_active == True,
                )
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return None

            # Verify password
            password_result = await session.execute(
                select(UserPassword).where(UserPassword.user_id == user.id)
            )
            password_doc = password_result.scalar_one_or_none()
            if not password_doc or not self.pwd_context.verify(
                password, password_doc.hashed_password
            ):
                return None

            # Update last login
            await session.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_login=datetime.utcnow())
            )
            await session.commit()

            return {
                "id": user.id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": datetime.utcnow(),
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                    "industry_module": tenant.industry_module,
                },
            }

    async def create_access_token(
        self, user_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = {"sub": user_id}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.PyJWTError:
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            return {
                "id": user.id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login,
            }

    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions based on role"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return []

        # Define role-based permissions
        role_permissions = {
            "platform_admin": ["*"],  # All permissions
            "account_owner": [
                "tenant.manage",
                "users.manage",
                "pages.manage",
                "forms.manage",
                "leads.manage",
                "tours.manage",
                "settings.manage",
                "role.account_owner",  # Add role-based permission
            ],
            "administrator": [
                "users.manage",
                "pages.manage",
                "forms.manage",
                "leads.manage",
                "tours.manage",
                "role.administrator",
            ],
            "property_manager": [
                "pages.manage",
                "forms.manage",
                "leads.manage",
                "tours.manage",
                "role.property_manager",
            ],
            "front_desk": [
                "leads.view",
                "leads.update",
                "tours.view",
                "tours.manage",
                "role.front_desk",
            ],
            "member": ["dashboard.view", "role.member"],
            "company_admin": ["dashboard.view", "role.company_admin"],
            "company_user": ["dashboard.view", "role.company_user"],
            "maintenance": ["spaces.view", "spaces.update", "role.maintenance"],
            "security": ["access.manage", "role.security"],
        }

        return role_permissions.get(user["role"], [])

    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = await self.get_user_permissions(user_id)
        return "*" in permissions or permission in permissions

    # Tenant Management
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tenant"""
        async with self.connection_manager.get_session() as session:
            tenant_obj = Tenant(
                **tenant_data, is_active=True, created_at=datetime.utcnow()
            )
            session.add(tenant_obj)
            await session.commit()

            return {
                "id": tenant_obj.id,
                "name": tenant_obj.name,
                "subdomain": tenant_obj.subdomain,
                "industry_module": tenant_obj.industry_module,
                "is_active": tenant_obj.is_active,
                "created_at": tenant_obj.created_at,
            }

    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """Get tenant by subdomain"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.subdomain == subdomain, Tenant.is_active == True
                )
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                return None

            return {
                "id": tenant.id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "industry_module": tenant.industry_module,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at,
            }

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
            )
            tenant = result.scalar_one_or_none()
            if not tenant:
                return None

            return {
                "id": tenant.id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "industry_module": tenant.industry_module,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at,
            }
