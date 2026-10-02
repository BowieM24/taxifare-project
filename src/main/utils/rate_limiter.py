from slowapi import Limiter
from slowapi.util import get_remote_address

# Configure limiter to use the client's IP address and Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1",    # Dedicated DB index for rate limiting
    default_limits=["100/minute"]              # Global fallback limit
) 