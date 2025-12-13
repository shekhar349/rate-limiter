"""
Example demonstrating core RateLimiter usage without frameworks.
"""

import time
from python_rate_limiter import RateLimiter, RateLimitExceeded

# Create a rate limiter: 5 requests per 10 seconds
limiter = RateLimiter(max_requests=5, time_window=10.0)

# Simulate requests from different users
user1 = "192.168.1.1"
user2 = "192.168.1.2"

print("=== Example 1: Basic Usage ===\n")

# User 1 makes requests
for i in range(7):
    is_allowed, retry_after = limiter.is_allowed(user1)
    if is_allowed:
        print(f"Request {i+1} from {user1}: ALLOWED")
    else:
        print(f"Request {i+1} from {user1}: BLOCKED (retry after {retry_after:.2f}s)")

print(f"\nRemaining requests for {user1}: {limiter.get_remaining(user1)}")
print(f"Reset time for {user1}: {time.ctime(limiter.get_reset_time(user1))}")

print("\n=== Example 2: Exception Handling ===\n")

# User 2 makes requests
for i in range(7):
    try:
        limiter.check_rate_limit(user2)
        print(f"Request {i+1} from {user2}: ALLOWED")
    except RateLimitExceeded as e:
        print(f"Request {i+1} from {user2}: BLOCKED (retry after {e.retry_after:.2f}s)")

print("\n=== Example 3: Reset ===\n")

print(f"Remaining requests for {user1} before reset: {limiter.get_remaining(user1)}")
limiter.reset(user1)
print(f"Remaining requests for {user1} after reset: {limiter.get_remaining(user1)}")

print("\n=== Example 4: Multiple Users ===\n")

users = ["user1", "user2", "user3"]
for user in users:
    is_allowed, _ = limiter.is_allowed(user)
    remaining = limiter.get_remaining(user)
    print(f"{user}: {'ALLOWED' if is_allowed else 'BLOCKED'}, Remaining: {remaining}")

