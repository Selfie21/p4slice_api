from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from dependencies import get_config

config = get_config()
admin = APIRouter(dependencies=[Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1))])

@admin.get("/monitor")
def monitor():
    return {"message": "test"}
