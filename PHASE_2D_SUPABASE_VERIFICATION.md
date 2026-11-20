# Phase 2D — Supabase Live Verification

Status: **BLOCKED — live Supabase verification did not pass**

Date: 2026-11-20

## Scope and safety

The original repository, working-tree changes, active `main` branch, and existing
SQLite database were preserved. The live test used an isolated disposable SQLite
database and a generated `[DEMONSTRATION ONLY]` PDF.

The existing [rois.db](/c:/Users/Niros/rois-regulatory-obligation-intelligence/rois.db)
SHA-256 before testing was:

`7901b5194cea53dd61489397d1453f17bbc1d6188b319985b69890c217920fa3`

No existing production or test document was deleted or modified.

## Configuration verification

The backend `.env` was inspected only by key presence and non-secret
configuration. Secret values were not printed.

| Setting | Result |
|---|---|
| `ROIS_ENV` | `development` |
| `DATABASE_URL` | Set; SQLite for the local environment |
| `DOCUMENT_STORAGE_PROVIDER` | `supabase` |
| `SUPABASE_URL` | Set; HTTPS |
| `SUPABASE_SERVICE_ROLE_KEY` | Set; value length 46 |
| `SUPABASE_STORAGE_BUCKET` | `rois-documents` |
| `CORS_ORIGINS` | Set |
| `SECRET_KEY` | Set; non-secret length 52 |

The Supabase service-role credential is available to the backend environment,
but live bucket and object operations have not passed verification.

## Mocked test results

Command:

```powershell
cd backend
python -m pytest -q
```

Result: **55 tests passed**.

The storage suite includes mocked Supabase provider tests. Those tests are not
an actual Supabase integration and must not be treated as live verification.

Frontend build verification also passed:

```powershell
cd frontend
npm ci
npm run build
```

The frontend build succeeded, but this was unrelated to live Supabase access.

## Live configuration results

Command used to list Supabase bucket metadata:

```powershell
python c:/Users/Niros/.copilot/session-state/6de7c66a-7529-48f6-b3dc-5741515bedf3/files/supabase_bucket_probe.py
```

Actual results:

- Supabase bucket count: `0`
- `rois-documents` found: `False`
- Bucket names returned: none

Result: **FAIL — required private bucket is not visible to the configured
backend credential**.

A disposable application integration test was then started:

```powershell
cd backend
python c:/Users/Niros/.copilot/session-state/6de7c66a-7529-48f6-b3dc-5741515bedf3/files/phase2d_live_test.py
```

Actual partial results:

| Check | Result |
|---|---|
| Private bucket verification | FAIL |
| Disposable user login | PASS (`200`) |
| Unauthorized request without bearer token | PASS (`401`) |
| Real application upload | FAIL (`400`) |
| Upload detail | `Could not store or verify the uploaded PDF.` |
| Object existence verification | Not completed |
| Authenticated application download | Not completed |
| SHA-256 comparison | Not completed |
| File-size consistency | Not completed |
| Unauthorized document download | Not completed |
| Direct public access rejection | Not completed |
| Real deletion | Not completed |
| Missing-object handling | Not completed |
| Cleanup retry/recovery | Not completed |
| Backend restart persistence | Not completed |

The live test stopped immediately when the application upload failed. No live
object was confirmed to exist, and no existing document or database record was
affected.

## Required configuration

Before Phase 2D can continue, configure the following in the Supabase dashboard:

1. Create the bucket `rois-documents`.
2. Set the bucket visibility to **Private**.
3. Ensure the configured service-role credential can list and administer
   Storage buckets and objects.
4. Do not use a frontend or anonymous key for `SUPABASE_SERVICE_ROLE_KEY`.
5. Preserve the current backend-only environment-variable configuration.

Do not place the service-role credential in frontend source or environment
configuration.

After bucket creation, confirm without printing secret values that:

