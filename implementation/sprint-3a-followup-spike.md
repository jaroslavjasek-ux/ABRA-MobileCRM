# Sprint 3A P0 — Follow-up activity create spike

**Status:** Passed (DEMO Gen 26)  
**Run (UTC):** 2026-06-06T08:28:30Z  
**Environment:** `http://localhost/demo` (credentials `api` / `123`)  
**Spike script:** [`scripts/spike_follow_up_activity_create.py`](../scripts/spike_follow_up_activity_create.py)  
**Raw log:** [`analysis/spikes/follow-up-activity-create-results.json`](../analysis/spikes/follow-up-activity-create-results.json)

---

## 1. Goal

Verify that a new CRM activity can be created in ABRA Gen via `POST /crmactivities` using the same **validate-then-commit** pattern as Sprint 2B (`PUT` status changes), before implementing follow-up scheduling on activity completion.

**No UI in this step.**

---

## 2. Source activity (completed context)

Data inherited from completed activity `2000000101` (`PrHo-1/2006`, Status `2`):

| Field | Value |
|-------|-------|
| `Firm_ID` | `3000000101` |
| `Person_ID` | *(null on this source)* |
| `ActivityType_ID` | `2000000101` |
| `ResponsibleUser_ID` | *(null)* |
| `SolverUser_ID` | `1300000101` |
| `Subject` | `otázka na pozáručný servis` |

**Reference fields** copied from full GET of source (mandatory on DEMO):

| Field | Value |
|-------|-------|
| `ActQueue_ID` | `2000000101` |
| `Period_ID` | `4000000101` |
| `Division_ID` | `2000000101` |
| `SolverRole_ID` | `1000000101` |
| `ActivityArea_ID` | `2000000101` |

Session user (`GET currentuser`): `2610000101` (login `API`).

---

## 3. Validate-then-commit pattern

Aligned with Sprint 2B:

```
1. POST /crmactivities?validation=true   → fail if @meta.validation.errors.count > 0
2. POST /crmactivities                   → commit (NO validation flag)
3. GET  /crmactivities/{id}              → confirm persisted
```

**Anti-pattern (confirmed):** `POST /crmactivities?validation=true` on commit returns HTTP 200 + preview `id`, but **GET → 404** — not persisted (same as Sprint 2B PUT preview).

---

## 4. Primary scenario — recommended path (C)

**Scenario:** Source reference fields + session owner (`ResponsibleUser_ID` / `SolverUser_ID` = `2610000101`).

### 4.1 Validation request

```http
POST /crmactivities?validation=true
Content-Type: application/json
```

```json
{
  "Subject": "Sprint 3A follow-up test (source refs + session owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "2610000101",
  "SolverUser_ID": "2610000101",
  "ActQueue_ID": "2000000101",
  "Period_ID": "4000000101",
  "Division_ID": "2000000101",
  "SolverRole_ID": "1000000101",
  "ActivityArea_ID": "2000000101"
}
```

### 4.2 Validation response

- **HTTP:** 200  
- **`@meta.validation.errors.count`:** `0`  
- **Preview fields (not persisted):**
  - Preview `id`: `G100000101` (discarded)
  - Preview `displayname`: `Bez čísla`
  - `status`: `0` (open)
  - `createdby_id`: `2610000101`
  - `responsibleuser_id` / `solveruser_id`: `2610000101`
  - `firmoffice_id`: `3000000101` (auto-derived from firm)
  - Nested `contacts[]` row created in preview

### 4.3 Commit request

```http
POST /crmactivities
Content-Type: application/json
```

Same JSON body as validation request (no merge from preview required when source refs are pre-filled).

### 4.4 Commit response

- **HTTP:** 201  
- **Persisted record (excerpt):**

```json
{
  "id": "H100000101",
  "displayname": "PrHo-9/2006",
  "subject": "Sprint 3A follow-up test (source refs + session owner)",
  "status": 0,
  "firm_id": "3000000101",
  "activitytype_id": "2000000101",
  "responsibleuser_id": "2610000101",
  "solveruser_id": "2610000101",
  "sheduledstart$date": "2026-06-08T10:00:00.000Z",
  "createdby_id": "2610000101",
  "createdat$date": "2026-06-06T08:28:00.000Z"
}
```

### 4.5 Resulting activity

| Property | Value |
|----------|-------|
| **Activity ID** | `H100000101` |
| **Document number (`DisplayName`)** | `PrHo-9/2006` |
| **Status** | `0` (open) |

`GET /crmactivities/H100000101` confirmed persistence.

---

## 5. Control scenarios

### 5.1 Minimal payload without source refs (A) — **FAIL**

