# Testing the Flask Example

This guide explains how to test the `flask_example.py` file.

## Quick Start

### Prerequisites

For automated testing, install the `requests` library:
```bash
pip install requests
```

### 1. Start the Flask Server

In one terminal, run:

```bash
python examples/flask_example.py
```

The server will start on `http://localhost:5000`

### 2. Test Options

You have three options for testing:

#### Option A: Automated Test Script (Recommended)

Install requests first (if not already installed):
```bash
pip install requests
```

Then run the automated test script in another terminal:

```bash
python examples/test_flask_example.py
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
curl http://localhost:5000/health

# Test root endpoint (rate limited by extension - 100 req/60s)
curl http://localhost:5000/

# Test strict endpoint (5 req/60s)
curl http://localhost:5000/api/strict

# Test user-specific endpoint with custom header
curl -H "X-User-ID: user123" http://localhost:5000/api/user-data

# Make multiple requests to test rate limiting
for i in {1..10}; do curl http://localhost:5000/api/strict; echo ""; done
```

**Windows PowerShell:**
```powershell
# Test basic endpoint
curl http://localhost:5000/

# Test multiple requests
1..10 | ForEach-Object { curl http://localhost:5000/api/strict; Write-Host "" }
```

#### Option C: Browser / Postman

1. Open `http://localhost:5000/` in your browser
2. Use browser's developer tools (F12) to check response headers
3. Use Postman or similar tool to test endpoints with custom headers

## Testing Rate Limiting Behavior

### Test 1: Extension Rate Limiting

The extension applies to all routes except exempt paths:
- Limit: 100 requests per 60 seconds
- Test by making many requests to `/` or `/api/data`

```bash
# Make 101 requests - the last one should be rate limited
for i in {1..101}; do curl -s http://localhost:5000/ | head -1; done
```

**Windows PowerShell:**
```powershell
1..101 | ForEach-Object { (Invoke-WebRequest -Uri http://localhost:5000/).Content }
```

### Test 2: Strict Decorator Rate Limiting

The `/api/strict` endpoint has stricter limits:
- Limit: 5 requests per 60 seconds
- Test by making 6+ requests quickly

```bash
# This should show rate limiting after 5 requests
for i in {1..7}; do 
  curl -s http://localhost:5000/api/strict
  echo ""
done
```

**Windows PowerShell:**
```powershell
1..7 | ForEach-Object { 
  (Invoke-WebRequest -Uri http://localhost:5000/api/strict).Content
  Write-Host ""
}
```

### Test 3: User-Specific Rate Limiting

The `/api/user-data` endpoint limits per user ID:
- Each user gets their own 50 req/60s limit
- Test with different `X-User-ID` headers

```bash
# User 1 - should work
curl -H "X-User-ID: alice" http://localhost:5000/api/user-data

# User 2 - should work (separate limit)
curl -H "X-User-ID: bob" http://localhost:5000/api/user-data

# User 1 again - counts against alice's limit
curl -H "X-User-ID: alice" http://localhost:5000/api/user-data
```

**Windows PowerShell:**
```powershell
# User 1
Invoke-WebRequest -Uri http://localhost:5000/api/user-data -Headers @{"X-User-ID"="alice"}

# User 2
Invoke-WebRequest -Uri http://localhost:5000/api/user-data -Headers @{"X-User-ID"="bob"}
```

### Test 4: Exempt Endpoints

These endpoints should never be rate limited:
- `/health`
- `/static/*` (any path starting with /static)

```bash
# Should always return 200, even with many requests
for i in {1..200}; do curl -s http://localhost:5000/health; done
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
- Make sure you have Flask installed: `pip install flask`
- Check if port 5000 is already in use
- Verify dependencies: `pip install -e ".[flask]"`

### Rate limiting not working
- Check that the extension/decorator is properly applied
- Verify the endpoint is not in the exempt_paths list
- Make sure you're making requests fast enough (within the time window)
- Check Flask debug mode isn't interfering (though it shouldn't)

### Can't see rate limit headers
- Use `curl -v` to see all headers
- Check browser developer tools (Network tab)
- The headers should be present in all responses

### Port 5000 already in use
If port 5000 is already in use, you can change it in `flask_example.py`:
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)  # Changed to 5001
```

Then update `BASE_URL` in `test_flask_example.py` accordingly.

## Flask-Specific Notes

- Flask uses a `before_request` and `after_request` approach for rate limiting
- The `FlaskRateLimiter` uses the `init_app()` pattern following Flask extension conventions
- Static files (served from `/static`) are automatically exempt from rate limiting
- The decorator-based rate limiting works independently of the extension

