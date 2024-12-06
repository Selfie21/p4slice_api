import sys
import uvicorn
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi import FastAPI
from fastapi.responses import FileResponse
from loguru import logger

from routers.auth import auth
from routers.slice import slice
from routers.admin import admin
from core.dependencies import get_config, get_client, get_slice_data_base


async def lifespan(_: FastAPI):
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG", diagnose=False)
    client = get_client()
    if not client:
        logger.error(f"Unable to connect via gRPC shutting down API")
        sys.exit(1)

    logger.debug(f"Configuring m_filter to drop packets with classification RED/3")
    client.add_mfilter_entry(3)
    max_slices = client.size_slice_ident()
    logger.info(f"Identified MAX_SLICES as {max_slices}")
    logger.info(f"MAX_BANDWIDTH_PER_USER is {config.bandwidth_per_user_kbit / 1000} Mbit/s")
    slice_database = get_slice_data_base()
    slice_database += [None for _ in range(max_slices)]

    logger.info(f"Connecting to redis on {config.redis_url}:6379")
    redis_connection = redis.Redis(
        host=config.redis_url,
        port=6379,
        password=config.redis_password.get_secret_value(),
        encoding="utf8",
    )
    await FastAPILimiter.init(redis=redis_connection)
    logger.info("Startup Complete!")
    yield
    await FastAPILimiter.close()


config = get_config()
app = FastAPI(lifespan=lifespan)
app.include_router(auth)
app.include_router(slice)
app.include_router(admin)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to P4Slice your framework for creating slice instances!"
    }

favicon_path = './favicon.ico'

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


if __name__ == "__main__":
    # TODO: for production set reload to false
    uvicorn.run(
        "main:app",
        host=config.server_url,
        port=config.server_port,
        log_level="info",
        workers=4,
        reload=True,
    )
