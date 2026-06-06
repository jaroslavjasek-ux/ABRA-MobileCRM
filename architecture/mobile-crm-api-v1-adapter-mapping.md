# Mobile CRM API v1 — ABRA Gen Adapter Mapping

**Status:** Draft (companion to normative contract)  
**Version:** 1.1.0  
**Date:** 2026-06-04  
**Audience:** Thin ABRA Adapter implementers only — **not** the Mobile CRM frontend

**Normative contract (frontend):** [`mobile-crm-api-v1.md`](mobile-crm-api-v1.md)  
**Implements:** [ADR 0004 — Thin ABRA Adapter](../docs/decisions/0004-thin-abra-adapter.md) · [Integration decision study](abra-integration-decision-study.md)

**Evidence:** Validated Gen spikes only — do not invent endpoints beyond spike evidence.

| Spike | Reference |
|-------|-----------|
| CRM activities | [`analysis/spikes/crmactivities-lifecycle.md`](../analysis/spikes/crmactivities-lifecycle.md) |
| Contacts | [`analysis/spikes/contact-model.md`](../analysis/spikes/contact-model.md) |
| Sales rep identity | [`analysis/spikes/sales-representative-model.md`](../analysis/spikes/sales-representative-model.md) |

**Applied review:** [`mobile-crm-api-v1-review.md`](mobile-crm-api-v1-review.md)

---

## 1. Purpose

This document is the **only** place Gen business object names, field names, validation mechanics, and spike-validated constraints belong. The normative API contract defines CRM DTOs and HTTP behaviour; this document defines how the **ABRA Gen adapter** fulfils that contract.

Gen remains the **source of truth** (ADR 0001). MVP is **online-only** (ADR 0002).

---

## 2. Spike-validated constraints (must not regress)

| Constraint | Source | Adapter implication |
|------------|--------|---------------------|
| Use **`crmactivities`**, not `tasks` | Lifecycle spike | All activity R/C/U via `crmactivities` |
| Do **not** set `ResponsibleCustomerPerson_ID` | Lifecycle spike | Map `contactId` → `Person_ID` only |
| Do **not** send customer **`X_*`** custom fields | Lifecycle spike | Strip from outbound bodies |
| Create uses **`POST crmactivities?validation=true`** | Lifecycle spike | Validate-then-commit; merge defaults on validation errors |
| Complete via **`PUT`** + **`Status = 2`** | Lifecycle spike | Do not use `pmchangestate` in v1 |
| Avoid invalid **`select`** fields | All spikes | No `ResponsibleCustomerPerson_ID`, `FirmPersons` in select, `Hidden` on securityuser, `Address_ID` on firm where rejected |
| **`persons?where=Firm_ID`** invalid on DEMO | Contact spike | Contacts via `GET firms/{id}` → `firmpersons[]` only |
| **`currentuser.id`** = **`securityusers.ID`** | Rep spike | `representative.id` in session |
| **`employees`** via **`Person_ID`** | Rep spike | `employeeNumber` optional; employee id ≠ user id |
| My Day ownership **OR** | Rep spike | `ResponsibleUser_ID` OR `SolverUser_ID` OR `CreatedBy_ID` |
| Response casing | Lifecycle spike | Gen responses often lowercase; requests PascalCase |

**Not validated on DEMO (provisional — return empty/null until confirmed on target Gen):**

- Firm search `where` syntax
- `crmactivities?where=Firm_ID eq '{firmId}'` for `recentActivities`
- Commercial health finance field map
- Today/overdue date filter on `SheduledStart$DATE` (OQ-SR-04 / OQ-LC-04)

---

## 3. CRM enum → Gen mapping

