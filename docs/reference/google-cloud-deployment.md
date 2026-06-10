# Google Cloud Deployment

This repository is currently easiest to deploy on Google Cloud with this split:

- Frontend, backend, and Caddy on one Compute Engine VM using Docker Compose
- Frontend shipped as a prebuilt container image
- MongoDB private inside the same VM Docker network

This matches the default VM deployment behavior because local document storage writes uploads under `UPLOAD_DIR`. The backend also has a GCS-capable storage path via `DOCUMENT_STORAGE_BACKEND=gcs`, but the single-VM deployment keeps local storage as the simplest operational model.

## Architecture

- Compute Engine runs `mongo`, `backend`, `frontend`, and `caddy` using `deploy/gcp/docker-compose.vm.yml` plus `deploy/gcp/docker-compose.frontend.vm.yml`
- Caddy terminates HTTPS, proxies `/api` and health routes to the backend container, and forwards SPA routes to the frontend container
- MongoDB stays private inside the Docker network on the VM

## Prerequisites

- A Google Cloud project
- A billing account linked to that project
- A Compute Engine VM in `us-central1`, `us-east1`, or `us-west1` if you want the best chance of staying near the Always Free tier
- A domain or subdomain for the public app if you want HTTPS via Let's Encrypt

## Files Added For This Setup

- `deploy/gcp/docker-compose.vm.yml`: backend, MongoDB, and Caddy services
- `deploy/gcp/docker-compose.frontend.vm.yml`: frontend compose override for the VM
- `deploy/gcp/.env.example`: backend environment template for the VM
- `deploy/gcp/Caddyfile.example`: reverse proxy template
- `deploy/gcp/Dockerfile.frontend`: production frontend image build
- `deploy/gcp/Caddyfile.frontend`: SPA file-server config inside the frontend image

## 1. Build And Deploy The Frontend Image

The production frontend image builds from `frontend/`, runs `vite build`, and serves `dist/` from a small Caddy container.

Build and push it manually if needed:

```bash
docker build -f deploy/gcp/Dockerfile.frontend \
	--build-arg REACT_APP_BACKEND_URL=/api \
	-t us-central1-docker.pkg.dev/your-project-id/iems/myiems-frontend:latest .
docker push us-central1-docker.pkg.dev/your-project-id/iems/myiems-frontend:latest
```

The GitHub workflow `.github/workflows/publish-frontend-image.yml` publishes the frontend image to Artifact Registry, and `.github/workflows/deploy-frontend-vm.yml` promotes a chosen image tag onto the VM. The deploy workflow uploads the frontend compose override, rewrites the VM Caddyfile for the configured app host, and rolls `frontend` plus `caddy`.

Required repository variables:

- `GCP_PROJECT_ID`
- `GAR_LOCATION` (optional, defaults to `us-central1`)
- `GAR_REPOSITORY` (optional, defaults to `iems`)
- `FRONTEND_IMAGE_NAME` (optional, defaults to `myiems-frontend`)
- `GCE_ZONE`
- `GCE_INSTANCE_NAME`
- `GCE_SSH_USER`
- `GCE_REPO_ROOT_ON_VM`
- `FRONTEND_DEPLOY_COMPOSE_FILE` (optional, defaults to `deploy/gcp/docker-compose.frontend.vm.yml`)
- `FRONTEND_DEPLOY_ENV_FILE` (optional, defaults to `deploy/gcp/.env`)
- `FRONTEND_APP_URL`

Additional variable needed by the publish workflow:

- `FRONTEND_BACKEND_URL`

Required repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

## 2. Create The Compute Engine VM

Recommended VM for learning:

- Machine type: `e2-micro`
- Region: `us-central1`, `us-east1`, or `us-west1`
- Boot disk: Ubuntu LTS
- Disk size: 30 GB standard persistent disk
- Allow HTTP and HTTPS traffic

These settings line up with the current Google Cloud Always Free limits for Compute Engine in supported US regions.

## 3. Install Docker On The VM

SSH into the VM and run:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

## 4. Copy The Repo To The VM

Either clone from GitHub:

```bash
git clone https://github.com/pawngai/MyIEMS.git
cd MyIEMS
```

Or copy only the deploy files you need onto the VM if you already build the backend image elsewhere.

Important: the recommended deploy flow is now to build and push the backend image outside the VM, then let the VM pull that image. This avoids slow VM-side Docker builds on small Compute Engine instances.

