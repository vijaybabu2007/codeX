import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    versions = relationship("SourceVersion", back_populates="document", cascade="all, delete-orphan", order_by="SourceVersion.version_number")

class SourceVersion(Base):
    __tablename__ = "source_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_document_id = Column(String(36), ForeignKey("source_documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    char_count = Column(Integer, nullable=False)
    mime_type = Column(String(64), nullable=False, default="text/plain")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("SourceDocument", back_populates="versions")
    contracts = relationship("ObjectiveContract", back_populates="source_version")
