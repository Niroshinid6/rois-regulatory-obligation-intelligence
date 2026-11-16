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

# Copy environment file
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

# Run FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

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
