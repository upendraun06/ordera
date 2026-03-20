from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.middleware.auth import get_current_owner
from app.models.owner import Owner

router = APIRouter(prefix="/api/orders", tags=["orders"])

VALID_STATUSES = {"new", "confirmed", "preparing", "ready", "picked_up", "cancelled"}
AUTO_CONFIRM_SECONDS = 60


def _get_restaurant(db: Session, owner: Owner) -> Restaurant:
    restaurant = db.query(Restaurant).filter(Restaurant.owner_id == owner.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


def _auto_confirm_stale(db: Session, restaurant_id: str):
    """Auto-confirm new orders older than AUTO_CONFIRM_SECONDS (inline, no background task)."""
    cutoff = datetime.utcnow() - timedelta(seconds=AUTO_CONFIRM_SECONDS)
    stale = (
        db.query(Order)
        .filter(Order.restaurant_id == restaurant_id, Order.status == "new", Order.created_at <= cutoff)
        .all()
    )
    for order in stale:
        order.status = "confirmed"
    if stale:
        db.commit()


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    status: Optional[str] = Query(None),
    order_date: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = _get_restaurant(db, current_owner)

    # Auto-confirm stale orders on every list request
    _auto_confirm_stale(db, restaurant.id)

    q = db.query(Order).filter(Order.restaurant_id == restaurant.id)

    if status:
        q = q.filter(Order.status == status)

    if order_date:
        from sqlalchemy import func
        q = q.filter(func.date(Order.created_at) == order_date)

    return q.order_by(Order.created_at.desc()).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = _get_restaurant(db, current_owner)
    order = db.query(Order).filter(
        Order.id == order_id, Order.restaurant_id == restaurant.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {VALID_STATUSES}")

    restaurant = _get_restaurant(db, current_owner)
    order = db.query(Order).filter(
        Order.id == order_id, Order.restaurant_id == restaurant.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = data.status
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}")
def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner),
):
    restaurant = _get_restaurant(db, current_owner)
    order = db.query(Order).filter(
        Order.id == order_id, Order.restaurant_id == restaurant.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "cancelled"
    db.commit()
    return {"message": "Order cancelled"}
