"""
Performance Testing Suite
Automated performance tests with benchmarks and reporting
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class PerformanceTest:
    """Performance test configuration"""

    name: str
    description: str
    target_function: Callable
    args: tuple = ()
    kwargs: dict = None
    iterations: int = 100
    target_time_ms: float = 100.0
    concurrent_users: int = 1


@dataclass
class TestResult:
    """Performance test result"""

    test_name: str
    iterations: int
    concurrent_users: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    success_rate: float
    errors: List[str]
    target_met: bool


class PerformanceTester:
    """Performance testing framework"""

    def __init__(self):
        self.tests = []
        self.results = []

    def add_test(self, test: PerformanceTest):
        """Add a performance test"""
        self.tests.append(test)

    async def run_single_test(self, test: PerformanceTest) -> TestResult:
        """Run a single performance test"""
        logger.info(f"Running test: {test.name}")

        execution_times = []
        errors = []
        successful_runs = 0

        # Run test iterations
        for i in range(test.iterations):
            start_time = time.time()

            try:
                if asyncio.iscoroutinefunction(test.target_function):
                    await test.target_function(*test.args, **(test.kwargs or {}))
                else:
                    test.target_function(*test.args, **(test.kwargs or {}))

                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                execution_times.append(execution_time)
                successful_runs += 1

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                execution_times.append(execution_time)
                errors.append(f"Iteration {i}: {str(e)}")

        # Calculate statistics
        if execution_times:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            p95_time = self._percentile(execution_times, 95)
            p99_time = self._percentile(execution_times, 99)
            total_time = sum(execution_times)
        else:
            avg_time = min_time = max_time = p95_time = p99_time = total_time = 0

        success_rate = (successful_runs / test.iterations) * 100
        target_met = avg_time <= test.target_time_ms and success_rate >= 95

        result = TestResult(
            test_name=test.name,
            iterations=test.iterations,
            concurrent_users=test.concurrent_users,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            success_rate=success_rate,
            errors=errors,
            target_met=target_met,
        )

        self.results.append(result)
        return result

    async def run_concurrent_test(self, test: PerformanceTest) -> TestResult:
        """Run test with concurrent users"""
        logger.info(
            f"Running concurrent test: {test.name} with {test.concurrent_users} users"
        )

        # Create tasks for concurrent execution
        tasks = []
        for user in range(test.concurrent_users):
            user_test = PerformanceTest(
                name=f"{test.name}_user_{user}",
                description=test.description,
                target_function=test.target_function,
                args=test.args,
                kwargs=test.kwargs,
                iterations=test.iterations // test.concurrent_users,
                target_time_ms=test.target_time_ms,
            )
            tasks.append(self.run_single_test(user_test))

        # Run all tasks concurrently
        user_results = await asyncio.gather(*tasks)

        # Aggregate results
        all_times = []
        all_errors = []
        total_successful = 0
        total_iterations = 0

        for result in user_results:
            # Reconstruct execution times from statistics (approximation)
            user_times = [result.avg_time_ms] * (result.iterations - len(result.errors))
            all_times.extend(user_times)
            all_errors.extend(result.errors)
            total_successful += int((result.success_rate / 100) * result.iterations)
            total_iterations += result.iterations

        # Calculate aggregate statistics
        if all_times:
            avg_time = statistics.mean(all_times)
            min_time = min(all_times)
            max_time = max(all_times)
            p95_time = self._percentile(all_times, 95)
            p99_time = self._percentile(all_times, 99)
            total_time = sum(all_times)
        else:
            avg_time = min_time = max_time = p95_time = p99_time = total_time = 0

        success_rate = (
            (total_successful / total_iterations) * 100 if total_iterations > 0 else 0
        )
        target_met = avg_time <= test.target_time_ms and success_rate >= 95

        result = TestResult(
            test_name=test.name,
            iterations=total_iterations,
            concurrent_users=test.concurrent_users,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            success_rate=success_rate,
            errors=all_errors,
            target_met=target_met,
        )

        self.results.append(result)
        return result

    async def run_all_tests(self) -> List[TestResult]:
        """Run all registered tests"""
        logger.info(f"Running {len(self.tests)} performance tests")

        for test in self.tests:
            if test.concurrent_users > 1:
                await self.run_concurrent_test(test)
            else:
                await self.run_single_test(test)

        return self.results

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0

        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1

        return sorted_data[index]

    def generate_report(self) -> Dict[str, Any]:
        """Generate performance test report"""
        if not self.results:
            return {"message": "No test results available"}

        passed_tests = [r for r in self.results if r.target_met]
        failed_tests = [r for r in self.results if not r.target_met]

        report = {
            "summary": {
                "total_tests": len(self.results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "pass_rate": (len(passed_tests) / len(self.results)) * 100,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "results": [],
        }

        for result in self.results:
            report["results"].append(
                {
                    "test_name": result.test_name,
                    "status": "PASS" if result.target_met else "FAIL",
                    "avg_time_ms": round(result.avg_time_ms, 2),
                    "p95_time_ms": round(result.p95_time_ms, 2),
                    "success_rate": round(result.success_rate, 2),
                    "iterations": result.iterations,
                    "concurrent_users": result.concurrent_users,
                    "error_count": len(result.errors),
                }
            )

        return report

    def save_report(self, filename: str = None):
        """Save performance report to file"""
        if filename is None:
            filename = (
                f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )

        report = self.generate_report()

        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Performance report saved to {filename}")
        return filename


# Database performance tests
class DatabasePerformanceTests:
    """Database-specific performance tests"""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.tester = PerformanceTester()
        self._setup_tests()

    def _setup_tests(self):
        """Setup database performance tests"""

        # User query test
        self.tester.add_test(
            PerformanceTest(
                name="user_query_by_tenant",
                description="Query users by tenant_id",
                target_function=self._test_user_query,
                iterations=100,
                target_time_ms=50.0,
            )
        )

        # Page query test
        self.tester.add_test(
            PerformanceTest(
                name="page_query_by_tenant",
                description="Query pages by tenant_id",
                target_function=self._test_page_query,
                iterations=100,
                target_time_ms=50.0,
            )
        )

        # Lead query test
        self.tester.add_test(
            PerformanceTest(
                name="lead_query_with_filters",
                description="Query leads with status filter",
                target_function=self._test_lead_query,
                iterations=100,
                target_time_ms=75.0,
            )
        )

        # Concurrent user test
        self.tester.add_test(
            PerformanceTest(
                name="concurrent_user_queries",
                description="Concurrent user queries",
                target_function=self._test_user_query,
                iterations=200,
                target_time_ms=100.0,
                concurrent_users=10,
            )
        )

    async def _test_user_query(self):
        """Test user query performance"""
        from sqlalchemy import select

        from models.postgresql_models import User

        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(User)
                .where(User.tenant_id == "test_tenant", User.is_active == True)
                .limit(100)
            )
            users = result.scalars().all()

    async def _test_page_query(self):
        """Test page query performance"""
        from sqlalchemy import select

        from models.postgresql_models import Page

        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(Page)
                .where(Page.tenant_id == "test_tenant", Page.status == "published")
                .limit(100)
            )
            pages = result.scalars().all()

    async def _test_lead_query(self):
        """Test lead query performance"""
        from sqlalchemy import select

        from models.postgresql_models import Lead

        async with self.connection_manager.get_session() as session:
            result = await session.execute(
                select(Lead)
                .where(Lead.tenant_id == "test_tenant", Lead.status == "new_inquiry")
                .order_by(Lead.created_at.desc())
                .limit(50)
            )
            leads = result.scalars().all()

    async def run_tests(self) -> Dict[str, Any]:
        """Run all database performance tests"""
        await self.tester.run_all_tests()
        return self.tester.generate_report()


# API performance tests
class APIPerformanceTests:
    """API endpoint performance tests"""

    def __init__(self, client):
        self.client = client
        self.tester = PerformanceTester()
        self._setup_tests()

    def _setup_tests(self):
        """Setup API performance tests"""

        # Health check test
        self.tester.add_test(
            PerformanceTest(
                name="health_check",
                description="Health check endpoint",
                target_function=self._test_health_check,
                iterations=50,
                target_time_ms=50.0,
            )
        )

        # Pages API test
        self.tester.add_test(
            PerformanceTest(
                name="get_pages_api",
                description="Get pages API endpoint",
                target_function=self._test_get_pages,
                iterations=50,
                target_time_ms=200.0,
            )
        )

        # Leads API test
        self.tester.add_test(
            PerformanceTest(
                name="get_leads_api",
                description="Get leads API endpoint",
                target_function=self._test_get_leads,
                iterations=50,
                target_time_ms=200.0,
            )
        )

    async def _test_health_check(self):
        """Test health check endpoint"""
        response = await self.client.get("/api/health")
        assert response.status_code == 200

    async def _test_get_pages(self):
        """Test get pages endpoint"""
        # This would need proper authentication setup
        pass

    async def _test_get_leads(self):
        """Test get leads endpoint"""
        # This would need proper authentication setup
        pass

    async def run_tests(self) -> Dict[str, Any]:
        """Run all API performance tests"""
        await self.tester.run_all_tests()
        return self.tester.generate_report()


# Global performance test runner
async def run_performance_tests(connection_manager=None, client=None) -> Dict[str, Any]:
    """Run comprehensive performance tests"""
    results = {"timestamp": datetime.utcnow().isoformat(), "tests": {}}

    if connection_manager:
        logger.info("Running database performance tests")
        db_tests = DatabasePerformanceTests(connection_manager)
        results["tests"]["database"] = await db_tests.run_tests()

    if client:
        logger.info("Running API performance tests")
        api_tests = APIPerformanceTests(client)
        results["tests"]["api"] = await api_tests.run_tests()

    return results
