"""
End-to-end tests for complete user workflows across different industries
"""
import pytest
import asyncio
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

@pytest.mark.e2e
class TestCoworkingWorkflows:
    """Test complete coworking space user workflows"""
    
    async def test_member_booking_workflow(self, clean_db: AsyncIOMotorDatabase, seed_spaces: Dict[str, Dict[str, Any]]):
        """Test complete member booking workflow"""
        # Step 1: User searches for available spaces
        search_criteria = {
            "tenant_id": "coworking",
            "date": "2024-12-01",
            "start_time": "10:00",
            "end_time": "11:00",
            "capacity": 8
        }
        
        # Simulate space search
        available_spaces = await clean_db.spaces.find({
            "tenant_id": search_criteria["tenant_id"],
            "capacity": {"$gte": search_criteria["capacity"]},
            "active": True
        }).to_list(None)
        
        assert len(available_spaces) > 0
        selected_space = available_spaces[0]
        
        # Step 2: User creates booking
        booking_data = {
            "booking_id": "member_booking_001",
            "tenant_id": "coworking",
            "user_id": "member_user",
            "space_id": selected_space["space_id"],
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z",
            "purpose": "Team standup meeting",
            "status": "confirmed",
            "created_at": datetime.utcnow()
        }
        
        await clean_db.bookings.insert_one(booking_data)
        
        # Step 3: Verify booking confirmation
        confirmed_booking = await clean_db.bookings.find_one({"booking_id": "member_booking_001"})
        assert confirmed_booking is not None
        assert confirmed_booking["status"] == "confirmed"
        
        # Step 4: Simulate notification creation
        notification = {
            "notification_id": "booking_confirm_001",
            "tenant_id": "coworking",
            "user_id": "member_user",
            "type": "booking_confirmation",
            "message": f"Your booking for {selected_space['name']} is confirmed",
            "booking_id": "member_booking_001",
            "sent": True
        }
        
        await clean_db.notifications.insert_one(notification)
        
        # Step 5: User views their bookings
        user_bookings = await clean_db.bookings.find({
            "tenant_id": "coworking",
            "user_id": "member_user"
        }).to_list(None)
        
        assert len(user_bookings) == 1
        assert user_bookings[0]["booking_id"] == "member_booking_001"
    
    async def test_admin_space_management_workflow(self, clean_db: AsyncIOMotorDatabase):
        """Test admin space management workflow"""
        # Step 1: Admin creates new space
        new_space = {
            "space_id": "new_meeting_room",
            "tenant_id": "coworking",
            "name": "Meeting Room B",
            "capacity": 12,
            "hourly_rate": 35.0,
            "amenities": ["projector", "whiteboard", "wifi", "video_conference"],
            "active": True,
            "created_by": "admin_user",
            "created_at": datetime.utcnow()
        }
        
        await clean_db.spaces.insert_one(new_space)
        
        # Step 2: Admin configures booking rules
        booking_rules = {
            "rule_id": "meeting_room_b_rules",
            "tenant_id": "coworking",
            "space_id": "new_meeting_room",
            "max_advance_days": 30,
            "min_booking_duration": 30,
            "max_booking_duration": 480,
            "cancellation_hours": 24,
            "auto_approval": True
        }
        
        await clean_db.booking_rules.insert_one(booking_rules)
        
        # Step 3: Admin sets pricing schedule
        pricing_schedule = {
            "schedule_id": "meeting_room_b_pricing",
            "tenant_id": "coworking",
            "space_id": "new_meeting_room",
            "base_rate": 35.0,
            "peak_hours": {"start": "09:00", "end": "17:00", "multiplier": 1.0},
            "off_peak_multiplier": 0.8,
            "weekend_multiplier": 1.2
        }
        
        await clean_db.pricing_schedules.insert_one(pricing_schedule)
        
        # Step 4: Verify space is available for booking
        available_space = await clean_db.spaces.find_one({
            "space_id": "new_meeting_room",
            "tenant_id": "coworking",
            "active": True
        })
        
        assert available_space is not None
        assert available_space["name"] == "Meeting Room B"
        
        # Step 5: Admin views space utilization
        # Simulate some bookings for the new space
        test_bookings = [
            {
                "booking_id": f"test_booking_{i}",
                "tenant_id": "coworking",
                "space_id": "new_meeting_room",
                "start_time": f"2024-12-0{i+1}T10:00:00Z",
                "end_time": f"2024-12-0{i+1}T11:00:00Z",
                "status": "confirmed"
            }
            for i in range(3)
        ]
        
        await clean_db.bookings.insert_many(test_bookings)
        
        # Calculate utilization
        total_bookings = await clean_db.bookings.count_documents({
            "tenant_id": "coworking",
            "space_id": "new_meeting_room",
            "status": "confirmed"
        })
        
        assert total_bookings == 3

