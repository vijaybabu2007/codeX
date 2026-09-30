import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class LearningPack(Base):
    __tablename__ = "learning_packs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("objective_contracts.id"), nullable=False)
    source_version_id = Column(String(36), ForeignKey("source_versions.id"), nullable=False)
    owner_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    contract = relationship("ObjectiveContract", back_populates="learning_packs")
    assets = relationship("GeneratedAsset", back_populates="learning_pack", cascade="all, delete-orphan")

class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learning_pack_id = Column(String(36), ForeignKey("learning_packs.id"), nullable=False)
    asset_type = Column(String(64), nullable=False)  # "concept_explanation", "formative_quiz"
    active_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    learning_pack = relationship("LearningPack", back_populates="assets")
    versions = relationship("AssetVersion", back_populates="asset", cascade="all, delete-orphan", foreign_keys="AssetVersion.asset_id")
    quiz_questions = relationship("QuizQuestion", back_populates="asset", cascade="all, delete-orphan")

class AssetVersion(Base):
    __tablename__ = "asset_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("generated_assets.id"), nullable=False)
    source_version_id = Column(String(36), ForeignKey("source_versions.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    content_json = Column(Text, nullable=False)  # JSON string
    review_status = Column(String(32), nullable=False, default="DRAFT")  # DRAFT, NEEDS_REVISION, APPROVED, OVERRIDE
    model_identifier = Column(String(64), nullable=False)
    prompt_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    asset = relationship("GeneratedAsset", back_populates="versions", foreign_keys=[asset_id])
    validations = relationship("ValidationReport", back_populates="asset_version", cascade="all, delete-orphan")
    decisions = relationship("TeacherDecision", back_populates="asset_version", cascade="all, delete-orphan")
