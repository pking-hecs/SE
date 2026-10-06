"""
cache.py — Redis caching layer for FinReq AI Platform.
Caches project states, RAG retrieval outputs, and rate limiting counters.
Falls back gracefully if Redis is unavailable.
"""
import os
import json
import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger("FinReqCache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client = None
_redis_available = False

try:
    import redis
    _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2.0)
    _redis_client.ping()
    _redis_available = True
    logger.info("Connected to Redis cache at %s", REDIS_URL)
except Exception as e:
    logger.warning("Redis not available: %s. Using in-memory fallback.", e)
    _redis_available = False

_in_memory_cache: Dict[str, Any] = {}


def is_redis_active() -> bool:
    """Check if Redis connection is active and healthy."""
    global _redis_available
    if not _redis_client:
        return False
    try:
        _redis_client.ping()
        _redis_available = True
        return True
    except Exception:
        _redis_available = False
        return False


def set_cached_state(project_id: str, state_dict: dict, ttl: int = 3600) -> bool:
    """Store serialized project state in Redis (default 1 hr TTL)."""
    key = f"finreq:state:{project_id}"
    data = json.dumps(state_dict)
    if _redis_available and _redis_client:
        try:
            _redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error("Redis set error: %s", e)
    _in_memory_cache[key] = data
    return True


def get_cached_state(project_id: str) -> Optional[dict]:
    """Retrieve serialized project state from Redis or memory."""
    key = f"finreq:state:{project_id}"
    if _redis_available and _redis_client:
        try:
            data = _redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error("Redis get error: %s", e)
    data = _in_memory_cache.get(key)
    if data:
        try:
            return json.loads(data)
        except Exception:
            return None
    return None


def invalidate_cached_state(project_id: str) -> None:
    """Evict cached state upon major modifications."""
    key = f"finreq:state:{project_id}"
    if _redis_available and _redis_client:
        try:
            _redis_client.delete(key)
        except Exception:
            pass
    _in_memory_cache.pop(key, None)


def cache_rag_result(query_hash: str, results: List[dict], ttl: int = 900) -> None:
    """Cache RAG retrieval matches for identical queries."""
    key = f"finreq:rag:{query_hash}"
    if _redis_available and _redis_client:
        try:
            _redis_client.setex(key, ttl, json.dumps(results))
        except Exception:
            pass


def get_cached_rag_result(query_hash: str) -> Optional[List[dict]]:
    """Retrieve cached RAG result."""
    key = f"finreq:rag:{query_hash}"
    if _redis_available and _redis_client:
        try:
            val = _redis_client.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass
    return None


def check_rate_limit(identifier: str, limit: int = 60, window_secs: int = 60) -> bool:
    """
    Token bucket / sliding window rate limiter.
    Returns True if request is allowed, False if exceeded.
    """
    key = f"finreq:ratelimit:{identifier}"
    if _redis_available and _redis_client:
        try:
            current = _redis_client.incr(key)
            if current == 1:
                _redis_client.expire(key, window_secs)
            return current <= limit
        except Exception:
            return True
    return True


def get_cache_stats() -> dict:
    """Return status and key metrics for admin monitoring."""
    active = is_redis_active()
    info = {
        "status": "connected" if active else "in_memory_fallback",
        "redis_host": REDIS_URL,
        "keys_count": 0,
        "memory_used": "0KB"
    }
    if active and _redis_client:
        try:
            info_dict = _redis_client.info()
            info["keys_count"] = _redis_client.dbsize()
            info["memory_used"] = info_dict.get("used_memory_human", "N/A")
            info["uptime_days"] = info_dict.get("uptime_in_days", 0)
        except Exception:
            pass
    else:
        info["keys_count"] = len(_in_memory_cache)
    return info
