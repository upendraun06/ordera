from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from app.middleware.auth import get_current_owner
from app.models.owner import Owner

router = APIRouter(prefix="/api/menu", tags=["menu"])


def _get_restaurant(db: Session, owner: Owner) -> Restaurant:
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == owner.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/", response_model=List[MenuItemResponse])
def list_menu(db: Session = Depends(get_db), current_owner: Owner = Depends(get_current_owner)):
    restaurant = _get_restaurant(db, current_owner)
    return db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant.id).all()


@router.post("/", response_model=MenuItemResponse, status_code=201)
def create_item(
    data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = _get_restaurant(db, current_owner)
    item = MenuItem(restaurant_id=restaurant.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=MenuItemResponse)
def update_item(
    item_id: str,
    data: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = _get_restaurant(db, current_owner)
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = _get_restaurant(db, current_owner)
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}


@router.post("/seed", status_code=201)
def seed_menu(db: Session = Depends(get_db), current_owner: Owner = Depends(get_current_owner)):
    """Seed a demo menu for development."""
    restaurant = _get_restaurant(db, current_owner)

    sample_items = [
        {"category": "Appetizers", "name": "Mozzarella Sticks", "price": 8.99, "description": "Golden fried with marinara sauce"},
        {"category": "Appetizers", "name": "Chicken Wings", "price": 12.99, "description": "Buffalo or BBQ, 10 pieces"},
        {"category": "Mains", "name": "Classic Burger", "price": 13.99, "description": "8oz beef patty, lettuce, tomato, onion"},
        {"category": "Mains", "name": "Grilled Chicken Sandwich", "price": 12.99, "description": "Herb-marinated chicken breast"},
        {"category": "Mains", "name": "Margherita Pizza", "price": 14.99, "description": "Tomato, mozzarella, fresh basil"},
        {"category": "Mains", "name": "Caesar Salad", "price": 10.99, "description": "Romaine, parmesan, croutons"},
        {"category": "Sides", "name": "French Fries", "price": 3.99, "description": "Crispy golden fries"},
        {"category": "Sides", "name": "Onion Rings", "price": 4.99, "description": "Beer-battered"},
        {"category": "Drinks", "name": "Soft Drink", "price": 2.99, "description": "Coke, Diet Coke, Sprite, Ginger Ale"},
        {"category": "Drinks", "name": "Fresh Lemonade", "price": 3.99, "description": "Freshly squeezed"},
        {"category": "Desserts", "name": "Chocolate Brownie", "price": 5.99, "description": "Warm with vanilla ice cream"},
    ]

    for item_data in sample_items:
        existing = db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant.id,
            MenuItem.name == item_data["name"]
        ).first()
        if not existing:
            db.add(MenuItem(restaurant_id=restaurant.id, **item_data))

    db.commit()
    return {"message": f"Seeded {len(sample_items)} menu items"}
