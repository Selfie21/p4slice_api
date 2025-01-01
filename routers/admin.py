from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from typing import Annotated
from pydantic import Field

from internal.authlib import current_user_is_admin
from core.dependencies import get_config, get_client, get_base_model
from core.models import FirewallEntry, VlanEntry, IpEntry, ArpEntry

config = get_config()
admin = APIRouter(
    prefix="/admin",
    dependencies=[
        Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1)),
        Depends(current_user_is_admin),
    ],
)


@admin.get("/monitor", response_model=dict)
def monitor(base_model = Depends(get_base_model)):
    """
    This endpoint can be used to monitor the digests consumed by the control plane. The probe interval is set in the configuration to 10 seconds.
    """
    client = get_client()
    probe = client.loop_digest(base_model)
    if not probe:
        return {"message": "No digests consumed!"}
    return probe


@admin.get("/table_info", response_model=list)
def table_info():
    """
    This endpoint can be used to get the information about the tables in the data plane. The information includes the table name, table type and amount of occupied table entries.
    """
    client = get_client()
    return client.get_base_info()

@admin.get("/port_info", response_model=list)
def table_info():
    """
    This endpoint can be used to get the information about the ports of the hardware unit running P4Slice.
    """
    client = get_client()
    return client.get_port_info()

@admin.post("/firewall")
def add_firewall(entry: FirewallEntry):
    """
    This endpoint can be used to add a firewall entry to the data plane. The firewall entry blocks the traffic from the source IP address with the given prefix length.
    """
    client = get_client()
    client.add_firewall_entry(entry.src_addr, entry.prefix_len)

@admin.post("/arp_route", response_model=dict)
def add_arp(entry: ArpEntry):
    """
    This endpoint can be used to add an ARP entry to the data plane. The ARP entry maps the destination IP address to the given port.
    """
    client = get_client()
    arp_insert_state = client.add_arp_entry(**entry.model_dump())
    if arp_insert_state:
        return {"message": f"Creating ARP entry with {entry.dst_addr} to PORT {entry.port} successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add arp entry, configuring control plane tables failed!")


@admin.post("/vlan_route", response_model=dict)
def add_vlan(entry: VlanEntry):
    """
    This endpoint can be used to add a VLAN entry to the data plane. The VLAN entry maps the VLAN ID to the given port.
    """
    client = get_client()
    vlan_insert_state = client.add_vlan_entry(**entry.model_dump())
    if vlan_insert_state:
        return {"message": f"Creating VLAN entry with VLAN ID {entry.vlan_id} to PORT {entry.port} successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add vlan entry, configuring control plane tables failed!")

@admin.post("/ip_route", response_model=dict)
def add_ip(entry: IpEntry):
    """
    This endpoint can be used to add an IP entry to the data plane. The IP entry maps the destination IP address to the given port.
    """
    client = get_client()
    ip_insert_state = client.add_ip_entry(**entry.model_dump())
    if ip_insert_state:
        return {"message": f"Creating IP entry with destination IP {entry.dst_addr} to PORT {entry.port} successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add IP entry, configuring control plane tables failed!")

@admin.post("/egress_route", response_model=dict)
def add_egress(port: Annotated[int, Field(ge=0, le=400)]):
    """
    This endpoint can be used to set a port as egress port. This can be used to strip the internally used VLAN header from the packet after exiting the specified port.
    """
    client = get_client()
    ip_insert_state = client.add_egress_entry(port)
    if ip_insert_state:
        return {"message": f"Setting PORT {port} as egress successful!"}
    else:
        raise HTTPException(status_code=400, detail="Could not add egress entry, configuring control plane tables failed!")
    