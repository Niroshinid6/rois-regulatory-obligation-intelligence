from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ControlCategory(Base):
    __tablename__ = "control_categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., GOV-01, RISK-01, REP-01
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    mappings = relationship("ObligationControl", back_populates="control_category", cascade="all, delete-orphan")

class ObligationControl(Base):
    __tablename__ = "obligation_controls"

    id = Column(Integer, primary_key=True, index=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id"), nullable=False)
    control_category_id = Column(Integer, ForeignKey("control_categories.id"), nullable=False)
    rationale = Column(Text, nullable=False)
    mapping_method = Column(String(50), default="nlp_suggested", nullable=False)  # nlp_suggested, reviewer_assigned
    review_status = Column(String(50), default="suggested", nullable=False)  # suggested, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    obligation = relationship("Obligation", back_populates="controls")
    control_category = relationship("ControlCategory", back_populates="mappings")