## 5. Build And Push The Backend Image

Build the production backend image from your workstation or CI using the GCP backend Dockerfile:

```bash
docker build -f deploy/gcp/Dockerfile.backend -t us-central1-docker.pkg.dev/your-project-id/iems/myiems-backend:latest .
docker push us-central1-docker.pkg.dev/your-project-id/iems/myiems-backend:latest
```

If you use Artifact Registry, authenticate Docker first:

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

If local Docker is unavailable, build the same image remotely with Cloud Build:

```bash
gcloud builds submit --project your-project-id --config deploy/gcp/cloudbuild.backend.yaml .
```

From Windows, you can also use the helper script from the repository root:

```powershell
./deploy/gcp/build-and-push-image.ps1
```

Or run the full publish-and-deploy flow in one command:

```powershell
./deploy/gcp/publish-and-deploy.ps1 -HealthUrl https://app.example.com/api/health
```

If direct inbound SSH from your workstation is blocked, use IAP tunneling instead:

```powershell
./deploy/gcp/enable-iap-ssh.ps1
./deploy/gcp/publish-and-deploy.ps1 -TunnelThroughIap -HealthUrl https://app.example.com/api/health
```

Useful parameters:

- `-ProjectId`, `-Region`, `-Repository`, `-ImageName`, and `-Tag` to control the Artifact Registry target
- `-SkipDockerAuth` if Docker is already authenticated for the Artifact Registry host
- `-Dockerfile` and `-BuildContext` if you need to point at a different image source
- `-TunnelThroughIap` on `deploy-vm.ps1` and `publish-and-deploy.ps1` to route VM access through Identity-Aware Proxy instead of direct SSH

The production image now installs only runtime dependencies from `backend/requirements-prod.txt`, which reduces image build time and package install time compared with the dev/test dependency set.

### GitHub Actions Publish And Deploy Option

This repository includes `.github/workflows/publish-backend-image.yml` for automated image publishing to Artifact Registry and `.github/workflows/deploy-backend-vm.yml` for production VM deployment.

Configure these GitHub repository variables:

- `GCP_PROJECT_ID`: your Google Cloud project id
- `GAR_LOCATION`: Artifact Registry region, for example `us-central1`
- `GAR_REPOSITORY`: Artifact Registry repository name, for example `iems`
- `BACKEND_IMAGE_NAME`: image name, for example `myiems-backend`

Configure these GitHub repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`: full Workload Identity Provider resource name
- `GCP_SERVICE_ACCOUNT`: deploy service account email

After that, run the `Publish Backend Image` workflow manually. It publishes both `latest` and `sha-<full-commit-sha>` tags.

Run `Deploy Backend VM` manually with the image tag you want to promote, for example `sha-<commit>` or `latest`.

For the frontend, run `.github/workflows/publish-frontend-image.yml` first. It publishes both `latest` and `sha-<full-commit-sha>` tags.

Then run `.github/workflows/deploy-frontend-vm.yml` manually with the image tag you want to promote, for example `sha-<commit>` or `latest`. The default production frontend build uses `/api` for backend requests so the app and API can share one public origin.

Recommended promotion practice:

- Prefer immutable `sha-<full-commit-sha>` tags for both backend and frontend deployment.
- Use `latest` only for quick manual recovery when you have verified which commit it points to.
- Backend deploy waits for `/health/ready`; frontend deploy verifies the configured public frontend URL.

## 6. Configure Backend Environment

On the VM:

```bash
cd deploy/gcp
cp .env.example .env
cp Caddyfile.example Caddyfile
```

Edit `deploy/gcp/.env`:

- Set `BACKEND_IMAGE` to the pushed backend image reference
- Set `FRONTEND_IMAGE` to the pushed frontend image reference when deploying outside GitHub Actions
- Keep `ENVIRONMENT=production` so production-only hardening is active
- Set a real `JWT_SECRET`
- Keep `MONGO_URL=mongodb://mongo:27017` when Mongo runs in the same Compose project
- Set `CORS_ORIGINS` to your public frontend origin
- If frontend and API are on different sites and refresh-cookie flows are required, set `REFRESH_COOKIE_SAMESITE=none` and a suitable `REFRESH_COOKIE_DOMAIN`; production defaults `REFRESH_COOKIE_SECURE=true`
- For multi-worker or multi-process backend deployments, set `RATE_LIMIT_STORAGE_URI` to a shared backend such as Redis

