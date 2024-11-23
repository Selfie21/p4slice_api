from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from models import BaseSlice

slice = APIRouter(prefix="/slice", tags=["slice"])

@slice.post("/add")
def add_slice(slice: BaseSlice):
    return slice

@slice.post("/del")
def delete_slice(slice_id: UUID4):
    return slice