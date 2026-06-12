---
name: run-dev-stack
description: Launch the IEMS-MADC dev stack (Mongo + FastAPI backend + Vite frontend) and drive it in a browser with seeded role logins for smoke-testing frontend changes.
---

# Run the IEMS-MADC dev stack

## Check what's already running

All three servers may already be up (the team often leaves them running):

```powershell
Get-NetTCPConnection -LocalPort 27017,8000,3000 -State Listen -ErrorAction SilentlyContinue
```

- 27017 = MongoDB, 8000 = FastAPI backend, 3000 = Vite frontend.
- Probe health: `curl http://127.0.0.1:8000/docs` and `curl http://localhost:3000/` should both return 200.

## Launch (only what's missing)

The repo launcher is `start-dev.ps1` (spawns two PowerShell windows; needs
`-ExecutionPolicy Bypass`, which automated runs may not be allowed to pass).
Direct background launches are equivalent and policy-clean:

**Mongo** (if not listening): `powershell -File start-mongo-local.ps1` or start the MongoDB Windows service.

**Backend** (from repo root, Git Bash syntax; JWT_SECRET must be ≥32 chars — `uuidgen` is NOT available in Git Bash, use a literal):

```bash
JWT_SECRET="dev-only-jwt-secret-for-local-smoke-testing-0123456789abcdef" \
MONGO_URL="mongodb://localhost:27017" DB_NAME="iems_db" \
IEMS_SEED_ADMIN_PASSWORD="iemsadmin123" \
.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

**Frontend** (from `frontend/`):

```bash
REACT_APP_BACKEND_URL="http://127.0.0.1:8000" npm run dev -- --host 0.0.0.0 --port 3000
```

Run both in the background; backend is ready when `/docs` returns 200 (~10s).

## Seeded dev logins (dev DB `iems_db` only)

| Role | Email | Password |
|---|---|---|
| System Admin | admin@madc.gov.in | iemsadmin123 (only if seeded via `IEMS_SEED_ADMIN_PASSWORD`) |
| Global Data Entry | global.dataentry@madc.gov.in | dataentry123 |
| Verifier | verifier@madc.gov.in | verifier123 |
| Approving Authority | hoo@madc.gov.in | hoo123 |
| Dealing Clerk | dealing.clerk@madc.gov.in | dealing123 |
| Auditor | auditor@madc.gov.in | auditor123 |
| Employee (smoke) | smoke.employee@madc.gov.in | employee123! (manually created; linked to MADC-0083) |

No HOD/department-scoped login is seeded; department portal pages can only be verified via unit tests.

## Drive it with Playwright

Playwright is not a project dependency; install transiently and remove after:

```bash
cd frontend && npm i --no-save playwright   # chromium already cached in %LOCALAPPDATA%/ms-playwright
node smoke.mjs
npm uninstall --no-save playwright && rm smoke.mjs smoke-*.png
```

Smoke script skeleton (login form fields are `input[type=email]` / `input[type=password]`, submit is `button[type=submit]`):

```js
import { chromium } from "playwright";
const b = await chromium.launch(); const p = await b.newPage();
const errs = []; p.on("pageerror", (e) => errs.push(String(e)));
await p.goto("http://localhost:3000/login", { waitUntil: "networkidle" });
await p.fill('input[type="email"]', "global.dataentry@madc.gov.in");
await p.fill('input[type="password"]', "dataentry123");
await p.click('button[type="submit"]');
await p.waitForTimeout(3000); // role-aware redirect via DefaultLanding
// useful testids: [data-testid="sidebar"], nav-*, user-menu-trigger, logout-btn
await p.screenshot({ path: "smoke-01.png" });
console.log("pageerrors:", errs);
await b.close();
```

**Look at the screenshots** — a blank frame means the page failed to render.

## Known noise

- An anonymous visit to a protected path logs one `400` on `/api/auth/refresh` — that is the designed silent-refresh attempt; it correctly ends at `/login`.
- `vite build` warns about chunk size; exit code 0 is what matters.
