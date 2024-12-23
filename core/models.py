from typing import Literal, List, Annotated
from ipaddress import IPv4Address, IPv6Address
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, SecretStr, UUID4
from pydantic_extra_types.mac_address import MacAddress

DEFAULT_LENGTH = 50
PROTOCOL_MAPPING = {"ICMP": 1, "TCP": 6, "UDP": 17}


class Configuration(BaseModel):
    rate_limit_per_minute: int
    bandwidth_per_user_kbit: int
    jwt_secret_key: SecretStr
    grpc_urls: List[str]
    server_url: str
    server_port: int
    redis_url: str
    redis_password: SecretStr


# Slice Management
class FlowIdentification(BaseModel):
    src_addr: IPv4Address | IPv6Address = Field(alias="source_ip")
    dst_addr: IPv4Address | IPv6Address = Field(alias="destination_ip")
    #protocol: Literal["ICMP", "TCP", "UDP"]

    #@field_validator("protocol", mode="after")
    #@classmethod
    #def map_iptype(cls, raw: Literal["ICMP", "TCP", "UDP"]) -> int:
        #return PROTOCOL_MAPPING[raw]

    @field_validator("src_addr", "dst_addr", mode="after")
    @classmethod
    def ip_to_str(cls, raw: IPv4Address | IPv6Address) -> str:
        return str(raw)


class BaseSlice(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    guaranteed_bandwidth: Annotated[int, Field(strict=True, gt=0, description="guaranteed bandwidth in kilobit/s")]
    max_bandwidth: Annotated[int, Field(strict=True, gt=0, description="maximum bandwidth in kilobit/s")]
    flow_identification: Annotated[List[FlowIdentification], Field(min_length=1, max_length=20)]


class FirewallEntry(BaseModel):
    src_addr: IPv4Address | IPv6Address = Field(alias="source_ip")
    prefix_len: Annotated[int, Field(strict=True, ge=0, le=32, alias="prefix_len")]

    @field_validator("src_addr", mode="after")
    @classmethod
    def ip_to_str(cls, raw: IPv4Address | IPv6Address) -> str:
        return str(raw)

class IpEntry(BaseModel):
    dst_addr: IPv4Address | IPv6Address = Field(alias="destination_ip")
    prefix_len: Annotated[int, Field(strict=True, ge=0, le=32, alias="prefix_len")]
    dst_mac_addr: MacAddress = "12:34:56:78:9a:bc"
    port : Annotated[int, Field(strict=True, ge=0, le=400)]

    @field_validator("dst_addr", mode="after")
    @classmethod
    def ip_to_str(cls, raw: IPv4Address | IPv6Address) -> str:
        return str(raw)

class VlanEntry(BaseModel):
    vlan_id: int
    dst_mac_addr: MacAddress = "12:34:56:78:9a:bc"
    port : Annotated[int, Field(strict=True, ge=0, le=400)]

class ArpEntry(BaseModel):
    dst_addr: IPv4Address = Field(alias="destination_ip")
    port : Annotated[int, Field(strict=True, ge=0, le=400)]

    @field_validator("dst_addr", mode="after")
    @classmethod
    def ip_to_str(cls, raw: IPv4Address) -> str:
        return str(raw)
    

# User Management
class User(BaseModel):
    username: str = Field(max_length=DEFAULT_LENGTH)
    hashed_password: SecretStr
    admin: bool
    slices: List[UUID4] = []


class CreateUser(BaseModel):
    username: str = Field(max_length=DEFAULT_LENGTH)
    password: str = Field(max_length=DEFAULT_LENGTH)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
