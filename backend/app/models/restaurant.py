from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("owners.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)           # Customer-facing phone (Telnyx number)
    telnyx_phone = Column(String, nullable=True)    # Assigned Telnyx DID
    hours = Column(Text, nullable=True)             # JSON string of operating hours
    timezone = Column(String, default="America/New_York")
    estimated_wait_minutes = Column(String, default="20")
    employees = Column(Text, nullable=True)           # JSON array of employee timesheet data
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("Owner", back_populates="restaurants")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="restaurant", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="restaurant", cascade="all, delete-orphan")
