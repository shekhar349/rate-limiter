# Rate Limiter

A Python rate limiter library for FastAPI and Flask applications. This library provides a simple, thread-safe rate limiting implementation using a sliding window algorithm.

[![PyPI version](https://badge.fury.io/py/python-rate-limiter.svg)](https://pypi.org/project/python-rate-limiter/)
[![GitHub](https://img.shields.io/github/stars/shekhar349/rate-limiter?style=social)](https://github.com/shekhar349/rate-limiter)

- **PyPI**: https://pypi.org/project/python-rate-limiter/
- **GitHub**: https://github.com/shekhar349/rate-limiter

## Features

- 🚀 **Easy to use** - Simple API for both FastAPI and Flask
- 🔒 **Thread-safe** - Safe for concurrent requests
- ⚡ **Lightweight** - No external dependencies for core functionality
- 🎯 **Flexible** - Support for custom key functions and exempt paths
- 📊 **Headers** - Automatic rate limit headers in responses

## Installation

Install the package from PyPI:

```bash
pip install python-rate-limiter
```

For framework-specific integrations, install with extras:

```bash
# FastAPI
pip install python-rate-limiter[fastapi]

# Flask
pip install python-rate-limiter[flask]

# Both frameworks
pip install python-rate-limiter[all]
```

### Alternative Installation Methods

**Install from GitHub (latest development version):**

```bash
pip install git+https://github.com/shekhar349/rate-limiter.git
```

**Install from local source (for development):**

```bash
# Install in development mode (editable)
pip install -e .

# With extras
pip install -e ".[fastapi]"  # or [flask] or [all]
```

## Quick Start

**Note:** When using decorators, import the framework-specific decorator:
- FastAPI: Use `fastapi_rate_limit`
- Flask: Use `flask_rate_limit`

This ensures you get the correct decorator for your framework (async for FastAPI, sync for Flask).

### FastAPI

#### Using Middleware (Recommended)

```python
from fastapi import FastAPI
from python_rate_limiter import FastAPIRateLimiter

app = FastAPI()

# Initialize rate limiter
limiter = FastAPIRateLimiter(
    max_requests=100,
    time_window=60.0,  # 60 seconds
    exempt_paths=["/health", "/docs"]  # Optional: exempt certain paths
)

# Add middleware
app.middleware("http")(limiter.middleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/data")
async def get_data():
    return {"data": "some data"}
```

#### Using Decorator

```python
from fastapi import FastAPI, Request
from python_rate_limiter import fastapi_rate_limit

app = FastAPI()

@app.get("/api/endpoint")
@fastapi_rate_limit(max_requests=10, time_window=60)
async def endpoint(request: Request):
    return {"message": "Hello"}
```

#### Custom Key Function

```python
from fastapi import FastAPI, Request
from python_rate_limiter import fastapi_rate_limit

app = FastAPI()

def get_user_id(request: Request) -> str:
    # Extract user ID from request (e.g., from JWT token)
    return request.headers.get("X-User-ID", "anonymous")

@app.get("/api/user-data")
@fastapi_rate_limit(max_requests=50, time_window=60, key_func=get_user_id)
async def user_data(request: Request):
    return {"user_data": "..."}
```

### Flask

#### Using Extension (Recommended)

```python
from flask import Flask
from python_rate_limiter import FlaskRateLimiter

app = Flask(__name__)

# Initialize rate limiter
limiter = FlaskRateLimiter(
    max_requests=100,
    time_window=60.0,
    exempt_paths=["/health", "/static"]  # Optional: exempt certain paths
)

# Initialize with app
limiter.init_app(app)

@app.route("/")
def root():
    return {"message": "Hello World"}

@app.route("/api/data")
def get_data():
    return {"data": "some data"}
```

#### Using Decorator

```python
from flask import Flask
from python_rate_limiter import flask_rate_limit

app = Flask(__name__)

@app.route("/api/endpoint")
@flask_rate_limit(max_requests=10, time_window=60)
def endpoint():
    return {"message": "Hello"}
```

#### Custom Key Function

```python
from flask import Flask, request
from python_rate_limiter import flask_rate_limit

app = Flask(__name__)

def get_user_id() -> str:
    # Extract user ID from request (e.g., from session or JWT)
    return request.headers.get("X-User-ID", "anonymous")

@app.route("/api/user-data")
@flask_rate_limit(max_requests=50, time_window=60, key_func=get_user_id)
def user_data():
    return {"user_data": "..."}
```

## Core API

### RateLimiter

The core rate limiter class can be used independently:

```python
from python_rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=100, time_window=60.0)

# Check if request is allowed
is_allowed, retry_after = limiter.is_allowed("user_ip_address")
if not is_allowed:
    print(f"Rate limit exceeded. Retry after {retry_after} seconds")

# Or raise exception
try:
    limiter.check_rate_limit("user_ip_address")
except RateLimitExceeded as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")

# Get remaining requests
remaining = limiter.get_remaining("user_ip_address")

# Reset rate limit
limiter.reset("user_ip_address")  # Reset specific key
limiter.reset()  # Reset all keys
```

## Response Headers

The library automatically adds rate limit headers to responses:

- `X-RateLimit-Limit`: Maximum number of requests allowed
- `X-RateLimit-Remaining`: Number of remaining requests
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `Retry-After`: Seconds to wait before retrying (when rate limit exceeded)

## Error Responses

When rate limit is exceeded, the library returns:

- **Status Code**: `429 Too Many Requests`
- **Response Body**:
  ```json
  {
    "error": "Rate limit exceeded",
    "retry_after": 45.2,
    "message": "Too many requests. Please try again later."
  }
  ```

## Configuration Options

### FastAPIRateLimiter / FlaskRateLimiter

- `max_requests` (int): Maximum number of requests allowed (default: 100)
- `time_window` (float): Time window in seconds (default: 60.0)
- `key_func` (Callable): Function to extract key from request (default: uses IP address)
- `exempt_paths` (list[str]): List of path patterns to exempt from rate limiting

### Rate Limiter Algorithm

The library uses a **sliding window** algorithm, which provides accurate rate limiting by tracking individual request timestamps within the time window.

## Examples

See the `examples/` directory for complete working examples.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request on [GitHub](https://github.com/shekhar349/rate-limiter).

