"""
Flask example demonstrating rate limiter usage.
"""

from flask import Flask, request, jsonify
from python_rate_limiter import FlaskRateLimiter, rate_limit

app = Flask(__name__)

# Example 1: Using extension (applies to all routes)
limiter = FlaskRateLimiter(
    max_requests=100,
    time_window=60.0,  # 100 requests per 60 seconds
    exempt_paths=["/health", "/static"]
)

limiter.init_app(app)


@app.route("/health")
def health():
    """Health check endpoint (exempt from rate limiting)"""
    return jsonify({"status": "healthy"})


@app.route("/")
def root():
    """Root endpoint (rate limited by extension)"""
    return jsonify({
        "message": "Hello World",
        "note": "This endpoint is rate limited"
    })


@app.route("/api/data")
def get_data():
    """API endpoint (rate limited by extension)"""
    return jsonify({
        "data": "some data",
        "note": "This endpoint is rate limited"
    })


# Example 2: Using decorator (per-route rate limiting)
@app.route("/api/strict")
@rate_limit(max_requests=5, time_window=60)  # 5 requests per 60 seconds
def strict_endpoint():
    """Strictly rate limited endpoint"""
    return jsonify({
        "message": "This endpoint has stricter rate limiting",
        "limit": "5 requests per 60 seconds"
    })


# Example 3: Custom key function (rate limit by user ID)
def get_user_id() -> str:
    """Extract user ID from request headers"""
    return request.headers.get("X-User-ID", "anonymous")


@app.route("/api/user-data")
@rate_limit(max_requests=50, time_window=60, key_func=get_user_id)
def user_data():
    """User-specific rate limited endpoint"""
    user_id = get_user_id()
    return jsonify({
        "message": f"Data for user {user_id}",
        "note": "Rate limited per user ID"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