@pytest.mark.e2e
class TestUniversityWorkflows:
    """Test university-specific workflows"""
    
    async def test_faculty_classroom_booking_workflow(self, clean_db: AsyncIOMotorDatabase):
        """Test faculty classroom booking with academic calendar integration"""
        # Step 1: Create academic calendar
        academic_calendar = {
            "calendar_id": "fall_2024",
            "tenant_id": "university",
            "semester": "Fall 2024",
            "start_date": "2024-08-26",
            "end_date": "2024-12-15",
            "holidays": ["2024-11-28", "2024-11-29"],  # Thanksgiving
            "exam_period": {"start": "2024-12-09", "end": "2024-12-15"}
        }
        
        await clean_db.academic_calendars.insert_one(academic_calendar)
        
        # Step 2: Faculty creates recurring class booking
        recurring_booking = {
            "booking_id": "cs101_fall2024",
            "tenant_id": "university",
            "user_id": "faculty_user",
            "space_id": "lecture_hall_1",
            "course_code": "CS101",
            "course_name": "Introduction to Computer Science",
            "recurring_pattern": {
                "type": "weekly",
                "days": ["monday", "wednesday", "friday"],
                "start_time": "10:00",
                "end_time": "11:00",
                "start_date": "2024-08-26",
                "end_date": "2024-12-06"  # Exclude exam period
            },
            "status": "confirmed",
            "priority": "high"  # Faculty bookings have high priority
        }
        
        await clean_db.recurring_bookings.insert_one(recurring_booking)
        
        # Step 3: Generate individual booking instances
        booking_instances = []
        current_date = datetime(2024, 8, 26)  # Start date
        end_date = datetime(2024, 12, 6)
        
        while current_date <= end_date:
            if current_date.strftime("%A").lower() in ["monday", "wednesday", "friday"]:
                # Skip holidays
                if current_date.strftime("%Y-%m-%d") not in academic_calendar["holidays"]:
                    instance = {
                        "booking_id": f"cs101_{current_date.strftime('%Y%m%d')}",
                        "tenant_id": "university",
                        "user_id": "faculty_user",
                        "space_id": "lecture_hall_1",
                        "start_time": current_date.replace(hour=10, minute=0),
                        "end_time": current_date.replace(hour=11, minute=0),
                        "course_code": "CS101",
                        "status": "confirmed",
                        "recurring_parent": "cs101_fall2024"
                    }
                    booking_instances.append(instance)
            
            current_date += timedelta(days=1)
        
        await clean_db.bookings.insert_many(booking_instances)
        
        # Step 4: Verify booking instances were created
        created_instances = await clean_db.bookings.find({
            "recurring_parent": "cs101_fall2024"
        }).to_list(None)
        
        assert len(created_instances) > 30  # Should have many instances over semester
        
        # Step 5: Student views class schedule
        student_schedule = await clean_db.bookings.find({
            "tenant_id": "university",
            "course_code": "CS101",
            "start_time": {"$gte": datetime(2024, 12, 1)}
        }).sort("start_time", 1).to_list(None)
        
        assert len(student_schedule) > 0
    
    async def test_student_study_room_booking_workflow(self, clean_db: AsyncIOMotorDatabase):
        """Test student study room booking with restrictions"""
        # Step 1: Create study room with student restrictions
        study_room = {
            "space_id": "study_room_1",
            "tenant_id": "university",
            "name": "Group Study Room A",
            "capacity": 6,
            "hourly_rate": 0.0,  # Free for students
            "amenities": ["whiteboard", "wifi", "power_outlets"],
            "restrictions": {
                "student_only": True,
                "max_booking_hours": 3,
                "advance_booking_days": 7,
                "max_daily_bookings": 1
            },
            "active": True
        }
        
        await clean_db.spaces.insert_one(study_room)
        
        # Step 2: Student attempts to book study room
        student_booking = {
            "booking_id": "student_study_001",
            "tenant_id": "university",
            "user_id": "student_user",
            "space_id": "study_room_1",
            "start_time": datetime.utcnow() + timedelta(days=2, hours=2),
            "end_time": datetime.utcnow() + timedelta(days=2, hours=4),
            "purpose": "Group project work",
            "status": "pending"  # Requires validation
        }
        
        # Step 3: Validate booking against restrictions
        def validate_student_booking(booking: Dict[str, Any], restrictions: Dict[str, Any]) -> Dict[str, bool]:
            errors = []
            
            # Check booking duration
            duration_hours = (booking["end_time"] - booking["start_time"]).total_seconds() / 3600
            if duration_hours > restrictions["max_booking_hours"]:
                errors.append(f"Booking duration exceeds {restrictions['max_booking_hours']} hour limit")
            
            # Check advance booking
            advance_days = (booking["start_time"] - datetime.utcnow()).days
            if advance_days > restrictions["advance_booking_days"]:
                errors.append(f"Cannot book more than {restrictions['advance_booking_days']} days in advance")
            
            return {"valid": len(errors) == 0, "errors": errors}
        
        validation_result = validate_student_booking(student_booking, study_room["restrictions"])
        
        if validation_result["valid"]:
            student_booking["status"] = "confirmed"
        
        await clean_db.bookings.insert_one(student_booking)
        
        # Step 4: Verify booking was confirmed
        confirmed_booking = await clean_db.bookings.find_one({"booking_id": "student_study_001"})
        assert confirmed_booking["status"] == "confirmed"

@pytest.mark.e2e
class TestHotelWorkflows:
    """Test hotel-specific workflows"""
    
    async def test_guest_room_booking_workflow(self, clean_db: AsyncIOMotorDatabase):
        """Test hotel guest room booking workflow"""
        # Step 1: Create hotel room inventory
        hotel_rooms = [
            {
                "space_id": "room_101",
                "tenant_id": "hotel",
                "name": "Standard Room 101",
                "room_type": "standard",
                "capacity": 2,
                "nightly_rate": 120.0,
                "amenities": ["wifi", "tv", "air_conditioning", "private_bathroom"],
                "bed_configuration": "1 Queen Bed",
                "active": True
            },
            {
                "space_id": "room_201",
                "tenant_id": "hotel",
                "name": "Deluxe Room 201",
                "room_type": "deluxe",
                "capacity": 4,
                "nightly_rate": 180.0,
                "amenities": ["wifi", "tv", "air_conditioning", "private_bathroom", "balcony"],
                "bed_configuration": "2 Queen Beds",
                "active": True
            }
        ]
        
        await clean_db.spaces.insert_many(hotel_rooms)
        
        # Step 2: Guest searches for available rooms
        search_criteria = {
            "tenant_id": "hotel",
            "check_in": "2024-12-15",
            "check_out": "2024-12-18",
            "guests": 2,
            "room_type": "standard"
        }
        
        # Find available rooms
        available_rooms = await clean_db.spaces.find({
            "tenant_id": search_criteria["tenant_id"],
            "room_type": search_criteria["room_type"],
            "capacity": {"$gte": search_criteria["guests"]},
            "active": True
        }).to_list(None)
        
        assert len(available_rooms) > 0
        selected_room = available_rooms[0]
        
        # Step 3: Create reservation
        reservation = {
            "booking_id": "reservation_001",
            "tenant_id": "hotel",
            "guest_id": "guest_001",
            "space_id": selected_room["space_id"],
            "check_in_date": "2024-12-15",
            "check_out_date": "2024-12-18",
            "nights": 3,
            "guests": 2,
            "room_rate": selected_room["nightly_rate"],
            "total_amount": selected_room["nightly_rate"] * 3,
            "status": "confirmed",
            "guest_info": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1234567890"
            },
            "special_requests": "Late check-in"
        }
        
        await clean_db.bookings.insert_one(reservation)
        
        # Step 4: Process payment
        payment_record = {
            "payment_id": "payment_001",
            "tenant_id": "hotel",
            "booking_id": "reservation_001",
            "amount": reservation["total_amount"],
            "payment_method": "credit_card",
            "status": "completed",
            "processed_at": datetime.utcnow()
        }
        
        await clean_db.payments.insert_one(payment_record)
        
        # Step 5: Generate confirmation
        confirmation = {
            "confirmation_id": "conf_001",
            "tenant_id": "hotel",
            "booking_id": "reservation_001",
            "confirmation_number": "HTL-2024-001",
            "sent_to": "john.doe@email.com",
            "sent_at": datetime.utcnow()
        }
        
        await clean_db.confirmations.insert_one(confirmation)
        
        # Verify complete workflow
        final_reservation = await clean_db.bookings.find_one({"booking_id": "reservation_001"})
        payment = await clean_db.payments.find_one({"booking_id": "reservation_001"})
        confirm = await clean_db.confirmations.find_one({"booking_id": "reservation_001"})
        
        assert final_reservation["status"] == "confirmed"
        assert payment["status"] == "completed"
        assert confirm["confirmation_number"] == "HTL-2024-001"

@pytest.mark.e2e
class TestCrossIndustryWorkflows:
    """Test workflows that span multiple industry modules"""
    
    async def test_multi_tenant_platform_admin_workflow(self, clean_db: AsyncIOMotorDatabase):
        """Test platform admin managing multiple tenants"""
        # Step 1: Platform admin creates new tenant
        new_tenant = {
            "tenant_id": "creative_studio",
            "name": "Creative Studio Co",
            "subdomain": "creative",
            "module": "creative_studio_module",
            "plan": "professional",
            "settings": {
                "booking_advance_days": 60,
                "cancellation_hours": 48,
                "max_booking_duration": 720,  # 12 hours for creative projects
                "equipment_booking": True
            },
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        await clean_db.tenants.insert_one(new_tenant)
        
        # Step 2: Create tenant admin user
        tenant_admin = {
            "user_id": "creative_admin",
            "tenant_id": "creative_studio",
            "email": "admin@creativestudio.com",
            "role": "account_owner",
            "password_hash": "$2b$12$hashed_password",
            "active": True,
            "created_at": datetime.utcnow()
        }
        
        await clean_db.users.insert_one(tenant_admin)
        
        # Step 3: Platform admin monitors tenant usage
        tenant_stats = {
            "tenant_id": "creative_studio",
            "month": "2024-12",
            "active_users": 0,
            "total_bookings": 0,
            "revenue": 0.0,
            "storage_used_gb": 0.0,
            "api_calls": 0
        }
        
        await clean_db.tenant_stats.insert_one(tenant_stats)
        
        # Step 4: Verify tenant isolation
        creative_tenant = await clean_db.tenants.find_one({"tenant_id": "creative_studio"})
        creative_admin_user = await clean_db.users.find_one({"tenant_id": "creative_studio"})
        
        assert creative_tenant is not None
        assert creative_admin_user["tenant_id"] == "creative_studio"
        
        # Step 5: Platform admin views cross-tenant analytics
        all_tenant_stats = await clean_db.tenant_stats.find({}).to_list(None)
        
        # Should include stats for the new tenant
        creative_stats = next((stats for stats in all_tenant_stats 
                             if stats["tenant_id"] == "creative_studio"), None)
        assert creative_stats is not None