"""
Resource & Booking Kernel (The "Scheduler")
Universal scheduling engine for any type of resource
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from kernels.base_kernel import BaseKernel
from models.postgresql_models import User, Booking, Resource, AvailabilitySchedule
from sqlalchemy import select, update, delete, func


class BookingKernel(BaseKernel):
    """Universal resource booking and scheduling engine"""
    
    async def _initialize_kernel(self):
        """Initialize booking kernel"""
        pass
    
    async def validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Validate user belongs to tenant"""
        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
            return user is not None
    
    # Resource Management
    async def create_resource(self, tenant_id: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new bookable resource"""
        async with self.connection_manager.get_session() as session:
            resource_data.update({
                "tenant_id": tenant_id,
                "is_active": True,
                "created_at": datetime.utcnow()
            })
            resource_obj = Resource(**resource_data)
            session.add(resource_obj)
            await session.commit()
            return resource_data
    
    async def get_resources(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get resources for tenant with optional filters"""
        async with self.connection_manager.get_session() as session:
            query_conditions = [Resource.tenant_id == tenant_id, Resource.is_active == True]
            
            result = await session.execute(
                select(Resource).where(*query_conditions)
            )
            resources = result.scalars().all()
            return [resource.__dict__ for resource in resources]
    
    async def set_resource_availability(self, resource_id: str, availability_schedule: List[Dict[str, Any]]):
        """Set availability schedule for a resource"""
        async with self.connection_manager.get_session() as session:
            # Clear existing schedule
            await session.execute(delete(AvailabilitySchedule).where(AvailabilitySchedule.resource_id == resource_id))
            
            # Insert new schedule
            for schedule in availability_schedule:
                schedule_data = {
                    **schedule,
                    "resource_id": resource_id,
                    "created_at": datetime.utcnow()
                }
                schedule_obj = AvailabilitySchedule(**schedule_data)
                session.add(schedule_obj)
            
            await session.commit()
    
    # Booking Engine
    async def check_availability(self, resource_id: str, start_time: datetime, end_time: datetime) -> bool:
        """Check if resource is available for the given time slot"""
        async with self.connection_manager.get_session() as session:
            # Check for existing bookings
            result = await session.execute(
                select(Booking).where(
                    Booking.resource_id == resource_id,
                    Booking.status.in_(["confirmed", "pending"]),
                    Booking.start_time < end_time,
                    Booking.end_time > start_time
                )
            )
            existing_booking = result.scalar_one_or_none()
            
            if existing_booking:
                return False
            
            # Check availability schedule
            day_of_week = start_time.weekday()  # 0=Monday, 6=Sunday
            result = await session.execute(
                select(AvailabilitySchedule).where(
                    AvailabilitySchedule.resource_id == resource_id,
                    AvailabilitySchedule.day_of_week == day_of_week,
                    AvailabilitySchedule.start_time <= start_time.time(),
                    AvailabilitySchedule.end_time >= end_time.time()
                )
            )
            availability = result.scalar_one_or_none()
            
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
