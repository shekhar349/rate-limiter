"""
Django integration for rate limiting.
"""

from functools import wraps
from typing import Optional, Callable
from django.http import JsonResponse, HttpRequest
from django.utils.deprecation import MiddlewareMixin

from .core import RateLimiter, RateLimitExceeded


class DjangoRateLimiter(MiddlewareMixin):
    """
    Rate limiter for Django applications.
    
    Usage:
        Option 1: Programmatic usage (similar to FastAPI/Flask)
        limiter = DjangoRateLimiter(
            get_response=app.get_response,
            max_requests=100,
            time_window=60,
            exempt_paths=["/admin/", "/static/"]
        )
        
        Option 2: Add to MIDDLEWARE in settings.py (uses defaults or settings)
        MIDDLEWARE = [
            ...
            'python_rate_limiter.django_integration.DjangoRateLimiter',
        ]
        And optionally configure in settings:
        RATE_LIMITER_MAX_REQUESTS = 100
        RATE_LIMITER_TIME_WINDOW = 60.0
        RATE_LIMITER_EXEMPT_PATHS = ["/admin/", "/static/"]
    """
    
    def __init__(
        self,
        get_response=None,
        max_requests: Optional[int] = None,
        time_window: Optional[float] = None,
        key_func: Optional[Callable[[HttpRequest], str]] = None,
        exempt_paths: Optional[list[str]] = None
    ):
        """
        Initialize Django rate limiter.
        
        Args:
            get_response: Django's get_response callable (provided by framework)
            max_requests: Maximum number of requests allowed (default: 100 or from settings)
            time_window: Time window in seconds (default: 60.0 or from settings)
            key_func: Function to extract key from request (default: uses client IP)
            exempt_paths: List of path patterns to exempt from rate limiting
        """
        super().__init__(get_response)
        
        # Try to get configuration from Django settings if not provided
        try:
            from django.conf import settings
            self.max_requests = max_requests if max_requests is not None else getattr(settings, 'RATE_LIMITER_MAX_REQUESTS', 100)
            self.time_window = time_window if time_window is not None else getattr(settings, 'RATE_LIMITER_TIME_WINDOW', 60.0)
            self.exempt_paths = exempt_paths if exempt_paths is not None else getattr(settings, 'RATE_LIMITER_EXEMPT_PATHS', [])
        except ImportError:
            # Django not available, use provided values or defaults
            self.max_requests = max_requests if max_requests is not None else 100
            self.time_window = time_window if time_window is not None else 60.0
            self.exempt_paths = exempt_paths or []
        
        self.rate_limiter = RateLimiter(self.max_requests, self.time_window, key_func)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP (when behind proxy/load balancer)
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.META.get("HTTP_X_REAL_IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        return request.META.get("REMOTE_ADDR", "unknown")
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def process_request(self, request: HttpRequest):
        """Django middleware process_request for rate limiting."""
        # Check if path is exempt
        if self._is_exempt(request.path):
            return None
        
        # Get key for rate limiting
        key = self._get_client_ip(request)
        request._rate_limit_key = key
        
        try:
            self.rate_limiter.check_rate_limit(key)
        except RateLimitExceeded as e:
            response = JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "retry_after": e.retry_after,
                    "message": "Too many requests. Please try again later."
                },
                status=429
            )
            response["Retry-After"] = str(int(e.retry_after) + 1)
            response["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
            response["X-RateLimit-Remaining"] = str(self.rate_limiter.get_remaining(key))
            response["X-RateLimit-Reset"] = str(int(self.rate_limiter.get_reset_time(key)))
            return response
        
        return None
    
    def process_response(self, request: HttpRequest, response):
        """Django middleware process_response to add rate limit headers."""
        if hasattr(request, "_rate_limit_key"):
            key = request._rate_limit_key
            remaining = self.rate_limiter.get_remaining(key)
            reset_time = self.rate_limiter.get_reset_time(key)
            
            response["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
            response["X-RateLimit-Remaining"] = str(remaining)
            response["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response


def rate_limit(
    max_requests: int = 100,
    time_window: float = 60.0,
    key_func: Optional[Callable[[HttpRequest], str]] = None
):
    """
    Decorator for rate limiting Django view functions.
    
    Usage:
        @rate_limit(max_requests=10, time_window=60)
        def my_view(request):
            return JsonResponse({"message": "Hello"})
    """
    limiter = RateLimiter(max_requests, time_window, key_func)
    
    def decorator(func):
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Get key for rate limiting
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                if forwarded_for:
                    key = forwarded_for.split(",")[0].strip()
                else:
                    real_ip = request.META.get("HTTP_X_REAL_IP")
                    key = real_ip if real_ip else request.META.get("REMOTE_ADDR", "unknown")
            
            try:
                limiter.check_rate_limit(key)
            except RateLimitExceeded as e:
                response = JsonResponse(
                    {
                        "error": "Rate limit exceeded",
                        "retry_after": e.retry_after,
                        "message": "Too many requests. Please try again later."
                    },
                    status=429
                )
                response["Retry-After"] = str(int(e.retry_after) + 1)
                response["X-RateLimit-Limit"] = str(limiter.max_requests)
                response["X-RateLimit-Remaining"] = str(limiter.get_remaining(key))
                response["X-RateLimit-Reset"] = str(int(limiter.get_reset_time(key)))
                return response
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator

