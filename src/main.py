import uvicorn as uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from starlette.responses import JSONResponse
from http import HTTPStatus
from redis.asyncio import ConnectionPool, Redis

from booking_api.api import router as booking_router
from booking_api.utils.exceptions import NotFoundException, UniqueConflictException, \
    ForbiddenException
from config.base import settings
from config.logger import LOGGING
from db.utils import redis

app = FastAPI(
    title=settings.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.on_event("startup")
async def startup():
    pool = ConnectionPool.from_url(settings.redis.url, max_connections=20)
    redis.redis = Redis(connection_pool=pool)


@app.on_event("shutdown")
async def shutdown():
    await redis.redis.close()


@app.exception_handler(NotFoundException)
async def _exception(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND,
        content={"message": exc.message, "detail": exc.extras},
    )


@app.exception_handler(UniqueConflictException)
async def _exception(request: Request, exc: UniqueConflictException):
    return JSONResponse(
        status_code=HTTPStatus.CONFLICT,
        content={
            "message": exc.message,
            "detail": exc.extras,
        },
    )


@app.exception_handler(ForbiddenException)
async def _exception(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=HTTPStatus.FORBIDDEN,
        content={
            "message": exc.message,
            "detail": exc.extras,
        },
    )


app.include_router(booking_router.router, prefix="/booking_api")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=LOGGING,
        log_level="info",
    )
