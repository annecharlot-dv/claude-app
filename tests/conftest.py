"""
Pytest configuration and shared fixtures for multi-tenant testing
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator, Dict, Any
from database.config.connection_pool import PostgreSQLConnectionManager
from models.postgresql_models import Base, Tenant, User, Page, Lead, Form, Tour, TourSlot
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Test database configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/claude_platform_test")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database connection"""
    engine = create_async_engine(TEST_DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from sqlalchemy.ext.asyncio import async_sessionmaker
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    # Cleanup after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def clean_db(test_db: AsyncSession):
    """Clean database before each test"""
    from sqlalchemy import delete
    await test_db.execute(delete(Tour))
    await test_db.execute(delete(TourSlot))
    await test_db.execute(delete(Lead))
    await test_db.execute(delete(Form))
    await test_db.execute(delete(Page))
    await test_db.execute(delete(User))
    await test_db.execute(delete(Tenant))
    await test_db.commit()
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
async def seed_tenants(clean_db: AsyncSession, test_tenants: Dict[str, Dict[str, Any]]):
    """Seed test tenants"""
    for tenant_data in test_tenants.values():
        tenant = Tenant(**tenant_data)
        clean_db.add(tenant)
    await clean_db.commit()
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
async def seed_users(clean_db: AsyncSession, test_users: Dict[str, Dict[str, Any]]):
    """Seed test users"""
    for user_data in test_users.values():
        user = User(**user_data)
        clean_db.add(user)
    await clean_db.commit()
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
async def seed_spaces(clean_db: AsyncSession, test_spaces: Dict[str, Dict[str, Any]]):
    """Seed test spaces"""
    for space_data in test_spaces.values():
        space = Page(**space_data)
        clean_db.add(space)
    await clean_db.commit()
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
