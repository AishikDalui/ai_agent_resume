import logging
from collections.abc import Callable
from functools import lru_cache

from redis import Redis
from redis.exceptions import RedisError

from config import get_settings


logger = logging.getLogger(__name__)


@lru_cache
def get_redis_client() -> Redis | None:
    settings = get_settings()
    redis_url = settings.celery_broker_url or settings.celery_result_backend
    if not redis_url:
        return None
    try:
        client = Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except RedisError:
        logger.warning("Redis is unavailable. Falling back to in-memory runtime state.")
        return None


def with_redis(operation: Callable[[Redis], object]) -> object | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        return operation(client)
    except RedisError:
        logger.warning("Redis operation failed. Falling back to in-memory runtime state.")
        return None
