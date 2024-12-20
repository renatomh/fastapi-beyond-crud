"""Redis client for the application."""

import redis.asyncio as aioredis

from src.config import Config

JTI_EXPIRY = 3600  # 1 hour

# Defining the blocked token list
token_blocklist = aioredis.from_url(Config.redis_url)


async def add_jti_to_blocklist(jti: str) -> None:
    """Adds a JTI to the Redis blocklist."""
    await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY)


async def token_in_blocklist(jti: str) -> bool:
    """Checks if JTI is present in Redis blocklist."""
    redis_jti = await token_blocklist.get(jti)

    return redis_jti is not None
