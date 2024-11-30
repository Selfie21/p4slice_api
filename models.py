from typing import Literal, List, Optional
from ipaddress import IPv4Address, IPv6Address
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, SecretStr, UUID4

DEFAULT_LENGTH = 50
PROTOCOL_MAPPING = {"ICMP": 1, "TCP": 6, "UDP": 17}

class Configuration(BaseModel):
    rate_limit_per_minute: int
    jwt_secret_key: SecretStr
    server_url: str
    server_port: int
    redis_url: str
    redis_password: SecretStr
    
# Slice Management
class FlowIdentification(BaseModel):
    src_addr: IPv4Address | IPv6Address = Field(alias="source_ip")
    dst_addr: IPv4Address | IPv6Address = Field(alias="destination_ip")
    src_port: int = Field(alias="source_port")
    dst_port: int = Field(alias="destination_port")
    protocol: Literal["ICMP", "TCP", "UDP"]

    @field_validator("protocol", mode="after")
    @classmethod
    def map_iptype(cls, raw: Literal["ICMP", "TCP", "UDP"]) -> int:
        return PROTOCOL_MAPPING[raw]

    @field_validator("src_addr","dst_addr", mode="after")
    @classmethod
    def ip_to_str(cls, raw: IPv4Address | IPv6Address) -> str:
        return str(raw)
    
class BaseSlice(BaseModel):
    id: UUID4 = uuid4()
    slice_index: Optional[int] = None
    guaranteed_bandwidth: int = Field(description="guaranteed bandwidth in kilobit/s")
    max_bandwidth: int = Field(description="maximum bandwidth in kilobit/s")
    flow_identification: List[FlowIdentification]


# User Management
class User(BaseModel):
    username: str = Field(max_length=DEFAULT_LENGTH)
    hashed_password: SecretStr
    admin: bool
    slice: List[BaseSlice] = []


class CreateUser(BaseModel):
    username: str = Field(max_length=DEFAULT_LENGTH)
    password: str = Field(max_length=DEFAULT_LENGTH)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
