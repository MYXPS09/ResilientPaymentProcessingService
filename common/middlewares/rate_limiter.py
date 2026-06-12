import time
from collections import defaultdict, deque
from fastapi import Request
from common.exceptions.base import RateLimitException
from common.config import settings

# In-memory rate limiter using sliding window
# Upgrade path: Use Redis sorted sets for a distributed rate limiter.
# ZADD to add timestamps, ZREMRANGEBYSCORE to remove old, ZCARD to count.
_rate_limits = defaultdict(deque)

async def rate_limit_check(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean up old entries
    while _rate_limits[client_ip] and _rate_limits[client_ip][0] < current_time - settings.RATE_LIMIT_WINDOW:
        _rate_limits[client_ip].popleft()
        
    if len(_rate_limits[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
        raise RateLimitException("Rate limit exceeded. Please try again later.")
        
    _rate_limits[client_ip].append(current_time)
