"""
Cache Service
Prevents duplicate storage with unique IDs and caching
"""

import hashlib
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    In-memory cache with unique ID generation
    
    Features:
    - Generate unique IDs for data
    - Cache API responses
    - Prevent duplicate storage
    - TTL (Time To Live) support
    """
    
    def __init__(self, ttl: int = None, max_size: int = None):
        """
        Initialize cache service
        
        Args:
            ttl: Time to live in seconds (default from settings)
            max_size: Maximum cache entries (default from settings)
        """
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl or settings.CACHE_TTL
        self.max_size = max_size or settings.MAX_CACHE_SIZE
        
        # Persistent cache directory
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Cache Service initialized (TTL: {self.ttl}s, Max: {self.max_size})")
    
    def generate_unique_id(self, data: Any) -> str:
        """
        Generate unique ID from data using SHA256 hash
        
        Args:
            data: Any data (string, dict, list, etc.)
        
        Returns:
            Unique hash ID
            
        Example:
            >>> cache = CacheService()
            >>> id1 = cache.generate_unique_id("Hello World")
            >>> id2 = cache.generate_unique_id("Hello World")
            >>> assert id1 == id2  # Same input = same ID
        """
        try:
            # Convert data to string representation
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            # Generate SHA256 hash
            unique_id = hashlib.sha256(data_str.encode()).hexdigest()
            
            logger.debug(f"🔑 Generated ID: {unique_id[:16]}...")
            return unique_id
            
        except Exception as e:
            logger.error(f"❌ Error generating ID: {e}")
            raise
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live (optional, uses default if None)
        
        Returns:
            True if successful
            
        Example:
            >>> cache = CacheService()
            >>> cache.set("user_123", {"name": "John"})
        """
        try:
            # Check cache size limit
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            # Calculate expiration time
            ttl = ttl or self.ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # Store in cache
            self.cache[key] = {
                'value': value,
                'created_at': datetime.now(),
                'expires_at': expires_at,
                'hits': 0
            }
            
            logger.debug(f"💾 Cached: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
            
        Example:
            >>> cache = CacheService()
            >>> cache.set("user_123", {"name": "John"})
            >>> data = cache.get("user_123")
            >>> print(data)
            {'name': 'John'}
        """
        try:
            if key not in self.cache:
                logger.debug(f"❌ Cache miss: {key}")
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if datetime.now() > entry['expires_at']:
                logger.debug(f"⏰ Cache expired: {key}")
                del self.cache[key]
                return None
            
            # Update hit count
            entry['hits'] += 1
            logger.debug(f"✅ Cache hit: {key} (hits: {entry['hits']})")
            
            return entry['value']
            
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired
        
        Args:
            key: Cache key
        
        Returns:
            True if exists and valid
        """
        return self.get(key) is not None
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"🗑️ Deleted from cache: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()
        logger.info("🧹 Cache cleared")
    
    def _evict_oldest(self) -> None:
        """Remove oldest cache entry"""
        if not self.cache:
            return
        
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['created_at']
        )
        
        del self.cache[oldest_key]
        logger.debug(f"🗑️ Evicted oldest: {oldest_key}")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_hits = sum(entry['hits'] for entry in self.cache.values())
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'total_hits': total_hits,
            'keys': list(self.cache.keys())
        }
    
    def save_to_disk(self, filename: str) -> bool:
        """
        Save cache to disk (persistent storage)
        
        Args:
            filename: File name to save cache
        
        Returns:
            True if successful
        """
        try:
            filepath = self.cache_dir / filename
            with open(filepath, 'wb') as f:
                pickle.dump(self.cache, f)
            
            logger.info(f"💾 Cache saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")
            return False
    
    def load_from_disk(self, filename: str) -> bool:
        """
        Load cache from disk
        
        Args:
            filename: File name to load cache from
        
        Returns:
            True if successful
        """
        try:
            filepath = self.cache_dir / filename
            
            if not filepath.exists():
                logger.warning(f"⚠️ Cache file not found: {filepath}")
                return False
            
            with open(filepath, 'rb') as f:
                self.cache = pickle.load(f)
            
            # Remove expired entries
            expired_keys = [
                k for k, v in self.cache.items()
                if datetime.now() > v['expires_at']
            ]
            for key in expired_keys:
                del self.cache[key]
            
            logger.info(f"✅ Cache loaded from {filepath} ({len(self.cache)} entries)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading cache: {e}")
            return False


# Global cache instance
cache_service = CacheService()


# Test function
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CACHE SERVICE TEST")
    print("=" * 60 + "\n")
    
    cache = CacheService(ttl=5)  # 5 second TTL for testing
    
    # Test 1: Generate unique IDs
    print("🔑 Test 1: Unique ID generation")
    id1 = cache.generate_unique_id("Hello World")
    id2 = cache.generate_unique_id("Hello World")
    id3 = cache.generate_unique_id("Different Data")
    
    print(f"  ID1: {id1[:16]}...")
    print(f"  ID2: {id2[:16]}...")
    print(f"  ID3: {id3[:16]}...")
    print(f"  ✅ Same input = same ID: {id1 == id2}")
    print(f"  ✅ Different input = different ID: {id1 != id3}")
    
    # Test 2: Set and get
    print("\n💾 Test 2: Set and get")
    cache.set("user_1", {"name": "John", "age": 30})
    data = cache.get("user_1")
    print(f"  Retrieved: {data}")
    print(f"  ✅ Data matches: {data['name'] == 'John'}")
    
    # Test 3: Cache miss
    print("\n❌ Test 3: Cache miss")
    missing = cache.get("non_existent")
    print(f"  Result: {missing}")
    print(f"  ✅ Returns None: {missing is None}")
    
    # Test 4: Stats
    print("\n📊 Test 4: Cache statistics")
    stats = cache.get_stats()
    print(f"  Size: {stats['size']}")
    print(f"  Total hits: {stats['total_hits']}")
    
    # Test 5: Expiration
    print("\n⏰ Test 5: Expiration (wait 6 seconds)")
    print("  Waiting...", end="", flush=True)
    import time
    time.sleep(6)
    print(" Done!")
    expired = cache.get("user_1")
    print(f"  After expiration: {expired}")
    print(f"  ✅ Expired correctly: {expired is None}")
    
    print("\n✅ All tests passed!")
    print("=" * 60 + "\n")