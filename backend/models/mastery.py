import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from backend.database import Base

class ObjectiveMastery(Base):
    __tablename__ = "objective_masteries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(128), nullable=False, index=True)
    pack_id = Column(String(36), ForeignKey("learning_packs.id"), nullable=False, index=True)
    objective_id = Column(String(64), nullable=False)  # e.g., "LO-01"
    attempted_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    mastery_state = Column(String(32), nullable=False, default="NEEDS_PRACTICE")  # MASTERED, DEVELOPING, NEEDS_PRACTICE
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class StudentQuizAttempt(Base):
    __tablename__ = "student_quiz_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(128), nullable=False, index=True)
    pack_id = Column(String(36), ForeignKey("learning_packs.id"), nullable=False, index=True)
    total_questions = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    score_percentage = Column(Float, nullable=False, default=0.0)
    answers_json = Column(Text, nullable=False)  # JSON dictionary of question_id -> answer
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
