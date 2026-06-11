# Sprint 4.0B.1 — Complete / Handover UX Polish

**Status:** Implemented (UX labels + guidance); validation unchanged  
**Date:** 2026-06-09  
**Depends on:** [3B.4 handover UX](sprint-3b-4-handover-ux-simplification.md), [3B follow-up context](sprint-3b-followup-source-context.md), [4.0B minimal create](sprint-4-0b-minimal-create-activity.md)

---

## 1. Problem

When completing an activity with **Naplánovať ďalší krok** enabled, the form shows:

- **Nový výsledok** (required)
- Predmet, Termín, Priradený používateľ

Users perceive this as entering information twice. In practice they should type **once** — the outcome field serves both as the completion note and as context for the assignee of the next activity. The workflow is technically correct (since 3B.4 removed duplicate **Popis**), but the label does not communicate reuse.

---

## 2. Task 1 — Current data flow (verified in code)

### 2.1 End-to-end diagram

```
User: "Nový výsledok" textarea (ActivityDetailPage)
        │
        ▼
PUT /api/v1/activities/{id}/complete
  body: { answer, followUp?: { enabled, subject, scheduledStart, assignedUserId } }
        │
        ├─► ActivityService.CompleteAsync
        │     • AppendAnswer(existing Answer, new text, Now, authorDisplayName)
        │     • PUT source Status = 2 (Dokončená)
        │     • Returns completedDetail (merged Answer on source)
        │
        └─► if followUp.enabled:
              ActivityCreateService.CreateAsync
                • SourceDescription = completedDetail.Description
                • SourceAnswer      = completedDetail.Answer  (includes new outcome)
                • ResolveFollowUpTextFields → child Description + Answer
                • POST crmactivities with Source_ID
                • Gen sets source → Status 3 (Odovzdaná) on child commit
```

### 2.2 Where text is stored

| User input | Written to (source) | Copied to (child) | Mechanism |
|------------|---------------------|-------------------|-----------|
| **Nový výsledok** | `Answer` — appended with `DD.MM.YYYY HH:mm \| Author` header | Full source `Answer` (incl. new entry + prior notes) | `AppendAnswer` → `completedDetail.Answer` → `ResolveFollowUpTextFields` |
| Prior notes | Already in source `Answer` | Same full `Answer` | Inherited unchanged |
| Source `Description` (visit brief) | Unchanged on complete | Child `Description` | `ResolveFollowUpTextFields` when no `followUp.description` |
| Follow-up **Popis** | — | — | **Removed in 3B.4** — not sent from UI |

### 2.3 `ResolveFollowUpTextFields` rules

```csharp
Description = userDescription ?? sourceDescription
Answer      = sourceAnswer   // always copy when non-empty
```

Since 3B.4, `userDescription` is always `null` from the client → child inherits source **Description**; child **Answer** is the full history including the completion text just appended.

### 2.4 Key files

| Layer | File | Role |
|-------|------|------|
| UI | `ActivityDetailPage.tsx` | Outcome textarea, follow-up fields, `handleComplete` |
| API | `ActivitiesController.Complete` | Validates `answer`, orchestrates complete then create |
| Gen | `ActivityService.CompleteAsync` | `AppendAnswer`, status 2 |
| Gen | `ActivityCreateService.CreateAsync` | `BuildGenPayload`, `Source_ID`, text inheritance |
| Gen | `ActivityMapper.ResolveFollowUpTextFields` | Description/Answer rules |
| Gen | `ActivityMapper.AppendAnswer` | Timestamp + author header, prepend to history |

**Conclusion:** Users type once. The perceived duplication is a **labelling/guidance** problem, not a data-model bug.

---

## 3. Task 2 — Outcome field label (implemented)

| Naplánovať ďalší krok | Label | Placeholder |
|----------------------|-------|-------------|
| `false` | **Nový výsledok** | Zapíšte nový výsledok návštevy alebo hovoru… |
| `true` | **Výsledok a pokyny pre ďalší krok** | Zhrňte výsledok a čo má urobiť ďalší riešiteľ… |

Label switches immediately when the checkbox toggles. No backend change.

**Wording rationale:** “Výsledok a pokyny” signals dual use without implying a second field. Shorter than “Výsledok návštevy a pokyny pre ďalší krok” — fits mobile labels.

---

## 4. Task 3 — Required validation recommendation

### 4.1 Current behaviour

| Layer | Rule |
|-------|------|
| Browser | `required` on textarea → native “Please fill out this field.” |
| Frontend JS | `outcomeRequired` if empty on submit |
| Backend | `answer` required on `PUT …/complete` → 422 |

