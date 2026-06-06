# Review — Mobile CRM API Contract v1

**Reviewed:** [`mobile-crm-api-v1.md`](mobile-crm-api-v1.md) v1.0.0  
**Applied in:** contract v1.1.0 + [`mobile-crm-api-v1-adapter-mapping.md`](mobile-crm-api-v1-adapter-mapping.md)  
**Date:** 2026-06-04  
**Scope:** MVP unchanged — refinements only

---

## 1. Executive summary

The contract successfully separates **CRM-facing** paths from Gen BO names in the main endpoint definitions, but **several sections still leak ABRA/Gen into the frontend contract surface**. A few endpoints and fields mirror **Gen-specific concepts** (`handedOver`, `activityTypeId`, validate-then-commit semantics) that would complicate **offline** or **multi-ERP** backends without v2 breaking changes.

**Recommendation:** Apply the refinements in §6 (documentation and minor contract tweaks) without adding endpoints or screens.

---

## 2. Endpoints that are ABRA-specific

These endpoints are **justified for MVP** (thin adapter over Gen) but are **not ERP-neutral** — another backend would need equivalent concepts or a different v1 shape.

| Endpoint | Why ABRA-specific | ERP-neutral alternative (future) |
|----------|-------------------|----------------------------------|
| **`GET /activity-types`** | Tied to Gen `crmactivitytypes` code list (`Tel`, …). Not all ERPs expose a separate activity type catalogue with opaque ids. | `GET /reference/activity-categories` or embed types in save form schema |
| **`GET /my-day`** | Semantics assume Gen **crmactivities** + `SheduledStart$DATE` + tri-field ownership OR (`Responsible`/`Solver`/`Created`). | `GET /agenda` with generic `workItemType=customerActivity` |
| **`POST` / `PUT /activities`** | Validate-then-commit, merge `ActQueue_ID` / `Period_ID` / `X_*` suppression — Gen lifecycle spike only. | Single-shot create with server-side defaults; idempotent `PATCH` |
| **`GET /firms/{firmId}`** (contacts) | Contacts only via **`firmpersons`** nested on firm read; no standalone contact-by-firm query. | `GET /customers/{id}/contacts` backed by any junction model |
| **`GET /session`** | Maps to Gen **`currentuser`** + **`securityusers`** (+ optional **`employees`**). | Standard OIDC/JWT claims + `/me` profile |
| All read/write on **`/activities`** | Object is Gen **crmactivity**, not generic Task/Interaction. | Resource naming could be `/customer-interactions` in a neutral API |

**Least ABRA-specific (good CRM shape):**

- `GET /firms`, `GET /firms/{firmId}` (customer hub)
- `GET /contacts/{contactId}`
- Session resource pattern (if auth is abstracted)

---

## 3. Endpoints and fields that expose implementation details

Items the **mobile client can see today** that reveal Gen/adapter internals (should be adapter-only or appendix-only).

### 3.1 In the normative contract (move or soften)

| Location | Leak | Refinement |
|----------|------|------------|
| §4.3 enum table | Column **"Gen source (adapter mapping)"** with `crmactivity.Status`, `pmstate` | Move table to **Appendix A**; keep §4.3 values-only for frontend |
| §4.4 `GEN_UNAVAILABLE` | Names the ERP in error code | Rename to **`BACKEND_UNAVAILABLE`** or **`SERVICE_UNAVAILABLE`**; map Gen in adapter docs only |
| §4.1 | **"max length 10 on DEMO"** | Replace with **"opaque string; format deployment-specific"** |
| §5.1 `employeeNumber` | Exposes Gen HR **`employees`** link | Optional field; document as **organisational metadata** or drop from v1 client types |
| §5.3 `positionIndex` | Direct echo of **`firmperson.PosIndex`** | Hide from client; use **`isPrimary`** + server sort only |
| §5.3 `isPrimary` rule text | **`initialFirmPersonId`**, **`0000000000`** placeholder | Remove placeholder id from contract; say "server-derived primary flag" |
| §5.6 `ActivityTypeOption.code` | Gen **`crmactivitytypes.Code`** (`Tel`) | Client only needs `id` + `name`; drop `code` from public type or mark optional/internal |
| §6.2.1 | Gen field names in **ownership rule** | Move to §8 / adapter spec only; public rule: **"owned by session representative"** |
| §6.5 POST validation rules 1–7 | **`ActQueue_ID`, `X_*`, `ResponsibleCustomerPerson_ID`, `@meta.validation`** | Move to **Adapter implementation requirements** annex; client sees only `422` + `details[]` |
| §6.5 `answer` vs `description` | Mirrors Gen **`Answer`** / **`Description`** split | Acceptable if documented as CRM domain; alias **`outcome`** in v1.1 for neutrality |
| `ActivityStatus.handedOver` | Gen status **3 = Odovzdané** — rare in generic CRM | Keep for MVP parity with Gen; note in review as ERP-specific enum value |
| `registrationNumber` + comment **IČO** | SK-localised Gen field | Use neutral **`businessRegistrationNumber`** in API; map ICO in adapter |
| `connectionLabel` on session (§2) | Gen **connection** path hint | Restrict to **non-production** response extension documented in ops guide, not OpenAPI |

