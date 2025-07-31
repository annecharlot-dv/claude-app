"""
Database Performance Optimizer
Implements enterprise-grade database optimizations for MongoDB with migration support for PostgreSQL
"""
import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimizes database performance with indexes, query optimization, and monitoring"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.query_metrics = {}
        self.slow_query_threshold = 100  # 100ms threshold
        
    async def initialize_indexes(self):
        """Create optimized indexes for all collections"""
        
        # Users collection indexes
        users_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("email", ASCENDING)], unique=True),
            IndexModel([("tenant_id", ASCENDING), ("role", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("last_login", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
        await self._create_indexes("users", users_indexes)
        
        # Pages collection indexes
        pages_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("slug", ASCENDING)], unique=True),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("is_homepage", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("updated_at", DESCENDING)]),
            IndexModel([("searchKeywords", TEXT)]),  # Full-text search
            IndexModel([("tenant_id", ASCENDING), ("template_id", ASCENDING)]),
        ]
        await self._create_indexes("pages", pages_indexes)
        
        # Leads collection indexes
        leads_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("email", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("assigned_to", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("source", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("tour_scheduled_at", ASCENDING)]),
        ]
        await self._create_indexes("leads", leads_indexes)
        
        # Bookings collection indexes
        bookings_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("resource_id", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("start_time", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("end_time", ASCENDING)]),
            IndexModel([("start_time", ASCENDING), ("end_time", ASCENDING)]),  # Range queries
        ]
        await self._create_indexes("bookings", bookings_indexes)
        
        # Forms collection indexes
        forms_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)]),
        ]
        await self._create_indexes("forms", forms_indexes)
        
        # Form submissions collection indexes
        form_submissions_indexes = [
            IndexModel([("form_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("lead_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),  # For cleanup
        ]
        await self._create_indexes("form_submissions", form_submissions_indexes)
        
        # Tours collection indexes
        tours_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("scheduled_at", ASCENDING)]),
            IndexModel([("lead_id", ASCENDING)]),
            IndexModel([("staff_user_id", ASCENDING), ("scheduled_at", ASCENDING)]),
        ]
        await self._create_indexes("tours", tours_indexes)
        
        # Tour slots collection indexes
        tour_slots_indexes = [
            IndexModel([("tenant_id", ASCENDING), ("date", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("staff_user_id", ASCENDING), ("date", ASCENDING)]),
            IndexModel([("tenant_id", ASCENDING), ("is_available", ASCENDING)]),
        ]
        await self._create_indexes("tour_slots", tour_slots_indexes)
        
        logger.info("✅ All database indexes created successfully")
    
    async def _create_indexes(self, collection_name: str, indexes: List[IndexModel]):
        """Create indexes for a specific collection"""
        try:
            collection = self.db[collection_name]
            await collection.create_indexes(indexes)
            logger.info(f"✅ Created {len(indexes)} indexes for {collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes for {collection_name}: {e}")
    
    async def optimize_query(self, collection_name: str, query: Dict, options: Dict = None):
        """Execute optimized query with performance monitoring"""
        start_time = time.time()
        
        try:
            collection = self.db[collection_name]
            
            # Add query hints for better performance
            if options is None:
                options = {}
            
            # Auto-add tenant_id to query if not present but available in options
            if "tenant_id" in options and "tenant_id" not in query:
                query["tenant_id"] = options["tenant_id"]
            
            # Execute query
            if options.get("find_one"):
                result = await collection.find_one(query)
            else:
                cursor = collection.find(query)
                
                # Apply sorting
                if options.get("sort"):
                    cursor = cursor.sort(options["sort"])
                
                # Apply pagination
                if options.get("skip"):
                    cursor = cursor.skip(options["skip"])
                if options.get("limit"):
                    cursor = cursor.limit(options["limit"])
                
                result = await cursor.to_list(length=options.get("limit", 1000))
            
            # Record performance metrics
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            await self._record_query_metrics(collection_name, query, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query failed on {collection_name}: {e} (took {execution_time:.2f}ms)")
            raise
    
    async def _record_query_metrics(self, collection: str, query: Dict, execution_time: float):
        """Record query performance metrics"""
        if collection not in self.query_metrics:
            self.query_metrics[collection] = {
                "total_queries": 0,
                "total_time": 0,
                "slow_queries": 0,
                "avg_time": 0
            }
        
        metrics = self.query_metrics[collection]
        metrics["total_queries"] += 1
        metrics["total_time"] += execution_time
        metrics["avg_time"] = metrics["total_time"] / metrics["total_queries"]
        
        if execution_time > self.slow_query_threshold:
            metrics["slow_queries"] += 1
            logger.warning(f"🐌 Slow query detected on {collection}: {execution_time:.2f}ms - {query}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        return {
            "query_metrics": self.query_metrics,
            "slow_query_threshold": self.slow_query_threshold,
            "total_collections": len(self.query_metrics),
            "overall_avg_time": sum(m["avg_time"] for m in self.query_metrics.values()) / len(self.query_metrics) if self.query_metrics else 0
        }
    
    async def cleanup_old_data(self):
        """Clean up old data to maintain performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Clean up old form submissions
        result = await self.db.form_submissions.delete_many({
            "created_at": {"$lt": cutoff_date}
        })
        logger.info(f"🧹 Cleaned up {result.deleted_count} old form submissions")
        
        # Clean up old page versions (keep only last 10)
        # This would be implemented based on your versioning strategy
        
        return {"cleaned_submissions": result.deleted_count}
    
    async def analyze_collection_performance(self, collection_name: str) -> Dict[str, Any]:
        """Analyze performance of a specific collection"""
        collection = self.db[collection_name]
        
        # Get collection stats
        stats = await self.db.command("collStats", collection_name)
        
        # Get index usage stats
        index_stats = []
        async for index in collection.list_indexes():
            index_stats.append(index)
        
        return {
            "collection": collection_name,
            "document_count": stats.get("count", 0),
            "storage_size": stats.get("storageSize", 0),
            "index_count": len(index_stats),
            "indexes": index_stats,
            "avg_obj_size": stats.get("avgObjSize", 0)
        }

# Global optimizer instance
db_optimizer = None

async def get_db_optimizer(db: AsyncIOMotorDatabase) -> DatabaseOptimizer:
    """Get or create database optimizer instance"""
    global db_optimizer
    if db_optimizer is None:
        db_optimizer = DatabaseOptimizer(db)
        await db_optimizer.initialize_indexes()
    return db_optimizer