#!/usr/bin/env python3
"""
Seed demo data for the Space Management Platform
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from passlib.context import CryptContext

from database.config.connection_pool import PostgreSQLConnectionManager

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Database connection
connection_manager = PostgreSQLConnectionManager()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_demo_data():
    print("🌱 Seeding demo data...")

    # Create demo tenant
    tenant_id = str(uuid.uuid4())
    tenant = {
        "id": tenant_id,
        "name": "Demo Coworking Space",
        "subdomain": "demo",
        "custom_domain": None,
        "plan": "premium",
        "is_active": True,
        "settings": {
            "timezone": "America/New_York",
            "business_hours": {
                "monday": {"open": "09:00", "close": "18:00"},
                "tuesday": {"open": "09:00", "close": "18:00"},
                "wednesday": {"open": "09:00", "close": "18:00"},
                "thursday": {"open": "09:00", "close": "18:00"},
                "friday": {"open": "09:00", "close": "18:00"},
                "saturday": {"open": "10:00", "close": "16:00"},
                "sunday": {"closed": True},
            },
        },
        "created_at": datetime.utcnow(),
    }

    from models.postgresql_models import Tenant

    async with connection_manager.get_session() as session:
        tenant_obj = Tenant(**tenant)
        session.add(tenant_obj)
        await session.commit()
    print(f"✅ Created tenant: {tenant['name']}")

    # Create demo users
    users = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": "admin@demo.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": "tenant_admin",
            "is_active": True,
            "membership_tier": None,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "password": "password123",
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": "staff@demo.com",
            "first_name": "Staff",
            "last_name": "Member",
            "role": "staff",
            "is_active": True,
            "membership_tier": None,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "password": "password123",
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": "john@demo.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "member",
            "is_active": True,
            "membership_tier": "premium",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "password": "password123",
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": "jane@demo.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": "member",
            "is_active": True,
            "membership_tier": "basic",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "password": "password123",
        },
    ]

    for user in users:
        password = user.pop("password")
        hashed_password = pwd_context.hash(password)

        from models.postgresql_models import User, UserPassword

        async with connection_manager.get_session() as session:
            user_obj = User(**user)
            session.add(user_obj)

            user_password = UserPassword(
                user_id=user["id"], hashed_password=hashed_password
            )
            session.add(user_password)
            await session.commit()

        print(f"✅ Created user: {user['email']} (role: {user['role']})")

    # Create demo resources
    resources = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Conference Room A",
            "type": "room",
            "parent_id": None,
            "capacity": 8,
            "amenities": ["Projector", "Whiteboard", "WiFi", "Video Conferencing"],
            "hourly_rate": 25.00,
            "is_bookable": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Conference Room B",
            "type": "room",
            "parent_id": None,
            "capacity": 12,
            "amenities": [
                "Projector",
                "Whiteboard",
                "WiFi",
                "Video Conferencing",
                "Catering Setup",
            ],
            "hourly_rate": 35.00,
            "is_bookable": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Hot Desk 1",
            "type": "desk",
            "parent_id": None,
            "capacity": 1,
            "amenities": ["WiFi", "Monitor", "Power Outlet"],
            "hourly_rate": 5.00,
            "is_bookable": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Hot Desk 2",
            "type": "desk",
            "parent_id": None,
            "capacity": 1,
            "amenities": ["WiFi", "Monitor", "Power Outlet"],
            "hourly_rate": 5.00,
            "is_bookable": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Phone Booth 1",
            "type": "room",
            "parent_id": None,
            "capacity": 1,
            "amenities": ["Soundproof", "WiFi", "Power Outlet"],
            "hourly_rate": 8.00,
            "is_bookable": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "3D Printer",
            "type": "equipment",
            "parent_id": None,
            "capacity": None,
            "amenities": ["PLA Filament", "ABS Filament", "Technical Support"],
            "hourly_rate": 15.00,
            "is_bookable": True,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Main Floor",
            "type": "floor",
            "parent_id": None,
            "capacity": 50,
            "amenities": ["Open Space", "Kitchen", "Lounge Area"],
            "hourly_rate": None,
            "is_bookable": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
    ]

    from models.postgresql_models import Resource

    async with connection_manager.get_session() as session:
        for resource in resources:
            resource_obj = Resource(**resource)
            session.add(resource_obj)
            await session.commit()
            print(f"✅ Created resource: {resource['name']} ({resource['type']})")

    # Create some demo bookings
    now = datetime.utcnow()
    bookings = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": users[2]["id"],  # John Doe
            "resource_id": resources[0]["id"],  # Conference Room A
            "start_time": now + timedelta(hours=2),
            "end_time": now + timedelta(hours=4),
            "status": "confirmed",
            "attendees": 5,
            "notes": "Weekly team meeting",
            "total_cost": 50.00,
            "created_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": users[3]["id"],  # Jane Smith
            "resource_id": resources[2]["id"],  # Hot Desk 1
            "start_time": now + timedelta(hours=1),
            "end_time": now + timedelta(hours=5),
            "status": "confirmed",
            "attendees": 1,
            "notes": "Working on project presentation",
            "total_cost": 20.00,
            "created_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": users[2]["id"],  # John Doe
            "resource_id": resources[1]["id"],  # Conference Room B
            "start_time": now - timedelta(hours=2),
            "end_time": now - timedelta(hours=1),
            "status": "confirmed",
            "attendees": 8,
            "notes": "Client presentation",
            "total_cost": 35.00,
            "created_at": now - timedelta(hours=3),
        },
    ]

    from models.postgresql_models import Booking

    async with connection_manager.get_session() as session:
        for booking in bookings:
            booking_obj = Booking(**booking)
            session.add(booking_obj)
            await session.commit()
            print(f"✅ Created booking: {booking['notes']}")

    print("\n🎉 Demo data seeded successfully!")
    print("\nDemo Login Credentials:")
    print("- Tenant: demo")
    print("- Admin: admin@demo.com / password123")
    print("- Staff: staff@demo.com / password123")
    print("- Member: john@demo.com / password123")
    print("- Member: jane@demo.com / password123")


async def main():
    await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(main())
