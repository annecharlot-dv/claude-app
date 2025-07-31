"""
Lead Management API
Provides endpoints for lead capture, management, and tour scheduling
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta

from kernels.lead_kernel import (
    LeadKernel, LeadModel, FormModel, TourSlotModel,
    LeadStatus, LeadSource, FormFieldType, FormFieldModel
)
from middleware.tenant_middleware import get_tenant_id_from_request

router = APIRouter(prefix="/api/leads", tags=["leads"])


# Request/Response Models
class CreateLeadRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE_FORM
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    assigned_to: Optional[str] = None


class UpdateLeadRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    assigned_to: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    status: LeadStatus
    source: LeadSource
    score: int
    assigned_to: Optional[str]
    tour_scheduled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CreateFormRequest(BaseModel):
    name: str
    title: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]]
    success_message: str = "Thank you for your submission!"
    redirect_url: Optional[str] = None
    email_notifications: List[str] = Field(default_factory=list)
    auto_assign_to: Optional[str] = None
    lead_source: LeadSource = LeadSource.WEBSITE_FORM


class FormResponse(BaseModel):
    id: str
    name: str
    title: str
    description: Optional[str]
    fields: List[Dict[str, Any]]
    success_message: str
    is_active: bool
    created_at: datetime


class FormSubmissionRequest(BaseModel):
    form_data: Dict[str, Any]


class CreateTourSlotsRequest(BaseModel):
    staff_user_id: str
    start_date: datetime
    end_date: datetime
    duration_minutes: int = 30
    slots_per_day: int = 8


class ScheduleTourRequest(BaseModel):
    lead_id: str
    tour_slot_id: str
    notes: Optional[str] = None


class CompleteTourRequest(BaseModel):
    notes: Optional[str] = None
    outcome: str = "completed"


# Dependency injection
async def get_lead_kernel(request: Request) -> LeadKernel:
    """Get lead kernel from app state"""
    return request.app.state.platform_core.get_kernel("lead")


# Lead Management Endpoints
@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    request: CreateLeadRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Create a new lead"""
    try:
        lead = await lead_kernel.create_lead(tenant_id, request.dict())
        
        return LeadResponse(
            id=lead.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            status=lead.status,
            source=lead.source,
            score=lead.score,
            assigned_to=lead.assigned_to,
            tour_scheduled_at=lead.tour_scheduled_at,
            created_at=lead.created_at,
            updated_at=lead.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}"
        )


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    status_filter: Optional[LeadStatus] = None,
    assigned_to: Optional[str] = None,
    source: Optional[LeadSource] = None,
    limit: int = Field(default=100, le=1000),
    offset: int = Field(default=0, ge=0),
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """List leads with filtering"""
    try:
        leads = await lead_kernel.list_leads(
            tenant_id=tenant_id,
            status=status_filter,
            assigned_to=assigned_to,
            source=source,
            limit=limit,
            offset=offset
        )
        
        return [
            LeadResponse(
                id=lead.id,
                first_name=lead.first_name,
                last_name=lead.last_name,
                email=lead.email,
                phone=lead.phone,
                company=lead.company,
                status=lead.status,
                source=lead.source,
                score=lead.score,
                assigned_to=lead.assigned_to,
                tour_scheduled_at=lead.tour_scheduled_at,
                created_at=lead.created_at,
                updated_at=lead.updated_at
            )
            for lead in leads
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list leads: {str(e)}"
        )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Get lead by ID"""
    lead = await lead_kernel.get_lead_by_id(tenant_id, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return LeadResponse(
        id=lead.id,
        first_name=lead.first_name,
        last_name=lead.last_name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        status=lead.status,
        source=lead.source,
        score=lead.score,
        assigned_to=lead.assigned_to,
        tour_scheduled_at=lead.tour_scheduled_at,
        created_at=lead.created_at,
        updated_at=lead.updated_at
    )


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    request: UpdateLeadRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Update lead information"""
    # Filter out None values
    updates = {k: v for k, v in request.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )
    
    success = await lead_kernel.update_lead(tenant_id, lead_id, updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Return updated lead
    updated_lead = await lead_kernel.get_lead_by_id(tenant_id, lead_id)
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found after update"
        )
    
    return LeadResponse(
        id=updated_lead.id,
        first_name=updated_lead.first_name,
        last_name=updated_lead.last_name,
        email=updated_lead.email,
        phone=updated_lead.phone,
        company=updated_lead.company,
        status=updated_lead.status,
        source=updated_lead.source,
        score=updated_lead.score,
        assigned_to=updated_lead.assigned_to,
        tour_scheduled_at=updated_lead.tour_scheduled_at,
        created_at=updated_lead.created_at,
        updated_at=updated_lead.updated_at
    )