### 3.2 ABRA mapping blocks per endpoint (acceptable placement)

§6 **ABRA mapping** tables under each endpoint are correct for **adapter implementers** but should be clearly labelled **non-normative for frontend** (e.g. collapsible appendix or separate `mobile-crm-api-v1-gen-mapping.md`) so OpenAPI generators do not surface them to app teams.

### 3.3 Duplication that hints at Gen read patterns

| Pattern | Issue |
|---------|--------|
| `GET /firms/{firmId}/contacts` vs contacts on firm detail | Exposes that contacts are not first-class list API — implementation uses second full firm GET |
| `activityTypeId` required on create | Client must prefetch Gen catalogue ids |
| `firmId` required on PUT | Gen header PUT pattern leaked as API rule |

---

## 4. Future offline challenges

ADR 0002 excludes offline for MVP; the v1 contract still shapes what a **future offline ADR** must undo or extend.

| Challenge | Root cause in v1 | Future implication |
|-----------|------------------|-------------------|
| **No local entity graph** | Aggregates (`MyDayResponse`, `FirmDetailResponse`) are read-only composites | Need versioned local entities + sync metadata (`updatedAt`, `etag`) |
| **Opaque Gen ids** | `firmId`, `activityTypeId` are meaningless offline without prior sync | Seed catalogues (activity types, firms) on connect; handle stale id invalidation on sync |
| **Validate-then-commit create** | POST may need two Gen hops; 201 vs 200 unclear (OQ-LC-01) | Offline queue must store **intent** + replay; conflict on `ObjVersion` not in v1 contract |
| **Ownership OR rule** | Server-side only; client does not send filter | Cached My Day must replicate same OR logic or trust server sync endpoint |
| **`GEN_UNAVAILABLE` / no queue** | Writes fail hard | Need `POST /sync/outbox` or accept draft-local-only UX (new ADR) |
| **`isOverdue` server-derived** | Client cannot recompute without timezone + status rules | Document timezone in contract or return `scheduledStart` only and derive client-side |
| **No `ETag` / `version` on activities** | Gen `ObjVersion` not exposed | Optimistic concurrency required for offline replay |
| **Contact list only via firm** | Cannot refresh contacts without firm blob | Offline contact picker needs cached `firmId → contacts[]` from last online fetch |
| **Pull-to-refresh = full refetch** | No delta APIs | `GET /my-day?since=` or sync cursor in v2 |
| **Search `GET /firms?q=`** | No local index API | Offline search needs local FTS index built from last sync |
| **Handed-over status** | Ambiguous for "open work" offline filters | Product rule for whether handed-over appears in overdue |

---

## 5. Future multi-ERP challenges

If Mobile CRM must support **Gen + another ERP** (or Gen cloud vs on-prem variants), v1 coupling points:

| Coupling | v1 manifestation | Multi-ERP impact |
|----------|------------------|------------------|
| **Resource names** | `/activities`, `/firms` | Gen uses crmactivities/firms; SAP/D365 use different nouns — need neutral `/customers`, `/interactions` or provider facade |
| **Activity type catalogue** | `GET /activity-types` | Per-ERP catalogues; ids not portable |
| **Status enum** | Four values including `handedOver` | Map per ERP or reduce to `open`/`completed`/`cancelled` in neutral core |
| **Contact model** | Firm-nested contacts, `positionIndex`, `isPrimary` rules | SAP Business Partner vs Gen firmperson — different junction |
| **Commercial health** | `CommercialHealth` on firm | Finance modules differ wildly; optional plugin per ERP |
| **Auth** | Basic/Bearer → Gen | Other ERPs need OAuth2/OIDC-only; `POST /session` body differs |
| **Error `GEN_UNAVAILABLE`** | ERP-specific branding | Need `providerId` + generic errors |
| **Rep identity** | `representative.id` = security user | Other systems use workforce GUID / email subject |
| **Write semantics** | `mode: complete` + `status: completed` | Some ERPs use separate "close" operations or state machines |
| **Pagination** | `take`/`skip` (Gen OData-like) | Cursor-based paging for other APIs |
| **Tax/registration fields** | ICO/DIC naming | Country-specific; config-driven field map per deployment |
| **Pipeline stub** | `pipelineSnapshot` on firm | Gen busorders; other ERP Opportunity object — already nullable stub |