- `DOCUMENT_STORAGE_PROVIDER= supabase`
- `SUPABASE_URL` is an HTTPS project URL.
- `SUPABASE_SERVICE_ROLE_KEY` is set.
- `SUPABASE_STORAGE_BUCKET=rois-documents`
- Bucket `public` metadata is `false`.

## Acceptance criteria

| Acceptance criterion | Actual status |
|---|---|
| Real upload tested | **FAIL — blocked by unavailable bucket/access** |
| Real download tested | **NOT RUN** |
| Real deletion tested | **NOT RUN** |
| Private bucket verified | **FAIL — bucket was not visible** |
| SHA-256 integrity verified | **NOT RUN** |
| File-size consistency verified | **NOT RUN** |
| Access control verified | Partial: unauthenticated API rejected |
| Public access rejection verified | **NOT RUN** |
| Missing-object handling tested | **NOT RUN** |
| Cleanup retry/recovery tested | **NOT RUN** |
| Restart persistence tested | **NOT RUN** |
| Existing data unaffected | **PASS — isolated disposable database used** |

## Git state

The live test did not change the repository source or commit any files. Existing
uncommitted work was preserved and the active branch remained `main`.

Git status was reviewed before the test. The existing database file was
fingerprinted before testing and was not used by the live test.

## Next action

Stop and configure the private `rois-documents` bucket and service-role access.
This report must remain blocked until a real Supabase bucket can be listed and
a disposable PDF can be uploaded, downloaded, deleted, and reconciled
successfully.

## Retry after bucket creation

Date: 2026-11-20

The private bucket was reported as created, and the retry performed a fresh
configuration and credential check before attempting live object operations.

### Configuration retry

The live `.env` configuration was redacted and inspected:

- `DOCUMENT_STORAGE_PROVIDER=supabase`
- `SUPABASE_STORAGE_BUCKET=rois-documents`
- Supabase URL host: `yejvrtqyktojseqimrhb.storage.supabase.co`
- Service-role key: present
- Service-role key format: unrecognized; it was neither an `sb_publishable_*`
  key, a legacy JWT key, nor an `sb_secret_*` service-role key

The URL host differs from the normal Supabase project URL shape
(`*.supabase.co`). It appears to be a Storage endpoint host rather than the
project URL required by the application.

### Actual bucket probe retry

Command:

```powershell
python c:/Users/Niros/.copilot/session-state/6de7c66a-7529-48f6-b3dc-5741515bedf3/files/supabase_bucket_probe.py
```

Actual results:

- Supabase bucket count: `0`
- `rois-documents` found: `False`
- Bucket names returned: none

The direct Storage REST probe returned:

```text
HTTP_STATUS=403
Resource=storage/v1/bucket
Code=AccessDenied
Message=Missing signature
```

The credential was redacted from the response.

Result: **FAIL — the configured URL and credential cannot authenticate the
Storage bucket administration endpoint**.

### Root-cause determination

Two configuration defects block the live integration:

1. `SUPABASE_URL` is configured with a `storage.supabase.co` endpoint host.
   The application expects the HTTPS project URL.
2. `SUPABASE_SERVICE_ROLE_KEY` is not in a recognized Supabase service-role
   credential format. The configured value cannot authorize bucket listing or
   bucket/object operations.

The earlier HTTP 400 is therefore not safe to treat as an application-only
upload failure. The underlying Storage API returned HTTP 403
`Missing signature` during direct bucket authentication probing. The
disposable application upload was not retried against this state because there
is no confirmed private bucket access.

### Disposable cleanup

The previous failed live attempt created one isolated temp directory containing:

- one disposable database
- one disposable PDF

The directory was inspected and removed completely:

```text
C:\Users\Niros\AppData\Local\Temp\rois-phase2d-h4m2e379
```

No previous Supabase object was confirmed to exist. The original
[rois.db](/c:/Users/Niros/rois-regulatory-obligation-intelligence/rois.db)
SHA-256 remained unchanged:

`7901b5194cea53dd61489397d1453f17bbc1d6188b319985b69890c217920fa3`

