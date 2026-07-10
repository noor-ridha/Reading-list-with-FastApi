import redis

from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def list_cache_key(owner_id, list_id) -> str:
    return f"list:{owner_id}:{list_id}"