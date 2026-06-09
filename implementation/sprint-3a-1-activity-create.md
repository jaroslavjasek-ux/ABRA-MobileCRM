# Sprint 3A.1 — Activity create infrastructure

**Status:** Implemented and verified (DEMO Gen 26)  
**Depends on:** [Sprint 3A P0 spike](sprint-3a-followup-spike.md)  
**Scope:** Backend only — no follow-up UI

---

## 1. Overview

Sprint 3A.1 adds adapter infrastructure to create CRM activities in ABRA Gen using the **validate-then-commit** `POST /crmactivities` pattern proven in the P0 spike (Scenario C).

| Component | Location |
|-----------|----------|
| `PostAsync` | `MobileCrm.Adapter.Gen/GenApiClient.cs` |
| `ActivityCreateService` | `MobileCrm.Adapter.Gen/ActivityCreateService.cs` |
| Reference field extraction | `MobileCrm.Adapter.Gen/ActivityMapper.cs` → `TryGetReferenceFields` |
| API DTO | `MobileCrm.Adapter/Models/ApiModels.cs` → `CreateActivityRequestDto` |
| Endpoint | `POST /api/v1/activities` |

---

## 2. API

### 2.1 Create activity

```http
POST /api/v1/activities
Authorization: Bearer {sessionToken}
Content-Type: application/json
```

**Request body (`CreateActivityRequestDto`):**

```json
{
  "sourceActivityId": "2000000101",
  "subject": "Follow-up call",
  "scheduledStart": "2026-06-10T10:00:00.000Z",
  "description": "Optional note"
}
```

| Field | Required | Description |
|-------|:--------:|-------------|
| `sourceActivityId` | ✓ | Existing activity to inherit firm, type, contact, and Gen reference fields from |
| `subject` | ✓ | New activity subject |
| `scheduledStart` | ✓ | ISO-8601 instant → Gen `SheduledStart$DATE` |
| `description` | ○ | Optional description |

**Server-side additions (not in client DTO):**

- `ResponsibleUser_ID` / `SolverUser_ID` → session representative
- `Firm_ID`, `ActivityType_ID`, `Person_ID` (when set) → from source activity
- `ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`, `ActivityArea_ID` → from source full GET

**Success:** HTTP **200** + `ActivityDetailResponseDto` (refetched after commit).

**Errors:**

| HTTP | Code | When |
|------|------|------|
| 404 | `NOT_FOUND` | Source activity not found |
| 422 | `VALIDATION_FAILED` | Missing request fields, source missing firm/type/refs, Gen validation failed |
| 401 | `UNAUTHORIZED` | Invalid session |

---

## 3. Gen workflow (`ActivityCreateService`)

```
1. ActivityLookup.LoadAsync(sourceActivityId)     → resolve canonical ID
2. GET crmactivities/{id}                         → full payload (reference fields)
3. TryGetReferenceFields + ParseDetailRow         → build inherit context
4. BuildGenPayload(command, source, refs, repId)
5. POST crmactivities?validation=true             → errors.count must be 0
6. POST crmactivities                             → commit (no validation flag)
7. IActivityService.GetDetailAsync(createdId)     → ActivityDetailResponse
```

**Anti-pattern avoided:** commit with `?validation=true` (preview only, not persisted).

---

## 4. Gen payload (Scenario C mapping)

```json
{
  "Subject": "{from request}",
  "Firm_ID": "{from source}",
  "ActivityType_ID": "{from source}",
  "SheduledStart$DATE": "{from request.scheduledStart}",
  "Description": "{optional}",
  "ResponsibleUser_ID": "{session rep}",
  "SolverUser_ID": "{session rep}",
  "Person_ID": "{from source when set}",
  "ActQueue_ID": "{from source}",
  "Period_ID": "{from source}",
  "Division_ID": "{from source}",
  "SolverRole_ID": "{from source}",
  "ActivityArea_ID": "{from source}"
}
```

---

## 5. New types

### 5.1 `CreateActivityCommand` (Gen layer)

```csharp
public sealed record CreateActivityCommand(
    string SourceActivityId,
    string Subject,
    DateTimeOffset ScheduledStart,
    string? Description);
```

### 5.2 `ActivityOperationErrorCode.MissingReferenceFields`

Returned when source activity full GET lacks any of the five mandatory reference fields.

### 5.3 `GenActivityReferenceFields`

```csharp
public sealed record GenActivityReferenceFields(
    string ActQueueId,
    string PeriodId,
    string DivisionId,
    string SolverRoleId,
    string ActivityAreaId);
```

---

## 6. Field name handling

Gen list/detail `select` responses use PascalCase (`ActivityType_ID`); full GET responses use lowercase (`activitytype_id`). `ActivityMapper.ParseRow` and `TryGetReferenceFields` accept both conventions.

`ActivityCreateService` always performs a **full GET** of the source activity because `ActivityDetailSelect` does not include reference fields.

---

## 7. Verification (2026-06-06, DEMO)

**Environment:** `http://localhost/demo`, adapter `http://localhost:5080`, user `api`/`123`

**Request:**

```http
POST /api/v1/activities
```

```json
{
  "sourceActivityId": "2000000101",
  "subject": "Sprint 3A.1 adapter create test",
  "scheduledStart": "2026-06-10T10:00:00.000Z",
  "description": "3A.1 verification"
}
```

**Response (excerpt):**

| Field | Value |
|-------|-------|
| `id` | `N100000101` |
| `documentNumber` | `PrHo-11/2006` |
| `status` | `open` |
| `canEdit` | `true` |
| `canComplete` | `false` |
| `canAddNote` | `true` |
| `ownerId` | `2610000101` |
| `firm.name` | `EUROCAR s.r.o.` |

Gen assigned `DisplayName` automatically; activity is open and actionable for the session rep.

**Manual verification:**

```powershell
$login = Invoke-RestMethod -Uri "http://localhost:5080/api/v1/session" `
  -Method POST -ContentType "application/json" `
  -Body '{"loginName":"api","password":"123"}'
$headers = @{ Authorization = "Bearer $($login.sessionToken)" }
Invoke-RestMethod -Uri "http://localhost:5080/api/v1/activities" -Method POST `
  -Headers $headers -ContentType "application/json" `
  -Body '{"sourceActivityId":"2000000101","subject":"Test","scheduledStart":"2026-06-10T10:00:00.000Z"}'
```

---

## 8. Out of scope (Sprint 3A.2+)

- Follow-up UI on complete form
- `CompleteAsync` integration with `followUp` request block
- Partial-success warnings (`FOLLOW_UP_CREATE_FAILED`)

---

## 9. Files changed

| File | Change |
|------|--------|
| `GenApiClient.cs` | `PostAsync` |
| `ActivityCreateService.cs` | New service |
| `ActivityMapper.cs` | `TryGetReferenceFields`, lowercase field aliases |
| `ActivityOperationResult.cs` | `MissingReferenceFields` |
| `ServiceCollectionExtensions.cs` | Register `IActivityCreateService` |
| `ApiModels.cs` | `CreateActivityRequestDto` |
| `ActivitiesController.cs` | `POST /api/v1/activities` |
