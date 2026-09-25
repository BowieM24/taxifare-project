from fastapi import Request, HTTPException, status  # type: ignore[import]
import logging
from src.main.database_src.redis import redis_client

logger = logging.getLogger(__name__)

async def rate_limit_dependency(request: Request):
    """
    FastAPI Dependency that rate-limits based on the client's IP address.
    Limits to 60 requests per minute per IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:ip:{client_ip}"
    
    current_requests = await redis_client.incr(key)
    if current_requests == 1:
        await redis_client.expire(key, 60)  # 60-second window
        
    if current_requests > 60:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down."
        )

    return current_requests


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
