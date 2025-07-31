"""
Claude Platform Core - Integrates kernels with modules for complete experience orchestration
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid

from kernels import (
    IdentityKernel,
    BookingKernel,
    FinancialKernel,
    CMSKernel,
    CommunicationKernel,
)
from kernels.lead_kernel import LeadKernel
from modules import BaseModule
from modules.module_registry import load_tenant_module


def convert_uuid_to_str(obj):
    """Convert UUID to string recursively"""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_uuid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_uuid_to_str(item) for item in obj]
    else:
        return obj


class ClaudePlatformCore:
    """Core platform that orchestrates kernels and modules"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.kernels = {}
        self.active_modules = {}  # tenant_id -> module instance
        self._initialize_kernels()

    def _initialize_kernels(self):
        """Initialize all universal kernels"""
        secret_key = os.environ.get(
            "SECRET_KEY", "your-secret-key-change-this-in-production"
        )

        self.kernels = {
            "identity": IdentityKernel(self.session, secret_key),
            "booking": BookingKernel(self.session),
            "financial": FinancialKernel(self.session),
            "cms": CMSKernel(self.session),
            "communication": CommunicationKernel(self.session),
            "lead": LeadKernel(self.session),
        }

    async def initialize(self):
        """Initialize the platform and all kernels"""
        for kernel_name, kernel in self.kernels.items():
            await kernel.initialize()
            print(f"✅ Initialized {kernel_name} kernel")

    async def load_tenant_module(self, tenant_id: str) -> BaseModule:
        """Load and cache module for tenant"""
        if tenant_id in self.active_modules:
            return self.active_modules[tenant_id]

        # Get tenant data
        from models.postgresql_models import Tenant
        from sqlalchemy import select

        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_data = result.scalar_one_or_none()
        if not tenant_data:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Load appropriate module
        module = load_tenant_module(tenant_data)
        self.active_modules[tenant_id] = module

        return module

    async def get_tenant_experience(self, tenant_id: str) -> Dict[str, Any]:
        """Get complete tenant experience configuration"""
        module = await self.load_tenant_module(tenant_id)

        return {
            "module_info": {
                "name": module.get_module_name(),
                "version": module.get_module_version(),
                "industry": module.get_industry_type(),
            },
            "terminology": module.get_terminology_dictionary(),
            "features": module.get_enabled_features(),
            "navigation": module.get_navigation_structure(),
            "dashboard": module.get_dashboard_layout(),
            "roles": module.get_role_hierarchy(),
            "workflows": module.get_active_workflows(),
            "color_scheme": module.get_color_scheme(),
            "booking_rules": module.get_booking_rules(),
            "resource_types": module.get_resource_types(),
        }

    async def translate_response(self, tenant_id: str, response_data: Any) -> Any:
        """Translate response data using tenant's module terminology"""
        module = await self.load_tenant_module(tenant_id)
        return module.translate_object(response_data)

    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user access across all kernels"""
        for kernel in self.kernels.values():
            if not await kernel.validate_tenant_access(tenant_id, user_id):
                return False
        return True

    async def check_feature_access(self, tenant_id: str, feature_name: str) -> bool:
        """Check if tenant has access to specific feature"""
        module = await self.load_tenant_module(tenant_id)
        return module.is_feature_enabled(feature_name)

    async def check_user_permission(
        self, tenant_id: str, user_id: str, permission: str
    ) -> bool:
        """Check if user has specific permission"""
        identity_kernel = self.kernels["identity"]

        # First validate that user belongs to tenant
        if not await identity_kernel.validate_tenant_access(tenant_id, user_id):
            return False

        return await identity_kernel.check_permission(user_id, permission)

    async def trigger_workflow(
        self, tenant_id: str, event: str, context: Dict[str, Any]
    ):
        """Trigger workflows via communication kernel"""
        communication_kernel = self.kernels["communication"]
        await communication_kernel.trigger_event(tenant_id, event, context)

    async def get_dashboard_data(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Get dashboard data with module-specific metrics"""
        module = await self.load_tenant_module(tenant_id)

        # Get basic stats from kernels
        identity_kernel = self.kernels["identity"]
        booking_kernel = self.kernels["booking"]
        financial_kernel = self.kernels["financial"]
        cms_kernel = self.kernels["cms"]

        # Get user info
        user = await identity_kernel.get_user_by_id(user_id)
        tenant = await identity_kernel.get_tenant_by_id(tenant_id)

        # Convert UUIDs to strings to avoid serialization issues
        user = convert_uuid_to_str(user) if user else {}
        tenant = convert_uuid_to_str(tenant) if tenant else {}

        # Get metrics based on module configuration
        metrics = {}
        for metric_config in module.get_dashboard_metrics():
            metric_name = metric_config["name"]

            # Calculate metric based on type and name
            from models.postgresql_models import User, Booking, Page, Lead
            from sqlalchemy import select, func

            if metric_name == "active_users" or metric_name == "active_members":
                result = await self.session.execute(
                    select(func.count(User.id)).where(
                        User.tenant_id == tenant_id, User.is_active == True
                    )
                )
                metrics[metric_name] = result.scalar()
            elif metric_name == "total_bookings" or metric_name == "active_bookings":
                result = await self.session.execute(
                    select(func.count(Booking.id)).where(
                        Booking.tenant_id == tenant_id, Booking.status == "confirmed"
                    )
                )
                metrics[metric_name] = result.scalar()
            elif metric_name == "total_pages":
                result = await self.session.execute(
                    select(func.count(Page.id)).where(
                        Page.tenant_id == tenant_id, Page.status == "published"
                    )
                )
                metrics[metric_name] = result.scalar()
            elif metric_name == "total_leads" or metric_name == "new_leads":
                result = await self.session.execute(
                    select(func.count(Lead.id)).where(Lead.tenant_id == tenant_id)
                )
                metrics[metric_name] = result.scalar()
            # Add more metric calculations as needed

        return {
            "user": module.translate_object(user),
            "tenant": module.translate_object(tenant),
            "metrics": module.translate_object(metrics),
            "dashboard_config": module.get_dashboard_layout(),
            "quick_actions": module.get_dashboard_layout().get("quick_actions", []),
        }

    async def get_platform_health(self) -> Dict[str, Any]:
        """Get health status of entire platform"""
        kernel_health = {}
        for name, kernel in self.kernels.items():
            kernel_health[name] = await kernel.get_kernel_health()

        from models.postgresql_models import Tenant
        from sqlalchemy import select, func

        result = await self.session.execute(
            select(func.count(Tenant.id)).where(Tenant.is_active == True)
        )
        total_tenants = result.scalar()

        return {
            "platform_status": "healthy",
            "kernels": kernel_health,
            "active_modules": len(self.active_modules),
            "total_tenants": total_tenants,
        }

    def get_kernel(self, kernel_name: str):
        """Get specific kernel instance"""
        return self.kernels.get(kernel_name)

    async def reload_tenant_module(self, tenant_id: str):
        """Reload module for tenant (useful after configuration changes)"""
        if tenant_id in self.active_modules:
            del self.active_modules[tenant_id]
        return await self.load_tenant_module(tenant_id)


# Global platform instance
platform_core = None


async def get_platform_core(session: AsyncSession) -> ClaudePlatformCore:
    """Get or create the global platform core instance"""
    global platform_core
    if platform_core is None:
        platform_core = ClaudePlatformCore(session)
        await platform_core.initialize()
    return platform_core


async def initialize_platform(session: AsyncSession) -> ClaudePlatformCore:
    """Initialize the Claude Platform"""
    core = ClaudePlatformCore(session)
    await core.initialize()

    global platform_core
    platform_core = core

    return core
