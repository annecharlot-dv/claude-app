#!/usr/bin/env python3
"""
Performance Test Runner
Comprehensive performance testing suite for the Claude platform
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from performance.test_suite import run_performance_tests
from performance.database_optimizer import get_db_optimizer
from performance.monitor import get_performance_monitor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_test_environment():
    """Setup test environment with sample data"""
    logger.info("Setting up test environment...")
    
    # Connect to database
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'claude_test')]
    
    # Initialize performance systems
    db_optimizer = await get_db_optimizer(db)
    monitor = await get_performance_monitor()
    await monitor.start_monitoring()
    
    # Create test data
    await create_test_data(db)
    
    return db, client

async def create_test_data(db):
    """Create test data for performance testing"""
    logger.info("Creating test data...")
    
    # Create test tenant
    test_tenant = {
        "id": "test_tenant",
        "name": "Test Tenant",
        "subdomain": "test",
        "industry_module": "coworking",
        "is_active": True
    }
    await db.tenants.replace_one({"id": "test_tenant"}, test_tenant, upsert=True)
    
    # Create test users
    test_users = []
    for i in range(100):
        user = {
            "id": f"user_{i}",
            "tenant_id": "test_tenant",
            "email": f"user{i}@test.com",
            "first_name": f"User",
            "last_name": f"{i}",
            "role": "member",
            "is_active": True
        }
        test_users.append(user)
    
    await db.users.delete_many({"tenant_id": "test_tenant"})
    await db.users.insert_many(test_users)
    
    # Create test pages
    test_pages = []
    for i in range(50):
        page = {
            "id": f"page_{i}",
            "tenant_id": "test_tenant",
            "title": f"Test Page {i}",
            "slug": f"test-page-{i}",
            "status": "published",
            "content_blocks": [{"type": "text", "content": f"Content for page {i}"}],
            "searchKeywords": f"test page {i} content"
        }
        test_pages.append(page)
    
    await db.pages.delete_many({"tenant_id": "test_tenant"})
    await db.pages.insert_many(test_pages)
    
    # Create test leads
    test_leads = []
    for i in range(200):
        lead = {
            "id": f"lead_{i}",
            "tenant_id": "test_tenant",
            "first_name": f"Lead",
            "last_name": f"{i}",
            "email": f"lead{i}@test.com",
            "status": "new_inquiry" if i % 3 == 0 else "converted",
            "source": "website"
        }
        test_leads.append(lead)
    
    await db.leads.delete_many({"tenant_id": "test_tenant"})
    await db.leads.insert_many(test_leads)
    
    logger.info("Test data created successfully")

async def cleanup_test_data(db):
    """Clean up test data"""
    logger.info("Cleaning up test data...")
    
    await db.tenants.delete_many({"id": "test_tenant"})
    await db.users.delete_many({"tenant_id": "test_tenant"})
    await db.pages.delete_many({"tenant_id": "test_tenant"})
    await db.leads.delete_many({"tenant_id": "test_tenant"})
    
    logger.info("Test data cleaned up")

async def run_benchmark_tests(db):
    """Run comprehensive benchmark tests"""
    logger.info("Running benchmark tests...")
    
    # Run performance tests
    results = await run_performance_tests(db=db)
    
    # Generate detailed report
    report = {
        "test_summary": {
            "timestamp": results["timestamp"],
            "total_tests": len(results.get("tests", {}).get("database", {}).get("results", [])),
            "environment": {
                "database": "MongoDB",
                "python_version": sys.version,
                "platform": sys.platform
            }
        },
        "results": results
    }
    
    return report

def print_performance_report(report):
    """Print formatted performance report"""
    print("\n" + "="*80)
    print("PERFORMANCE TEST REPORT")
    print("="*80)
    
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
            print(f"{status_icon} {result['test_name']:<30} {result['avg_time_ms']:>8.2f}ms")
            if result["status"] == "FAIL":
                print(f"   └─ P95: {result['p95_time_ms']:.2f}ms, Success: {result['success_rate']:.1f}%")
    
    print("\n" + "="*80)

async def main():
    """Main test runner"""
    try:
        # Setup test environment
        db, client = await setup_test_environment()
        
        # Run benchmark tests
        report = await run_benchmark_tests(db)
        
        # Print results
        print_performance_report(report)
        
        # Save report to file
        import json
        from datetime import datetime
        
        filename = f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {filename}")
        
        # Determine exit code based on results
        if "database" in report["results"]["tests"]:
            db_results = report["results"]["tests"]["database"]
            if db_results["summary"]["pass_rate"] < 100:
                print(f"\n⚠️  Some tests failed. Pass rate: {db_results['summary']['pass_rate']:.1f}%")
                return 1
        
        print("\n✅ All performance tests passed!")
        return 0
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return 1
        
    finally:
        # Cleanup
        try:
            await cleanup_test_data(db)
            client.close()
        except:
            pass

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)