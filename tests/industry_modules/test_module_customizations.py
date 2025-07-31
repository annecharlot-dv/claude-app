"""
Tests for industry-specific module customizations
"""
import pytest
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

@pytest.mark.unit
class TestCoworkingModuleCustomizations:
    """Test coworking space specific customizations"""
    
    def test_coworking_terminology_mapping(self):
        """Test coworking-specific terminology"""
        coworking_terms = {
            "space": "workspace",
            "booking": "reservation", 
            "user": "member",
            "admin": "community_manager",
            "rate": "membership_fee"
        }
        
        # Test terminology mapping
        assert coworking_terms["space"] == "workspace"
        assert coworking_terms["user"] == "member"
        assert coworking_terms["admin"] == "community_manager"
    
    def test_coworking_booking_rules(self):
        """Test coworking-specific booking rules"""
        coworking_rules = {
            "advance_booking_days": 30,
            "max_booking_duration": 480,  # 8 hours
            "cancellation_hours": 24,
            "member_priority": True,
            "hot_desk_limit": 1,  # One hot desk per member per day
            "meeting_room_advance": 7  # Meeting rooms can be booked 7 days ahead
        }
        
        def validate_coworking_booking(booking_data: Dict[str, Any]) -> Dict[str, Any]:
            errors = []
            
            # Check hot desk limit
            if booking_data.get("space_type") == "hot_desk":
                if booking_data.get("daily_bookings", 0) >= coworking_rules["hot_desk_limit"]:
                    errors.append("Hot desk limit exceeded for today")
            
            # Check meeting room advance booking
            if booking_data.get("space_type") == "meeting_room":
                advance_days = booking_data.get("advance_days", 0)
                if advance_days > coworking_rules["meeting_room_advance"]:
                    errors.append(f"Meeting rooms can only be booked {coworking_rules['meeting_room_advance']} days in advance")
            
            return {"valid": len(errors) == 0, "errors": errors}
        
        # Test valid hot desk booking
        valid_booking = {"space_type": "hot_desk", "daily_bookings": 0}
        result = validate_coworking_booking(valid_booking)
        assert result["valid"] is True
        
        # Test hot desk limit exceeded
        invalid_booking = {"space_type": "hot_desk", "daily_bookings": 1}
        result = validate_coworking_booking(invalid_booking)
        assert result["valid"] is False
        assert "Hot desk limit exceeded" in result["errors"][0]
    
    def test_coworking_pricing_model(self):
        """Test coworking-specific pricing"""
        def calculate_coworking_price(space_type: str, duration_hours: float, member_type: str) -> Dict[str, Any]:
            base_rates = {
                "hot_desk": 5.0,
                "dedicated_desk": 15.0,
                "meeting_room": 25.0,
                "phone_booth": 10.0
            }
            
            member_discounts = {
                "day_pass": 1.0,
                "monthly": 0.8,
                "annual": 0.7
            }
            
            base_cost = base_rates.get(space_type, 0) * duration_hours
            discount = member_discounts.get(member_type, 1.0)
            final_cost = base_cost * discount
            
            return {
                "base_cost": base_cost,
                "discount_rate": discount,
                "final_cost": final_cost,
                "member_type": member_type
            }
        
        # Test monthly member discount
        pricing = calculate_coworking_price("meeting_room", 2.0, "monthly")
        assert pricing["base_cost"] == 50.0
        assert pricing["discount_rate"] == 0.8
        assert pricing["final_cost"] == 40.0

@pytest.mark.unit
class TestUniversityModuleCustomizations:
    """Test university-specific customizations"""
    
    def test_university_terminology_mapping(self):
        """Test university-specific terminology"""
        university_terms = {
            "space": "classroom",
            "booking": "class_schedule",
            "user": "student",
            "admin": "registrar",
            "rate": "course_fee"
        }
        
        assert university_terms["space"] == "classroom"
        assert university_terms["user"] == "student"
        assert university_terms["admin"] == "registrar"
    
    def test_university_role_hierarchy(self):
        """Test university-specific role hierarchy"""
        university_roles = {
            "student": 1,
            "teaching_assistant": 2,
            "instructor": 3,
            "professor": 4,
            "department_head": 5,
            "dean": 6,
            "registrar": 7
        }
        
        def check_university_permission(user_role: str, required_role: str) -> bool:
            user_level = university_roles.get(user_role, 0)
            required_level = university_roles.get(required_role, 999)
            return user_level >= required_level
        
        # Test role hierarchy
        assert check_university_permission("professor", "instructor") is True
        assert check_university_permission("student", "professor") is False
        assert check_university_permission("dean", "department_head") is True
    
    def test_academic_calendar_integration(self):
        """Test academic calendar specific rules"""
        def validate_academic_booking(booking_data: Dict[str, Any], calendar: Dict[str, Any]) -> Dict[str, Any]:
            errors = []
            
            booking_date = booking_data.get("date")
            
            # Check if date is within semester
            if booking_date < calendar["semester_start"] or booking_date > calendar["semester_end"]:
                errors.append("Booking date is outside current semester")
            
            # Check if date is a holiday
            if booking_date in calendar.get("holidays", []):
                errors.append("Cannot book on university holidays")
            
            # Check if during exam period
            if (calendar.get("exam_start") <= booking_date <= calendar.get("exam_end")):
                if booking_data.get("booking_type") != "exam":
                    errors.append("Only exam bookings allowed during exam period")
            
            return {"valid": len(errors) == 0, "errors": errors}
        
        calendar = {
            "semester_start": "2024-08-26",
            "semester_end": "2024-12-15",
            "holidays": ["2024-11-28", "2024-11-29"],
            "exam_start": "2024-12-09",
            "exam_end": "2024-12-15"
        }
        
        # Test valid booking
        valid_booking = {"date": "2024-10-15", "booking_type": "lecture"}
        result = validate_academic_booking(valid_booking, calendar)
        assert result["valid"] is True
        
        # Test holiday booking
        holiday_booking = {"date": "2024-11-28", "booking_type": "lecture"}
        result = validate_academic_booking(holiday_booking, calendar)
        assert result["valid"] is False
        assert "Cannot book on university holidays" in result["errors"]

