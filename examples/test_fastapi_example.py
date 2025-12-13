"""
Test script for FastAPI rate limiter example.

This script demonstrates how to test the FastAPI example endpoints
and verify that rate limiting works correctly.

Prerequisites:
    pip install requests

Run the FastAPI server first:
    python examples/fastapi_example.py

Then run this test script in another terminal:
    python examples/test_fastapi_example.py
"""

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required for this test script.")
    print("Install it with: pip install requests")
    exit(1)

import time
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def print_response(response: requests.Response, label: str = ""):
    """Pretty print response with rate limit headers."""
    print(f"\n{'='*60}")
    if label:
        print(f"Test: {label}")
    print(f"Status: {response.status_code}")
    print(f"Headers:")
    for key, value in response.headers.items():
        if key.startswith("X-RateLimit") or key == "Retry-After":
            print(f"  {key}: {value}")
    print(f"Body: {response.json()}")
    print(f"{'='*60}\n")


def test_health_endpoint():
    """Test health endpoint (should be exempt from rate limiting)."""
    print("Testing /health endpoint (exempt from rate limiting)...")
    for i in range(5):
        response = requests.get(f"{BASE_URL}/health")
        print_response(response, f"Health check #{i+1}")
        assert response.status_code == 200, "Health endpoint should always return 200"


def test_middleware_rate_limiting():
    """Test middleware-based rate limiting on root endpoint."""
    print("Testing middleware rate limiting on / endpoint...")
    print("Making 5 requests (should all succeed)...")
    
    for i in range(5):
        response = requests.get(f"{BASE_URL}/")
        print_response(response, f"Request #{i+1}")
        assert response.status_code == 200, f"Request #{i+1} should succeed"
        remaining = int(response.headers.get("X-RateLimit-Remaining", "0"))
        print(f"  Remaining requests: {remaining}")


def test_strict_rate_limiting():
    """Test decorator-based rate limiting with strict limits."""
    print("Testing strict rate limiting on /api/strict endpoint...")
    print("Limit: 5 requests per 60 seconds")
    
    print("\nMaking 7 requests (first 5 should succeed, last 2 should fail)...")
    for i in range(7):
        response = requests.get(f"{BASE_URL}/api/strict")
        if response.status_code == 200:
            print(f"Request #{i+1}: SUCCESS - {response.json()}")
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            print(f"  Remaining: {remaining}")
        elif response.status_code == 429:
            print(f"Request #{i+1}: RATE LIMITED - {response.json()}")
            retry_after = response.headers.get("Retry-After", "unknown")
            print(f"  Retry-After: {retry_after} seconds")
        else:
            print(f"Request #{i+1}: Unexpected status {response.status_code}")
        
        time.sleep(0.5)  # Small delay between requests


def test_user_specific_rate_limiting():
    """Test user-specific rate limiting with custom key function."""
    print("Testing user-specific rate limiting on /api/user-data endpoint...")
    
    # Test with different user IDs
    user1 = "user-123"
    user2 = "user-456"
    
    print(f"\nMaking 3 requests as {user1}...")
    for i in range(3):
        response = requests.get(
            f"{BASE_URL}/api/user-data",
            headers={"X-User-ID": user1}
        )
        print_response(response, f"{user1} - Request #{i+1}")
        assert response.status_code == 200, f"Request #{i+1} should succeed"
    
    print(f"\nMaking 3 requests as {user2} (should be independent)...")
    for i in range(3):
        response = requests.get(
            f"{BASE_URL}/api/user-data",
            headers={"X-User-ID": user2}
        )
        print_response(response, f"{user2} - Request #{i+1}")
        assert response.status_code == 200, f"Request #{i+1} should succeed"
        print(f"  Note: Rate limits are per-user, so {user2} has separate limits")


def test_rate_limit_headers():
    """Test that rate limit headers are present in responses."""
    print("Testing rate limit headers...")
    response = requests.get(f"{BASE_URL}/api/data")
    
    required_headers = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    for header in required_headers:
        assert header in response.headers, f"Missing header: {header}"
        print(f"  {header}: {response.headers[header]}")


def test_docs_endpoint():
    """Test that /docs endpoint is exempt from rate limiting."""
    print("Testing /docs endpoint (should be exempt)...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200, "Docs endpoint should be accessible"


def main():
    """Run all tests."""
    print("=" * 60)
    print("FastAPI Rate Limiter Test Suite")
    print("=" * 60)
    print(f"\nTesting server at: {BASE_URL}")
    print("Make sure the FastAPI server is running!")
    print("\nPress Enter to continue...")
    input()
    
    try:
        # Test exempt endpoints first
        test_health_endpoint()
        test_docs_endpoint()
        
        # Test middleware rate limiting
        test_middleware_rate_limiting()
        
        # Test rate limit headers
        test_rate_limit_headers()
        
        # Test strict rate limiting
        test_strict_rate_limiting()
        
        # Test user-specific rate limiting
        test_user_specific_rate_limiting()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Could not connect to {BASE_URL}")
        print("Please make sure the FastAPI server is running:")
        print("  python examples/fastapi_example.py")
    except Exception as e:
        print(f"\nERROR: {e}")
        raise


if __name__ == "__main__":
    main()

