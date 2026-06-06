# Mobile CRM API Contract v1

**Status:** Draft  
**Version:** 1.1.0  
**Date:** 2026-06-04  
**Audience:** Mobile client (frontend), OpenAPI consumers  
**Scope:** MVP screens SCR-001–SCR-010 only (see [screen inventory v0.2](../analysis/screens/README.md))

**Implements:** [ADR 0004 — Thin ABRA Adapter](../docs/decisions/0004-thin-abra-adapter.md) · [Integration decision study](abra-integration-decision-study.md)

**Adapter implementation (non-normative):** [`mobile-crm-api-v1-adapter-mapping.md`](mobile-crm-api-v1-adapter-mapping.md)

**Domain alignment:** [`analysis/domain/business-domain-model.md`](../analysis/domain/business-domain-model.md) v0.2

**Review (applied in v1.1.0):** [`mobile-crm-api-v1-review.md`](mobile-crm-api-v1-review.md)

---

## 1. Purpose

This contract defines the **only** HTTP API the Mobile CRM frontend may call. It exposes **CRM-oriented** resources and properties. ERP-specific names, field identifiers, and validation mechanics are **not** part of this document.

The backend is the **source of truth** for business data (ADR 0001). The API is **online-only** (ADR 0002): no offline sync or outbox endpoints.

---

## 2. Normative boundary

| In scope (this document) | Out of scope (adapter mapping doc) |
|--------------------------|-------------------------------------|
| Paths, methods, CRM DTOs | Gen business objects and field names |
| Client validation and UX rules | Validate-then-commit steps, default merges |
| Error codes and HTTP status | Spike `where` clauses, `select` restrictions |
| Screen → endpoint matrix | Enum-to-Gen numeric mapping |

Frontend code and generated OpenAPI clients must use **only** this contract. Adapter teams implement [`mobile-crm-api-v1-adapter-mapping.md`](mobile-crm-api-v1-adapter-mapping.md).

---

## 3. Base URL and versioning

| Item | Value |
|------|-------|
| Base path | `/api/v1` |
| Media type | `application/json` |
| Charset | UTF-8 |
| Idempotency | `PUT` on activities is idempotent by `activityId`; `POST` create is not |

Production host and TLS are deployment-specific.

---

## 4. Authentication

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes (except `POST /session`) | `Basic {base64(user:password)}` or `Bearer {token}` — must match **backend** deployment configured for this tenant |

The server authenticates the user and resolves the sales representative profile.

| HTTP | When |
|------|------|
| `401 Unauthorized` | Invalid or expired credentials → client navigates to SCR-008 |
| `403 Forbidden` | Authenticated but operation not permitted |

---

## 5. Conventions

### 5.1 Naming

- JSON properties: **camelCase** (e.g. `firmId`, `scheduledStart`).
- Identifiers: opaque strings; format is deployment-specific.
- Timestamps: ISO 8601 UTC (e.g. `2026-06-04T14:30:00.000Z`).

### 5.2 Pagination and search

| Parameter | Type | Default | Use |
|-----------|------|---------|-----|
| `take` | integer | 20 | Max rows (cap 50 server-side) |
| `skip` | integer | 0 | Offset |

List endpoints return:

```json
{
  "items": [],
  "total": null,
  "hasMore": false
}
```

`total` may be `null` when the backend does not provide a total count.

### 5.3 Enumerations

| Enum | Values |
|------|--------|
| `ActivityStatus` | `open`, `inProgress`, `completed`, `handedOver` |
| `ActivitySaveMode` | `create`, `update`, `complete` |
| `CommercialStatus` | `active`, `blocked`, `watch`, `unknown` |
| `CreditIndicator` | `withinLimit`, `overLimit`, `unknown` |
| `OverdueIndicator` | `yes`, `no`, `unknown` |

**`handedOver`:** Supported for parity with backend state machines. MVP UI may exclude it from today and overdue filters.

**Future:** `cancelled` may be added in v2 when product requires it.

