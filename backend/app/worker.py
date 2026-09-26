import asyncio
from uuid import uuid4
from redis.exceptions import ResponseError
from app.config import settings
from app.database import SessionLocal
from app.metrics import SELECTION_RESULTS
from app.redis_client import redis_client
from app.services.enrollment import select_course
from app.services.idempotency import release_selection_key
from app.services.queue import set_job_result

CONSUMER = f"worker-{uuid4().hex[:8]}"


async def ensure_group() -> None:
    try:
        await redis_client.xgroup_create(settings.queue_stream, settings.queue_group, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def process_message(message_id: str, fields: dict) -> None:
    job_id = fields["job_id"]
    user_id = int(fields["user_id"])
    course_id = int(fields["course_id"])
    try:
        await set_job_result(job_id, "processing", "Worker is processing request")
        async with SessionLocal() as db:
            status, message = await select_course(db, user_id, course_id)
        await set_job_result(job_id, status, message)
        SELECTION_RESULTS.labels(mode="queued_worker", result=status).inc()
    except Exception as exc:
        await set_job_result(job_id, "failed", f"Worker error: {type(exc).__name__}")
        SELECTION_RESULTS.labels(mode="queued_worker", result="failed").inc()
    finally:
        await release_selection_key(user_id, course_id, job_id)
        await redis_client.xack(settings.queue_stream, settings.queue_group, message_id)


async def main() -> None:
    await ensure_group()
    print(f"worker {CONSUMER} listening on stream={settings.queue_stream}")
    while True:
        rows = await redis_client.xreadgroup(
            groupname=settings.queue_group,
            consumername=CONSUMER,
            streams={settings.queue_stream: ">"},
            count=20,
            block=3000,
        )
        if not rows:
            continue
        for _stream, messages in rows:
            for message_id, fields in messages:
                await process_message(message_id, fields)


if __name__ == "__main__":
    asyncio.run(main())