### Updated acceptance criteria

| Acceptance criterion | Retry status |
|---|---|
| Supabase URL is the project URL | **FAIL** |
| Backend service-role credential is available | **FAIL — format/authorization invalid** |
| `rois-documents` accessible | **FAIL** |
| Bucket private | **NOT VERIFIED** |
| Real upload tested | **NOT RUN** |
| Real download tested | **NOT RUN** |
| Real deletion tested | **NOT RUN** |
| SHA-256 integrity verified | **NOT RUN** |
| File-size consistency verified | **NOT RUN** |
| Unauthorized access verified | **NOT RUN** |
| Public access rejection verified | **NOT RUN** |
| Missing-object handling tested | **NOT RUN** |
| Cleanup retry/recovery tested | **NOT RUN** |
| Restart persistence tested | **NOT RUN** |
| Existing data unaffected | **PASS** |

## Required configuration change

Configure both values in the backend `.env` or deployment environment:

1. Set `SUPABASE_URL` to the project's HTTPS URL, normally:
   `https://<project-ref>.supabase.co`
2. Set `SUPABASE_SERVICE_ROLE_KEY` to the Supabase **service-role** secret from
   Project Settings → API, not a publishable key or anonymous key.
3. Confirm the backend can list `rois-documents` and that its private/public
   metadata is `false`.

Do not send secret values through chat. Restart the backend after the
configuration is corrected.

## Current retry — 2026-11-20

Status: **BLOCKED — no live Storage tests were run**

### Sanitized configuration validation

The latest configuration check found:

| Check | Result |
|---|---|
| `DOCUMENT_STORAGE_PROVIDER=supabase` | PASS |
| `SUPABASE_STORAGE_BUCKET=rois-documents` | PASS |
| `SUPABASE_URL` is HTTPS | FAIL |
| `SUPABASE_URL` is a `*.supabase.co` project URL | FAIL |
| `SUPABASE_SERVICE_ROLE_KEY` is supported | FAIL |
| Bucket exists | NOT VERIFIED |
| Bucket is private | NOT VERIFIED |

The direct value check shows that the URL value begins with the key name itself:
`SUPABASE_URL=` rather than `https://`. This is a malformed environment value.

The direct Storage API probe returned:

```text
Error type: UnsupportedProtocol
Sanitized error: Request URL is missing an 'http://' or 'https://' protocol.
```

The credential format did not match a supported backend service-role format
(`sb_secret_*` or a legacy JWT). No credential value or project credential was
printed or written to repository logs.

### Live test status

No disposable PDF, Supabase object, or disposable database record was created
for this retry.

| Live test | Result |
|---|---|
| Real upload | NOT RUN |
| Object existence | NOT RUN |
| Authenticated download | NOT RUN |
| SHA-256 comparison | NOT RUN |
| Anonymous/public access denial | NOT RUN |
| Authorized deletion | NOT RUN |
| Deleted-object verification | NOT RUN |
| Missing-object handling | NOT RUN |
| Cleanup/failure recovery | NOT RUN |
| Backend restart persistence | NOT RUN |

### Cleanup and integrity

- No `rois-phase2d-*` temporary directory exists.
- [rois.db](/c:/Users/Niros/rois-regulatory-obligation-intelligence/rois.db)
  SHA-256 remains
  `7901b5194cea53dd61489397d1453f17bbc1d6188b319985b69890c217920fa3`.
- No existing document or database record was touched.
- No secret value was written to the report or Git-tracked files.

### Stop reason

The Supabase URL is malformed and the backend credential is not recognized as
a supported service-role credential. Configure the `.env` as:

```text
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<backend service-role credential>
SUPABASE_STORAGE_BUCKET=rois-documents
DOCUMENT_STORAGE_PROVIDER=supabase
```

Do not include the credential in chat. After correcting the environment values,
restart the backend and rerun configuration validation. Phase 2D and all live
Storage acceptance tests remain blocked.
