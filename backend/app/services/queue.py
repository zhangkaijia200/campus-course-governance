import json
from uuid import uuid4
from app.config import settings
from app.redis_client import redis_client


async def enqueue_selection(user_id: int, course_id: int, device_id: str, job_id: str | None = None) -> str:
    job_id = job_id or str(uuid4())
    job_key = f"job:{job_id}"
    payload = {
        "job_id": job_id,
        "user_id": str(user_id),
        "course_id": str(course_id),
        "device_id": device_id,
    }
    await redis_client.hset(
        job_key,
        mapping={
            "status": "queued",
            "message": "Waiting for worker",
            "course_id": str(course_id),
            "user_id": str(user_id),
        },
    )
    await redis_client.expire(job_key, 3600)
    await redis_client.xadd(settings.queue_stream, payload)
    return job_id


async def get_job(job_id: str) -> dict | None:
    data = await redis_client.hgetall(f"job:{job_id}")
    if not data:
        return None
    return {
        "job_id": job_id,
        "status": data.get("status", "unknown"),
        "message": data.get("message"),
        "course_id": int(data["course_id"]) if data.get("course_id") else None,
        "user_id": int(data["user_id"]) if data.get("user_id") else None,
    }


async def set_job_result(job_id: str, status: str, message: str) -> None:
    key = f"job:{job_id}"
    await redis_client.hset(key, mapping={"status": status, "message": message})
    await redis_client.expire(key, 3600)
