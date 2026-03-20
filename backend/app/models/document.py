from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("owners.id"), nullable=False)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=True)
    filename = Column(String, nullable=False)
    doc_type = Column(
        Enum("menu", "allergy", "policy", "faq", "general", name="doc_type_enum"),
        default="general"
    )
    content = Column(Text, nullable=True)       # Extracted full text
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("Owner", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    owner_id = Column(String, ForeignKey("owners.id"), nullable=False)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=True)
    chunk_text = Column(Text, nullable=False)
    doc_type = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")
