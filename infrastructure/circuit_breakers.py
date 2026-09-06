"""
Sentinel — Circuit Breaker Infrastructure

Implements circuit breaker patterns for external dependencies using PyBreaker.
Circuit breakers prevent cascading failures by failing fast when a dependency
is detected as unhealthy, and automatically recovering when health is restored.

Configuration:
    Redis Breaker:
        - fail_max: 5 failures before opening circuit
        - timeout_duration: 30 seconds before attempting recovery

    Kafka Breaker:
        - fail_max: 10 failures before opening circuit
        - timeout_duration: 60 seconds before attempting recovery

Usage:
    from infrastructure.circuit_breakers import redis_with_breaker, kafka_with_breaker

    # Wrap async operations
    result = await redis_with_breaker(async_redis_operation)
    await kafka_with_breaker(async_kafka_operation)

Production behavior:
    - Circuit CLOSED (healthy): All requests pass through normally
    - Circuit OPEN (failing): Requests fail immediately without calling dependency
    - Circuit HALF_OPEN (recovering): Limited requests pass through to test recovery

    When circuit is OPEN, Sentinel FAILS CLOSED (ESCALATE) to maintain security invariants.
"""

import logging
import functools
from typing import Callable, TypeVar, Any
from pybreaker import CircuitBreaker, CircuitBreakerError
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ─────────────────────────────────────────────────────────────────────────────
# Circuit Breaker Definitions
# ─────────────────────────────────────────────────────────────────────────────


class SentinelCircuitBreakerListener:
    """Listener for circuit breaker state changes (non-authoritative logging)."""

    def __init__(self, name: str):
        self.name = name

    def state_change(self, cb, old_state, new_state):
        """Called when circuit breaker changes state."""
        logger.warning(
            f"Circuit breaker state change: {self.name}",
            circuit=self.name,
            old_state=str(old_state),
            new_state=str(new_state),
            failure_count=cb.fail_counter,
        )

    def before_call(self, cb, func, *args, **kwargs):
        """Called before attempting a call through the breaker."""
        pass  # No-op, avoid log spam

    def success(self, cb):
        """Called on successful call."""
        pass  # No-op

    def failure(self, cb, exc):
        """Called on failed call."""
        logger.error(
            f"Circuit breaker detected failure: {self.name}",
            circuit=self.name,
            failure_count=cb.fail_counter,
            error=str(exc),
        )


# Redis Circuit Breaker
# Opens after 5 consecutive failures, recovers after 30 seconds
redis_breaker = CircuitBreaker(
    fail_max=5, timeout_duration=30, name="redis", listeners=[SentinelCircuitBreakerListener("redis")]
)

# Kafka Circuit Breaker
# Opens after 10 consecutive failures (higher threshold for transient issues)
# Recovers after 60 seconds (longer recovery for distributed system)
kafka_breaker = CircuitBreaker(
    fail_max=10, timeout_duration=60, name="kafka", listeners=[SentinelCircuitBreakerListener("kafka")]
)

# MLflow Circuit Breaker
# Opens after 3 failures (non-critical, fail fast)
mlflow_breaker = CircuitBreaker(
    fail_max=3, timeout_duration=45, name="mlflow", listeners=[SentinelCircuitBreakerListener("mlflow")]
)

# Database Circuit Breaker
# Opens after 5 failures, recovers after 20 seconds
database_breaker = CircuitBreaker(
    fail_max=5, timeout_duration=20, name="database", listeners=[SentinelCircuitBreakerListener("database")]
)


# ─────────────────────────────────────────────────────────────────────────────
# Async Wrapper Functions
# ─────────────────────────────────────────────────────────────────────────────


async def redis_with_breaker(operation: Callable[[], T]) -> T:
    """
    Execute Redis operation with circuit breaker protection.

    Args:
        operation: Async callable that performs Redis operation

    Returns:
        Result of the operation

    Raises:
        CircuitBreakerError: If circuit is open (Redis unavailable)
        Exception: Any exception from the underlying operation
    """
    try:
        # PyBreaker doesn't natively support async, so we wrap it
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: redis_breaker.call(lambda: asyncio.run(operation())))
        return result
    except CircuitBreakerError as e:
        logger.error(
            "Redis circuit breaker is OPEN — failing closed",
            circuit_state=str(redis_breaker.current_state),
            error=str(e),
        )
        raise
    except Exception as e:
        logger.error(f"Redis operation failed: {e}")
        raise


async def kafka_with_breaker(operation: Callable[[], T]) -> T:
    """
    Execute Kafka operation with circuit breaker protection.

    Args:
        operation: Async callable that performs Kafka operation

    Returns:
        Result of the operation

    Raises:
        CircuitBreakerError: If circuit is open (Kafka unavailable)
        Exception: Any exception from the underlying operation
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: kafka_breaker.call(lambda: asyncio.run(operation())))
        return result
    except CircuitBreakerError as e:
        logger.error(
            "Kafka circuit breaker is OPEN — failing closed",
            circuit_state=str(kafka_breaker.current_state),
            error=str(e),
        )
        raise
    except Exception as e:
        logger.error(f"Kafka operation failed: {e}")
        raise


async def database_with_breaker(operation: Callable[[], T]) -> T:
    """
    Execute database operation with circuit breaker protection.

    Args:
        operation: Async callable that performs database operation

    Returns:
        Result of the operation

    Raises:
        CircuitBreakerError: If circuit is open (database unavailable)
        Exception: Any exception from the underlying operation
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: database_breaker.call(lambda: asyncio.run(operation())))
        return result
    except CircuitBreakerError as e:
        logger.error(
            "Database circuit breaker is OPEN — failing closed",
            circuit_state=str(database_breaker.current_state),
            error=str(e),
        )
        raise
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Synchronous Decorator (for backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────


def with_circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator to wrap synchronous functions with circuit breaker.

    Usage:
        @with_circuit_breaker(redis_breaker)
        def redis_operation():
            return redis_client.get("key")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(
                    f"Circuit breaker {breaker.name} is OPEN", circuit=breaker.name, state=str(breaker.current_state)
                )
                raise

        return wrapper

    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Health Check Integration
# ─────────────────────────────────────────────────────────────────────────────


def get_circuit_breaker_status() -> dict:
    """
    Get current status of all circuit breakers for health checks.

    Returns:
        Dictionary with circuit breaker states
    """
    return {
        "redis": {
            "state": str(redis_breaker.current_state),
            "failure_count": redis_breaker.fail_counter,
            "last_failure": redis_breaker.last_failure_exception,
        },
        "kafka": {
            "state": str(kafka_breaker.current_state),
            "failure_count": kafka_breaker.fail_counter,
            "last_failure": kafka_breaker.last_failure_exception,
        },
        "database": {
            "state": str(database_breaker.current_state),
            "failure_count": database_breaker.fail_counter,
            "last_failure": database_breaker.last_failure_exception,
        },
        "mlflow": {
            "state": str(mlflow_breaker.current_state),
            "failure_count": mlflow_breaker.fail_counter,
            "last_failure": mlflow_breaker.last_failure_exception,
        },
    }


def is_system_healthy() -> bool:
    """
    Check if critical circuit breakers are healthy.

    Returns:
        True if all critical systems (Redis, Kafka, Database) are operational
    """
    critical_breakers = [redis_breaker, kafka_breaker, database_breaker]
    return all(str(breaker.current_state) != "open" for breaker in critical_breakers)
