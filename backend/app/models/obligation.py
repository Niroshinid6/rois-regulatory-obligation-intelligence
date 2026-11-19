from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Obligation(Base):
    __tablename__ = "obligations"

    id = Column(Integer, primary_key=True, index=True)
    obligation_code = Column(String(50), index=True, nullable=False)  # e.g., OBL-2024-001
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    evidence_span_id = Column(Integer, ForeignKey("evidence_spans.id"), nullable=True)
    source_page = Column(Integer, default=1, nullable=False)
    obligation_text = Column(Text, nullable=False)
    responsible_entity = Column(String(255), nullable=True)
    required_action = Column(Text, nullable=False)
    deadline = Column(String(255), nullable=True)
    conditions_json = Column(Text, default="[]", nullable=False)
    exceptions_json = Column(Text, default="[]", nullable=False)
    confidence_score = Column(Float, default=0.85, nullable=False)
    evidence_status = Column(String(50), default="anchored", nullable=False)  # anchored, unverified, mismatched
    review_status = Column(String(50), default="pending", nullable=False)  # pending, approved, corrected, rejected, requires_investigation
    extraction_method = Column(String(50), default="rule_nlp_baseline", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="obligations")
    evidence_span = relationship("EvidenceSpan", back_populates="obligation")
    controls = relationship("ObligationControl", back_populates="obligation", cascade="all, delete-orphan")
    reviews = relationship("ReviewRecord", back_populates="obligation", cascade="all, delete-orphan")

class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    base_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    target_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    base_document = relationship("Document", foreign_keys=[base_document_id])
    target_document = relationship("Document", foreign_keys=[target_document_id])
    changes = relationship("ObligationChange", back_populates="comparison", cascade="all, delete-orphan")

class ObligationChange(Base):
    __tablename__ = "obligation_changes"

    id = Column(Integer, primary_key=True, index=True)
    comparison_id = Column(Integer, ForeignKey("comparisons.id"), nullable=False)
    previous_obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=True)
    current_obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=True)
    change_type = Column(String(50), nullable=False)  # new, modified, retired, unchanged, requires_review
    change_explanation = Column(Text, nullable=False)
    diff_details_json = Column(Text, default="{}", nullable=False)
    human_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    comparison = relationship("Comparison", back_populates="changes")
    previous_obligation = relationship("Obligation", foreign_keys=[previous_obligation_id])
    current_obligation = relationship("Obligation", foreign_keys=[current_obligation_id])