**Validation request** — user fields only:

```json
{
  "Subject": "Sprint 3A follow-up test (minimal)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete"
}
```

**Validation response:** HTTP 200, `errors.count = 4`:

| Field | Error |
|-------|-------|
| `actqueue_id` | Chyba v zadaní položky Rad aktivít |
| `period_id` | Rad aktivít nemá identitu |
| `solverrole_id` | Chyba v zadaní položky Rola riešiteľa |
| `division_id` | Chyba v zadaní položky Stredisko |

Merging validate preview into commit body **does not fix** missing `ActQueue_ID` on DEMO — preview leaves `actqueue_id: null`.

**Commit:** HTTP 400 — not persisted.

### 5.2 Source refs, no explicit owner (B) — **SUCCESS**

Same user fields + inherited reference fields, no `ResponsibleUser_ID`:

- **Commit:** HTTP 201  
- **ID:** `F100000101`  
- **DisplayName:** `PrHo-8/2006`  
- **Owner:** `CreatedBy_ID = 2610000101` only (`ResponsibleUser_ID` null)

Proves explicit owner is **not required for persist**, but recommended for clear assignment.

### 5.3 Commit with `?validation=true` (E) — **FAIL persist**

- **Commit:** HTTP 200, preview `id` `L100000101`, `displayname` `Bez čísla`  
- **GET:** 404 — not in database

---

## 6. Findings

### 6.1 Minimum required payload (DEMO)

| Category | Fields |
|----------|--------|
| **User input** | `Subject`, `SheduledStart$DATE`; optional `Description` |
| **Inherited from completed activity** | `Firm_ID`, `ActivityType_ID`, `Person_ID` (when set on source) |
| **Inherited reference fields (mandatory on DEMO)** | `ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`, `ActivityArea_ID` |
| **Recommended ownership** | `ResponsibleUser_ID`, `SolverUser_ID` = session rep |

User-only payload (`Subject` + `Firm_ID` + `ActivityType_ID` + `SheduledStart$DATE`) is **insufficient**.

### 6.2 Fields automatically populated by Gen

| Field | Behaviour |
|-------|-----------|
| `ID` | Assigned on commit |
| `DisplayName` | Number series assigned on commit (e.g. `PrHo-9/2006`); preview shows `Bez čísla` |
| `Status` | Defaults to `0` (open) |
| `CreatedBy_ID` | Current authenticated Gen user |
| `CreatedAt$DATE` | Set on commit |
| `PMState_ID` | Default workflow (`CADEF00000`) |
| `FirmOffice_ID` | Often equals `Firm_ID` in validate preview |
| `RealStart$DATE` / `RealEnd$DATE` | Set to “now” in validate preview only |
| `contacts[]` | Nested contact row in validate preview when `Firm_ID` set |

### 6.3 Must validate response be merged into commit payload?

| Situation | Merge needed? |
|-----------|-----------------|
| Reference fields copied from **source activity full GET** | **No** — validate passes with `errors.count = 0`; commit uses same body |
| User-only payload | **Insufficient** — merge from preview cannot supply `ActQueue_ID` on DEMO |
| Optional enrich | Merge `FirmOffice_ID` from preview when source has null |

**Implementation rule:** inherit reference fields from completed activity GET; optionally merge `FirmOffice_ID` / `ActivityArea_ID` from validate response if still empty.

### 6.4 Document number

**Yes — auto-generated.** Mobile must never send `DisplayName` or `Code`. Read `DisplayName` from commit response or follow-up GET.

### 6.5 My Day visibility

My Day (`MyDayService`) includes activities when **all** of:

1. `Status` maps to `open` or `inProgress`
2. Ownership: `ResponsibleUser_ID`, `SolverUser_ID`, or `CreatedBy_ID` matches session rep
3. `SheduledStart$DATE` is on the selected agenda date (today bucket) or before it (overdue bucket)

Spike created activity `F100000101` with `SheduledStart$DATE = 2026-06-08`:

- **Ownership query:** found (`CreatedBy_ID = 2610000101`)
- **Agenda date 2026-06-08:** would appear in “today”
- **Agenda date 2026-06-06:** not in today/overdue (scheduled in the future)

### 6.6 Owner assignment

| Approach | Persist | My Day ownership | Recommendation |
|----------|---------|------------------|----------------|
| No owner fields | ✓ | ✓ via `CreatedBy_ID` | Works but implicit |
| `ResponsibleUser_ID` + `SolverUser_ID` = session rep | ✓ | ✓ explicit | **Preferred** |
| Inherited `SolverUser_ID` from source | ✓ | Depends on source user | Avoid for follow-up |

