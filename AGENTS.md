# Agent instructions — ABRA Mobile CRM

## Project intent

Build a **mobile CRM** for **field sales representatives**. **ABRA Gen** is the only source of truth for business data. **MVP scope** and **online-only** architecture are binding until explicitly changed via ADR.

## Before writing code

1. Read [`analysis/requirements/mvp-scope.md`](analysis/requirements/mvp-scope.md).
2. Read [`architecture/principles.md`](architecture/principles.md) and [`architecture/abra-gen-integration.md`](architecture/abra-gen-integration.md).
3. Check [`docs/decisions/`](docs/decisions/) for accepted decisions.
4. Update documentation first when behaviour or scope changes.

## Do not

- Introduce a local authoritative database for firms, contacts, orders, or stock.
- Design offline-first sync, conflict resolution, or background replication of Gen entities.
- Add features outside MVP without updating `mvp-scope.md` and an ADR or scope note.
- Call deprecated ABRA Gen collection sub-paths; follow OpenAPI and [`architecture/abra-gen-integration.md`](architecture/abra-gen-integration.md).

## Preferred locations

| Work | Location |
|------|----------|
| Business rules & scope | `analysis/` |
| Technical design | `architecture/` |
| ADRs | `docs/decisions/` |
| Application code (when started) | `src/` |
| Tests | `tests/` |

## Conventions

- Match existing doc tone: precise, Czech/Slovak business terms where established in glossary.
- Keep diffs minimal; no speculative application code in doc-only tasks.