**Thin adapter per ERP** (ADR 0004) absorbs most mapping; the **contract** should avoid encoding Gen-only rules in normative client-facing sections so a second adapter implements the same DTOs.

---

## 6. Suggested refinements (MVP scope unchanged)

No new screens, paths, or MVP features. Documentation and small contract clarifications only.

### 6.1 Document structure

| Action | Detail |
|--------|--------|
| **Split normative vs adapter** | `mobile-crm-api-v1.md` = frontend + OpenAPI; move §6 ABRA mapping blocks + §8 to **`mobile-crm-api-v1-adapter-mapping.md`** |
| **Add § "Normative boundary"** | State: anything under §6 mapping / §8 is **not** part of the frontend contract |
| **Add review appendix** | Link this review from contract §11 |

### 6.2 Error and auth

| Current | Refined |
|---------|---------|
| `GEN_UNAVAILABLE` | `SERVICE_UNAVAILABLE` (502/503) |
| Auth: "must match Gen deployment" | "Must match **backend** deployment configured for this tenant" |
| §4.4 mentions `@meta.validation` | Remove; say "field-level errors from server validation" |

### 6.3 Types (non-breaking clarifications)

| Field | Refinement |
|-------|------------|
| `ContactSummary.positionIndex` | **Remove from public schema** (server sort only) |
| `ActivityTypeOption.code` | Optional; not required for UI |
| `ActivitySaveRequest.mode` | Document as **server-controlled** discriminator; client sends but adapter may infer from HTTP method in v1.1 |
| `ActivitySummary.activityTypeId` | Keep; required for Gen — document as **external catalogue reference** |
| Add `meta.schemaVersion` on large responses | Optional string ` "1.0"` for forward-compatible clients (no behaviour change) |

### 6.4 Endpoint behaviour (wording only)

| Endpoint | Refinement |
|----------|------------|
| `GET /my-day` | Normative: "activities owned by authenticated representative for date"; move Gen OR to adapter doc |
| `POST /activities` | Normative: "creates customer activity"; single sentence: "Server may run multi-step validation against ERP" — no field names |
| `GET /firms/{firmId}` | Mark `recentActivities` and `commercialHealth` as **`availability: bestEffort`** in response meta (still allowed empty) |
| `GET /firms/{firmId}/contacts` | Note in contract: "Subset of firm detail contacts; may duplicate `GET /firms/{id}` data" — avoid implying independent contact service |

### 6.5 Future-proof hooks (optional fields, no new endpoints)

Add optional response fields (always nullable, no MVP UI requirement):

| Field | Where | Purpose |
|-------|-------|---------|
| `lastModifiedAt` | `ActivityDetail`, `FirmDetail` | Offline/v2 without breaking clients |
| `capabilities[]` | `SessionResponse` | e.g. `["activities.write","firms.read"]` — abstracts Gen permissions |
| `provider` | `SessionResponse` | `{ "name": "abra-gen", "version": "26.x" }` for support; not required in UI |

### 6.6 Enum neutralisation (documentation only)

Keep same enum values for Gen mapping, but add note:

- **`handedOver`**: "May be hidden from overdue/today filters in MVP UI."
- Map **`cancelled`** in v2 if Gen adds or maps from other states — not in v1.

### 6.7 Commercial health

Keep optional `commercialHealth` on firm detail (SCR-004 domain requirement) but add:

> MVP: section may be `null`. Populated only when deployment enables finance signals. **Not** part of offline-critical path.

---

## 7. Endpoint classification matrix

| Endpoint | CRM-neutral? | ABRA-specific? | Implementation leak in v1 doc? |
|----------|:------------:|:--------------:|:------------------------------:|
| `POST /session` | Partial | High (Gen auth) | Medium |
| `GET /session` | Partial | High | Low |
| `DELETE /session` | Yes | Low | Low |
| `GET /my-day` | Yes (concept) | High (filters) | High (§6.2.1 Gen fields) |
| `GET /firms` | Yes | Medium (Hidden) | Low |
| `GET /firms/{id}` | Yes | Medium (firmperson) | Medium (primary rule ids) |
| `GET /contacts/{id}` | Yes | Medium (person) | Low |
| `GET /firms/{id}/contacts` | Yes | High (read pattern) | Medium |
| `GET /activities/{id}` | Yes | High (crmactivity) | Low |
| `POST /activities` | Yes | High (validate) | High (validation rules) |
| `PUT /activities/{id}` | Yes | High | Medium |
| `GET /activity-types` | Partial | High | Medium (`code`) |

---

## 8. Document history

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-06-04 | Initial review of API contract v1.0.0 |
| 0.2 | 2026-06-04 | Marked applied in contract v1.1.0 and adapter mapping split |
