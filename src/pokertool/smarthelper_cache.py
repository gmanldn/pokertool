"""
SmartHelper Caching Layer

Redis-based caching for SmartHelper recommendations, GTO solutions, and equity calculations.
Implements TTL-based caching with cache warming and invalidation strategies.

Author: PokerTool Team
Created: 2025-10-22
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class SmartHelperCache:
    """
    Redis cache for SmartHelper data with TTL management

    Cache Keys:
    - rec:{hash}  - Recommendations (5s TTL)
    - gto:{hash}  - GTO solutions (24h TTL)
    - eq:{hash}   - Equity calculations (30s TTL)
    - factors:{street}:{position} - Factor lists (1h TTL)
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None
    ):
        """
        Initialize cache with Redis connection

        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (if required)
        """
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = True

        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_timeout=1,
                socket_connect_timeout=1
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected: {redis_host}:{redis_port}")

        except RedisError as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self.enabled = False
            self.redis_client = None

    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """
        Generate consistent hash for game state

        Args:
            data: Dictionary to hash

        Returns:
            SHA256 hash string
        """
        # Convert to sorted JSON for consistent hashing
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def _is_available(self) -> bool:
        """Check if cache is available"""
        if not self.enabled or not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False

    # Recommendation Caching (5s TTL)

    def get_recommendation(self, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached recommendation for game state

        Args:
            game_state: Current game state

        Returns:
            Cached recommendation or None
        """
        if not self._is_available():
            return None

        try:
            key = f"rec:{self._generate_hash(game_state)}"
            cached = self.redis_client.get(key)

            if cached:
                logger.debug(f"Cache hit: recommendation {key}")
                return json.loads(cached)

            logger.debug(f"Cache miss: recommendation {key}")
            return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading recommendation cache: {e}")
            return None

    def set_recommendation(
        self,
        game_state: Dict[str, Any],
        recommendation: Dict[str, Any],
        ttl_seconds: int = 5
    ) -> bool:
        """
        Cache recommendation with TTL

        Args:
            game_state: Current game state
            recommendation: Recommendation to cache
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        if not self._is_available():
            return False

        try:
            key = f"rec:{self._generate_hash(game_state)}"
            value = json.dumps(recommendation)

            self.redis_client.setex(
                key,
                timedelta(seconds=ttl_seconds),
                value
            )

            logger.debug(f"Cached recommendation {key} (TTL: {ttl_seconds}s)")
            return True

        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Error caching recommendation: {e}")
            return False

    # GTO Solution Caching (24h TTL)

    def get_gto_solution(self, gto_key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached GTO solution

        Args:
            gto_key: GTO state identifier (position, action, range, etc.)

        Returns:
            Cached GTO solution or None
        """
        if not self._is_available():
            return None

        try:
            key = f"gto:{self._generate_hash(gto_key)}"
            cached = self.redis_client.get(key)

            if cached:
                logger.debug(f"Cache hit: GTO solution {key}")
                return json.loads(cached)

            return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading GTO cache: {e}")
            return None

    def set_gto_solution(
        self,
        gto_key: Dict[str, Any],
        solution: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache GTO solution with long TTL

        Args:
            gto_key: GTO state identifier
            solution: GTO solution to cache
            ttl_hours: Time-to-live in hours

        Returns:
            True if cached successfully
        """
        if not self._is_available():
            return False

        try:
            key = f"gto:{self._generate_hash(gto_key)}"
            value = json.dumps(solution)

            self.redis_client.setex(
                key,
                timedelta(hours=ttl_hours),
                value
            )

            logger.debug(f"Cached GTO solution {key} (TTL: {ttl_hours}h)")
            return True

        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Error caching GTO solution: {e}")
            return False

    # Equity Calculation Caching (30s TTL)

    def get_equity(self, equity_key: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Get cached equity calculation

        Args:
            equity_key: Equity state (hero cards, villain range, board)

        Returns:
            Cached equity percentages or None
        """
        if not self._is_available():
            return None

        try:
            key = f"eq:{self._generate_hash(equity_key)}"
            cached = self.redis_client.get(key)

            if cached:
                logger.debug(f"Cache hit: equity {key}")
                return json.loads(cached)

            return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading equity cache: {e}")
            return None

    def set_equity(
        self,
        equity_key: Dict[str, Any],
        equity_result: Dict[str, float],
        ttl_seconds: int = 30
    ) -> bool:
        """
        Cache equity calculation

        Args:
            equity_key: Equity state identifier
            equity_result: Equity percentages
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        if not self._is_available():
            return False

        try:
            key = f"eq:{self._generate_hash(equity_key)}"
            value = json.dumps(equity_result)

            self.redis_client.setex(
                key,
                timedelta(seconds=ttl_seconds),
                value
            )

            logger.debug(f"Cached equity {key} (TTL: {ttl_seconds}s)")
            return True

        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Error caching equity: {e}")
            return False

    # Factor List Caching (1h TTL)

    def get_factors(self, street: str, position: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached factor list

        Args:
            street: Current street
            position: Hero's position

        Returns:
            Cached factor list or None
        """
        if not self._is_available():
            return None

        try:
            key = f"factors:{street}:{position or 'any'}"
            cached = self.redis_client.get(key)

            if cached:
                logger.debug(f"Cache hit: factors {key}")
                return json.loads(cached)

            return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading factors cache: {e}")
            return None

    def set_factors(
        self,
        street: str,
        factors: List[Dict[str, Any]],
        position: Optional[str] = None,
        ttl_hours: int = 1
    ) -> bool:
        """
        Cache factor list

        Args:
            street: Current street
            factors: List of factors
            position: Hero's position
            ttl_hours: Time-to-live in hours

        Returns:
            True if cached successfully
        """
        if not self._is_available():
            return False

        try:
            key = f"factors:{street}:{position or 'any'}"
            value = json.dumps(factors)

            self.redis_client.setex(
                key,
                timedelta(hours=ttl_hours),
                value
            )

            logger.debug(f"Cached factors {key} (TTL: {ttl_hours}h)")
            return True

        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Error caching factors: {e}")
            return False

    # Cache Management

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Redis key pattern (e.g., "rec:*")

        Returns:
            Number of keys deleted
        """
        if not self._is_available():
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching {pattern}")
                return deleted
            return 0

        except RedisError as e:
            logger.warning(f"Error invalidating pattern {pattern}: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all SmartHelper cache entries

        Returns:
            True if successful
        """
        if not self._is_available():
            return False

        try:
            patterns = ["rec:*", "gto:*", "eq:*", "factors:*"]
            total_deleted = 0

            for pattern in patterns:
                total_deleted += self.invalidate_pattern(pattern)

            logger.info(f"Cleared all cache ({total_deleted} keys)")
            return True

        except RedisError as e:
            logger.warning(f"Error clearing cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self._is_available():
            return {"enabled": False, "available": False}

        try:
            info = self.redis_client.info("stats")

            # Count keys by prefix
            rec_count = len(self.redis_client.keys("rec:*"))
            gto_count = len(self.redis_client.keys("gto:*"))
            eq_count = len(self.redis_client.keys("eq:*"))
            factors_count = len(self.redis_client.keys("factors:*"))

            return {
                "enabled": True,
                "available": True,
                "total_keys": rec_count + gto_count + eq_count + factors_count,
                "recommendations": rec_count,
                "gto_solutions": gto_count,
                "equity_calculations": eq_count,
                "factor_lists": factors_count,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100
                )
            }

        except RedisError as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"enabled": True, "available": False, "error": str(e)}


# Global cache instance
_cache: Optional[SmartHelperCache] = None


def get_cache() -> SmartHelperCache:
    """Get or create global cache instance"""
    global _cache
    if _cache is None:
        _cache = SmartHelperCache()
    return _cache