@router.post("/{lead_id}/assign")
async def assign_lead(
    lead_id: str,
    user_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Assign lead to a user"""
    success = await lead_kernel.assign_lead(tenant_id, lead_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return {"message": "Lead assigned successfully", "assigned_to": user_id}


# Form Management Endpoints
@router.post("/forms", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    request: CreateFormRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Create a new lead capture form"""
    try:
        form = await lead_kernel.create_form(tenant_id, request.dict())
        
        return FormResponse(
            id=form.id,
            name=form.name,
            title=form.title,
            description=form.description,
            fields=[field.dict() for field in form.fields],
            success_message=form.success_message,
            is_active=form.is_active,
            created_at=form.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create form: {str(e)}"
        )


@router.get("/forms", response_model=List[FormResponse])
async def list_forms(
    active_only: bool = True,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """List lead capture forms"""
    try:
        forms = await lead_kernel.list_forms(tenant_id, active_only)
        
        return [
            FormResponse(
                id=form.id,
                name=form.name,
                title=form.title,
                description=form.description,
                fields=[field.dict() for field in form.fields],
                success_message=form.success_message,
                is_active=form.is_active,
                created_at=form.created_at
            )
            for form in forms
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list forms: {str(e)}"
        )


@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Get form by ID"""
    form = await lead_kernel.get_form_by_id(tenant_id, form_id)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    return FormResponse(
        id=form.id,
        name=form.name,
        title=form.title,
        description=form.description,
        fields=[field.dict() for field in form.fields],
        success_message=form.success_message,
        is_active=form.is_active,
        created_at=form.created_at
    )


@router.post("/forms/{form_id}/submit", response_model=LeadResponse)
async def submit_form(
    form_id: str,
    request: FormSubmissionRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Submit form and create lead"""
    try:
        lead = await lead_kernel.submit_form(tenant_id, form_id, request.form_data)
        
        return LeadResponse(
            id=lead.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            status=lead.status,
            source=lead.source,
            score=lead.score,
            assigned_to=lead.assigned_to,
            tour_scheduled_at=lead.tour_scheduled_at,
            created_at=lead.created_at,
            updated_at=lead.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit form: {str(e)}"
        )


# Tour Scheduling Endpoints
@router.post("/tours/slots", status_code=status.HTTP_201_CREATED)
async def create_tour_slots(
    request: CreateTourSlotsRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Create tour slots for a date range"""
    try:
        slots = await lead_kernel.create_tour_slots(
            tenant_id=tenant_id,
            staff_user_id=request.staff_user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            duration_minutes=request.duration_minutes,
            slots_per_day=request.slots_per_day
        )
        
        return {
            "message": f"Created {len(slots)} tour slots",
            "slots_created": len(slots)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tour slots: {str(e)}"
        )


@router.get("/tours/slots")
async def get_available_tour_slots(
    start_date: datetime,
    end_date: datetime,
    staff_user_id: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Get available tour slots"""
    try:
        slots = await lead_kernel.get_available_tour_slots(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            staff_user_id=staff_user_id
        )
        
        return [
            {
                "id": slot.id,
                "staff_user_id": slot.staff_user_id,
                "date": slot.date,
                "duration_minutes": slot.duration_minutes,
                "available_bookings": slot.max_bookings - slot.current_bookings
            }
            for slot in slots
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tour slots: {str(e)}"
        )


@router.post("/tours/schedule")
async def schedule_tour(
    request: ScheduleTourRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Schedule a tour for a lead"""
    success = await lead_kernel.schedule_tour(
        tenant_id=tenant_id,
        lead_id=request.lead_id,
        tour_slot_id=request.tour_slot_id,
        notes=request.notes
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to schedule tour - slot may be unavailable or lead not found"
        )
    
    return {"message": "Tour scheduled successfully"}


@router.post("/tours/{lead_id}/complete")
async def complete_tour(
    lead_id: str,
    request: CompleteTourRequest,
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Mark tour as completed"""
    success = await lead_kernel.complete_tour(
        tenant_id=tenant_id,
        lead_id=lead_id,
        notes=request.notes,
        outcome=request.outcome
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return {"message": "Tour marked as completed"}


# Analytics Endpoints
@router.get("/analytics")
async def get_lead_analytics(
    days: int = Field(default=30, ge=1, le=365),
    tenant_id: str = Depends(get_tenant_id_from_request),
    lead_kernel: LeadKernel = Depends(get_lead_kernel)
):
    """Get lead analytics for the specified period"""
    try:
        analytics = await lead_kernel.get_lead_analytics(tenant_id, days)
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )
