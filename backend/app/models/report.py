from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ImpactReport(Base):
    __tablename__ = "impact_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    comparison_id = Column(Integer, ForeignKey("comparisons.id"), nullable=True)
    executive_summary = Column(Text, nullable=False)
    metrics_json = Column(Text, default="{}", nullable=False)
    report_data_json = Column(Text, default="{}", nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document")
    comparison = relationship("Comparison")
    generator = relationship("User")
