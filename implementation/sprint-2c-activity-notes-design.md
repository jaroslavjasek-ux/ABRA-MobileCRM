# Sprint 2C — Activity notes (technical design)

**Status:** Implemented  
**Scope:** Append chronological notes to `Answer` without changing `Status`

---

## 1. Business goal

Reps can add timestamped notes to an open or in-progress activity without completing it.

---

## 2. Gen behaviour

| Aspect | Approach |
|--------|----------|
| Storage | Gen field **`Answer`** (same as completion outcome history) |
| Append format | `ActivityMapper.AppendAnswer()` — separator, `DD.MM.YYYY HH:mm \| Author`, text |
| Status | Unchanged — PUT body includes current Gen `Status` (0 or 1) |
| Write pattern | Validate-then-commit PUT (Sprint 2B) |

---

## 3. API

### `PUT /api/v1/activities/{activityId}/note`

**Request:**

```json
{ "note": "Zákazník požiadal o ponuku do piatka." }
```

**Response:** `200` + `ActivityDetailResponse` (refreshed detail)

**Errors:** Same as start/complete (`404`, `409 NOT_EDITABLE`, `422 VALIDATION_FAILED`)

### Availability (`canAddNote`)

| Status | `canAddNote` |
|--------|:------------:|
| `open` | ✓ (owned) |
| `inProgress` | ✓ (owned) |
| `completed` | ✗ |
| `handedOver` | ✗ |

---

## 4. Adapter flow

```
AddNoteAsync
  → Load activity
  → Preflight: not terminal, owned, CanAddNote
  → mergedAnswer = AppendAnswer(existing, note, now, authorDisplayName)
  → PutStatusAsync(id, firmId, currentGenStatus, answer: mergedAnswer)
  → Refetch → ActivityDetailResponse
```

---

## 5. UI (SCR-006)

- Button **„Pridať poznámku“** when `canAddNote`
- Expandable textarea form; optional read-only previous `Answer`
- Save → `PUT .../note` → invalidate activity detail + My Day

---

## 6. Files

| Layer | Path |
|-------|------|
| Service | `ActivityService.AddNoteAsync` |
| Controller | `ActivitiesController.AddNote` |
| DTO | `AddActivityNoteRequestDto` |
| Web | `ActivityDetailPage`, `api/activities.ts` |
| i18n | `sk-SK.ts` |
