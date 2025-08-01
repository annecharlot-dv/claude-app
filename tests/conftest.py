"""
Pytest configuration and shared fixtures for multi-tenant testing
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import jwt
from datetime import datetime, timedelta

# Test database configuration
TEST_DB_URL = os.getenv("TEST_MONGO_URL", "mongodb://localhost:27017")
TEST_DB_NAME = "claude_platform_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Create test database connection"""
    client = AsyncIOMotorClient(TEST_DB_URL)
    db = client[TEST_DB_NAME]
    
    # Clean up any existing test data
    await db.drop_collection("users")
    await db.drop_collection("tenants")
    await db.drop_collection("bookings")
    await db.drop_collection("spaces")
    await db.drop_collection("audit_logs")
    await db.drop_collection("cms_pages")
    
    yield db
    
    # Cleanup after tests
    await client.drop_database(TEST_DB_NAME)
    client.close()

@pytest.fixture
async def clean_db(test_db: AsyncIOMotorDatabase):
    """Clean database before each test"""
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    yield test_db

@pytest.fixture
def test_tenants() -> Dict[str, Dict[str, Any]]:
    """Test tenant configurations"""
    return {
        "coworking": {
            "tenant_id": "coworking",
            "name": "Test Coworking Space",
            "subdomain": "coworking",
            "module": "coworking_module",
            "settings": {
                "booking_advance_days": 30,
                "cancellation_hours": 24,
                "max_booking_duration": 480
            }
        },
        "university": {
            "tenant_id": "university",
            "name": "Test University",
            "subdomain": "university", 
            "module": "university_module",
            "settings": {
                "booking_advance_days": 90,
                "cancellation_hours": 48,
                "max_booking_duration": 240
            }
        },
        "hotel": {
            "tenant_id": "hotel",
            "name": "Test Hotel",
            "subdomain": "hotel",
            "module": "hotel_module",
            "settings": {
                "booking_advance_days": 365,
                "cancellation_hours": 72,
                "max_booking_duration": 1440
            }
        }
    }

@pytest.fixture
async def seed_tenants(clean_db: AsyncIOMotorDatabase, test_tenants: Dict[str, Dict[str, Any]]):
    """Seed test tenants"""
    for tenant_data in test_tenants.values():
        await clean_db.tenants.insert_one(tenant_data)
    return test_tenants

@pytest.fixture
def test_users() -> Dict[str, Dict[str, Any]]:
    """Test user configurations"""
    return {
        "admin": {
            "user_id": "admin_user",
            "email": "admin@test.com",
            "tenant_id": "coworking",
            "role": "admin",
            "password_hash": "$2b$12$test_hash",
            "active": True
        },
        "manager": {
            "user_id": "manager_user", 
            "email": "manager@test.com",
            "tenant_id": "coworking",
            "role": "property_manager",
            "password_hash": "$2b$12$test_hash",
            "active": True
        },
        "member": {
            "user_id": "member_user",
            "email": "member@test.com", 
            "tenant_id": "coworking",
            "role": "member",
            "password_hash": "$2b$12$test_hash",
            "active": True
        },
        "cross_tenant": {
            "user_id": "cross_tenant_user",
            "email": "cross@test.com",
            "tenant_id": "university",
            "role": "member", 
            "password_hash": "$2b$12$test_hash",
            "active": True
        }
    }

@pytest.fixture
async def seed_users(clean_db: AsyncIOMotorDatabase, test_users: Dict[str, Dict[str, Any]]):
    """Seed test users"""
    for user_data in test_users.values():
        await clean_db.users.insert_one(user_data)
    return test_users

@pytest.fixture
def jwt_secret() -> str:
    """JWT secret for testing"""
    return "test_secret_key_for_jwt_tokens"

@pytest.fixture
def create_jwt_token(jwt_secret: str):
    """Factory for creating JWT tokens"""
    def _create_token(user_id: str, tenant_id: str, role: str, expires_delta: timedelta = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, jwt_secret, algorithm="HS256")
    
    return _create_token

@pytest.fixture
def auth_headers(create_jwt_token):
    """Factory for creating authentication headers"""
    def _create_headers(user_id: str, tenant_id: str, role: str) -> Dict[str, str]:
        token = create_jwt_token(user_id, tenant_id, role)
        return {"Authorization": f"Bearer {token}"}
    
    return _create_headers

@pytest.fixture
def test_spaces() -> Dict[str, Dict[str, Any]]:
    """Test space configurations"""
    return {
        "meeting_room": {
            "space_id": "meeting_room_1",
            "tenant_id": "coworking",
            "name": "Meeting Room A",
            "capacity": 8,
            "hourly_rate": 25.00,
            "amenities": ["projector", "whiteboard", "wifi"],
            "active": True
        },
        "desk": {
            "space_id": "desk_1", 
            "tenant_id": "coworking",
            "name": "Hot Desk 1",
            "capacity": 1,
            "hourly_rate": 5.00,
            "amenities": ["wifi", "power"],
            "active": True
        },
        "university_room": {
            "space_id": "lecture_hall_1",
            "tenant_id": "university",
            "name": "Lecture Hall A",
            "capacity": 100,
            "hourly_rate": 50.00,
            "amenities": ["projector", "microphone", "wifi"],
            "active": True
        }
    }

@pytest.fixture
async def seed_spaces(clean_db: AsyncIOMotorDatabase, test_spaces: Dict[str, Dict[str, Any]]):
    """Seed test spaces"""
    for space_data in test_spaces.values():
        await clean_db.spaces.insert_one(space_data)
    return test_spaces

@pytest.fixture
def mock_external_services():
    """Mock external service dependencies"""
    return {
        "payment_gateway": AsyncMock(),
        "email_service": AsyncMock(),
        "sms_service": AsyncMock(),
        "storage_service": AsyncMock()
    }

@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """Performance testing thresholds"""
    return {
        "api_response_time_ms": 100,
        "database_query_time_ms": 50,
        "page_load_time_ms": 2000,
        "concurrent_users": 100,
        "requests_per_second": 1000
    }

# Pytest markers for test categorization
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "tenant_isolation: Multi-tenant isolation tests")
    config.addinivalue_line("markers", "slow: Slow running tests")