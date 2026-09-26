import time
from uuid import uuid4
from app.config import settings
from app.redis_client import redis_client

LUA = r"""
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
    return {0, count}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window)
return {1, count + 1}
"""


async def allow_selection(user_id: int) -> tuple[bool, int]:
    now_ms = int(time.time() * 1000)
    window_ms = settings.rate_limit_window_seconds * 1000
    key = f"rate:user:{user_id}"
    allowed, count = await redis_client.eval(
        LUA,
        1,
        key,
        now_ms,
        window_ms,
        settings.rate_limit_requests,
        f"{now_ms}:{uuid4()}",
    )
    return bool(allowed), int(count)