| CRM enum | CRM values | Gen source |
|----------|------------|------------|
| `ActivityStatus` | `open`, `inProgress`, `completed`, `handedOver` | `crmactivity.Status` 0, 1, 2, 3 |
| `ActivitySaveMode` | `create`, `update`, `complete` | POST vs PUT + `Status` |
| `CommercialStatus` | `active`, `blocked`, `watch`, `unknown` | `firm` / `pmstate` (deployment rules) |
| `CreditIndicator` | `withinLimit`, `overLimit`, `unknown` | Derived when Gen finance fields available |
| `OverdueIndicator` | `yes`, `no`, `unknown` | Derived when Gen finance fields available |

**Normative note (forwarded to client doc):** `handedOver` maps Gen status 3 (Odovzdané). MVP UI may exclude it from today/overdue filters.

---

## 4. CRM field → Gen field mapping (DTOs)

### 4.1 Session / representative

| CRM field | Gen |
|---------|-----|
| Auth | Gen login / Basic as configured |
| `representative.id` | `GET currentuser` → `id` (= `securityusers.ID`) |
| `representative.loginName` | `securityusers.LoginName` |
| `representative.displayName` | `currentuser.name` or `securityusers.Name` |
| `representative.email` | From user/person when available |
| `representative.employeeNumber` | `GET employees?where=Person_ID eq '{securityusers.Person_ID}'` → `PersonalNumber` (optional) |
| `SessionResponse.provider` | `{ "name": "abra-gen", "version": "<deployment>" }` |
| `SessionResponse.capabilities` | Map from Gen permissions / object access (deployment-specific) |

### 4.2 Firm

| CRM field | Gen |
|---------|-----|
| `id` | `firm.ID` |
| `name` | `Name` |
| `code` | `Code` |
| `businessRegistrationNumber` | `OrgIdentNumber` or equivalent (e.g. IČO) |
| `taxNumber` | Tax id field when present (e.g. DIČ) |
| `city` | From address projection |
| `commercialStatus` | Deployment rules on firm / `pmstate` |
| `mainAddress` | `residenceaddress_id` embed |
| `electronicAddress` | `electronicaddress_id` embed |
| `website` | Firm web field when present |
| Hidden firms | Exclude `Hidden eq true` when filter supported |

### 4.3 Contact

| CRM field | Gen |
|---------|-----|
| `id` | `person.ID` |
| Names | `FirstName`, `LastName`, `FullName`, `DisplayName` |
| `jobTitle` | `Grade` or work position |
| `isPrimary` | `InitialFirmPerson_ID` on firm if not placeholder `0000000000`; else lowest `firmperson.PosIndex` |
| Contact sort order | `firmperson.PosIndex` (not exposed on CRM `ContactSummary`) |
| Phones/email | `address` embed per contact-model spike |
| Exclude employees | `person.IsEmployee eq true` → omit from firm contact lists |

### 4.4 Activity

| CRM field | Gen `crmactivity` |
|---------|-------------------|
| `firmId` | `Firm_ID` |
| `contactId` | `Person_ID` (not `ResponsibleCustomerPerson_ID`) |
| `activityTypeId` | `ActivityType_ID` |
| `subject` | `Subject` |
| `description` | `Description` |
| `answer` | `Answer` |
| `scheduledStart` | `SheduledStart$DATE` |
| `scheduledEnd` | `SheduledEnd$DATE` |
| `status` | `Status` (0–3) |
| Owner | `ResponsibleUser_ID` = session `representative.id` on create |
| `lastModifiedAt` | From `ObjVersion` / change timestamp when available |

### 4.5 Activity type

| CRM field | Gen `crmactivitytype` |
|---------|----------------------|
| `id` | `ID` |
| `code` | `Code` (optional in client contract) |
| `name` | `Name` |

Query: `GET crmactivitytypes?take=50&select=ID,Code,Name`

---

## 5. Gen resource summary

| CRM resource | Gen controller | Gen schema | MVP operations |
|--------------|----------------|------------|----------------|
| Session / rep | `currentuser`, `securityusers` | — / `securityuser` | R |
| Rep HR (optional) | `employees` | `employee` | R |
| Firm | `firms` | `firm` | R |
| Contact | `persons` | `person` | R |
| Firm–contact link | (nested) | `firmperson` in `FirmPersons[]` | R |
| Address | `addresses` | `address` | R |
| Activity | `crmactivities` | `crmactivity` | R, C, U |
| Activity type | `crmactivitytypes` | `crmactivitytype` | R |

