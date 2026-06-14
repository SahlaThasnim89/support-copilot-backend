import hashlib
import json
import logging
from upstash_redis import Redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CACHE_TTL_SECONDS = 3600 * 24  # 24 hours

redis = Redis(
    url=settings.upstash_redis_rest_url,
    token=settings.upstash_redis_rest_token,
)


def _hash_query(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()


def get_cached(query: str) -> dict | None:
    key = _hash_query(query)
    try:
        data = redis.get(key)
        if not data:
            logger.info(f"[Cache] MISS: '{query[:50]}'")
            return None
        redis.expire(key, CACHE_TTL_SECONDS)
        logger.info(f"[Cache] HIT: '{query[:50]}'")
        return json.loads(data)
    except Exception as e:
        logger.error(f"[Cache] Get failed: {e}")
        return None


def set_cache(query: str, data: dict) -> None:
    key = _hash_query(query)
    try:
        redis.setex(key, CACHE_TTL_SECONDS, json.dumps(data))
        logger.info(f"[Cache] STORED: '{query[:50]}'")
    except Exception as e:
        logger.error(f"[Cache] Set failed: {e}")


def get_cache_stats() -> dict:
    try:
        keys = redis.keys("*")
        return {
            "cached_queries": len(keys),
            "keys": keys,
        }
    except Exception as e:
        logger.error(f"[Cache] Stats failed: {e}")
        return {"cached_queries": 0, "keys": []}