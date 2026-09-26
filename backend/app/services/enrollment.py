from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Course, Enrollment


async def select_course(db: AsyncSession, user_id: int, course_id: int) -> tuple[str, str]:
    existing = await db.scalar(
        select(Enrollment.id).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
    )
    if existing:
        return "already_enrolled", "You already selected this course"

    try:
        async with db.begin_nested():
            result = await db.execute(
                update(Course)
                .where(Course.id == course_id, Course.remaining > 0)
                .values(remaining=Course.remaining - 1)
            )
            if result.rowcount != 1:
                course_exists = await db.scalar(select(Course.id).where(Course.id == course_id))
                if not course_exists:
                    return "rejected", "Course not found"
                return "full", "Course is full"

            await db.execute(insert(Enrollment).values(user_id=user_id, course_id=course_id))
        await db.commit()
        return "selected", "Course selected successfully"
    except IntegrityError:
        await db.rollback()
        return "already_enrolled", "You already selected this course"
    except Exception:
        await db.rollback()
        raise
