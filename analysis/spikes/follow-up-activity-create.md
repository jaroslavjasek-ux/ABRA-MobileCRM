# Sprint 3A P0 — Follow-up activity create spike

**Run (UTC):** 2026-06-05  
**Base URL:** `http://localhost/demo`  
**Script:** [`scripts/spike_follow_up_activity_create.py`](../../scripts/spike_follow_up_activity_create.py)  
**Raw log:** [`follow-up-activity-create-results.json`](follow-up-activity-create-results.json)

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| Can follow-up activities be created reliably? | **Yes**, with validate-then-commit and **reference fields inherited from the completed source activity** |
| Minimum user payload sufficient alone? | **No** — `Subject` + `Firm_ID` + `ActivityType_ID` + `SheduledStart$DATE` alone fails validation (4 errors) and commit returns **400** |
| Validate response must be merged? | **Partially** — merge alone is **insufficient** on DEMO; **`ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`** must be copied from the **source completed activity** |
| Document number auto-generated? | **Yes** — Gen assigns `DisplayName` (e.g. `PrHo-5/2006`); mobile never sends it |
| Appears in My Day? | **Yes** — when `SheduledStart$DATE` falls on agenda day and ownership matches (`CreatedBy_ID` and/or `ResponsibleUser_ID` / `SolverUser_ID`) |
| `ResponsibleUser_ID` required? | **Not for persist** — Gen sets `CreatedBy_ID` from credentials; **recommended** for explicit rep ownership |

**Anti-pattern confirmed:** `POST ?validation=true` on commit returns preview id but **GET → 404** (not persisted), same as Sprint 2B PUT.

---

## 2. Source context (completed activity)

| Field | Value |
|-------|-------|
| `ID` | `2000000101` |
| `DisplayName` | `PrHo-1/2006` |
| `Status` | `2` (completed) |
| `Firm_ID` | `3000000101` |
| `ActivityType_ID` | `2000000101` |
| `ResponsibleUser_ID` | `null` |
| `SolverUser_ID` | `1300000101` |

**Reference fields copied from source (full GET):**

| Gen field | Value |
|-----------|-------|
| `ActQueue_ID` | `2000000101` |
| `Period_ID` | `4000000101` |
| `Division_ID` | `2000000101` |
| `SolverRole_ID` | `1000000101` |
| `ActivityArea_ID` | `2000000101` |

---

## 3. Scenario results

### A — Minimal payload, no source refs (control — **FAIL**)

**Validate payload:**

```json
{
  "Subject": "Sprint 3A follow-up test (minimal)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-06T10:00:00.000Z",
  "Description": "P0 spike — safe to delete"
}
```

- Validate: **200**, `errors.count = 4` → `actqueue_id`, `period_id`, `solverrole_id`, `division_id`
- Commit (`POST` without flag): **400** — *Chyba v zadaní položky Rad aktivít*
- Persisted: **No**

### B — Source refs, no explicit owner (**SUCCESS**)

**Validate payload:** same user fields as A.

**Commit payload (after inheriting source refs):**

```json
{
  "Subject": "Sprint 3A follow-up test (source refs, no owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-07T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ActQueue_ID": "2000000101",
  "Period_ID": "4000000101",
  "Division_ID": "2000000101",
  "SolverRole_ID": "1000000101",
  "ActivityArea_ID": "2000000101"
}
```

- Validate: **200**, `errors.count = 0`
- Commit: **201**
- Resulting **ID:** `1100000101`
- Resulting **DisplayName:** `PrHo-5/2006`
- Resulting **Status:** `0` (open)
- My Day ownership query: **found** (via `CreatedBy_ID = 2610000101`)

### C — Source refs + session owner (**SUCCESS**)

Adds:

```json
"ResponsibleUser_ID": "2610000101",
"SolverUser_ID": "2610000101"
```

- Commit: **201**, persisted, open status
- Recommended path for Sprint 3A follow-up

### D — Source refs + inherited owner from source (**SUCCESS**)

Uses `SolverUser_ID` from completed activity (`1300000101`) as owner — also persists (**201**).

### E — Commit with `?validation=true` (anti-pattern — **FAIL persist**)

- Commit: **200**, preview id returned
- GET by id: **404** — not persisted

---

## 4. Field analysis

### 4.1 Truly required (DEMO evidence)

