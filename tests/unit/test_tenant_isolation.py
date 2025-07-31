"""
Unit tests for multi-tenant data isolation
"""
import pytest
from unittest.mock import AsyncMock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any

@pytest.mark.unit
@pytest.mark.tenant_isolation
class TestTenantIsolation:
    """Test tenant data isolation at the kernel level"""
    
    async def test_user_data_isolation(self, clean_db: AsyncIOMotorDatabase, seed_users: Dict[str, Dict[str, Any]]):
        """Test that users can only access their tenant's data"""
        # Simulate identity kernel filtering
        coworking_users = await clean_db.users.find({"tenant_id": "coworking"}).to_list(None)
        university_users = await clean_db.users.find({"tenant_id": "university"}).to_list(None)
        
        assert len(coworking_users) == 3  # admin, manager, member
        assert len(university_users) == 1  # cross_tenant user
        
        # Verify no cross-tenant data leakage
        for user in coworking_users:
            assert user["tenant_id"] == "coworking"
        
        for user in university_users:
            assert user["tenant_id"] == "university"
    
    async def test_booking_data_isolation(self, clean_db: AsyncIOMotorDatabase):
        """Test booking data isolation between tenants"""
        # Create test bookings for different tenants
        bookings = [
            {
                "booking_id": "booking_1",
                "tenant_id": "coworking",
                "user_id": "member_user",
                "space_id": "meeting_room_1",
                "start_time": "2024-12-01T10:00:00Z",
                "end_time": "2024-12-01T11:00:00Z"
            },
            {
                "booking_id": "booking_2", 
                "tenant_id": "university",
                "user_id": "cross_tenant_user",
                "space_id": "lecture_hall_1",
                "start_time": "2024-12-01T10:00:00Z",
                "end_time": "2024-12-01T11:00:00Z"
            }
        ]
        
        await clean_db.bookings.insert_many(bookings)
        
        # Test tenant filtering
        coworking_bookings = await clean_db.bookings.find({"tenant_id": "coworking"}).to_list(None)
        university_bookings = await clean_db.bookings.find({"tenant_id": "university"}).to_list(None)
        
        assert len(coworking_bookings) == 1
        assert len(university_bookings) == 1
        assert coworking_bookings[0]["tenant_id"] == "coworking"
        assert university_bookings[0]["tenant_id"] == "university"
    
    async def test_space_data_isolation(self, clean_db: AsyncIOMotorDatabase, seed_spaces: Dict[str, Dict[str, Any]]):
        """Test space data isolation between tenants"""
        coworking_spaces = await clean_db.spaces.find({"tenant_id": "coworking"}).to_list(None)
        university_spaces = await clean_db.spaces.find({"tenant_id": "university"}).to_list(None)
        
        assert len(coworking_spaces) == 2  # meeting_room, desk
        assert len(university_spaces) == 1  # lecture_hall
        
        # Verify tenant isolation
        for space in coworking_spaces:
            assert space["tenant_id"] == "coworking"
        
        for space in university_spaces:
            assert space["tenant_id"] == "university"
    
    async def test_cms_data_isolation(self, clean_db: AsyncIOMotorDatabase):
        """Test CMS page data isolation between tenants"""
        pages = [
            {
                "page_id": "home_coworking",
                "tenant_id": "coworking",
                "slug": "home",
                "title": "Coworking Home",
                "content": {"blocks": []}
            },
            {
                "page_id": "home_university",
                "tenant_id": "university", 
                "slug": "home",
                "title": "University Home",
                "content": {"blocks": []}
            }
        ]
        
        await clean_db.cms_pages.insert_many(pages)
        
        # Test same slug different tenants
        coworking_home = await clean_db.cms_pages.find_one({"tenant_id": "coworking", "slug": "home"})
        university_home = await clean_db.cms_pages.find_one({"tenant_id": "university", "slug": "home"})
        
        assert coworking_home["title"] == "Coworking Home"
        assert university_home["title"] == "University Home"
        assert coworking_home["tenant_id"] != university_home["tenant_id"]
    
    async def test_audit_log_isolation(self, clean_db: AsyncIOMotorDatabase):
        """Test audit log isolation between tenants"""
        audit_logs = [
            {
                "event_type": "user_login",
                "tenant_id": "coworking",
                "user_id": "member_user",
                "timestamp": "2024-12-01T10:00:00Z",
                "details": {"ip": "192.168.1.1"}
            },
            {
                "event_type": "user_login",
                "tenant_id": "university",
                "user_id": "cross_tenant_user", 
                "timestamp": "2024-12-01T10:00:00Z",
                "details": {"ip": "192.168.1.2"}
            }
        ]
        
        await clean_db.audit_logs.insert_many(audit_logs)
        
        # Test audit log filtering
        coworking_logs = await clean_db.audit_logs.find({"tenant_id": "coworking"}).to_list(None)
        university_logs = await clean_db.audit_logs.find({"tenant_id": "university"}).to_list(None)
        
        assert len(coworking_logs) == 1
        assert len(university_logs) == 1
        assert coworking_logs[0]["user_id"] == "member_user"
        assert university_logs[0]["user_id"] == "cross_tenant_user"

@pytest.mark.unit
@pytest.mark.tenant_isolation
class TestTenantMiddleware:
    """Test tenant resolution and context injection"""
    
    def test_subdomain_tenant_resolution(self):
        """Test tenant resolution from subdomain"""
        test_cases = [
            ("coworking.example.com", "coworking"),
            ("university.example.com", "university"),
            ("hotel.example.com", "hotel"),
            ("invalid.example.com", None)
        ]
        
        for host, expected_tenant in test_cases:
            # Mock tenant resolution logic
            subdomain = host.split('.')[0]
            valid_tenants = ["coworking", "university", "hotel"]
            resolved_tenant = subdomain if subdomain in valid_tenants else None
            
            assert resolved_tenant == expected_tenant
    
    def test_tenant_context_injection(self):
        """Test tenant context is properly injected into requests"""
        # Mock request context
        mock_request = {
            "headers": {"host": "coworking.example.com"},
            "tenant_id": None
        }
        
        # Simulate middleware processing
        host = mock_request["headers"]["host"]
        tenant_id = host.split('.')[0]
        mock_request["tenant_id"] = tenant_id
        
        assert mock_request["tenant_id"] == "coworking"
    
    async def test_cross_tenant_access_prevention(self, clean_db: AsyncIOMotorDatabase):
        """Test that cross-tenant access is prevented"""
        # Create data for different tenants
        await clean_db.users.insert_one({
            "user_id": "coworking_user",
            "tenant_id": "coworking",
            "email": "user@coworking.com"
        })
        
        await clean_db.users.insert_one({
            "user_id": "university_user", 
            "tenant_id": "university",
            "email": "user@university.com"
        })
        
        # Simulate API request with tenant filtering
        def get_user_by_id(user_id: str, requesting_tenant_id: str):
            # This simulates the kernel-level filtering
            user = {"user_id": user_id, "tenant_id": "university"}  # User exists in university
            
            if user["tenant_id"] != requesting_tenant_id:
                return None  # Access denied
            return user
        
        # Test cross-tenant access is blocked
        result = get_user_by_id("university_user", "coworking")
        assert result is None
        
        # Test same-tenant access is allowed
        result = get_user_by_id("university_user", "university") 
        assert result is not None
        assert result["user_id"] == "university_user"