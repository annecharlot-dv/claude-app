"""
Tenant Management API
Provides endpoints for tenant provisioning, configuration, and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from models.tenant import (
    TenantModel, TenantRepository, TenantService,
    TenantStatus, SubscriptionPlan, IndustryType,
    TenantSettings, TenantBranding, TenantFeatures
)
from middleware.tenant_middleware import (
    get_tenant_from_request, get_tenant_id_from_request,
    TenantSecurityValidator
)
from kernels.identity_kernel import IdentityKernel

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


# Request/Response Models
class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    subdomain: str = Field(..., min_length=3, max_length=50)
    industry: IndustryType
    billing_email: str
    owner_data: Dict[str, Any]
    branding: Dict[str, Any]


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    subdomain: str
    industry: IndustryType
    status: TenantStatus
    subscription_plan: SubscriptionPlan
    created_at: datetime
    user_count: int
    storage_used_mb: int


class TenantDetailResponse(TenantResponse):
    settings: TenantSettings
    branding: TenantBranding
    features: TenantFeatures
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]


class SubdomainCheckResponse(BaseModel):
    subdomain: str
    available: bool
    suggestions: List[str] = Field(default_factory=list)


# Dependency injection
async def get_tenant_repo(request: Request) -> TenantRepository:
    """Get tenant repository from app state"""
    return request.app.state.tenant_repo


async def get_tenant_service(tenant_repo: TenantRepository = Depends(get_tenant_repo)) -> TenantService:
    """Get tenant service"""
    return TenantService(tenant_repo)


# Platform Admin Endpoints (require platform admin role)
@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Create a new tenant (Platform Admin only)"""
    
    # Validate subdomain
    if not TenantSecurityValidator.validate_subdomain_security(request.subdomain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subdomain format"
        )
    
    # Check subdomain availability
    if not await tenant_service.validate_subdomain_available(request.subdomain):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subdomain already exists"
        )
    
    try:
        # Create tenant
        tenant = await tenant_service.provision_new_tenant(
            name=request.name,
            subdomain=request.subdomain,
            industry=request.industry,
            billing_email=request.billing_email,
            owner_data=request.owner_data,
            branding=request.branding
        )
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            subdomain=tenant.subdomain,
            industry=tenant.industry,
            status=tenant.status,
            subscription_plan=tenant.subscription_plan,
            created_at=tenant.created_at,
            user_count=tenant.user_count,
            storage_used_mb=tenant.storage_used_mb
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    status: Optional[TenantStatus] = None,
    industry: Optional[IndustryType] = None,
    limit: int = Field(default=100, le=1000),
    offset: int = Field(default=0, ge=0),
    tenant_repo: TenantRepository = Depends(get_tenant_repo)
):
    """List all tenants (Platform Admin only)"""
    
    try:
        tenants = await tenant_repo.list_tenants(
            status=status,
            industry=industry,
            limit=limit,
            offset=offset
        )
        
        return [
            TenantResponse(
                id=tenant.id,
                name=tenant.name,
                subdomain=tenant.subdomain,
                industry=tenant.industry,
                status=tenant.status,
                subscription_plan=tenant.subscription_plan,
                created_at=tenant.created_at,
                user_count=tenant.user_count,
                storage_used_mb=tenant.storage_used_mb
            )
            for tenant in tenants
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.get("/check-subdomain/{subdomain}", response_model=SubdomainCheckResponse)
async def check_subdomain_availability(
    subdomain: str,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Check if subdomain is available"""
    
    # Sanitize input
    try:
        subdomain = TenantSecurityValidator.sanitize_tenant_input(subdomain.lower())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Validate format
    if not TenantSecurityValidator.validate_subdomain_security(subdomain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subdomain format"
        )
    
    # Check availability
    available = await tenant_service.validate_subdomain_available(subdomain)
    
    # Generate suggestions if not available
    suggestions = []
    if not available:
        for i in range(1, 6):
            suggestion = f"{subdomain}{i}"
            if await tenant_service.validate_subdomain_available(suggestion):
                suggestions.append(suggestion)
    
    return SubdomainCheckResponse(
        subdomain=subdomain,
        available=available,
        suggestions=suggestions
    )


# Tenant-Specific Endpoints (require tenant context)
@router.get("/current", response_model=TenantDetailResponse)
async def get_current_tenant(
    tenant: TenantModel = Depends(get_tenant_from_request)
):
    """Get current tenant details"""
    
    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        industry=tenant.industry,
        status=tenant.status,
        subscription_plan=tenant.subscription_plan,
        created_at=tenant.created_at,
        user_count=tenant.user_count,
        storage_used_mb=tenant.storage_used_mb,
        settings=tenant.settings,
        branding=tenant.branding,
        features=tenant.features,
        trial_ends_at=tenant.trial_ends_at,
        subscription_ends_at=tenant.subscription_ends_at
    )


@router.put("/current", response_model=TenantDetailResponse)
async def update_current_tenant(
    request: UpdateTenantRequest,
    tenant: TenantModel = Depends(get_tenant_from_request),
    tenant_repo: TenantRepository = Depends(get_tenant_repo)
):
    """Update current tenant configuration"""
    
    # Build update dictionary
    updates = {}
    
    if request.name is not None:
        updates["name"] = request.name
    
    if request.settings is not None:
        # Validate settings
        try:
            settings = TenantSettings(**request.settings)
            updates["settings"] = settings.dict()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid settings: {str(e)}"
            )
    
    if request.branding is not None:
        # Validate branding
        try:
            branding = TenantBranding(**{**tenant.branding.dict(), **request.branding})
            updates["branding"] = branding.dict()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid branding: {str(e)}"
            )
    
    if request.features is not None:
        # Validate features
        try:
            features = TenantFeatures(**{**tenant.features.dict(), **request.features})
            updates["features"] = features.dict()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid features: {str(e)}"
            )
    
    # Update tenant
    try:
        success = await tenant_repo.update_tenant(tenant.id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Get updated tenant
        updated_tenant = await tenant_repo.get_tenant_by_id(tenant.id)
        
        return TenantDetailResponse(
            id=updated_tenant.id,
            name=updated_tenant.name,
            subdomain=updated_tenant.subdomain,
            industry=updated_tenant.industry,
            status=updated_tenant.status,
            subscription_plan=updated_tenant.subscription_plan,
            created_at=updated_tenant.created_at,
            user_count=updated_tenant.user_count,
            storage_used_mb=updated_tenant.storage_used_mb,
            settings=updated_tenant.settings,
            branding=updated_tenant.branding,
            features=updated_tenant.features,
            trial_ends_at=updated_tenant.trial_ends_at,
            subscription_ends_at=updated_tenant.subscription_ends_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


@router.get("/current/stats")
async def get_tenant_stats(
    tenant_id: str = Depends(get_tenant_id_from_request),
    tenant_repo: TenantRepository = Depends(get_tenant_repo)
):
    """Get tenant usage statistics"""
    
    try:
        stats = await tenant_repo.get_tenant_stats(tenant_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant stats: {str(e)}"
        )


@router.post("/current/upgrade")
async def upgrade_subscription(
    new_plan: SubscriptionPlan,
    tenant_id: str = Depends(get_tenant_id_from_request),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Upgrade tenant subscription plan"""
    
    try:
        success = await tenant_service.upgrade_subscription(tenant_id, new_plan)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return {"message": f"Successfully upgraded to {new_plan}", "plan": new_plan}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade subscription: {str(e)}"
        )


@router.get("/current/health")
async def get_tenant_health(
    tenant: TenantModel = Depends(get_tenant_from_request)
):
    """Get tenant health status"""
    
    health_status = {
        "tenant_id": tenant.id,
        "status": tenant.status,
        "subscription_plan": tenant.subscription_plan,
        "trial_ends_at": tenant.trial_ends_at,
        "subscription_ends_at": tenant.subscription_ends_at,
        "health": "healthy" if tenant.status == "active" else "warning"
    }
    
    # Add warnings for trial/subscription expiry
    if tenant.trial_ends_at and tenant.trial_ends_at < datetime.utcnow():
        health_status["warnings"] = ["Trial period has expired"]
        health_status["health"] = "warning"
    
    if tenant.subscription_ends_at and tenant.subscription_ends_at < datetime.utcnow():
        health_status["warnings"] = health_status.get("warnings", []) + ["Subscription has expired"]
        health_status["health"] = "critical"
    
    return health_status