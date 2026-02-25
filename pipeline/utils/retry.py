"""
Retry decorator with exponential backoff for API calls.

Handles rate limits, timeouts, and server errors gracefully.
"""

import time
import random
import logging
import functools
from typing import Callable, Type, Tuple

# OpenAI error types we handle
try:
    from openai import RateLimitError, APITimeoutError, APIStatusError
    OPENAI_ERRORS = (RateLimitError, APITimeoutError, APIStatusError)
except ImportError:
    OPENAI_ERRORS = ()


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    jitter: float = 0.5,
    retryable_exceptions: Tuple[Type[Exception], ...] = None,
    logger: logging.Logger = None
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter: Random jitter factor (0-1) to prevent thundering herd
        retryable_exceptions: Tuple of exception types to retry on
        logger: Logger instance for retry messages

    Usage:
        @retry_with_backoff(max_retries=5, base_delay=2.0)
        def call_api():
            ...
    """
    if retryable_exceptions is None:
        retryable_exceptions = OPENAI_ERRORS if OPENAI_ERRORS else (Exception,)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    # Check if it's a server error (5xx)
                    is_server_error = False
                    if hasattr(e, 'status_code'):
                        is_server_error = 500 <= e.status_code < 600

                    # Check if rate limit or timeout
                    is_rate_limit = 'RateLimitError' in type(e).__name__
                    is_timeout = 'Timeout' in type(e).__name__

                    if not (is_server_error or is_rate_limit or is_timeout):
                        # Don't retry client errors (4xx except 429)
                        if hasattr(e, 'status_code') and 400 <= e.status_code < 500:
                            if e.status_code != 429:  # 429 is rate limit
                                raise

                    if attempt >= max_retries:
                        log.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    # Add jitter
                    jitter_amount = delay * jitter * random.random()
                    delay = delay + jitter_amount

                    log.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {type(e).__name__}: {str(e)[:100]}. "
                        f"Waiting {delay:.1f}s..."
                    )

                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryConfig:
    """Configuration holder for retry settings."""

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        jitter: float = 0.5
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def decorator(self, logger: logging.Logger = None) -> Callable:
        """Get a decorator with these settings."""
        return retry_with_backoff(
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            jitter=self.jitter,
            logger=logger
        )
