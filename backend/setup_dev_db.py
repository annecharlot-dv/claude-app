#!/usr/bin/env python3
"""
Development Database Setup
Creates a SQLite database for local development and testing
"""
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from models.postgresql_models import Base

# Add backend to path
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_development_database():
    """Set up SQLite database for development"""

    # Use SQLite for development
    db_path = Path(__file__).parent / "claude_platform_dev.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"

    logger.info(f"Setting up development database at: {db_path}")

    try:
        # Create async engine for SQLite
        engine = create_async_engine(
            database_url, echo=True, future=True  # Show SQL queries in development
        )

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables created successfully")

        # Create sample data
        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        await create_sample_data(async_session_factory)

        logger.info("✅ Sample data created successfully")
        logger.info(f"✅ Development database ready at: {db_path}")

        # Update .env file
        env_path = Path(__file__).parent / ".env"
        update_env_file(env_path, database_url)

        return True

    except Exception as e:
        logger.error(f"❌ Failed to set up database: {e}")
        return False


async def create_sample_data(session_factory):
    """Create sample tenant and user data"""
    import uuid
    from datetime import datetime

    from passlib.context import CryptContext

    from models.cross_db_models import Tenant, User

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with session_factory() as session:
        # Create sample tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Demo Coworking Space",
            subdomain="demo",
            custom_domain=None,
            industry_module="coworking",
            plan="professional",
            is_active=True,
            branding={
                "primary_color": "#3B82F6",
                "logo_url": "/images/demo-logo.png",
                "company_name": "Demo Coworking",
            },
            settings={
                "timezone": "America/New_York",
                "currency": "USD",
                "booking_advance_days": 30,
            },
            feature_toggles={
                "website_builder": True,
                "lead_management": True,
                "booking_system": True,
                "community_platform": True,
                "events_system": True,
            },
            created_at=datetime.utcnow(),
        )
        session.add(tenant)
        await session.flush()  # Get the tenant ID

        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="admin@demo.com",
            first_name="Admin",
            last_name="User",
            role="account_owner",
            is_active=True,
            hashed_password=pwd_context.hash("admin123"),
            profile={"phone": "+1-555-0123", "department": "Management"},
            created_at=datetime.utcnow(),
            last_login=None,
        )
        session.add(admin_user)

        # Create property manager
        manager_user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="manager@demo.com",
            first_name="Property",
            last_name="Manager",
            role="property_manager",
            is_active=True,
            hashed_password=pwd_context.hash("manager123"),
            profile={"phone": "+1-555-0124", "department": "Operations"},
            created_at=datetime.utcnow(),
            last_login=None,
        )
        session.add(manager_user)

        # Create front desk user
        frontdesk_user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="frontdesk@demo.com",
            first_name="Front",
            last_name="Desk",
            role="front_desk",
            is_active=True,
            hashed_password=pwd_context.hash("frontdesk123"),
            profile={"phone": "+1-555-0125", "department": "Customer Service"},
            created_at=datetime.utcnow(),
            last_login=None,
        )
        session.add(frontdesk_user)

        await session.commit()

        logger.info("Sample users created:")
        logger.info("  - admin@demo.com / admin123 (Account Owner)")
        logger.info("  - manager@demo.com / manager123 (Property Manager)")
        logger.info("  - frontdesk@demo.com / frontdesk123 (Front Desk)")


def update_env_file(env_path: Path, database_url: str):
    """Update .env file with development database URL"""
    if env_path.exists():
        content = env_path.read_text()
        lines = content.split("\n")

        # Update or add DATABASE_URL
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("DATABASE_URL="):
                lines[i] = f'DATABASE_URL="{database_url}"'
                updated = True
                break

        if not updated:
            lines.append(f'DATABASE_URL="{database_url}"')

        env_path.write_text("\n".join(lines))
        logger.info(f"✅ Updated {env_path} with development database URL")


if __name__ == "__main__":
    success = asyncio.run(setup_development_database())
    if success:
        print("\n🎉 Development database setup complete!")
        print("You can now run the application with:")
        print("  uvicorn server:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n❌ Database setup failed. Check the logs above.")
        sys.exit(1)
