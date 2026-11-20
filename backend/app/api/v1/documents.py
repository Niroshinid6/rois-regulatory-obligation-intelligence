import os
import json
import hashlib
import uuid
from pathlib import Path
from io import BytesIO
import tempfile as tempfile_module
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
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
from app.core.storage import get_storage_provider
from app.services.storage.base import StorageNotFoundError, StorageVerificationError
from app.models.audit import AuditLog
from app.models.storage_cleanup import StorageCleanupTask

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
            file_path=None,
            file_hash=d.file_hash,
            file_size=d.file_size,
            status=d.status,
            page_count=d.page_count,
            created_at=d.created_at.isoformat(),
            created_by=d.created_by,
            obligation_count=len(d.obligations),
            storage_provider=d.storage_provider,
            storage_status=d.storage_status,
            processing_status=d.processing_status,
            can_download=d.storage_status in ("available", "legacy"),
        ))

    return DocumentListResponse(total=total, items=items)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    circular_number: Optional[str] = Form(None),
    upload_id: Optional[str] = Form(None),
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
    if file.content_type not in (None, "", "application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="Unsupported PDF media type.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    hasher = hashlib.sha256()
    size = 0
    spool = tempfile_module.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b")
    try:
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_MB}MB).",
                )
            spool.write(chunk)
            hasher.update(chunk)

        spool.seek(0)
        if spool.read(5) != b"%PDF-":
            raise HTTPException(status_code=400, detail="Invalid PDF file signature.")
        spool.seek(0, os.SEEK_END)
        eof_position = spool.tell()
        spool.seek(max(0, eof_position - 1024))
        if b"%%EOF" not in spool.read():
            raise HTTPException(status_code=400, detail="Corrupted or incomplete PDF file.")

        spool.seek(0)
        file_hash = hasher.hexdigest()
    except HTTPException:
        spool.close()
        raise
    except Exception:
        spool.close()
        raise HTTPException(status_code=400, detail="Could not process the uploaded PDF.")

    resolved_upload_id = upload_id.strip() if upload_id else uuid.uuid4().hex
    if len(resolved_upload_id) > 64:
        spool.close()
        raise HTTPException(status_code=400, detail="Invalid upload operation identifier.")

    existing_upload = db.query(Document).filter(
        Document.storage_upload_id == resolved_upload_id
    ).first()
    if existing_upload:
        if existing_upload.file_hash != file_hash:
            spool.close()
            raise HTTPException(
                status_code=409,
                detail="Upload operation identifier is already associated with different PDF content.",
            )
        if existing_upload.processing_status == "completed":
            if existing_upload.storage_object_key:
                try:
                    provider = get_storage_provider()
                    stored = await provider.open(existing_upload.storage_object_key)
                    try:
                        stored_hash = PDFExtractionService.calculate_file_hash(stored.stream)
                        object_valid = (
                            stored.size == existing_upload.file_size
                            and stored_hash == existing_upload.file_hash
                        )
                    finally:
                        stored.stream.close()
                    if object_valid:
                        spool.close()
                        return DocumentResponse(
                            id=existing_upload.id,
                            title=existing_upload.title,
                            circular_number=existing_upload.circular_number,
                            regulator=existing_upload.regulator,
                            publication_date=existing_upload.publication_date,
                            effective_date=existing_upload.effective_date,
                            category=existing_upload.category,
                            description=existing_upload.description,
                            file_path=None,
                            file_hash=existing_upload.file_hash,
                            file_size=existing_upload.file_size,
                            status=existing_upload.status,
                            page_count=existing_upload.page_count,
                            created_at=existing_upload.created_at.isoformat(),
                            created_by=existing_upload.created_by,
                            obligation_count=len(existing_upload.obligations),
                            storage_provider=existing_upload.storage_provider,
                            storage_status=existing_upload.storage_status,
                            processing_status=existing_upload.processing_status,
                            can_download=existing_upload.storage_status in ("available", "legacy"),
                        )
                    existing_upload.storage_status = "storage_failed"
                    db.commit()
                except Exception:
                    existing_upload.storage_status = "storage_failed"
                    db.commit()
        existing_doc = existing_upload
    else:
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()

    if existing_doc and existing_doc.id != getattr(locals().get("existing_upload"), "id", None):
        spool.close()
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate document detected. This PDF was previously uploaded as '{existing_doc.title}' (ID: {existing_doc.id})."
        )

    try:
        spool.seek(0)
        reader = PdfReader(spool)
        if reader.is_encrypted:
            raise PDFExtractionError("Password-protected PDFs are not supported.")
        if len(reader.pages) == 0:
            raise PDFExtractionError("PDF contains zero pages.")
    except PDFExtractionError:
        spool.close()
        raise HTTPException(status_code=400, detail="Password-protected PDFs are not supported.")
    except Exception as exc:
        spool.close()
        raise HTTPException(status_code=400, detail="Corrupted or invalid PDF structure.") from exc

    if existing_upload:
        new_doc = existing_upload
        new_doc.title = title.strip()
        new_doc.circular_number = circular_number.strip() if circular_number else None
        new_doc.regulator = regulator.strip()
        new_doc.publication_date = publication_date.strip() if publication_date else None
        new_doc.effective_date = effective_date.strip() if effective_date else None
        new_doc.category = category.strip()
        new_doc.description = description.strip() if description else None
    else:
        new_doc = Document(
            title=title.strip(),
            circular_number=circular_number.strip() if circular_number else None,
            regulator=regulator.strip(),
            publication_date=publication_date.strip() if publication_date else None,
            effective_date=effective_date.strip() if effective_date else None,
            category=category.strip(),
            description=description.strip() if description else None,
            file_path=None,
            file_hash=file_hash,
            file_size=size,
            status="pending_upload",
            page_count=0,
            created_by=current_user.id,
            storage_upload_id=resolved_upload_id,
            storage_status="pending_upload",
            processing_status="pending",
        )
        db.add(new_doc)
        db.flush()

    key = f"documents/{new_doc.id}/{resolved_upload_id}-{file_hash}.pdf"
    new_doc.file_hash = file_hash
    new_doc.file_size = size
    new_doc.storage_provider = settings.DOCUMENT_STORAGE_PROVIDER.lower()
    new_doc.storage_object_key = key
    new_doc.storage_status = "uploading"
    new_doc.processing_status = "pending"
    db.commit()

    provider = get_storage_provider()
    try:
        spool.seek(0)
        upload_result = await provider.upload(key, spool, "application/pdf", size)
        if upload_result.size != size or upload_result.sha256 != file_hash:
            new_doc.storage_status = "storage_failed"
            db.commit()
            raise HTTPException(status_code=400, detail="Stored PDF integrity verification failed.")

        new_doc.storage_status = "verifying"
        db.commit()
        stored = await provider.open(key)
        try:
            stored_hash = PDFExtractionService.calculate_file_hash(stored.stream)
            if stored.size != size or stored_hash != file_hash:
                raise StorageVerificationError("Stored PDF verification failed.")
        finally:
            stored.stream.close()

        new_doc.storage_status = "verified"
        new_doc.processing_status = "processing"
        db.commit()

        spool.seek(0)
        extraction_data = PDFExtractionService.extract_document(spool)
    except StorageVerificationError as exc:
        spool.close()
        new_doc.storage_status = "storage_failed"
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PDFExtractionError as exc:
        spool.close()
        new_doc.storage_status = "available"
        new_doc.processing_status = "processing_failed"
        new_doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(exc)}") from exc
    except HTTPException:
        spool.close()
        raise
    except Exception as exc:
        spool.close()
        new_doc.storage_status = "storage_failed"
        new_doc.processing_status = "processing_failed"
        db.commit()
        raise HTTPException(status_code=400, detail="Could not store or verify the uploaded PDF.") from exc

    if existing_upload:
        human_reviewed = any(
            obligation.review_status in ("approved", "corrected", "rejected")
            or bool(obligation.reviews)
            for obligation in new_doc.obligations
        )
        if human_reviewed:
            spool.close()
            raise HTTPException(
                status_code=409,
                detail="Extraction retry conflicts with existing human review decisions.",
            )
        for obligation in list(new_doc.obligations):
            db.delete(obligation)
        for evidence in list(new_doc.evidence_spans):
            db.delete(evidence)
        for page in list(new_doc.pages):
            db.delete(page)
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

    new_doc.status = extraction_data["status"]
    new_doc.page_count = extraction_data["page_count"]
    new_doc.storage_status = "available"
    new_doc.processing_status = (
        "requires_ocr" if extraction_data["status"] == "requires_ocr" else "completed"
    )
    new_doc.storage_migrated_at = None

    existing_audit = db.query(AuditLog).filter(
        AuditLog.action == "document_upload",
        AuditLog.resource_type == "document",
        AuditLog.resource_id == str(new_doc.id),
        AuditLog.user_id == current_user.id,
    ).first()
    if not existing_audit:
        db.add(AuditLog(
            user_id=current_user.id,
            action="document_upload",
            resource_type="document",
            resource_id=str(new_doc.id),
            details_json=json.dumps({
                "title": new_doc.title,
                "circular_number": new_doc.circular_number,
                "page_count": new_doc.page_count,
                "obligations_extracted": saved_obligations_count,
            }),
        ))

    try:
        db.commit()
        db.refresh(new_doc)
    except Exception:
        db.rollback()
        orphan_task = StorageCleanupTask(
            document_id=new_doc.id,
            storage_provider=new_doc.storage_provider or "local",
            storage_object_key=key,
            operation="delete",
            status="pending",
            attempts=0,
            last_error="Document and extraction finalization transaction failed.",
        )
        db.add(orphan_task)
        db.commit()
        spool.close()
        raise HTTPException(status_code=500, detail="Document processing could not be saved.")

    spool.close()

    return DocumentResponse(
        id=new_doc.id,
        title=new_doc.title,
        circular_number=new_doc.circular_number,
        regulator=new_doc.regulator,
        publication_date=new_doc.publication_date,
        effective_date=new_doc.effective_date,
        category=new_doc.category,
        description=new_doc.description,
        file_path=None,
        file_hash=new_doc.file_hash,
        file_size=new_doc.file_size,
        status=new_doc.status,
        page_count=new_doc.page_count,
        created_at=new_doc.created_at.isoformat(),
        created_by=new_doc.created_by,
        obligation_count=saved_obligations_count,
        storage_provider=new_doc.storage_provider,
        storage_status=new_doc.storage_status,
        processing_status=new_doc.processing_status,
        can_download=new_doc.storage_status in ("available", "legacy"),
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
        file_path=None,
        file_hash=doc.file_hash,
        file_size=doc.file_size,
        status=doc.status,
        page_count=doc.page_count,
        created_at=doc.created_at.isoformat(),
        created_by=doc.created_by,
        obligation_count=len(doc.obligations),
        storage_provider=doc.storage_provider,
        storage_status=doc.storage_status,
        processing_status=doc.processing_status,
        can_download=doc.storage_status in ("available", "legacy"),
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
    if doc.storage_status == "deleting":
        raise HTTPException(status_code=404, detail="Document is unavailable while it is being deleted.")

    if doc.storage_status == "legacy" or not doc.storage_object_key:
        if not doc.file_path or not os.path.isfile(doc.file_path):
            raise HTTPException(status_code=404, detail="Underlying PDF file not found.")
        stream = open(doc.file_path, "rb")
    else:
        try:
            provider = get_storage_provider()
            import asyncio
            provider_result = asyncio.run(provider.open(doc.storage_object_key))
            stream = provider_result.stream
        except StorageNotFoundError:
            raise HTTPException(status_code=404, detail="Stored PDF object not found.")
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Could not retrieve the stored PDF.") from exc

    def iterate_stream():
        try:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            stream.close()

    return StreamingResponse(
        iterate_stream(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ROIS_Document_{doc.id}.pdf"'},
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
    doc.storage_status = "deleting"
    cleanup = StorageCleanupTask(
        document_id=doc.id,
        storage_provider=doc.storage_provider or "local",
        storage_object_key=doc.storage_object_key or doc.file_path or "",
        operation="delete",
        status="pending",
        attempts=0,
    )
    db.add(cleanup)
    db.commit()

    provider = get_storage_provider()
    try:
        if doc.storage_object_key:
            import asyncio
            asyncio.run(provider.delete(doc.storage_object_key))
        elif doc.file_path and os.path.isfile(doc.file_path):
            os.unlink(doc.file_path)
        cleanup.status = "object_deleted"
        cleanup.object_deleted_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        cleanup.status = "failed"
        cleanup.attempts = (cleanup.attempts or 0) + 1
        cleanup.last_error = "Object deletion failed."
        cleanup.next_retry_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=502,
            detail="Document deletion was scheduled; object cleanup retry is required.",
        ) from exc

    try:
        db.delete(doc)
        db.commit()
        cleanup.database_deleted_at = datetime.now(timezone.utc)
        cleanup.status = "completed"
        cleanup.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        cleanup.status = "object_deleted"
        cleanup.attempts = (cleanup.attempts or 0) + 1
        cleanup.last_error = "Database document deletion failed."
        db.commit()
        raise HTTPException(
            status_code=500,
            detail="The object was deleted; document database cleanup will be retried.",
        ) from exc

    AuditService.log(
        db,
        action="document_delete",
        resource_type="document",
        resource_id=str(document_id),
        user_id=current_user.id,
        details={"deleted_title": doc_title}
    )

    return {"message": f"Document '{doc_title}' and associated extraction records deleted successfully."}

@router.post("/cleanup/{task_id}/reconcile")
def reconcile_storage_cleanup(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    task = db.query(StorageCleanupTask).filter(
        StorageCleanupTask.id == task_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Cleanup task not found.")
    if task.status == "completed":
        return {"message": "Cleanup task already completed.", "status": "completed"}

    if task.status != "object_deleted":
        try:
            if task.storage_provider != settings.DOCUMENT_STORAGE_PROVIDER:
                raise HTTPException(
                    status_code=409,
                    detail="Cleanup task provider does not match the active storage provider.",
                )
            if task.storage_object_key.startswith("documents/"):
                provider = get_storage_provider()
                import asyncio
                asyncio.run(provider.delete(task.storage_object_key))
            elif task.storage_provider == "local" and os.path.isfile(task.storage_object_key):
                os.unlink(task.storage_object_key)
            task.status = "object_deleted"
            task.object_deleted_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            task.status = "failed"
            task.attempts = (task.attempts or 0) + 1
            task.last_error = "Object deletion retry failed."
            task.next_retry_at = datetime.now(timezone.utc)
            db.commit()
            raise HTTPException(status_code=502, detail="Object cleanup retry failed.") from exc

    if task.document_id:
        doc = db.query(Document).filter(Document.id == task.document_id).first()
        if doc:
            try:
                db.delete(doc)
                db.commit()
            except Exception as exc:
                db.rollback()
                task.status = "object_deleted"
                task.attempts = (task.attempts or 0) + 1
                task.last_error = "Database cleanup retry failed."
                db.commit()
                raise HTTPException(status_code=500, detail="Database cleanup retry failed.") from exc

    task.database_deleted_at = datetime.now(timezone.utc)
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Cleanup reconciliation completed.", "status": "completed"}
