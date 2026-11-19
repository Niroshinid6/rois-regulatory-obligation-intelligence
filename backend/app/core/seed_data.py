import os
import json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from app.core.database import engine, Base, SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.control import ControlCategory, ObligationControl
from app.models.document import Document, DocumentVersion, DocumentPage, EvidenceSpan
from app.models.obligation import Obligation, Comparison, ObligationChange
from app.models.review import ReviewRecord
from app.models.report import ImpactReport
from app.models.audit import AuditLog
from app.services.pdf_extractor import PDFExtractionService
from app.services.obligation_extractor import ObligationExtractor
from app.services.version_comparator import VersionComparator
from app.services.control_mapper import ControlMapper
from app.services.report_generator import ImpactReportGenerator
from app.services.audit_service import AuditService

def draw_demo_notice(c, width, height):
    c.saveState()
    c.setFillColor(HexColor("#b91c1c"))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(
        width / 2,
        height - 24,
        "DEMONSTRATION DOCUMENT - NOT AN OFFICIAL IFSCA CIRCULAR",
    )
    c.restoreState()

def generate_sample_pdf_v1(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Page 1
    draw_demo_notice(c, width, height)
    # Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(54, height - 54, "INTERNATIONAL FINANCIAL SERVICES CENTRES AUTHORITY")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#0d9488"))
    c.drawString(54, height - 70, "GIFT CITY, GANDHINAGAR, GUJARAT - 382355")
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.line(54, height - 76, width - 54, height - 76)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(54, height - 95, "Ref: IFSCA/2024-25/GN/CIR-001")
    c.drawString(width - 160, height - 95, "Date: 15th May 2024")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(54, height - 120, "CIRCULAR: Anti Money Laundering and Counter-Terrorist Financing Guidelines, 2024")

    c.setFont("Helvetica", 9)
    c.drawString(54, height - 145, "To: All IFSC Banking Units (IBUs), Registered Intermediaries, and Finance Companies in GIFT IFSC.")

    # Clauses
    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 175, "1. Mandatory AML Framework Implementation")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 192, "All IFSC Banking Units (IBUs) shall establish a comprehensive risk-based Anti Money Laundering (AML)")
    c.drawString(54, height - 206, "framework approved by the Board of Directors within 30 days of circular issuance.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 235, "2. Appointment of Compliance and Principal Officers")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 252, "Every Registered Intermediary must appoint a designated Compliance Officer and a Principal Officer,")
    c.drawString(54, height - 266, "who shall report directly to the Board of Directors.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 295, "3. Beneficial Ownership Due Diligence")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 312, "Finance Companies shall verify and record the identity of all beneficial owners holding more than")
    c.drawString(54, height - 326, "ten percent (10%) equity prior to commencement of operations.")

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#64748b"))
    c.drawString(width / 2 - 20, 36, "Page 1 of 2")
    c.showPage()

    # Page 2
    draw_demo_notice(c, width, height)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(54, height - 54, "IFSCA/2024-25/GN/CIR-001 (Continued)")
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.line(54, height - 60, width - 54, height - 60)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 85, "4. Quarterly Regulatory Reporting")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 102, "All Regulated Entities (REs) shall submit the quarterly AML compliance return to the Authority")
    c.drawString(54, height - 116, "within 15 days of the end of each quarter.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 145, "5. Record Retention Mandate")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 162, "Every IBU must maintain records of all customer due diligence documents and transaction logs for")
    c.drawString(54, height - 176, "a minimum period of 10 years, save as provided by statutory court directives.")

    # Sign-off
    c.setFont("Helvetica-Bold", 9)
    c.drawString(54, height - 230, "Sd/-")
    c.drawString(54, height - 245, "Chief General Manager")
    c.drawString(54, height - 258, "International Financial Services Centres Authority")

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#64748b"))
    c.drawString(width / 2 - 20, 36, "Page 2 of 2")
    c.showPage()
    c.save()

def generate_sample_pdf_v2(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Page 1
    draw_demo_notice(c, width, height)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(54, height - 54, "INTERNATIONAL FINANCIAL SERVICES CENTRES AUTHORITY")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#0d9488"))
    c.drawString(54, height - 70, "GIFT CITY, GANDHINAGAR, GUJARAT - 382355")
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.line(54, height - 76, width - 54, height - 76)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(54, height - 95, "Ref: IFSCA/2024-25/GN/CIR-002")
    c.drawString(width - 160, height - 95, "Date: 20th August 2024")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(54, height - 120, "CIRCULAR: Anti Money Laundering and Counter-Terrorist Financing (Amendment) Guidelines, 2024")

    c.setFont("Helvetica", 9)
    c.drawString(54, height - 145, "To: All IFSC Banking Units (IBUs), Fund Management Entities (FMEs), and Registered Intermediaries.")

    # Clauses
    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 175, "1. Accelerated AML Framework Implementation")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 192, "All IFSC Banking Units (IBUs) shall establish a comprehensive risk-based Anti Money Laundering (AML)")
    c.drawString(54, height - 206, "framework approved by the Board of Directors within 15 days of circular issuance.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 235, "2. Expanded Governance Appointment Scope")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 252, "Every Registered Intermediary and Fund Management Entity (FME) must appoint a designated Compliance")
    c.drawString(54, height - 266, "Officer and a Principal Officer, who shall report directly to the Board of Directors.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 295, "3. Automated Monitoring System Mandate (NEW)")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 312, "All IFSC Banking Units (IBUs) and Fund Management Entities (FMEs) shall implement automated suspicious")
    c.drawString(54, height - 326, "transaction monitoring systems capable of real-time alert generation within 45 days.")

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#64748b"))
    c.drawString(width / 2 - 20, 36, "Page 1 of 2")
    c.showPage()

    # Page 2
    draw_demo_notice(c, width, height)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(54, height - 54, "IFSCA/2024-25/GN/CIR-002 (Continued)")
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.line(54, height - 60, width - 54, height - 60)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 85, "4. Quarterly Regulatory Reporting")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 102, "All Regulated Entities (REs) shall submit the quarterly AML compliance return to the Authority")
    c.drawString(54, height - 116, "within 15 days of the end of each quarter.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(54, height - 145, "5. Record Retention Mandate")
    c.setFont("Helvetica", 9)
    c.drawString(54, height - 162, "Every IBU must maintain records of all customer due diligence documents and transaction logs for")
    c.drawString(54, height - 176, "a minimum period of 10 years, save as provided by statutory court directives.")

    # Sign-off
    c.setFont("Helvetica-Bold", 9)
    c.drawString(54, height - 230, "Sd/-")
    c.drawString(54, height - 245, "Chief General Manager")
    c.drawString(54, height - 258, "International Financial Services Centres Authority")

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#64748b"))
    c.drawString(width / 2 - 20, 36, "Page 2 of 2")
    c.showPage()
    c.save()

def init_and_seed_database():
    if settings.ROIS_ENV.lower() == "production":
        raise RuntimeError("Demo seeding is disabled in production.")
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Roles
        roles_data = [
            ("admin", "System Administrator with full access to settings, user management, and audit logs", '["*"]'),
            ("compliance_officer", "Compliance Officer with rights to upload, process, compare circulars and generate reports", '["documents:read", "documents:write", "obligations:read", "reports:write", "comparisons:write"]'),
            ("reviewer", "Regulatory Reviewer with rights to inspect evidence, approve, correct, or reject obligations", '["documents:read", "obligations:read", "obligations:review", "controls:review"]'),
            ("management", "Executive Management and Internal Audit with view-only access to dashboards, reports, and change summaries", '["documents:read", "obligations:read", "reports:read", "audit:read"]')
        ]
        for name, desc, perms in roles_data:
            existing_role = db.query(Role).filter(Role.name == name).first()
            if not existing_role:
                db.add(Role(name=name, description=desc, permissions_json=perms))
        db.commit()

        # 2. Seed Users
        demo_passwords = {
            "admin": settings.ROIS_DEMO_ADMIN_PASSWORD,
            "compliance_officer": settings.ROIS_DEMO_COMPLIANCE_PASSWORD,
            "reviewer": settings.ROIS_DEMO_REVIEWER_PASSWORD,
            "management": settings.ROIS_DEMO_MANAGEMENT_PASSWORD,
        }
        if any(
            not password or len(password) < 12 or password.lower().startswith("replace-")
            for password in demo_passwords.values()
        ):
            raise RuntimeError(
                "Demo seeding requires unique ROIS_DEMO_*_PASSWORD environment variables "
                "of at least 12 characters."
            )
        users_data = [
            ("admin@rois.internal", demo_passwords["admin"], "Ananya Sharma (System Administrator)", "admin"),
            ("compliance@rois.internal", demo_passwords["compliance_officer"], "Vikramaditya Mehta (Lead Compliance Officer)", "compliance_officer"),
            ("reviewer@rois.internal", demo_passwords["reviewer"], "Pooja Singhania (Senior Regulatory Reviewer)", "reviewer"),
            ("management@rois.internal", demo_passwords["management"], "Director of Risk & Audit", "management")
        ]
        user_objs = {}
        for email, pwd, name, role in users_data:
            existing_user = db.query(User).filter(User.email == email).first()
            if not existing_user:
                u = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=role,
                    is_active=True
                )
                db.add(u)
                db.flush()
                user_objs[role] = u
            else:
                user_objs[role] = existing_user
        db.commit()

        # 3. Seed Control Taxonomy
        control_tax = [
            ("CDD-01", "Customer Due Diligence & AML/CFT", "Customer identification, beneficial ownership verification, PEP screening, and ongoing transaction monitoring."),
            ("REP-01", "Regulatory Reporting & Disclosures", "Mandatory periodic filings, incident intimacy, and statutory compliance returns to IFSCA."),
            ("GOV-01", "Corporate Governance & Oversight", "Board oversight, appointment of Key Managerial Personnel (Compliance Officer, Principal Officer), and governance charters."),
            ("RISK-01", "Risk Management & Internal Controls", "Comprehensive risk assessment frameworks, risk-based classification, and independent internal audit coverage."),
            ("REC-01", "Record Keeping & Audit Trails", "Maintenance and preservation of client records, correspondence, and transaction audit trails for statutory periods."),
            ("DATA-01", "Data Protection & Information Security", "Cyber resilience, customer data encryption, vulnerability assessments, and cybersecurity incident reporting."),
            ("OPS-01", "Operational Compliance & Outsourcing", "Business continuity planning, vendor due diligence, and regulatory conditions for critical outsourcing arrangements.")
        ]
        control_objs = []
        for code, name, desc in control_tax:
            existing_cat = db.query(ControlCategory).filter(ControlCategory.code == code).first()
            if not existing_cat:
                cat = ControlCategory(code=code, name=name, description=desc, is_active=True)
                db.add(cat)
                db.flush()
                control_objs.append(cat)
            else:
                control_objs.append(existing_cat)
        db.commit()

        # 4. Generate clearly marked demonstration documents if not present
        pdf_dir = os.path.abspath("data/sample_documents")
        pdf_v1_path = os.path.join(pdf_dir, "IFSCA_Circular_AML_CFT_2024.pdf")
        pdf_v2_path = os.path.join(pdf_dir, "IFSCA_Circular_AML_CFT_Amendment_2024.pdf")

        if not os.path.exists(pdf_v1_path):
            generate_sample_pdf_v1(pdf_v1_path)
            print(f"Generated demonstration PDF (not official): {pdf_v1_path}")

        if not os.path.exists(pdf_v2_path):
            generate_sample_pdf_v2(pdf_v2_path)
            print(f"Generated demonstration PDF (not official): {pdf_v2_path}")

        # 5. Process Circular 1 (Base Document)
        doc1 = db.query(Document).filter(Document.circular_number == "IFSCA/2024-25/GN/CIR-001").first()
        if not doc1:
            extraction_v1 = PDFExtractionService.extract_document(pdf_v1_path)
            admin_user = user_objs.get("admin")
            admin_id = admin_user.id if admin_user else 1

            doc1 = Document(
                title="[DEMONSTRATION ONLY] IFSCA AML/CFT Guidelines, 2024",
                circular_number="IFSCA/2024-25/GN/CIR-001",
                regulator="IFSCA",
                publication_date="2024-05-15",
                effective_date="2024-06-01",
                category="Circular",
                description="Synthetic demonstration content. NOT an official IFSCA circular; use uploaded official publications for regulatory analysis.",
                file_path=pdf_v1_path,
                file_hash=extraction_v1["file_hash"],
                file_size=extraction_v1["file_size"],
                status="processed",
                page_count=extraction_v1["page_count"],
                created_by=admin_id
            )
            db.add(doc1)
            db.flush()

            # Store Document Pages
            for p in extraction_v1["pages"]:
                db.add(DocumentPage(
                    document_id=doc1.id,
                    page_number=p["page_number"],
                    extracted_text=p["text"],
                    char_count=p["char_count"],
                    word_count=p["word_count"],
                    has_selectable_text=p["has_selectable_text"],
                    bounding_boxes_json=json.dumps(p["bounding_boxes"]),
                    layout_blocks_json=json.dumps(p["layout_blocks"])
                ))
            db.flush()

            # Extract Obligations & Evidence Spans
            extracted_obls_v1 = ObligationExtractor.extract_from_pages(extraction_v1["pages"], doc1.circular_number)
            saved_obls_v1 = []

            for raw_o in extracted_obls_v1:
                # Create Evidence Span
                span = EvidenceSpan(
                    document_id=doc1.id,
                    page_number=raw_o["source_page"],
                    exact_text=raw_o["source_text"],
                    char_start=raw_o["char_start"],
                    char_end=raw_o["char_end"],
                    bounding_box_json=json.dumps(raw_o["bounding_box"]),
                    confidence=raw_o["confidence_score"]
                )
                db.add(span)
                db.flush()

                # Create Obligation
                obl = Obligation(
                    obligation_code=raw_o["obligation_code"],
                    document_id=doc1.id,
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
                saved_obls_v1.append(obl)

                # Suggest and map controls
                ctrl_suggestions = ControlMapper.suggest_controls_for_obligation(
                    obl.obligation_text,
                    [{"id": c.id, "code": c.code, "name": c.name} for c in control_objs]
                )
                for cs in ctrl_suggestions:
                    db.add(ObligationControl(
                        obligation_id=obl.id,
                        control_category_id=cs["control_category_id"],
                        rationale=cs["rationale"],
                        mapping_method="nlp_suggested",
                        review_status="approved" if obl.review_status == "approved" else "suggested"
                    ))

            db.commit()
            print(f"Processed circular v1: {doc1.id} with {len(saved_obls_v1)} obligations.")

        # 6. Process Circular 2 (Target Amended Document)
        doc2 = db.query(Document).filter(Document.circular_number == "IFSCA/2024-25/GN/CIR-002").first()
        if not doc2:
            extraction_v2 = PDFExtractionService.extract_document(pdf_v2_path)
            admin_user = user_objs.get("admin")
            admin_id = admin_user.id if admin_user else 1

            doc2 = Document(
                title="[DEMONSTRATION ONLY] IFSCA AML/CFT Guidelines Amendment, 2024",
                circular_number="IFSCA/2024-25/GN/CIR-002",
                regulator="IFSCA",
                publication_date="2024-08-20",
                effective_date="2024-09-01",
                category="Circular",
                description="Synthetic demonstration content. NOT an official IFSCA circular; use uploaded official publications for regulatory analysis.",
                file_path=pdf_v2_path,
                file_hash=extraction_v2["file_hash"],
                file_size=extraction_v2["file_size"],
                status="processed",
                page_count=extraction_v2["page_count"],
                created_by=admin_id
            )
            db.add(doc2)
            db.flush()

            # Version Link
            db.add(DocumentVersion(
                document_id=doc2.id,
                version_number="2.0",
                predecessor_document_id=doc1.id,
                change_summary="Accelerated AML framework implementation from 30 to 15 days; added automated real-time transaction monitoring requirement."
            ))

            for p in extraction_v2["pages"]:
                db.add(DocumentPage(
                    document_id=doc2.id,
                    page_number=p["page_number"],
                    extracted_text=p["text"],
                    char_count=p["char_count"],
                    word_count=p["word_count"],
                    has_selectable_text=p["has_selectable_text"],
                    bounding_boxes_json=json.dumps(p["bounding_boxes"]),
                    layout_blocks_json=json.dumps(p["layout_blocks"])
                ))
            db.flush()

            extracted_obls_v2 = ObligationExtractor.extract_from_pages(extraction_v2["pages"], doc2.circular_number)
            saved_obls_v2 = []

            for raw_o in extracted_obls_v2:
                span = EvidenceSpan(
                    document_id=doc2.id,
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
                    document_id=doc2.id,
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
                    review_status="approved",
                    extraction_method=raw_o["extraction_method"]
                )
                db.add(obl)
                db.flush()
                saved_obls_v2.append(obl)

                ctrl_suggestions = ControlMapper.suggest_controls_for_obligation(
                    obl.obligation_text,
                    [{"id": c.id, "code": c.code, "name": c.name} for c in control_objs]
                )
                for cs in ctrl_suggestions:
                    db.add(ObligationControl(
                        obligation_id=obl.id,
                        control_category_id=cs["control_category_id"],
                        rationale=cs["rationale"],
                        mapping_method="nlp_suggested",
                        review_status="approved"
                    ))

            db.commit()
            print(f"Processed circular v2: {doc2.id} with {len(saved_obls_v2)} obligations.")

        # 7. Create Regulatory Version Comparison between v1 and v2
        existing_comp = db.query(Comparison).filter(
            Comparison.base_document_id == doc1.id,
            Comparison.target_document_id == doc2.id
        ).first()

        if not existing_comp:
            comp = Comparison(
                title=f"Regulatory Delta: {doc1.circular_number} vs {doc2.circular_number}",
                base_document_id=doc1.id,
                target_document_id=doc2.id,
                created_by=user_objs.get("compliance_officer", user_objs.get("admin")).id,
                status="completed"
            )
            db.add(comp)
            db.flush()

            base_obls_raw = [{"id": o.id, "obligation_text": o.obligation_text, "deadline": o.deadline, "responsible_entity": o.responsible_entity, "source_page": o.source_page} for o in doc1.obligations]
            target_obls_raw = [{"id": o.id, "obligation_text": o.obligation_text, "deadline": o.deadline, "responsible_entity": o.responsible_entity, "source_page": o.source_page} for o in doc2.obligations]

            diff_results = VersionComparator.compare_documents(base_obls_raw, target_obls_raw)

            for d in diff_results:
                db.add(ObligationChange(
                    comparison_id=comp.id,
                    previous_obligation_id=d["previous_obligation_id"],
                    current_obligation_id=d["current_obligation_id"],
                    change_type=d["change_type"],
                    change_explanation=d["change_explanation"],
                    diff_details_json=json.dumps(d["diff_details"]),
                    human_verified=d["human_verified"]
                ))
            db.commit()
            print(f"Created Version Comparison: {comp.id} with {len(diff_results)} change items.")

        # 8. Create Demonstration Regulatory Impact Report
        existing_report = db.query(ImpactReport).filter(ImpactReport.document_id == doc2.id).first()
        if not existing_report:
            doc2_obls_data = []
            for o in doc2.obligations:
                doc2_obls_data.append({
                    "id": o.id,
                    "obligation_code": o.obligation_code,
                    "source_page": o.source_page,
                    "obligation_text": o.obligation_text,
                    "responsible_entity": o.responsible_entity,
                    "required_action": o.required_action,
                    "deadline": o.deadline,
                    "review_status": o.review_status
                })

            controls_data = []
            for o in doc2.obligations:
                for c in o.controls:
                    controls_data.append({
                        "category_name": c.control_category.name,
                        "category_code": c.control_category.code
                    })

            rep_data = ImpactReportGenerator.generate_document_impact_report(
                document={
                    "id": doc2.id,
                    "title": doc2.title,
                    "circular_number": doc2.circular_number,
                    "regulator": doc2.regulator,
                    "publication_date": doc2.publication_date
                },
                obligations=doc2_obls_data,
                control_mappings=controls_data,
                generated_by_user="Vikramaditya Mehta (Lead Compliance Officer)"
            )

            db.add(ImpactReport(
                title=rep_data["title"],
                document_id=doc2.id,
                executive_summary=rep_data["executive_summary"],
                metrics_json=json.dumps(rep_data["metrics"]),
                report_data_json=json.dumps(rep_data),
                generated_by=user_objs.get("compliance_officer", user_objs.get("admin")).id
            ))
            db.commit()
            print("Generated Demonstration Impact Report.")

        # 9. Initial Audit Logs
        AuditService.log(
            db,
            action="system_init",
            resource_type="system",
            resource_id="0",
            user_id=user_objs.get("admin").id,
            details={"event": "ROIS system initialized with IFSCA demonstration dataset", "status": "active"}
        )

        print("Database initialized and seeded successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    init_and_seed_database()