### 5.4 Standard error envelope

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Human-readable summary",
    "details": [
      { "field": "subject", "message": "Required" }
    ],
    "traceId": "optional-correlation-id"
  }
}
```

| `error.code` | HTTP | SCR |
|--------------|------|-----|
| `UNAUTHORIZED` | 401 | SCR-008 |
| `FORBIDDEN` | 403 | — |
| `NOT_FOUND` | 404 | — |
| `VALIDATION_FAILED` | 422 | SCR-007 |
| `SERVICE_UNAVAILABLE` | 502 / 503 | SCR-009 |
| `NETWORK_ERROR` | — (client) | SCR-009 |

Field-level validation on activity save is returned in `error.details[]` with CRM field names.

### 5.5 Response metadata (optional)

Large read responses may include:

```json
{
  "meta": {
    "schemaVersion": "1.0"
  }
}
```

`schemaVersion` is informational; clients must tolerate its absence.

### 5.6 Best-effort sections

Some firm-detail fields are populated only when the deployment exposes the underlying data. They may be `null`, omitted, or empty arrays without indicating an error.

| Section | Availability |
|---------|----------------|
| `commercialHealth` | `bestEffort` — not required for MVP flows; not offline-critical |
| `recentActivities` | `bestEffort` |

When present on `FirmDetailResponse`, `meta.availability` may document this:

```json
{
  "meta": {
    "schemaVersion": "1.0",
    "availability": {
      "commercialHealth": "bestEffort",
      "recentActivities": "bestEffort"
    }
  }
}
```

---

## 6. Shared types

### 6.1 `SalesRepresentative`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Authenticated user id for server-side ownership filters |
| `loginName` | string | yes | |
| `displayName` | string | yes | |
| `email` | string | no | May be empty |
| `employeeNumber` | string | no | Optional organisational metadata (e.g. HR number) |

### 6.2 `BackendProvider` (optional)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | e.g. `abra-gen` |
| `version` | string | Deployment/backend version for support |

Not required for UI rendering.

### 6.3 `Address`

| Field | Type | Description |
|-------|------|-------------|
| `line1` | string | Short formatted line (e.g. street + city) |
| `street` | string | |
| `city` | string | |
| `postCode` | string | |
| `countryCode` | string | e.g. `SK` |
| `phone1` | string | |
| `phone2` | string | |
| `email` | string | |
| `fax` | string | |

### 6.4 `ContactSummary`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Contact id |
| `displayName` | string | |
| `firstName` | string | |
| `lastName` | string | |
| `jobTitle` | string | Role or position label |
| `isPrimary` | boolean | Server-derived primary contact for the firm |
| `phone1` | string | |
| `email` | string | |

Contacts in lists are sorted by the server (primary first, then stable order).

### 6.5 `FirmSummary`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | |
| `name` | string | |
| `code` | string | Internal customer code |
| `businessRegistrationNumber` | string | National business registration id when present |
| `city` | string | From main address when present |
| `commercialStatus` | `CommercialStatus` | |

### 6.6 `ActivitySummary`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | |
| `subject` | string | |
| `status` | `ActivityStatus` | |
| `activityTypeId` | string | Reference to activity type catalogue (`GET /activity-types`) |
| `activityTypeName` | string | Optional display |
| `firmId` | string | |
| `firmName` | string | Denormalized for lists |
| `contactId` | string | nullable |
| `contactName` | string | nullable |
| `scheduledStart` | string (date-time) | |
| `scheduledEnd` | string (date-time) | nullable |
| `isOverdue` | boolean | Server-derived: open/inProgress and scheduled before agenda date (org timezone TBD) |

### 6.7 `ActivityTypeOption`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Catalogue id |
| `name` | string | yes | Display label |
| `code` | string | no | Optional short code; not required for UI |

### 6.8 `CommercialHealth` (optional section)

Returned on firm detail when the backend can derive it; otherwise `null` or omitted.

| Field | Type | Description |
|-------|------|-------------|
| `statusLine` | string | Human-readable sales status |
| `commercialStatus` | `CommercialStatus` | |
| `creditIndicator` | `CreditIndicator` | |
| `overdueIndicator` | `OverdueIndicator` | |
| `guidanceText` | string | e.g. visit guidance |

**MVP:** May be `null`. Populated only when deployment enables finance signals. Not part of offline-critical paths (ADR 0002).

---

## 7. Endpoints

### 7.1 Session

#### `POST /session`

| | |
|--|--|
| **Purpose** | Establish authenticated session and load sales representative profile (SCR-001). |
| **Screens** | SCR-001 |

**Request body**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `loginName` | string | yes | Non-empty, max 30 |
| `password` | string | yes | Non-empty |

**Response `200`** — `SessionResponse`

| Field | Type | Description |
|-------|------|-------------|
| `representative` | `SalesRepresentative` | |
| `expiresAt` | string | nullable; if token expiry known |
| `capabilities` | string[] | Optional, e.g. `activities.write`, `firms.read` |
| `provider` | `BackendProvider` | Optional; for diagnostics |

**Response errors:** `401`, `SERVICE_UNAVAILABLE`

---

#### `GET /session`

| | |
|--|--|
| **Purpose** | Validate existing session and refresh representative profile (SCR-010, SCR-001 silent check). |
| **Screens** | SCR-010, SCR-002 (if profile stale) |

**Request:** none (auth header only)

**Response `200`:** same as `SessionResponse`

**Response `401`:** invalid session

---

#### `DELETE /session`

| | |
|--|--|
| **Purpose** | Sign out (client clears local tokens). |
| **Screens** | SCR-002 overflow |

**Response `204`:** no body

---

### 7.2 My Day

#### `GET /my-day`

| | |
|--|--|
| **Purpose** | Operational agenda: today’s and overdue customer activities for the authenticated sales representative (SCR-002). |
| **Screens** | SCR-002 |

**Query parameters**

| Param | Type | Required | Validation |
|-------|------|----------|------------|
| `date` | string (date) | no | Defaults to **today** in rep/org timezone (product: confirm timezone) |
| `take` | integer | no | Per section cap; default 50 |

**Response `200`** — `MyDayResponse`

| Field | Type | Description |
|-------|------|-------------|
| `date` | string (date) | Agenda date |
| `representative` | `SalesRepresentative` | |
| `today` | `ActivitySummary[]` | |
| `overdue` | `ActivitySummary[]` | |
| `todayCount` | integer | |
| `overdueCount` | integer | |
| `meta` | object | Optional; may include `schemaVersion` |

**Server rules**

- Include only activities **owned by** the authenticated representative (per backend ownership policy).
- `today`: `scheduledStart` within `[date 00:00, date+1 00:00)` — default statuses **`open`** and **`inProgress`** only (product may widen later).
- `overdue`: `status` in `open`, `inProgress`; `scheduledStart` before start of `date`.
- Exclude activities linked to inactive or hidden customers when detectable.

---

### 7.3 Firms (customer hub)

#### `GET /firms`

| | |
|--|--|
| **Purpose** | Search customers by name, business registration number, or code (SCR-003). |
| **Screens** | SCR-003 |

**Query parameters**

| Param | Type | Required | Validation |
|-------|------|----------|------------|
| `q` | string | yes | Min length **2** after trim |
| `take` | integer | no | |
| `skip` | integer | no | |

**Response `200`:** `PagedResult<FirmSummary>`

**Server rules**

- Prefer `200` with empty `items` when `q` is shorter than 2 characters (HTTP 400 optional).
- Exclude hidden or inactive customers when the backend supports it.

---

#### `GET /firms/{firmId}`

| | |
|--|--|
| **Purpose** | Customer 360° read model: header, address, contacts, recent activities, commercial health (SCR-004). |
| **Screens** | SCR-004 |

**Path parameters**

| Param | Validation |
|-------|------------|
| `firmId` | Required, non-empty |

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `recentTake` | integer | 10 | Max recent activities |

**Response `200`** — `FirmDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | |
| `name` | string | |
| `code` | string | |
| `businessRegistrationNumber` | string | |
| `taxNumber` | string | National tax id when present |
| `commercialStatus` | `CommercialStatus` | |
| `commercialHealth` | `CommercialHealth` | nullable; **bestEffort** |
| `mainAddress` | `Address` | Company main address |
| `electronicAddress` | `Address` | nullable |
| `website` | string | nullable |
| `contacts` | `ContactSummary[]` | Server-sorted |
| `primaryContactId` | string | nullable |
| `recentActivities` | `ActivitySummary[]` | **bestEffort**; last N for firm |
| `pipelineSnapshot` | object | nullable; MVP stub `{ "openDealCount": null }` |
| `lastModifiedAt` | string (date-time) | Optional |
| `meta` | object | Optional; `schemaVersion`, `availability` per §5.6 |

