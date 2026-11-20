# ROIS Implementation Status

Deployment-preparation report: 2026-11-19.

## Final acceptance

| Area | Status | Evidence |
|---|---|---|
| Backend tests | PASS | 30 tests pass, including production settings and revocation coverage. |
| Frontend build | PASS | Production build passes. |
| Authentication | PASS | Login, bcrypt passwords, bearer JWT, role dependencies, and logout revocation verified. |
| PDF processing | PASS | Signature, structure, encryption, duplicate, size, evidence, and report behavior tested. |
| Evidence traceability | PASS | Exact text/page offsets verified; no unsupported evidence was fabricated. |
| Version comparison | PASS | One-to-one modified-obligation comparison and attribute diffs verified. |
| Human review | PASS | Approve, reject, and corrected values persisted. |
| Control mapping | PASS | Actual database mappings and reviewable suggestions verified. |
| PDF/JSON downloads | PASS | Direct API and browser report response types verified; PDF/JSON files were valid. |
| PostgreSQL | NOT TESTED | PostgreSQL/`psql` executable unavailable. |
| OCR | NOT TESTED | Tesseract executable unavailable; OCR fallback remains scaffolded and image-only PDFs mark review required. |
| Docker | NOT TESTED | Docker executable unavailable. |
| Production security | PARTIAL | Secrets, CORS, role, upload, revocation, and production database rules hardened. Persistent infrastructure review remains. |
| Public deployment | NOT DEPLOYED | Vercel/Render configuration prepared only; no provider account or approval was used. |

## Deployment preparation completed

- Production rejects SQLite `DATABASE_URL` values.
- Production requires PostgreSQL and HTTPS CORS origins.
- Backend Docker startup accepts the platform `PORT`.
- Render blueprint defines PostgreSQL, backend disk, migration predeploy command,
  health check, and secret environment placeholders.
- Vercel rewrite provides SPA routing.
- Frontend API base URL is environment-configured and rejects localhost/HTTP
  URLs in Vercel builds.
- Initial production administrator provisioning is available through
  `python -m app.core.bootstrap_admin`; it uses protected environment variables
  and creates no credentials itself.
- Database and upload backup `.db`, `.db.*`, and `.backup` patterns are ignored.

## Explicit deployment blockers

1. No public Vercel account or deployment command was used.
2. No public Render account or deployment command was used.
3. PostgreSQL, Docker, and Tesseract executables are unavailable on this host.
4. An HTTPS Vercel origin and Render backend URL must be configured.
5. A PostgreSQL database URL and unique JWT secret must be supplied through
   the deployment provider.
6. Render persistent disk configuration must be provisioned and mounted.
7. Administrator credentials must be created through protected environment
   variables, without committing secrets.
8. Object-storage migration is required for multi-region or ephemeral replicas.

## Data protection

The original `rois.db` was not migrated or changed.
The existing backup remains present but is now ignored by Git:
`rois.db.pre-final-integration.20261119-225914.backup`.

## Browser and regulatory validation

The browser workflow was exercised against disposable data:

- Login and dashboard: PASS.
- Document listing and PDF upload: PASS.
- Obligation and evidence routes: PASS.
- Version comparison: PASS.
- Review approval/rejection/correction: PASS through API and browser routes.
- Control mapping: PASS.
- Report rendering and export responses: PASS.
- Audit ledger: PASS.
- Demo and synthetic documents remain clearly labeled.
- Comparison and mapping outputs remain machine recommendations until human review.

## Remaining work before production

- Execute PostgreSQL migrations and CRUD tests.
- Test Docker and full Compose networking/storage.
- Execute real Tesseract OCR on a scanned PDF.
- Provision a public PostgreSQL database.
- Configure Vercel and Render environment variables.
- Attach persistent document storage.
- Bootstrap the evaluation administrator.
- Perform external-browser login, upload, evidence, report, and restart tests.
- Add rate limiting, password reset, and audit retention policies.
