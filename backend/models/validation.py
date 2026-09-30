import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_version_id = Column(String(36), ForeignKey("asset_versions.id"), nullable=True)
    question_version_id = Column(String(36), ForeignKey("quiz_question_versions.id"), nullable=True)
    validation_type = Column(String(64), nullable=False)  # "GROUNDING", "KEY_INTEGRITY", "ALIGNMENT"
    severity = Column(String(16), nullable=False)         # "CRITICAL", "WARNING", "INFO"
    rule_code = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    evidence_snippet = Column(Text, nullable=True)
    affected_entity_id = Column(String(64), nullable=False) # asset ID or question ID
    is_blocking = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    asset_version = relationship("AssetVersion", back_populates="validations")
    question_version = relationship("QuizQuestionVersion", back_populates="validations")
