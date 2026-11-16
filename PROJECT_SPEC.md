# ROIS — Regulatory Obligation Intelligence System
## Specification & Architecture Document (GIFT FutureLab Evaluation)

### 1. Product Identity & Purpose
- **Product Name:** ROIS — Regulatory Obligation Intelligence System
- **Tagline:** Every compliance obligation, traced to the exact sentence that created it.
- **Domain:** Regulatory Technology (RegTech), AI and intelligent financial systems.
- **Initial Scope:** International Financial Services Centres Authority (IFSCA).
- **Target Audience:** Compliance Officers, Legal and Regulatory Teams, Risk and Control Professionals, Internal Audit Teams, Executive Management.
- **Strict Boundary (What ROIS Is NOT):**
  - NOT a generic AI chatbot.
  - NOT a simple PDF summarizer.
  - NOT a general-purpose document management system.
  - NOT an autonomous legal-advice platform.
  - NOT a generic business analytics dashboard.

---

### 2. Core Product Principles
1. **Evidence First:** Every extracted obligation is strictly linked to a source evidence record and passage.
2. **Traceability:** Users can navigate to and visually inspect the exact source text on the original PDF page.
3. **Explainability:** Transparent rule/linguistic reasoning for why text was extracted as a mandatory obligation.
4. **Human Oversight:** AI produces structured candidate obligations; humans review, approve, correct, or reject.
5. **Auditability:** Complete immutable history of machine extractions and subsequent reviewer actions.
6. **Accuracy over Appearance:** Never fabricate regulatory citations, circular numbers, deadlines, or source locations.
7. **Transparency:** Clear distinction between extracted facts, inferred fields, and reviewer-confirmed decisions.
8. **Reliability:** Every button, filter, viewer, and workflow is fully functional.
9. **Security:** Secure RBAC, safe file handling, environment secrets management.
10. **Maintainability:** Modular architecture, clean TypeScript/Python codebases, comprehensive documentation.

---

### 3. Architecture & Monorepo Structure

```
ROIS/
  frontend/                  # React 18, Vite, TypeScript, Tailwind CSS, Lucide icons, React Router
    src/
      components/            # UI components (Shell, Tables, Badges, Modals, EvidenceViewer)
      pages/                 # 14 distinct functional views
      layouts/               # App layout with Sidebar, Header, Breadcrumbs
      services/              # API client and service endpoints
      hooks/                 # Custom React hooks
      types/                 # Comprehensive TypeScript interfaces
      utils/                 # Formatting, text matching, helper utilities
      assets/
    public/
    package.json
    tsconfig.json
    vite.config.ts
    tailwind.config.js
    postcss.config.js
  backend/                   # FastAPI, SQLAlchemy, Alembic, Pydantic, pdfplumber, spaCy
    app/
      api/v1/                # REST endpoints (auth, docs, obligations, comparison, controls, reports, audit)
      core/                  # Config, database session, security, dependencies
      models/                # SQLAlchemy relational ORM models
      schemas/               # Pydantic request/response schemas
      services/              # Document processor, extraction engine, comparison, report generator
      ml/                    # Rule-based NLP + Legal linguistic classification models
      utils/                 # PDF utilities, text span finders, hashing
      main.py                # FastAPI entry point
    tests/                   # Pytest test suites (endpoints, extraction, comparison, auth)
    requirements.txt
  data/
    sample_documents/        # Authentic IFSCA regulatory PDFs & sample circulars
    annotations/             # Demonstration & ground truth annotations
  research/
    methodology/             # Scientific RegTech extraction & alignment methodology
    evaluation/              # Precision/recall and extraction benchmark artifacts
  docker-compose.yml         # Containerized local/staging setup
  PROJECT_SPEC.md            # Master specification
  README.md                  # Comprehensive setup and run documentation
  .gitignore
  .env.example
```

---

### 4. Database Schema Design (PostgreSQL / SQLAlchemy)

