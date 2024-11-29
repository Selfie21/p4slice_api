from fastapi import APIRouter, Depends, HTTPException, status
#from fastapi_limiter.depends import RateLimiter
from pydantic import UUID4

from models import BaseSlice
from dependencies import get_config
from internal.controller import Client

config = get_config()
#slice = APIRouter(prefix="/slice", dependencies=[Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1))])
slice = APIRouter()

@slice.post("/add")
def add_slice(slice: BaseSlice):
    return slice

@slice.post("/del")
def delete_slice(slice_id: UUID4):
    return slice_id

@slice.get("/monitor")
def monitor():
    return {"message": "test"}