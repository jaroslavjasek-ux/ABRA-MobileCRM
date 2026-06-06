# Architecture Decision Records (ADR)

Lightweight decision log for ABRA Mobile CRM.

## Format

Each ADR is numbered `NNNN-short-title.md` with:

- **Status:** Proposed | Accepted | Superseded
- **Context** — problem and constraints
- **Decision** — what we chose
- **Consequences** — positive and negative follow-ups

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-abra-gen-source-of-truth.md) | ABRA Gen as sole source of truth | Accepted |
| [0002](0002-online-only-architecture.md) | Online-only architecture | Accepted |
| [0003](0003-documentation-first.md) | Documentation-first delivery | Accepted |
| [0004](0004-thin-abra-adapter.md) | Thin ABRA Adapter for Gen integration | Proposed |
| [0005](0005-solution-architecture-v1.md) | Solution Architecture v1 (MVP stack) | Accepted |
| [0006](0006-frontend-technology.md) | Frontend technology — browser web app (React SPA) | Accepted v2 |

## When to add an ADR

- Choosing mobile stack, auth model, or BFF vs direct Gen calls
- Changing MVP boundaries or offline behaviour
- Adopting a new Gen API pattern (e.g. ABRA 26+ header expand rules)
