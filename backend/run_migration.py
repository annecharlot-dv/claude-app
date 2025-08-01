#!/usr/bin/env python3
"""
Run PostgreSQL database migration
"""
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import text

from database.postgresql_connection import get_connection_manager
from models.postgresql_models import Base

# Add backend to path
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Run the database migration"""
    try:
        # Initialize connection manager
        connection_manager = await get_connection_manager()
        await connection_manager.initialize()

        logger.info("🔄 Starting PostgreSQL migration...")

        # Create all tables
        async with connection_manager.get_session() as session:
            # Create tables using SQLAlchemy
            async with connection_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("✅ Database tables created successfully")

            # Enable RLS and create policies
            await session.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
            await session.execute(text("ALTER TABLE pages ENABLE ROW LEVEL SECURITY"))
            await session.execute(text("ALTER TABLE leads ENABLE ROW LEVEL SECURITY"))
            await session.execute(text("ALTER TABLE forms ENABLE ROW LEVEL SECURITY"))
            await session.execute(text("ALTER TABLE widgets ENABLE ROW LEVEL SECURITY"))
            await session.execute(
                text("ALTER TABLE tour_slots ENABLE ROW LEVEL SECURITY")
            )
            await session.execute(text("ALTER TABLE tours ENABLE ROW LEVEL SECURITY"))

            logger.info("✅ Row-Level Security enabled")

            # Create application role
            try:
                await session.execute(text("CREATE ROLE application_role"))
                await session.execute(
                    text("GRANT USAGE ON SCHEMA public TO application_role")
                )
                await session.execute(
                    text(
                        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                        "IN SCHEMA public TO application_role"
                    )
                )
                await session.execute(
                    text(
                        "GRANT USAGE, SELECT ON ALL SEQUENCES "
                        "IN SCHEMA public TO application_role"
                    )
                )
                logger.info("✅ Application role created")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("ℹ️ Application role already exists")
                else:
                    raise

            # Create RLS policies
            policies = [
                """
                CREATE POLICY tenant_isolation_users ON users
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
                """
                CREATE POLICY tenant_isolation_pages ON pages
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
                """
                CREATE POLICY tenant_isolation_leads ON leads
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
                """
                CREATE POLICY tenant_isolation_forms ON forms
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
                """
                CREATE POLICY tenant_isolation_widgets ON widgets
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
                """
                CREATE POLICY tenant_isolation_tour_slots ON tour_slots
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
                """
                CREATE POLICY tenant_isolation_tours ON tours
                    FOR ALL TO application_role
                    USING (tenant_id = current_setting(
                        'app.current_tenant_id')::uuid)
                """,
            ]

            for policy in policies:
                try:
                    await session.execute(text(policy))
                except Exception as e:
                    if "already exists" in str(e):
                        logger.info(f"ℹ️ Policy already exists: {policy.split()[2]}")
                    else:
                        logger.warning(f"⚠️ Failed to create policy: {e}")

            logger.info("✅ RLS policies created")

            # Create search function and trigger for pages
            search_function = """
                CREATE OR REPLACE FUNCTION update_page_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector := to_tsvector('english',
                        COALESCE(NEW.title, '') || ' ' ||
                        COALESCE(NEW.meta_description, '') || ' ' ||
                        COALESCE(NEW.search_keywords, '')
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """

            search_trigger = """
                CREATE TRIGGER update_pages_search_vector
                    BEFORE INSERT OR UPDATE ON pages
                    FOR EACH ROW EXECUTE FUNCTION update_page_search_vector();
            """

            try:
                await session.execute(text(search_function))
                await session.execute(text(search_trigger))
                logger.info("✅ Full-text search setup completed")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("ℹ️ Search function/trigger already exists")
                else:
                    logger.warning(f"⚠️ Failed to create search setup: {e}")

            await session.commit()

        logger.info("🎉 PostgreSQL migration completed successfully!")

        # Test connection
        async with connection_manager.get_session() as session:
            result = await session.execute(text("SELECT 1 as test"))
            test_result = result.scalar()
            logger.info(f"🔍 Connection test: {test_result}")

        await connection_manager.close()

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_migration())
