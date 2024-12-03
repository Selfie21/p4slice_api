from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter
from typing import List

from models import FirewallEntry
from internal.authlib import current_user_is_admin
from dependencies import get_config, get_client

config = get_config()
admin = APIRouter(
    prefix="/admin",
    dependencies=[
        Depends(RateLimiter(times=config.rate_limit_per_minute, minutes=1)),
        Depends(current_user_is_admin),
    ],
)


@admin.get("/monitor", response_model=List)
def monitor():
    client = get_client()
    base_model = client.bfrt_info.learn_get("digest_inst")
    probe = client.loop_digest(base_model)
    if not probe:
        probe.append("No digests received!")
    return probe


@admin.get("/table_info", response_model=List)
def table_info():
    client = get_client()
    return client.get_base_info()


@admin.post("/firewall")
def add_firewall(entry: FirewallEntry):
    client = get_client()
    client.add_firewall_entry(entry.src_addr, entry.prefix_len)
