from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from pydantic import UUID4
from typing import Annotated, List
from loguru import logger

from core.models import BaseSlice, User
from core.dependencies import get_config, get_client, get_slice_data_base, get_user_data_base
from internal.util import get_from_database, insert_into_database, delete_from_database, used_bandwidth
from internal.authlib import get_current_active_user

config = get_config()
slice = APIRouter(
    prefix="/slice",
    dependencies=[Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1))],
)
BURST_SIZE = 2


@slice.post("/add")
def add_slice(
    current_user: Annotated[User, Depends(get_current_active_user)],
    slice: BaseSlice,
    slice_database: dict = Depends(get_slice_data_base),
):
    
    total_bandwidth = used_bandwidth(current_user.slices, slice_database)
    if (total_bandwidth + slice.max_bandwidth) > config.bandwidth_per_user_kbit:
        raise HTTPException(
            status_code=417,
            detail=f"Could not add slice! User exceeded maximum bandwidth per user (current usage {total_bandwidth/1000} mbit/s and maximum is {config.bandwidth_per_user_kbit/1000} mbit/s)",
        )
    
    client = get_client()
    meter = client.get_table("Ingress.meter")
    slice_index = insert_into_database(slice_database, slice)
    if slice_index is None:
        raise HTTPException(
            status_code=400,
            detail="Could not add slice id, likely slice database is full!",
        )

    logger.debug(f"Inserted into the database with index {slice_index}")
    meter_insert_state = client.program_meter(
        meter=meter,
        meter_index=slice_index,
        meter_type="bytes",
        cir=slice.guaranteed_bandwidth,
        pir=slice.max_bandwidth,
        cbs=BURST_SIZE,
        pbs=BURST_SIZE,
    )
    slice_insert_state = client.add_slice_entry(slice_index, **slice.flow_identification[0].model_dump())

    if meter_insert_state and slice_insert_state:
        current_user.slices.append(slice.id)
        logger.debug(f"Programmed meter and slice ident table with {slice_index}")
        return {"message": f"Creating slice with id {slice.id} successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add slice, configuring control plane tables failed!")


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
        slice_delete_status = client.delete_slice_entry(**slice_info.flow_identification[0].model_dump())
        if slice_delete_status:
            return {"message": f"Deletion of slice {slice_id} successful!"}
        else:
            raise HTTPException(status_code=400, detail=f"Error while deleting {slice_id}, error configuring control plane tables!")  
    else:
        raise HTTPException(status_code=404, detail=f"Error while deleting {slice_id}, likely slice id is not found!")


@slice.get("/info", response_model=List[BaseSlice])
def info_slice(current_user: Annotated[User, Depends(get_current_active_user)], slice_database: dict = Depends(get_slice_data_base)):
    tmp = []
    for slice_id in current_user.slices:
        tmp.append(get_from_database(slice_id, slice_database))
    return tmp


# TODO: only used for debug remove in prod
@slice.get("/database")
def info_slice(current_user: Annotated[User, Depends(get_current_active_user)], slice_database: dict = Depends(get_slice_data_base)):
    return slice_database
