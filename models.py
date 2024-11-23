from typing import Literal, List
from ipaddress import IPv4Address, IPv6Address
from uuid import uuid4
from pydantic import BaseModel, Field, SecretStr, UUID4

DEFAULT_LENGTH = 50



# Slice Management
class FlowIdentification(BaseModel):
    source_ip: IPv4Address | IPv6Address
    destination_ip: IPv4Address | IPv6Address
    source_port: int
    destination_port: int
    protocol: Literal["TCP", "UDP", "QUIC"]

class BaseSlice(BaseModel):
    id: UUID4 = uuid4()
    min_bandwidth: float
    max_bandwidth: float
    identification: List[FlowIdentification]


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
