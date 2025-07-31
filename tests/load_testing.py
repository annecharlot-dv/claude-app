"""
Enhanced load testing suite for multi-tenant SaaS platform with industry-specific scenarios
"""
import asyncio
import aiohttp
import time
import json
import random
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import logging
import os
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    error_rate: float

class LoadTester:
    def __init__(self, base_url: str = "https://your-domain.com"):
        self.base_url = base_url
        self.session = None
        self.test_scenarios = [
            {
                "name": "API Health Check",
                "endpoint": "/api/health",
                "method": "GET",
                "concurrent_users": 50,
                "requests_per_user": 20,
                "think_time": 0.1
            },
            {
                "name": "User Authentication",
                "endpoint": "/api/auth/login",
                "method": "POST",
                "concurrent_users": 20,
                "requests_per_user": 10,
                "think_time": 1.0,
                "payload": {
                    "email": "test@example.com",
                    "password": "testpassword"
                }
            },
            {
                "name": "Booking Availability Check",
                "endpoint": "/api/bookings/availability",
                "method": "GET",
                "concurrent_users": 30,
                "requests_per_user": 15,
                "think_time": 0.5,
                "params": {
                    "date": "2024-12-01",
                    "duration": "60"
                }
            },
            {
                "name": "CMS Page Load",
                "endpoint": "/api/cms/pages",
                "method": "GET",
                "concurrent_users": 40,
                "requests_per_user": 25,
                "think_time": 0.3
            },
            {
                "name": "Multi-tenant Isolation Test",
                "endpoint": "/api/tenant/info",
                "method": "GET",
                "concurrent_users": 15,
                "requests_per_user": 10,
                "think_time": 0.2,
                "tenant_specific": True
            }
        ]
        
        self.tenant_subdomains = ["demo", "coworking", "university", "hotel"]
    
    async def run_load_tests(self) -> Dict[str, Any]:
        """Run comprehensive load tests"""
        logger.info("Starting load testing suite...")
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=200, limit_per_host=50)
        ) as session:
            self.session = session
            
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "test_results": [],
                "summary": {}
            }
            
            for scenario in self.test_scenarios:
                logger.info(f"Running scenario: {scenario['name']}")
                
                if scenario.get("tenant_specific"):
                    # Run test for each tenant
                    for subdomain in self.tenant_subdomains:
                        tenant_url = f"https://{subdomain}.your-domain.com"
                        scenario_result = await self._run_scenario(scenario, tenant_url)
                        scenario_result.endpoint = f"{subdomain}.{scenario_result.endpoint}"
                        results["test_results"].append(scenario_result)
                else:
                    # Run test for main domain
                    scenario_result = await self._run_scenario(scenario, self.base_url)
                    results["test_results"].append(scenario_result)
            
            # Generate summary
            results["summary"] = self._generate_summary(results["test_results"])
            
            return results
    
    async def _run_scenario(self, scenario: Dict[str, Any], base_url: str) -> LoadTestResult:
        """Run a single load test scenario"""
        concurrent_users = scenario["concurrent_users"]
        requests_per_user = scenario["requests_per_user"]
        think_time = scenario["think_time"]
        
        # Create tasks for concurrent users
        tasks = []
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_user(scenario, base_url, user_id, requests_per_user, think_time)
            )
            tasks.append(task)
        
        # Wait for all users to complete
        start_time = time.time()
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Aggregate results
        all_response_times = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        
        for user_result in user_results:
            if isinstance(user_result, Exception):
                logger.error(f"User simulation failed: {user_result}")
                continue
            
            response_times, success_count, fail_count = user_result
            all_response_times.extend(response_times)
            total_requests += success_count + fail_count
            successful_requests += success_count
            failed_requests += fail_count
        
        # Calculate statistics
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]  # 95th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        return LoadTestResult(
            endpoint=scenario["endpoint"],
            method=scenario["method"],
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=round(avg_response_time, 2),
            min_response_time=round(min_response_time, 2),
            max_response_time=round(max_response_time, 2),
            p95_response_time=round(p95_response_time, 2),
            requests_per_second=round(requests_per_second, 2),
            error_rate=round(error_rate, 2)
        )
    
    async def _simulate_user(
        self, 
        scenario: Dict[str, Any], 
        base_url: str, 
        user_id: int, 
        requests_per_user: int, 
        think_time: float
    ) -> tuple:
        """Simulate a single user's behavior"""
        response_times = []
        success_count = 0
        fail_count = 0
        
        for request_num in range(requests_per_user):
            try:
                # Add some randomness to think time
                actual_think_time = think_time * (0.5 + random.random())
                await asyncio.sleep(actual_think_time)
                
                # Make request
                start_time = time.time()
                
                url = f"{base_url}{scenario['endpoint']}"
                method = scenario["method"].upper()
                
                kwargs = {}
                if scenario.get("payload"):
                    kwargs["json"] = scenario["payload"]
                if scenario.get("params"):
                    kwargs["params"] = scenario["params"]
                
                async with self.session.request(method, url, **kwargs) as response:
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    response_times.append(response_time)
                    
                    if response.status < 400:
                        success_count += 1
                    else:
                        fail_count += 1
                        logger.warning(f"Request failed: {response.status} for {url}")
                        
            except Exception as e:
                fail_count += 1
                logger.error(f"Request exception for user {user_id}: {e}")
        
        return response_times, success_count, fail_count
    
    def _generate_summary(self, test_results: List[LoadTestResult]) -> Dict[str, Any]:
        """Generate summary statistics from test results"""
        if not test_results:
            return {}
        
        total_requests = sum(r.total_requests for r in test_results)
        total_successful = sum(r.successful_requests for r in test_results)
        total_failed = sum(r.failed_requests for r in test_results)
        
        avg_response_times = [r.avg_response_time for r in test_results if r.avg_response_time > 0]
        avg_rps = [r.requests_per_second for r in test_results if r.requests_per_second > 0]
        
        summary = {
            "total_requests": total_requests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "overall_success_rate": round((total_successful / total_requests * 100), 2) if total_requests > 0 else 0,
            "average_response_time": round(statistics.mean(avg_response_times), 2) if avg_response_times else 0,
            "average_requests_per_second": round(statistics.mean(avg_rps), 2) if avg_rps else 0,
            "slowest_endpoint": max(test_results, key=lambda x: x.avg_response_time).endpoint if test_results else None,
            "fastest_endpoint": min(test_results, key=lambda x: x.avg_response_time).endpoint if test_results else None,
            "performance_grade": self._calculate_performance_grade(test_results)
        }
        
        return summary
    
    def _calculate_performance_grade(self, test_results: List[LoadTestResult]) -> str:
        """Calculate overall performance grade"""
        if not test_results:
            return "F"
        
        # Scoring criteria
        avg_response_time = statistics.mean([r.avg_response_time for r in test_results if r.avg_response_time > 0])
        avg_error_rate = statistics.mean([r.error_rate for r in test_results])
        
        score = 100
        
        # Deduct points for slow response times
        if avg_response_time > 2000:  # 2 seconds
            score -= 30
        elif avg_response_time > 1000:  # 1 second
            score -= 15
        elif avg_response_time > 500:  # 500ms
            score -= 5
        
        # Deduct points for errors
        if avg_error_rate > 5:
            score -= 40
        elif avg_error_rate > 1:
            score -= 20
        elif avg_error_rate > 0.1:
            score -= 10
        
        # Convert to letter grade
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

async def main():
    """Main load testing execution"""
    tester = LoadTester()
    results = await tester.run_load_tests()
    
    # Print results
    print(json.dumps(results, indent=2, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x)))
    
    # Exit with error if performance is poor
    if results["summary"].get("performance_grade") in ["D", "F"]:
        logger.error("Load test performance is below acceptable threshold")
        exit(1)
    
    logger.info("Load testing completed successfully")

if __name__ == "__main__":
    asyncio.run(main())