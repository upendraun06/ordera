from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RestaurantCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    timezone: str = "America/New_York"
    estimated_wait_minutes: str = "20"


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    timezone: Optional[str] = None
    estimated_wait_minutes: Optional[str] = None
    employees: Optional[str] = None


class RestaurantResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    address: Optional[str]
    phone: Optional[str]
    telnyx_phone: Optional[str]
    hours: Optional[str]
    timezone: str
    estimated_wait_minutes: str
    employees: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
