from fastapi import APIRouter, Depends
from app.dependencies import RequestIdentity, require_admin
from app.redis_client import redis_client
from app.schemas import DeviceInfo

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/{user_id}/devices", response_model=list[DeviceInfo])
async def user_devices(user_id: int, _: RequestIdentity = Depends(require_admin)):
    items = await redis_client.hgetall(f"devices:user:{user_id}")
    result: list[DeviceInfo] = []
    for device_id, last_seen in items.items():
        count = await redis_client.get(f"device:req:{user_id}:{device_id}") or 0
        result.append(
            DeviceInfo(device_id=device_id, last_seen=int(last_seen), request_count=int(count))
        )
    return sorted(result, key=lambda x: x.last_seen, reverse=True)
