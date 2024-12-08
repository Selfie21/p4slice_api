from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from typing import List, Dict, Annotated
from pydantic import Field

from internal.authlib import current_user_is_admin
from core.dependencies import get_config, get_client, get_base_model
from core.models import FirewallEntry, VlanEntry

config = get_config()
admin = APIRouter(
    prefix="/admin",
    dependencies=[
        Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1)),
        Depends(current_user_is_admin),
    ],
)


@admin.get("/monitor", response_model=Dict)
def monitor(base_model = Depends(get_base_model)):
    client = get_client()
    probe = client.loop_digest(base_model)
    if not probe:
        return {"message": "No digests consumed!"}
    return probe


@admin.get("/table_info", response_model=List)
def table_info():
    client = get_client()
    return client.get_base_info()

@admin.get("/port_info", response_model=List)
def table_info():
    client = get_client()
    return client.get_port_info()

@admin.post("/firewall")
def add_firewall(entry: FirewallEntry):
    client = get_client()
    client.add_firewall_entry(entry.src_addr, entry.prefix_len)

@admin.post("/vlan_route")
def add_vlan(entry: VlanEntry):
    client = get_client()
    vlan_insert_state = client.add_vlan_entry(**entry.model_dump())
    if vlan_insert_state:
        return {"message": f"Creating VLAN entry with VLAN ID {entry.vlan_id} to PORT {entry.port} successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add vlan entry, configuring control plane tables failed!")

@admin.post("/egress_route")
def add_egress(port: Annotated[int, Field(ge=0, le=400)]):
    client = get_client()
    ip_insert_state = client.add_egress_entry(port)
    if ip_insert_state:
        return {"message": f"Setting PORT {port} as egress successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add egress entry, configuring control plane tables failed!")
    