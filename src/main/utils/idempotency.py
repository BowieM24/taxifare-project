import json
import hashlib
from functools import wraps
from fastapi import Request
from src.main.database_src.redis import redis_client

def idempotent_transaction(expire_seconds: int = 86400):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            idem_key = request.headers.get("Idempotency-Key")
            
            if not idem_key:
                body = await request.body()
                idem_key = hashlib.sha256(body).hexdigest()

            redis_key = f"idempotency:{request.url.path}:{idem_key}"

            cached_response = await redis_client.get(redis_key)
            if cached_response:
                return json.loads(cached_response)

            response = await func(request, *args, **kwargs)

            await redis_client.setex(
                name=redis_key,
                time=expire_seconds,
                value=json.dumps(response)
            )
            return response
        return wrapper
    return decorator
