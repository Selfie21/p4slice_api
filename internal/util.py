import ipaddress
from pydantic import UUID4
from typing import Optional

from models import BaseSlice


def ip2int(ip):
    return int(ipaddress.ip_address(ip))


def int2ip(ip):
    return ipaddress.ip_address(ip)


def get_from_database(id: UUID4, database: dict) -> Optional[BaseSlice]:
    for entry in database:
        if entry and entry.id == id:
            return entry
    return None


def insert_into_database(database: dict, slice: BaseSlice) -> Optional[int]:
    for index, entry in enumerate(database):
        if not entry:
            database[index] = slice
            return index
    return None


def delete_from_database(id: UUID4, database: dict) -> bool:
    for index, entry in enumerate(database):
        if entry and entry.id == id:
            database[index] = None
            return True
    return False
