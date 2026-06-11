# Sprint 4.1.1 — My Day Ownership Cleanup

**Status:** Implemented  
**Date:** 2026-06-11  
**Depends on:** [3B.0 assignment analysis](sprint-3b-0-activity-assignment-analysis.md), [3B.1 user assignment](sprint-3b-1-user-assignment.md), [4.1 assignment](sprint-4-1-assignment.md)

---

## 1. Problem

After Sprint 4.1, assigning an activity to another user worked in Gen, but **the creator still saw the activity in Môj deň**:

```text
JANO creates activity → assigns to JAROJ
→ JAROJ sees it in My Day ✓
→ JANO still sees it in My Day ✗
```

Root cause: My Day ownership included `CreatedBy_ID`, so creators always matched the filter.

**Business rule:** My Day = activities **I am expected to work on**, not activities I created.

---

## 2. Current filter analysis (before change)

### 2.1 My Day pipeline

```text
GET /api/v1/my-day
  → MyDayService.GetMyDayAsync
  → ActivityMapper.BuildActivitiesQuery(repUserId)
  → Gen GET crmactivities?where={ownership}&take=…
  → client-side: open/in-progress + date bucket (today / overdue)
```

### 2.2 Previous ownership filter

```csharp
// ActivityMapper.BuildOwnershipWhere (before 4.1.1)
"(ResponsibleUser_ID eq '{rep}' or SolverUser_ID eq '{rep}' or CreatedBy_ID eq '{rep}')"
```

Confirmed in code and documented in [3B.0](sprint-3b-0-activity-assignment-analysis.md).

### 2.3 Separate: detail edit ownership

`ActivityMapper.IsOwnedByRepresentative` — used for **activity detail** start/complete/note guards — **still includes** `CreatedBy_ID`:

```csharp
// Unchanged in 4.1.1 — not used by My Day query
ResponsibleUser_ID | SolverUser_ID | CreatedBy_ID
```

Only `BuildOwnershipWhere` was changed (My Day exclusive).

---

## 3. Final filter definition

```csharp
/// My Day ownership: activities the rep is expected to work on.
public static string BuildOwnershipWhere(string repUserId) =>
    $"(ResponsibleUser_ID eq '{repUserId}' or SolverUser_ID eq '{repUserId}')";
```

| Field | My Day (after 4.1.1) | Activity detail actions |
|-------|:--------------------:|:-----------------------:|
| `SolverUser_ID` | ✓ | ✓ |
| `ResponsibleUser_ID` | ✓ | ✓ |
| `CreatedBy_ID` | **✗** | ✓ (unchanged) |

---

## 4. Code changes

| File | Change |
|------|--------|
| `ActivityMapper.cs` | Remove `CreatedBy_ID` from `BuildOwnershipWhere` only |
| `ActivityMapperOwnershipTests.cs` | Unit test: filter excludes `CreatedBy_ID` |

**Not changed:** assignment model, handover workflow, create API, history/`AppendAnswer`, `IsOwnedByRepresentative`.

---

## 5. Verification matrix (DEMO Gen)

**Script:** `scripts/verify_sprint_4_1_1_myday_ownership.py`  
**Results:** `analysis/spikes/sprint-4-1-1-myday-ownership-results.json`  
**Adapter:** `http://localhost:5083` (`.adapter-4-1-1-verify-out`)

| Scenario | Expected | Result |
|----------|----------|:------:|
| **A** JANO → JANO (create) | Visible to JANO | **PASS** |
| **B** JANO → JAROJ (create) | Visible only to JAROJ | **PASS** |
| **C** JANO handover → JAROJ | Child visible only to JAROJ | **PASS** |
| **D** Handover child → JANO | Child visible only to JANO | **PASS** |

### Scenario notes

| ID | Detail |
|----|--------|
| A | Standalone create, `assignedUserId` = JANO |
| B | `inJanoMyDay: false`, `inJaroMyDay: true` |
| C | Complete + follow-up; child not in JANO My Day |
| D | Follow-up child assigned to JANO; not in JAROJ My Day. On DEMO, **JAROJ** `complete+follow-up` returns Gen **401** (permission); My Day outcome verified via documented **proxy** (JANO completes JAROJ-assigned activity with follow-up to JANO). Filter behaviour is the same. |

### Unit tests

`MobileCrm.Adapter.Gen.Tests` — 9 tests pass (including `BuildOwnershipWhere_includes_solver_and_responsible_only`).

---

## 6. Task 3 — Side effects

| Area | Impact |
|------|--------|
| **My Day** | Creators no longer see activities they assigned away. **Intended.** |
| **Activity detail** | Unchanged. Creator may still open by ID (e.g. post-create redirect); `canEdit`/`canComplete` still true via `CreatedBy_ID` in `IsOwnedByRepresentative`. |
| **Search** | No global activity search in Mobile CRM today — **no impact**. |
| **Future reporting** | Reports should not assume My Day = creator visibility. Use explicit solver/responsible filters. |
| **Activity history** | Unchanged. `Answer` append, handover text inheritance unaffected. |
| **Handover / assignment** | Unchanged. Only Gen query filter for My Day changed. |
| **Firm recent activities** | Separate query — **no impact**. |

**Conclusion:** No other feature relied on `CreatedBy_ID` **for My Day listing**. Detail-level creator access remains by design (separate sprint if creators should lose edit rights after assign-away).

---

## 7. Task 4 — Future extensibility (not implemented)

Optional tenant flag for customers who want legacy creator visibility:

```json
{
  "myDay": {
    "includeCreatedActivities": false
  }
}
```

| `includeCreatedActivities` | `BuildOwnershipWhere` |
|----------------------------|------------------------|
| `false` (recommended default) | Solver OR Responsible only |
| `true` | Add `or CreatedBy_ID eq '{rep}'` |

Implement in `GenOptions` / `MyDayOptions` when a customer requests it. Session could expose `myDay.includeCreatedActivities` for transparency.

---

## 8. Screenshots (manual)

After deploy, capture:

1. **JANO My Day** — no activities assigned to JAROJ
2. **JAROJ My Day** — activities JANO created for JAROJ
3. **Create success** — redirect to detail still works for creator

---

## 9. Summary

My Day now answers: **“What should I work on today?”** — not **“What did I create?”**

```text
My Day = SolverUser_ID = me  OR  ResponsibleUser_ID = me
```

`CreatedBy_ID` does not affect My Day visibility.
