from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    call_sid = Column(String, nullable=False, unique=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    messages = Column(Text, default="[]")   # JSON array of {role, content} dicts
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    status = Column(String, default="active")   # active | completed | abandoned
    language_detected = Column(String, nullable=True)  # 'en' | 'es' | 'zh'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    restaurant = relationship("Restaurant", back_populates="conversations")
