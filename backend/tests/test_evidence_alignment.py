from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from app.core.seed_data import generate_sample_pdf_v1
from app.services.obligation_extractor import ObligationExtractor
from app.services.pdf_extractor import PDFExtractionService


def _create_test_pdf() -> bytes:
    content = BytesIO()
    pdf = canvas.Canvas(content)
    pdf.drawString(
        48,
        760,
        "DEMONSTRATION DOCUMENT - NOT AN OFFICIAL IFSCA CIRCULAR",
    )
    pdf.drawString(
        48,
        720,
        "All IFSC Banking Units (IBUs) shall establish an AML framework",
    )
    pdf.drawString(48, 704, "within 30 days of circular issuance.")
    pdf.save()
    return content.getvalue()


def test_generated_sample_is_marked_as_demonstration(tmp_path):
    pdf_path = tmp_path / "demo.pdf"
    generate_sample_pdf_v1(str(pdf_path))

    extracted = PDFExtractionService.extract_document(str(pdf_path))
    assert all(
        "DEMONSTRATION DOCUMENT - NOT AN OFFICIAL IFSCA CIRCULAR"
        in page["text"]
        for page in extracted["pages"]
    )


def test_extracted_obligation_evidence_matches_page_text(tmp_path):
    pdf_path = tmp_path / "circular.pdf"
    pdf_path.write_bytes(_create_test_pdf())
    extracted = PDFExtractionService.extract_document(str(pdf_path))
    page = extracted["pages"][0]
    obligations = ObligationExtractor.extract_from_pages(extracted["pages"])

    assert len(obligations) == 1
    obligation = obligations[0]
    assert obligation["source_text"] == page["text"][
        obligation["char_start"]:obligation["char_end"]
    ]
    assert obligation["source_text"] in page["text"]
    assert "shall establish" in obligation["obligation_text"]
    assert obligation["bounding_box"]


def test_document_upload_returns_resolvable_evidence_and_exports_reports(api_client):
    client, headers = api_client
    upload = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "title": "[DEMONSTRATION ONLY] Evidence alignment test",
            "regulator": "ROIS Demo",
        },
        files={"file": ("test.pdf", _create_test_pdf(), "application/pdf")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["id"]

    obligations = client.get(
        "/api/v1/obligations/",
        headers=headers,
        params={"document_id": document_id},
    )
    assert obligations.status_code == 200
    obligation = obligations.json()["items"][0]

    evidence = client.get(
        f"/api/v1/evidence/{obligation['id']}",
        headers=headers,
    )
    assert evidence.status_code == 200
    evidence_data = evidence.json()
    exact_text = evidence_data["evidence_span"]["exact_text"]
    page_text = evidence_data["source_page"]["extracted_text"]

    assert exact_text in page_text
    assert exact_text == page_text[
        evidence_data["evidence_span"]["char_start"]:
        evidence_data["evidence_span"]["char_end"]
    ]

    generated_report = client.post(
        "/api/v1/reports/generate",
        headers=headers,
        json={"document_id": document_id, "title": "Evidence test report"},
    )
    assert generated_report.status_code == 200
    report_id = generated_report.json()["id"]

    pdf_response = client.get(
        f"/api/v1/reports/{report_id}/download/pdf",
        headers=headers,
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    pdf_reader = PdfReader(BytesIO(pdf_response.content))
    assert len(pdf_reader.pages) == 1
    assert "Evidence test report" in pdf_reader.pages[0].extract_text()

    json_response = client.get(
        f"/api/v1/reports/{report_id}/download",
        headers=headers,
    )
    assert json_response.status_code == 200
    assert json_response.json()["all_obligations"][0]["evidence"]["exact_text"] == exact_text
