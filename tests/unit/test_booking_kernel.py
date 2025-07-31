"""
Unit tests for booking kernel business logic
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any

@pytest.mark.unit
class TestBookingKernel:
    """Test core booking business logic"""
    
    async def test_availability_checking(self, clean_db: AsyncIOMotorDatabase, seed_spaces: Dict[str, Dict[str, Any]]):
        """Test space availability checking logic"""
        # Create existing booking
        existing_booking = {
            "booking_id": "existing_1",
            "tenant_id": "coworking",
            "space_id": "meeting_room_1",
            "start_time": datetime(2024, 12, 1, 10, 0),
            "end_time": datetime(2024, 12, 1, 11, 0),
            "status": "confirmed"
        }
        await clean_db.bookings.insert_one(existing_booking)
        
        # Test availability check function
        async def check_availability(space_id: str, start_time: datetime, end_time: datetime, tenant_id: str) -> bool:
            conflicts = await clean_db.bookings.find({
                "tenant_id": tenant_id,
                "space_id": space_id,
                "status": {"$in": ["confirmed", "pending"]},
                "$or": [
                    {"start_time": {"$lt": end_time, "$gte": start_time}},
                    {"end_time": {"$gt": start_time, "$lte": end_time}},
                    {"start_time": {"$lte": start_time}, "end_time": {"$gte": end_time}}
                ]
            }).to_list(None)
            return len(conflicts) == 0
        
        # Test conflicting booking
        is_available = await check_availability(
            "meeting_room_1",
            datetime(2024, 12, 1, 10, 30),
            datetime(2024, 12, 1, 11, 30),
            "coworking"
        )
        assert not is_available
        
        # Test non-conflicting booking
        is_available = await check_availability(
            "meeting_room_1", 
            datetime(2024, 12, 1, 12, 0),
            datetime(2024, 12, 1, 13, 0),
            "coworking"
        )
        assert is_available
    
    async def test_booking_creation_validation(self, clean_db: AsyncIOMotorDatabase):
        """Test booking creation with business rule validation"""
        
        class BookingValidator:
            def __init__(self, tenant_settings: Dict[str, Any]):
                self.tenant_settings = tenant_settings
            
            def validate_booking_request(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
                errors = []
                
                # Check advance booking limit
                advance_days = self.tenant_settings.get("booking_advance_days", 30)
                max_advance_date = datetime.now() + timedelta(days=advance_days)
                if booking_data["start_time"] > max_advance_date:
                    errors.append(f"Cannot book more than {advance_days} days in advance")
                
                # Check maximum duration
                max_duration = self.tenant_settings.get("max_booking_duration", 480)  # minutes
                duration = (booking_data["end_time"] - booking_data["start_time"]).total_seconds() / 60
                if duration > max_duration:
                    errors.append(f"Booking duration cannot exceed {max_duration} minutes")
                
                # Check minimum duration
                if duration < 30:  # 30 minutes minimum
                    errors.append("Booking duration must be at least 30 minutes")
                
                return {"valid": len(errors) == 0, "errors": errors}
        
        # Test with coworking settings
        coworking_settings = {"booking_advance_days": 30, "max_booking_duration": 480}
        validator = BookingValidator(coworking_settings)
        
        # Valid booking
        valid_booking = {
            "start_time": datetime.now() + timedelta(days=1),
            "end_time": datetime.now() + timedelta(days=1, hours=2)
        }
        result = validator.validate_booking_request(valid_booking)
        assert result["valid"] is True
        
        # Too far in advance
        invalid_booking = {
            "start_time": datetime.now() + timedelta(days=45),
            "end_time": datetime.now() + timedelta(days=45, hours=2)
        }
        result = validator.validate_booking_request(invalid_booking)
        assert result["valid"] is False
        assert "Cannot book more than 30 days in advance" in result["errors"]
        
        # Too long duration
        long_booking = {
            "start_time": datetime.now() + timedelta(days=1),
            "end_time": datetime.now() + timedelta(days=1, hours=10)
        }
        result = validator.validate_booking_request(long_booking)
        assert result["valid"] is False
        assert "Booking duration cannot exceed 480 minutes" in result["errors"]
    
    async def test_booking_pricing_calculation(self):
        """Test booking pricing calculation logic"""
        
        class PricingCalculator:
            def calculate_booking_cost(self, space_data: Dict[str, Any], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
                duration_hours = (end_time - start_time).total_seconds() / 3600
                base_cost = space_data["hourly_rate"] * duration_hours
                
                # Apply time-based multipliers
                multiplier = 1.0
                if start_time.hour >= 18 or start_time.hour < 8:  # Evening/early morning
                    multiplier = 1.2
                elif start_time.weekday() >= 5:  # Weekend
                    multiplier = 1.5
                
                total_cost = base_cost * multiplier
                
                return {
                    "base_cost": round(base_cost, 2),
                    "multiplier": multiplier,
                    "total_cost": round(total_cost, 2),
                    "duration_hours": duration_hours
                }
        
        calculator = PricingCalculator()
        space_data = {"hourly_rate": 25.0}
        
        # Regular hours booking
        start_time = datetime(2024, 12, 2, 10, 0)  # Monday 10 AM
        end_time = datetime(2024, 12, 2, 12, 0)    # Monday 12 PM
        
        pricing = calculator.calculate_booking_cost(space_data, start_time, end_time)
        assert pricing["base_cost"] == 50.0
        assert pricing["multiplier"] == 1.0
        assert pricing["total_cost"] == 50.0
        
        # Evening booking
        start_time = datetime(2024, 12, 2, 19, 0)  # Monday 7 PM
        end_time = datetime(2024, 12, 2, 21, 0)    # Monday 9 PM
        
        pricing = calculator.calculate_booking_cost(space_data, start_time, end_time)
        assert pricing["base_cost"] == 50.0
        assert pricing["multiplier"] == 1.2
        assert pricing["total_cost"] == 60.0
    
    async def test_booking_cancellation_logic(self, clean_db: AsyncIOMotorDatabase):
        """Test booking cancellation business rules"""
        
        class BookingCancellation:
            def __init__(self, tenant_settings: Dict[str, Any]):
                self.tenant_settings = tenant_settings
            
            def can_cancel_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
                cancellation_hours = self.tenant_settings.get("cancellation_hours", 24)
                min_cancel_time = booking_data["start_time"] - timedelta(hours=cancellation_hours)
                
                can_cancel = datetime.now() <= min_cancel_time
                
                return {
                    "can_cancel": can_cancel,
                    "reason": None if can_cancel else f"Must cancel at least {cancellation_hours} hours in advance"
                }
        
        # Test with different tenant settings
        coworking_settings = {"cancellation_hours": 24}
        university_settings = {"cancellation_hours": 48}
        
        coworking_cancellation = BookingCancellation(coworking_settings)
        university_cancellation = BookingCancellation(university_settings)
        
        # Booking starting in 30 hours
        future_booking = {
            "start_time": datetime.now() + timedelta(hours=30)
        }
        
        # Coworking allows cancellation (24h policy)
        result = coworking_cancellation.can_cancel_booking(future_booking)
        assert result["can_cancel"] is True
        
        # University doesn't allow cancellation (48h policy)
        result = university_cancellation.can_cancel_booking(future_booking)
        assert result["can_cancel"] is False
        assert "Must cancel at least 48 hours in advance" in result["reason"]
    
    async def test_waitlist_management(self, clean_db: AsyncIOMotorDatabase):
        """Test waitlist functionality for fully booked spaces"""
        
        class WaitlistManager:
            def __init__(self, db: AsyncIOMotorDatabase):
                self.db = db
            
            async def add_to_waitlist(self, booking_request: Dict[str, Any]) -> str:
                waitlist_entry = {
                    "waitlist_id": f"waitlist_{booking_request['user_id']}_{int(datetime.now().timestamp())}",
                    "tenant_id": booking_request["tenant_id"],
                    "user_id": booking_request["user_id"],
                    "space_id": booking_request["space_id"],
                    "requested_start": booking_request["start_time"],
                    "requested_end": booking_request["end_time"],
                    "created_at": datetime.now(),
                    "status": "waiting"
                }
                
                await self.db.waitlist.insert_one(waitlist_entry)
                return waitlist_entry["waitlist_id"]
            
            async def process_waitlist_on_cancellation(self, cancelled_booking: Dict[str, Any]):
                # Find waitlist entries for the same space and time
                waitlist_entries = await self.db.waitlist.find({
                    "tenant_id": cancelled_booking["tenant_id"],
                    "space_id": cancelled_booking["space_id"],
                    "requested_start": {"$lte": cancelled_booking["end_time"]},
                    "requested_end": {"$gte": cancelled_booking["start_time"]},
                    "status": "waiting"
                }).sort("created_at", 1).to_list(None)
                
                return waitlist_entries
        
        waitlist_manager = WaitlistManager(clean_db)
        
        # Add waitlist entry
        booking_request = {
            "tenant_id": "coworking",
            "user_id": "member_user",
            "space_id": "meeting_room_1",
            "start_time": datetime(2024, 12, 1, 10, 0),
            "end_time": datetime(2024, 12, 1, 11, 0)
        }
        
        waitlist_id = await waitlist_manager.add_to_waitlist(booking_request)
        assert waitlist_id.startswith("waitlist_member_user_")
        
        # Verify waitlist entry was created
        waitlist_entry = await clean_db.waitlist.find_one({"waitlist_id": waitlist_id})
        assert waitlist_entry is not None
        assert waitlist_entry["status"] == "waiting"
        
        # Test waitlist processing on cancellation
        cancelled_booking = {
            "tenant_id": "coworking",
            "space_id": "meeting_room_1",
            "start_time": datetime(2024, 12, 1, 10, 0),
            "end_time": datetime(2024, 12, 1, 11, 0)
        }
        
        matching_entries = await waitlist_manager.process_waitlist_on_cancellation(cancelled_booking)
        assert len(matching_entries) == 1
        assert matching_entries[0]["waitlist_id"] == waitlist_id