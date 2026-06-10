# Frontend Context Boundaries

This frontend follows context-owned boundaries aligned with backend bounded contexts.

## Purpose

- Keep app composition stable while features evolve.
- Prevent cross-module coupling from bypassing context entrypoints.
- Ensure frontend ownership matches backend context ownership.

## Import Rules

### 1) App shell must use context entrypoints

For these layers:

- `src/app/**`
- `src/shared/**`
- `src/platform/**`

Do **not** import `@/features/*` directly.

Use context-owned entrypoints under `@/contexts/*`.

### 2) Shared layer must stay context-agnostic

For `src/shared/**`:

- Do **not** import `@/contexts/*/api/*`
- Do **not** import `@/contexts/*/ui/*`

If shared needs domain behavior, create a small adapter in a context `model` layer and call that adapter.

## Current Enforcement

ESLint enforces these rules in `eslint.config.js` via `no-restricted-imports`:

- Block `@/features/*` in `src/{lib,hooks,shared}/**` (shared/hook layers must use context entrypoints).
- Block `@/contexts/*/api/*` in `src/app/{providers,router,layouts}/**` (app must use context model/ui adapters).
- Block `@/contexts/*/api/*` in `src/hooks/**` (hooks must use context model adapters).
- Block `@/features/*` in `src/contexts/**/__tests__/*` (context tests must target context contracts).
- Block `@/features/*` in `src/contexts/**` (context modules must not import feature modules).
- Block `@/contexts/*/api/*` and `@/contexts/*/ui/*` in `src/shared/**` (shared layer stays context-agnostic).
- Block `@/contexts/*` and `@/features/*` in `src/shared/ui/**` (shared UI stays dumb).

## Enforcement Matrix

- `src/app/{providers,router,layouts}/**`
	- ❌ `@/contexts/*/api/*`
- `src/{lib,hooks,shared}/**`
	- ❌ `@/features/*`
- `src/hooks/**`
	- ❌ `@/contexts/*/api/*`
- `src/shared/**`
	- ❌ `@/features/*`
	- ❌ `@/contexts/*/api/*`
	- ❌ `@/contexts/*/ui/*`
- `src/shared/ui/**`
	- ❌ `@/contexts/*`
	- ❌ `@/features/*`
- `src/contexts/**/__tests__/*`
	- ❌ `@/features/*`
- `src/contexts/**`
	- ❌ `@/features/*`

## Recommended Structure

- `src/contexts/<context>/api/*` for HTTP contracts.
- `src/contexts/<context>/model/*` for adapters and domain-facing helpers.
- `src/contexts/<context>/pages/*` and `src/contexts/<context>/components/*` for context-owned UI entrypoints.
- `src/features/*` for implementation details behind context wrappers.
- `src/portals/*` for portal-specific composition that imports contexts only through public context index contracts.

## Target Top-Level Directories

- `src/app`
- `src/contexts`
- `src/features`
- `src/platform`
- `src/portals`
- `src/shared`

## Practical Pattern

- Good: `src/app/router/*` imports `@/contexts/*/pages/*`
- Good: `src/shared/*` imports only shared utilities/components (or context model adapters if needed)
- Avoid: direct `@/features/*` imports from app shell/shared layers

## Route And Capability Gates

- Use `ProtectedRoute` for route-level permission, authority, and optional module gates.
- Keep backend write safety in the owning context; frontend module access is a visibility/routing signal, not an authorization substitute.
- Authorities such as `GLOBAL_DATA_ENTRY` are roles, permissions such as `PROFILE_CREATE` are action grants, and module ids such as `data_entry` are visibility flags from `/api/auth/module-access`.
- Global Employee Directory create actions for regular and non-regular employees are gated by authority plus `PROFILE_CREATE`, not by the `data_entry` module flag.

## Validation

Run:

```bash
npm run lint
```

Boundary violations fail lint.
