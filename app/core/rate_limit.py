"""
Rate limiting implementation for the application.
This module provides rate limiting functionality to protect against brute force attacks
and other forms of abuse.
"""

import logging
from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from typing import Callable, Optional
import time

from app.core.config import SETTINGS

# Setup logging
logger = logging.getLogger("app.core.rate_limit")

# Rate limit configurations
LOGIN_RATE_LIMIT = "5/minute"  # 5 login attempts per minute per IP
API_GENERAL_RATE_LIMIT = "60/minute"  # 60 API requests per minute per IP
SENSITIVE_ENDPOINTS_RATE_LIMIT = "10/minute"  # 10 requests per minute for sensitive endpoints

# IP ban threshold (number of rate limit violations before temporary ban)
IP_BAN_THRESHOLD = 10
IP_BAN_DURATION = 3600  # 1 hour in seconds

# Redis key prefixes
RATE_LIMIT_VIOLATIONS_PREFIX = "rate_limit_violations:"
IP_BAN_PREFIX = "ip_ban:"


async def setup_rate_limiting():
    """
    Initialize the rate limiter with Redis
    """
    try:
        redis_url = SETTINGS.redis_url or "redis://localhost:6379/0"
        redis_instance = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_instance)
        logger.info("Rate limiting initialized with Redis")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize rate limiting: {str(e)}")
        return False


def login_rate_limit():
    """
    Rate limiter for login endpoints
    """
    return RateLimiter(times=5, seconds=60, callback=login_rate_limit_callback)


def api_general_rate_limit():
    """
    General rate limiter for API endpoints
    """
    return RateLimiter(times=60, seconds=60)


def sensitive_endpoints_rate_limit():
    """
    Rate limiter for sensitive endpoints (password reset, etc.)
    """
    return RateLimiter(times=10, seconds=60)


async def login_rate_limit_callback(request: Request, response: Response, pexpire: int):
    """
    Callback for login rate limit violations
    Logs the violation and increments the violation counter for the IP
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Log the rate limit violation
    logger.warning(
        f"Rate limit exceeded for login endpoint. "
        f"IP: {client_ip}, "
        f"User-Agent: {user_agent}, "
        f"Reset in {pexpire/1000:.1f} seconds"
    )
    
    # Increment violation counter in Redis
    if hasattr(FastAPILimiter, "redis"):
        violation_key = f"{RATE_LIMIT_VIOLATIONS_PREFIX}{client_ip}"
        try:
            # Increment the counter and set expiry
            await FastAPILimiter.redis.incr(violation_key)
            await FastAPILimiter.redis.expire(violation_key, 86400)  # 24 hours
            
            # Check if we should ban this IP
            violations = int(await FastAPILimiter.redis.get(violation_key) or 0)
            if violations >= IP_BAN_THRESHOLD:
                ban_key = f"{IP_BAN_PREFIX}{client_ip}"
                await FastAPILimiter.redis.set(ban_key, time.time(), ex=IP_BAN_DURATION)
                logger.warning(f"IP {client_ip} has been temporarily banned due to excessive rate limit violations")
        except Exception as e:
            logger.error(f"Error tracking rate limit violations: {str(e)}")


async def check_ip_ban(request: Request) -> bool:
    """
    Check if an IP is banned
    Returns True if the IP is banned, False otherwise
    """
    # If rate limiting is disabled or not initialized, skip the check
    if not hasattr(FastAPILimiter, "redis") or FastAPILimiter.redis is None or not SETTINGS.rate_limiting_enabled:
        return False
        
    client_ip = request.client.host if request.client else "unknown"
    ban_key = f"{IP_BAN_PREFIX}{client_ip}"
    
    try:
        banned_until = await FastAPILimiter.redis.get(ban_key)
        if banned_until:
            # IP is banned
            logger.info(f"Blocked request from banned IP: {client_ip}")
            return True
    except Exception as e:
        logger.error(f"Error checking IP ban status: {str(e)}")
    
    return False


async def ip_ban_middleware(request: Request, call_next: Callable):
    """
    Middleware to check if an IP is banned before processing the request
    """
    is_banned = await check_ip_ban(request)
    if is_banned:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"detail": "Too many failed attempts. Please try again later."}
        )
    
    return await call_next(request)