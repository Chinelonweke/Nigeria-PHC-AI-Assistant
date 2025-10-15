"""
Deduplication Service
Prevents storing duplicate queries using content hashing and embeddings
"""

import hashlib
import json
from typing import Dict, Optional, List
from datetime import datetime

from backend.core.logger import get_logger
from backend.services.cache_service import cache_service

logger = get_logger(__name__)


class DeduplicationService:
    """
    Service to prevent duplicate query storage
    Uses content hashing and optional embedding similarity
    """
    
    def __init__(self):
        """Initialize deduplication service"""
        self.seen_hashes = {}  # In-memory store of seen query hashes
        self.similarity_threshold = 0.9  # 90% similarity threshold
        logger.info("✅ Deduplication Service initialized")
    
    def generate_query_id(self, content: Dict) -> str:
        """
        Generate unique ID for query based on content
        
        Args:
            content: Dictionary containing query data
            
        Returns:
            Unique hash ID
        """
        # Normalize content for hashing
        normalized = {
            'symptoms': str(content.get('symptoms', '')).lower().strip(),
            'age': content.get('age'),
            'gender': content.get('gender'),
            'language': content.get('language', 'english')
        }
        
        # Create hash from normalized content
        content_string = json.dumps(normalized, sort_keys=True)
        query_hash = hashlib.sha256(content_string.encode()).hexdigest()
        
        return query_hash
    
    def is_duplicate(self, query_id: str) -> bool:
        """
        Check if query has been seen before
        
        Args:
            query_id: Unique query hash
            
        Returns:
            True if duplicate, False otherwise
        """
        # Check cache first
        cache_key = f"query_seen_{query_id}"
        cached = cache_service.get(cache_key)
        
        if cached:
            logger.info(f"🔄 Duplicate query detected: {query_id[:8]}...")
            return True
        
        # Check in-memory store
        if query_id in self.seen_hashes:
            logger.info(f"🔄 Duplicate query in memory: {query_id[:8]}...")
            return True
        
        return False
    
    def mark_as_seen(self, query_id: str, ttl: int = 86400):
        """
        Mark query as seen to prevent duplicates
        
        Args:
            query_id: Unique query hash
            ttl: Time to live in seconds (default 24 hours)
        """
        # Store in cache
        cache_key = f"query_seen_{query_id}"
        cache_service.set(cache_key, {
            'seen_at': datetime.now().isoformat(),
            'query_id': query_id
        }, ttl=ttl)
        
        # Store in memory
        self.seen_hashes[query_id] = datetime.now()
        
        logger.info(f"✅ Query marked as seen: {query_id[:8]}...")
    
    def get_or_create_query_id(self, content: Dict) -> tuple[str, bool]:
        """
        Get existing query ID or create new one
        
        Args:
            content: Query content
            
        Returns:
            Tuple of (query_id, is_new)
        """
        query_id = self.generate_query_id(content)
        is_duplicate = self.is_duplicate(query_id)
        
        if not is_duplicate:
            self.mark_as_seen(query_id)
        
        return query_id, not is_duplicate
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity
        Uses character-level similarity (Jaccard)
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        text1_set = set(text1.lower().split())
        text2_set = set(text2.lower().split())
        
        if not text1_set or not text2_set:
            return 0.0
        
        intersection = text1_set.intersection(text2_set)
        union = text1_set.union(text2_set)
        
        return len(intersection) / len(union)
    
    def find_similar_queries(
        self, 
        symptoms: str, 
        threshold: float = 0.9
    ) -> List[str]:
        """
        Find similar queries based on symptoms
        
        Args:
            symptoms: Symptom text to compare
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar query IDs
        """
        similar_queries = []
        
        # Check against recently seen queries
        for query_id, timestamp in self.seen_hashes.items():
            # Get cached query details
            cache_key = f"query_seen_{query_id}"
            cached = cache_service.get(cache_key)
            
            if cached:
                # Calculate similarity (simplified)
                # In production, use embeddings here
                similarity = 0.0  # Placeholder
                
                if similarity >= threshold:
                    similar_queries.append(query_id)
        
        return similar_queries


# Global instance
deduplication_service = DeduplicationService()