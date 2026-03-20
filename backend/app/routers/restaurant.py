from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from app.middleware.auth import get_current_owner
from app.models.owner import Owner

router = APIRouter(prefix="/api/restaurant", tags=["restaurant"])


@router.get("/", response_model=RestaurantResponse)
def get_restaurant(
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_owner.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.put("/", response_model=RestaurantResponse)
def update_restaurant(
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == current_owner.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)
    return restaurant