### Explicitly excluded from v1 adapter

| Gen | Reason |
|-----|--------|
| `tasks` | Wrong module (lifecycle spike) |
| `contacts` collection | Does not exist; use `persons` |
| `persons?where=Firm_ID` | Invalid on DEMO (contact spike) |
| `pmchangestate` for activity complete | v1 uses PUT + `Status=2` |

---

## 6. Endpoint implementation

### 6.1 `POST /session`

| Contract | Gen |
|----------|-----|
| Auth | Gen login / Basic as configured |
| Profile | `GET currentuser`; optional `GET securityusers/{id}?select=ID,LoginName,Name,Person_ID` |
| Errors | Map Gen auth failure → `401`; unreachable Gen → normative `SERVICE_UNAVAILABLE` |

**Non-production only:** Ops guide may document `connectionLabel` (Gen connection path hint) — not in normative OpenAPI.

---

### 6.2 `GET /session`

Same mapping as POST without credential body.

---

### 6.3 `DELETE /session`

Client-side token discard; optional Gen session invalidate if deployment supports it.

---

### 6.4 `GET /my-day`

**Ownership filter (validated OR)** — `GET crmactivities` where **any** of:

- `ResponsibleUser_ID eq '{repId}'`
- `SolverUser_ID eq '{repId}'`
- `CreatedBy_ID eq '{repId}'`

**Date filter (OQ-SR-04 / OQ-LC-04):** Predicates on `SheduledStart$DATE`; exact `where` syntax to confirm on target Gen.

| Contract | Gen |
|----------|-----|
| `today[]`, `overdue[]` | `GET crmactivities?select=…&where=…` (1–2 queries or combined OR) |
| `firmName` | Deduped `GET firms/{id}?select=ID,Name` per distinct `Firm_ID` |
| Activity rows | `crmactivities` only — **not** `tasks` |

**Normative filters (adapter must implement):**

- `today`: `scheduledStart` in agenda date window; default statuses `open`, `inProgress`
- `overdue`: `open` or `inProgress`, `scheduledStart` before start of agenda `date`
- Exclude activities for hidden/inactive firms when detectable

---

### 6.5 `GET /firms`

| Contract | Gen |
|----------|-----|
| List | `GET firms?select=ID,Name,Code,Hidden&where=…&take&skip` |
| `businessRegistrationNumber` | `OrgIdentNumber` or equivalent |
| `city` | Address projection |

**OQ:** Exact search `where` clause not validated in spikes; deployment-specific name/code/registration filter.

---

### 6.6 `GET /firms/{firmId}`

| Contract | Gen |
|----------|-----|
| Core + contacts | `GET firms/{firmId}` (full payload); parse `firmpersons[]` |
| Contact names/phones | `firmperson` embed + optional `GET persons/{id}` |
| `mainAddress` | `residenceaddress_id` embed |
| `electronicAddress` | `electronicaddress_id` embed |
| `recentActivities` | **Provisional:** `GET crmactivities?where=Firm_ID eq '{firmId}'` — return `[]` until confirmed |
| `commercialHealth` | Deployment finance fields — **not** spike-validated; return `null` until workshop |
| `lastModifiedAt` | Firm change timestamp when available |

**Primary contact rule:** `InitialFirmPerson_ID` if not placeholder `0000000000`; else lowest `PosIndex`.

---

### 6.7 `GET /firms/{firmId}/contacts`

Same `firmpersons[]` parse as firm detail. Adapter may call `GET firms/{firmId}` again (duplicate of firm detail contacts — expected for MVP).

---

### 6.8 `GET /contacts/{contactId}`