@pytest.mark.unit
class TestHotelModuleCustomizations:
    """Test hotel-specific customizations"""
    
    def test_hotel_terminology_mapping(self):
        """Test hotel-specific terminology"""
        hotel_terms = {
            "space": "room",
            "booking": "reservation",
            "user": "guest",
            "admin": "front_desk_manager",
            "rate": "room_rate"
        }
        
        assert hotel_terms["space"] == "room"
        assert hotel_terms["user"] == "guest"
        assert hotel_terms["booking"] == "reservation"
    
    def test_hotel_room_types_and_rates(self):
        """Test hotel room type management"""
        room_types = {
            "standard": {"base_rate": 120.0, "capacity": 2, "amenities": ["wifi", "tv"]},
            "deluxe": {"base_rate": 180.0, "capacity": 4, "amenities": ["wifi", "tv", "balcony"]},
            "suite": {"base_rate": 300.0, "capacity": 6, "amenities": ["wifi", "tv", "balcony", "kitchenette"]}
        }
        
        def calculate_hotel_rate(room_type: str, nights: int, season: str) -> Dict[str, Any]:
            base_rate = room_types[room_type]["base_rate"]
            
            seasonal_multipliers = {
                "low": 0.8,
                "regular": 1.0,
                "peak": 1.5
            }
            
            multiplier = seasonal_multipliers.get(season, 1.0)
            nightly_rate = base_rate * multiplier
            total_cost = nightly_rate * nights
            
            return {
                "room_type": room_type,
                "base_rate": base_rate,
                "nightly_rate": nightly_rate,
                "nights": nights,
                "total_cost": total_cost,
                "season": season
            }
        
        # Test peak season pricing
        pricing = calculate_hotel_rate("deluxe", 3, "peak")
        assert pricing["base_rate"] == 180.0
        assert pricing["nightly_rate"] == 270.0  # 180 * 1.5
        assert pricing["total_cost"] == 810.0    # 270 * 3
    
    def test_hotel_guest_services(self):
        """Test hotel guest service features"""
        def process_guest_request(request_type: str, guest_data: Dict[str, Any]) -> Dict[str, Any]:
            service_catalog = {
                "room_service": {"available_hours": "24/7", "delivery_fee": 5.0},
                "housekeeping": {"available_hours": "8:00-18:00", "extra_cleaning_fee": 25.0},
                "concierge": {"available_hours": "6:00-22:00", "booking_fee": 0.0},
                "spa": {"available_hours": "9:00-21:00", "booking_required": True}
            }
            
            service = service_catalog.get(request_type)
            if not service:
                return {"success": False, "error": "Service not available"}
            
            return {
                "success": True,
                "service": request_type,
                "details": service,
                "guest_id": guest_data.get("guest_id")
            }
        
        # Test room service request
        guest = {"guest_id": "guest_001", "room": "101"}
        result = process_guest_request("room_service", guest)
        assert result["success"] is True
        assert result["details"]["available_hours"] == "24/7"

