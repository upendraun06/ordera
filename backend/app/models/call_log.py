from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    call_sid = Column(String, nullable=False, unique=True, index=True)
    caller_phone = Column(String, nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String, default="completed")    # completed | abandoned | failed
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    ai_turns = Column(Integer, default=0)           # Number of AI exchanges
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    restaurant = relationship("Restaurant", back_populates="call_logs")
