# Documentation index — ABRA Mobile CRM

Central index for project documentation. **Documentation leads implementation.**

## Structure

| Area | Path | Purpose |
|------|------|---------|
| Business analysis | [`../analysis/`](../analysis/) | Personas, MVP scope, requirements, user journeys, [screen inventory](../analysis/screens/README.md) |
| Architecture | [`../architecture/`](../architecture/) | Context, online model, ABRA Gen integration |
| Decisions (ADR) | [`decisions/`](decisions/) | Recorded architecture and product decisions |
| Development | [`development/`](development/) | Git workflow, local setup (when code exists) |
| Glossary | [`glossary.md`](glossary.md) | Terms and ABRA Gen object names |

## Reading order (new contributors)

1. [Project README](../README.md)
2. [MVP scope](../analysis/requirements/mvp-scope.md)
3. [Business domain model](../analysis/domain/business-domain-model.md)
4. [Architecture principles](../architecture/principles.md)
5. [Solution overview (MVP)](../architecture/mvp/solution-overview.md)
6. [ABRA Gen integration](../architecture/abra-gen-integration.md)
7. ADRs in [`decisions/`](decisions/)

## Maintaining docs

- **Scope change** → update `analysis/requirements/mvp-scope.md` and add or amend an ADR.
- **API / Gen behaviour** → update `architecture/abra-gen-integration.md` and link OpenAPI evidence under `architecture/reference/`.
- **New term** → add to [`glossary.md`](glossary.md).

## Status

| Document set | Status |
|--------------|--------|
| Analysis (MVP) | Draft — ready for workshop |
| Architecture (MVP) | Draft — ready for review |
| ADRs (0001–0003) | Accepted |
| Source & tests | Not started |
