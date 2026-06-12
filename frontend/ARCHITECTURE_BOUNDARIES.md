# Frontend Context Boundaries

This frontend follows module-owned boundaries (one `src/modules/<module>` per backend bounded context).

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

Use context-owned entrypoints under `@/modules/*`.

### 2) Shared layer must stay context-agnostic

For `src/shared/**`:

- Do **not** import `@/modules/*/api/*`
- Do **not** import `@/modules/*/ui/*`

If shared needs domain behavior, create a small adapter in a context `model` layer and call that adapter.

## Current Enforcement

ESLint enforces these rules in `eslint.config.js` via `no-restricted-imports`:

- Block `@/features/*` in `src/{lib,hooks,shared}/**` (shared/hook layers must use context entrypoints).
- Block `@/modules/*/api/*` in `src/app/{providers,router,layouts}/**` (app must use context model/ui adapters).
- Block `@/modules/*/api/*` in `src/hooks/**` (hooks must use context model adapters).
- Block `@/features/*` in `src/modules/**/__tests__/*` (context tests must target context contracts).
- Block `@/features/*` in `src/modules/**` (context modules must not import feature modules).
- Block `@/modules/*/api/*` and `@/modules/*/ui/*` in `src/shared/**` (shared layer stays context-agnostic).
- Block `@/modules/*` and `@/features/*` in `src/shared/ui/**` (shared UI stays dumb).

## Enforcement Matrix

- `src/app/{providers,router,layouts}/**`
	- ❌ `@/modules/*/api/*`
- `src/{lib,hooks,shared}/**`
	- ❌ `@/features/*`
- `src/hooks/**`
	- ❌ `@/modules/*/api/*`
- `src/shared/**`
	- ❌ `@/features/*`
	- ❌ `@/modules/*/api/*`
	- ❌ `@/modules/*/ui/*`
- `src/shared/ui/**`
	- ❌ `@/modules/*`
	- ❌ `@/features/*`
- `src/modules/**/__tests__/*`
	- ❌ `@/features/*`
- `src/modules/**`
	- ❌ `@/features/*`

## Recommended Structure

- `src/modules/<context>/api/*` for HTTP contracts.
- `src/modules/<context>/model/*` for adapters and domain-facing helpers.
- `src/modules/<context>/pages/*` and `src/modules/<context>/components/*` for context-owned UI entrypoints.

## Target Top-Level Directories

- `src/app`
- `src/modules`
- `src/platform`
- `src/shared`

## Practical Pattern

- Good: `src/app/router/*` imports `@/modules/*/pages/*`
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
