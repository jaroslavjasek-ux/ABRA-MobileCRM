# Sprint 3A.2 — Activity dimensions analysis

**Status:** Analysis complete (DEMO Gen 26)  
**Date:** 2026-06-06  
**Goal:** Design a reusable activity model for Mobile CRM and future Mobile Projects, covering Business Case, Work Order, and Project dimensions.

**Sources:** OpenAPI `crmactivities.json`, live DEMO API, [crmactivities lifecycle spike](../analysis/spikes/crmactivities-lifecycle.md), [Sprint 3A.1 create](sprint-3a-1-activity-create.md).

---

## 1. Executive summary

| Mobile concept | ABRA Gen BO | `crmactivities` field (POST/PUT) | GET (full) | GET (list select) |
|----------------|-------------|----------------------------------|------------|-------------------|
| **Business Case** | `bustransactions` (Obchodný prípad) | `BusTransaction_ID` | `bustransaction_id` | `BusTransaction_ID` or `bustransaction_id` |
| **Work Order** | `busorders` (Zákazka) | `BusOrder_ID` | `busorder_id` | `BusOrder_ID` or `busorder_id` |
| **Project** | `busprojects` (Projekt) | `BusProject_ID` | `busproject_id` | `BusProject_ID` or `busproject_id` |

All three fields are **optional FK links** on `crmactivity`. They are **available on `crmactivities`**, **writable on POST/PUT**, and **inherit cleanly from a source activity** when non-null.

DEMO seed data has **no firm-linked** dimension rows (`Firm_ID` is null on sample `busorders` / `busprojects` / `bustransactions`), so firm-scoped pickers return empty lists on DEMO — production installs with linked data are expected to filter by `Firm_ID`.

---

## 2. Gen field reference

### 2.1 Activity foreign keys

| Mobile field | Gen POST field | Gen GET (lowercase) | BO class | Slovak label (OpenAPI) | Max length |
|--------------|----------------|---------------------|----------|--------------------------|------------|
| `businessCase` | `BusTransaction_ID` | `bustransaction_id` | `bustransaction` | Obchodný prípad | 10 |
| `workOrder` | `BusOrder_ID` | `busorder_id` | `busorder` | Zákazka | 10 |
| `project` | `BusProject_ID` | `busproject_id` | `busproject` | Projekt | 10 |

**Related (out of scope for MVP dimensions):**

| Field | Purpose |
|-------|---------|
| `PipeLineStatus_ID` | CRM pipeline stage enum (`crmpipelinestatus`) — not a dimension picker |
| `CreditBusOrder_ID` / `DebitBusOrder_ID` | Accounting variants on other schemas — **not** on standard `crmactivity` header |

### 2.2 Requirement flags (activity type)

Each `crmactivitytype` defines whether a dimension is used:

| Gen field | Values | Meaning |
|-----------|--------|---------|
| `BusTransactionReq` | 0 / 1 / 2 | Obch. prípad: optional / **required** / hidden |
| `BusOrderReq` | 0 / 1 / 2 | Zákazka: optional / **required** / hidden |
| `BusProjectReq` | 0 / 1 / 2 | Projekt: optional / **required** / hidden |

On DEMO type `2000000101` (Telefón): all three are **0** (optional, not hidden).

Adapter should read these flags when `ActivityType_ID` is known and enforce required dimensions before Gen validate.

---

## 3. GET representation

### 3.1 Full GET (`GET crmactivities/{id}`)

Returns lowercase keys (Gen native JSON):

```json
{
  "id": "P100000101",
  "firm_id": "3000000101",
  "busorder_id": "A000000101",
  "busproject_id": "2000000101",
  "bustransaction_id": "3000000101"
}
```

Confirmed on DEMO after create with all three dimensions set.

### 3.2 List / selective GET

`select` accepts **PascalCase or lowercase**:

```http
GET crmactivities?select=ID,BusOrder_ID,BusProject_ID,BusTransaction_ID&take=1
```

```json
{
  "value": [
    {
      "ID": "2000000101",
      "BusOrder_ID": null,
      "BusProject_ID": null,
      "BusTransaction_ID": null
    }
  ]
}
```

**Note:** DEMO list responses may wrap rows in `{ "value": [...], "Count": n }` instead of a bare array.

### 3.3 Display names

Activity stores **IDs only**. Labels come from linked BO GET:

| BO | Display field | Example (DEMO) |
|----|---------------|----------------|
| `busorder` | `DisplayName` (also `Code`, `Name`) | `S Služby` |
| `busproject` | `DisplayName` | `Dealer Sprostredkovanie predaja` |
| `bustransaction` | `DisplayName` | `Zľavy Zľavové akcie` |

`DisplayName` is typically `{Code} {Name}` — use for mobile picker labels; persist **ID** only.

---

## 4. POST / PUT representation

### 4.1 Payload casing

Use **PascalCase** in POST/PUT bodies (consistent with Sprint 2B/3A.1):

```json
{
  "Subject": "Site visit",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-15T10:00:00.000Z",
  "BusTransaction_ID": "3000000101",
  "BusProject_ID": "2000000101",
  "BusOrder_ID": "A000000101"
}
```

