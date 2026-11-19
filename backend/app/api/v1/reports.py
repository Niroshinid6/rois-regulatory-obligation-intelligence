from io import BytesIO
import json
from xml.sax.saxutils import escape
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.document import Document
from app.models.obligation import Comparison
from app.models.report import ImpactReport
from app.schemas.report import ImpactReportCreate, ImpactReportResponse
from app.services.report_generator import ImpactReportGenerator
from app.services.audit_service import AuditService

router = APIRouter(prefix="/reports", tags=["Regulatory Impact Reports"])

@router.get("/", response_model=List[ImpactReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = db.query(ImpactReport).order_by(ImpactReport.created_at.desc()).all()
    results = []
    for r in reports:
        results.append(ImpactReportResponse(
            id=r.id,
            title=r.title,
            document_id=r.document_id,
            comparison_id=r.comparison_id,
            executive_summary=r.executive_summary,
            metrics=json.loads(r.metrics_json or "{}"),
            report_data=json.loads(r.report_data_json or "{}"),
            created_at=r.created_at.isoformat(),
            generated_by=r.generated_by
        ))
    return results

@router.post("/generate", response_model=ImpactReportResponse)
def generate_report(
    req: ImpactReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["compliance_officer", "admin", "management"]))
):
    if not req.document_id and not req.comparison_id:
        raise HTTPException(status_code=400, detail="Must provide either document_id or comparison_id to generate a report.")

    doc = None
    if req.document_id:
        doc = db.query(Document).filter(Document.id == req.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Target document not found.")

    comp = None
    if req.comparison_id:
        comp = db.query(Comparison).filter(Comparison.id == req.comparison_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Target comparison record not found.")
        if not doc:
            doc = comp.target_document

    # Build obligations payload
    obls_payload = []
    for o in doc.obligations:
        evidence = o.evidence_span
        obls_payload.append({
            "id": o.id,
            "obligation_code": o.obligation_code,
            "source_page": o.source_page,
            "obligation_text": o.obligation_text,
            "responsible_entity": o.responsible_entity,
            "required_action": o.required_action,
            "deadline": o.deadline,
            "review_status": o.review_status,
            "evidence": {
                "page": evidence.page_number,
                "exact_text": evidence.exact_text,
                "char_start": evidence.char_start,
                "char_end": evidence.char_end,
            } if evidence else None,
            "review_comments": [
                {
                    "action": review.action,
                    "reviewer": review.reviewer.full_name if review.reviewer else None,
                    "comments": review.comments,
                    "created_at": review.created_at.isoformat(),
                }
                for review in o.reviews
                if review.comments
            ],
        })

    controls_payload = []
    for o in doc.obligations:
        for c in o.controls:
            controls_payload.append({
                "category_name": c.control_category.name,
                "category_code": c.control_category.code,
                "rationale": c.rationale,
                "review_status": c.review_status,
                "mapping_method": c.mapping_method,
            })

    report_content = ImpactReportGenerator.generate_document_impact_report(
        document={
            "id": doc.id,
            "title": doc.title,
            "circular_number": doc.circular_number,
            "regulator": doc.regulator,
            "publication_date": doc.publication_date
        },
        obligations=obls_payload,
        control_mappings=controls_payload,
        generated_by_user=current_user.full_name
    )

    if comp:
        # Append comparison change breakdown into report_data
        report_content["comparison_id"] = comp.id
        report_content["comparison_title"] = comp.title
        report_content["changes_breakdown"] = [
            {
                "id": ch.id,
                "change_type": ch.change_type,
                "change_explanation": ch.change_explanation,
                "human_verified": ch.human_verified,
                "current_code": ch.current_obligation.obligation_code if ch.current_obligation else None,
                "previous_code": ch.previous_obligation.obligation_code if ch.previous_obligation else None
            }
            for ch in comp.changes
        ]

    new_report = ImpactReport(
        title=req.title or report_content["title"],
        document_id=doc.id,
        comparison_id=comp.id if comp else None,
        executive_summary=report_content["executive_summary"],
        metrics_json=json.dumps(report_content["metrics"]),
        report_data_json=json.dumps(report_content),
        generated_by=current_user.id
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    AuditService.log(
        db,
        action="report_generated",
        resource_type="impact_report",
        resource_id=str(new_report.id),
        user_id=current_user.id,
        details={"report_title": new_report.title}
    )

    return ImpactReportResponse(
        id=new_report.id,
        title=new_report.title,
        document_id=new_report.document_id,
        comparison_id=new_report.comparison_id,
        executive_summary=new_report.executive_summary,
        metrics=json.loads(new_report.metrics_json or "{}"),
        report_data=json.loads(new_report.report_data_json or "{}"),
        created_at=new_report.created_at.isoformat(),
        generated_by=new_report.generated_by
    )

@router.get("/{report_id}", response_model=ImpactReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    r = db.query(ImpactReport).filter(ImpactReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")

    return ImpactReportResponse(
        id=r.id,
        title=r.title,
        document_id=r.document_id,
        comparison_id=r.comparison_id,
        executive_summary=r.executive_summary,
        metrics=json.loads(r.metrics_json or "{}"),
        report_data=json.loads(r.report_data_json or "{}"),
        created_at=r.created_at.isoformat(),
        generated_by=r.generated_by
    )

@router.get("/{report_id}/download")
def download_report_json(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    r = db.query(ImpactReport).filter(ImpactReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found.")

    data = json.loads(r.report_data_json or "{}")
    formatted_json = json.dumps(data, indent=2)

    return Response(
        content=formatted_json,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=ROIS_Impact_Report_{r.id}.json"}
    )

@router.get("/{report_id}/download/pdf")
def download_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(ImpactReport).filter(ImpactReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    data = json.loads(report.report_data_json or "{}")
    styles = getSampleStyleSheet()
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=report.title,
    )
    story = [
        Paragraph(escape(report.title), styles["Title"]),
        Spacer(1, 5 * mm),
        Paragraph(escape(data.get("executive_summary") or "No executive summary is recorded."), styles["BodyText"]),
        Spacer(1, 4 * mm),
        Paragraph(
            escape(
                f"Authority: {data.get('regulator') or 'Not recorded'} | "
                f"Circular: {data.get('circular_number') or 'Not recorded'} | "
                f"Generated: {data.get('generated_at') or report.created_at.isoformat()}"
            ),
            styles["BodyText"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Report metrics", styles["Heading2"]),
    ]

    metrics = data.get("metrics") or {}
    metric_rows = [["Metric", "Value"]]
    metric_rows.extend(
        [[escape(str(key).replace("_", " ").title()), escape(str(value))]
         for key, value in metrics.items()]
    )
    story.append(Table(
        metric_rows,
        colWidths=[100 * mm, 55 * mm],
        repeatRows=1,
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]),
    ))

    obligations = data.get("all_obligations") or []
    story.extend([Spacer(1, 6 * mm), Paragraph("Obligations and evidence", styles["Heading2"])])
    if not obligations:
        story.append(Paragraph("No obligation records are included in this report snapshot.", styles["BodyText"]))

    for obligation in obligations:
        code = escape(str(obligation.get("obligation_code") or "Obligation"))
        status = escape(str(obligation.get("review_status") or "Not reviewed"))
        story.extend([
            Spacer(1, 3 * mm),
            Paragraph(            f"{code} - {status}", styles["Heading3"]),
        ])
        for label, key in (
            ("Obligation text", "obligation_text"),
            ("Required action", "required_action"),
            ("Responsible entity", "responsible_entity"),
            ("Deadline", "deadline"),
        ):
            value = obligation.get(key)
            if value:
                story.append(Paragraph(f"<b>{label}:</b> {escape(str(value))}", styles["BodyText"]))

        evidence = obligation.get("evidence")
        if evidence:
            story.append(Paragraph(
                f"<b>Evidence reference:</b> Page {escape(str(evidence.get('page')))}; "
                f"characters {escape(str(evidence.get('char_start')))}-{escape(str(evidence.get('char_end')))}",
                styles["BodyText"],
            ))
            if evidence.get("exact_text"):
                quote = escape(str(evidence["exact_text"])).replace("\n", "<br/>")
                story.append(Paragraph(f"<b>Source passage:</b> {quote}", styles["BodyText"]))
        else:
            story.append(Paragraph("<b>Evidence reference:</b> Not recorded in this report snapshot.", styles["BodyText"]))

        for review in obligation.get("review_comments") or []:
            if review.get("comments"):
                comment = escape(str(review["comments"])).replace("\n", "<br/>")
                reviewer = escape(str(review.get("reviewer") or "Reviewer not recorded"))
                story.append(Paragraph(f"<b>Reviewer comment ({reviewer}):</b> {comment}", styles["BodyText"]))

    changes = data.get("changes_breakdown") or []
    if changes:
        story.extend([Spacer(1, 6 * mm), Paragraph("Version changes", styles["Heading2"])])
        for change in changes:
            classification = escape(str(change.get("change_type") or "Unclassified"))
            explanation = escape(str(change.get("change_explanation") or ""))
            verification = "Human verified" if change.get("human_verified") else "Pending human verification"
            story.append(Paragraph(
                f"<b>{classification} - {verification}:</b> {explanation}",
                styles["BodyText"],
            ))

    notice = escape(str(data.get("legal_limitations_notice") or ""))
    if notice:
        story.extend([Spacer(1, 8 * mm), Paragraph(notice, styles["Italic"])])

    pdf.build(story)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ROIS_Impact_Report_{report.id}.pdf"},
    )
