"""
Enterprise Caching Manager
Implements multi-layer caching with intelligent invalidation for optimal performance
"""
import asyncio
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Multi-layer cache manager with intelligent invalidation"""
    
    def __init__(self):
        # In-memory cache layers
        self.l1_cache = {}  # Hot data (< 1MB, < 5min TTL)
        self.l2_cache = {}  # Warm data (< 10MB, < 30min TTL)
        self.l3_cache = {}  # Cold data (< 100MB, < 24h TTL)
        
        # Cache metadata
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "size_bytes": 0
        }
        
        # TTL configurations (in seconds)
        self.ttl_config = {
            "l1": 300,    # 5 minutes
            "l2": 1800,   # 30 minutes
            "l3": 86400   # 24 hours
        }
        
        # Size limits (in bytes)
        self.size_limits = {
            "l1": 1024 * 1024,      # 1MB
            "l2": 10 * 1024 * 1024, # 10MB
            "l3": 100 * 1024 * 1024 # 100MB
        }
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_layer(self, data_size: int) -> str:
        """Determine appropriate cache layer based on data size"""
        if data_size <= self.size_limits["l1"]:
            return "l1"
        elif data_size <= self.size_limits["l2"]:
            return "l2"
        else:
            return "l3"
    
    def _get_cache_store(self, layer: str) -> Dict:
        """Get cache store for specific layer"""
        if layer == "l1":
            return self.l1_cache
        elif layer == "l2":
            return self.l2_cache
        else:
            return self.l3_cache
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic layer detection"""
        # Check all layers (L1 -> L2 -> L3)
        for layer in ["l1", "l2", "l3"]:
            cache_store = self._get_cache_store(layer)
            if key in cache_store:
                entry = cache_store[key]
                
                # Check TTL
                if time.time() > entry["expires_at"]:
                    del cache_store[key]
                    continue
                
                # Update access time and promote to L1 if frequently accessed
                entry["last_accessed"] = time.time()
                entry["access_count"] += 1
                
                # Promote to L1 if accessed more than 3 times
                if layer != "l1" and entry["access_count"] > 3:
                    await self._promote_to_l1(key, entry)
                
                self.cache_stats["hits"] += 1
                return entry["data"]
        
        self.cache_stats["misses"] += 1
        return None
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None, tags: List[str] = None) -> bool:
        """Set value in appropriate cache layer"""
        try:
            # Serialize data to calculate size
            serialized_data = json.dumps(data, default=str)
            data_size = len(serialized_data.encode())
            
            # Determine cache layer
            layer = self._get_cache_layer(data_size)
            cache_store = self._get_cache_store(layer)
            
            # Use layer-specific TTL if not provided
            if ttl is None:
                ttl = self.ttl_config[layer]
            
            # Create cache entry
            entry = {
                "data": data,
                "created_at": time.time(),
                "expires_at": time.time() + ttl,
                "last_accessed": time.time(),
                "access_count": 0,
                "size_bytes": data_size,
                "layer": layer,
                "tags": tags or []
            }
            
            # Check cache size limits and evict if necessary
            await self._evict_if_necessary(layer, data_size)
            
            cache_store[key] = entry
            self.cache_stats["size_bytes"] += data_size
            
            logger.debug(f"Cached {key} in {layer} layer ({data_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            return False
    
    async def _promote_to_l1(self, key: str, entry: Dict):
        """Promote frequently accessed item to L1 cache"""
        if entry["size_bytes"] <= self.size_limits["l1"]:
            # Remove from current layer
            current_layer = entry["layer"]
            current_store = self._get_cache_store(current_layer)
            if key in current_store:
                del current_store[key]
            
            # Add to L1
            entry["layer"] = "l1"
            entry["expires_at"] = time.time() + self.ttl_config["l1"]
            self.l1_cache[key] = entry
            
            logger.debug(f"Promoted {key} to L1 cache")
    
    async def _evict_if_necessary(self, layer: str, new_data_size: int):
        """Evict old entries if cache is full"""
        cache_store = self._get_cache_store(layer)
        current_size = sum(entry["size_bytes"] for entry in cache_store.values())
        
        if current_size + new_data_size > self.size_limits[layer]:
            # Sort by last accessed time (LRU eviction)
            sorted_entries = sorted(
                cache_store.items(),
                key=lambda x: x[1]["last_accessed"]
            )
            
            # Evict oldest entries until we have space
            for key, entry in sorted_entries:
                del cache_store[key]
                self.cache_stats["size_bytes"] -= entry["size_bytes"]
                current_size -= entry["size_bytes"]
                
                if current_size + new_data_size <= self.size_limits[layer]:
                    break
    
    async def invalidate(self, pattern: str = None, tags: List[str] = None):
        """Invalidate cache entries by pattern or tags"""
        invalidated_count = 0
        
        for layer in ["l1", "l2", "l3"]:
            cache_store = self._get_cache_store(layer)
            keys_to_remove = []
            
            for key, entry in cache_store.items():
                should_invalidate = False
                
                # Pattern matching
                if pattern and pattern in key:
                    should_invalidate = True
                
                # Tag matching
                if tags and any(tag in entry.get("tags", []) for tag in tags):
                    should_invalidate = True
                
                if should_invalidate:
                    keys_to_remove.append(key)
            
            # Remove invalidated entries
            for key in keys_to_remove:
                entry = cache_store[key]
                self.cache_stats["size_bytes"] -= entry["size_bytes"]
                del cache_store[key]
                invalidated_count += 1
        
        self.cache_stats["invalidations"] += invalidated_count
        logger.info(f"Invalidated {invalidated_count} cache entries")
        return invalidated_count
    
    async def clear_expired(self):
        """Clear expired cache entries"""
        current_time = time.time()
        cleared_count = 0
        
        for layer in ["l1", "l2", "l3"]:
            cache_store = self._get_cache_store(layer)
            expired_keys = [
                key for key, entry in cache_store.items()
                if current_time > entry["expires_at"]
            ]
            
            for key in expired_keys:
                entry = cache_store[key]
                self.cache_stats["size_bytes"] -= entry["size_bytes"]
                del cache_store[key]
                cleared_count += 1
        
        logger.debug(f"Cleared {cleared_count} expired cache entries")
        return cleared_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_entries = len(self.l1_cache) + len(self.l2_cache) + len(self.l3_cache)
        hit_rate = (self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"])) * 100 if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0 else 0
        
        return {
            "hit_rate": round(hit_rate, 2),
            "total_entries": total_entries,
            "layer_distribution": {
                "l1": len(self.l1_cache),
                "l2": len(self.l2_cache),
                "l3": len(self.l3_cache)
            },
            "size_bytes": self.cache_stats["size_bytes"],
            "size_mb": round(self.cache_stats["size_bytes"] / (1024 * 1024), 2),
            **self.cache_stats
        }

# Specialized cache managers for different data types
class TenantCacheManager(CacheManager):
    """Specialized cache manager for tenant-specific data"""
    
    async def get_tenant_data(self, tenant_id: str) -> Optional[Dict]:
        """Get cached tenant data"""
        key = self._generate_cache_key("tenant", tenant_id=tenant_id)
        return await self.get(key)
    
    async def set_tenant_data(self, tenant_id: str, data: Dict):
        """Cache tenant data with tenant-specific tags"""
        key = self._generate_cache_key("tenant", tenant_id=tenant_id)
        await self.set(key, data, ttl=3600, tags=[f"tenant:{tenant_id}"])
    
    async def get_user_data(self, tenant_id: str, user_id: str) -> Optional[Dict]:
        """Get cached user data"""
        key = self._generate_cache_key("user", tenant_id=tenant_id, user_id=user_id)
        return await self.get(key)
    
    async def set_user_data(self, tenant_id: str, user_id: str, data: Dict):
        """Cache user data"""
        key = self._generate_cache_key("user", tenant_id=tenant_id, user_id=user_id)
        await self.set(key, data, ttl=1800, tags=[f"tenant:{tenant_id}", f"user:{user_id}"])
    
    async def invalidate_tenant(self, tenant_id: str):
        """Invalidate all cache entries for a tenant"""
        await self.invalidate(tags=[f"tenant:{tenant_id}"])

class PageCacheManager(CacheManager):
    """Specialized cache manager for CMS pages"""
    
    async def get_page(self, tenant_id: str, slug: str) -> Optional[Dict]:
        """Get cached page data"""
        key = self._generate_cache_key("page", tenant_id=tenant_id, slug=slug)
        return await self.get(key)
    
    async def set_page(self, tenant_id: str, slug: str, data: Dict):
        """Cache page data"""
        key = self._generate_cache_key("page", tenant_id=tenant_id, slug=slug)
        await self.set(key, data, ttl=7200, tags=[f"tenant:{tenant_id}", "pages"])
    
    async def get_page_list(self, tenant_id: str, status: str = None) -> Optional[List]:
        """Get cached page list"""
        key = self._generate_cache_key("page_list", tenant_id=tenant_id, status=status)
        return await self.get(key)
    
    async def set_page_list(self, tenant_id: str, data: List, status: str = None):
        """Cache page list"""
        key = self._generate_cache_key("page_list", tenant_id=tenant_id, status=status)
        await self.set(key, data, ttl=1800, tags=[f"tenant:{tenant_id}", "pages"])
    
    async def invalidate_pages(self, tenant_id: str):
        """Invalidate all page cache for a tenant"""
        await self.invalidate(tags=[f"tenant:{tenant_id}", "pages"])

# Global cache instances
tenant_cache = TenantCacheManager()
page_cache = PageCacheManager()
general_cache = CacheManager()

async def get_cache_manager(cache_type: str = "general") -> CacheManager:
    """Get appropriate cache manager"""
    if cache_type == "tenant":
        return tenant_cache
    elif cache_type == "page":
        return page_cache
    else:
        return general_cache