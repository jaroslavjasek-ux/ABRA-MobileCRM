# Sprint 3B.2 — Follow-up default date/time analysis

**Status:** Analysis complete  
**Date:** 2026-06-09  
**Scope:** Task 1 — investigate default termín when **Naplánovať ďalší krok** is enabled. **No implementation.**

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| Where is the default generated? | `followUpDefaults.ts` → `defaultFollowUpStartLocal()` |
| Why next day? | Intentional Sprint 3A.4 design (“tomorrow 10:00 local”, PipeDrive-style) |
| Why 10:00? | Hard-coded business-hour default in same function |
| Is it intentional? | **Yes** — documented in [sprint-3a-4-schedule-next-activity.md](sprint-3a-4-schedule-next-activity.md) |
| Main UX risk | Pre-filled **tomorrow** date + checkbox **checked by default** → user may submit without noticing → follow-up **invisible in My Day until that day** |

---

## 2. Current behaviour

### 2.1 Code path

```
ActivityDetailPage mount
  → useState(defaultFollowUpStartLocal)   // line 43
  → <input type="datetime-local" value={followUpStart} />
  → handleComplete → followUpStartToIso(followUpStart) → API followUp.scheduledStart
  → ActivityCreateService → Gen SheduledStart$DATE
```

**Source:**

```1:7:src/MobileCrm.Web/src/features/activities/followUpDefaults.ts
/** Default follow-up start: tomorrow 10:00 local time (datetime-local input format). */
export function defaultFollowUpStartLocal(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(10, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
```

### 2.2 When the default is applied

| Event | `followUpStart` value |
|-------|---------------------|
| First open of activity detail | Tomorrow 10:00 local (computed at mount) |
| User toggles checkbox off/on | **Unchanged** — not reset |
| After successful complete | **Not reset** in `onSuccess` (only outcome, description cleared) |
| Navigate to another activity | New mount → **new** tomorrow 10:00 |

### 2.3 Companion defaults (same form)

| Field | Default | Source |
|-------|---------|--------|
| **Naplánovať ďalší krok** | Checked (`true`) | `useState(true)` |
| **Predmet** | Current activity subject | `useEffect` on `data.subject` |
| **Priradený používateľ** | Session rep | `useEffect` on `representative.id` |
| **Termín** | Tomorrow 10:00 | `defaultFollowUpStartLocal()` |

---

## 3. Why tomorrow and 10:00?

### 3.1 Design intent (Sprint 3A.4)

From [sprint-3a-4-schedule-next-activity.md](sprint-3a-4-schedule-next-activity.md):

- PipeDrive-style “schedule next step on complete”
- Default termín: **tomorrow 10:00 local**
- Encourage planning the **next** touchpoint, not same-moment duplicate

**Rationale (inferred):**

| Choice | Likely reason |
|--------|----------------|
| **+1 day** | Avoid scheduling in the past; separate from “just finished” moment |
| **10:00** | Common field-sales start / call window; round time easy to remember |
| **Local timezone** | Matches rep’s calendar mental model (browser local, not `Europe/Bratislava` explicitly in TS) |

**Note:** Adapter My Day buckets use `GenOptions.TimeZoneId` (`Europe/Bratislava`). Follow-up default uses **browser local** `Date`. Usually aligned for SK users; edge case if device TZ ≠ server TZ.

### 3.2 Interaction with My Day

My Day (`MyDayService`) only shows activities where `SheduledStart$DATE` is:

- On **agenda date** (default: today) → **Dnes**
- **Before** agenda date → **Po termíne**

Activities with `SheduledStart` **after today** are **dropped** — not returned in API.

**Therefore:** default tomorrow 10:00 → follow-up **will not appear** in assignee’s My Day until that calendar day (unless user changes date to today).

This is the **primary surprise** reported in E2E testing.

---

## 4. UX problems observed

| # | Problem | Severity |
|---|---------|----------|
| P1 | Pre-filled date looks “already chosen” — user may not review | **High** |
| P2 | Tomorrow default → invisible in My Day → “follow-up didn’t work” | **High** |
| P3 | Checkbox checked by default → follow-up created even when user only wanted to complete | **Medium** |
| P4 | No helper text explaining default or My Day visibility | **Medium** |
| P5 | `datetime-local` display format may be US-style on some devices (see [datetime localization doc](sprint-3b-2-datetime-localization.md)) | **Medium** |
| P6 | 10:00 arbitrary for afternoon field work | **Low** |

---

## 5. Recommendations (do not implement in 3B.2)

### 5.1 Preferred: default to **today**, next sensible slot

| Approach | My Day visibility | UX |
|----------|-------------------|-----|
| **Today, now + 1 hour** (rounded) | ✓ Appears in **Dnes** immediately | User sees follow-up right away |
| **Today, 10:00** if before 10:00 else **now + 30 min** | ✓ Dnes | Keeps morning bias |

**Implementation sketch (future):** replace `defaultFollowUpStartLocal()` with `defaultFollowUpStartToday()` using same rounding rules; add one-line hint under field.

### 5.2 Alternative: keep tomorrow but make explicit

- Uncheck **Naplánovať ďalší krok** by default, **or**
- Keep checked but show hint: *„Predvolený termín je zajtra 10:00. Aktivita sa v Mojom dni zobrazí až v tento deň.“*
- Require focus/change on datetime field before first submit (aggressive)

### 5.3 Alternative: no default datetime

- Empty `datetime-local` → validation error until user picks
- Forces conscious choice; more taps

### 5.4 Not recommended

| Approach | Why |
|----------|-----|
| Keep tomorrow + checked + no hint | Reproduces current E2E confusion |
| Default to source activity’s `scheduledStart` | May be in the past after complete |

### 5.5 Recommended decision for Sprint 3B.3 / pre-4.0 fix

**Option 5.1 (today, rounded)** + **helper text** under Termín + consider **unchecking** follow-up checkbox by default.

---

## 6. Verification checklist (for future fix)

1. Complete with follow-up, default unchanged → assignee sees activity in **Dnes** same day.
2. Complete with follow-up, user sets tomorrow → activity **not** in today’s My Day.
3. Complete with checkbox **off** → no follow-up created.
4. TZ: device `Europe/Bratislava`, server `Europe/Bratislava` — bucket matches picker.

---

## 7. References

| Doc / file | Relevance |
|------------|-----------|
| `src/MobileCrm.Web/src/features/activities/followUpDefaults.ts` | Default generator |
| `src/MobileCrm.Web/src/features/activities/ActivityDetailPage.tsx` | Form wiring |
| `src/MobileCrm.Adapter.Gen/MyDayService.cs` | Date buckets |
| [sprint-3a-4-schedule-next-activity.md](sprint-3a-4-schedule-next-activity.md) | Original intent |
| [sprint-3b-2-myday-visibility-analysis.md](sprint-3b-2-myday-visibility-analysis.md) | Why future dates are hidden |
