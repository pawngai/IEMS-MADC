# MyIEMS (MADC-HRMS)

MyIEMS is a bounded-context HRMS for MADC. The current implementation is a modular monolith with a FastAPI + MongoDB backend, a React + Vite frontend, and architecture guardrails that enforce context ownership, projection boundaries, and read/write separation.

## Current Implementation

- Backend app entrypoint: `backend/app/main.py`
- Frontend app entrypoint: `frontend/src/index.jsx`
- Backend API base: `/api`
- Health endpoints: `/health/live`, `/health/ready`
- Backend contexts currently present: `audit`, `change_requests`, `department`, `documents`, `employee_identity`, `employee_profile`, `ess`, `identity`, `leave`, `notifications`, `pay`, `rbac`, `reporting`, `seniority`, `service_book`, `system_admin`, `workflow`
- Frontend contexts currently present: `access_control`, `admin`, `analytics`, `applications`, `audit`, `change_requests`, `department`, `documents`, `employee_identity`, `employee_profile`, `ess`, `forms`, `identity`, `leave`, `masters`, `notifications`, `pay`, `seniority`, `service_book`, `workflow`

## What The App Currently Ships

- Employee identity management with canonical identity ownership in `employee_identity`
- Employee profile enrichment and read-side file views in `employee_profile`
- Workflow queue and staged approval flows in `workflow`
- Service Book read, opening, verification, correction, print, and records surfaces under `service_book`
- Service history mutation lifecycle surfaced through Service Book Records
- Department portal with dashboard, directory, pending work, leave view, employee file access, and sanctioned-strength management
- ESS portal with self profile, documents, service book, leave, notifications, and change requests
- Identity and user administration with role changes, authority history, employee account provisioning, and password flows
- Leave, pay, seniority, reporting, audit, and document-management modules
- Event-driven projection updates through an outbox + in-process event bus

Employee Directory creation note:

- The global Employee Directory exposes separate `Regular Employee` and `Non-Regular Employee` creation actions for `GLOBAL_DATA_ENTRY` and `DEALING_ASSISTANT` users who have `PROFILE_CREATE`.
- Those buttons do not depend on the `data_entry` module flag. The create route and backend write path still enforce authority and permission checks.

## Architecture

The repo is organized around bounded contexts and thin APIs.

- `employee_identity` owns canonical employee identity and the employee event Published Language (`contexts.employee_identity.contracts.events`)
- `employee_profile` owns profile enrichment and read projections; employment-type / service-book-eligibility predicates are delegated to `employee_identity` (no local mirror)
- `department` owns department-scoped portal orchestration and sanctioned-strength establishment data
- `documents` owns document storage and metadata and its own event payloads (`contexts.documents.contracts.events`)
- `leave` and `pay` own their ledgers
- `service_book` owns the service-event payloads under `contexts.service_book.records.contracts.events`
- `audit` is append-only
- `reporting` is read-only and runs aggregation queries against canonical collections
- `shared_kernel` and `app_platform` contain technical primitives only — no business event schemas, no domain truth, no business policies. `app_platform.policy_engine` hosts only the `Decision` primitive; leave-rule and change-request policies live in their owning contexts
- Cross-context DB writes are not allowed; cross-context coupling goes through `contracts/` modules only (Published Language / ACL pattern)

Service history note:

- The runtime exposes service-history behavior through `backend/contexts/service_book/records` and the frontend `service_book/records` surfaces.
- Service Book is the employee-facing read/print surface, and only regular employees have a Service Book.

Backend composition is centralized in `backend/app/bootstrap/router_registry.py`, with startup wiring in `backend/app/bootstrap/app_factory.py`. Cross-context updates flow through `backend/app_platform/outbox` and subscriber registration in `backend/app/bootstrap/subscribers.py`.

## Current User Surfaces

### Admin / operations surfaces

- `/employees`
- `/employees/:employeeId`
- `/documents`
- `/work`
- `/service-book`
- `/service-book/opening`
- `/service-book/records`
- `/leave`
- `/auditor`
- `/analytics`
- `/admin`
- `/seniority`

### Department portal

- `/department-portal/dashboard`
- `/department-portal/directory`
- `/department-portal/pending-work`
- `/department-portal/leave`
- `/department-portal/sanctioned-strength`
- `/department-portal/employee/:employeeId`

### ESS

- `/ess/dashboard`
- `/ess/profile`
- `/ess/documents`
- `/ess/service-book`
- `/ess/leave`
- `/ess/notifications`
- `/ess/change-requests`

The `/portal/*` scope is an active operations alias layer for the canonical paths above (see [`frontend/ROUTE_ALIAS_ALLOWLIST.md`](frontend/ROUTE_ALIAS_ALLOWLIST.md)).

