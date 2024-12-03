from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from pydantic import UUID4
from typing import Annotated, List
from loguru import logger

from models import BaseSlice, User
from dependencies import get_config, get_client, get_slice_data_base, get_user_data_base
from internal.util import get_from_database, insert_into_database, delete_from_database
from internal.authlib import get_current_active_user

config = get_config()
slice = APIRouter(
    prefix="/slice",
    dependencies=[Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1))],
)
BURST_SIZE = 2000


@slice.post("/add")
def add_slice(
    current_user: Annotated[User, Depends(get_current_active_user)],
    slice: BaseSlice,
    slice_database: dict = Depends(get_slice_data_base),
):
    client = get_client()
    meter = client.get_table("Ingress.meter")
    slice_index = insert_into_database(slice_database, slice)
    if slice_index is None:
        raise HTTPException(
            status_code=400,
            detail="Could not add slice id, likely slice database is full!",
        )

    logger.debug(f"Inserted into the database with index {slice_index}")
    client.program_meter(
        meter=meter,
        meter_index=slice_index,
        meter_type="bytes",
        cir=slice.guaranteed_bandwidth,
        pir=slice.max_bandwidth,
        cbs=BURST_SIZE,
        pbs=BURST_SIZE,
    )
    client.add_slice_entry(slice_index, **slice.flow_identification[0].model_dump())
    logger.debug(f"Programmed meter and slice ident table with {slice_index}")
    current_user.slices.append(slice.id)
    return {"message": f"Creating slice with id {slice.id} successful!"}


@slice.delete("/del")
def delete_slice(
    slice_id: UUID4,
    current_user: Annotated[User, Depends(get_current_active_user)],
    slice_database: dict = Depends(get_slice_data_base),
    user_database: dict = Depends(get_user_data_base),
):
    client = get_client()
    if not slice_id in current_user.slices:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized for this action!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    slice_info = get_from_database(slice_id, slice_database)
    if slice_info:
        delete_from_database(slice_id, slice_database)
        user_database[current_user.username].slices.remove(slice_id)
        client.delete_slice_entry(**slice_info.flow_identification[0].model_dump())
        return {"message": f"Deletion of slice {slice_id} successful!"}
    else:
        return {
            "message": f"Error while deleting {slice_id}, likely slice id is not found!"
        }


@slice.get("/info", response_model=List[BaseSlice])
def info_slice(
    current_user: Annotated[User, Depends(get_current_active_user)],
    slice_database: dict = Depends(get_slice_data_base),
):
    tmp = []
    for slice_id in current_user.slices:
        tmp.append(get_from_database(slice_id, slice_database))
    return tmp


# TODO: only used for debug remove in prod
@slice.get("/database")
def info_slice(
    current_user: Annotated[User, Depends(get_current_active_user)],
    slice_database: dict = Depends(get_slice_data_base),
):
    return slice_database
