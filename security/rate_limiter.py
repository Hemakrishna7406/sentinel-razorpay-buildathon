"""
Redis-backed rate limiter using token bucket algorithm.

Implements sliding window rate limiting to prevent abuse and DoS attacks.
Uses Redis for distributed rate limiting across multiple API instances.
"""

import time
from typing import Optional
from security.exceptions import SentinelSecurityException


class RedisRateLimiter:
    """Token bucket rate limiter with Redis backend."""

    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            redis_client: Async Redis client
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check_rate_limit(self, key: str) -> bool:
        """
        Check if the request is within rate limits.

        Uses sliding window algorithm with Redis sorted sets.

        Args:
            key: Unique identifier for the rate limit bucket (e.g., agent_id, IP)

        Returns:
            True if allowed

        Raises:
            SentinelSecurityException: If rate limit exceeded
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Redis key for this bucket
        redis_key = f"ratelimit:{key}"

        # Remove old entries outside the window
        await self.redis.zremrangebyscore(redis_key, 0, window_start)

        # Count current requests in window
        current_count = await self.redis.zcard(redis_key)

        if current_count >= self.max_requests:
            raise SentinelSecurityException(
                f"Rate limit exceeded for {key}. "
                f"Maximum {self.max_requests} requests per {self.window_seconds} seconds."
            )

        # Add current request with timestamp as score
        await self.redis.zadd(redis_key, {str(now): now})

        # Set expiry on the key to auto-cleanup
        await self.redis.expire(redis_key, self.window_seconds)

        return True

    async def get_remaining(self, key: str) -> int:
        """
        Get remaining requests available in the current window.

        Args:
            key: Unique identifier for the rate limit bucket

        Returns:
            Number of remaining requests
        """
        now = time.time()
        window_start = now - self.window_seconds
        redis_key = f"ratelimit:{key}"

        # Clean up old entries
        await self.redis.zremrangebyscore(redis_key, 0, window_start)

        # Count current requests
        current_count = await self.redis.zcard(redis_key)

        return max(0, self.max_requests - current_count)

    async def reset(self, key: str) -> None:
        """
        Reset rate limit for a specific key (admin operation).

        Args:
            key: Unique identifier for the rate limit bucket
        """
        redis_key = f"ratelimit:{key}"
        await self.redis.delete(redis_key)
