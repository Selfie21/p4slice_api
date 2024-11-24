import uvicorn
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi import FastAPI

from routers.auth import auth
from routers.slice import slice
from dependencies import get_config

async def lifespan(_: FastAPI):
    redis_connection = redis.Redis(host=config.redis_url, port=6379, password=config.redis_password.get_secret_value(), encoding="utf8")
    await FastAPILimiter.init(redis=redis_connection)
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
