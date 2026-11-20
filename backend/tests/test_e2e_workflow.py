from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfgen import canvas


DEMO_NOTICE = "DEMONSTRATION DOCUMENT - NOT AN OFFICIAL IFSCA CIRCULAR"


def _create_demo_circular(amended: bool) -> bytes:
    content = BytesIO()
    pdf = canvas.Canvas(content)
    pdf.drawString(40, 760, DEMO_NOTICE)

    deadline = "15 days" if amended else "30 days"
    pdf.drawString(
        48,
        720,
        "All IFSC Banking Units (IBUs) shall establish an AML framework",
    )
    pdf.drawString(48, 704, f"within {deadline} of circular issuance.")
    pdf.drawString(
        48,
        676,
        "Every Registered Intermediary shall appoint a Compliance Officer.",
    )

    if amended:
        pdf.drawString(
            48,
            648,
            "All IFSC Banking Units (IBUs) shall implement an automated transaction monitoring",
        )
        pdf.drawString(48, 632, "system within 45 days of circular issuance.")

    pdf.save()
    return content.getvalue()


def _upload_demo_circular(client, headers, title, circular_number, amended):
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "title": f"[DEMONSTRATION ONLY] {title}",
            "circular_number": circular_number,
            "regulator": "ROIS Demo",
            "category": "Demonstration",
        },
        files={
            "file": (
                f"{circular_number}.pdf",
                _create_demo_circular(amended),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_full_regulatory_workflow_with_uploaded_demo_documents(api_client):
    client, headers = api_client

    base_document = _upload_demo_circular(
        client,
        headers,
        "Base AML requirements",
        "DEMO-BASE-001",
        amended=False,
    )
    target_document = _upload_demo_circular(
        client,
        headers,
        "Amended AML requirements",
        "DEMO-AMEND-002",
        amended=True,
    )

    assert base_document["status"] == "processed"
    assert target_document["status"] == "processed"
    assert base_document["obligation_count"] == 2
    assert target_document["obligation_count"] == 3

    base_obligations = client.get(
        "/api/v1/obligations/",
        headers=headers,
        params={"document_id": base_document["id"]},
    ).json()["items"]
    target_obligations = client.get(
        "/api/v1/obligations/",
        headers=headers,
        params={"document_id": target_document["id"]},
    ).json()["items"]

    source_evidence = client.get(
        f"/api/v1/evidence/{target_obligations[0]['id']}",
        headers=headers,
    )
    assert source_evidence.status_code == 200
    evidence_data = source_evidence.json()
    assert evidence_data["evidence_span"]["exact_text"] in evidence_data["source_page"]["extracted_text"]

    comparison_response = client.post(
        "/api/v1/comparisons/",
        headers=headers,
        json={
            "base_document_id": base_document["id"],
            "target_document_id": target_document["id"],
            "title": "Demonstration version comparison",
        },
    )
    assert comparison_response.status_code == 200
    comparison = comparison_response.json()
    change_types = {change["change_type"] for change in comparison["changes"]}
    assert {"new", "modified", "unchanged"}.issubset(change_types)
    assert all(not change["human_verified"] for change in comparison["changes"])

    modified_change = next(
        change for change in comparison["changes"]
        if change["change_type"] == "modified"
    )
    verified_change = client.put(
        f"/api/v1/comparisons/changes/{modified_change['id']}/verify",
        headers=headers,
        params={"verified_type": "modified"},
    )
    assert verified_change.status_code == 200
    assert verified_change.json()["human_verified"] is True

    first_obligation = target_obligations[0]
    review_response = client.put(
        f"/api/v1/obligations/{first_obligation['id']}/review",
        headers=headers,
        json={
            "action": "corrected",
            "required_action": "establish an AML framework (reviewed)",
            "comments": "Reviewed against the demonstration source passage.",
        },
    )
    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "corrected"

    mappings_response = client.get(
        "/api/v1/controls/mappings",
        headers=headers,
        params={"obligation_id": first_obligation["id"]},
    )
    assert mappings_response.status_code == 200
    mappings = mappings_response.json()
    assert mappings
    mapping_review = client.put(
        f"/api/v1/controls/mappings/{mappings[0]['id']}",
        headers=headers,
        json={"review_status": "approved"},
    )
    assert mapping_review.status_code == 200
    assert mapping_review.json()["review_status"] == "approved"

    report_response = client.post(
        "/api/v1/reports/generate",
        headers=headers,
        json={
            "document_id": target_document["id"],
            "comparison_id": comparison["id"],
            "title": "Demonstration impact report",
        },
    )
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["metrics"]["total_obligations"] == 3
    assert report["report_data"]["all_obligations"][0]["evidence"]["exact_text"]
    assert report["report_data"]["changes_breakdown"]

    pdf_response = client.get(
        f"/api/v1/reports/{report['id']}/download/pdf",
        headers=headers,
    )
    assert pdf_response.status_code == 200
    assert len(PdfReader(BytesIO(pdf_response.content)).pages) >= 1

    json_response = client.get(
        f"/api/v1/reports/{report['id']}/download",
        headers=headers,
    )
    assert json_response.status_code == 200
    assert json_response.json()["comparison_id"] == comparison["id"]

    audit_response = client.get("/api/v1/audit/", headers=headers)
    assert audit_response.status_code == 200
    audit_actions = {entry["action"] for entry in audit_response.json()}
    assert {
        "document_upload",
        "comparison_created",
        "obligation_corrected",
        "report_generated",
    }.issubset(audit_actions)
