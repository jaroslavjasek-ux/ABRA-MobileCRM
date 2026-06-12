# Sprint 4.3B.1 — Classification Validation UX

**Status:** Complete  
**Date:** 2026-06-12  
**Depends on:** [4.3B classification](sprint-4-3b-activity-classification.md)  
**Scope:** UX hardening only — no dependent selectors, no business logic changes

---

## 1. Root cause analysis

### Scenario

ABRA has two activity areas on DEMO:

| Area | Code | Types / queues configured |
|------|------|---------------------------|
| Spoločná | `Sp` | Tel, Obch + all queues |
| Test | `TT` | **None** (misconfigured) |

Mobile CRM lists both areas from `crmactivityareas`. User selects **TT**, then picks **Tel** and **PrHo** from global type/queue catalogs (valid rows, but not allowed for TT).

### What Gen does

Gen `POST crmactivities?validation=true` rejects the combination. Typical error:

```json
{
  "field": "activitytype_id",
  "code": 803,
  "message": "Chyba v zadaní položky Typ aktivity",
  "displayLabel": "Typ aktivity"
}
```

The failure is **ABRA configuration**, not a Mobile CRM bug. Before 4.3B.1 the adapter returned:

```text
Gen rejected the activity create.
```

which reads like an application crash.

### Evidence

[`analysis/spikes/sprint-4-3b-1-classification-validation-results.json`](../analysis/spikes/sprint-4-3b-1-classification-validation-results.json)  
Spike script: [`scripts/spike_4_3b_1_classification_validation.py`](../scripts/spike_4_3b_1_classification_validation.py)

---

## 2. Gen error structure

Validation errors live under `@meta.validation.errors`:

```json
{
  "@meta": {
    "validation": {
      "errors": {
        "count": 3,
        "values": [
          {
            "activitytype_id": {
              "@code": 803,
              "@description": "Chyba v zadaní položky Typ aktivity",
              "@displaylabel": "Typ aktivity",
              "@clsid": "SMOEDRFJASV4P4XCFPYBZ1UYYO"
            }
          }
        ]
      }
    }
  }
}
```

### Classification-related fields (DEMO)

| Gen field | Code | Slovak label | Example message |
|-----------|------|--------------|-----------------|
| `actqueue_id` | **800** | Rad aktivít | Chyba v zadaní položky Rad aktivít |
| `period_id` | **801** | Obdobie | Objekt „Rad aktivít" nemá identitu (queue missing) |
| `activitytype_id` | **803** | Typ aktivity | Chyba v zadaní položky Typ aktivity |
| `activityarea_id` | — | Oblasť aktivít | Not observed on DEMO; mapped when Gen returns it |

**TT area probe:** fails with `activitytype_id` / 803 (type invalid for area), sometimes with `nextcontact$date` / `tradedate$date` (846/849) as side effects — those are **not** treated as classification errors.

---

## 3. Error mapping

### Backend detection

`GenValidation.HasClassificationErrors()` returns true when any error targets:

- `activityarea_id`
- `activitytype_id`
- `actqueue_id`
- `period_id` with code **801** (queue-related)

### API mapping

| Condition | HTTP | API `code` | User-facing (SK via i18n) |
|-----------|------|------------|---------------------------|
| Classification Gen error | 422 | `CLASSIFICATION_INVALID` | Vybraná klasifikácia aktivity nie je platná… |
| Other Gen validation | 422 | `VALIDATION_FAILED` | Unchanged |
| Adapter field validation | 422 | `VALIDATION_FAILED` | Unchanged (e.g. missing `actQueueId`) |

### Before / after

| | Before | After |
|---|--------|-------|
| **API code** | `VALIDATION_FAILED` | `CLASSIFICATION_INVALID` |
| **API message** | Gen rejected the activity create. | Selected activity classification is not valid… |
| **UI (SK)** | Same generic English text | Structured Slovak configuration guidance |

**After (UI):**

```text
Vybraná klasifikácia aktivity nie je platná.

Skontrolujte konfiguráciu:
• Oblasť aktivity
• Typ aktivity
• Rad aktivity

Ak problém pretrváva, kontaktujte administrátora ABRA.
```

---

## 4. Implementation

| Layer | File | Change |
|-------|------|--------|
| Gen parsing | `GenValidation.cs` | `ParseErrors`, `HasClassificationErrors` |
| Create service | `ActivityCreateService.cs` | Map validate/commit failures to `ClassificationValidationFailed` |
| API | `ActivitiesController.cs` | `CLASSIFICATION_INVALID` response |
| Frontend | `CreateActivityPage.tsx` | Handle `CLASSIFICATION_INVALID` → i18n message |
| i18n | `sk-SK.ts` | `createActivity.classificationInvalid` |
| CSS | `global.css` | `white-space: pre-line` on form error |

**Explicitly unchanged:** lookup APIs, selector logic, payload shape, dependent filtering.

---

## 5. Verification

```bash
ADAPTER_URL=http://localhost:5087/api/v1 python scripts/verify_sprint_4_3b_1_classification_validation_ux.py
```

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | Sp + Tel + PrHo create | 200 | PASS |
| 2 | TT + Tel + PrHo create | 422 | PASS |
| 3 | Error code | `CLASSIFICATION_INVALID` | PASS |
| 4 | Message not "Gen rejected" | — | PASS |
| 5 | Missing queue (adapter) | `VALIDATION_FAILED` | PASS |

**6/6 PASS** (2026-06-12)

### Manual checklist

- [ ] Create Activity → select area **TT** → Tel → PrHo → submit
- [ ] See Slovak configuration message (not "Gen rejected")
- [ ] Valid Sp classification still creates activity
- [ ] My Day / complete / handover unchanged

### Screenshots

Capture manually:

1. **Before:** generic "Gen rejected the activity create." (pre-4.3B.1 build)
2. **After:** multi-line Slovak classification guidance with bullet list

---

## 6. Out of scope (future sprint)

- Area → Type dependent selectors
- Type → Queue filtering
- Automatic fallback when configuration is invalid
- ABRA configuration repair tools

---

## 7. Artefacts

| Path | Purpose |
|------|---------|
| `analysis/spikes/sprint-4-3b-1-classification-validation-results.json` | Gen error evidence |
| `scripts/spike_4_3b_1_classification_validation.py` | Spike |
| `scripts/verify_sprint_4_3b_1_classification_validation_ux.py` | API verification |
