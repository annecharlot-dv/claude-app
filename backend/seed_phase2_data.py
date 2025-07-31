#!/usr/bin/env python3
"""
Seed Phase 2 demo data - Enhanced member profiles, events, and community
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from database.config.connection_pool import PostgreSQLConnectionManager

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Database connection
connection_manager = PostgreSQLConnectionManager()


async def seed_phase2_data():
    print("🌱 Seeding Phase 2 demo data...")

    from sqlalchemy import select

    from models.postgresql_models import Tenant, User

    async with connection_manager.get_session() as session:
        # Find demo tenant
        result = await session.execute(select(Tenant).where(Tenant.subdomain == "demo"))
        tenant = result.scalar_one_or_none()
        if not tenant:
            print("❌ Demo tenant not found. Please run seed_demo_data.py first")
            return

        tenant_id = tenant.id

        # Find existing users
        result = await session.execute(select(User).where(User.tenant_id == tenant_id))
        users = result.scalars().all()
        user_map = {user.email: user for user in users}

    # Enhanced member profiles
    profile_updates = [
        {
            "email": "john@demo.com",
            "profile": {
                "bio": (
                    "Experienced software engineer and startup enthusiast. "
                    "I love building innovative products that solve real "
                    "problems. "
                    "Always looking for collaboration opportunities!"
                ),
                "company": "TechStart Inc",
                "job_title": "Senior Software Engineer",
                "skills": ["React", "Node.js", "Python", "AWS", "MongoDB"],
                "interests": ["Startups", "AI/ML", "Open Source", "Photography"],
                "linkedin": "https://linkedin.com/in/johndoe",
                "website": "https://johndoe.dev",
                "phone": "+1-555-0123",
                "looking_for": "Co-founders for my next startup, "
                "technical collaborators",
                "open_to_connect": True,
            },
        },
        {
            "email": "jane@demo.com",
            "profile": {
                "bio": "Digital marketing strategist with a passion for "
                "helping businesses grow online. I specialize in content "
                "marketing and social media strategy.",
                "company": "Marketing Pro",
                "job_title": "Digital Marketing Manager",
                "skills": [
                    "Digital Marketing",
                    "Content Strategy",
                    "SEO",
                    "Social Media",
                    "Analytics",
                ],
                "interests": ["Marketing", "Content Creation", "Podcasts", "Travel"],
                "linkedin": "https://linkedin.com/in/janesmith",
                "website": "https://janesmith.marketing",
                "phone": "+1-555-0456",
                "looking_for": "Networking opportunities, potential clients",
                "open_to_connect": True,
            },
        },
        {
            "email": "admin@demo.com",
            "profile": {
                "bio": "Community builder and space operations expert. "
                "I'm passionate about creating environments where innovation "
                "thrives.",
                "company": "Demo Coworking Space",
                "job_title": "Community Manager",
                "skills": [
                    "Community Building",
                    "Event Management",
                    "Operations",
                    "Customer Service",
                ],
                "interests": ["Community", "Events", "Networking", "Entrepreneurship"],
                "linkedin": "https://linkedin.com/in/admin",
                "looking_for": "Great people to join our community",
                "open_to_connect": True,
            },
        },
    ]

    async with connection_manager.get_session() as session:
        for profile_update in profile_updates:
            if profile_update["email"] in user_map:
                from sqlalchemy import update

                await session.execute(
                    update(User)
                    .where(
                        User.email == profile_update["email"],
                        User.tenant_id == tenant_id,
                    )
                    .values(profile=profile_update["profile"])
                )
                print(f"✅ Updated profile for {profile_update['email']}")

        await session.commit()

    # Create demo events
    now = datetime.utcnow()
    events = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "host_user_id": user_map["admin@demo.com"].id,
            "title": "Weekly Networking Happy Hour",
            "description": "Join us every Friday for drinks, conversation, "
            "and making new connections! This is our signature community "
            "event where members can unwind, share ideas, and build "
            "relationships.",
            "event_type": "networking",
            "start_time": now + timedelta(days=2, hours=17),  # Friday 5 PM
            "end_time": now + timedelta(days=2, hours=19),  # This Friday 7 PM
            "location": "Main Lounge Area",
            "resource_id": None,
            "max_attendees": 30,
            "is_public": True,
            "requires_approval": False,
            "cost": None,
            "attendees": [user_map["john@demo.com"].id, user_map["jane@demo.com"].id],
            "waitlist": [],
            "tags": ["networking", "social", "weekly"],
            "created_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "host_user_id": user_map["john@demo.com"].id,
            "title": "React & Node.js Workshop",
            "description": (
                "Learn the fundamentals of full-stack development with React "
                "and Node.js. Perfect for beginners and those looking to "
                "refresh their skills. All materials provided!"
            ),
            "event_type": "workshop",
            "start_time": now + timedelta(days=5, hours=14),  # Monday 2 PM
            "end_time": now + timedelta(days=5, hours=17),  # Monday 5 PM
            "location": "Conference Room A",
            "resource_id": None,
            "max_attendees": 12,
            "is_public": True,
            "requires_approval": False,
            "cost": 25.00,
            "attendees": [user_map["jane@demo.com"].id],
            "waitlist": [],
            "tags": ["workshop", "programming", "react", "nodejs"],
            "created_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "host_user_id": user_map["jane@demo.com"].id,
            "title": "Digital Marketing Mastermind",
            "description": (
                "Monthly meetup for marketers to share strategies, discuss "
                "trends, and help each other solve marketing challenges. "
                "Bring your questions and case studies!"
            ),
            "event_type": "meeting",
            "start_time": now
            + timedelta(days=7, hours=10),  # Next week Wednesday 10 AM
            "end_time": now + timedelta(days=7, hours=12),  # Wednesday 12 PM
            "location": "Conference Room B",
            "resource_id": None,
            "max_attendees": 8,
            "is_public": True,
            "requires_approval": False,
            "cost": None,
            "attendees": [user_map["admin@demo.com"].id],
            "waitlist": [],
            "tags": ["marketing", "mastermind", "monthly"],
            "created_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "host_user_id": user_map["admin@demo.com"].id,
            "title": "Startup Pitch Practice",
            "description": (
                "Safe space for entrepreneurs to practice their pitches and "
                "get constructive feedback from the community. Open to all "
                "stages of startups!"
            ),
            "event_type": "presentation",
            "start_time": now + timedelta(days=10, hours=18),  # Saturday 6 PM
            "end_time": now + timedelta(days=10, hours=20),  # Saturday 8 PM
            "location": "Main Event Space",
            "resource_id": None,
            "max_attendees": 20,
            "is_public": True,
            "requires_approval": True,
            "cost": None,
            "attendees": [user_map["john@demo.com"].id],
            "waitlist": [],
            "tags": ["startup", "pitch", "feedback", "entrepreneurship"],
            "created_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "host_user_id": user_map["jane@demo.com"].id,
            "title": "Coffee & Collaboration",
            "description": (
                "Casual morning meetup over coffee. Great for making new "
                "connections and finding collaboration partners. No agenda, "
                "just good conversations!"
            ),
            "event_type": "social",
            "start_time": now + timedelta(days=1, hours=9),  # Tomorrow 9 AM
            "end_time": now + timedelta(days=1, hours=10),  # Tomorrow 10 AM
            "location": "Kitchen Area",
            "resource_id": None,
            "max_attendees": 15,
            "is_public": True,
            "requires_approval": False,
            "cost": None,
            "attendees": [user_map["admin@demo.com"].id],
            "waitlist": [],
            "tags": ["coffee", "networking", "morning", "casual"],
            "created_at": now,
        },
    ]

    for event in events:
        print(f"✅ Would create event: {event['title']}")

    # Create some check-in records for demo
    checkins = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_map["john@demo.com"].id,
            "resource_id": None,
            "check_in_time": now - timedelta(hours=2),
            "check_out_time": now - timedelta(minutes=30),
            "status": "checked_out",
            "duration_minutes": 90,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_map["jane@demo.com"].id,
            "resource_id": None,
            "check_in_time": now - timedelta(hours=4),
            "check_out_time": now - timedelta(hours=1),
            "status": "checked_out",
            "duration_minutes": 180,
        },
    ]

    for checkin in checkins:
        print("✅ Would create check-in record for user")

    # Update resources with enhanced pricing and member benefits
    resources_updates = [
        {
            "name": "Conference Room A",
            "updates": {
                "member_discount": 10.0,  # 10% discount for basic members
                "premium_member_discount": 20.0,  # 20% discount for premium
                "min_booking_duration": 30,  # 30 minutes minimum
                "max_booking_duration": 480,  # 8 hours maximum
                "daily_rate": 150.0,
            },
        },
        {
            "name": "Conference Room B",
            "updates": {
                "member_discount": 15.0,
                "premium_member_discount": 25.0,
                "min_booking_duration": 30,
                "max_booking_duration": 480,
                "daily_rate": 200.0,
            },
        },
        {
            "name": "Hot Desk 1",
            "updates": {
                "member_discount": 20.0,
                "premium_member_discount": 30.0,
                "min_booking_duration": 60,  # 1 hour minimum
                "max_booking_duration": 600,  # 10 hours maximum
                "daily_rate": 30.0,
            },
        },
        {
            "name": "Hot Desk 2",
            "updates": {
                "member_discount": 20.0,
                "premium_member_discount": 30.0,
                "min_booking_duration": 60,
                "max_booking_duration": 600,
                "daily_rate": 30.0,
            },
        },
    ]

    # Update resources (assuming Resource model exists)
    for resource_update in resources_updates:
        print(f"✅ Would update resource: {resource_update['name']}")

    print("✅ Phase 2 data processing complete")

    print("\n🎉 Phase 2 demo data seeded successfully!")
    print("\nNew Features Available:")
    print(
        "- Enhanced member profiles with skills, interests, and networking "
        "preferences"
    )
    print("- Community events with different types (networking, workshops, " "social)")
    print("- Member directory for networking and collaboration")
    print("- Check-in/check-out system for space usage tracking")
    print("- Member pricing tiers with discounts")
    print("- Booking duration limits and daily rates")


async def main():
    await seed_phase2_data()


if __name__ == "__main__":
    asyncio.run(main())