**Server rules**

- `404` if firm not found or not visible to the representative.
- Contacts exclude internal employee-only persons when detectable.
- Primary contact is server-derived.

---

### 7.4 Contacts

#### `GET /contacts/{contactId}`

| | |
|--|--|
| **Purpose** | Contact detail for call/e-mail and context (SCR-005). |
| **Screens** | SCR-005 |

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `firmId` | string | Recommended when opening from SCR-004 to resolve `isPrimary` |

**Response `200`** — `ContactDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | |
| `firmId` | string | |
| `firmName` | string | |
| `firstName` | string | |
| `lastName` | string | |
| `displayName` | string | |
| `jobTitle` | string | |
| `address` | `Address` | |
| `isPrimary` | boolean | When `firmId` query provided |
| `notes` | string | nullable |

---

#### `GET /firms/{firmId}/contacts`

| | |
|--|--|
| **Purpose** | Contact list for log-visit picker (SCR-007) without loading full firm detail. |
| **Screens** | SCR-007 |

**Response `200`:** `ContactSummary[]` — same contact rules as firm detail.

**Note:** This is a **subset** of firm-detail contacts. Data may duplicate `GET /firms/{firmId}`; clients may reuse SCR-004 payload instead of calling this path.

---

### 7.5 Activities

#### `GET /activities/{activityId}`

| | |
|--|--|
| **Purpose** | Full activity context; entry to complete/edit (SCR-006). |
| **Screens** | SCR-006 |

**Response `200`** — `ActivityDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | |
| `subject` | string | |
| `description` | string | |
| `answer` | string | Outcome notes when completed |
| `status` | `ActivityStatus` | |
| `activityTypeId` | string | |
| `activityTypeName` | string | |
| `scheduledStart` | string | |
| `scheduledEnd` | string | nullable |
| `firm` | `FirmSummary` | |
| `contact` | `ContactSummary` | nullable |
| `ownerId` | string | Responsible representative id |
| `ownerDisplayName` | string | nullable |
| `canEdit` | boolean | `true` when `open` or `inProgress` |
| `canComplete` | boolean | Same as `canEdit` for MVP |
| `lastModifiedAt` | string (date-time) | Optional |
| `meta` | object | Optional; may include `schemaVersion` |

