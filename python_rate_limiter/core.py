"""
Core rate limiter implementation using sliding window algorithm.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Optional, Callable


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: float, message: str = "Rate limit exceeded"):
        self.retry_after = retry_after
        self.message = message
        super().__init__(self.message)


class RateLimiter:
    """
    A thread-safe rate limiter using sliding window algorithm.
    
    Args:
        max_requests: Maximum number of requests allowed
        time_window: Time window in seconds
        key_func: Optional function to extract key from request (default: uses IP address)
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60.0,
        key_func: Optional[Callable] = None
    ):
        if max_requests <= 0:
            raise ValueError("max_requests must be greater than 0")
        if time_window <= 0:
            raise ValueError("time_window must be greater than 0")
        
        self.max_requests = max_requests
        self.time_window = time_window
        self.key_func = key_func
        
        # Store request timestamps for each key
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
    
    def _cleanup_old_requests(self, key: str, current_time: float):
        """Remove requests outside the time window."""
        cutoff_time = current_time - self.time_window
        self._requests[key] = [
            timestamp
            for timestamp in self._requests[key]
            if timestamp > cutoff_time
        ]
    
    def is_allowed(self, key: str) -> tuple[bool, Optional[float]]:
        """
        Check if a request is allowed.
        
        Args:
            key: Unique identifier for the rate limit (e.g., IP address, user ID)
        
        Returns:
            Tuple of (is_allowed, retry_after)
            - is_allowed: True if request is allowed, False otherwise
            - retry_after: Seconds to wait before retrying (None if allowed)
        """
        current_time = time.time()
        
        with self._lock:
            self._cleanup_old_requests(key, current_time)
            
            if len(self._requests[key]) >= self.max_requests:
                # Calculate retry_after based on oldest request in window
                oldest_request = min(self._requests[key])
                retry_after = (oldest_request + self.time_window) - current_time
                return False, max(0, retry_after)
            
            # Add current request
            self._requests[key].append(current_time)
            return True, None
    
    def check_rate_limit(self, key: str):
        """
        Check rate limit and raise exception if exceeded.
        
        Args:
            key: Unique identifier for the rate limit
        
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        is_allowed, retry_after = self.is_allowed(key)
        if not is_allowed:
            raise RateLimitExceeded(retry_after)
    
    def reset(self, key: Optional[str] = None):
        """
        Reset rate limit for a specific key or all keys.
        
        Args:
            key: Key to reset. If None, resets all keys.
        """
        with self._lock:
            if key is None:
                self._requests.clear()
            elif key in self._requests:
                del self._requests[key]
    
    def get_remaining(self, key: str) -> int:
        """
        Get remaining requests for a key.
        
        Args:
            key: Unique identifier for the rate limit
        
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        
        with self._lock:
            self._cleanup_old_requests(key, current_time)
            remaining = self.max_requests - len(self._requests[key])
            return max(0, remaining)
    
    def get_reset_time(self, key: str) -> float:
        """
        Get the time when the rate limit will reset for a key.
        
        Args:
            key: Unique identifier for the rate limit
        
        Returns:
            Unix timestamp when rate limit resets
        """
        current_time = time.time()
        
        with self._lock:
            self._cleanup_old_requests(key, current_time)
            if not self._requests[key]:
                return current_time
            
            oldest_request = min(self._requests[key])
            return oldest_request + self.time_window

