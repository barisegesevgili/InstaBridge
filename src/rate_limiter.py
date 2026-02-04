"""Rate limiting utilities to prevent Instagram account bans.

This module provides rate limiting to make automation appear more human-like
and reduce the risk of triggering Instagram's bot detection.
"""

import random
import time
from functools import wraps
from typing import Callable, TypeVar, cast

# Type variable for decorated functions
F = TypeVar("F", bound=Callable)


class RateLimiter:
    """Simple rate limiter with random jitter to appear human-like."""

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        requests_per_hour: int = 60,
    ):
        """Initialize rate limiter.

        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            requests_per_hour: Maximum requests per hour limit
        """
        self.min_delay = max(0.5, min_delay)
        self.max_delay = max(self.min_delay, max_delay)
        self.requests_per_hour = max(1, requests_per_hour)
        self.last_request_time = 0.0
        self.request_times: list[float] = []

    def wait(self) -> float:
        """Wait appropriate amount of time before next request.

        Returns:
            Actual delay applied (seconds)
        """
        now = time.time()

        # Clean old request times (older than 1 hour)
        hour_ago = now - 3600
        self.request_times = [t for t in self.request_times if t > hour_ago]

        # Check if we've hit hourly limit
        if len(self.request_times) >= self.requests_per_hour:
            # Calculate when we can make next request
            oldest_request = min(self.request_times)
            wait_until = oldest_request + 3600
            if now < wait_until:
                delay = wait_until - now
                print(
                    f"[rate_limiter] Hourly limit reached ({self.requests_per_hour} req/hour). Waiting {delay:.1f}s"
                )
                time.sleep(delay)
                now = time.time()

        # Apply random delay between min and max
        time_since_last = now - self.last_request_time
        needed_delay = self.min_delay - time_since_last

        if needed_delay > 0:
            # Add random jitter to appear human-like
            jitter = random.uniform(0, self.max_delay - self.min_delay)
            actual_delay = needed_delay + jitter
            time.sleep(actual_delay)
        else:
            actual_delay = 0.0

        # Record this request
        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)

        return actual_delay

    def __call__(self, func: F) -> F:
        """Decorator to rate-limit a function."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)

        return cast(F, wrapper)


# Pre-configured rate limiters for different use cases
class RateLimits:
    """Pre-configured rate limiters for different Instagram operations."""

    # Conservative (safest, recommended for new accounts)
    CONSERVATIVE = RateLimiter(
        min_delay=3.0,
        max_delay=7.0,
        requests_per_hour=40,
    )

    # Moderate (balanced, good for established throwaway accounts)
    MODERATE = RateLimiter(
        min_delay=2.0,
        max_delay=5.0,
        requests_per_hour=60,
    )

    # Aggressive (higher risk, only for testing)
    AGGRESSIVE = RateLimiter(
        min_delay=1.0,
        max_delay=3.0,
        requests_per_hour=80,
    )

    # Analytics (for follower/following lists - less strict)
    ANALYTICS = RateLimiter(
        min_delay=0.7,
        max_delay=1.5,
        requests_per_hour=100,
    )


def human_like_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Add a human-like delay with random variation.

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def rate_limit(
    min_delay: float = 2.0,
    max_delay: float = 5.0,
    requests_per_hour: int = 60,
) -> Callable:
    """Decorator factory for rate-limiting functions.

    Args:
        min_delay: Minimum delay between calls (seconds)
        max_delay: Maximum delay between calls (seconds)
        requests_per_hour: Maximum calls per hour

    Returns:
        Decorator function

    Example:
        @rate_limit(min_delay=2.0, max_delay=4.0)
        def fetch_posts():
            # This will be rate-limited
            pass
    """
    limiter = RateLimiter(min_delay, max_delay, requests_per_hour)
    return limiter


# Global limiter instance for Instagram operations (can be configured)
_global_limiter = RateLimits.MODERATE


def set_global_rate_limit(limiter: RateLimiter) -> None:
    """Set the global rate limiter.

    Args:
        limiter: RateLimiter instance to use globally
    """
    global _global_limiter
    _global_limiter = limiter


def get_global_rate_limiter() -> RateLimiter:
    """Get the current global rate limiter."""
    return _global_limiter
