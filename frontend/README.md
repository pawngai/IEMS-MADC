# Frontend (Vite)

This frontend runs on Vite and follows context-owned architecture boundaries.

## Architecture Boundaries

- See `ARCHITECTURE_BOUNDARIES.md` for required import rules and layering.
- Run `npm run lint` to validate boundary compliance.

## Available Scripts

- `npm run dev` or `npm start`: Start Vite dev server.
- `npm run build`: Create production build in `dist/`.
- `npm run preview`: Preview production build locally.
- `npm run test`: Run tests via Vitest.
- `npm run test:watch`: Run tests in watch mode.
- `npm run test:context-boundary:update`: Regenerate `src/contexts/__tests__/fixtures/context-boundary-allowlist.json` from current imports.
- `npm run lint`: Run ESLint.

## Deep-Link Routing

Vite dev server supports SPA fallback for BrowserRouter routes out of the box, so direct navigation and refresh on routes like `/ess/dashboard` and `/admin` resolve to the app shell.

## Workspace Startup Helpers

From workspace root:

```powershell
./start-dev.ps1
```

To force cleanup first:

```powershell
./start-dev.ps1 -ForceStop
```