Example:

```env
BACKEND_IMAGE=us-central1-docker.pkg.dev/your-project-id/iems/myiems-backend:latest
FRONTEND_IMAGE=us-central1-docker.pkg.dev/your-project-id/iems/myiems-frontend:latest
ENVIRONMENT=production
JWT_SECRET=replace-with-a-long-random-secret
DB_NAME=iems_db
MONGO_URL=mongodb://mongo:27017
UPLOAD_DIR=/app/uploads
DOCUMENT_STORAGE_BACKEND=local
CORS_ORIGINS=https://app.example.com
# RATE_LIMIT_STORAGE_URI=redis://redis:6379/0
# REFRESH_COOKIE_SAMESITE=none
# REFRESH_COOKIE_DOMAIN=.example.com
```

Edit `deploy/gcp/Caddyfile` and replace `your-app-domain.example.com` with your actual public app domain if you are not using the GitHub deploy workflow to write it for you.

## 6.1 Module Access Configuration

`GET /api/auth/module-access` returns module visibility flags used by the frontend shell, route guards, and workflow queues. These are not permissions or roles.

Current module ids include:

- `data_entry`
- `service_book`
- `leave`
- `audit`
- `verification`
- `approval`
- `attestation`
- `admin_console`
- `user_management`
- `department_management`
- `ess_portal`

Current production behavior:

- If the DB is unavailable or `module_permissions.matrix` has not been configured, the backend fails closed but infers a safe baseline from authorities and permissions.
- If `module_permissions.matrix` exists, it is authoritative. A configured `false` disables a module even if the user's authority would otherwise infer that module.
- Backend writes remain protected by authority and permission checks; module access is a visibility/routing contract.

Example system config payload:

```json
{
  "module_permissions": {
    "matrix": {
      "GLOBAL_DATA_ENTRY": {
        "data_entry": true,
        "service_book": true,
        "leave": true
      },
      "VERIFIER": {
        "verification": true,
        "service_book": true
      },
      "SYSTEM_ADMIN": {
        "admin_console": true,
        "user_management": true,
        "department_management": true,
        "audit": true
      }
    }
  }
}
```

Operational check after changing module config:

```bash
curl -H "Authorization: Bearer <token>" https://app.example.com/api/auth/module-access
```

## 7. Point DNS To The VM

Create an `A` record for your public app domain pointing to the VM external IP.

Example:

- `app.example.com -> <vm-external-ip>`

Once DNS resolves correctly, Caddy can obtain and renew Let's Encrypt certificates automatically.

## 8. Start The VM Stack

From the repository root on the VM:

```bash
docker compose -f deploy/gcp/docker-compose.vm.yml -f deploy/gcp/docker-compose.frontend.vm.yml pull
docker compose -f deploy/gcp/docker-compose.vm.yml -f deploy/gcp/docker-compose.frontend.vm.yml up -d
```

This compose file now pulls the backend image named in `BACKEND_IMAGE` instead of building it locally on the VM.

From Windows, you can also use the helper script from the repository root:

```powershell
./deploy/gcp/deploy-vm.ps1 -HealthUrl https://app.example.com/api/health
```

To roll a published tag onto the VM from GitHub Actions, use `.github/workflows/deploy-backend-vm.yml`.

Required repository variables:

- `GCP_PROJECT_ID`
- `GCE_ZONE`
- `GCE_INSTANCE_NAME`
- `GCE_SSH_USER`
- `GCE_REPO_ROOT_ON_VM`
- `BACKEND_DEPLOY_COMPOSE_FILE` (defaults to `deploy/gcp/docker-compose.vm.yml`)
- `BACKEND_DEPLOY_ENV_FILE` (defaults to `deploy/gcp/.env`)
- `BACKEND_HEALTH_URL` (optional, enables post-deploy health probing)

Required repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

Run that workflow with the backend image tag you want to promote, for example `sha-<commit>` or `latest`.

The deploy workflow removes any stale `IEMS_SEED_ADMIN_PASSWORD` entry from `deploy/gcp/.env` and does not write seed admin credentials. Dev account sync is skipped in production, so admin credentials must be managed through the application or an approved operational reset procedure.

Useful parameters:

