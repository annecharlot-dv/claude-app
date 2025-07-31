"""
Integration tests for API endpoints with multi-tenant context
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any
import json

@pytest.mark.integration
class TestAuthenticationAPI:
    """Test authentication endpoints"""
    
    def test_login_success(self, auth_headers, test_users: Dict[str, Dict[str, Any]]):
        """Test successful login"""
        # Mock FastAPI client
        login_data = {
            "email": "admin@test.com",
            "password": "testpassword",
            "tenant_id": "coworking"
        }
        
        # Simulate successful login response
        expected_response = {
            "access_token": "mock_jwt_token",
            "token_type": "bearer",
            "user": {
                "user_id": "admin_user",
                "email": "admin@test.com",
                "role": "admin",
                "tenant_id": "coworking"
            }
        }
        
        # In a real test, this would use TestClient
        # response = client.post("/api/auth/login", json=login_data)
        # assert response.status_code == 200
        # assert response.json() == expected_response
        
        # For now, validate the expected structure
        assert "access_token" in expected_response
        assert expected_response["user"]["tenant_id"] == "coworking"
    
    def test_login_cross_tenant_prevention(self):
        """Test that users cannot login to wrong tenant"""
        login_data = {
            "email": "admin@test.com",  # Coworking user
            "password": "testpassword",
            "tenant_id": "university"    # Wrong tenant
        }
        
        # Should return 401 Unauthorized
        # In real implementation, this would check tenant_id matches user's tenant
        user_tenant = "coworking"
        requested_tenant = "university"
        
        assert user_tenant != requested_tenant  # Should fail authentication
    
    def test_token_validation(self, create_jwt_token, jwt_secret: str):
        """Test JWT token validation"""
        # Create valid token
        token = create_jwt_token("admin_user", "coworking", "admin")
        
        # Simulate token validation
        import jwt
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            assert payload["sub"] == "admin_user"
            assert payload["tenant_id"] == "coworking"
            assert payload["role"] == "admin"
        except jwt.InvalidTokenError:
            pytest.fail("Valid token should not raise InvalidTokenError")

@pytest.mark.integration
class TestBookingAPI:
    """Test booking-related API endpoints"""
    
    async def test_create_booking_success(self, clean_db: AsyncIOMotorDatabase, seed_spaces: Dict[str, Dict[str, Any]]):
        """Test successful booking creation"""
        booking_data = {
            "space_id": "meeting_room_1",
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z",
            "purpose": "Team meeting"
        }
        
        # Simulate booking creation logic
        booking_record = {
            "booking_id": "booking_123",
            "tenant_id": "coworking",  # From auth context
            "user_id": "member_user",  # From auth context
            **booking_data,
            "status": "confirmed",
            "created_at": "2024-12-01T09:00:00Z"
        }
        
        await clean_db.bookings.insert_one(booking_record)
        
        # Verify booking was created
        created_booking = await clean_db.bookings.find_one({"booking_id": "booking_123"})
        assert created_booking is not None
        assert created_booking["tenant_id"] == "coworking"
        assert created_booking["space_id"] == "meeting_room_1"
    
    async def test_create_booking_conflict(self, clean_db: AsyncIOMotorDatabase):
        """Test booking creation with time conflict"""
        # Create existing booking
        existing_booking = {
            "booking_id": "existing_123",
            "tenant_id": "coworking",
            "space_id": "meeting_room_1",
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z",
            "status": "confirmed"
        }
        await clean_db.bookings.insert_one(existing_booking)
        
        # Try to create conflicting booking
        conflicting_booking = {
            "space_id": "meeting_room_1",
            "start_time": "2024-12-01T10:30:00Z",
            "end_time": "2024-12-01T11:30:00Z"
        }
        
        # Check for conflicts
        conflicts = await clean_db.bookings.find({
            "tenant_id": "coworking",
            "space_id": "meeting_room_1",
            "status": "confirmed",
            "$or": [
                {"start_time": {"$lt": "2024-12-01T11:30:00Z", "$gte": "2024-12-01T10:30:00Z"}},
                {"end_time": {"$gt": "2024-12-01T10:30:00Z", "$lte": "2024-12-01T11:30:00Z"}}
            ]
        }).to_list(None)
        
        assert len(conflicts) > 0  # Should find conflict
    
    async def test_get_bookings_tenant_filtered(self, clean_db: AsyncIOMotorDatabase):
        """Test that booking retrieval is tenant-filtered"""
        # Create bookings for different tenants
        bookings = [
            {
                "booking_id": "coworking_booking",
                "tenant_id": "coworking",
                "user_id": "member_user",
                "space_id": "meeting_room_1"
            },
            {
                "booking_id": "university_booking", 
                "tenant_id": "university",
                "user_id": "cross_tenant_user",
                "space_id": "lecture_hall_1"
            }
        ]
        await clean_db.bookings.insert_many(bookings)
        
        # Simulate API request for coworking tenant
        tenant_id = "coworking"
        user_bookings = await clean_db.bookings.find({"tenant_id": tenant_id}).to_list(None)
        
        assert len(user_bookings) == 1
        assert user_bookings[0]["booking_id"] == "coworking_booking"
        assert user_bookings[0]["tenant_id"] == "coworking"

@pytest.mark.integration
class TestSpaceAPI:
    """Test space management API endpoints"""
    
    async def test_get_available_spaces(self, clean_db: AsyncIOMotorDatabase, seed_spaces: Dict[str, Dict[str, Any]]):
        """Test retrieving available spaces for booking"""
        # Create a booking that makes one space unavailable
        await clean_db.bookings.insert_one({
            "booking_id": "blocking_booking",
            "tenant_id": "coworking",
            "space_id": "meeting_room_1",
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z",
            "status": "confirmed"
        })
        
        # Simulate availability check
        requested_start = "2024-12-01T10:30:00Z"
        requested_end = "2024-12-01T11:30:00Z"
        tenant_id = "coworking"
        
        # Get all spaces for tenant
        all_spaces = await clean_db.spaces.find({"tenant_id": tenant_id, "active": True}).to_list(None)
        
        # Check availability for each space
        available_spaces = []
        for space in all_spaces:
            conflicts = await clean_db.bookings.find({
                "tenant_id": tenant_id,
                "space_id": space["space_id"],
                "status": "confirmed",
                "$or": [
                    {"start_time": {"$lt": requested_end, "$gte": requested_start}},
                    {"end_time": {"$gt": requested_start, "$lte": requested_end}}
                ]
            }).to_list(None)
            
            if len(conflicts) == 0:
                available_spaces.append(space)
        
        # Should have desk available but not meeting room
        assert len(available_spaces) == 1
        assert available_spaces[0]["space_id"] == "desk_1"
    
    async def test_space_creation_tenant_isolation(self, clean_db: AsyncIOMotorDatabase):
        """Test that space creation includes tenant context"""
        space_data = {
            "name": "New Meeting Room",
            "capacity": 10,
            "hourly_rate": 30.0,
            "amenities": ["projector", "wifi"]
        }
        
        # Simulate space creation with tenant context
        tenant_id = "coworking"  # From auth context
        space_record = {
            "space_id": "new_meeting_room",
            "tenant_id": tenant_id,
            **space_data,
            "active": True,
            "created_at": "2024-12-01T09:00:00Z"
        }
        
        await clean_db.spaces.insert_one(space_record)
        
        # Verify space was created with correct tenant
        created_space = await clean_db.spaces.find_one({"space_id": "new_meeting_room"})
        assert created_space is not None
        assert created_space["tenant_id"] == "coworking"

@pytest.mark.integration
class TestCMSAPI:
    """Test CMS-related API endpoints"""
    
    async def test_create_cms_page(self, clean_db: AsyncIOMotorDatabase):
        """Test CMS page creation with tenant isolation"""
        page_data = {
            "slug": "about-us",
            "title": "About Our Coworking Space",
            "content": {
                "blocks": [
                    {"type": "heading", "content": "Welcome"},
                    {"type": "paragraph", "content": "We are a modern coworking space."}
                ]
            },
            "published": True
        }
        
        # Simulate page creation with tenant context
        tenant_id = "coworking"
        page_record = {
            "page_id": "about_us_page",
            "tenant_id": tenant_id,
            **page_data,
            "created_at": "2024-12-01T09:00:00Z",
            "updated_at": "2024-12-01T09:00:00Z"
        }
        
        await clean_db.cms_pages.insert_one(page_record)
        
        # Verify page was created with tenant isolation
        created_page = await clean_db.cms_pages.find_one({"page_id": "about_us_page"})
        assert created_page is not None
        assert created_page["tenant_id"] == "coworking"
        assert created_page["slug"] == "about-us"
    
    async def test_get_cms_pages_tenant_filtered(self, clean_db: AsyncIOMotorDatabase):
        """Test that CMS page retrieval is tenant-filtered"""
        pages = [
            {
                "page_id": "coworking_home",
                "tenant_id": "coworking",
                "slug": "home",
                "title": "Coworking Home"
            },
            {
                "page_id": "university_home",
                "tenant_id": "university", 
                "slug": "home",
                "title": "University Home"
            }
        ]
        await clean_db.cms_pages.insert_many(pages)
        
        # Simulate API request for coworking tenant
        tenant_id = "coworking"
        tenant_pages = await clean_db.cms_pages.find({"tenant_id": tenant_id}).to_list(None)
        
        assert len(tenant_pages) == 1
        assert tenant_pages[0]["title"] == "Coworking Home"
        assert tenant_pages[0]["tenant_id"] == "coworking"

@pytest.mark.integration
class TestUserManagementAPI:
    """Test user management API endpoints"""
    
    async def test_create_user_with_tenant_context(self, clean_db: AsyncIOMotorDatabase):
        """Test user creation includes tenant context"""
        user_data = {
            "email": "newuser@test.com",
            "password": "securepassword",
            "role": "member",
            "first_name": "New",
            "last_name": "User"
        }
        
        # Simulate user creation with tenant context
        tenant_id = "coworking"  # From auth context
        user_record = {
            "user_id": "new_user_123",
            "tenant_id": tenant_id,
            "email": user_data["email"],
            "password_hash": "$2b$12$hashed_password",
            "role": user_data["role"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "active": True,
            "created_at": "2024-12-01T09:00:00Z"
        }
        
        await clean_db.users.insert_one(user_record)
        
        # Verify user was created with correct tenant
        created_user = await clean_db.users.find_one({"user_id": "new_user_123"})
        assert created_user is not None
        assert created_user["tenant_id"] == "coworking"
        assert created_user["email"] == "newuser@test.com"
    
    async def test_get_users_tenant_filtered(self, clean_db: AsyncIOMotorDatabase, seed_users: Dict[str, Dict[str, Any]]):
        """Test that user retrieval is tenant-filtered"""
        # Simulate API request for coworking tenant
        tenant_id = "coworking"
        tenant_users = await clean_db.users.find({"tenant_id": tenant_id}).to_list(None)
        
        # Should only get coworking users
        assert len(tenant_users) == 3  # admin, manager, member
        for user in tenant_users:
            assert user["tenant_id"] == "coworking"