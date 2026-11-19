import os
import json
import hashlib
import tempfile
import uuid
from pathlib import Path
from io import BytesIO
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pypdf import PdfReader

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.document import Document, DocumentPage, EvidenceSpan
from app.models.obligation import Obligation
from app.models.control import ObligationControl, ControlCategory
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentPageResponse
from app.services.pdf_extractor import PDFExtractionService, PDFExtractionError
from app.services.obligation_extractor import ObligationExtractor
from app.services.control_mapper import ControlMapper
from app.services.audit_service import AuditService

router = APIRouter(prefix="/documents", tags=["Regulatory Documents"])

@router.get("/", response_model=DocumentListResponse)
def list_documents(
    search: Optional[str] = None,
    regulator: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Document)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Document.title.ilike(term)) | (Document.circular_number.ilike(term)))

    if regulator:
        query = query.filter(Document.regulator == regulator)

    if status_filter:
        query = query.filter(Document.status == status_filter)

    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for d in docs:
        items.append(DocumentResponse(
            id=d.id,
            title=d.title,
            circular_number=d.circular_number,
            regulator=d.regulator,
            publication_date=d.publication_date,
            effective_date=d.effective_date,
            category=d.category,
            description=d.description,
            file_path=d.file_path,
            file_hash=d.file_hash,
            file_size=d.file_size,
            status=d.status,
            page_count=d.page_count,
            created_at=d.created_at.isoformat(),
            created_by=d.created_by,
            obligation_count=len(d.obligations)
        ))

    return DocumentListResponse(total=total, items=items)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    circular_number: Optional[str] = Form(None),
    regulator: str = Form("IFSCA"),
    publication_date: Optional[str] = Form(None),
    effective_date: Optional[str] = Form(None),
    category: str = Form("Circular"),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["compliance_officer", "admin"]))
):
    original_filename = Path(file.filename or "").name
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Only PDF documents (.pdf) are permitted.",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    hasher = hashlib.sha256()
    chunks = []
    size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_MB}MB).",
            )
        hasher.update(chunk)
        chunks.append(chunk)

    contents = b"".join(chunks)
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file signature.")
    if b"%%EOF" not in contents[-1024:]:
        raise HTTPException(status_code=400, detail="Corrupted or incomplete PDF file.")

    file_hash = hasher.hexdigest()
    existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing_doc:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate document detected. This PDF was previously uploaded as '{existing_doc.title}' (ID: {existing_doc.id})."
        )

    try:
        reader = PdfReader(BytesIO(contents))
        if reader.is_encrypted:
            raise PDFExtractionError("Password-protected PDFs are not supported.")
        if len(reader.pages) == 0:
            raise PDFExtractionError("PDF contains zero pages.")
    except PDFExtractionError:
        raise HTTPException(status_code=400, detail="Password-protected PDFs are not supported.")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Corrupted or invalid PDF structure.") from exc

    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    server_filename = f"{uuid.uuid4().hex}.pdf"
    upload_path = str(upload_dir / server_filename)

    fd, temp_path = tempfile.mkstemp(prefix="rois-upload-", suffix=".pdf", dir=str(upload_dir))
    os.close(fd)
    try:
        with open(temp_path, "wb") as output:
            output.write(contents)
        extraction_data = PDFExtractionService.extract_document(temp_path)
    except PDFExtractionError as pe:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(pe)}")
    os.replace(temp_path, upload_path)

    new_doc = Document(
        title=title.strip(),
        circular_number=circular_number.strip() if circular_number else None,
        regulator=regulator.strip(),
        publication_date=publication_date.strip() if publication_date else None,
        effective_date=effective_date.strip() if effective_date else None,
        category=category.strip(),
        description=description.strip() if description else None,
        file_path=upload_path,
        file_hash=file_hash,
        file_size=len(contents),
        status=extraction_data["status"],
        page_count=extraction_data["page_count"],
        created_by=current_user.id
    )
    db.add(new_doc)
    db.flush()

    # Save document pages
    for p in extraction_data["pages"]:
        db.add(DocumentPage(
            document_id=new_doc.id,
            page_number=p["page_number"],
            extracted_text=p["text"],
            char_count=p["char_count"],
            word_count=p["word_count"],
            has_selectable_text=p["has_selectable_text"],
            bounding_boxes_json=json.dumps(p["bounding_boxes"]),
            layout_blocks_json=json.dumps(p["layout_blocks"]),
            extraction_method=p["extraction_method"],
            ocr_confidence=p["ocr_confidence"],
            requires_human_review=p["requires_human_review"]
        ))
    db.flush()

    # Extract obligations if document has selectable text
    saved_obligations_count = 0
    if extraction_data["has_selectable_text"]:
        extracted_obls = ObligationExtractor.extract_from_pages(
            extraction_data["pages"],
            new_doc.circular_number
        )
        all_categories = db.query(ControlCategory).filter(ControlCategory.is_active == True).all()
        cat_dicts = [{"id": c.id, "code": c.code, "name": c.name} for c in all_categories]

        for raw_o in extracted_obls:
            span = EvidenceSpan(
                document_id=new_doc.id,
                page_number=raw_o["source_page"],
                exact_text=raw_o["source_text"],
                char_start=raw_o["char_start"],
                char_end=raw_o["char_end"],
                bounding_box_json=json.dumps(raw_o["bounding_box"]),
                confidence=raw_o["confidence_score"]
            )
            db.add(span)
            db.flush()

            obl = Obligation(
                obligation_code=raw_o["obligation_code"],
                document_id=new_doc.id,
                evidence_span_id=span.id,
                source_page=raw_o["source_page"],
                obligation_text=raw_o["obligation_text"],
                responsible_entity=raw_o["responsible_entity"],
                required_action=raw_o["required_action"],
                deadline=raw_o["deadline"],
                conditions_json=json.dumps(raw_o["conditions"]),
                exceptions_json=json.dumps(raw_o["exceptions"]),
                confidence_score=raw_o["confidence_score"],
                evidence_status=raw_o["evidence_status"],
                review_status=raw_o["review_status"],
                extraction_method=raw_o["extraction_method"]
            )
            db.add(obl)
            db.flush()
            saved_obligations_count += 1

            # Suggest controls
            suggestions = ControlMapper.suggest_controls_for_obligation(obl.obligation_text, cat_dicts)
            for s in suggestions:
                db.add(ObligationControl(
                    obligation_id=obl.id,
                    control_category_id=s["control_category_id"],
                    rationale=s["rationale"],
                    mapping_method="nlp_suggested",
                    review_status="suggested"
                ))

    try:
        db.commit()
        db.refresh(new_doc)
    except Exception:
        db.rollback()
        if os.path.exists(upload_path):
            os.unlink(upload_path)
        raise HTTPException(status_code=500, detail="Document processing could not be saved.")

    AuditService.log(
        db,
        action="document_upload",
        resource_type="document",
        resource_id=str(new_doc.id),
        user_id=current_user.id,
        details={
            "title": new_doc.title,
            "circular_number": new_doc.circular_number,
            "page_count": new_doc.page_count,
            "obligations_extracted": saved_obligations_count
        }
    )

    return DocumentResponse(
        id=new_doc.id,
        title=new_doc.title,
        circular_number=new_doc.circular_number,
        regulator=new_doc.regulator,
        publication_date=new_doc.publication_date,
        effective_date=new_doc.effective_date,
        category=new_doc.category,
        description=new_doc.description,
        file_path=new_doc.file_path,
        file_hash=new_doc.file_hash,
        file_size=new_doc.file_size,
        status=new_doc.status,
        page_count=new_doc.page_count,
        created_at=new_doc.created_at.isoformat(),
        created_by=new_doc.created_by,
        obligation_count=saved_obligations_count
    )

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        circular_number=doc.circular_number,
        regulator=doc.regulator,
        publication_date=doc.publication_date,
        effective_date=doc.effective_date,
        category=doc.category,
        description=doc.description,
        file_path=doc.file_path,
        file_hash=doc.file_hash,
        file_size=doc.file_size,
        status=doc.status,
        page_count=doc.page_count,
        created_at=doc.created_at.isoformat(),
        created_by=doc.created_by,
        obligation_count=len(doc.obligations)
    )

@router.get("/{document_id}/pages", response_model=List[DocumentPageResponse])
def get_document_pages(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    pages = db.query(DocumentPage).filter(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number.asc()).all()

    return [
        DocumentPageResponse(
            id=p.id,
            page_number=p.page_number,
            char_count=p.char_count,
            word_count=p.word_count,
            has_selectable_text=p.has_selectable_text,
            extracted_text=p.extracted_text,
            bounding_boxes=json.loads(p.bounding_boxes_json or "[]"),
            layout_blocks=json.loads(p.layout_blocks_json or "[]"),
            extraction_method=p.extraction_method,
            ocr_confidence=p.ocr_confidence,
            requires_human_review=p.requires_human_review
        )
        for p in pages
    ]

@router.get("/{document_id}/pdf")
def get_document_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Underlying PDF file not found on disk storage.")

    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        filename=os.path.basename(doc.file_path)
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "compliance_officer"]))
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc_title = doc.title
    db.delete(doc)
    db.commit()

    AuditService.log(
        db,
        action="document_delete",
        resource_type="document",
        resource_id=str(document_id),
        user_id=current_user.id,
        details={"deleted_title": doc_title}
    )

    return {"message": f"Document '{doc_title}' and associated extraction records deleted successfully."}