- `-ProjectId`, `-Zone`, `-InstanceName` to target a different VM
- `-RepoRootOnVm` if the repository lives in a different home directory on the VM
- `-SkipPull` if the image is already pulled and you only want to restart the stack
- `-SkipHealthCheck` to skip the post-deploy HTTP probe

Check status:

```bash
docker compose -f deploy/gcp/docker-compose.vm.yml ps
docker compose -f deploy/gcp/docker-compose.vm.yml logs -f backend
docker compose -f deploy/gcp/docker-compose.vm.yml logs -f caddy
```

## 8.1 Backup And Restore

Create a production backup before deployments, migrations, and administrative bulk changes:

```powershell
./deploy/gcp/backup-vm.ps1 -TunnelThroughIap
```

Validate backup command construction without contacting the VM:

```powershell
./deploy/gcp/backup-vm.ps1 -TunnelThroughIap -DryRun
```

The backup script creates a timestamped archive on the VM under `/home/kenne/iems-backups` and downloads it to a local `backups/` folder unless `-SkipDownload` is provided. The archive contains:

- `mongo-iems_db.archive.gz` from `mongodump --db iems_db`
- `uploads.tar.gz` from the backend uploads volume
- a `.sha256` sidecar for archive integrity checks

Restore is destructive and requires an explicit `-Force` flag:

```powershell
./deploy/gcp/restore-vm.ps1 -LocalBackupArchive ./backups/iems-backup-YYYYMMDD-HHMMSS.tgz -TunnelThroughIap -Force
```

Validate restore command construction without uploading files or contacting the VM:

```powershell
./deploy/gcp/restore-vm.ps1 -RemoteBackupArchive /home/kenne/iems-backups/iems-backup-YYYYMMDD-HHMMSS.tgz -TunnelThroughIap -DryRun
```

After restore, run the VM smoke workflow and verify `/health/ready` before reopening normal use. Keep at least one off-VM backup copy and periodically test restore on a non-production VM.

## 9. Verify The Deployment

Backend health checks:

```bash
curl https://app.example.com/api/health
curl https://app.example.com/health/live
curl https://app.example.com/health/ready
```

Frontend:

- Open `https://app.example.com`
- Sign in and verify API calls succeed

## Cost Notes

For learning use, the likely recurring GCP costs are:

- One `e2-micro` VM in a supported US region: often free inside Always Free limits
- 30 GB standard persistent disk: often free inside Always Free limits
- Public IPv4 address on the VM: usually still billed
- Network egress beyond free limits: billed

That means the practical floor is usually a few dollars per month rather than a true zero-cost deployment.

## Important Limits Of This Setup

- Uploads are stored on the VM's attached volume, so this is a single-instance deployment
- Horizontal scaling will require moving uploads and document metadata away from the local filesystem
- The VM deployment path now uses `deploy/gcp/Dockerfile.backend`, which avoids rebuilding the frontend for backend-only deploys

## Cloud Run Migration Plan

Cloud Run is not a clean fit for the default local-storage backend because document uploads are stored on the container filesystem. Document metadata is stored in MongoDB when the database is available and falls back to local sidecar metadata only for offline/local resilience paths.

Current blockers in the codebase:

- `backend/contexts/documents/infrastructure/service.py` selects the configured storage backend
- local storage writes files under `UPLOAD_DIR/photos`, `UPLOAD_DIR/signatures`, and `UPLOAD_DIR/documents`
- `backend/contexts/documents/infrastructure/service.py` reads and writes document metadata under `documents/_meta/*.json`
- `backend/contexts/change_requests/infrastructure/document_lock.py` also reads and writes those metadata JSON files
- `backend/contexts/documents/services/document_service.py` updates metadata by calling internal filesystem helpers directly

Cloud Run instances use ephemeral local storage, so any upload written to disk can disappear when the instance is replaced or scaled.

### Target End State

To run the backend on Cloud Run safely, move to this shape:

- Binary file storage in Google Cloud Storage
- Document metadata and lock state in MongoDB, not JSON sidecar files
- Backend document endpoints continue to serve through `/api/documents/...` so the frontend contract stays stable
- Cloud Run runs only stateless API code

### Recommended Refactor Sequence

#### Phase 1: Introduce A Storage Port

Create a storage abstraction inside the documents context.

Suggested interface responsibilities:

