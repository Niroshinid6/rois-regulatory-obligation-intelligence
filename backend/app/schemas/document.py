from typing import Optional, List, Any
from pydantic import BaseModel

class DocumentBase(BaseModel):
    title: str
    circular_number: Optional[str] = None
    regulator: str = "IFSCA"
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    category: str = "Circular"
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentPageResponse(BaseModel):
    id: int
    page_number: int
    char_count: int
    word_count: int
    has_selectable_text: bool
    extracted_text: str
    bounding_boxes: List[Any] = []
    layout_blocks: List[Any] = []
    extraction_method: str = "pdf_text"
    ocr_confidence: Optional[float] = None
    requires_human_review: bool = False

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: int
    file_path: Optional[str] = None
    file_hash: str
    file_size: int
    status: str
    storage_provider: Optional[str] = None
    storage_status: str = "legacy"
    processing_status: str = "not_started"
    can_download: bool = True
    page_count: int
    created_at: str
    created_by: Optional[int] = None
    obligation_count: Optional[int] = 0

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentResponse]
