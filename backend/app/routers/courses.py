from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import RequestIdentity, get_identity
from app.metrics import SELECTION_RESULTS
from app.models import Course, Enrollment
from app.schemas import CourseOut, EnrollmentOut, JobStatus, SelectionResponse
from app.services.enrollment import select_course
from app.services.idempotency import acquire_selection_key, release_selection_key
from app.services.queue import enqueue_selection, get_job
from app.services.rate_limit import allow_selection

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseOut])
async def list_courses(
    _: RequestIdentity = Depends(get_identity),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.scalars(select(Course).order_by(Course.id))
    return list(rows)


@router.post("/courses/{course_id}/select", response_model=SelectionResponse)
async def choose_course(
    course_id: int,
    mode: str = Query(default="queued", pattern="^(queued|direct)$"),
    identity: RequestIdentity = Depends(get_identity),
    db: AsyncSession = Depends(get_db),
):
    allowed, _count = await allow_selection(identity.user.id)
    if not allowed:
        SELECTION_RESULTS.labels(mode=mode, result="rate_limited").inc()
        raise HTTPException(status_code=429, detail="Account-level rate limit exceeded")

    request_id = str(uuid4())
    acquired = await acquire_selection_key(identity.user.id, course_id, request_id)
    if not acquired:
        SELECTION_RESULTS.labels(mode=mode, result="duplicate").inc()
        return SelectionResponse(status="rejected", message="Duplicate request suppressed")

    if mode == "queued":
        job_id = await enqueue_selection(identity.user.id, course_id, identity.device_id, request_id)
        SELECTION_RESULTS.labels(mode=mode, result="queued").inc()
        return SelectionResponse(status="queued", message="Request queued", job_id=job_id)

    try:
        status, message = await select_course(db, identity.user.id, course_id)
        SELECTION_RESULTS.labels(mode=mode, result=status).inc()
        return SelectionResponse(status=status, message=message)
    finally:
        await release_selection_key(identity.user.id, course_id, request_id)


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str, identity: RequestIdentity = Depends(get_identity)):
    job = await get_job(job_id)
    if not job or job.get("user_id") != identity.user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    job.pop("user_id", None)
    return JobStatus(**job)


@router.get("/enrollments/me", response_model=list[EnrollmentOut])
async def my_enrollments(
    identity: RequestIdentity = Depends(get_identity),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.user_id == identity.user.id)
        .order_by(Enrollment.created_at.desc())
    )
    return [
        EnrollmentOut(
            id=e.id,
            course_id=c.id,
            course_code=c.code,
            course_name=c.name,
            created_at=e.created_at,
        )
        for e, c in rows.all()
    ]
