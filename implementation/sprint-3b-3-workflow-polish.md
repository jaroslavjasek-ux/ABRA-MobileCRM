# Sprint 3B.3 — Workflow polish

**Status:** Implemented  
**Date:** 2026-06-08  
**Depends on:** [3B.2 workflow review](sprint-3b-2-workflow-review.md), [3B.2 follow-up default date analysis](sprint-3b-2-followup-default-date-analysis.md), [3B.2 datetime localization](sprint-3b-2-datetime-localization.md)

---

## 1. Goal

Finalize and polish the activity workflow before Sprint 4.0. No new business functionality — only fixes and UX improvements identified during Sprint 3B.2.

---

## 2. Changes made

### Task 1 — Follow-up default date/time

**Problem:** `defaultFollowUpStartLocal()` initialized follow-up to **tomorrow 10:00**. Users who accepted defaults created activities scheduled for the next day, which disappeared from **Môj deň** (My Day only shows today + overdue).

**Fix:** `followUpDefaults.ts` now exposes `defaultFollowUpSchedule()` — **now + 1 hour**, seconds/milliseconds zeroed (full minutes).

| Before | After |
|--------|-------|
| `09.06.2026 10:00` (tomorrow) | `08.06.2026 15:20` (today + 1 h, example) |

**Files:**

- `src/MobileCrm.Web/src/features/activities/followUpDefaults.ts` — rewritten
- `src/MobileCrm.Web/src/features/activities/ActivityDetailPage.tsx` — uses `followUpDate` + `followUpTime` state

### Task 2 — Slovak DateTime UX

**Problem:** Single `datetime-local` input rendered US-style (`06/09/2026 10:00 AM`) with AM/PM on many browsers.

**Fix (MVP):** Split into separate `type="date"` and `type="time"` inputs (`step={60}` for whole minutes). Added a read-only preview line using existing `formatDateTimeFull()` from `i18n/format.ts`:

```
09.06.2026 15:30
```

Format: **DD.MM.YYYY**, **24-hour**, no AM/PM in the preview users rely on for confirmation.

**Files:**

- `src/MobileCrm.Web/src/features/activities/ActivityDetailPage.tsx`
- `src/MobileCrm.Web/src/styles/global.css` — `.follow-up-schedule`, `.follow-up-schedule-preview`

### Task 3 — Remove debug instrumentation

Removed all `[AssignDebug]` logging and the temporary post-create refetch trace added in Sprint 3B.1.

**Removed from:**

- `src/MobileCrm.Adapter/Controllers/ActivitiesController.cs` — create + complete follow-up paths
- `src/MobileCrm.Adapter.Gen/ActivityCreateService.cs` — payload/validate/commit logs, refetch-after-create block; simplified `PostCreateAsync` return type

**Kept intact:**

- `ValidateAssignedUserAsync` / `ResolveAssignedUserId` business validation
- Standard `CreateAsync committed id=…` information log
- Gen validate/commit error handling

---

## 3. API / behaviour

No API contract changes. `followUp.scheduledStart` still sent as ISO-8601 instant; only the **default** and **form UX** changed.

---

## 4. Verification

### Automated

| Check | Result |
|-------|--------|
| `npm run build` (MobileCrm.Web) | **Pass** |
| `dotnet build` MobileCrm.Adapter.Gen | **Pass** |
| `dotnet test` ActivityMapperAppendAnswerTests (4 tests) | **Pass** |
| `grep AssignDebug src/` | **No matches** |

> **Note:** Full `dotnet build` for `MobileCrm.Adapter` may fail while `MobileCrm.Adapter.exe` is running (DLL lock). Stop the adapter process and rebuild to pick up backend changes.

### Task 1 — Default schedule logic

`defaultFollowUpSchedule()`:

1. Takes current local time
2. Adds 60 minutes
3. Rounds to full minutes (`setSeconds(0, 0)`)
4. Returns `{ date: YYYY-MM-DD, time: HH:mm }` for **today** (unless +1 h crosses midnight)

Follow-up with accepted defaults is scheduled **today** → visible in **Môj deň** immediately after creation.

### Task 2 — Slovak preview

On the complete-activity form with **Naplánovať ďalší krok** enabled:

- Date and time are separate native inputs (editing)
- Preview below shows `formatDateTimeFull` output, e.g. `08.06.2026 15:30`
- No AM/PM in preview

### Task 3 — Debug cleanup

Confirmed no `[AssignDebug]` remains in `src/`. Assignment resolution (`assignedUserId` → `SolverUser_ID` / `ResponsibleUser_ID`) unchanged.

### Regression checklist (manual — Gen DEMO + adapter)

| Step | Expected |
|------|----------|
| My Day → open activity | Loads |
| Start activity | Status in progress |
| Add note | Note prepended (newest first) |
| Complete + schedule follow-up (defaults) | Follow-up **today + 1 h** |
| Assign another user (e.g. JAROJ) | `SolverUser_ID` / `ResponsibleUser_ID` set |
| Follow-up in assignee My Day | Visible under **Dnes** |
| Notes after second note | Newest block first (`B\n---\nA`) |

*Manual end-to-end run against `http://localhost/demo` + adapter `:5080` recommended before Sprint 4.0.*

---

## 5. Out of scope (Sprint 4.0)

Not implemented in 3B.3:

- Business Case, Work Order, Project
- Activity Area, Activity Type, Activity Series

---

## 6. Files touched

| File | Change |
|------|--------|
| `followUpDefaults.ts` | Today + 1 h default; split date/time helpers |
| `ActivityDetailPage.tsx` | Split inputs + Slovak preview |
| `global.css` | Follow-up schedule layout |
| `ActivitiesController.cs` | Remove AssignDebug |
| `ActivityCreateService.cs` | Remove AssignDebug + refetch trace |
