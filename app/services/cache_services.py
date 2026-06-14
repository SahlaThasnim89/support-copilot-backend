import hashlib
import time
import logging

logger = logging.getLogger(__name__)

_cache: dict = {}
CACHE_TTL_SECONDS = 3600 * 24  # 24 hour


def _hash_query(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()


def get_cached(query: str) -> dict | None:
    key = _hash_query(query)
    try:
        entry = _cache.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del _cache[key]
            logger.info(f"[Cache] Expired: '{query[:50]}'")
            return None
        entry["expires_at"] = time.time() + CACHE_TTL_SECONDS  #sliding TTL
        logger.info(f"[Cache] HIT: '{query[:50]}'")
        return entry["data"]
    except Exception as e:
        logger.error(f"[Cache] Get failed: {e}")
        return None


def set_cache(query: str, data: dict) -> None:
    key = _hash_query(query)
    try:
        _cache[key] = {
            "data": data,
            "expires_at": time.time() + CACHE_TTL_SECONDS,
        }
        logger.info(f"[Cache] STORED: '{query[:50]}'")
    except Exception as e:
        logger.error(f"[Cache] Set failed: {e}")


def get_cache_stats() -> dict:
    return {
        "cached_queries": len(_cache),
        "keys": list(_cache.keys()),
    }



# import redis
# import json

# r=redis.from_url("your-redis-url")

# def get_cached(query:str)->dict|None:
#     key=_hash_query(query)
#     data=r.get(key)
#     return json.loads(data) if data else None


# def set_cache(query:str,data:dict)->None:
#     key=_hash_query(query)
#     r.setex(key,CACHE_TTL_SECONDS, json.dumps(data))