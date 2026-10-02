import redis

from src.main.config import settings

aioredis = getattr(redis, "asyncio", redis)

# Global async Redis client
# Some redis packages expose from_url at module level, others on the Redis class
try:
    from_url = getattr(aioredis, "from_url")
except AttributeError:
    from_url = getattr(aioredis, "Redis").from_url

redis_client = from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def get_redis():
    """
    Dependency provider for FastAPI endpoints if needed.
    """
    return redis_client