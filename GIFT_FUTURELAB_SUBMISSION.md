# GIFT FutureLab Submission Material

## Project Overview

ROIS converts regulatory circulars into traceable compliance obligations.
Every extracted requirement is linked to a source PDF page and exact text span.
Human reviewers approve, reject, or correct machine extraction before it is
presented as verified.

## Problem Statement

Compliance teams must identify obligations across circulars, compare revisions,
map requirements to controls, and preserve evidence. Manual processes are slow,
error-prone, and difficult to audit.

## Proposed Solution

ROIS provides:

- PDF ingestion and text extraction
- Candidate obligation extraction
- Exact evidence anchoring
- One-to-one version comparison
- Control mapping recommendations
- Human review and audit records
- PDF and JSON impact reports

## Technology Stack

- React, TypeScript, Vite
- FastAPI, Pydantic, SQLAlchemy, Alembic
- SQLite for local development; PostgreSQL for production
- pdfplumber and optional Tesseract OCR
- ReportLab
- JWT/bcrypt authentication
- Vercel and Render deployment configuration

## Demonstration Workflow

1. Sign in with a confidential evaluation account.
2. Open the dashboard.
3. Upload a PDF explicitly marked as demonstration-only.
4. Inspect extracted obligations and source evidence.
5. Upload a newer synthetic version.
6. Review machine-classified changes.
7. Map obligations to control categories.
8. Approve, reject, or correct a candidate.
9. Generate an impact report.
10. Export PDF or JSON.
11. Inspect audit activity.

No synthetic obligation or quotation may be treated as authentic IFSCA guidance.

## 2–4 Minute Demonstration Script

1. Introduce ROIS and the compliance traceability problem.
2. Log in and show the dashboard's database-derived metrics.
3. Upload the demonstration PDF.
4. Open one obligation and navigate to the exact source text and page.
5. Explain that OCR and extraction remain candidate processes requiring review.
6. Upload a second demonstration version and show the comparison.
7. Explain modified/new/retired/unchanged classifications and human verification.
8. Select a control mapping and explain that it is only a recommendation.
9. Approve or correct the obligation.
10. Generate and export PDF/JSON reports.
11. Finish on the audit ledger and governance limitation notice.

## Submission Checklist

- Live application URL: NOT AVAILABLE — deployment pending approval
- GitHub repository URL: NOT INVENTED
- Demonstration video URL: NOT AVAILABLE
- Supporting documentation URL: NOT AVAILABLE
- README: available in the repository
- Architecture specification: available in `PROJECT_SPEC.md`
- Final validation status: available in `ROIS_IMPLEMENTATION_STATUS.md`

## Known Limitations

- OCR text execution is not runtime-verified on this host.
- PostgreSQL and Docker runtime validation are not tested.
- Public deployment has not been executed.
- Older evidence records may require reprocessing.
- Extracted obligations require human verification.
