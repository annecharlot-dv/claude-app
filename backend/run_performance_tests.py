#!/usr/bin/env python3
"""
Performance Test Runner
Comprehensive performance testing suite for the Claude platform
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from database.config.connection_pool import PostgreSQLConnectionManager
from dotenv import load_dotenv
from performance.database_optimizer import get_db_optimizer
from performance.monitor import get_performance_monitor
from performance.test_suite import run_performance_tests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def setup_test_environment():
    """Setup test environment with sample data"""
    logger.info("Setting up test environment...")

    # Connect to PostgreSQL database
    connection_manager = PostgreSQLConnectionManager()

    # Initialize performance systems
    db_optimizer = await get_db_optimizer(connection_manager)
    monitor = await get_performance_monitor()
    await monitor.start_monitoring()

    # Create test data
    await create_test_data(connection_manager)

    return connection_manager


async def create_test_data(connection_manager):
    """Create test data for performance testing"""
    logger.info("Creating test data...")

    import uuid

    from models.postgresql_models import Lead, Page, Tenant, User
    from sqlalchemy import delete

    async with connection_manager.get_session() as session:
        # Clear existing test data
        await session.execute(delete(Lead).where(Lead.tenant_id == "test_tenant"))
        await session.execute(delete(Page).where(Page.tenant_id == "test_tenant"))
        await session.execute(delete(User).where(User.tenant_id == "test_tenant"))
        await session.execute(delete(Tenant).where(Tenant.id == "test_tenant"))
        await session.commit()

        # Create test tenant
        test_tenant = Tenant(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Test Tenant",
            subdomain="test",
            industry_module="coworking",
            is_active=True,
        )
        session.add(test_tenant)
        await session.commit()

        # Create test users
        for i in range(100):
            user = User(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                email=f"user{i}@test.com",
                first_name="User",
                last_name=str(i),
                role="member",
                is_active=True,
            )
            session.add(user)

        await session.commit()

        # Create test pages
        for i in range(50):
            page = Page(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                title=f"Test Page {i}",
                slug=f"test-page-{i}",
                status="published",
                content_blocks=[{"type": "text", "content": f"Content for page {i}"}],
            )
            session.add(page)

        await session.commit()

        # Create test leads
        for i in range(200):
            lead = Lead(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                first_name="Lead",
                last_name=str(i),
                email=f"lead{i}@test.com",
                status="new_inquiry" if i % 3 == 0 else "converted",
                source="website",
            )
            session.add(lead)

        await session.commit()
        logger.info("Test data created successfully")


async def cleanup_test_data(connection_manager):
    """Clean up test data"""
    logger.info("Cleaning up test data...")

    from models.postgresql_models import Tenant, User, Page, Lead
    from sqlalchemy import delete

    async with connection_manager.get_session() as session:
        await session.execute(delete(Lead).where(Lead.tenant_id == "test_tenant"))
        await session.execute(delete(Page).where(Page.tenant_id == "test_tenant"))
        await session.execute(delete(User).where(User.tenant_id == "test_tenant"))
        await session.execute(delete(Tenant).where(Tenant.id == "test_tenant"))
        await session.commit()

    logger.info("Test data cleaned up")


async def run_benchmark_tests(connection_manager):
    """Run comprehensive benchmark tests"""
    logger.info("Running benchmark tests...")

    # Run performance tests
    results = await run_performance_tests(connection_manager=connection_manager)

    # Generate detailed report
    report = {
        "test_summary": {
            "timestamp": results["timestamp"],
            "total_tests": len(
                results.get("tests", {}).get("database", {}).get("results", [])
            ),
            "environment": {
                "database": "PostgreSQL",
                "python_version": sys.version,
                "platform": sys.platform,
            },
        },
        "results": results,
    }

    return report


def print_performance_report(report):
    """Print formatted performance report"""
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST REPORT")
    print("=" * 80)

    summary = report["test_summary"]
    print(f"Timestamp: {summary['timestamp']}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Environment: {summary['environment']}")

    # Database test results
    if "database" in report["results"]["tests"]:
        db_results = report["results"]["tests"]["database"]
        print(f"\nDatabase Tests: {db_results['summary']['total_tests']}")
        print(f"Passed: {db_results['summary']['passed']}")
        print(f"Failed: {db_results['summary']['failed']}")
        print(f"Pass Rate: {db_results['summary']['pass_rate']:.1f}%")

        print("\nDetailed Results:")
        print("-" * 60)
        for result in db_results["results"]:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(
                f"{status_icon} {result['test_name']:<30} {result['avg_time_ms']:>8.2f}ms"
            )
            if result["status"] == "FAIL":
                print(
                    f"   └─ P95: {result['p95_time_ms']:.2f}ms, Success: {result['success_rate']:.1f}%"
                )

    print("\n" + "=" * 80)


async def main():
    """Main test runner"""
    try:
        # Setup test environment
        connection_manager = await setup_test_environment()

        # Run benchmark tests
        report = await run_benchmark_tests(connection_manager)

        # Print results
        print_performance_report(report)

        # Save report to file
        import json
        from datetime import datetime

        filename = (
            f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\nDetailed report saved to: {filename}")

        # Determine exit code based on results
        if "database" in report["results"]["tests"]:
            db_results = report["results"]["tests"]["database"]
            if db_results["summary"]["pass_rate"] < 100:
                print(
                    f"\n⚠️  Some tests failed. Pass rate: {db_results['summary']['pass_rate']:.1f}%"
                )
                return 1

        print("\n✅ All performance tests passed!")
        return 0

    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return 1

    finally:
        # Cleanup
        try:
            await cleanup_test_data(connection_manager)
        except:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