| Contract | Gen |
|----------|-----|
| Person | `GET persons/{id}?select=ID,FirstName,LastName,FullName,DisplayName,Grade,Address_ID,Hidden,IsEmployee` |
| Address | Embedded `address_id` or `GET addresses/{id}?select=EMail,PhoneNumber1,PhoneNumber2,…` |
| Firm name | Prior firm detail or `GET firms/{firmId}?select=ID,Name` |

---

### 6.9 `GET /activities/{activityId}`

| Contract | Gen |
|----------|-----|
| Activity | `GET crmactivities/{id}?select=` safe list (no `ResponsibleCustomerPerson_ID`) |
| Firm | `GET firms/{firmId}` or embedded |
| Contact | `GET persons/{personId}` when `Person_ID` set |
| `canEdit` / `canComplete` | `Status` 0–1 |
| `lastModifiedAt` | From `ObjVersion` / change timestamp when available |

---

### 6.10 `POST /activities`

**Validate-then-commit (lifecycle spike):**

1. `POST crmactivities?validation=true` with mapped PascalCase body.
2. If `@meta.validation.errors` non-empty, merge Gen-returned defaults (`ActQueue_ID`, `Period_ID`, `ActivityArea_ID`, …) and retry until clean or return normative `422` with CRM field names in `details[]`.
3. **Never** send customer `X_*` custom fields.
4. Set `ResponsibleUser_ID` = session `representative.id`.
5. Do **not** set `ResponsibleCustomerPerson_ID`.
6. Map `contactId` → `Person_ID`.
7. Persist per OQ-LC-01 (201 vs validation-only 200).

Map validation item names → CRM field names for `error.details[]`.

**Normative client behaviour:** Server may run multi-step ERP validation; client receives `201` or `422` only.

---

### 6.11 `PUT /activities/{activityId}`

- `PUT crmactivities/{id}?validation=true`; retain `Firm_ID` on body.
- `complete` → `Status: 2`; set `Answer` and/or `Description`.
- `404` if missing; `409`/`422` if Gen disallows edit on completed rows.
- `pmchangestate` **not** used in v1.

**Note:** Normative contract requires `firmId` on update when provided — adapter must include `Firm_ID` on Gen PUT header pattern.

---

### 6.12 `GET /activity-types`

`GET crmactivitytypes?take=50&select=ID,Code,Name`

---

## 7. Error mapping

| Normative `error.code` | Gen / adapter |
|------------------------|---------------|
| `UNAUTHORIZED` | Auth failure |
| `FORBIDDEN` | Gen denies object/operation |
| `NOT_FOUND` | 404 from Gen |
| `VALIDATION_FAILED` | `@meta.validation` or business rule failure → map fields to CRM names |
| `SERVICE_UNAVAILABLE` | Gen unreachable, timeout, 502/503 |

---

## 8. Open questions (adapter blockers)

| ID | Question | Endpoints affected |
|----|----------|-------------------|
| OQ-SR-04 / OQ-LC-04 | Today/overdue date `where` on `SheduledStart$DATE` | `GET /my-day` |
| OQ-LC-01 | Create HTTP 201 vs validation-only 200 | `POST /activities` |
| OQ-LC-02 | Required Gen defaults on create | `POST /activities` |
| OQ-SR-02 | Single vs OR ownership filter | `GET /my-day` |
| OQ-SR-05 | My customers when `firms.ResponsibleUser_ID` empty | Future `GET /firms?mine=true` |
| — | `crmactivities` filter by `Firm_ID` | `GET /firms/{id}` → `recentActivities` |
| — | Firm search `where` syntax | `GET /firms` |
| — | Commercial health field map | `commercialHealth` |

---

## 9. Out of scope (adapter v1)

| Item | Target |
|------|--------|
| Pipeline, quotes, orders | API v2 / other Gen BOs |
| Contact create/update | Gen admin / v2 |
| Offline sync queue | ADR 0002 |
| Calendar in `/my-day` | v2 |
| Activity attachments | v2 |

---

## 10. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.1.0 | 2026-06-04 | Split from normative contract per API v1 review; spike constraints preserved |
