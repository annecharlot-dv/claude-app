"""
PostgreSQL Identity & Authentication Kernel (The "Gatekeeper")
Universal user management and authentication system - PostgreSQL Version
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from kernels.postgresql_base_kernel import PostgreSQLBaseKernel
from models.postgresql_models import User, Tenant, UserPassword
from passlib.context import CryptContext
from sqlalchemy import select, and_
import jwt
import uuid
import logging

logger = logging.getLogger(__name__)


class PostgreSQLIdentityKernel(PostgreSQLBaseKernel):
    """Universal identity and authentication management with PostgreSQL"""

    def __init__(self, db_session, secret_key: str, algorithm: str = "HS256"):
        super().__init__(db_session)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        user = await self.get_by_field(User, "id", user_id, tenant_id)
        return user is not None and str(user.tenant_id) == tenant_id

    # User Management
    async def create_user(
        self, tenant_id: str, user_data: Dict[str, Any], password: str
    ) -> Dict[str, Any]:
        """Create a new user in the system"""
        try:
            # Hash password
            hashed_password = self.pwd_context.hash(password)

            # Create user
            user = await self.create_record(User, user_data, tenant_id)

            # Create password record
            password_data = {"user_id": user.id, "hashed_password": hashed_password}
            await self.create_record(UserPassword, password_data)

            # Convert to dict for response
            user_dict = {
                "id": str(user.id),
                "tenant_id": str(user.tenant_id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "profile": user.profile,
                "created_at": user.created_at,
                "last_login": user.last_login,
            }

            logger.info(f"Created user: {user.email} for tenant: {tenant_id}")
            return user_dict

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    async def get_user_by_email(
        self, tenant_id: str, email: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by email within tenant"""
        try:
            await self.set_tenant_context(tenant_id)
            user = await self.get_by_field(User, "email", email, tenant_id)

            if user:
                return {
                    "id": str(user.id),
                    "tenant_id": str(user.tenant_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "profile": user.profile,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise

    async def get_user_by_id(
        self, user_id: str, tenant_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            if tenant_id:
                await self.set_tenant_context(tenant_id)

            user = await self.get_by_id(User, user_id, tenant_id)

            if user:
                return {
                    "id": str(user.id),
                    "tenant_id": str(user.tenant_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "profile": user.profile,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            raise

    async def authenticate_user(
        self, tenant_subdomain: str, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            # Find tenant by subdomain
            tenant = await self.get_by_field(Tenant, "subdomain", tenant_subdomain)
            if not tenant or not tenant.is_active:
                logger.warning(f"Tenant not found or inactive: {tenant_subdomain}")
                return None

            # Set tenant context
            await self.set_tenant_context(str(tenant.id))

            # Find user by email
            user = await self.get_by_field(User, "email", email, str(tenant.id))
            if not user or not user.is_active:
                logger.warning(f"User not found or inactive: {email}")
                return None

            # Get password hash
            session = await self._get_session()
            result = await session.execute(
                select(UserPassword).where(UserPassword.user_id == user.id)
            )
            password_record = result.scalar_one_or_none()

            if not password_record:
                logger.warning(f"No password record found for user: {email}")
                return None

            # Verify password
            if not self.pwd_context.verify(password, password_record.hashed_password):
                logger.warning(f"Invalid password for user: {email}")
                return None

            # Update last login
            await self.update_record(
                User, user.id, {"last_login": datetime.utcnow()}, str(tenant.id)
            )

            # Return user and tenant info
            return {
                "id": str(user.id),
                "tenant_id": str(user.tenant_id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "profile": user.profile,
                "created_at": user.created_at,
                "last_login": datetime.utcnow(),
                "tenant": {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                    "industry_module": tenant.industry_module,
                    "plan": tenant.plan,
                    "is_active": tenant.is_active,
                },
            }

        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None

    async def update_user(
        self, tenant_id: str, user_id: str, updates: Dict[str, Any]
    ) -> bool:
        """Update user information"""
        try:
            await self.set_tenant_context(tenant_id)
            updated_user = await self.update_record(User, user_id, updates, tenant_id)
            return updated_user is not None

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    async def change_password(
        self, tenant_id: str, user_id: str, new_password: str
    ) -> bool:
        """Change user password"""
        try:
            # Hash new password
            hashed_password = self.pwd_context.hash(new_password)

            # Update password record
            session = await self._get_session()
            await self.set_tenant_context(tenant_id)

            result = await session.execute(
                select(UserPassword).where(UserPassword.user_id == uuid.UUID(user_id))
            )
            password_record = result.scalar_one_or_none()

            if password_record:
                await self.update_record(
                    UserPassword,
                    password_record.id,
                    {
                        "hashed_password": hashed_password,
                        "updated_at": datetime.utcnow(),
                    },
                )
                logger.info(f"Password changed for user: {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise

    # Tenant Management
    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """Get tenant by subdomain"""
        try:
            tenant = await self.get_by_field(Tenant, "subdomain", subdomain)

            if tenant:
                return {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                    "custom_domain": tenant.custom_domain,
                    "industry_module": tenant.industry_module,
                    "plan": tenant.plan,
                    "is_active": tenant.is_active,
                    "branding": tenant.branding,
                    "settings": tenant.settings,
                    "feature_toggles": tenant.feature_toggles,
                    "created_at": tenant.created_at,
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get tenant by subdomain {subdomain}: {e}")
            raise

    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        try:
            tenant = await self.get_by_id(Tenant, tenant_id)

            if tenant:
                return {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                    "custom_domain": tenant.custom_domain,
                    "industry_module": tenant.industry_module,
                    "plan": tenant.plan,
                    "is_active": tenant.is_active,
                    "branding": tenant.branding,
                    "settings": tenant.settings,
                    "feature_toggles": tenant.feature_toggles,
                    "created_at": tenant.created_at,
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get tenant by ID {tenant_id}: {e}")
            raise

    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tenant"""
        try:
            tenant = await self.create_record(Tenant, tenant_data)

            return {
                "id": str(tenant.id),
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "custom_domain": tenant.custom_domain,
                "industry_module": tenant.industry_module,
                "plan": tenant.plan,
                "is_active": tenant.is_active,
                "branding": tenant.branding,
                "settings": tenant.settings,
                "feature_toggles": tenant.feature_toggles,
                "created_at": tenant.created_at,
            }

        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            raise

    # JWT Token Management
    async def create_access_token(
        self, user_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=30)

            to_encode = {"sub": user_id, "exp": expire, "iat": datetime.utcnow()}

            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=self.algorithm
            )
            return encoded_jwt

        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise

    async def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")

            if user_id is None:
                return None

            return user_id

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    # Role and Permission Management
    async def check_user_permission(
        self, tenant_id: str, user_id: str, permission: str
    ) -> bool:
        """Check if user has specific permission"""
        try:
            user = await self.get_user_by_id(user_id, tenant_id)
            if not user or not user["is_active"]:
                return False

            # Simple role-based permission check
            role = user["role"]

            # Platform admin has all permissions
            if role == "platform_admin":
                return True

            # Define role hierarchy and permissions
            role_permissions = {
                "account_owner": ["*"],  # All permissions within tenant
                "administrator": [
                    "user.create",
                    "user.update",
                    "page.create",
                    "page.update",
                    "page.delete",
                    "lead.manage",
                ],
                "property_manager": [
                    "page.create",
                    "page.update",
                    "lead.manage",
                    "booking.manage",
                ],
                "front_desk": ["lead.view", "lead.update", "booking.view"],
                "member": ["profile.update"],
            }

            allowed_permissions = role_permissions.get(role, [])

            # Check if user has permission
            if "*" in allowed_permissions or permission in allowed_permissions:
                return True

            # Check role-based permissions
            if permission.startswith("role.") and permission == f"role.{role}":
                return True

            return False

        except Exception as e:
            logger.error(
                f"Failed to check permission {permission} for user {user_id}: {e}"
            )
            return False

    async def list_users(
        self,
        tenant_id: str,
        filters: Dict[str, Any] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List users in tenant"""
        try:
            users = await self.list_records(
                User,
                filters=filters,
                tenant_id=tenant_id,
                limit=limit,
                offset=offset,
                order_by="created_at DESC",
            )

            return [
                {
                    "id": str(user.id),
                    "tenant_id": str(user.tenant_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "profile": user.profile,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                }
                for user in users
            ]

        except Exception as e:
            logger.error(f"Failed to list users for tenant {tenant_id}: {e}")
            raise

    async def get_kernel_health(self) -> Dict[str, Any]:
        """Get kernel health status"""
        try:
            # Test basic operations
            session = await self._get_session()

            # Test tenant query
            result = await session.execute(select(Tenant).limit(1))
            tenant_test = result.scalar_one_or_none()

            # Test user query
            result = await session.execute(select(User).limit(1))
            user_test = result.scalar_one_or_none()

            return {
                "status": "healthy",
                "database": "postgresql",
                "kernel": "PostgreSQLIdentityKernel",
                "tables": ["tenants", "users", "user_passwords"],
                "test_results": {
                    "tenant_query": "success" if tenant_test is not None else "no_data",
                    "user_query": "success" if user_test is not None else "no_data",
                },
                "last_check": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "postgresql",
                "kernel": "PostgreSQLIdentityKernel",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }
