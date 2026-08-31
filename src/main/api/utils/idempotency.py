import json
import hashlib

from functools import wraps
from fastapi import Request
from src.main.database_src.redis import redis_client

# In a production environment, load this URL from your .env variables
#redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def idempotent_transaction(expire_seconds: int = 86400):
    """
    Prevents duplicate processing of the smae request within the specified timeframe.
    Caches the original response and retunrs it fi the exact same request is received again.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 1. Try to get an explicit idempotency-Key from headers
            idemp_key = request.headers.get("Idempotency-Key")

            # 2. Fallback: Hash the request body to create a unique signature 
            if not idemp_key:
                body = await request.body()
                idem_key = hashlib.sha256(body).hexdigest()

            redis_key = f"idempotency: {request.url.path}:{idemp_key}"

            # 3. Check if we already processed this exact transaction
            cached_response = await redis_client.get(redis_key)
            if cached_response:
                return json.loads(cached_response)

            # 4. If new, execute the actual endpoint logic
            response = await func(request, *args, **kwargs)

            # 5. Cache the successful response so future duplicates get this exact return value
            await redis_client.setex(
                name=redis_key,
                time=expire_seconds,
                value=json.dumps(response)
            )

            return response
        return wrapper
    return decorator