## Repository Map

- `backend/`
  - FastAPI app, bounded contexts, platform services, tests, and Mongo scripts
- `frontend/`
  - React + Vite app, context-owned pages/components/models/api modules, Vitest tests
- `deploy/gcp/`
  - Compute Engine deployment scripts, Caddy config, backup/restore helpers
- `docs/reference/`
  - code map, deployment notes, security notes
- `scripts/`
  - root-level support and backfill helpers

## Local Development

### Prerequisites

- Python 3.12 recommended
- Node.js 20 recommended
- MongoDB 7 locally, or Docker Desktop if you want the Compose flow

### Fastest path

From the repo root:

```powershell
./start-dev.ps1
```

This starts:

- Backend on `http://127.0.0.1:8000`
- Frontend on `http://localhost:3000`

`start-dev.ps1` currently:

- injects `JWT_SECRET`, `MONGO_URL`, and `DB_NAME` for the backend process
- sets `REACT_APP_BACKEND_URL` for the frontend process
- attempts local Mongo bootstrap when `localhost:27017` is not already listening
- reclaims stale backend listeners on port `8000`
- can force-stop dev ports with `-ForceStop`
- can enable uvicorn reload with `-EnableReload`

Useful variants:

```powershell
./start-dev.ps1 -ForceStop
./start-dev.ps1 -EnableReload
./start-dev.ps1 -SkipMongoBootstrap
./start-dev.cmd -BackendPort 8001 -FrontendPort 3001 -ForceStop
```

To stop both dev servers:

```powershell
./stop-dev.ps1
```

### Manual backend startup

The backend loads environment variables from the project-root `.env`.

1. Create a virtual environment and install dependencies.
2. Copy `.env.example` to `.env` and set at least `JWT_SECRET`.
3. Start the API:

```powershell
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### Manual frontend startup

```powershell
cd frontend
npm ci
npm run dev -- --host 0.0.0.0 --port 3000
```

Implementation note:

- The frontend is Vite-based.
- The codebase reads `REACT_APP_BACKEND_URL` via `frontend/vite.config.mjs`.
- API requests are routed through `frontend/src/platform/api/httpClient.js`, which defaults to `http://<current-host>:8000/api` when `REACT_APP_BACKEND_URL` is not supplied.

## Environment Configuration

The canonical runtime env file is the project-root `.env`.

Important variables:

- `JWT_SECRET`
- `MONGO_URL`
- `DB_NAME`
- `ENVIRONMENT`
- `CORS_ORIGINS`
- `CORS_ORIGIN_REGEX`
- `RATE_LIMIT_STORAGE_URI`
- `API_TITLE`
- `API_DESCRIPTION`
- `API_VERSION`
- `UPLOAD_DIR`
- `DOCUMENT_STORAGE_BACKEND`
- `GCS_BUCKET_NAME`
- `GCP_PROJECT_ID`
- `REFRESH_COOKIE_SECURE`
- `REFRESH_COOKIE_SAMESITE`
- `REFRESH_COOKIE_DOMAIN`
- `REACT_APP_BACKEND_URL`

Notes:

- `backend/.env.example` is still useful as a backend-focused template, but the current settings loader reads root `.env`.
- Docker Compose also reads root `.env`.
- The backend will fail fast if `JWT_SECRET` is missing.
- Deployed runtimes should set `ENVIRONMENT=production`; this enables production defaults for cookies, CORS, document-storage fallback, and database startup behavior.

## Local Development Accounts

When you use `./start-dev.ps1`, the script seeds workflow users for local use and prints the credentials it started with.

Default workflow users started by the script:

- `global.dataentry@madc.gov.in` / `dataentry123`
- `verifier@madc.gov.in` / `verifier123`
- `hoo@madc.gov.in` / `hoo123`
- `dealing.clerk@madc.gov.in` / `dealing123`
- `auditor@madc.gov.in` / `auditor123`

System admin bootstrap is separate:

- `admin@madc.gov.in` is only synced when `IEMS_SEED_ADMIN_PASSWORD` is explicitly set in the environment or `.env`

Auth implementation details:

- access tokens are stored by the frontend in session/local storage
- refresh tokens are transported in an HttpOnly cookie on `/api/auth`
- login, refresh, logout, password change, and module-access routes live under `/api/auth`
- authorities such as `GLOBAL_DATA_ENTRY` and `DEPT_DATA_ENTRY` are roles/authorities
- permissions such as `PROFILE_CREATE` and `SERVICE_BOOK_READ_ALL` are backend action grants
- module ids such as `data_entry`, `service_book`, `leave`, `audit`, `verification`, `approval`, and `attestation` are UI/module visibility flags returned by `/api/auth/module-access`
- when module configuration is absent or the DB is unavailable, production module access infers a safe baseline from authorities and permissions
- when `module_permissions.matrix` exists in system configuration, it is the source of truth: configured `false` disables a module even if the authority would otherwise infer it

