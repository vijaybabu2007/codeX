import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("generated_assets.id"), nullable=False)
    ordinal_position = Column(Integer, nullable=False)
    active_version_id = Column(String(36), nullable=True)

    asset = relationship("GeneratedAsset", back_populates="quiz_questions")
    versions = relationship("QuizQuestionVersion", back_populates="question", cascade="all, delete-orphan", foreign_keys="QuizQuestionVersion.question_id")

class QuizQuestionVersion(Base):
    __tablename__ = "quiz_question_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("quiz_questions.id"), nullable=False)
    source_version_id = Column(String(36), ForeignKey("source_versions.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON list of string options
    correct_answer = Column(Text, nullable=False)
    objective_ids_json = Column(Text, nullable=False)  # JSON list of objective IDs
    supporting_quote = Column(Text, nullable=True)
    grounding_status = Column(String(32), nullable=False, default="UNVERIFIED")  # VERIFIED, UNVERIFIED, INSUFFICIENT_SOURCE
    review_status = Column(String(32), nullable=False, default="DRAFT")  # DRAFT, NEEDS_REVISION, APPROVED, OVERRIDE
    model_identifier = Column(String(64), nullable=False)
    teacher_notes = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    question = relationship("QuizQuestion", back_populates="versions", foreign_keys=[question_id])
    validations = relationship("ValidationReport", back_populates="question_version", cascade="all, delete-orphan")
    decisions = relationship("TeacherDecision", back_populates="question_version", cascade="all, delete-orphan")