### 4.2 Option A — Keep mandatory (recommended)

**Pros**

- One intentional entry documents what happened and what the next person should do.
- Audit trail always gets a timestamped, attributed completion line (`AppendAnswer`).
- Aligns with backend contract and existing tests.
- Assignee receives at least one fresh instruction in copied `Answer` history.
- Matches field-sales expectation: completing/handover without any note is exceptional.

**Cons**

- Cannot hand over with only scheduling metadata (subject/date/assignee) and zero new text.
- Users with all context already in older notes must still type something (can be brief).

### 4.3 Option B — Allow empty outcome during handover

**Pros**

- Fastest handover when prior notes are sufficient.
- Removes friction for power users.

**Cons**

- Requires backend + frontend changes (relax validation only when `followUp.enabled`).
- Risk of empty handovers with no new instruction for assignee.
- `AppendAnswer("", …)` would still write a header-only line or need special-casing — messy audit.
- Inconsistent with ABRA expectation that completing a step records an outcome.
- Conflicts with “minimum typing while preserving complete history” — empty outcome weakens history.

### 4.4 Recommendation

**Option A — keep mandatory.** Do not implement Option B in this sprint.

Handover already minimizes typing (one field, no **Popis**). UX polish should clarify reuse, not remove the single required narrative field.

---

## 5. Task 4 — User guidance (implemented)

When **Naplánovať ďalší krok** is checked, helper text below the textarea:

> Text sa uloží do histórie tejto aktivity a celá história sa prenesie do novej aktivity.

Styled with existing `.hint` class; mobile-friendly, one sentence.

---

## 6. Task 5 — Follow-up context inheritance review

| Aspect | Expected (Sprint 3) | Current behaviour | Gap? |
|--------|---------------------|-------------------|------|
| **Description** | Inherit source when user omits follow-up popis | ✓ `completedDetail.Description` → child | None |
| **Answer** | Full source history including new outcome | ✓ `completedDetail.Answer` after `AppendAnswer` | None |
| **Metadata** | Firm, type, refs, dimensions, contact | ✓ From source GET in `CreateAsync` | None |
| **Author on new entry** | Session rep display name on appended line | ✓ `ResolveAuthorDisplayNameAsync` → `AppendAnswer` | None |
| **Timestamp on new entry** | Local `DD.MM.YYYY HH:mm` | ✓ `DateTimeOffset.Now` in `AppendAnswer` | None |
| **Source terminal state** | Odovzdaná (`Status 3`) via `Source_ID` | ✓ Gen on child commit | None |
| **Multi-hop chain merge** | Not in scope | Only immediate source | Documented Phase 2 |
| **Link to source on child UI** | Nice-to-have | Not shown | Future UX |

**Regression note:** Ensure adapter DLL is reloaded after backend changes (known NP-17/NP-18 stale-DLL issue).

---

## 7. Screenshots (manual capture)

After `npm run dev`, on an open activity with **Naplánovať ďalší krok**:

| # | Screen | Shows |
|---|--------|-------|
| 1 | Complete form, checkbox off | Label **Nový výsledok** |
| 2 | Complete form, checkbox on | Label **Výsledok a pokyny pre ďalší krok** + hint |
| 3 | After submit | Success banners; source terminal; child in My Day |
| 4 | Child detail | Inherited **Answer** history with new header line |

---

## 8. Final implementation proposal

### 8.1 Done in 4.0B.1

| Change | Files |
|--------|-------|
| Conditional outcome label + placeholder | `ActivityDetailPage.tsx`, `sk-SK.ts` |
| Handover helper hint | `ActivityDetailPage.tsx`, `sk-SK.ts`, `global.css` |
| Analysis + validation recommendation | This document |

### 8.2 Explicitly not in scope

- Relaxing required outcome validation (Option B)
- New assignment UI (Sprint 4.1)
- Workflow redesign
- Re-adding follow-up **Popis** field
- Multi-hop answer chain merge

### 8.3 Optional follow-ups (later)

- Show “Predchádzajúca aktivita” link on child detail when `Source_ID` present
- Collapse follow-up fields behind checkbox animation for clearer single-screen flow
- Replace browser `required` tooltip with consistent Slovak-only validation (minor)

---

## 9. Files changed

| File | Change |
|------|--------|
| `src/MobileCrm.Web/src/features/activities/ActivityDetailPage.tsx` | Conditional label, placeholder, hint |
| `src/MobileCrm.Web/src/i18n/locales/sk-SK.ts` | New strings |
| `src/MobileCrm.Web/src/styles/global.css` | Hint spacing |
| `implementation/sprint-4-0b-1-handover-ux-polish.md` | This document |

No backend changes.