The database schema supports end-to-end evidence tracking:
- `users`: ID, email, hashed_password, full_name, role (`admin`, `compliance_officer`, `reviewer`, `management`), is_active, created_at.
- `roles`: Role definitions and permission sets.
- `documents`: ID, title, circular_number, regulator (`IFSCA`), publication_date, category, description, file_path, file_hash, file_size, status (`uploaded`, `queued`, `processing`, `processed`, `requires_ocr`, `failed`, `requires_review`), page_count, created_by, created_at, updated_at.
- `document_versions`: Version tracking, predecessor links, version metadata.
- `document_pages`: ID, document_id, page_number, extracted_text, char_count, word_count, has_selectable_text, bounding_boxes_json.
- `evidence_spans`: ID, document_id, page_number, exact_text, char_start, char_end, bounding_box_json, confidence, created_at.
- `obligations`: ID, obligation_id (human readable formatted code), document_id, evidence_span_id, obligation_text, responsible_entity, required_action, deadline, conditions_json, exceptions_json, confidence_score, evidence_status (`unverified`, `anchored`, `mismatched`), review_status (`pending`, `approved`, `corrected`, `rejected`), created_at, updated_at.
- `obligation_attributes`: Granular attribute audit entries (deadline type, penalty, frequency).
- `obligation_changes`: Comparison results between versions (`new`, `modified`, `retired`, `unchanged`), change_basis_explanation, previous_obligation_id, current_obligation_id, human_verified.
- `control_categories`: Configurable taxonomy (e.g. Governance & Oversight, Risk Management, Reporting & Disclosures, Customer Due Diligence, Data Protection, Record Keeping, Operational Compliance).
- `obligation_controls`: Many-to-many relationship mapping obligations to control categories with rationale, mapping_method (`nlp_suggested`, `reviewer_assigned`), reviewer_status.
- `review_records`: Full audit trail of reviewer decisions, original vs corrected values, reviewer_id, comments, timestamp.
- `impact_reports`: Generated compliance reports, executive summaries, version diffs, affected control summaries, export_path.
- `audit_logs`: Global system activity log (who did what, when, IP address, payload summary).

---

### 5. The 14 Required Pages
1. **Login:** Role-based credentials, demo account quick-fill, secure JWT tokens.
2. **Dashboard:** Live operational metrics calculated directly from records (no mock graphs), quick actions, pending items.
3. **Regulatory Documents:** Document repository, filter by regulator/status, document details modal/view.
4. **Upload Document:** Drag-and-drop PDF upload, metadata validation, file integrity check, duplicate detection.
5. **Document Processing Details:** Real-time extraction status, page count, OCR detection, log inspection.
6. **Obligation Explorer:** Tabular explorer with faceted filters (entity, status, confidence, doc, date) and pagination.
7. **Evidence Verification:** Dual-panel split view (PDF viewer on left with jump-to-page and coordinate highlighting, structured extraction on right).
8. **Regulatory Version Comparison:** Side-by-side or diff comparison of two circular versions, categorizing obligations as New, Modified, Retired, Unchanged.
9. **Compliance Control Mapping:** Configurable control matrix, mapping rationale, reviewer approval buttons.
10. **Human Review Queue:** Dedicated inbox for compliance officers to approve, reject, or edit extracted fields with audit logs.
11. **Regulatory Impact Reports:** Report generator (executive overview, change delta, control impact, exportable as JSON/PDF).
12. **Audit History:** Full immutable ledger of changes and extraction provenance.
13. **User & Role Management:** Admin panel to manage roles, users, and permissions.
14. **Settings:** Regulator scope configuration, extraction confidence thresholds, taxonomy customization.

---

### 6. Extraction & Evidence Anchoring Pipeline
1. **PDF Text & Layout Extraction:** Powered by `pdfplumber` to extract clean page text and character/word layout blocks.
2. **Image-only / Scanned Detection:** Transparent detection of non-searchable PDFs; marks as `requires_ocr`.
3. **Regulatory Sentence Segmentation:** Legal text tokenizer respecting circular numbering, clauses, and sub-clauses.
4. **Mandatory Obligation Classifier:**
   - Detects normative modal verbs (*shall*, *must*, *is required to*, *shall ensure*, *will be liable to*).
   - Filters out non-normative definitions, recitals, and purely informational statements.
5. **Entity & Action Extraction:**
   - Entities: IFSCA registered entities, Fund Managers, Stock Exchanges, Intermediaries, Custodians, Authorized Persons.
   - Actions: Verbs and verb phrases following normative modals.
   - Deadlines: Temporal expressions (*within 30 days*, *quarterly*, *by 31st March*, *immediate*).
   - Conditions & Exceptions: Clauses initiated by *provided that*, *subject to*, *except where*, *unless*.
6. **Source Evidence Span Anchoring:**
   - Calculates exact character indices and page numbers in raw document text.
   - Attaches `evidence_status: anchored` when verified.
   - Flags low-confidence or unaligned items as `requires_review`.

---

### 7. Phase Plan Summary
- **Phase A:** Project specification, repository structure, environment variables, base configs, README.
- **Phase B:** Application shell, navigation, authentication, and core UI pages.
- **Phase C:** Database models, migrations, document upload, and PDF text/layout extraction.
- **Phase D:** Obligation extraction pipeline, evidence anchoring, and dual-panel evidence verification viewer.
- **Phase E:** Version comparison engine, compliance control mapping, and human review queue.
- **Phase F:** Impact report generator, comprehensive test suite, bug verification.
- **Phase G:** Docker, deployment configuration for Render and Vercel, demo data preparation.