Validate-then-commit: `POST crmactivities?validation=true` then `POST crmactivities`.

### 4.2 Live validation (DEMO 2026-06-06)

| Scenario | `errors.count` | Result |
|----------|:--------------:|--------|
| Valid IDs for all three dimensions | **0** | Preview echoes `busorder_id`, `busproject_id`, `bustransaction_id` |
| Commit same body | **201** | Persisted; GET confirms all three IDs |
| Invalid `BusOrder_ID` (`INVALID99`) | **1** | Gen error (invalid object id); surfaced under validation metadata |

Dimensions are **not required** when activity type flags are `0`, but invalid IDs fail validation.

### 4.3 Omit vs null

- **Omit** field → unchanged on PUT; null on new create.
- Send explicit ID only when user selects a value.
- Do not send empty string — Gen expects 10-char ID or absent.

---

## 5. Inheritance from source activity

When creating a follow-up or cloned activity (Sprint 3A.1 `ActivityCreateService`):

| Field | Inherit when | Notes |
|-------|--------------|-------|
| `BusTransaction_ID` | Source `bustransaction_id` non-null | Copy as-is |
| `BusProject_ID` | Source `busproject_id` non-null | Copy as-is |
| `BusOrder_ID` | Source `busorder_id` non-null | Copy as-is |
| `Firm_ID` | Always from source | Already implemented |
| `Person_ID` | When set | Already implemented |

**Verified:** Activity `P100000101` created with dimensions; full GET returns all three IDs — suitable as `sourceActivityId` for inherit-on-create extension.

**Recommendation:** Inherit dimensions by default on follow-up create; allow user override when feature flags enable pickers (Sprint 3A.3+).

**Hierarchy note:** ABRA links BOs via nested `*source` collections (`busordersource`, `busprojectsource`, `bustransactionsource`). When source activity has no dimensions but firm context exists, adapter may suggest candidates from `busorders?where=Firm_ID eq '…'` — empty on DEMO, expected on production.

---

## 6. Lookup APIs for selection

### 6.1 Primary list endpoints

| Dimension | Endpoint | Schema |
|-----------|----------|--------|
| Business Case | `GET bustransactions` | `bustransaction` |
| Work Order | `GET busorders` | `busorder` |
| Project | `GET busprojects` | `busproject` |

### 6.2 Recommended select projection

```http
GET busorders?select=ID,DisplayName,Code,Name,Firm_ID&take=50
```

Works on DEMO. Avoid non-existent fields in `select` (e.g. `Subject` on `busorders` → **400**).

### 6.3 Filtering

| Filter | OData example | DEMO result |
|--------|---------------|-------------|
| By firm | `where=Firm_ID eq '{firmId}'` | Empty (seed has `Firm_ID: null`) |
| By id | `where=ID eq '{id}'` | Works |
| Take | `take=50` | Works |

**Production expectation:** filter pickers by `Firm_ID` matching activity firm. Fallback: global search on `DisplayName` / `Code` (confirm `contains` / `substringof` support per install).

### 6.4 Detail resolve (for display)

```http
GET busorders/{id}
GET busprojects/{id}
GET bustransactions/{id}
```

Use `DisplayName` for UI; store `id` / `ID` on activity.

### 6.5 Cascade selection (Mobile Projects)

ABRA BO source links suggest optional UX order:

```
Business Case (bustransaction)
    └── Project (busproject)      ← busprojectsource.BusTransaction_ID
            └── Work Order (busorder)  ← busordersource.BusProject_ID
```

For Mobile CRM MVP: **independent optional pickers** filtered by `Firm_ID`. Cascade can be added in Mobile Projects without API changes.

### 6.6 Adapter endpoints (proposed)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/firms/{firmId}/business-cases` | Paginated `bustransactions` for firm |
| `GET /api/v1/firms/{firmId}/work-orders` | Paginated `busorders` for firm |
| `GET /api/v1/firms/{firmId}/projects` | Paginated `busprojects` for firm |

Or single generic: `GET /api/v1/dimensions/{type}?firmId=…&q=…` behind feature flags.

---

## 7. Validation requirements

### 7.1 Layers

| Layer | Rule |
|-------|------|
| **Feature config** | If `businessCase: false`, omit field and hide UI |
| **Activity type** | If `BusTransactionReq === 1`, require `BusTransaction_ID` before Gen POST |
| **Activity type** | If `*Req === 2`, dimension hidden — do not send |
| **Gen validate** | `POST ?validation=true` — invalid FK → `errors.count > 0` |
| **Firm consistency** | Recommend: selected dimension `Firm_ID` matches activity `Firm_ID` when both set (soft warning on DEMO, hard rule TBD for production) |

### 7.2 Activity type lookup

```http
GET crmactivitytypes/{activityTypeId}?select=ID,BusOrderReq,BusProjectReq,BusTransactionReq
```

Cache per type in adapter session or config.

---

## 8. Reusable activity model (Mobile CRM / Mobile Projects)

### 8.1 Domain model

