import sys
import uvicorn
from loguru import logger
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi import FastAPI

from routers.auth import auth
from routers.slice import slice
from dependencies import get_config, get_client, get_slice_data_base

async def lifespan(_: FastAPI):
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG", diagnose=False)
    client = get_client()
    if not client:
        logger.error(f"Unable to connect via gRPC shutting down API")
        sys.exit(1)
    
    max_slices = client.size_slice_ident()
    logger.info(f"Identified MAX_SLICES as {max_slices}")
    slice_database = get_slice_data_base()
    slice_database += [None for _ in range(max_slices)]

    logger.info("Configuring Rate Limiter")
    redis_connection = redis.Redis(host=config.redis_url, port=6379, password=config.redis_password.get_secret_value(), encoding="utf8")
    await FastAPILimiter.init(redis=redis_connection)
    logger.info("Startup Complete!")
    yield
    await FastAPILimiter.close()

config = get_config()
app = FastAPI(lifespan=lifespan)
app.include_router(auth)
app.include_router(slice)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to P4Slice your framework for creating slice instances!"
    }

if __name__ == "__main__":
    # TODO: for production set reload to false
    uvicorn.run('main:app', host=config.server_url, port=config.server_port, log_level='info', workers=4, reload=True)
