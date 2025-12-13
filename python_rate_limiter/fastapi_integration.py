"""
FastAPI integration for rate limiting.
"""

from functools import wraps
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from .core import RateLimiter, RateLimitExceeded


class FastAPIRateLimiter:
    """
    Rate limiter for FastAPI applications.
    
    Usage:
        limiter = FastAPIRateLimiter(max_requests=100, time_window=60)
        app.add_middleware(limiter.middleware)
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60.0,
        key_func: Optional[Callable[[Request], str]] = None,
        exempt_paths: Optional[list[str]] = None
    ):
        """
        Initialize FastAPI rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            key_func: Function to extract key from request (default: uses client IP)
            exempt_paths: List of path patterns to exempt from rate limiting
        """
        self.rate_limiter = RateLimiter(max_requests, time_window, key_func)
        self.exempt_paths = exempt_paths or []
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    async def middleware(self, request: Request, call_next):
        """FastAPI middleware for rate limiting."""
        # Check if path is exempt
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # Get key for rate limiting
        key = self._get_client_ip(request)
        
        try:
            self.rate_limiter.check_rate_limit(key)
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": e.retry_after,
                    "message": "Too many requests. Please try again later."
                },
                headers={
                    "Retry-After": str(int(e.retry_after) + 1),
                    "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                    "X-RateLimit-Remaining": str(self.rate_limiter.get_remaining(key)),
                    "X-RateLimit-Reset": str(int(self.rate_limiter.get_reset_time(key)))
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = self.rate_limiter.get_remaining(key)
        reset_time = self.rate_limiter.get_reset_time(key)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response


def rate_limit(
    max_requests: int = 100,
    time_window: float = 60.0,
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    Decorator for rate limiting FastAPI route handlers.
    
    Usage:
        @app.get("/api/endpoint")
        @rate_limit(max_requests=10, time_window=60)
        async def endpoint():
            return {"message": "Hello"}
    """
    limiter = RateLimiter(max_requests, time_window, key_func)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get key for rate limiting
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    key = forwarded_for.split(",")[0].strip()
                else:
                    real_ip = request.headers.get("X-Real-IP")
                    key = real_ip if real_ip else (request.client.host if request.client else "unknown")
            
            try:
                limiter.check_rate_limit(key)
            except RateLimitExceeded as e:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": e.retry_after,
                        "message": "Too many requests. Please try again later."
                    },
                    headers={
                        "Retry-After": str(int(e.retry_after) + 1),
                        "X-RateLimit-Limit": str(limiter.max_requests),
                        "X-RateLimit-Remaining": str(limiter.get_remaining(key)),
                        "X-RateLimit-Reset": str(int(limiter.get_reset_time(key)))
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

