"""
Flask integration for rate limiting.
"""

from functools import wraps
from typing import Optional, Callable
from flask import request, jsonify, g

from .core import RateLimiter, RateLimitExceeded


class FlaskRateLimiter:
    """
    Rate limiter for Flask applications.
    
    Usage:
        limiter = FlaskRateLimiter(max_requests=100, time_window=60)
        app.before_request(limiter.before_request)
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60.0,
        key_func: Optional[Callable[[], str]] = None,
        exempt_paths: Optional[list[str]] = None
    ):
        """
        Initialize Flask rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            key_func: Function to extract key from request (default: uses client IP)
            exempt_paths: List of path patterns to exempt from rate limiting
        """
        self.rate_limiter = RateLimiter(max_requests, time_window, key_func)
        self.exempt_paths = exempt_paths or []
        self.app = None
    
    def init_app(self, app):
        """Initialize Flask app with rate limiter."""
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def _get_client_ip(self) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        return request.remote_addr or "unknown"
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def before_request(self):
        """Flask before_request handler for rate limiting."""
        # Check if path is exempt
        if self._is_exempt(request.path):
            return None
        
        # Get key for rate limiting
        key = self._get_client_ip()
        g.rate_limit_key = key
        
        try:
            self.rate_limiter.check_rate_limit(key)
        except RateLimitExceeded as e:
            response = jsonify({
                "error": "Rate limit exceeded",
                "retry_after": e.retry_after,
                "message": "Too many requests. Please try again later."
            })
            response.status_code = 429
            response.headers["Retry-After"] = str(int(e.retry_after) + 1)
            response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(self.rate_limiter.get_remaining(key))
            response.headers["X-RateLimit-Reset"] = str(int(self.rate_limiter.get_reset_time(key)))
            return response
        
        return None
    
    def after_request(self, response):
        """Flask after_request handler to add rate limit headers."""
        if hasattr(g, "rate_limit_key"):
            key = g.rate_limit_key
            remaining = self.rate_limiter.get_remaining(key)
            reset_time = self.rate_limiter.get_reset_time(key)
            
            response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response


def rate_limit(
    max_requests: int = 100,
    time_window: float = 60.0,
    key_func: Optional[Callable[[], str]] = None
):
    """
    Decorator for rate limiting Flask route handlers.
    
    Usage:
        @app.route("/api/endpoint")
        @rate_limit(max_requests=10, time_window=60)
        def endpoint():
            return jsonify({"message": "Hello"})
    """
    limiter = RateLimiter(max_requests, time_window, key_func)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get key for rate limiting
            if key_func:
                key = key_func()
            else:
                # Default: use IP address
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    key = forwarded_for.split(",")[0].strip()
                else:
                    real_ip = request.headers.get("X-Real-IP")
                    key = real_ip if real_ip else (request.remote_addr or "unknown")
            
            try:
                limiter.check_rate_limit(key)
            except RateLimitExceeded as e:
                response = jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": e.retry_after,
                    "message": "Too many requests. Please try again later."
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(int(e.retry_after) + 1)
                response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
                response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining(key))
                response.headers["X-RateLimit-Reset"] = str(int(limiter.get_reset_time(key)))
                return response
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

