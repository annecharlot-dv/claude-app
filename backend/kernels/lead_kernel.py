"""
Lead Management Kernel
Handles lead capture, processing, scoring, and tour scheduling
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from kernels.base_kernel import BaseKernel
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import uuid


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    TOUR_SCHEDULED = "tour_scheduled"
    TOUR_COMPLETED = "tour_completed"
    PROPOSAL_SENT = "proposal_sent"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, Enum):
    WEBSITE_FORM = "website_form"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    WALK_IN = "walk_in"
    EVENT = "event"
    ADVERTISING = "advertising"


class FormFieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    NUMBER = "number"
    FILE = "file"


class LeadModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    source: LeadSource = LeadSource.WEBSITE_FORM
    score: int = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    assigned_to: Optional[str] = None  # User ID
    tags: List[str] = Field(default_factory=list)
    
    # Tour information
    tour_scheduled_at: Optional[datetime] = None
    tour_completed_at: Optional[datetime] = None
    tour_notes: Optional[str] = None
    
    # Conversion tracking
    converted_at: Optional[datetime] = None
    conversion_value: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_contacted_at: Optional[datetime] = None


class FormFieldModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    type: FormFieldType
    is_required: bool = False
    options: List[str] = Field(default_factory=list)
    placeholder: Optional[str] = None
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    order: int = 0


class FormModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    title: str
    description: Optional[str] = None
    fields: List[FormFieldModel] = Field(default_factory=list)
    success_message: str = "Thank you for your submission!"
    redirect_url: Optional[str] = None
    email_notifications: List[str] = Field(default_factory=list)
    auto_assign_to: Optional[str] = None  # User ID
    lead_source: LeadSource = LeadSource.WEBSITE_FORM
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TourSlotModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    staff_user_id: str
    date: datetime
    duration_minutes: int = 30
    max_bookings: int = 1
    current_bookings: int = 0
    is_available: bool = True
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LeadKernel(BaseKernel):
    """Universal lead management and tour scheduling"""
    
    def __init__(self, db):
        super().__init__(db)
        self.leads_collection = db.leads
        self.forms_collection = db.forms
        self.tour_slots_collection = db.tour_slots
        self.lead_activities_collection = db.lead_activities
    
    async def _initialize_kernel(self):
        """Initialize lead kernel with indexes"""
        # Lead indexes
        await self.leads_collection.create_index([("tenant_id", 1), ("email", 1)], unique=True)
        await self.leads_collection.create_index([("tenant_id", 1), ("status", 1)])
        await self.leads_collection.create_index([("tenant_id", 1), ("assigned_to", 1)])
        await self.leads_collection.create_index([("tenant_id", 1), ("created_at", -1)])
        await self.leads_collection.create_index([("tenant_id", 1), ("score", -1)])
        
        # Form indexes
        await self.forms_collection.create_index([("tenant_id", 1), ("name", 1)], unique=True)
        await self.forms_collection.create_index([("tenant_id", 1), ("is_active", 1)])
        
        # Tour slot indexes
        await self.tour_slots_collection.create_index([("tenant_id", 1), ("date", 1)])
        await self.tour_slots_collection.create_index([("tenant_id", 1), ("staff_user_id", 1)])
        await self.tour_slots_collection.create_index([("tenant_id", 1), ("is_available", 1)])
    
    # Lead Management
    async def create_lead(self, tenant_id: str, lead_data: Dict[str, Any]) -> LeadModel:
        """Create a new lead"""
        lead = LeadModel(tenant_id=tenant_id, **lead_data)
        
        # Calculate initial lead score
        lead.score = await self._calculate_lead_score(lead)
        
        # Insert lead
        await self.leads_collection.insert_one(lead.dict())
        
        # Log activity
        await self._log_lead_activity(
            tenant_id, lead.id, "lead_created", 
            {"source": lead.source, "score": lead.score}
        )
        
        return lead
    
    async def update_lead(self, tenant_id: str, lead_id: str, updates: Dict[str, Any]) -> bool:
        """Update lead information"""
        updates["updated_at"] = datetime.utcnow()
        
        # Recalculate score if relevant fields changed
        if any(field in updates for field in ["company", "phone", "custom_fields"]):
            lead = await self.get_lead_by_id(tenant_id, lead_id)
            if lead:
                for key, value in updates.items():
                    setattr(lead, key, value)
                updates["score"] = await self._calculate_lead_score(lead)
        
        result = await self.leads_collection.update_one(
            {"tenant_id": tenant_id, "id": lead_id},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            await self._log_lead_activity(
                tenant_id, lead_id, "lead_updated", updates
            )
        
        return result.modified_count > 0
    
    async def get_lead_by_id(self, tenant_id: str, lead_id: str) -> Optional[LeadModel]:
        """Get lead by ID"""
        doc = await self.leads_collection.find_one({
            "tenant_id": tenant_id,
            "id": lead_id
        })
        return LeadModel(**doc) if doc else None
    
    async def list_leads(
        self,
        tenant_id: str,
        status: Optional[LeadStatus] = None,
        assigned_to: Optional[str] = None,
        source: Optional[LeadSource] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LeadModel]:
        """List leads with filtering"""
        query = {"tenant_id": tenant_id}
        
        if status:
            query["status"] = status
        if assigned_to:
            query["assigned_to"] = assigned_to
        if source:
            query["source"] = source
        
        cursor = self.leads_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        return [LeadModel(**doc) for doc in docs]
    
    async def assign_lead(self, tenant_id: str, lead_id: str, user_id: str) -> bool:
        """Assign lead to a user"""
        result = await self.leads_collection.update_one(
            {"tenant_id": tenant_id, "id": lead_id},
            {"$set": {"assigned_to": user_id, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            await self._log_lead_activity(
                tenant_id, lead_id, "lead_assigned", {"assigned_to": user_id}
            )
        
        return result.modified_count > 0
    
    # Lead Scoring
    async def _calculate_lead_score(self, lead: LeadModel) -> int:
        """Calculate lead score based on various factors"""
        score = 0
        
        # Base score for having contact info
        if lead.email:
            score += 20
        if lead.phone:
            score += 15
        
        # Company information adds value
        if lead.company:
            score += 25
        
        # Source-based scoring
        source_scores = {
            LeadSource.REFERRAL: 30,
            LeadSource.WEBSITE_FORM: 20,
            LeadSource.PHONE_CALL: 25,
            LeadSource.EMAIL: 15,
            LeadSource.WALK_IN: 35,
            LeadSource.EVENT: 20,
            LeadSource.SOCIAL_MEDIA: 10,
            LeadSource.ADVERTISING: 15
        }
        score += source_scores.get(lead.source, 10)
        
        # Custom field scoring (industry-specific)
        custom_score = await self._calculate_custom_field_score(lead.custom_fields)
        score += custom_score
        
        return min(score, 100)  # Cap at 100
    
    async def _calculate_custom_field_score(self, custom_fields: Dict[str, Any]) -> int:
        """Calculate score from custom fields"""
        score = 0
        
        # Budget information
        if "budget" in custom_fields:
            budget = custom_fields.get("budget", "")
            if "high" in str(budget).lower() or "premium" in str(budget).lower():
                score += 20
            elif "medium" in str(budget).lower():
                score += 10
        
        # Urgency
        if "urgency" in custom_fields:
            urgency = custom_fields.get("urgency", "")
            if "immediate" in str(urgency).lower() or "asap" in str(urgency).lower():
                score += 15
        
        # Team size (for coworking)
        if "team_size" in custom_fields:
            try:
                team_size = int(custom_fields.get("team_size", 0))
                if team_size > 10:
                    score += 15
                elif team_size > 5:
                    score += 10
                elif team_size > 1:
                    score += 5
            except (ValueError, TypeError):
                pass
        
        return score
    
    # Form Management
    async def create_form(self, tenant_id: str, form_data: Dict[str, Any]) -> FormModel:
        """Create a new lead capture form"""
        form = FormModel(tenant_id=tenant_id, **form_data)
        await self.forms_collection.insert_one(form.dict())
        return form
    
    async def get_form_by_id(self, tenant_id: str, form_id: str) -> Optional[FormModel]:
        """Get form by ID"""
        doc = await self.forms_collection.find_one({
            "tenant_id": tenant_id,
            "id": form_id
        })
        return FormModel(**doc) if doc else None
    
    async def list_forms(self, tenant_id: str, active_only: bool = True) -> List[FormModel]:
        """List forms for tenant"""
        query = {"tenant_id": tenant_id}
        if active_only:
            query["is_active"] = True
        
        cursor = self.forms_collection.find(query).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        
        return [FormModel(**doc) for doc in docs]
    
    async def submit_form(self, tenant_id: str, form_id: str, submission_data: Dict[str, Any]) -> LeadModel:
        """Process form submission and create lead"""
        form = await self.get_form_by_id(tenant_id, form_id)
        if not form or not form.is_active:
            raise ValueError("Form not found or inactive")
        
        # Extract lead data from submission
        lead_data = {
            "first_name": submission_data.get("first_name", ""),
            "last_name": submission_data.get("last_name", ""),
            "email": submission_data.get("email", ""),
            "phone": submission_data.get("phone"),
            "company": submission_data.get("company"),
            "source": form.lead_source,
            "custom_fields": {k: v for k, v in submission_data.items() 
                            if k not in ["first_name", "last_name", "email", "phone", "company"]},
            "assigned_to": form.auto_assign_to
        }
        
        # Create lead
        lead = await self.create_lead(tenant_id, lead_data)
        
        # Send notifications if configured
        if form.email_notifications:
            await self._send_form_notifications(form, lead, submission_data)
        
        return lead
    
    # Tour Scheduling
    async def create_tour_slots(
        self,
        tenant_id: str,
        staff_user_id: str,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30,
        slots_per_day: int = 8
    ) -> List[TourSlotModel]:
        """Create tour slots for a date range"""
        slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Create slots for each day (9 AM to 5 PM by default)
            for hour in range(9, 17):
                if len(slots) >= slots_per_day:
                    break
                
                slot_datetime = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                
                slot = TourSlotModel(
                    tenant_id=tenant_id,
                    staff_user_id=staff_user_id,
                    date=slot_datetime,
                    duration_minutes=duration_minutes
                )
                
                await self.tour_slots_collection.insert_one(slot.dict())
                slots.append(slot)
            
            current_date += timedelta(days=1)
        
        return slots
    
    async def get_available_tour_slots(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        staff_user_id: Optional[str] = None
    ) -> List[TourSlotModel]:
        """Get available tour slots"""
        query = {
            "tenant_id": tenant_id,
            "date": {"$gte": start_date, "$lte": end_date},
            "is_available": True,
            "$expr": {"$lt": ["$current_bookings", "$max_bookings"]}
        }
        
        if staff_user_id:
            query["staff_user_id"] = staff_user_id
        
        cursor = self.tour_slots_collection.find(query).sort("date", 1)
        docs = await cursor.to_list(length=None)
        
        return [TourSlotModel(**doc) for doc in docs]
    
    async def schedule_tour(
        self,
        tenant_id: str,
        lead_id: str,
        tour_slot_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Schedule a tour for a lead"""
        # Check if slot is available
        slot = await self.tour_slots_collection.find_one({
            "tenant_id": tenant_id,
            "id": tour_slot_id,
            "is_available": True,
            "$expr": {"$lt": ["$current_bookings", "$max_bookings"]}
        })
        
        if not slot:
            return False
        
        # Update lead with tour information
        tour_updates = {
            "status": LeadStatus.TOUR_SCHEDULED,
            "tour_scheduled_at": slot["date"],
            "tour_notes": notes,
            "updated_at": datetime.utcnow()
        }
        
        lead_result = await self.leads_collection.update_one(
            {"tenant_id": tenant_id, "id": lead_id},
            {"$set": tour_updates}
        )
        
        if lead_result.modified_count == 0:
            return False
        
        # Update slot booking count
        await self.tour_slots_collection.update_one(
            {"tenant_id": tenant_id, "id": tour_slot_id},
            {"$inc": {"current_bookings": 1}}
        )
        
        # Log activity
        await self._log_lead_activity(
            tenant_id, lead_id, "tour_scheduled",
            {"tour_slot_id": tour_slot_id, "scheduled_at": slot["date"]}
        )
        
        return True
    
    async def complete_tour(
        self,
        tenant_id: str,
        lead_id: str,
        notes: Optional[str] = None,
        outcome: str = "completed"
    ) -> bool:
        """Mark tour as completed"""
        updates = {
            "status": LeadStatus.TOUR_COMPLETED,
            "tour_completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if notes:
            updates["tour_notes"] = notes
        
        result = await self.leads_collection.update_one(
            {"tenant_id": tenant_id, "id": lead_id},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            await self._log_lead_activity(
                tenant_id, lead_id, "tour_completed",
                {"outcome": outcome, "notes": notes}
            )
        
        return result.modified_count > 0
    
    # Analytics and Reporting
    async def get_lead_analytics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get lead analytics for the specified period"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total leads
        total_leads = await self.leads_collection.count_documents({
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_date}
        })
        
        # Leads by status
        status_pipeline = [
            {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_results = await self.leads_collection.aggregate(status_pipeline).to_list(None)
        status_breakdown = {result["_id"]: result["count"] for result in status_results}
        
        # Leads by source
        source_pipeline = [
            {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$source", "count": {"$sum": 1}}}
        ]
        source_results = await self.leads_collection.aggregate(source_pipeline).to_list(None)
        source_breakdown = {result["_id"]: result["count"] for result in source_results}
        
        # Conversion rate
        converted_leads = await self.leads_collection.count_documents({
            "tenant_id": tenant_id,
            "status": LeadStatus.CONVERTED,
            "created_at": {"$gte": start_date}
        })
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Average lead score
        score_pipeline = [
            {"$match": {"tenant_id": tenant_id, "created_at": {"$gte": start_date}}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ]
        score_results = await self.leads_collection.aggregate(score_pipeline).to_list(None)
        avg_score = score_results[0]["avg_score"] if score_results else 0
        
        return {
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": round(conversion_rate, 2),
            "average_score": round(avg_score, 1),
            "status_breakdown": status_breakdown,
            "source_breakdown": source_breakdown,
            "period_days": days
        }
    
    # Helper Methods
    async def _log_lead_activity(
        self,
        tenant_id: str,
        lead_id: str,
        activity_type: str,
        details: Dict[str, Any]
    ):
        """Log lead activity for audit trail"""
        activity = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "activity_type": activity_type,
            "details": details,
            "created_at": datetime.utcnow()
        }
        
        await self.lead_activities_collection.insert_one(activity)
    
    async def _send_form_notifications(
        self,
        form: FormModel,
        lead: LeadModel,
        submission_data: Dict[str, Any]
    ):
        """Send email notifications for form submissions"""
        # This would integrate with the communication kernel
        # For now, just log the notification
        print(f"Sending form notification for lead {lead.id} to {form.email_notifications}")
    
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user access to tenant leads"""
        # This would check if user belongs to tenant
        # For now, return True
        return True
    
    async def get_kernel_health(self) -> Dict[str, Any]:
        """Get kernel health status"""
        try:
            # Test database connectivity
            await self.leads_collection.find_one({"tenant_id": "health_check"})
            
            return {
                "status": "healthy",
                "collections": ["leads", "forms", "tour_slots", "lead_activities"],
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }