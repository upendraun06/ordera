from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MenuItemCreate(BaseModel):
    category: str
    name: str
    description: Optional[str] = None
    price: float
    available: bool = True


class MenuItemUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: str
    restaurant_id: str
    category: str
    name: str
    description: Optional[str]
    price: float
    available: bool
    created_at: datetime

    class Config:
        from_attributes = True