## Docker

Backend + MongoDB:

```powershell
docker compose up --build
```

Backend + MongoDB + frontend dev server:

```powershell
docker compose --profile dev up --build
```

Current Compose behavior:

- `mongo` uses `mongo:7`
- `backend` builds from the repo `Dockerfile`
- `frontend` is optional and only starts with the `dev` profile
- uploads are persisted in the `uploads_data` volume

## Testing And Guardrails

### Backend

From the repo root:

```powershell
python -m pytest -q backend/tests
```

Or from `backend/`:

```powershell
pytest tests -q
```

### Frontend

```powershell
cd frontend
npm run test
npm run lint
npm run build
```

Important guardrails:

- `backend/tests/test_architecture_guardrails.py` — single-aggregate enforcement (Service Book eligibility, workflow payload boundary, documents boundary, role-check policy, **event ownership boundary**, **profile-normalization mirror stays deleted**)
- `backend/tests/test_import_boundaries.py` — per-file cross-context import allowlist; domain→infrastructure restrictions
- `backend/tests/test_context_boundaries.py` — cross-context infrastructure import block
- `backend/tests/test_context_isolation_whole_repo.py` — repo-wide isolation
- `backend/tests/test_cross_context_collection_isolation.py` — MongoDB collection ownership
- `backend/tests/test_collection_ownership_enforced.py` — repository ownership at construction
- `backend/tests/test_target_architecture_enforcement.py` — backend topology
- `backend/tests/test_service_book_routes_are_read_only.py`
- `frontend/src/app/router/__tests__/routesImportGuard.test.js`
- `frontend/src/contexts/__tests__/contextBoundary.test.js`

CI workflows:

- `.github/workflows/ci.yml`
- `.github/workflows/boundary-guards.yml`
- `.github/workflows/frontend-boundary-lint.yml`
- `.github/workflows/dependency-audit.yml`

## Deployment

Current deployment assets live under `deploy/gcp/`.

The active deployment flow uses prebuilt backend images:

- publish backend image: `.github/workflows/publish-backend-image.yml`
- publish frontend image: `.github/workflows/publish-frontend-image.yml`
- deploy backend VM: `.github/workflows/deploy-backend-vm.yml`
- deploy frontend VM: `.github/workflows/deploy-frontend-vm.yml`
- VM smoke verification: `.github/workflows/smoke-test-vm.yml`

Helpful scripts:

- `deploy/gcp/build-and-push-image.ps1`
- `deploy/gcp/deploy-vm.ps1`
- `deploy/gcp/publish-and-deploy.ps1`
- `deploy/gcp/backup-vm.ps1`
- `deploy/gcp/restore-vm.ps1`

Production images install runtime dependencies from `backend/requirements-prod.txt`. Local development and CI use `backend/requirements.txt`.

Deployment notes:

- Publish workflows push both `latest` and `sha-<full-commit-sha>` tags to Artifact Registry.
- Deploy workflows should promote the immutable `sha-<full-commit-sha>` tag.
- Backend VM deploy recreates the backend container and waits for `/health/ready`.
- Frontend VM deploy recreates `frontend` plus `caddy` and verifies the public frontend URL.

## Reference Docs

- [App code map](docs/reference/app-code-documentation.md)
- [Backend architecture](backend/ARCHITECTURE.md)
- [Architecture rules](ARCHITECTURE_RULES.md)
- [Architecture tests](ARCHITECTURE_TESTS.md)
- [Architecture status inventory](ARCHITECTURE_STATUS.md)
- [Frontend boundaries](frontend/ARCHITECTURE_BOUNDARIES.md)
- [Document management implementation](docs/reference/document-management-implementation.md)
- [Google Cloud deployment guide](docs/reference/google-cloud-deployment.md)
- [Security review summary](docs/reference/SECURITY_REVIEW_SUMMARY.md)
- [Product requirements](memory/PRD.md)

## Notes

- The runtime entrypoint is `backend/app/main.py`; service-history behavior is owned by `service_book/records` end-to-end.
- The frontend reads `REACT_APP_BACKEND_URL` via `frontend/vite.config.mjs`. Renaming that env var requires updating this README, `.env.example`, deployment workflows, and local startup scripts together.
- This README is an orientation guide, not an API contract. Endpoint-level behavior should be verified in context routers, API adapters, and tests before changing integrations.
