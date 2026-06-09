# Sprint 3B.1 — User assignment

**Status:** Implemented  
**Date:** 2026-06-08  
**Depends on:** [3B.0 assignment analysis](sprint-3b-0-activity-assignment-analysis.md), [3A.4 schedule next activity](sprint-3a-4-schedule-next-activity.md)

---

## 1. Goal

Allow assigning follow-up activities to a specific user so the activity appears in that user's **Môj deň**, while preserving Gen reference-field inheritance from the source activity.

---

## 2. API

### `GET /api/v1/users`

Lists assignable Gen `securityusers` for the follow-up picker.

| Query | Default | Description |
|-------|---------|-------------|
| `q` | — | Optional filter on display name, login, or short name (client-side on fetched page) |
| `take` | 30 | Max 50 |

**Response:** `PagedResult<SalesRepresentative>` (`id`, `loginName`, `displayName`).

**Gen source:** `GET securityusers?select=ID,Name,LoginName,ShortName&take=…`

**Example:**

```http
GET /api/v1/users?take=30
Authorization: Bearer …
```

```json
{
  "items": [
    { "id": "1200000101", "loginName": "JANO", "displayName": "Jaroslav Novák" },
    { "id": "2610000101", "loginName": "API", "displayName": "API" }
  ],
  "total": 2,
  "hasMore": false
}
```

### `PUT /api/v1/activities/{id}/complete` (extended)

`followUp` object gains optional `assignedUserId`:

```json
{
  "answer": "Výsledok",
  "followUp": {
    "enabled": true,
    "subject": "Ďalší telefonát",
    "scheduledStart": "2026-06-25T08:00:00.000Z",
    "assignedUserId": "1200000101",
    "description": "optional"
  }
}
```

| Field | Required when `followUp.enabled` | Default |
|-------|----------------------------------|---------|
| `followUp.assignedUserId` | No | Session representative (`currentuser` id) |

When set (or defaulted), adapter writes **both** `SolverUser_ID` and `ResponsibleUser_ID` on Gen `POST crmactivities`.

### `POST /api/v1/activities` (extended)

Same optional `assignedUserId` on standalone create (Sprint 3A.1 path).

### `ActivityDetailResponse` (extended)

| Field | Source |
|-------|--------|
| `ownerId` | Gen `ResponsibleUser_ID` |
| `ownerDisplayName` | Resolved from `ResponsibleUser_ID` (fallback `SolverUser_ID`) via `securityusers/{id}` |

---

## 3. Backend behaviour

### Assignment on create

`ActivityCreateService.BuildGenPayload`:

```csharp
var assigneeId = string.IsNullOrWhiteSpace(command.AssignedUserId)
    ? repUserId
    : command.AssignedUserId.Trim();

body["ResponsibleUser_ID"] = assigneeId;
body["SolverUser_ID"] = assigneeId;
```

**Still inherited from source (unchanged):** `Firm_ID`, `Person_ID`, `ActivityType_ID`, `ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`, `ActivityArea_ID`, dimensions, `Source_ID`.

**Not inherited for assignee:** previous source `SolverUser_ID` / `ResponsibleUser_ID` — replaced by selected user.

### Validation

- `assignedUserId` must reference an active `securityuser` when explicitly sent.
- Omitted → session rep (no extra lookup).

### My Day visibility (Mobile CRM)

After assignment to User B:

| User | Sees follow-up in My Day? | Reason |
|------|:-------------------------:|--------|
| **User B** | ✓ | `SolverUser_ID` / `ResponsibleUser_ID` |
| **User A (creator)** | ✓* | `CreatedBy_ID` = Gen API user who committed POST |

\*Per [3B.0 analysis](sprint-3b-0-activity-assignment-analysis.md): creator visibility is a Gen platform rule; Mobile My Day includes `CreatedBy_ID`. User A sees the activity **only** via creator rule, not via solver assignment.

User B can **start** and **complete** the activity (`IsOwnedByRepresentative` matches solver/responsible).

---

## 4. Frontend

### Completion form (follow-up section)

When **Naplánovať ďalší krok** is checked:

| Control | Field |
|---------|-------|
| Predmet | `followUp.subject` |
| Termín | `followUp.scheduledStart` |
| **Priradený používateľ** | `followUp.assignedUserId` |
| Popis | `followUp.description` (optional) |

**Default assignee:** current session `representative.id` (logged-in user).

