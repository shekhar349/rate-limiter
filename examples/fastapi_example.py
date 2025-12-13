"""
FastAPI example demonstrating rate limiter usage.
"""

from fastapi import FastAPI, Request
from python_rate_limiter import FastAPIRateLimiter, rate_limit

app = FastAPI(title="Rate Limiter FastAPI Example")

# Example 1: Using middleware (applies to all routes)
limiter = FastAPIRateLimiter(
    max_requests=100,
    time_window=60.0,  # 100 requests per 60 seconds
    exempt_paths=["/health", "/docs", "/openapi.json"]
)

app.middleware("http")(limiter.middleware)


@app.get("/health")
async def health():
    """Health check endpoint (exempt from rate limiting)"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint (rate limited by middleware)"""
    return {"message": "Hello World", "note": "This endpoint is rate limited"}


@app.get("/api/data")
async def get_data():
    """API endpoint (rate limited by middleware)"""
    return {"data": "some data", "note": "This endpoint is rate limited"}


# Example 2: Using decorator (per-route rate limiting)
@app.get("/api/strict")
@rate_limit(max_requests=5, time_window=60)  # 5 requests per 60 seconds
async def strict_endpoint(request: Request):
    """Strictly rate limited endpoint"""
    return {
        "message": "This endpoint has stricter rate limiting",
        "limit": "5 requests per 60 seconds"
    }


# Example 3: Custom key function (rate limit by user ID)
def get_user_id(request: Request) -> str:
    """Extract user ID from request headers"""
    return request.headers.get("X-User-ID", "anonymous")


@app.get("/api/user-data")
@rate_limit(max_requests=50, time_window=60, key_func=get_user_id)
async def user_data(request: Request):
    """User-specific rate limited endpoint"""
    user_id = get_user_id(request)
    return {
        "message": f"Data for user {user_id}",
        "note": "Rate limited per user ID"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

