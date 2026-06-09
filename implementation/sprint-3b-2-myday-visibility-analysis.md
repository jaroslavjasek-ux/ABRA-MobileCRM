# Sprint 3B.2 — My Day visibility analysis

**Status:** Analysis complete  
**Date:** 2026-06-09  
**Scope:** Task 3 — why only **Dnes** and **Po termíne** appear; future activities excluded. **No UI changes.**

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| Is excluding future activities intentional? | **Yes** — by design in `MyDayService` since Sprint 0 |
| Aligned with common CRM? | **Partially** — many CRMs have Today + Overdue; **Planned/Upcoming** is also common |
| What does the API return today? | Only `today` + `overdue` arrays; future-owned activities are fetched from Gen then **filtered out** |
| Effort to add future section later? | **Medium** — backend bucket + API DTO + UI section; no Gen change required |

---

## 2. Current Mobile CRM behaviour

### 2.1 UI (`MyDayPage.tsx`)

| Section | i18n key | `formatWhen` |
|---------|----------|--------------|
| **Dnes** | `myDay.today` | `formatTime` → `HH:mm` |
| **Po termíne** | `myDay.overdue` | `formatCalendarDate` → `DD.MM.YYYY` |

No third section. `getMyDay()` called without `date` param → server uses **today**.

### 2.2 API (`GET /api/v1/my-day`)

Response (`MyDayResponseDto`):

```json
{
  "date": "2026-06-09",
  "today": [ /* activities scheduled on date */ ],
  "overdue": [ /* activities scheduled before date */ ],
  "todayCount": 0,
  "overdueCount": 0
}
```

**No `upcoming` / `future` field.**

### 2.3 Backend filter (`MyDayService.cs`)

Pipeline for each owned, open activity with `SheduledStart$DATE`:

```
1. Fetch from Gen: ownership OR (ResponsibleUser, SolverUser, CreatedBy)
2. Status in open | inProgress
3. Bucket by scheduled start vs agenda date (Europe/Bratislava):
     start ∈ [dayStart, dayEnd)  → today
     start < dayStart            → overdue
     start ≥ dayEnd              → DISCARDED (future)
```

```61:75:src/MobileCrm.Adapter.Gen/MyDayService.cs
            var start = row.ScheduledStart.Value;
            if (start >= dayStart && start < dayEnd)
            {
                if (today.Count < take)
                {
                    today.Add(row);
                }
            }
            else if (start < dayStart)
            {
                if (overdue.Count < take)
                {
                    overdue.Add(row);
                }
            }
```

**Agenda date:** `DateOnly.FromDateTime(DateTime.Today)` on server unless `?date=YYYY-MM-DD` (API supports it; **web does not expose** date navigation).

---

## 3. Is this intentional?

### 3.1 Product intent (Sprint 0)

**Môj deň** = actionable **today** + **late** work. Not a full calendar.

Documented in [sprint-3b-0-activity-assignment-analysis.md](sprint-3b-0-activity-assignment-analysis.md) §3.

### 3.2 Side effect on follow-up workflow

Follow-up default **tomorrow 10:00** ([follow-up date analysis](sprint-3b-2-followup-default-date-analysis.md)) → assignee **cannot see** new activity until tomorrow.

This is **consistent with filter rules** but **conflicts with user expectation** after complete + assign.

---

## 4. Comparison with CRM patterns

| Pattern | Mobile CRM today | Examples elsewhere |
|---------|:----------------:|-------------------|
| Today / agenda day | ✓ Dnes | Salesforce “Today”, Dynamics “My Work” |
| Overdue | ✓ Po termíne | Common |
| Upcoming / Planned | ✗ | PipeDrive “Activities” future list, HubSpot tasks |
| Calendar week view | ✗ | Out of scope MVP |

**Conclusion:** Excluding future is a **valid MVP choice** but should be **explicit in UX** (hints after follow-up create) or paired with **today-biased defaults**.

---

## 5. What activities exist but are hidden?

For a rep with activities A (yesterday), B (today), C (tomorrow), all owned + open:

| Activity | Scheduled | Visible bucket |
|----------|-----------|----------------|
| A | Yesterday | **Po termíne** |
| B | Today | **Dnes** |
| C | Tomorrow | **None** (dropped) |
| D | Next week | **None** |

Gen query returns A, B, C, D (up to `take * 4`); server filters to A, B only.

**Ownership reminder:** assignee sees activity if `SolverUser_ID`, `ResponsibleUser_ID`, or `CreatedBy_ID` matches — see 3B.0.

---

## 6. Adding a future / planned section (later)

### 6.1 Backend changes

| Item | Effort |
|------|--------|
| `MyDaySlice` + `Upcoming` list | S |
| Bucket: `start >= dayEnd` (optionally cap range e.g. +14 days) | S |
| `MyDayResponseDto.Upcoming` | S |
| Sort upcoming ascending by `ScheduledStart` | S |
| i18n `myDay.upcoming` | S |

**No Gen API change** — same ownership query; different client-side partition.

### 6.2 API shape (proposed)

```json
{
  "today": [],
  "overdue": [],
  "upcoming": [],
  "upcomingCount": 0
}
```

Optional query: `?upcomingDays=14` to limit horizon.

### 6.3 Frontend changes

| Item | Effort |
|------|--------|
| Third `ActivitySection` on `MyDayPage` | S |
| `formatWhen` → `formatDateTimeFull` or date+time | S |
| Empty state copy | S |

### 6.4 Alternative: link from complete success

Instead of full upcoming section: after follow-up create, show link *„Ďalšia aktivita je naplánovaná na 09.06.2026 10:00“* + open detail (no My Day dependency).

**Effort:** S — complements or replaces upcoming section for MVP.

### 6.5 Recommendation

| Priority | Action |
|----------|--------|
| **Pre-4.0 (quick)** | Fix follow-up default to **today** OR success message with scheduled date |
| **3B.3 / 4.0** | Add **Plánované** section if field users need forward visibility |

---

## 7. Risks if upcoming is added without other fixes

| Risk | Mitigation |
|------|------------|
| My Day becomes long | `take` per bucket + “show more” |
| Duplicate with firm recent activities | Different entry points OK |
| Creator + assignee both see via `CreatedBy_ID` | Document; optional filter later |

---

## 8. References

| File | Role |
|------|------|
| `MyDayService.cs` | Bucket logic |
| `MyDayController.cs` | API |
| `MyDayPage.tsx` | UI sections |
| `ActivityMapper.BuildOwnershipWhere` | Ownership |
| `appsettings.json` → `TimeZoneId` | `Europe/Bratislava` |
