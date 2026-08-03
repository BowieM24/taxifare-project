import logging
from src.main.database_src.redis import redis_client

logger = logging.getLogger(__name__)

async def is_rate_limited(commuter_id: str, limit: int=5, window_seconds: int=60) -> bool:
    """
    Atomic fixed-window rate limiter using Redis INCR and EXPIRE.
    Allows up to 'limit' payment requests per 'window_seconds'.
    """
    key = f"rate_limit:commuter:{commuter_id}"

    # Increment counter atomically
    current_requests = await redis_client.incr(key)


    # If it is the first request in the window, set expiration time
    if current_requests == 1:
        await redis_client.expire(key, window_seconds)

    return current_requests > limit


async def is_transaction_processed(transaction_id: str, ttl_seconds: int = 86400) -> bool:
    """
    Idempotency check: Returns True if transaction was already processed.
    if new, marks it as processed with a 24-hour TTL (86400s).
    """
    key = f"idempotency:tx:{transaction_id}"

    # SETNX (Set if Not Exists): Returns True if key was set, False if key already existed
    is_new = await redis_client.set(key, "PROCESSED", nx=True, ex=ttl_seconds)

    # If is_new is None/False, it means the key already exists (duplicate)
    return not is_new
