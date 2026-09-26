from app.config import settings
from app.redis_client import redis_client


async def acquire_selection_key(user_id: int, course_id: int, value: str) -> bool:
    key = f"idem:select:{user_id}:{course_id}"
    ok = await redis_client.set(key, value, ex=settings.idempotency_ttl_seconds, nx=True)
    return bool(ok)


async def release_selection_key(user_id: int, course_id: int, value: str) -> None:
    key = f"idem:select:{user_id}:{course_id}"
    current = await redis_client.get(key)
    if current == value:
        await redis_client.delete(key)
