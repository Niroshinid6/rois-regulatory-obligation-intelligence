# ROIS — Regulatory Obligation Intelligence System

> **Tagline:** Every compliance obligation, traced to the exact sentence that created it.  
> **Domain:** Regulatory Technology (RegTech), AI and intelligent financial systems.  
> **Initial Scope:** International Financial Services Centres Authority (IFSCA).  
> **Target Evaluation:** GIFT FutureLab Evaluation Panel.

---

## 1. Overview
ROIS transforms complex financial regulatory circulars, rules, and guidelines into structured, traceable, and actionable compliance intelligence.

Unlike generic chatbots or PDF summarizers, ROIS preserves **exact character-level and page-level source coordinates** for every extracted obligation, maps obligations across versions, links them to a compliance control taxonomy, and provides an end-to-end human verification and audit trail.

---

## 2. Monorepo Architecture

```text
ROIS/
  frontend/          # React 18, TypeScript, Vite, Tailwind CSS
  backend/           # FastAPI, SQLAlchemy, Alembic, Pydantic, pdfplumber
  data/              # Sample authentic IFSCA regulatory documents and annotations
  research/          # RegTech methodology and evaluation metrics
  docker-compose.yml # Containerized multi-service deployment
  PROJECT_SPEC.md    # Detailed system specification
  README.md          # Setup & execution instructions
  .env.example       # Environment variables template
```

---

## 3. Quick Start (Local Development)

### Prerequisites
- **Node.js** v18+ (tested with v24)
- **Python** 3.11+ (tested with Python 3.14 on Windows)
- **Git**

---

### Step 1: Clone and Configure Environment

```bash
git clone https://github.com/niros-org/rois-regulatory-obligation-intelligence.git
cd rois-regulatory-obligation-intelligence

# Copy environment file (PowerShell: Copy-Item .env.example .env)
cp .env.example .env
```

---

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create or update the database schema
python -m alembic upgrade head

# Optional: add local demonstration users, documents, and sample data
python -m app.core.seed_data

# Run FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Demo seeding is for local development only. Generated sample circular-like
  PDFs are marked as demonstrations and are not official IFSCA publications.
- Set a unique secret key and `ROIS_ENV=production` before production use.

---

### Step 3: Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 4. Docker Deployment

To launch the complete application stack (PostgreSQL, FastAPI Backend, React Frontend):

```bash
cp .env.example .env
# Replace SECRET_KEY and POSTGRES_PASSWORD in .env before starting.
docker-compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- PostgreSQL Database: `localhost:5432`

---

## 5. Development Phases

- [x] **Phase A:** Workspace inspection, `PROJECT_SPEC.md`, project structure, environments, base configs, README.
- [ ] **Phase B:** Application shell, navigation, authentication, and core UI pages.
- [ ] **Phase C:** PostgreSQL models, migrations, document upload, and PDF text/layout extraction.
- [ ] **Phase D:** Obligation extraction pipeline, evidence anchoring, and dual-panel evidence verification viewer.
- [ ] **Phase E:** Version comparison engine, compliance control mapping, and human review queue.
- [ ] **Phase F:** Impact report generator, comprehensive test suite, bug verification.
- [ ] **Phase G:** Docker, deployment configuration for Render and Vercel, demo data preparation.

---

## 6. License
Individual research and innovation project for GIFT FutureLab evaluation. All rights reserved.

## 7. Final Local Run Commands

### Windows PowerShell

```powershell
Copy-Item .env.example .env
# Replace placeholder SECRET_KEY and database credentials before non-development use.

cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Second terminal
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. Demo accounts are created only by:

```powershell
cd backend
.\venv\Scripts\python.exe -m app.core.seed_data
```

Demo seeding is blocked by `ROIS_ENV=production`. Generated PDFs contain a
visible demonstration notice and must not be treated as official IFSCA documents.

### Tests

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm run build
```

## 8. OCR

Scanned pages are detected by low extractable character count. OCR runs only
for those pages. OCR text is stored separately through `extraction_method`,
`ocr_confidence`, and `requires_human_review`.

Windows installation:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Docker installs Tesseract automatically in `backend/Dockerfile`. Restart the
backend after installing Tesseract. OCR output is uncertain rather than
authoritative and is flagged below a 60-point confidence threshold.

## 9. PostgreSQL and Docker

PostgreSQL is supported by `DATABASE_URL=postgresql+psycopg://...`.

```powershell
docker compose up --build
```

At release time, set `ROIS_ENV=production`, a unique `SECRET_KEY`, a unique
`POSTGRES_PASSWORD`, and production CORS origins. PostgreSQL remains on the
Compose internal network; the external database port is not published. Run
migrations only against disposable databases first:

```powershell
docker compose run --rm backend python -m alembic upgrade head
```

Docker and PostgreSQL runtime validation could not be executed on this host
because Docker and PostgreSQL executables were unavailable.

## 10. Environment Variables

- `ROIS_ENV`: `development`, `test`, or `production`
- `SECRET_KEY`: unique secret of at least 32 characters
- `DATABASE_URL`: SQLite or PostgreSQL SQLAlchemy URL
- `UPLOAD_DIR`: server-controlled PDF storage directory
- `MAX_UPLOAD_SIZE_MB`: default 25
- `CORS_ORIGINS`: comma-separated browser origins
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Compose database settings
- `VITE_API_URL`: frontend API base URL

## 11. Release Validation Summary

The final validation pass used disposable SQLite databases and upload directories.
The original `rois.db` was not migrated or overwritten and remains backed up.

Verified:
- 28 backend tests pass.
- Frontend production build passes.
- PDF signature, structure, encryption, duplicate, size, and anonymous-download
  protections pass.
- Logout revocation persists in `revoked_tokens`.
- Browser login, dashboard, documents, uploads, evidence routes, comparisons,
  controls, review routes, reports, and audit routes were exercised.
- Direct PDF and JSON report exports produce valid files.

Not runtime-verified on this host:
- OCR text extraction with Tesseract.
- PostgreSQL migrations and CRUD.
- Docker image builds and Compose runtime.

Do not describe these areas as production-ready until their executable environments
are available and their tests are executed.

## 12. Public Demonstration Deployment

ROIS is prepared for a Vercel frontend and Render backend/PostgreSQL deployment.
Deployment has not been executed and no public URL is claimed.

### Render backend

Required environment variables:

- `ROIS_ENV=production`
- `DATABASE_URL`: Render PostgreSQL connection string
- `SECRET_KEY`: unique random secret of at least 32 characters
- `CORS_ORIGINS`: exact HTTPS Vercel origin
- `UPLOAD_DIR=/var/data/uploads`
- `MAX_UPLOAD_SIZE_MB=25`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `BOOTSTRAP_ADMIN_FULL_NAME`

The backend startup command accepts the platform `PORT` variable:

```sh
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

After migrations, create the initial administrator once:

```sh
python -m app.core.bootstrap_admin
```

This command creates no credentials itself. It requires protected environment
variables and must not be run with placeholder values. Do not seed official
regulatory circulars or authentic IFSCA content.

### Render persistent uploads

The repository's `render.yaml` declares a 1 GB Render disk mounted at
`/var/data/uploads`. Uploaded PDFs therefore persist in this environment only
when the same disk is attached to the service. For multi-region, high-volume,
or external-object-storage deployments, migrate files to an S3-compatible
object store and store provider-independent keys.

### Vercel frontend

Set the Vercel environment variable:

```text
VITE_API_URL=https://your-render-backend.example.com/api/v1
```

The frontend rejects missing or localhost API URLs in Vercel builds, and
`frontend/vercel.json` provides SPA fallback routing.
