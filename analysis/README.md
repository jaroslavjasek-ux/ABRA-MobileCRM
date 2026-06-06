# Business analysis — ABRA Mobile CRM

Business analysis artefacts for field sales CRM. Outputs feed architecture and MVP implementation.

## Contents

| Path | Description |
|------|-------------|
| [`personas/field-sales-representative.md`](personas/field-sales-representative.md) | Primary user persona |
| [`requirements/mvp-scope.md`](requirements/mvp-scope.md) | **Binding** MVP in/out scope |
| [`requirements/functional-overview.md`](requirements/functional-overview.md) | Capability map (post-MVP marked) |
| [`requirements/non-functional.md`](requirements/non-functional.md) | Quality attributes |
| [`user-journeys/README.md`](user-journeys/README.md) | Journey templates and index |
| [`screens/README.md`](screens/README.md) | **MVP screen inventory** (one file per screen) |
| [`domain/business-domain-model.md`](domain/business-domain-model.md) | **Business domain model** (entities, ownership, permissions) |
| [`spikes/crmactivities-lifecycle.md`](spikes/crmactivities-lifecycle.md) | **CRM activities** lifecycle validation spike |
| [`spikes/contact-model.md`](spikes/contact-model.md) | **Contact model** validation spike (`persons` / `firmperson`) |
| [`spikes/sales-representative-model.md`](spikes/sales-representative-model.md) | **Sales rep identity** spike (`currentuser` / `securityusers`) |
| [`stakeholders.md`](stakeholders.md) | Roles and interests |

## Workflow

1. Validate persona and journeys with sales leadership.
2. Freeze MVP scope in workshop → update `mvp-scope.md`.
3. Hand off Gen BO mapping to architecture (`architecture/abra-gen-integration.md`).

## Out of scope here

Technical API patterns, deployment, and mobile stack — see [`../architecture/`](../architecture/).