```typescript
/** Shared activity context — CRM visits and Projects tasks. */
export interface ActivityContext {
  firm: FirmRef;
  contact?: ContactRef;
  businessCase?: DimensionRef;  // BusTransaction
  workOrder?: DimensionRef;     // BusOrder
  project?: DimensionRef;       // BusProject
}

export interface DimensionRef {
  id: string;              // Gen 10-char ID — canonical for API/Gen
  displayName: string;     // Resolved from BO GET (DisplayName)
  code?: string;           // busorder/busproject/bustransaction Code
}

export interface FirmRef {
  id: string;
  name: string;
}

export interface ContactRef {
  id: string;
  displayName: string;
}
```

### 8.2 Adapter DTO extension (proposed)

Extend `ActivityDetailResponseDto`:

```csharp
public sealed class ActivityDimensionDto
{
    public required string Id { get; init; }
    public required string DisplayName { get; init; }
    public string? Code { get; init; }
}

// On ActivityDetailResponseDto:
public ActivityDimensionDto? BusinessCase { get; init; }
public ActivityDimensionDto? WorkOrder { get; init; }
public ActivityDimensionDto? Project { get; init; }
```

Gen → Mobile mapping:

| Response field | Gen source |
|----------------|------------|
| `businessCase.id` | `bustransaction_id` |
| `workOrder.id` | `busorder_id` |
| `project.id` | `busproject_id` |
| `*.displayName` | Secondary GET to respective BO |

### 8.3 Create / update payload extension

Extend `CreateActivityRequestDto` (and future complete follow-up):

```csharp
public string? BusinessCaseId { get; init; }  // → BusTransaction_ID
public string? WorkOrderId { get; init; }    // → BusOrder_ID
public string? ProjectId { get; init; }       // → BusProject_ID
```

When null: inherit from source if present; otherwise omit from Gen body.

---

## 9. Feature configuration proposal

Per-tenant or per-app module flags control visibility and adapter behaviour:

```json
{
  "activityDimensions": {
    "businessCase": true,
    "workOrder": true,
    "project": true
  }
}
```

### 9.1 Suggested delivery

| Location | Purpose |
|----------|---------|
| `appsettings.json` / tenant config | Adapter reads flags at startup |
| `GET /api/v1/session` → `capabilities` | Web hides disabled pickers |
| Activity type `*Req === 2` | Gen overrides config — dimension hidden regardless |

### 9.2 Behaviour matrix

| Config | `*Req` | UI | Gen payload |
|--------|--------|-----|-------------|
| `true` | 0 | Optional picker | Send when selected |
| `true` | 1 | Required picker | Must send valid ID |
| `false` | 0 | Hidden | Omit |
| `false` | 2 | Hidden | Omit |
| `true` | 2 | Hidden (Gen) | Omit — log config conflict |

### 9.3 Mobile CRM vs Mobile Projects defaults

| Module | Suggested default |
|--------|-------------------|
| **Mobile CRM** | `{ businessCase: false, workOrder: false, project: false }` — firm + contact only for MVP |
| **Mobile Projects** | `{ businessCase: true, workOrder: true, project: true }` |

CRM can enable dimensions per customer without code changes.

---

## 10. Implementation roadmap (post-analysis)

| Sprint | Work |
|--------|------|
| **3A.2** | This analysis ✓ |
| **3A.3** | `ActivityMapper` dimension getters; extend `ActivityDetailResponse`; optional resolve display names |
| **3A.4** | Extend `ActivityCreateService` / `CreateActivityRequestDto` with optional dimension IDs + inherit |
| **3A.5** | Firm-scoped dimension list endpoints + feature config in session |
| **3B** | Mobile Projects pickers with cascade UX |

---

## 11. Open questions

| ID | Question |
|----|----------|
| OQ-3A2-01 | Production DEMO/customer: is `Firm_ID` always set on `busorders` / `busprojects` / `bustransactions` used in CRM? |
| OQ-3A2-02 | Should adapter enforce firm-dimension consistency when BO `Firm_ID` is set? |
| OQ-3A2-03 | Is `DisplayName` or `Code` preferred label in Slovak UI for pickers? |
| OQ-3A2-04 | Pipeline: expose `PipeLineStatus_ID` alongside dimensions or separate feature? |
| OQ-3A2-05 | Mobile Projects: implement cascade filters via `*source` APIs or flat firm lists? |

---

## 12. Evidence log (DEMO live)

| Test | Result |
|------|--------|
| `POST crmactivities?validation=true` with all three dimension IDs | `errors.count = 0` |
| `POST crmactivities` commit | `201`, id `P100000101` |
| `GET crmactivities/P100000101?select=…` | All three `*_ID` persisted |
| `GET busorders?select=ID,DisplayName,Code,Name,Firm_ID&take=3` | 200, `DisplayName` populated |
| `where=Firm_ID eq '3000000101'` on dimension BOs | Empty on DEMO |
| Existing activities with dimensions | None in seed (`null` on all sampled rows) |

**OpenAPI:** `architecture/reference/spike/openapi/crmactivities.json` → schema `crmactivity` properties `BusOrder_ID`, `BusProject_ID`, `BusTransaction_ID` (lines ~14374–14424).
