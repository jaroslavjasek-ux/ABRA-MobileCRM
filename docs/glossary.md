# Glossary — ABRA Mobile CRM

Terms used consistently across analysis and architecture. Align names with **ABRA Gen** OpenAPI / UI where possible.

| Term | Definition |
|------|------------|
| **ABRA Gen** | ERP system of record. All authoritative business entities and documents. |
| **Field sales representative** | Mobile user visiting customers, logging activities, and creating/updating sales documents. |
| **Firm** | Customer / business partner in ABRA Gen (`Firm` BO). |
| **Contact** | Person linked to a firm. |
| **Activity** | Planned or completed customer interaction (visit, call, task). See [domain model](../analysis/domain/business-domain-model.md). |
| **Sales offer** | Quotation / non-binding proposal to a firm (Phase 2). |
| **Sales order** | Binding customer order document (Phase 2). |
| **Mobile CRM** | This product: mobile-optimised UI over Gen data for field sales. |
| **MVP** | Minimum viable first release; see [mvp-scope.md](../analysis/requirements/mvp-scope.md). |
| **Online-only** | Core flows require live connectivity to ABRA Gen; no offline master replica. |
| **OpenAPI** | ABRA Gen Web API specification; contract for integration. |
| **BFF** | Optional backend-for-frontend; thin orchestration only, not a second source of truth. |

## Domain reference

- Entities, hubs, permissions: [`analysis/domain/business-domain-model.md`](../analysis/domain/business-domain-model.md)
- ABRA Gen object mapping: [`analysis/domain/gen-business-object-mapping.md`](../analysis/domain/gen-business-object-mapping.md)

## Placeholders (confirm during analysis)

| Working name | To confirm in Gen |
|--------------|---------------------|
| Sales visit | Same as Activity or separate calendar object (see domain model §12 D-01) |
| Pipeline stage | Sales opportunity stage (Phase 2) |
