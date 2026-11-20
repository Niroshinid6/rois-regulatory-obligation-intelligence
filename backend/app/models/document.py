from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    circular_number = Column(String(100), index=True, nullable=True)
    regulator = Column(String(100), default="IFSCA", nullable=False)
    publication_date = Column(String(50), nullable=True)
    effective_date = Column(String(50), nullable=True)
    category = Column(String(100), default="Circular", nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(1000), nullable=True)
    storage_provider = Column(String(20), nullable=True)
    storage_object_key = Column(String(1000), nullable=True)
    storage_status = Column(String(32), nullable=False, default="legacy")
    storage_migrated_at = Column(DateTime, nullable=True)
    storage_upload_id = Column(String(64), nullable=True, unique=True, index=True)
    processing_status = Column(String(32), nullable=False, default="not_started")
    file_hash = Column(String(64), index=True, nullable=False)
    file_size = Column(BigInteger, default=0, nullable=False)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, queued, processing, processed, requires_ocr, failed, requires_review
    page_count = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    evidence_spans = relationship("EvidenceSpan", back_populates="document", cascade="all, delete-orphan")
    obligations = relationship("Obligation", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String(20), default="1.0", nullable=False)
    predecessor_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)  # 1-indexed
    extracted_text = Column(Text, nullable=False)
    char_count = Column(Integer, default=0, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    has_selectable_text = Column(Boolean, default=True, nullable=False)
    bounding_boxes_json = Column(Text, default="[]", nullable=False)  # extracted word boxes
    layout_blocks_json = Column(Text, default="[]", nullable=False)  # paragraphs / lines
    extraction_method = Column(String(20), default="pdf_text", nullable=False)
    ocr_confidence = Column(Float, nullable=True)
    requires_human_review = Column(Boolean, default=False, nullable=False)

    document = relationship("Document", back_populates="pages")

class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    exact_text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    bounding_box_json = Column(Text, default="{}", nullable=False)  # {x0, y0, x1, y1, width, height}
    confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="evidence_spans")
    obligation = relationship("Obligation", back_populates="evidence_span", uselist=False)