User list loaded from `GET /api/v1/users` on form open.

### Activity detail

Shows **Priradený používateľ** section when `ownerDisplayName` is present.

---

## 5. Files changed

| Area | Files |
|------|--------|
| Gen | `UserLookupService.cs`, `ActivityCreateService.cs`, `ActivityService.cs`, `ActivityMapper.cs`, `ServiceCollectionExtensions.cs` |
| Adapter | `UsersController.cs`, `ActivitiesController.cs`, `ApiModels.cs`, `ApiMapping.cs` |
| Web | `api/users.ts`, `api/types.ts`, `api/queryKeys.ts`, `ActivityDetailPage.tsx`, `sk-SK.ts` |
| Verify | `scripts/verify_3b1_user_assignment.py` |

---

## 6. Verification

### Automated script

```bash
python scripts/verify_3b1_user_assignment.py
```

Requires Gen DEMO (`http://localhost/demo`) and adapter (`http://localhost:5080`).

**Flow:**

1. Login as `api` (User A).
2. Complete an in-progress activity with follow-up `assignedUserId = 1200000101` (JANO / User B).
3. Assert User B My Day contains follow-up id.
4. User B starts and completes follow-up.
5. Log whether User A My Day contains follow-up (expected: yes via `CreatedBy_ID` when A is API user).

### Manual E2E

1. Login Mobile CRM as User A.
2. Open in-progress activity → complete with follow-up assigned to User B.
3. Login as User B → **Môj deň** shows new activity.
4. User B: **Začať riešiť** → **Dokončiť aktivitu**.
5. Open follow-up detail → **Priradený používateľ** shows User B name.

### DEMO ids

| User | ID | Login |
|------|-----|-------|
| API (integration) | `2610000101` | `api` |
| Jaroslav Novák | `1200000101` | `JANO` |

---

## 7. Verification result (2026-06-08)

| Check | Result |
|-------|--------|
| `dotnet build` (adapter) | ✓ Pass |
| `npm run build` (web) | ✓ Pass |
| Live E2E vs Gen DEMO | **Not run** — Gen DEMO unreachable (`http://localhost/demo` connection refused) during implementation |

Re-run `scripts/verify_3b1_user_assignment.py` when Gen DEMO is available.

---

## 8. Bug fix — assigned user ignored (2026-06-08)

### Symptom

UI selected **JAROJ** (`2620000101`), but created activity had `SolverUser_ID` / `ResponsibleUser_ID` = **JANO** (`1200000101`, session user).

### Root cause

**Frontend**, not backend Gen mapping:

1. `completeMutation` closed over `followUpAssignedUserId` from an earlier render instead of reading the value at submit time.
2. `assignedUserId: followUpAssignedUserId || undefined` omitted the field from JSON when empty → backend defaulted to `session.RepUserId` (JANO).

Direct API test with `followUp.assignedUserId: "2620000101"` persisted JAROJ correctly before the fix.

### Fix

| Layer | Change |
|-------|--------|
| **Web** | Build complete payload in `handleComplete` and pass to `mutate(payload)`; always send `assignedUserId` when follow-up enabled; default assignee via functional `setState` only when still empty |
| **Adapter** | Require `followUp.assignedUserId` when `followUp.enabled`; resolve assignee once in controller before `CreateActivityCommand` |
| **Gen** | `[AssignDebug]` logs: payload, validate/commit responses, refetched solver fields |

### Debug log keys (temporary)

```
[AssignDebug] selectedAssignedUserId / request.assignedUserId / resolvedAssignee
[AssignDebug] command.AssignedUserId / resolvedSolverUserId / resolvedResponsibleUserId
[AssignDebug] outgoing Gen POST payload
[AssignDebug] raw Gen POST validate response
[AssignDebug] raw Gen POST commit response
[AssignDebug] refetched SolverUser_ID / refetched ResponsibleUser_ID
```

### Verified (API repro)

`scripts/repro_3b1_assign_bug.py` — JANO session, assign JAROJ:

```
gen raw SolverUser_ID=2620000101 ResponsibleUser_ID=2620000101
```

---

## 9. Out of scope

- Role-only assignment (`SolverRole_ID` without user) — see 3B.0 Option B for My Day role expansion.
- `GET /api/v1/roles` — deferred.
- Removing creator visibility for assigner — requires Gen/platform change, not Mobile-only.
