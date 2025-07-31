"""
Tenant Data Model and Management
Implements comprehensive multi-tenant data structures and operations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class SubscriptionPlan(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class IndustryType(str, Enum):
    COWORKING = "coworking"
    UNIVERSITY = "university"
    HOTEL = "hotel"
    GOVERNMENT = "government"
    CREATIVE_STUDIO = "creative_studio"
    RESIDENTIAL = "residential"


class TenantSettings(BaseModel):
    """Tenant-specific configuration settings"""
    booking_advance_days: int = Field(default=30, ge=1, le=365)
    cancellation_hours: int = Field(default=24, ge=1, le=168)
    max_booking_duration: int = Field(default=480, ge=30, le=1440)  # minutes
    auto_approval: bool = Field(default=True)
    require_approval_over_hours: int = Field(default=4)
    allow_recurring_bookings: bool = Field(default=True)
    enable_waitlist: bool = Field(default=True)
    enable_notifications: bool = Field(default=True)
    timezone: str = Field(default="UTC")
    currency: str = Field(default="USD")
    language: str = Field(default="en")
    
    # Industry-specific settings
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class TenantBranding(BaseModel):
    """Tenant branding and customization"""
    primary_color: str = Field(default="#3B82F6")
    secondary_color: str = Field(default="#1E40AF")
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None
    company_name: str
    tagline: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None


class TenantFeatures(BaseModel):
    """Feature toggles for tenant"""
    cms_enabled: bool = Field(default=True)
    booking_enabled: bool = Field(default=True)
    lead_management: bool = Field(default=True)
    financial_management: bool = Field(default=True)
    analytics: bool = Field(default=True)
    api_access: bool = Field(default=False)
    custom_integrations: bool = Field(default=False)
    advanced_reporting: bool = Field(default=False)
    white_label: bool = Field(default=False)
    sso_enabled: bool = Field(default=False)
    
    # Industry-specific features
    industry_features: Dict[str, bool] = Field(default_factory=dict)


class TenantModel(BaseModel):
    """Complete tenant data model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    subdomain: str = Field(..., min_length=3, max_length=50)
    industry: IndustryType
    status: TenantStatus = Field(default=TenantStatus.TRIAL)
    subscription_plan: SubscriptionPlan = Field(default=SubscriptionPlan.STARTER)
    
    # Configuration
    settings: TenantSettings = Field(default_factory=TenantSettings)
    branding: TenantBranding
    features: TenantFeatures = Field(default_factory=TenantFeatures)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    trial_ends_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    
    # Owner information
    owner_user_id: Optional[str] = None
    billing_email: str
    
    # Usage tracking
    user_count: int = Field(default=0)
    storage_used_mb: int = Field(default=0)
    api_calls_this_month: int = Field(default=0)
    
    # Module configuration
    module_name: str  # e.g., "coworking_module"
    module_version: str = Field(default="1.0.0")
    module_config: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        """Validate subdomain format"""
        import re
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', v):
            raise ValueError('Subdomain must contain only lowercase letters, numbers, and hyphens')
        if v in ['www', 'api', 'admin', 'app', 'mail', 'ftp']:
            raise ValueError('Subdomain is reserved')
        return v
    
    @validator('billing_email')
    def validate_billing_email(cls, v):
        """Validate billing email format"""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for PostgreSQL storage"""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenantModel':
        """Create from dictionary (PostgreSQL record)"""
        return cls(**data)


class TenantRepository:
    """Repository for tenant data operations"""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
    
    async def initialize(self):
        """Initialize tenant table with indexes"""
        async with self.connection_manager.get_session() as session:
            pass
    
    async def create_tenant(self, tenant_data: TenantModel) -> TenantModel:
        """Create a new tenant"""
        from models.postgresql_models import Tenant
        from sqlalchemy import select
        
        async with self.connection_manager.get_session() as session:
            # Check if subdomain already exists
            result = await session.execute(select(Tenant).where(Tenant.subdomain == tenant_data.subdomain))
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError(f"Subdomain '{tenant_data.subdomain}' already exists")
            
            # Insert tenant
            tenant_obj = Tenant(**tenant_data.to_dict())
            session.add(tenant_obj)
            await session.commit()
            
            return tenant_data
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[TenantModel]:
        """Get tenant by ID"""
        from models.postgresql_models import Tenant
        from sqlalchemy import select
        
        async with self.connection_manager.get_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            return TenantModel.from_dict(tenant.__dict__) if tenant else None
    
    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[TenantModel]:
        """Get tenant by subdomain"""
        from models.postgresql_models import Tenant
        from sqlalchemy import select
        
        async with self.connection_manager.get_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.subdomain == subdomain))
            tenant = result.scalar_one_or_none()
            return TenantModel.from_dict(tenant.__dict__) if tenant else None
    
    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant data"""
        from models.postgresql_models import Tenant
        from sqlalchemy import update
        
        async with self.connection_manager.get_session() as session:
            updates["updated_at"] = datetime.utcnow()
            result = await session.execute(
                update(Tenant).where(Tenant.id == tenant_id).values(**updates)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Soft delete tenant (set status to cancelled)"""
        from models.postgresql_models import Tenant
        from sqlalchemy import update
        
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                update(Tenant).where(Tenant.id == tenant_id).values(
                    status=TenantStatus.CANCELLED,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            return result.rowcount > 0
    
    async def list_tenants(
        self, 
        status: Optional[TenantStatus] = None,
        industry: Optional[IndustryType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TenantModel]:
        """List tenants with filtering"""
        from models.postgresql_models import Tenant
        from sqlalchemy import select
        
        async with self.connection_manager.get_session() as session:
            query = select(Tenant)
            
            if status:
                query = query.where(Tenant.status == status)
            if industry:
                query = query.where(Tenant.industry_module == industry)
            
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            tenants = result.scalars().all()
            
            return [TenantModel.from_dict(tenant.__dict__) for tenant in tenants]
    
    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant usage statistics"""
        from models.postgresql_models import User, Booking, Page
        from sqlalchemy import select, func
        
        tenant = await self.get_tenant_by_id(tenant_id)
        if not tenant:
            return {}
        
        async with self.connection_manager.get_session() as session:
            # Get user count
            user_result = await session.execute(
                select(func.count(User.id)).where(
                    User.tenant_id == tenant_id,
                    User.is_active == True
                )
            )
            user_count = user_result.scalar()
            
            # Get booking count
            booking_result = await session.execute(
                select(func.count(Booking.id)).where(Booking.tenant_id == tenant_id)
            )
            booking_count = booking_result.scalar()
            
            # Get page count
            page_result = await session.execute(
                select(func.count(Page.id)).where(Page.tenant_id == tenant_id)
            )
            page_count = page_result.scalar()
            
            return {
                "user_count": user_count,
                "booking_count": booking_count,
                "page_count": page_count,
                "storage_used_mb": tenant.storage_used_mb,
                "api_calls_this_month": tenant.api_calls_this_month,
                "subscription_plan": tenant.subscription_plan,
                "status": tenant.status
            }
    
    async def update_usage_stats(self, tenant_id: str, stats: Dict[str, Any]):
        """Update tenant usage statistics"""
        from models.postgresql_models import Tenant
        from sqlalchemy import update
        
        async with self.connection_manager.get_session() as session:
            stats["updated_at"] = datetime.utcnow()
            await session.execute(
                update(Tenant).where(Tenant.id == tenant_id).values(**stats)
            )
            await session.commit()


class TenantService:
    """Service layer for tenant operations"""
    
    def __init__(self, tenant_repo: TenantRepository):
        self.tenant_repo = tenant_repo
    
    async def provision_new_tenant(
        self,
        name: str,
        subdomain: str,
        industry: IndustryType,
        billing_email: str,
        owner_data: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> TenantModel:
        """Provision a complete new tenant with default configuration"""
        
        # Create tenant branding
        tenant_branding = TenantBranding(
            company_name=name,
            contact_email=billing_email,
            **branding
        )
        
        # Set industry-specific defaults
        settings = TenantSettings()
        features = TenantFeatures()
        
        if industry == IndustryType.UNIVERSITY:
            settings.booking_advance_days = 90
            settings.cancellation_hours = 48
            features.industry_features = {
                "academic_calendar": True,
                "course_scheduling": True,
                "student_portal": True
            }
        elif industry == IndustryType.HOTEL:
            settings.booking_advance_days = 365
            settings.cancellation_hours = 72
            features.industry_features = {
                "guest_services": True,
                "room_management": True,
                "seasonal_pricing": True
            }
        elif industry == IndustryType.COWORKING:
            settings.booking_advance_days = 30
            settings.cancellation_hours = 24
            features.industry_features = {
                "hot_desk_booking": True,
                "member_community": True,
                "event_management": True
            }
        
        # Create tenant model
        tenant = TenantModel(
            name=name,
            subdomain=subdomain,
            industry=industry,
            billing_email=billing_email,
            branding=tenant_branding,
            settings=settings,
            features=features,
            module_name=f"{industry.value}_module",
            trial_ends_at=datetime.utcnow() + timedelta(days=14)  # 14-day trial
        )
        
        # Create tenant
        created_tenant = await self.tenant_repo.create_tenant(tenant)
        
        return created_tenant
    
    async def validate_subdomain_available(self, subdomain: str) -> bool:
        """Check if subdomain is available"""
        existing = await self.tenant_repo.get_tenant_by_subdomain(subdomain)
        return existing is None
    
    async def upgrade_subscription(
        self,
        tenant_id: str,
        new_plan: SubscriptionPlan
    ) -> bool:
        """Upgrade tenant subscription plan"""
        
        # Define plan features
        plan_features = {
            SubscriptionPlan.STARTER: {
                "api_access": False,
                "advanced_reporting": False,
                "custom_integrations": False,
                "white_label": False
            },
            SubscriptionPlan.PROFESSIONAL: {
                "api_access": True,
                "advanced_reporting": True,
                "custom_integrations": False,
                "white_label": False
            },
            SubscriptionPlan.ENTERPRISE: {
                "api_access": True,
                "advanced_reporting": True,
                "custom_integrations": True,
                "white_label": True
            }
        }
        
        # Update tenant
        updates = {
            "subscription_plan": new_plan,
            "features": plan_features[new_plan]
        }
        
        return await self.tenant_repo.update_tenant(tenant_id, updates)
