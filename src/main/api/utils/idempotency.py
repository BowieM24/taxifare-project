import json

from functools import wraps
from fastapi import Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis

# In a production environment, load this URL from your .env variables
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def idempotent_transaction(expire_seconds: int = 86400):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            idemp_key = request.headers.get("Idempotency-Key")

            if not idemp_key:
                return await func(request, *args, **kwargs)

            redis_key = f"idemp_tx:{idemp_key}"

            cached_response = await redis_client.get(redis_key)
            if cached_response:
                data = json.loads(cached_response)
                return JSONResponse(status_code=data["status_code"], content=data["body"])

            response = await func(request, *args, **kwargs)

            if isinstance(response, dict):
                cache_data = json.dumpd({
                    "status_code": 200,
                    "body": reponse
                })
                await redis_client.set(redis_key, cache_data, ex=expire_seconds)

            return response

        return wrapper
    return decorator