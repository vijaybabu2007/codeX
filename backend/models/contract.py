import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class ObjectiveContract(Base):
    __tablename__ = "objective_contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_version_id = Column(String(36), ForeignKey("source_versions.id"), nullable=False)
    title = Column(String(255), nullable=False)
    target_learner_level = Column(String(64), nullable=False)  # e.g., "Grade 10"
    expected_difficulty = Column(String(32), nullable=False)   # e.g., "Medium", "Introductory"
    constraints_json = Column(Text, nullable=True)             # JSON string for constraints
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source_version = relationship("SourceVersion", back_populates="contracts")
    objectives = relationship("LearningObjective", back_populates="contract", cascade="all, delete-orphan", order_by="LearningObjective.code")
    learning_packs = relationship("LearningPack", back_populates="contract")

class LearningObjective(Base):
    __tablename__ = "learning_objectives"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("objective_contracts.id"), nullable=False)
    code = Column(String(32), nullable=False)         # e.g., "LO-01"
    description = Column(Text, nullable=False)
    bloom_level = Column(String(32), nullable=False, default="Understand")

    contract = relationship("ObjectiveContract", back_populates="objectives")
