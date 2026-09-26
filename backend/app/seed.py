from sqlalchemy import select
from app.auth import hash_password
from app.database import SessionLocal
from app.models import Course, User


async def seed_data() -> None:
    async with SessionLocal() as db:
        has_user = await db.scalar(select(User.id).limit(1))
        if not has_user:
            db.add_all(
                [
                    User(username="student1", password_hash=hash_password("demo123"), role="student"),
                    User(username="student2", password_hash=hash_password("demo123"), role="student"),
                    User(username="student3", password_hash=hash_password("demo123"), role="student"),
                    User(username="admin", password_hash=hash_password("admin123"), role="admin"),
                ]
            )

        has_course = await db.scalar(select(Course.id).limit(1))
        if not has_course:
            db.add_all(
                [
                    Course(code="CS101", name="Python 程序设计", capacity=30, remaining=30),
                    Course(code="CS201", name="数据结构", capacity=20, remaining=20),
                    Course(code="CS301", name="计算机网络", capacity=15, remaining=15),
                    Course(code="AI401", name="人工智能导论", capacity=10, remaining=10),
                ]
            )
        await db.commit()
