# AGENTS.md

## Architecture rules
- Use bounded contexts only.
- EmployeeIdentity owns canonical employee identity.
- EmployeeProfile owns employee profile enrichment and projections.
- ServiceBook owns the current service-history runtime under `service_book/records`.
- There is no standalone `service_events` bounded context in the current implementation.
- Only regular employees have ServiceBook.
- No cross-context DB writes.
- shared_kernel contains primitives only, never business logic.

## Refactor rules
- Prefer moving/renaming/restructuring over layering adapters on bad code.
- Split large files by responsibility.
- Keep APIs thin.
- Put business logic in domain/services.
- Delete dead code and duplicates.
- Fix imports immediately after file moves.

## Frontend rules
- Organize by feature/domain.
- Keep domain logic near the feature.
- Shared UI must be domain-agnostic.

## Completion rules
- Run tests after major rewrites.
- Add architecture checks.
- End with a migration summary and risk list.
