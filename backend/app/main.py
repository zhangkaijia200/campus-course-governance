import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from app.config import settings
from app.database import Base, engine
from app.metrics import HTTP_DURATION, HTTP_REQUESTS
from app.redis_client import redis_client
from app.routers import admin, auth, courses
from app.seed import seed_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()
    try:
        yield
    finally:
        await redis_client.aclose()
        await engine.dispose()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    HTTP_REQUESTS.labels(request.method, path, response.status_code).inc()
    HTTP_DURATION.labels(request.method, path).observe(time.perf_counter() - started)
    return response


@app.get("/health", tags=["system"])
async def health():
    pong = await redis_client.ping()
    return {"status": "ok", "redis": bool(pong)}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(admin.router)
