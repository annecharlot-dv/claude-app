"""
Resource & Booking Kernel (The "Scheduler")
Universal scheduling engine for any type of resource
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .base_kernel import BaseKernel


class BookingKernel(BaseKernel):
    """Universal resource booking and scheduling engine"""
    
    async def _initialize_kernel(self):
        """Initialize booking kernel"""
        # Ensure indexes exist
        await self.db.resources.create_index([("tenant_id", 1), ("is_active", 1)])
        await self.db.bookings.create_index([("tenant_id", 1), ("resource_id", 1), ("start_time", 1)])
        await self.db.availability_schedules.create_index([("resource_id", 1), ("day_of_week", 1)])
    
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        user = await self.db.users.find_one({"id": user_id, "tenant_id": tenant_id})
        return user is not None
    
    # Resource Management
    async def create_resource(self, tenant_id: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new bookable resource"""
        resource_doc = {
            **resource_data,
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        await self.db.resources.insert_one(resource_doc)
        return resource_doc
    
    async def get_resources(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get resources for tenant with optional filters"""
        query = {"tenant_id": tenant_id, "is_active": True}
        if filters:
            query.update(filters)
        
        resources = await self.db.resources.find(query).to_list(1000)
        return resources
    
    async def set_resource_availability(self, resource_id: str, availability_schedule: List[Dict[str, Any]]):
        """Set availability schedule for a resource"""
        # Clear existing schedule
        await self.db.availability_schedules.delete_many({"resource_id": resource_id})
        
        # Insert new schedule
        for schedule in availability_schedule:
            schedule_doc = {
                **schedule,
                "resource_id": resource_id,
                "created_at": datetime.utcnow()
            }
            await self.db.availability_schedules.insert_one(schedule_doc)
    
    # Booking Engine
    async def check_availability(self, resource_id: str, start_time: datetime, end_time: datetime) -> bool:
        """Check if resource is available for the given time slot"""
        # Check for existing bookings
        existing_booking = await self.db.bookings.find_one({
            "resource_id": resource_id,
            "status": {"$in": ["confirmed", "pending"]},
            "$or": [
                {
                    "start_time": {"$lt": end_time},
                    "end_time": {"$gt": start_time}
                }
            ]
        })
        
        if existing_booking:
            return False
        
        # Check availability schedule
        day_of_week = start_time.weekday()  # 0=Monday, 6=Sunday
        availability = await self.db.availability_schedules.find_one({
            "resource_id": resource_id,
            "day_of_week": day_of_week,
            "start_time": {"$lte": start_time.time()},
            "end_time": {"$gte": end_time.time()}
        })
        
        return availability is not None
    
    async def create_booking(self, tenant_id: str, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new booking"""
        resource_id = booking_data["resource_id"]
        start_time = booking_data["start_time"]
        end_time = booking_data["end_time"]
        
        # Validate availability
        if not await self.check_availability(resource_id, start_time, end_time):
            raise ValueError("Resource not available for requested time slot")
        
        # Create booking
        booking_doc = {
            **booking_data,
            "tenant_id": tenant_id,
            "status": "confirmed",
            "created_at": datetime.utcnow()
        }
        await self.db.bookings.insert_one(booking_doc)
        return booking_doc
    
    async def get_bookings(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get bookings for tenant with optional filters"""
        query = {"tenant_id": tenant_id}
        if filters:
            query.update(filters)
        
        bookings = await self.db.bookings.find(query).sort("start_time", 1).to_list(1000)
        return bookings
    
    async def update_booking_status(self, booking_id: str, status: str, notes: Optional[str] = None) -> bool:
        """Update booking status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if notes:
            update_data["notes"] = notes
        
        result = await self.db.bookings.update_one(
            {"id": booking_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_resource_utilization(self, tenant_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get resource utilization statistics"""
        # This is a simplified version - real implementation would be more complex
        total_bookings = await self.db.bookings.count_documents({
            "tenant_id": tenant_id,
            "start_time": {"$gte": start_date, "$lte": end_date},
            "status": "confirmed"
        })
        
        total_resources = await self.db.resources.count_documents({
            "tenant_id": tenant_id,
            "is_active": True
        })
        
        return {
            "total_bookings": total_bookings,
            "total_resources": total_resources,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }