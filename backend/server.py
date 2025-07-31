from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

# Import database components
from database.config.connection_pool import PostgreSQLConnectionManager
from kernels.postgresql_identity_kernel import PostgreSQLIdentityKernel
from models.cross_db_models import Base

# Import performance optimizations
from performance.database_optimizer import get_db_optimizer
from performance.cache_manager import get_cache_manager
from performance.monitor import get_performance_monitor, monitor_performance
from performance.api_optimizer import PerformanceMiddleware, cache_response
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from enum import Enum
import json

# Import the new core platform
from claude_platform_core import initialize_platform, get_platform_core

# Import Enhanced CMS Engine
from cms_engine.coworking_cms import CoworkingCMSEngine

# Import multi-tenant components
from models.tenant import TenantRepository, TenantService
from middleware.tenant_middleware import TenantMiddleware
from api.tenant_api import router as tenant_router
from api.lead_api import router as lead_router
from api.financial_api import router as financial_router
from api.communication_api import router as communication_router
from api.health_api import router as health_router


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
connection_manager = PostgreSQLConnectionManager()

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(
    title="Claude - Space-as-a-Service Platform", 
    version="3.0.0",
    docs_url="/api/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add performance middleware
app.add_middleware(PerformanceMiddleware, enable_caching=True, enable_compression=True)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize PostgreSQL connection and kernels on startup"""
    global connection_manager, identity_kernel, platform_core
    
    try:
        # Initialize PostgreSQL connection
        connection_manager = PostgreSQLConnectionManager()
        await connection_manager.initialize()
        
        # Initialize identity kernel
        async with connection_manager.get_session() as session:
            identity_kernel = PostgreSQLIdentityKernel(session, SECRET_KEY)
        
        # Initialize platform core (if needed)
        # platform_core = await initialize_platform(connection_manager)
        
        logger.info("✅ PostgreSQL backend initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize PostgreSQL backend: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up PostgreSQL connections on shutdown"""
    global connection_manager
    
    try:
        if connection_manager:
            await connection_manager.close()
        logger.info("✅ PostgreSQL connections closed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Global platform core instance
platform_core = None
identity_kernel = None

# Enums
class UserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    ACCOUNT_OWNER = "account_owner"
    ADMINISTRATOR = "administrator"
    PROPERTY_MANAGER = "property_manager"
    FRONT_DESK = "front_desk"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    MEMBER = "member"
    COMPANY_ADMIN = "company_admin"
    COMPANY_USER = "company_user"

class IndustryModule(str, Enum):
    COWORKING = "coworking"
    GOVERNMENT = "government"
    COMMERCIAL_RE = "commercial_re"
    HOTEL = "hotel"
    UNIVERSITY = "university"
    CREATIVE = "creative"
    RESIDENTIAL = "residential"

class LeadStatus(str, Enum):
    NEW_INQUIRY = "new_inquiry"
    TOUR_SCHEDULED = "tour_scheduled"
    TOUR_COMPLETED = "tour_completed"
    CONVERTED = "converted"
    CLOSED = "closed"

class PageStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class WidgetType(str, Enum):
    HERO_BANNER = "hero_banner"
    BOOKING_CALENDAR = "booking_calendar"
    PRICING_CARDS = "pricing_cards"
    EVENT_LISTINGS = "event_listings"
    LEAD_FORM = "lead_form"
    TOUR_SCHEDULER = "tour_scheduler"
    MEMBER_DIRECTORY = "member_directory"
    TESTIMONIALS = "testimonials"
    FAQ = "faq"
    CONTACT_INFO = "contact_info"
    GALLERY = "gallery"
    NEWSLETTER_SIGNUP = "newsletter_signup"

class FormFieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    TIME = "time"
    NUMBER = "number"
    FILE = "file"

# Core Models
class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subdomain: str
    custom_domain: Optional[str] = None
    industry_module: IndustryModule = IndustryModule.COWORKING
    plan: str = "starter"
    is_active: bool = True
    branding: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    feature_toggles: Dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool = True
    company_id: Optional[str] = None  # For company users
    profile: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

# CMS Models
class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    slug: str
    content_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: PageStatus = PageStatus.DRAFT
    template_id: Optional[str] = None
    is_homepage: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Template(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    industry_module: IndustryModule
    preview_image: Optional[str] = None
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    default_content: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class Widget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    type: WidgetType
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Lead Management Models
class FormField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    type: FormFieldType
    is_required: bool = False
    options: List[str] = Field(default_factory=list)  # For select/radio/checkbox
    placeholder: Optional[str] = None
    validation_rules: Dict[str, Any] = Field(default_factory=dict)

class Form(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    title: str
    description: Optional[str] = None
    fields: List[FormField] = Field(default_factory=list)
    success_message: str = "Thank you for your submission!"
    redirect_url: Optional[str] = None
    email_notifications: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW_INQUIRY
    source: Optional[str] = None  # Form name, referral, etc.
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    assigned_to: Optional[str] = None  # User ID
    tour_scheduled_at: Optional[datetime] = None
    tour_completed_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TourSlot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    staff_user_id: str
    date: datetime
    duration_minutes: int = 30
    max_bookings: int = 1
    is_available: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Tour(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    lead_id: str
    tour_slot_id: str
    scheduled_at: datetime
    staff_user_id: str
    status: str = "scheduled"  # scheduled, completed, cancelled, no_show
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response Models
class TenantCreate(BaseModel):
    name: str
    subdomain: str
    industry_module: IndustryModule
    admin_email: EmailStr
    admin_password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.MEMBER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PageCreate(BaseModel):
    title: str
    slug: str
    content_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    template_id: Optional[str] = None
    is_homepage: bool = False

class PageUpdate(BaseModel):
    title: Optional[str] = None
    content_blocks: Optional[List[Dict[str, Any]]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: Optional[PageStatus] = None

class FormCreate(BaseModel):
    name: str
    title: str
    description: Optional[str] = None
    fields: List[FormField]
    success_message: str = "Thank you for your submission!"
    email_notifications: List[str] = Field(default_factory=list)

class FormSubmission(BaseModel):
    form_id: str
    data: Dict[str, Any]
    source_url: Optional[str] = None

class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class TourSlotCreate(BaseModel):
    staff_user_id: str
    date: datetime
    duration_minutes: int = 30
    max_bookings: int = 1

class TourBooking(BaseModel):
    tour_slot_id: str
    lead_id: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user using PostgreSQL identity kernel"""
    global identity_kernel
    
    if not identity_kernel:
        raise HTTPException(status_code=500, detail="Identity kernel not initialized")
    
    # Verify token
    user_id = await identity_kernel.verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Get user
    user_data = await identity_kernel.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_data)

def require_role(required_roles: List[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        async with connection_manager.get_session() as session:
            core = await get_platform_core(session)
        
        # Convert user role to string if it's an enum
        user_role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        
        # Check permission using identity kernel
        has_permission = await core.check_user_permission(
            current_user.tenant_id, 
            current_user.id, 
            f"role.{user_role_str}"
        )
        
        # Convert UserRole enums to strings for comparison
        required_role_strings = [role.value for role in required_roles]
        
        if not has_permission or user_role_str not in required_role_strings:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Authentication routes
@api_router.post("/auth/register", response_model=Token)
async def register_user(user_data: UserCreate, tenant_subdomain: str):
    """Register new user using PostgreSQL identity kernel"""
    global identity_kernel
    
    if not identity_kernel:
        raise HTTPException(status_code=500, detail="Identity kernel not initialized")
    
    # Find tenant
    tenant = await identity_kernel.get_tenant_by_subdomain(tenant_subdomain)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user already exists
    existing_user = await identity_kernel.get_user_by_email(tenant["id"], user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Create user using identity kernel
    user_dict = user_data.dict()
    password = user_dict.pop("password")
    user_dict["id"] = str(uuid.uuid4())
    
    created_user = await identity_kernel.create_user(tenant["id"], user_dict, password)
    
    # Create access token
    access_token = await identity_kernel.create_access_token(
        created_user["id"], 
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(access_token=access_token, user=User(**created_user))

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_data: UserLogin, tenant_subdomain: str):
    """Login user using PostgreSQL identity kernel"""
    global identity_kernel
    
    if not identity_kernel:
        raise HTTPException(status_code=500, detail="Identity kernel not initialized")
    
    # Authenticate user
    auth_result = await identity_kernel.authenticate_user(
        tenant_subdomain, 
        user_data.email, 
        user_data.password
    )
    
    if not auth_result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = await identity_kernel.create_access_token(
        auth_result["id"],
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(access_token=access_token, user=User(**auth_result))

# Tenant management
@api_router.post("/tenants", response_model=Tenant)
async def create_tenant(tenant_data: TenantCreate):
    # Check if subdomain is available
    from backend.models.postgresql_models import Tenant
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.subdomain == tenant_data.subdomain))
        existing_tenant = result.scalar_one_or_none()
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Subdomain already taken")
    
    # Create tenant with industry-specific defaults
    tenant = Tenant(
        name=tenant_data.name,
        subdomain=tenant_data.subdomain,
        industry_module=tenant_data.industry_module,
        feature_toggles=get_default_feature_toggles(tenant_data.industry_module)
    )
    
    async with connection_manager.get_session() as session:
        tenant_obj = Tenant(**tenant.dict())
        session.add(tenant_obj)
        await session.commit()
    
    # Create account owner
    hashed_password = get_password_hash(tenant_data.admin_password)
    admin_user = User(
        tenant_id=tenant.id,
        email=tenant_data.admin_email,
        first_name="Account",
        last_name="Owner",
        role=UserRole.ACCOUNT_OWNER
    )
    
    async with connection_manager.get_session() as session:
        from backend.models.postgresql_models import User, UserPassword
        
        admin_user_obj = User(**admin_user.dict())
        session.add(admin_user_obj)
        
        user_password = UserPassword(user_id=admin_user.id, hashed_password=hashed_password)
        session.add(user_password)
        await session.commit()
    
    # Create default homepage
    await create_default_homepage(tenant.id, tenant_data.industry_module)
    
    return tenant

def get_default_feature_toggles(industry_module: IndustryModule) -> Dict[str, bool]:
    """Get default feature toggles based on industry module"""
    base_features = {
        "website_builder": True,
        "lead_management": True,
        "booking_system": True,
        "support_system": True,
        "financial_management": True,
    }
    
    if industry_module == IndustryModule.COWORKING:
        base_features.update({
            "community_platform": True,
            "events_system": True,
            "member_directory": True,
        })
    elif industry_module == IndustryModule.GOVERNMENT:
        base_features.update({
            "approval_workflows": True,
            "public_transparency": True,
            "accessibility_features": True,
        })
    elif industry_module == IndustryModule.HOTEL:
        base_features.update({
            "complex_resource_booking": True,
            "guest_management": True,
        })
    
    return base_features

async def create_default_homepage(tenant_id: str, industry_module: IndustryModule):
    """Create a default homepage based on industry module"""
    # Get default template for industry
    from backend.models.postgresql_models import Template
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(select(Template).where(Template.industry_module == industry_module))
        template = result.scalar_one_or_none()
    
    default_content = get_default_page_content(industry_module)
    
    homepage = Page(
        tenant_id=tenant_id,
        title="Welcome",
        slug="home",
        content_blocks=default_content,
        meta_title=f"Welcome to Our Space",
        meta_description="Discover our amazing space and book your next meeting or workspace.",
        status=PageStatus.PUBLISHED,
        template_id=template["id"] if template else None,
        is_homepage=True
    )
    
    async with connection_manager.get_session() as session:
        from backend.models.postgresql_models import Page
        
        homepage_obj = Page(**homepage.dict())
        session.add(homepage_obj)
        await session.commit()

def get_default_page_content(industry_module: IndustryModule) -> List[Dict[str, Any]]:
    """Get default content blocks for homepage based on industry"""
    if industry_module == IndustryModule.COWORKING:
        return [
            {
                "type": "hero_banner",
                "config": {
                    "title": "Welcome to Our Coworking Space",
                    "subtitle": "Where innovation meets collaboration",
                    "background_image": "/images/coworking-hero.jpg",
                    "cta_text": "Book Your Space Today",
                    "cta_link": "/booking"
                }
            },
            {
                "type": "pricing_cards",
                "config": {
                    "title": "Membership Plans",
                    "plans": [
                        {
                            "name": "Hot Desk",
                            "price": "$99/month",
                            "features": ["Flexible seating", "WiFi", "Coffee"]
                        },
                        {
                            "name": "Dedicated Desk",
                            "price": "$199/month",
                            "features": ["Your own desk", "Storage", "24/7 access"]
                        }
                    ]
                }
            }
        ]
    elif industry_module == IndustryModule.GOVERNMENT:
        return [
            {
                "type": "hero_banner",
                "config": {
                    "title": "Public Facility Booking",
                    "subtitle": "Reserve community spaces for your events",
                    "background_image": "/images/government-hero.jpg",
                    "cta_text": "View Available Spaces",
                    "cta_link": "/spaces"
                }
            }
        ]
    else:
        return [
            {
                "type": "hero_banner",
                "config": {
                    "title": "Welcome to Our Space",
                    "subtitle": "Book your perfect workspace",
                    "cta_text": "Get Started",
                    "cta_link": "/booking"
                }
            }
        ]

# CMS Routes
@api_router.get("/cms/pages", response_model=List[Page])
@cache_response(ttl=1800, tags=["pages"])  # Cache for 30 minutes
@monitor_performance("api_response")
async def get_pages(
    status: Optional[PageStatus] = None,
    limit: int = 25,
    skip: int = 0,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    from backend.models.postgresql_models import Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        db_optimizer = await get_db_optimizer(session)
        
        query_conditions = [Page.tenant_id == current_user.tenant_id]
        if status:
            query_conditions.append(Page.status == status)
        
        result = await session.execute(
            select(Page).where(*query_conditions).offset(skip).limit(limit)
        )
        pages = result.scalars().all()
        
        await db_optimizer.log_query_performance("pages", "find", len(pages))
        
        return pages
    

@api_router.post("/cms/pages", response_model=Page)
async def create_page(
    page_data: PageCreate,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    from backend.models.postgresql_models import Page
    from sqlalchemy import select, update
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Page).where(
                Page.tenant_id == current_user.tenant_id,
                Page.slug == page_data.slug
            )
        )
        existing_page = result.scalar_one_or_none()
        if existing_page:
            raise HTTPException(status_code=400, detail="Page with this slug already exists")
        
        if page_data.is_homepage:
            await session.execute(
                update(Page).where(
                    Page.tenant_id == current_user.tenant_id,
                    Page.is_homepage == True
                ).values(is_homepage=False)
            )
        
        page = Page(**page_data.dict(), tenant_id=current_user.tenant_id)
        session.add(page)
        await session.commit()
        return page

@api_router.get("/cms/pages/{page_id}", response_model=Page)
async def get_page(
    page_id: str,
    current_user: User = Depends(get_current_user)
):
    from backend.models.postgresql_models import Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Page).where(
                Page.id == page_id,
                Page.tenant_id == current_user.tenant_id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page

@api_router.put("/cms/pages/{page_id}", response_model=Page)
async def update_page(
    page_id: str,
    page_data: PageUpdate,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    from backend.models.postgresql_models import Page
    from sqlalchemy import select, update
    from datetime import datetime
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Page).where(
                Page.id == page_id,
                Page.tenant_id == current_user.tenant_id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        update_data = {k: v for k, v in page_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await session.execute(
            update(Page).where(Page.id == page_id).values(**update_data)
        )
        await session.commit()
        
        result = await session.execute(select(Page).where(Page.id == page_id))
        updated_page = result.scalar_one()
        return updated_page

@api_router.delete("/cms/pages/{page_id}")
async def delete_page(
    page_id: str,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    from backend.models.postgresql_models import Page
    from sqlalchemy import select, delete
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Page).where(
                Page.id == page_id,
                Page.tenant_id == current_user.tenant_id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        if page.is_homepage:
            raise HTTPException(status_code=400, detail="Cannot delete homepage")
        
        await session.execute(delete(Page).where(Page.id == page_id))
        await session.commit()
        return {"message": "Page deleted successfully"}

@api_router.get("/cms/templates", response_model=List[Template])
async def get_templates(
    current_user: User = Depends(get_current_user)
):
    from backend.models.postgresql_models import Template, Tenant
    from sqlalchemy import select, or_
    
    async with connection_manager.get_session() as session:
        tenant_result = await session.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
        tenant = tenant_result.scalar_one()
        
        result = await session.execute(
            select(Template).where(
                or_(
                    Template.industry_module == tenant.industry_module,
                    Template.industry_module == None
                )
            )
        )
        templates = result.scalars().all()
        return templates

# Form Builder Routes
@api_router.get("/forms", response_model=List[Form])
async def get_forms(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER, UserRole.FRONT_DESK]))
):
    from backend.models.postgresql_models import Form
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(select(Form).where(Form.tenant_id == current_user.tenant_id))
        forms = result.scalars().all()
        return forms

@api_router.post("/forms", response_model=Form)
async def create_form(
    form_data: FormCreate,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    from backend.models.postgresql_models import Form
    
    async with connection_manager.get_session() as session:
        form = Form(**form_data.dict(), tenant_id=current_user.tenant_id)
        session.add(form)
        await session.commit()
        return form

@api_router.post("/forms/{form_id}/submit")
async def submit_form(
    form_id: str,
    submission: FormSubmission,
    request: Request
):
    # Get form by ID
    from backend.models.postgresql_models import Form
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(select(Form).where(Form.id == form_id, Form.is_active == True))
        form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Validate required fields
    form_obj = Form(**form)
    for field in form_obj.fields:
        if field.is_required and field.label.lower() not in [k.lower() for k in submission.data.keys()]:
            raise HTTPException(status_code=400, detail=f"Required field '{field.label}' is missing")
    
    # Create lead from form submission
    lead_data = {
        "tenant_id": form["tenant_id"],
        "first_name": submission.data.get("first_name", submission.data.get("name", "Unknown")),
        "last_name": submission.data.get("last_name", ""),
        "email": submission.data.get("email", ""),
        "phone": submission.data.get("phone"),
        "company": submission.data.get("company"),
        "source": form["name"],
        "notes": submission.data.get("message", submission.data.get("notes")),
        "custom_fields": {k: v for k, v in submission.data.items() 
                         if k not in ["first_name", "last_name", "email", "phone", "company", "message", "notes"]}
    }
    
    # Check if lead already exists
    from backend.models.postgresql_models import Lead
    
    existing_lead_result = await session.execute(
        select(Lead).where(
            Lead.tenant_id == form.tenant_id,
            Lead.email == lead_data.get("email")
        )
    )
    existing_lead = existing_lead_result.scalar_one_or_none()
    
    if existing_lead:
        # Update existing lead
        from sqlalchemy import update
        await session.execute(
            update(Lead).where(Lead.id == existing_lead.id).values(
                updated_at=datetime.utcnow(),
                custom_fields={**(existing_lead.custom_fields or {}), **lead_data["custom_fields"]}
            )
        )
        lead_id = existing_lead.id
    else:
        # Create new lead
        lead_obj = Lead(**lead_data)
        session.add(lead_obj)
        lead_id = lead_obj.id
    
    # Store form submission
    from backend.models.postgresql_models import FormSubmission
    submission_obj = FormSubmission(
        id=str(uuid.uuid4()),
        form_id=form_id,
        lead_id=lead_id,
        data=submission.data,
        source_url=submission.source_url,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        created_at=datetime.utcnow()
    )
    session.add(submission_obj)
    await session.commit()
    
    # TODO: Send notification emails to form.email_notifications
    
    return {"message": "Form submitted successfully", "lead_id": lead_id}

# Lead Management Routes
@api_router.get("/leads", response_model=List[Lead])
@cache_response(ttl=300, tags=["leads"])  # Cache for 5 minutes
@monitor_performance("api_response")
async def get_leads(
    status: Optional[LeadStatus] = None,
    assigned_to: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER, UserRole.FRONT_DESK]))
):
    from backend.models.postgresql_models import Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        db_optimizer = await get_db_optimizer(session)
        
        query_conditions = [Page.tenant_id == current_user.tenant_id]
        if status:
            query_conditions.append(Page.status == status)
        
        result = await session.execute(
            select(Page).where(*query_conditions).offset(skip).limit(limit)
        )
        pages = result.scalars().all()
        
        await db_optimizer.log_query_performance("pages", "find", len(pages))
        
        return pages

@api_router.post("/leads", response_model=Lead)
async def create_lead(
    lead_data: LeadCreate,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER, UserRole.FRONT_DESK]))
):
    from backend.models.postgresql_models import Lead
    
    async with connection_manager.get_session() as session:
        lead = Lead(**lead_data.dict(), tenant_id=current_user.tenant_id)
        session.add(lead)
        await session.commit()
        return lead

@api_router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER, UserRole.FRONT_DESK]))
):
    from backend.models.postgresql_models import Lead
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.tenant_id == current_user.tenant_id
            )
        )
        lead = result.scalar_one_or_none()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead

@api_router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER, UserRole.FRONT_DESK]))
):
    from backend.models.postgresql_models import Lead
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.tenant_id == current_user.tenant_id
            )
        )
        lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = {k: v for k, v in lead_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Handle status changes
    if "status" in update_data:
        if update_data["status"] == LeadStatus.CONVERTED:
            update_data["converted_at"] = datetime.utcnow()
        elif update_data["status"] == LeadStatus.TOUR_COMPLETED:
            update_data["tour_completed_at"] = datetime.utcnow()
    
        from sqlalchemy import update
        
        await session.execute(
            update(Lead).where(Lead.id == lead_id).values(**update_data)
        )
        await session.commit()
        
        result = await session.execute(select(Lead).where(Lead.id == lead_id))
        updated_lead = result.scalar_one()
    return Lead(**updated_lead)

# Tour Management Routes
@api_router.get("/tours/slots", response_model=List[TourSlot])
async def get_tour_slots(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {"tenant_id": current_user.tenant_id}
    
    if date_from:
        query["date"] = {"$gte": datetime.fromisoformat(date_from)}
    if date_to:
        if "date" in query:
            query["date"].update({"$lte": datetime.fromisoformat(date_to)})
        else:
            query["date"] = {"$lte": datetime.fromisoformat(date_to)}
    
    from backend.models.postgresql_models import TourSlot
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        query_conditions = [TourSlot.tenant_id == current_user.tenant_id]
        if date_from:
            query_conditions.append(TourSlot.date >= datetime.fromisoformat(date_from))
        if date_to:
            query_conditions.append(TourSlot.date <= datetime.fromisoformat(date_to))
        
        result = await session.execute(
            select(TourSlot).where(*query_conditions).order_by(TourSlot.date)
        )
        slots = result.scalars().all()
        return slots

@api_router.post("/tours/slots", response_model=TourSlot)
async def create_tour_slot(
    slot_data: TourSlotCreate,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    from backend.models.postgresql_models import TourSlot
    
    async with connection_manager.get_session() as session:
        slot = TourSlot(**slot_data.dict(), tenant_id=current_user.tenant_id)
        session.add(slot)
        await session.commit()
        return slot

@api_router.post("/tours/book")
async def book_tour(tour_data: TourBooking):
    from backend.models.postgresql_models import TourSlot, Tour, Lead
    from sqlalchemy import select, update
    import uuid
    from datetime import datetime
    
    async with connection_manager.get_session() as session:
        # Get tour slot
        result = await session.execute(
            select(TourSlot).where(
                TourSlot.id == tour_data.tour_slot_id,
                TourSlot.is_available == True
            )
        )
        slot = result.scalar_one_or_none()
        if not slot:
            raise HTTPException(status_code=404, detail="Tour slot not available")
        
        # Check if slot is already booked
        existing_tours_result = await session.execute(
            select(Tour).where(
                Tour.tour_slot_id == tour_data.tour_slot_id,
                Tour.status != "cancelled"
            )
        )
        existing_tours = existing_tours_result.scalars().all()
        
        if len(existing_tours) >= slot.max_bookings:
            raise HTTPException(status_code=400, detail="Tour slot is fully booked")
        
        # Create or find lead
        lead_id = tour_data.lead_id
        if not lead_id:
            # Create new lead from tour booking
            lead = Lead(
                tenant_id=slot.tenant_id,
                first_name=tour_data.first_name,
                last_name=tour_data.last_name,
                email=tour_data.email,
                phone=tour_data.phone,
                company=tour_data.company,
                status=LeadStatus.TOUR_SCHEDULED,
                source="tour_booking",
                notes=tour_data.notes,
                tour_scheduled_at=slot.date
            )
            session.add(lead)
            await session.flush()
            lead_id = lead.id
        else:
            # Update existing lead
            await session.execute(
                update(Lead).where(Lead.id == lead_id).values(
                    status=LeadStatus.TOUR_SCHEDULED,
                    tour_scheduled_at=slot.date,
                    updated_at=datetime.utcnow()
                )
            )
        
        # Create tour booking
        tour = Tour(
            tenant_id=slot.tenant_id,
            lead_id=lead_id,
            tour_slot_id=tour_data.tour_slot_id,
            scheduled_at=slot.date,
            staff_user_id=slot.staff_user_id
        )
        session.add(tour)
        await session.commit()
        
        return {"message": "Tour booked successfully", "tour_id": tour.id, "lead_id": lead_id}

@api_router.get("/tours", response_model=List[Tour])
async def get_tours(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER, UserRole.FRONT_DESK]))
):
    from backend.models.postgresql_models import Tour
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        result = await session.execute(
            select(Tour).where(Tour.tenant_id == current_user.tenant_id).order_by(Tour.scheduled_at)
        )
        tours = result.scalars().all()
        return tours

# Dashboard and Analytics
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    this_month = today.replace(day=1)
    
    from backend.models.postgresql_models import Lead, Page, Form, Tour
    from sqlalchemy import select, func
    
    async with connection_manager.get_session() as session:
        # Get stats
        total_leads_result = await session.execute(select(func.count(Lead.id)).where(Lead.tenant_id == current_user.tenant_id))
        total_leads = total_leads_result.scalar()
        
        new_leads_this_month_result = await session.execute(
            select(func.count(Lead.id)).where(
                Lead.tenant_id == current_user.tenant_id,
                Lead.created_at >= this_month
            )
        )
        new_leads_this_month = new_leads_this_month_result.scalar()
        
        total_pages_result = await session.execute(
            select(func.count(Page.id)).where(
                Page.tenant_id == current_user.tenant_id,
                Page.status == PageStatus.PUBLISHED
            )
        )
        total_pages = total_pages_result.scalar()
        
        total_forms_result = await session.execute(
            select(func.count(Form.id)).where(
                Form.tenant_id == current_user.tenant_id,
                Form.is_active == True
            )
        )
        total_forms = total_forms_result.scalar()
        
        upcoming_tours_result = await session.execute(
            select(func.count(Tour.id)).where(
                Tour.tenant_id == current_user.tenant_id,
                Tour.scheduled_at >= datetime.utcnow(),
                Tour.status == "scheduled"
            )
        )
        upcoming_tours = upcoming_tours_result.scalar()
        
        # Recent leads
        recent_leads_result = await session.execute(
            select(Lead).where(Lead.tenant_id == current_user.tenant_id)
            .order_by(Lead.created_at.desc())
            .limit(5)
        )
        recent_leads = recent_leads_result.scalars().all()
        
        # Conversion stats
        converted_leads_result = await session.execute(
            select(func.count(Lead.id)).where(
                Lead.tenant_id == current_user.tenant_id,
                Lead.status == LeadStatus.CONVERTED,
                Lead.created_at >= this_month
            )
        )
        converted_leads = converted_leads_result.scalar()
        
        conversion_rate = (converted_leads / new_leads_this_month * 100) if new_leads_this_month > 0 else 0
    
    return {
        "total_leads": total_leads,
        "new_leads_this_month": new_leads_this_month,
        "total_pages": total_pages,
        "total_forms": total_forms,
        "upcoming_tours": upcoming_tours,
        "conversion_rate": round(conversion_rate, 1),
        "recent_leads": [
            {
                "id": lead.id,
                "name": f"{lead.first_name} {lead.last_name}",
                "email": lead.email,
                "status": lead.status,
                "source": lead.source,
                "created_at": lead.created_at.isoformat()
            }
            for lead in recent_leads
        ]
    }

# Public API routes (no auth required)
@api_router.get("/public/{tenant_subdomain}/pages/{slug}")
async def get_public_page(tenant_subdomain: str, slug: str):
    from backend.models.postgresql_models import Tenant, Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        # Find tenant
        tenant_result = await session.execute(select(Tenant).where(Tenant.subdomain == tenant_subdomain))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get page
        page_result = await session.execute(
            select(Page).where(
                Page.tenant_id == tenant.id,
                Page.slug == slug,
                Page.status == PageStatus.PUBLISHED
            )
        )
        page = page_result.scalar_one_or_none()
        
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        return {
            "page": page,
            "tenant": {
                "name": tenant.name,
                "branding": tenant.branding or {},
                "industry_module": tenant.industry_module
            }
        }

@api_router.get("/public/{tenant_subdomain}/forms/{form_id}")
async def get_public_form(tenant_subdomain: str, form_id: str):
    from backend.models.postgresql_models import Tenant, Form
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        # Find tenant
        tenant_result = await session.execute(select(Tenant).where(Tenant.subdomain == tenant_subdomain))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get form
        form_result = await session.execute(
            select(Form).where(
                Form.id == form_id,
                Form.tenant_id == tenant.id,
                Form.is_active == True
            )
        )
        form = form_result.scalar_one_or_none()
        
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        return form

# Add new core platform endpoints BEFORE including router
@api_router.get("/platform/experience")
async def get_tenant_experience(current_user: User = Depends(get_current_user)):
    """Get complete tenant experience configuration"""
    core = await get_platform_core(db)
    experience = await core.get_tenant_experience(current_user.tenant_id)
    return experience

@api_router.get("/platform/health")
async def get_platform_health():
    """Get platform health status"""
    core = await get_platform_core(db)
    health = await core.get_platform_health()
    return health

@api_router.get("/dashboard/enhanced", response_model=Dict[str, Any])
async def get_enhanced_dashboard(current_user: User = Depends(get_current_user)):
    """Get enhanced dashboard with module-specific data"""
    core = await get_platform_core(db)
    dashboard_data = await core.get_dashboard_data(current_user.tenant_id, current_user.id)
    return dashboard_data

@api_router.post("/platform/reload-module")
async def reload_tenant_module(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR]))
):
    """Reload module configuration for tenant"""
    core = await get_platform_core(db)
    await core.reload_tenant_module(current_user.tenant_id)
    return {"message": "Module reloaded successfully"}

# Enhanced CMS System Routes
@api_router.get("/cms/coworking/blocks")
async def get_coworking_blocks(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    """Get available content blocks for coworking spaces"""
    cms_engine = CoworkingCMSEngine(db)
    blocks = cms_engine.get_coworking_content_blocks()
    return {"blocks": blocks}

@api_router.get("/cms/coworking/themes")
async def get_coworking_themes(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    """Get available themes for coworking spaces"""
    cms_engine = CoworkingCMSEngine(db)
    themes = cms_engine.get_coworking_themes()
    return {"themes": themes}

@api_router.get("/cms/coworking/page-templates")
async def get_coworking_page_templates(
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    """Get page templates for coworking spaces"""
    cms_engine = CoworkingCMSEngine(db)
    templates = cms_engine.get_coworking_page_templates()
    return {"templates": templates}

@api_router.post("/cms/pages/{page_id}/builder")
async def save_page_builder_data(
    page_id: str,
    blocks_data: Dict[str, Any],
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    """Save page builder configuration"""
    cms_engine = CoworkingCMSEngine(connection_manager)
    
    # Validate page exists and belongs to tenant
    from backend.models.postgresql_models import Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        page_result = await session.execute(
            select(Page).where(
                Page.id == page_id,
                Page.tenant_id == current_user.tenant_id
            )
        )
        page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    success = await cms_engine.save_page_builder_data(
        current_user.tenant_id, 
        page_id, 
        blocks_data.get("blocks", [])
    )
    
    if success:
        return {"message": "Page builder data saved successfully", "page_id": page_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to save page builder data")

@api_router.get("/cms/pages/{page_id}/builder")
async def get_page_builder_data(
    page_id: str,
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    """Get page builder configuration"""
    cms_engine = CoworkingCMSEngine(connection_manager)
    
    # Validate page exists and belongs to tenant
    from backend.models.postgresql_models import Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        page_result = await session.execute(
            select(Page).where(
                Page.id == page_id,
                Page.tenant_id == current_user.tenant_id
            )
        )
        page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    builder_data = await cms_engine.get_page_builder_data(current_user.tenant_id, page_id)
    
    if builder_data:
        return {
            "page_id": page_id,
            "blocks": builder_data.get("blocks", []),
            "updated_at": builder_data.get("updated_at")
        }
    else:
        return {
            "page_id": page_id,
            "blocks": [],
            "updated_at": None
        }

@api_router.post("/cms/pages/{page_id}/render")
async def render_page_with_blocks(
    page_id: str,
    render_data: Dict[str, Any],
    current_user: User = Depends(require_role([UserRole.ACCOUNT_OWNER, UserRole.ADMINISTRATOR, UserRole.PROPERTY_MANAGER]))
):
    """Render page with content blocks"""
    cms_engine = CoworkingCMSEngine(connection_manager)
    
    # Validate page exists and belongs to tenant
    from backend.models.postgresql_models import Page
    from sqlalchemy import select
    
    async with connection_manager.get_session() as session:
        page_result = await session.execute(
            select(Page).where(
                Page.id == page_id,
                Page.tenant_id == current_user.tenant_id
            )
        )
        page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get page builder data
    builder_data = await cms_engine.get_page_builder_data(current_user.tenant_id, page_id)
    
    if not builder_data:
        raise HTTPException(status_code=404, detail="No page builder data found")
    
    # Render blocks
    rendered_blocks = []
    theme_config = render_data.get("theme_config", {})
    
    for block in builder_data.get("blocks", []):
        try:
            rendered_block = await cms_engine.render_content_block(
                current_user.tenant_id,
                block.get("type"),
                block.get("config", {}),
                theme_config
            )
            rendered_blocks.append(rendered_block)
        except Exception as e:
            # Log error but continue with other blocks
            print(f"Error rendering block {block.get('type')}: {str(e)}")
            continue
    
    return {
        "page_id": page_id,
        "rendered_blocks": rendered_blocks,
        "theme_config": theme_config
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global repositories
tenant_repo = None

# Add platform initialization
@app.on_event("startup")
async def startup_event():
    """Initialize the Claude Platform on startup"""
    global platform_core, tenant_repo
    
    # Initialize tenant repository
    tenant_repo = TenantRepository(db)
    await tenant_repo.initialize()
    app.state.tenant_repo = tenant_repo
    
    # Add tenant middleware
    app.add_middleware(TenantMiddleware, tenant_repo=tenant_repo)
    
    # Initialize platform core
    platform_core = await initialize_platform(db)
    print("🚀 Claude Platform Core initialized successfully!")
    
    # Include API routers
    app.include_router(tenant_router)
    app.include_router(lead_router)
    app.include_router(financial_router)
    app.include_router(communication_router)
    app.include_router(health_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
# Performance Monitoring Routes
@api_router.get("/performance/metrics")
async def get_performance_metrics(
    hours: int = 1,
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN, UserRole.ACCOUNT_OWNER]))
):
    """Get performance metrics summary"""
    monitor = await get_performance_monitor()
    return await monitor.get_metrics_summary(hours)

@api_router.get("/performance/alerts")
async def get_performance_alerts(
    hours: int = 24,
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN, UserRole.ACCOUNT_OWNER]))
):
    """Get performance alerts"""
    monitor = await get_performance_monitor()
    return await monitor.get_alerts(hours)

@api_router.get("/performance/slow-queries")
async def get_slow_queries(
    limit: int = 10,
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN, UserRole.ACCOUNT_OWNER]))
):
    """Get slowest database queries"""
    monitor = await get_performance_monitor()
    return await monitor.get_slow_queries(limit)

@api_router.get("/performance/tenant/{tenant_id}")
async def get_tenant_performance(
    tenant_id: str,
    hours: int = 1,
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN, UserRole.ACCOUNT_OWNER]))
):
    """Get performance metrics for specific tenant"""
    # Ensure user can only access their own tenant data (unless platform admin)
    if current_user.role != UserRole.PLATFORM_ADMIN and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    monitor = await get_performance_monitor()
    return await monitor.get_tenant_performance(tenant_id, hours)

@api_router.get("/performance/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN, UserRole.ACCOUNT_OWNER]))
):
    """Get cache performance statistics"""
    cache_manager = await get_cache_manager()
    return await cache_manager.get_stats()

@api_router.post("/performance/cache/invalidate")
async def invalidate_cache(
    pattern: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN, UserRole.ACCOUNT_OWNER]))
):
    """Invalidate cache entries"""
    cache_manager = await get_cache_manager()
    
    # Restrict tenant users to their own data
    if current_user.role != UserRole.PLATFORM_ADMIN:
        if tags:
            tags = [tag for tag in tags if tag.startswith(f"tenant:{current_user.tenant_id}")]
        else:
            tags = [f"tenant:{current_user.tenant_id}"]
    
    invalidated_count = await cache_manager.invalidate(pattern=pattern, tags=tags)
    return {"invalidated_count": invalidated_count}

@api_router.get("/performance/database/stats")
async def get_database_stats(
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN]))
):
    """Get database performance statistics"""
    async with connection_manager.get_session() as session:
        db_optimizer = await get_db_optimizer(session)
        return await db_optimizer.get_performance_metrics()

@api_router.post("/performance/database/analyze/{collection}")
async def analyze_collection_performance(
    collection: str,
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN]))
):
    """Analyze performance of a specific collection"""
    async with connection_manager.get_session() as session:
        db_optimizer = await get_db_optimizer(session)
        return await db_optimizer.analyze_collection_performance(collection)

@api_router.post("/performance/database/cleanup")
async def cleanup_old_data(
    current_user: User = Depends(require_role([UserRole.PLATFORM_ADMIN]))
):
    """Clean up old data to maintain performance"""
    async with connection_manager.get_session() as session:
        db_optimizer = await get_db_optimizer(session)
        return await db_optimizer.cleanup_old_data()

# Health check endpoint with performance metrics
@api_router.get("/health")
async def health_check():
    """Enhanced health check with performance metrics"""
    try:
        # Check database connection
        from database.config.connection_pool import PostgreSQLConnectionManager
        connection_manager = PostgreSQLConnectionManager()
        health_result = await connection_manager.health_check()
        if health_result["status"] != "healthy":
            raise Exception(f"Database unhealthy: {health_result.get('error', 'Unknown error')}")
        
        # Get basic performance metrics
        monitor = await get_performance_monitor()
        cache_manager = await get_cache_manager()
        
        metrics_summary = await monitor.get_metrics_summary(hours=1)
        cache_stats = await cache_manager.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "performance": {
                "avg_response_time": metrics_summary.get("metrics", {}).get("response_time", {}).get("avg", 0),
                "cache_hit_rate": cache_stats.get("hit_rate", 0),
                "total_requests": metrics_summary.get("total_metrics", 0)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Initialize performance monitoring on startup
@app.on_event("startup")
async def startup_event():
    """Initialize performance monitoring and optimizations"""
    try:
        # Initialize database optimizer
        async with connection_manager.get_session() as session:
            db_optimizer = await get_db_optimizer(session)
            logger.info("✅ Database optimizer initialized")
        
        # Start performance monitoring
        monitor = await get_performance_monitor()
        await monitor.start_monitoring()
        logger.info("✅ Performance monitoring started")
        
        # Initialize platform core
        await initialize_platform(db)
        logger.info("✅ Platform core initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize performance systems: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        monitor = await get_performance_monitor()
        await monitor.stop_monitoring()
        logger.info("✅ Performance monitoring stopped")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
