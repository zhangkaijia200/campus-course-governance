import time
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import decode_access_token
from app.database import get_db
from app.models import User
from app.redis_client import redis_client

bearer = HTTPBearer(auto_error=True)


@dataclass
class RequestIdentity:
    user: User
    claims: dict
    device_id: str


async def get_identity(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    x_device_id: str = Header(default="unknown-device"),
    db: AsyncSession = Depends(get_db),
) -> RequestIdentity:
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    now = int(time.time())
    key = f"devices:user:{user.id}"
    count_key = f"device:req:{user.id}:{x_device_id}"
    pipe = redis_client.pipeline()
    pipe.hset(key, x_device_id, now)
    pipe.expire(key, 3600)
    pipe.incr(count_key)
    pipe.expire(count_key, 3600)
    await pipe.execute()

    return RequestIdentity(user=user, claims=claims, device_id=x_device_id)


async def require_admin(identity: RequestIdentity = Depends(get_identity)) -> RequestIdentity:
    if identity.user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return identity
