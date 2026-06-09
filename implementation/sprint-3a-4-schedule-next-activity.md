# Sprint 3A.4 — Schedule next activity on completion

**Status:** Implemented  
**Depends on:** [3A.1 create](sprint-3a-1-activity-create.md), [3A.3 handover spike](sprint-3a-3-handover-spike.md)

---

## 1. Business goal

When completing an activity, encourage scheduling the next step (PipeDrive-style) with optional follow-up create in the same action.

---

## 2. API

### `PUT /api/v1/activities/{id}/complete`

**Request** (extended):

```json
{
  "answer": "Výsledok návštevy",
  "description": "optional",
  "followUp": {
    "enabled": true,
    "subject": "Ďalší telefonát",
    "scheduledStart": "2026-06-25T08:00:00.000Z",
    "description": "optional"
  }
}
```

| Field | Required when `followUp.enabled` |
|-------|----------------------------------|
| `answer` | Always |
| `followUp.subject` | Yes |
| `followUp.scheduledStart` | Yes (ISO-8601) |
| `followUp.description` | No |

Omit `followUp` or set `enabled: false` to complete only.

**Success (200):** `ActivityDetailResponse` with completed/handover source activity.

**Follow-up created:**

```json
{
  "followUpActivity": {
    "id": "…",
    "documentNumber": "PrHo-…",
    "subject": "…",
    "scheduledStart": "…"
  }
}
```

**Follow-up failed (complete still succeeded):**

```json
{
  "warnings": [
    {
      "code": "FOLLOW_UP_CREATE_FAILED",
      "message": "…"
    }
  ]
}
```

---

## 3. Backend flow

```
1. Validate answer + follow-up fields
2. ActivityService.CompleteAsync (Status 2 + append Answer)
3. If followUp.enabled:
     ActivityCreateService.CreateAsync with Source_ID = completed id
4. Return ToDto(detail, followUp?, warnings?)
```

### Gen payload (follow-up)

Inherited via `ActivityCreateService` from source full GET:

- `Firm_ID`, `Person_ID`, `ActivityType_ID`
- `ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`, `ActivityArea_ID`
- `BusTransaction_ID`, `BusOrder_ID`, `BusProject_ID` (when set)
- `ResponsibleUser_ID`, `SolverUser_ID` (from source, else session rep)
- **`Source_ID`** = completed activity id → native handover (source → Status 3)

User-supplied: `Subject`, `SheduledStart$DATE`, optional `Description`.

---

## 4. Frontend

### Completion form

- Checkbox **Naplánovať ďalší krok** — default **checked**
- When enabled: Predmet (required), Termín `datetime-local` (required), Popis (optional)
- Default termín: tomorrow 10:00 local
- Default predmet: current activity subject

### Success UI

After complete on terminal activity:

- ✓ Aktivita dokončená
- ✓ Naplánovaná ďalšia aktivita (when `followUpActivity` returned)
- Warning line if `FOLLOW_UP_CREATE_FAILED`

Note history (append Answer on complete) unchanged.

---

## 5. Files changed

| Area | Files |
|------|--------|
| Gen | `ActivityMapper.cs`, `ActivityCreateService.cs` |
| Adapter | `ApiModels.cs`, `ApiMapping.cs`, `ActivitiesController.cs` |
| Web | `types.ts`, `ActivityDetailPage.tsx`, `followUpDefaults.ts`, `sk-SK.ts`, `global.css` |

---

## 6. Verification

```powershell
# Login
$login = Invoke-RestMethod -Uri "http://localhost:5080/api/v1/session" -Method POST `
  -ContentType "application/json" -Body '{"loginName":"api","password":"123"}'
$h = @{ Authorization = "Bearer $($login.sessionToken)" }

# Start in-progress activity, then complete with follow-up
$body = @{
  answer = "Test outcome"
  followUp = @{
    enabled = $true
    subject = "Next step call"
    scheduledStart = "2026-06-25T10:00:00.000Z"
  }
} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:5080/api/v1/activities/{id}/complete" `
  -Method PUT -Headers $h -ContentType "application/json" -Body $body
```

Expect: `status` `handedOver` or `completed`, `followUpActivity` populated, source `Answer` preserved.
