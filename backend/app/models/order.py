from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Enum, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    status = Column(
        Enum("new", "confirmed", "preparing", "ready", "picked_up", "cancelled", name="order_status"),
        default="new"
    )
    total = Column(Float, default=0.0)
    pay_method = Column(Enum("stripe_link", "cash", "card_on_pickup", name="pay_method_enum"), default="stripe_link")
    payment_status = Column(Enum("pending", "paid", "failed", name="payment_status_enum"), default="pending")
    stripe_payment_link = Column(String, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    call_sid = Column(String, nullable=True, index=True)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    modification = Column(Text, nullable=True)  # e.g. "no onions, extra cheese"

    # Relationships
    order = relationship("Order", back_populates="items")