---

#### `POST /activities`

| | |
|--|--|
| **Purpose** | Create customer activity / log visit (SCR-007 create mode). |
| **Screens** | SCR-007 |

**Request body** — `ActivitySaveRequest`

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `mode` | string | yes | Must be `create` (server may infer from `POST` in a future revision) |
| `firmId` | string | yes | |
| `contactId` | string | no | Must belong to firm when provided |
| `activityTypeId` | string | yes | From `GET /activity-types` |
| `subject` | string | yes | 1–100 chars |
| `description` | string | no | |
| `scheduledStart` | string | yes | ISO date-time |
| `scheduledEnd` | string | no | |
| `status` | `ActivityStatus` | no | Default `open` |

**Response `201`** — `ActivitySaveResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Created activity id |
| `status` | `ActivityStatus` | |
| `warnings` | string[] | Non-blocking server messages |

**Response `422`:** `VALIDATION_FAILED` with field details

**Server rules**

- Creates a customer activity owned by the authenticated representative.
- Server may run **multi-step validation** against the ERP before commit.
- Client treats success as `201` or `422` only.

---

#### `PUT /activities/{activityId}`

| | |
|--|--|
| **Purpose** | Update open activity or complete visit (SCR-007 edit/complete modes). |
| **Screens** | SCR-006, SCR-007 |

**Request body** — `ActivitySaveRequest`

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `mode` | string | yes | `update` or `complete` |
| `firmId` | string | yes when `mode=update` | Must match existing activity firm when provided |
| `contactId` | string | no | |
| `activityTypeId` | string | no | |
| `subject` | string | no | |
| `description` | string | no | |
| `answer` | string | yes when `mode=complete` | Outcome notes |
| `scheduledStart` | string | no | |
| `scheduledEnd` | string | no | |
| `status` | `ActivityStatus` | yes when `mode=complete` | Must be `completed` |

**Response `200`:** `ActivitySaveResponse`

**Server rules**

- `404` if activity missing.
- `409` or `422` if activity is not editable.
- `complete`: requires `answer` and `status` = `completed`.

---

### 7.6 Reference data

#### `GET /activity-types`

| | |
|--|--|
| **Purpose** | Populate activity type picker on log visit (SCR-007). |
| **Screens** | SCR-007 |

**Response `200`:** `ActivityTypeOption[]`

Client must use returned `id` values when creating activities.

---

## 8. Screen → endpoint matrix

| Screen | Method | Path | Notes |
|--------|--------|------|-------|
| SCR-001 Login | POST | `/session` | |
| SCR-010 App loading | GET | `/session` | |
| SCR-002 My Day | GET | `/my-day` | Pull-to-refresh repeats |
| SCR-003 Firm search | GET | `/firms?q=` | Debounced client-side |
| SCR-004 Firm detail | GET | `/firms/{firmId}` | |
| SCR-005 Contact detail | GET | `/contacts/{contactId}?firmId=` | |
| SCR-006 Activity detail | GET | `/activities/{activityId}` | |
| SCR-007 Log visit (create) | POST | `/activities` | |
| SCR-007 Log visit (edit/complete) | PUT | `/activities/{activityId}` | |
| SCR-007 Contact picker | GET | `/firms/{firmId}/contacts` | Or reuse SCR-004 payload |
| SCR-007 Type picker | GET | `/activity-types` | |
| SCR-008 Session expired | — | — | Client + `401` handling |
| SCR-009 Connection error | — | — | Client + `502`/`503`/`SERVICE_UNAVAILABLE`/network |

---

## 9. Out of scope for v1

| Item | Target |
|------|--------|
| Pipeline, quotes, orders (SCR-011–014) | API v2 |
| Contact create/update | Backend admin / v2 |
| Offline sync queue | ADR 0002 |
| Commercial health guaranteed fields | Backend workshop + adapter refresh |
| Calendar appointments in `/my-day` | v2 |
| File attachments on activities | v2 |

---

## 10. Open questions (client impact)

Implementation detail and Gen-specific blockers are tracked in [`mobile-crm-api-v1-adapter-mapping.md` §8](mobile-crm-api-v1-adapter-mapping.md#8-open-questions-adapter-blockers).

| Topic | Client impact |
|-------|----------------|
| Agenda date timezone | Overdue/today boundaries on SCR-002 |
| Activity create persistence semantics | SCR-007 success handling after save |
| `recentActivities` on firm detail | SCR-004 may show empty list until backend confirms filter |
| Firm search behaviour | SCR-003 result quality per deployment |
| `commercialHealth` | SCR-004 section may be empty in MVP |

---

## 11. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | Initial MVP contract from validated spikes + domain/screens v0.2 |
| 1.1.0 | 2026-06-04 | Split adapter mapping; remove Gen leakage; review refinements ([`mobile-crm-api-v1-review.md`](mobile-crm-api-v1-review.md)) |
