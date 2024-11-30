from fastapi import APIRouter, Depends, HTTPException, status

from fastapi_limiter.depends import RateLimiter
from pydantic import UUID4

from models import BaseSlice
from dependencies import get_config, get_client, get_slice_data_base
from internal.controller import Client
from internal.util import insert_into_database

config = get_config()
slice = APIRouter(prefix="/slice", dependencies=[Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1))])
slice = APIRouter()
BURST_SIZE = 2000


@slice.post("/add")
def add_slice(slice: BaseSlice, slice_database: dict = Depends(get_slice_data_base)):
    client = get_client()
    meter = client.get_table("Ingress.meter")

    slice_id = insert_into_database(slice_database, slice)
    client.program_meter(
        meter=meter,
        meter_index=slice_id,
        meter_type="bytes",
        cir=slice.guaranteed_bandwidth,
        pir=slice.max_bandwidth,
        cbs=BURST_SIZE,
        pbs=BURST_SIZE,
    )
    client.add_slice(slice_id, **slice.flow_identification[0].model_dump())
    return slice


@slice.post("/del")
def delete_slice(slice_id: UUID4):
    return slice_id


@slice.get("/monitor")
def monitor():
    return {"message": "test"}
