# ABRA Gen integration

**Status:** Draft — BO mapping incomplete until workshop  
**Binding rule:** ABRA Gen is the only source of truth (ADR 0001).

## Connection model

| Setting | Description |
|---------|-------------|
| Base URL | `https://<host>/<connection>/` per Gen deployment |
| Auth | BFF session to mobile; adapter → Gen per customer (Basic/Bearer) — see [solution-architecture-v1.md](solution-architecture-v1.md) §8 |
| API spec | OpenAPI 3 from Gen `api-docs` |

Store environment-specific values in `config/` templates only — never commit secrets.

## API usage rules (ABRA 26+ aligned)

Follow patterns proven on ABRA Gen **26.0+** (see sibling project `abra26-api-baseline`):

1. **Read** header and nested data with `GET` + `select` + `expand`.
2. **List / search** on collection root with `where`, `orderBy`, `take`.
3. **Create / update** nested collections on the **header** business object with `POST` / `PUT` and `?validation=true`.
4. **Never** rely on removed collection sub-paths (404 on 26+).

## MVP resource mapping (draft)

Business-level mapping (no endpoints): [`../analysis/domain/gen-business-object-mapping.md`](../analysis/domain/gen-business-object-mapping.md).

| Mobile CRM entity | Gen object (expected) | Business CRUD (mobile) |
|-------------------|----------------------|-------------------------|
| Firm | `Firm` | R |
| Contact | **TBD** | R (MVP) |
| Activity | **TBD** | R, C, U |
| Commercial health | Derived from Firm + finance | R |
| My Day | Composite over Activity | — |

Replace **TBD** via OpenAPI validation backlog (OQ-* in mapping doc).

## Example query shape (illustrative)

```http
GET /{connection}/firm?select=ID,Name,ICO&where=Name like '*{term}*'&take=20&orderBy=Name
```

Exact field names must match OpenAPI for the customer’s Gen version and customization.

## DTO and naming

- Use **exact JSON property names** from Gen responses in integration layer (same approach as Material Cutting `storecard_fields`).
- Map to UI-friendly labels in presentation layer only.

## Integration architecture

**Decision study (2026-06-04):** [abra-integration-decision-study.md](abra-integration-decision-study.md) — recommends a **thin ABRA Adapter** for MVP and Phase 2 based on activity, contact, and identity spikes. ADR: [0004-thin-abra-adapter.md](../docs/decisions/0004-thin-abra-adapter.md).

**Frontend contract:** [mobile-crm-api-v1.md](mobile-crm-api-v1.md) — CRM-oriented `/api/v1` surface (normative for mobile).

**Adapter mapping:** [mobile-crm-api-v1-adapter-mapping.md](mobile-crm-api-v1-adapter-mapping.md) — Gen BOs, fields, spike constraints (implementers only).

## OpenAPI reference artefacts

Place audited snapshots under:

```text
architecture/reference/openapi/
```

Regenerate via `scripts/` (to be added). Do not commit large dumps unless team policy requires; `.gitignore` excludes JSON by default.

## Permissions

- Service account vs per-user Gen identity — **decision required** (ADR).
- Mobile features must fail if Gen denies object access (no client-side-only security).

## Version matrix

| Environment | Gen version | OpenAPI hash | Verified by |
|-------------|-------------|--------------|-------------|
| DEV (localhost DEMO) | 26.x DEMO | 521 controllers (2026-06-04) | [spike](reference/spike/README.md) |
| PROD | TBD | TBD | |
