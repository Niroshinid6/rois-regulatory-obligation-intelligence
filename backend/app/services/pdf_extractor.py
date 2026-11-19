import hashlib
import os
import json
from typing import Dict, Any, List, Optional
import pdfplumber
from typing import Tuple

OCR_AVAILABLE = False
try:
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    pytesseract = None

class PDFExtractionError(Exception):
    pass

class PDFExtractionService:
    @staticmethod
    def _ocr_page(page) -> Tuple[str, Optional[float], List[Dict[str, Any]]]:
        if not OCR_AVAILABLE:
            return "", None, []
        try:
            rendered = page.to_image(resolution=300)
            image = rendered.original
            data = pytesseract.image_to_data(
                image,
                config="--oem 1 --psm 6",
                output_type=pytesseract.Output.DICT,
            )
            pieces = []
            confidences = []
            for index, value in enumerate(data.get("text", [])):
                text = (value or "").strip()
                try:
                    confidence = float(data["conf"][index])
                except (KeyError, TypeError, ValueError):
                    confidence = -1.0
                if text:
                    pieces.append(text)
                    if confidence >= 0:
                        confidences.append(confidence)
            ocr_text = " ".join(pieces)
            average_confidence = (
                sum(confidences) / len(confidences) if confidences else None
            )
            return ocr_text, average_confidence, []
        except Exception:
            return "", None, []

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def extract_document(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise PDFExtractionError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise PDFExtractionError("PDF file is completely empty (0 bytes)")

        file_hash = cls.calculate_file_hash(file_path)

        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                if page_count == 0:
                    raise PDFExtractionError("PDF contains zero pages")

                pages_data: List[Dict[str, Any]] = []
                total_chars = 0
                total_words = 0
                has_any_text = False

                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    text = page.extract_text() or ""
                    clean_text = text.strip()

                    words = page.extract_words() or []
                    word_boxes = []
                    extraction_method = "pdf_text"
                    ocr_confidence = None
                    requires_human_review = False
                    for w in words:
                        word_boxes.append({
                            "text": w.get("text", ""),
                            "x0": round(float(w.get("x0", 0)), 2),
                            "top": round(float(w.get("top", 0)), 2),
                            "x1": round(float(w.get("x1", 0)), 2),
                            "bottom": round(float(w.get("bottom", 0)), 2),
                        })

                    char_count = len(clean_text)
                    word_count = len(words)

                    if char_count <= 20:
                        ocr_text, ocr_confidence, ocr_boxes = cls._ocr_page(page)
                        if ocr_text.strip():
                            text = ocr_text
                            clean_text = text.strip()
                            char_count = len(clean_text)
                            word_count = len(ocr_text.split())
                            word_boxes = ocr_boxes
                            extraction_method = "ocr"
                            requires_human_review = ocr_confidence is None or ocr_confidence < 60.0
                        else:
                            requires_human_review = True

                    total_chars += char_count
                    total_words += word_count

                    is_selectable = char_count > 20

                    if is_selectable:
                        has_any_text = True

                    # Preserve line boundaries while recording offsets into the stored page text.
                    raw_paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
                    layout_blocks = []
                    curr_char_idx = 0
                    for p in raw_paragraphs:
                        start_pos = text.find(p, curr_char_idx)
                        if start_pos == -1:
                            start_pos = curr_char_idx
                        end_pos = start_pos + len(p)
                        curr_char_idx = end_pos
                        layout_blocks.append({
                            "text": p,
                            "char_start": start_pos,
                            "char_end": end_pos
                        })

                    pages_data.append({
                        "page_number": page_num,
                        "text": text,
                        "char_count": char_count,
                        "word_count": word_count,
                        "has_selectable_text": is_selectable,
                        "bounding_boxes": word_boxes,
                        "layout_blocks": layout_blocks,
                        "extraction_method": extraction_method,
                        "ocr_confidence": ocr_confidence,
                        "requires_human_review": requires_human_review
                    })

                status = "processed"
                if not has_any_text:
                    status = "requires_ocr"

                return {
                    "file_hash": file_hash,
                    "file_size": file_size,
                    "page_count": page_count,
                    "status": status,
                    "has_selectable_text": has_any_text,
                    "total_chars": total_chars,
                    "total_words": total_words,
                    "pages": pages_data
                }

        except Exception as e:
            if isinstance(e, PDFExtractionError):
                raise
            raise PDFExtractionError(f"Failed to parse PDF document: {str(e)}")
