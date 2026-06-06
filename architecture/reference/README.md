# Architecture reference artefacts

Store **non-secret** reference material supporting Gen integration.

## OpenAPI

- Directory: `openapi/`
- Add `.gitkeep` until first audited export
- Prefer scripted export documented in `scripts/README.md`

## Discovery spike (2026-06-04)

Run against configured server — see [`spike/README.md`](spike/README.md):

- [business-object-inventory.md](spike/business-object-inventory.md)
- [crm-object-validation.md](spike/crm-object-validation.md)
- [gap-analysis.md](spike/gap-analysis.md)

## Diagrams

- Source: Mermaid in markdown (preferred) or exported PNG in `diagrams/` if needed

## Do not store here

- Production credentials
- Full production database exports
- Customer PII samples
