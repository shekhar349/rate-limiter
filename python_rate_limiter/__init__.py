"""
Rate Limiter - A Python library for rate limiting in FastAPI and Flask applications.
"""

from .core import RateLimiter, RateLimitExceeded

__version__ = "0.1.0"
__all__ = [
    "RateLimiter",
    "RateLimitExceeded",
]

# Optional FastAPI integration
try:
    from .fastapi_integration import FastAPIRateLimiter, rate_limit as fastapi_rate_limit
    __all__.extend(["FastAPIRateLimiter", "fastapi_rate_limit"])
except ImportError:
    # FastAPI is not installed - create helpful error classes
    class _FastAPINotInstalled:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "FastAPI integration requires FastAPI to be installed. "
                "Install it with: pip install python-rate-limiter[fastapi]"
            )
    
    FastAPIRateLimiter = _FastAPINotInstalled
    
    def fastapi_rate_limit(*args, **kwargs):
        raise ImportError(
            "FastAPI integration requires FastAPI to be installed. "
            "Install it with: pip install python-rate-limiter[fastapi]"
        )
    
    __all__.extend(["FastAPIRateLimiter", "fastapi_rate_limit"])

# Optional Flask integration
try:
    from .flask_integration import FlaskRateLimiter, rate_limit as flask_rate_limit
    __all__.extend(["FlaskRateLimiter", "flask_rate_limit"])
except ImportError:
    # Flask is not installed - create helpful error class
    class _FlaskNotInstalled:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Flask integration requires Flask to be installed. "
                "Install it with: pip install python-rate-limiter[flask]"
            )
    
    FlaskRateLimiter = _FlaskNotInstalled
    
    def flask_rate_limit(*args, **kwargs):
        raise ImportError(
            "Flask integration requires Flask to be installed. "
            "Install it with: pip install python-rate-limiter[flask]"
        )
    
    __all__.extend(["FlaskRateLimiter", "flask_rate_limit"])

