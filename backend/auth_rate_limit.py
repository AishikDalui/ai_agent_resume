from collections import defaultdict, deque
from time import time

from runtime_store import with_redis


_local_hits: dict[str, deque[float]] = defaultdict(deque)


def _prune(queue: deque[float], window_seconds: int, now: float) -> None:
    cutoff = now - window_seconds
    while queue and queue[0] <= cutoff:
        queue.popleft()


def is_allowed(bucket: str, identifier: str, limit: int, window_seconds: int) -> bool:
    if limit <= 0:
        return True

    key = f"rate-limit:{bucket}:{identifier}"
    now = time()

    def redis_op(client) -> bool:
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zcard(key)
        _, current = pipe.execute()
        if int(current) >= limit:
            client.expire(key, window_seconds)
            return False
        pipe = client.pipeline()
        pipe.zadd(key, {f"{now}:{current}": now})
        pipe.expire(key, window_seconds)
        pipe.execute()
        return True

    redis_result = with_redis(redis_op)
    if isinstance(redis_result, bool):
        return redis_result

    queue = _local_hits[key]
    _prune(queue, window_seconds, now)
    if len(queue) >= limit:
        return False
    queue.append(now)
    return True