@pytest.mark.unit
class TestCreativeStudioModuleCustomizations:
    """Test creative studio specific customizations"""
    
    def test_creative_studio_terminology(self):
        """Test creative studio terminology"""
        creative_terms = {
            "space": "studio",
            "booking": "session",
            "user": "artist",
            "admin": "studio_manager",
            "rate": "studio_rate"
        }
        
        assert creative_terms["space"] == "studio"
        assert creative_terms["user"] == "artist"
        assert creative_terms["booking"] == "session"
    
    def test_equipment_booking_integration(self):
        """Test equipment booking alongside studio space"""
        def book_studio_with_equipment(studio_id: str, equipment_list: List[str], duration: int) -> Dict[str, Any]:
            studio_rates = {
                "recording_studio": 75.0,
                "photo_studio": 50.0,
                "video_studio": 100.0
            }
            
            equipment_rates = {
                "professional_camera": 25.0,
                "lighting_kit": 15.0,
                "microphone_set": 10.0,
                "editing_workstation": 20.0
            }
            
            studio_cost = studio_rates.get(studio_id, 0) * duration
            equipment_cost = sum(equipment_rates.get(item, 0) * duration for item in equipment_list)
            total_cost = studio_cost + equipment_cost
            
            return {
                "studio_id": studio_id,
                "equipment": equipment_list,
                "duration_hours": duration,
                "studio_cost": studio_cost,
                "equipment_cost": equipment_cost,
                "total_cost": total_cost
            }
        
        # Test studio booking with equipment
        booking = book_studio_with_equipment(
            "recording_studio", 
            ["professional_camera", "lighting_kit"], 
            4
        )
        
        assert booking["studio_cost"] == 300.0  # 75 * 4
        assert booking["equipment_cost"] == 160.0  # (25 + 15) * 4
        assert booking["total_cost"] == 460.0
    
    def test_project_based_booking(self):
        """Test project-based booking workflows"""
        def create_project_booking(project_data: Dict[str, Any]) -> Dict[str, Any]:
            # Creative projects can span multiple sessions
            sessions = []
            total_cost = 0
            
            for session in project_data["sessions"]:
                session_cost = session["studio_rate"] * session["duration"]
                total_cost += session_cost
                
                sessions.append({
                    "session_id": session["session_id"],
                    "date": session["date"],
                    "studio": session["studio"],
                    "duration": session["duration"],
                    "cost": session_cost
                })
            
            return {
                "project_id": project_data["project_id"],
                "project_name": project_data["project_name"],
                "artist_id": project_data["artist_id"],
                "sessions": sessions,
                "total_sessions": len(sessions),
                "total_cost": total_cost,
                "status": "scheduled"
            }
        
        project_data = {
            "project_id": "album_recording_001",
            "project_name": "Debut Album Recording",
            "artist_id": "artist_123",
            "sessions": [
                {"session_id": "s1", "date": "2024-12-01", "studio": "recording_studio", "duration": 8, "studio_rate": 75.0},
                {"session_id": "s2", "date": "2024-12-03", "studio": "recording_studio", "duration": 6, "studio_rate": 75.0},
                {"session_id": "s3", "date": "2024-12-05", "studio": "recording_studio", "duration": 4, "studio_rate": 75.0}
            ]
        }
        
        project = create_project_booking(project_data)
        assert project["total_sessions"] == 3
        assert project["total_cost"] == 1350.0  # (8+6+4) * 75

@pytest.mark.integration
class TestModuleInteroperability:
    """Test that different modules can coexist and don't interfere"""
    
    async def test_cross_module_data_isolation(self, clean_db: AsyncIOMotorDatabase):
        """Test that different modules maintain data isolation"""
        # Create data for different modules
        module_data = [
            {"tenant_id": "coworking", "module": "coworking_module", "data": "coworking_specific"},
            {"tenant_id": "university", "module": "university_module", "data": "university_specific"},
            {"tenant_id": "hotel", "module": "hotel_module", "data": "hotel_specific"}
        ]
        
        await clean_db.module_data.insert_many(module_data)
        
        # Test module-specific data retrieval
        coworking_data = await clean_db.module_data.find({"module": "coworking_module"}).to_list(None)
        university_data = await clean_db.module_data.find({"module": "university_module"}).to_list(None)
        
        assert len(coworking_data) == 1
        assert len(university_data) == 1
        assert coworking_data[0]["data"] == "coworking_specific"
        assert university_data[0]["data"] == "university_specific"
    
    def test_module_configuration_loading(self):
        """Test that modules load their specific configurations"""
        def load_module_config(module_name: str) -> Dict[str, Any]:
            module_configs = {
                "coworking_module": {
                    "terminology": {"space": "workspace", "user": "member"},
                    "booking_rules": {"advance_days": 30, "max_duration": 480},
                    "features": ["hot_desk_booking", "meeting_room_booking", "event_space"]
                },
                "university_module": {
                    "terminology": {"space": "classroom", "user": "student"},
                    "booking_rules": {"advance_days": 90, "max_duration": 240},
                    "features": ["class_scheduling", "exam_booking", "academic_calendar"]
                },
                "hotel_module": {
                    "terminology": {"space": "room", "user": "guest"},
                    "booking_rules": {"advance_days": 365, "max_duration": 1440},
                    "features": ["room_booking", "guest_services", "seasonal_pricing"]
                }
            }
            
            return module_configs.get(module_name, {})
        
        # Test different module configurations
        coworking_config = load_module_config("coworking_module")
        university_config = load_module_config("university_module")
        hotel_config = load_module_config("hotel_module")
        
        assert coworking_config["terminology"]["space"] == "workspace"
        assert university_config["terminology"]["space"] == "classroom"
        assert hotel_config["terminology"]["space"] == "room"
        
        assert coworking_config["booking_rules"]["advance_days"] == 30
        assert university_config["booking_rules"]["advance_days"] == 90
        assert hotel_config["booking_rules"]["advance_days"] == 365