---

## 7. Mandatory fields discovered

| Field | Required on DEMO | Source |
|-------|:----------------:|--------|
| `Subject` | ✓ | User |
| `Firm_ID` | ✓ | Completed activity |
| `ActivityType_ID` | ✓ | Completed activity |
| `SheduledStart$DATE` | ✓ | User |
| `ActQueue_ID` | ✓ | Source activity GET |
| `Period_ID` | ✓ | Source activity GET |
| `Division_ID` | ✓ | Source activity GET |
| `SolverRole_ID` | ✓ | Source activity GET |
| `ActivityArea_ID` | ✓ | Source activity GET |
| `ResponsibleUser_ID` | ○ | Session rep (recommended) |
| `SolverUser_ID` | ○ | Session rep (recommended) |
| `Person_ID` | ○ | Source when contact linked |
| `Description` | ○ | User |

**Never send:** `ID`, `DisplayName`, `Status`, `X_*`, `U_SV_*`.

---

## 8. Recommended DTO — follow-up activity creation

### 8.1 Mobile CRM API (extend `CompleteActivityRequest`)

```typescript
/** Optional follow-up scheduled when completing an activity. */
export interface FollowUpActivityRequest {
  /** When true, adapter creates a new open activity after successful complete. */
  enabled: boolean;
  /** Required when enabled. */
  subject: string;
  /** ISO-8601 instant; required when enabled. */
  scheduledStart: string;
  description?: string;
}

export interface CompleteActivityRequest {
  answer: string;
  description?: string;
  followUp?: FollowUpActivityRequest;
}
```

### 8.2 Adapter response extension (partial success)

```typescript
export interface ActivityDetailResponse {
  // ...existing fields...
  followUp?: {
    id: string;
    documentNumber: string;
    scheduledStart: string;
  };
}

export interface ApiWarning {
  code: "FOLLOW_UP_CREATE_FAILED";
  message: string;
}
```

Complete succeeds, follow-up fails → **HTTP 200** + `warnings: [{ code: "FOLLOW_UP_CREATE_FAILED", ... }]`.

### 8.3 Adapter → Gen payload builder (server-side only)

```csharp
/// <summary>
/// Built after successful CompleteAsync when followUp.enabled.
/// Reference fields from full GET of the just-completed activity.
/// </summary>
public sealed record FollowUpGenCreatePayload
{
    public required string Subject { get; init; }
    public required string FirmId { get; init; }
    public required string ActivityTypeId { get; init; }
    public required DateTimeOffset ScheduledStart { get; init; }
    public string? Description { get; init; }
    public string? PersonId { get; init; }
    public required string ResponsibleUserId { get; init; }
    public required string SolverUserId { get; init; }
    public required string ActQueueId { get; init; }
    public required string PeriodId { get; init; }
    public required string DivisionId { get; init; }
    public required string SolverRoleId { get; init; }
    public required string ActivityAreaId { get; init; }
    public string? FirmOfficeId { get; init; }
}
```

**Create service flow:**

```
1. Map FollowUpGenCreatePayload → Dictionary (PascalCase Gen fields)
2. POST crmactivities?validation=true → assert errors.count == 0
3. POST crmactivities → expect 201
4. GET crmactivities/{id} → return id + DisplayName to client
```

### 8.4 Adapter implementation prerequisites

| Item | Status |
|------|--------|
| `IGenApiClient.PostAsync` | **Not implemented** — add before 3A |
| `ActivityCreateService` | **Not implemented** |
| Extend `ActivityDetailSelect` / full GET for reference fields | Required on complete path |
| UI for follow-up form | **Out of scope (3A P0)** |

---

## 9. Verdict

**P0 spike passed.** Follow-up activity creation is feasible on DEMO Gen 26 using:

- Completed-activity context (firm, type, person, reference fields)
- Validate-then-commit POST (no validation flag on commit)
- Session rep as `ResponsibleUser_ID` / `SolverUser_ID`
- Auto-generated `DisplayName` read from commit response

Proceed to adapter implementation (`PostAsync`, `ActivityCreateService`, extend `CompleteAsync`). See also [`sprint-3a-follow-up-activity-design.md`](sprint-3a-follow-up-activity-design.md) for full 3A design.

---

## 10. Open questions

| ID | Question |
|----|----------|
| OQ-3A-P0-01 | Production Gen: is source-reference inheritance always sufficient, or is validate-merge loop needed? |
| OQ-3A-P0-02 | Fallback when completed source lacks `ActQueue_ID`? |
| OQ-3A-P0-03 | Default `ActivityType_ID` when source has none? |
