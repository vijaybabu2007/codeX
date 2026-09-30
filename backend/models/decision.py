import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class TeacherDecision(Base):
    __tablename__ = "teacher_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_version_id = Column(String(36), ForeignKey("asset_versions.id"), nullable=True)
    question_version_id = Column(String(36), ForeignKey("quiz_question_versions.id"), nullable=True)
    action = Column(String(32), nullable=False)  # "APPROVED", "NEEDS_REVISION", "OVERRIDE"
    acknowledged_warning_ids_json = Column(Text, nullable=True)  # JSON list of warning IDs
    teacher_notes = Column(Text, nullable=True)  # Required if action == "OVERRIDE"
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    asset_version = relationship("AssetVersion", back_populates="decisions")
    question_version = relationship("QuizQuestionVersion", back_populates="decisions")