- save photo
- save signature
- save document
- open photo
- open signature
- open document
- delete object
- test object existence

Recommended implementations:

- Local filesystem adapter for current dev and VM deployment
- Google Cloud Storage adapter for Cloud Run

Do not let API or application code call `Path`, `open`, `unlink`, or `FileResponse(path=...)` directly after this phase.

#### Phase 2: Move Metadata To MongoDB

Replace `documents/_meta/*.json` with a MongoDB collection, for example `document_metadata`.

Each document metadata record should contain at least:

- storage key
- category: photo, signature, or document
- original filename
- content type
- file size
- uploaded employee id
- uploaded employee code
- uploaded by user id
- uploaded at
- entity type
- entity id
- lock state
- lock reason
- locked at
- locked by request id

This removes the last filesystem dependency from document locking and metadata reads.

#### Phase 3: Stop Using Filename As The Primary Identifier

Right now the routes and metadata are filename-driven.

That works on local disk, but object storage is safer if you treat filenames as display values and store by generated object keys.

Recommended approach:

- keep public responses compatible by still returning `/api/documents/files/{id}` style URLs
- internally use a generated document id or storage key
- store the original filename separately for downloads and UI display

This avoids collisions and makes future migrations easier.

#### Phase 4: Adapt The HTTP Layer

Update document serving so the API streams bytes from the storage adapter instead of returning local file paths.

That means replacing the current path-based `FileResponse` behavior with streamed responses built from storage reads.

Keep these endpoints stable if possible:

- `/api/documents/photos/{...}`
- `/api/documents/signatures/{...}`
- `/api/documents/files/{...}`
- `/api/documents/files/{...}/download`

Preserving those routes minimizes frontend changes.

#### Phase 5: Add Storage Configuration

Extend settings with Cloud Run-safe storage configuration, for example:

- `DOCUMENT_STORAGE_BACKEND=local|gcs`
- `GCS_BUCKET_NAME`
- `GCP_PROJECT_ID`
- `GOOGLE_APPLICATION_CREDENTIALS` only for local development if needed

On Cloud Run, prefer Workload Identity through the service account instead of key files.

Current status:

- `DOCUMENT_STORAGE_BACKEND` is now implemented with `local` and `gcs` modes
- `GCS_BUCKET_NAME` and `GCP_PROJECT_ID` are now wired in settings
- local mode remains the default for current VM and local development flows
- the route contract remains unchanged while storage is selected behind the documents storage seam

#### Phase 6: Add Migration Script

If you already have uploaded files in local environments or on a VM, write a migration script that:

- scans `uploads/photos`, `uploads/signatures`, and `uploads/documents`
- uploads each object to the target GCS bucket
- reads sidecar metadata JSON when present
- writes canonical metadata records into MongoDB
- marks migrated records idempotently so reruns are safe

#### Phase 7: Update Tests

After the refactor, update or add tests around:

- upload and fetch flows for photos, signatures, and documents
- document ownership enforcement
- approved-document lock behavior
- metadata persistence in MongoDB
- storage adapter behavior with a fake or test double

Pay particular attention to tests under the existing documents and HTTP integration coverage because those routes are already exercised.

### Minimal Code Areas To Change

Expect the main work to center around these files first:

- `backend/contexts/documents/infrastructure/service.py`
- `backend/contexts/change_requests/infrastructure/document_lock.py`
- `backend/contexts/documents/services/document_service.py`
- `backend/app_platform/config/settings.py`
- `backend/contexts/documents/api/router.py`

### Frontend Impact

If the API route shape stays the same, the frontend impact should be small.

The main thing to preserve is the current contract where profile and service-book flows expect URLs such as `/api/documents/photos/...` and `/api/documents/files/...`.

### After The Refactor

Once storage is stateless, the backend can move to:

- Cloud Run for the API
- MongoDB Atlas for MongoDB
- managed static hosting or a dedicated frontend container

At that point the deployment flow becomes much simpler:

- build backend container
- push to Artifact Registry
- deploy to Cloud Run
- grant the Cloud Run service account access to the GCS bucket
- set Cloud Run environment variables for MongoDB, JWT, CORS, and bucket name

### Recommendation

If your goal is to get live quickly, keep the current Compute Engine deployment.

If your goal is to learn modern Google Cloud serverless deployment, the right next implementation task is not deployment itself. It is the document storage refactor above.
