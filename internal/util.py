from pydantic import UUID4
from typing import Optional, List

from models import BaseSlice

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

def used_bandwidth(slices: List[UUID4], database: dict) -> bool:
    total_bandwidth = 0
    for slice in slices:
        slice_data = get_from_database(slice, database) 
        if slice_data:
            total_bandwidth += slice_data.max_bandwidth
    return total_bandwidth
