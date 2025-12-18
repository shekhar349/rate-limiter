# Testing the FastAPI Example

This guide explains how to test the `fastapi_example.py` file.

## Quick Start

### Prerequisites

To run the FastAPI example, install the required dependencies:

1. **uvicorn** (required to run the server):
```bash
pip install uvicorn
```

2. **requests** (optional, for automated testing):
```bash
pip install requests
```

### 1. Start the FastAPI Server

**Note:** Make sure you have `uvicorn` installed (see Prerequisites above).

In one terminal, run:

```bash
python examples/fastapi_example.py
```

The server will start on `http://localhost:8000`

**Quick Links:**
- **Swagger UI (Interactive API Docs)**: http://localhost:8000/docs
- **ReDoc (Alternative API Docs)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 2. Test Options

You have three options for testing:

#### Option A: Automated Test Script (Recommended)

Install requests first (if not already installed):
```bash
pip install requests
```

Then run the automated test script in another terminal:

```bash
python examples/test_fastapi_example.py
```

This script will:
- Test all endpoints
- Verify rate limiting works correctly
- Check rate limit headers
- Test exempt endpoints
- Test user-specific rate limiting

#### Option B: Manual Testing with curl

```bash
# Test health endpoint (exempt from rate limiting)
curl http://localhost:8000/health

# Test root endpoint (rate limited by middleware - 100 req/60s)
curl http://localhost:8000/

# Test strict endpoint (5 req/60s)
curl http://localhost:8000/api/strict

# Test user-specific endpoint with custom header
curl -H "X-User-ID: user123" http://localhost:8000/api/user-data

# Make multiple requests to test rate limiting
for i in {1..10}; do curl http://localhost:8000/api/strict; echo ""; done
```

#### Option C: Browser / Swagger UI / Postman

**Interactive API Documentation (Swagger UI):**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

1. Open http://localhost:8000/docs in your browser (FastAPI's interactive Swagger UI)
2. Test endpoints directly from the UI - you can see all available endpoints and test them interactively
3. Use the browser's developer tools (F12) to check response headers
4. Alternatively, use Postman or similar tools to test endpoints with custom headers

## Testing Rate Limiting Behavior

### Test 1: Middleware Rate Limiting

The middleware applies to all routes except exempt paths:
- Limit: 100 requests per 60 seconds
- Test by making many requests to `/` or `/api/data`

```bash
# Make 101 requests - the last one should be rate limited
for i in {1..101}; do curl -s http://localhost:8000/ | head -1; done
```

### Test 2: Strict Decorator Rate Limiting

The `/api/strict` endpoint has stricter limits:
- Limit: 5 requests per 60 seconds
- Test by making 6+ requests quickly

```bash
# This should show rate limiting after 5 requests
for i in {1..7}; do 
  curl -s http://localhost:8000/api/strict
  echo ""
done
```

### Test 3: User-Specific Rate Limiting

The `/api/user-data` endpoint limits per user ID:
- Each user gets their own 50 req/60s limit
- Test with different `X-User-ID` headers

```bash
# User 1 - should work
curl -H "X-User-ID: alice" http://localhost:8000/api/user-data

# User 2 - should work (separate limit)
curl -H "X-User-ID: bob" http://localhost:8000/api/user-data

# User 1 again - counts against alice's limit
curl -H "X-User-ID: alice" http://localhost:8000/api/user-data
```

### Test 4: Exempt Endpoints

These endpoints should never be rate limited:
- `/health`
- `/docs`
- `/openapi.json`

```bash
# Should always return 200, even with many requests
for i in {1..200}; do curl -s http://localhost:8000/health; done
```

## Understanding Rate Limit Headers

Each response includes these headers:

- `X-RateLimit-Limit`: Maximum requests allowed (e.g., "100")
- `X-RateLimit-Remaining`: Remaining requests in current window (e.g., "95")
- `X-RateLimit-Reset`: Unix timestamp when limit resets (e.g., "1234567890")
- `Retry-After`: Seconds to wait before retrying (only on 429 responses)

## Expected Behavior

### Successful Request (200 OK)
```json
{
  "message": "Hello World",
  "note": "This endpoint is rate limited"
}
```

Headers:
- Status: 200
- `X-RateLimit-Remaining`: 99, 98, 97, ...

### Rate Limited Request (429 Too Many Requests)
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 45.2,
  "message": "Too many requests. Please try again later."
}
```

Headers:
- Status: 429
- `Retry-After`: seconds to wait
- `X-RateLimit-Remaining`: 0

## Troubleshooting

### Server won't start
- Make sure you have uvicorn installed: `pip install uvicorn`
- Check if port 8000 is already in use
- Verify dependencies: `pip install -e ".[fastapi]"`

### Rate limiting not working
- Check that the middleware/decorator is properly applied
- Verify the endpoint is not in the exempt_paths list
- Make sure you're making requests fast enough (within the time window)

### Can't see rate limit headers
- Use `curl -v` to see all headers
- Check browser developer tools (Network tab)
- The headers should be present in all responses