| Field | Required | Notes |
|-------|:--------:|-------|
| `Subject` | ✓ | User input |
| `Firm_ID` | ✓ | Inherited from completed activity |
| `ActivityType_ID` | ✓ | Inherited (default) |
| `SheduledStart$DATE` | ✓ | User due date/time |
| `ActQueue_ID` | ✓ | **Inherit from source** — not reliably filled by validate merge alone |
| `Period_ID` | ✓ | Inherit from source |
| `Division_ID` | ✓ | Inherit from source |
| `SolverRole_ID` | ✓ | Inherit from source |
| `ActivityArea_ID` | ✓ | Inherit from source (often equals type area) |

### 4.2 Gen fills automatically

| Field | Behaviour |
|-------|-----------|
| `ID` | Assigned on commit |
| `DisplayName` | Number series / caption (e.g. `PrHo-5/2006`) |
| `Status` | Defaults to **0** (open) |
| `CreatedBy_ID` | Current Gen user from credentials |
| `PMState_ID` | Default workflow state |
| `RealStart$DATE` / `RealEnd$DATE` | Set to “now” on validate preview |
| `contacts[]` | Nested row when `Firm_ID` set |
| `FirmOffice_ID` | Often equals `Firm_ID` on validate preview |

### 4.3 Recommended optional

| Field | Source |
|-------|--------|
| `Person_ID` | Inherited contact when present |
| `Description` | User input |
| `ResponsibleUser_ID` | Session rep (explicit ownership) |
| `SolverUser_ID` | Same as responsible on DEMO |

### 4.4 Never send

`ID`, `DisplayName`, `Status`, `X_*`, `U_SV_*`

---

## 5. Validate-then-commit pattern (Sprint 2B aligned)

```
1. POST /crmactivities?validation=true   → inspect errors.count
2. Build commit body:
     user fields
   + inherited context from completed activity (refs + firm + type + person)
   + merge FirmOffice_ID / ActivityArea_ID from validate if still needed
3. POST /crmactivities                  → expect 201 (or 200 + GET confirms)
4. GET /crmactivities/{id}            → confirm persisted
```

**Do not** use `?validation=true` on the commit POST.

---

## 6. Recommended Sprint 3A DTO

### 6.1 Mobile CRM request (extend complete)

```typescript
interface FollowUpActivityRequest {
  enabled: boolean;
  subject: string;           // required when enabled
  scheduledStart: string;    // ISO-8601, required when enabled
  description?: string;
}

interface CompleteActivityRequest {
  answer: string;
  description?: string;
  followUp?: FollowUpActivityRequest;
}
```

### 6.2 Adapter → Gen create payload

```csharp
// Built server-side after successful complete — not sent by client
var genBody = new Dictionary<string, object?>
{
    ["Subject"] = followUp.Subject,
    ["Firm_ID"] = completed.FirmId,
    ["ActivityType_ID"] = completed.ActivityTypeId ?? options.DefaultActivityTypeId,
    ["SheduledStart$DATE"] = followUp.ScheduledStart,
    ["Description"] = followUp.Description,
    ["Person_ID"] = completed.PersonId,                    // when set
    ["ResponsibleUser_ID"] = session.RepUserId,            // recommended
    ["SolverUser_ID"] = session.RepUserId,
    // From full GET of completed activity:
    ["ActQueue_ID"] = sourceRefs.ActQueueId,
    ["Period_ID"] = sourceRefs.PeriodId,
    ["Division_ID"] = sourceRefs.DivisionId,
    ["SolverRole_ID"] = sourceRefs.SolverRoleId,
    ["ActivityArea_ID"] = sourceRefs.ActivityAreaId,
    ["FirmOffice_ID"] = sourceRefs.FirmOfficeId,          // when set
};
```

### 6.3 Partial success response (unchanged from 3A design)

Complete succeeds → follow-up fails → **HTTP 200** + `warnings: [{ code: "FOLLOW_UP_CREATE_FAILED" }]`.

---

## 7. Implementation blockers resolved

| Blocker | Resolution |
|---------|------------|
| `PostAsync` missing | Add to `IGenApiClient` |
| Create validation on DEMO | Inherit reference fields from completed activity full GET |
| Preview-only commit | Second POST **without** `validation=true` |
| Document number | Read `DisplayName` from create response / GET |

---

## 8. Open questions for implementation

| ID | Question |
|----|----------|
| OQ-3A-P0-01 | Production Gen: same reference-field inheritance, or validate-merge loop enough? |
| OQ-3A-P0-02 | Fallback when source activity lacks `ActQueue_ID` (rare)? |
| OQ-3A-P0-03 | Default `ActivityType_ID` when source has none? |

---

## 9. Verdict

**P0 spike passed.** Follow-up create is feasible using completed-activity context + validate-then-commit. Proceed to adapter `ActivityCreateService` implementation; **no UI in this step**.
