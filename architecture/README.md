# Architecture — ABRA Mobile CRM

Technical architecture for an **online-only** mobile CRM backed by **ABRA Gen**.

## Documents

| Document | Description |
|----------|-------------|
| [`principles.md`](principles.md) | Architectural principles |
| [`context.md`](context.md) | System context (C4 level 1) |
| [`online-architecture.md`](online-architecture.md) | Runtime, connectivity, caching rules |
| [`abra-gen-integration.md`](abra-gen-integration.md) | Gen OpenAPI usage and BO mapping |
| [`abra-integration-decision-study.md`](abra-integration-decision-study.md) | **Direct OpenAPI vs thin adapter** (spike-based) |
| [`mobile-crm-api-v1.md`](mobile-crm-api-v1.md) | **Mobile CRM API contract v1** (normative MVP frontend surface) |
| [`mobile-crm-api-v1-adapter-mapping.md`](mobile-crm-api-v1-adapter-mapping.md) | **API v1 ABRA Gen adapter mapping** (spike-validated; non-normative) |
| [`mobile-crm-api-v1-review.md`](mobile-crm-api-v1-review.md) | API v1 review (applied in contract v1.1.0) |
| [`solution-architecture-v1.md`](solution-architecture-v1.md) | **Solution Architecture v1.1** (browser React SPA + adapter; MVP stack) |
| [`development-architecture-v1.md`](development-architecture-v1.md) | **Development Architecture v1** (repo layout, routing, API client, state) |
| [`mvp/solution-overview.md`](mvp/solution-overview.md) | MVP solution sketch (superseded for stack by v1 above) |
| [`reference/`](reference/) | OpenAPI snapshots, diagrams (generated later) |

## Related decisions

- [ADR 0001](../docs/decisions/0001-abra-gen-source-of-truth.md) — Gen source of truth
- [ADR 0002](../docs/decisions/0002-online-only-architecture.md) — Online only
- [ADR 0003](../docs/decisions/0003-documentation-first.md) — Docs first

## Next architecture tasks

- [ ] Confirm ABRA Gen version (26+ recommended; follow header `expand` rules)
- [x] Choose mobile client stack — [ADR 0006](../docs/decisions/0006-frontend-technology.md), [development-architecture-v1.md](development-architecture-v1.md)
- [x] Decide direct Gen vs adapter — see [integration decision study](abra-integration-decision-study.md) (ADR 0004 proposed)
- [ ] Map MVP features to OpenAPI operations with `select` / `where` examples
- [ ] Auth: OAuth / API key / Gen session — document threat model
