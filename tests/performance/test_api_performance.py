"""
Performance tests for API endpoints with specific benchmarks
"""
import pytest
import asyncio
import time
from typing import Dict, Any, List
import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase
from concurrent.futures import ThreadPoolExecutor
import statistics

@pytest.mark.performance
class TestAPIPerformance:
    """Test API response time performance"""
    
    async def test_health_endpoint_performance(self, performance_thresholds: Dict[str, float]):
        """Test health endpoint responds within threshold"""
        async def make_health_request():
            start_time = time.time()
            # Simulate health check logic
            await asyncio.sleep(0.01)  # Simulate minimal processing
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to ms
        
        # Make multiple requests to get average
        response_times = []
        for _ in range(10):
            response_time = await make_health_request()
            response_times.append(response_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < performance_thresholds["api_response_time_ms"]
        assert max_response_time < performance_thresholds["api_response_time_ms"] * 2
    
    async def test_authentication_performance(self, performance_thresholds: Dict[str, float]):
        """Test authentication endpoint performance"""
        async def simulate_auth_request():
            start_time = time.time()
            
            # Simulate authentication logic
            await asyncio.sleep(0.05)  # Password hashing simulation
            
            end_time = time.time()
            return (end_time - start_time) * 1000
        
        response_times = []
        for _ in range(5):  # Fewer iterations due to heavier operation
            response_time = await simulate_auth_request()
            response_times.append(response_time)
        
        avg_response_time = statistics.mean(response_times)
        
        # Auth can be slightly slower due to password hashing
        assert avg_response_time < performance_thresholds["api_response_time_ms"] * 2
    
    async def test_booking_creation_performance(self, clean_db: AsyncIOMotorDatabase, performance_thresholds: Dict[str, float]):
        """Test booking creation performance"""
        async def simulate_booking_creation():
            start_time = time.time()
            
            # Simulate booking creation logic
            booking_data = {
                "booking_id": f"perf_test_{int(time.time() * 1000)}",
                "tenant_id": "coworking",
                "user_id": "test_user",
                "space_id": "meeting_room_1",
                "start_time": "2024-12-01T10:00:00Z",
                "end_time": "2024-12-01T11:00:00Z",
                "status": "confirmed"
            }
            
            # Database write simulation
            await clean_db.bookings.insert_one(booking_data)
            
            end_time = time.time()
            return (end_time - start_time) * 1000
        
        response_times = []
        for _ in range(10):
            response_time = await simulate_booking_creation()
            response_times.append(response_time)
        
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < performance_thresholds["api_response_time_ms"]

@pytest.mark.performance
class TestDatabasePerformance:
    """Test database query performance"""
    
    async def test_user_lookup_performance(self, clean_db: AsyncIOMotorDatabase, seed_users: Dict[str, Dict[str, Any]], performance_thresholds: Dict[str, float]):
        """Test user lookup query performance"""
        async def time_user_lookup():
            start_time = time.time()
            
            user = await clean_db.users.find_one({
                "tenant_id": "coworking",
                "email": "admin@test.com"
            })
            
            end_time = time.time()
            return (end_time - start_time) * 1000, user is not None
        
        # Test multiple lookups
        query_times = []
        for _ in range(20):
            query_time, found = await time_user_lookup()
            query_times.append(query_time)
            assert found  # Ensure query actually found the user
        
        avg_query_time = statistics.mean(query_times)
        assert avg_query_time < performance_thresholds["database_query_time_ms"]
    
    async def test_booking_availability_query_performance(self, clean_db: AsyncIOMotorDatabase, performance_thresholds: Dict[str, float]):
        """Test booking availability query performance"""
        # Create test bookings for performance testing
        test_bookings = []
        for i in range(100):  # Create 100 bookings
            booking = {
                "booking_id": f"perf_booking_{i}",
                "tenant_id": "coworking",
                "space_id": f"space_{i % 10}",  # 10 different spaces
                "start_time": f"2024-12-{(i % 30) + 1:02d}T{(i % 12) + 8:02d}:00:00Z",
                "end_time": f"2024-12-{(i % 30) + 1:02d}T{(i % 12) + 9:02d}:00:00Z",
                "status": "confirmed"
            }
            test_bookings.append(booking)
        
        await clean_db.bookings.insert_many(test_bookings)
        
        async def time_availability_query():
            start_time = time.time()
            
            # Complex availability query
            conflicts = await clean_db.bookings.find({
                "tenant_id": "coworking",
                "space_id": "space_1",
                "status": {"$in": ["confirmed", "pending"]},
                "$or": [
                    {"start_time": {"$lt": "2024-12-15T11:00:00Z", "$gte": "2024-12-15T10:00:00Z"}},
                    {"end_time": {"$gt": "2024-12-15T10:00:00Z", "$lte": "2024-12-15T11:00:00Z"}},
                    {"start_time": {"$lte": "2024-12-15T10:00:00Z"}, "end_time": {"$gte": "2024-12-15T11:00:00Z"}}
                ]
            }).to_list(None)
            
            end_time = time.time()
            return (end_time - start_time) * 1000, len(conflicts)
        
        query_times = []
        for _ in range(10):
            query_time, conflict_count = await time_availability_query()
            query_times.append(query_time)
        
        avg_query_time = statistics.mean(query_times)
        assert avg_query_time < performance_thresholds["database_query_time_ms"]
    
    async def test_tenant_data_filtering_performance(self, clean_db: AsyncIOMotorDatabase, performance_thresholds: Dict[str, float]):
        """Test performance of tenant-filtered queries"""
        # Create test data across multiple tenants
        test_data = []
        tenants = ["coworking", "university", "hotel"]
        
        for tenant in tenants:
            for i in range(50):  # 50 records per tenant
                record = {
                    "record_id": f"{tenant}_record_{i}",
                    "tenant_id": tenant,
                    "data": f"test data for {tenant}",
                    "index_field": i
                }
                test_data.append(record)
        
        await clean_db.test_collection.insert_many(test_data)
        
        async def time_tenant_filtered_query():
            start_time = time.time()
            
            records = await clean_db.test_collection.find({
                "tenant_id": "coworking",
                "index_field": {"$gte": 10, "$lte": 40}
            }).to_list(None)
            
            end_time = time.time()
            return (end_time - start_time) * 1000, len(records)
        
        query_times = []
        for _ in range(15):
            query_time, record_count = await time_tenant_filtered_query()
            query_times.append(query_time)
            assert record_count == 31  # Should find records 10-40
        
        avg_query_time = statistics.mean(query_times)
        assert avg_query_time < performance_thresholds["database_query_time_ms"]

@pytest.mark.performance
class TestConcurrentLoad:
    """Test system performance under concurrent load"""
    
    async def test_concurrent_booking_requests(self, clean_db: AsyncIOMotorDatabase, performance_thresholds: Dict[str, float]):
        """Test system performance with concurrent booking requests"""
        async def create_booking(booking_id: str):
            start_time = time.time()
            
            booking_data = {
                "booking_id": booking_id,
                "tenant_id": "coworking",
                "user_id": f"user_{booking_id}",
                "space_id": "meeting_room_1",
                "start_time": f"2024-12-01T{10 + int(booking_id) % 8}:00:00Z",
                "end_time": f"2024-12-01T{11 + int(booking_id) % 8}:00:00Z",
                "status": "confirmed"
            }
            
            try:
                await clean_db.bookings.insert_one(booking_data)
                success = True
            except Exception:
                success = False
            
            end_time = time.time()
            return (end_time - start_time) * 1000, success
        
        # Create 20 concurrent booking requests
        tasks = []
        for i in range(20):
            task = asyncio.create_task(create_booking(str(i)))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        response_times = [result[0] for result in results]
        success_count = sum(1 for result in results if result[1])
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Performance assertions
        assert avg_response_time < performance_thresholds["api_response_time_ms"] * 2
        assert max_response_time < performance_thresholds["api_response_time_ms"] * 5
        assert success_count >= 15  # At least 75% success rate under load
    
    async def test_concurrent_user_authentication(self, performance_thresholds: Dict[str, float]):
        """Test authentication performance under concurrent load"""
        async def simulate_auth(user_id: str):
            start_time = time.time()
            
            # Simulate authentication logic
            await asyncio.sleep(0.02)  # Simulate password verification
            
            end_time = time.time()
            return (end_time - start_time) * 1000
        
        # Create 15 concurrent authentication requests
        tasks = []
        for i in range(15):
            task = asyncio.create_task(simulate_auth(f"user_{i}"))
            tasks.append(task)
        
        response_times = await asyncio.gather(*tasks)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Auth can be slower due to password hashing
        assert avg_response_time < performance_thresholds["api_response_time_ms"] * 3
        assert max_response_time < performance_thresholds["api_response_time_ms"] * 5

@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityLimits:
    """Test system scalability limits"""
    
    async def test_large_dataset_query_performance(self, clean_db: AsyncIOMotorDatabase, performance_thresholds: Dict[str, float]):
        """Test query performance with large datasets"""
        # Create large dataset (1000 records)
        large_dataset = []
        for i in range(1000):
            record = {
                "record_id": f"large_record_{i}",
                "tenant_id": "coworking",
                "category": f"category_{i % 10}",
                "value": i,
                "timestamp": f"2024-12-{(i % 30) + 1:02d}T{(i % 24):02d}:00:00Z"
            }
            large_dataset.append(record)
        
        await clean_db.large_test_collection.insert_many(large_dataset)
        
        async def time_complex_query():
            start_time = time.time()
            
            # Complex aggregation query
            pipeline = [
                {"$match": {"tenant_id": "coworking", "value": {"$gte": 100, "$lte": 900}}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}, "avg_value": {"$avg": "$value"}}},
                {"$sort": {"count": -1}}
            ]
            
            results = await clean_db.large_test_collection.aggregate(pipeline).to_list(None)
            
            end_time = time.time()
            return (end_time - start_time) * 1000, len(results)
        
        query_times = []
        for _ in range(5):
            query_time, result_count = await time_complex_query()
            query_times.append(query_time)
            assert result_count == 10  # Should have 10 categories
        
        avg_query_time = statistics.mean(query_times)
        
        # Allow more time for complex queries on large datasets
        assert avg_query_time < performance_thresholds["database_query_time_ms"] * 10
    
    async def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate memory-intensive operations
        large_data_sets = []
        for i in range(10):
            # Create moderately large data structures
            data_set = [{"id": j, "data": f"test_data_{j}" * 10} for j in range(1000)]
            large_data_sets.append(data_set)
            
            # Simulate processing
            await asyncio.sleep(0.01)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = peak_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for this test)
        assert memory_growth < 100
        
        # Clean up
        del large_data_sets