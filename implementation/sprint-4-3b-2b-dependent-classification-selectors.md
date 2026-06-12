# Sprint 4.3B.2B — Dependent Classification Selectors

**Status:** Complete  
**Date:** 2026-06-12  
**Depends on:** [4.3B classification](sprint-4-3b-activity-classification.md), [4.3B.2A dependency analysis](sprint-4-3b-2a-classification-dependency-analysis.md)

---

## 1. Summary

Mobile CRM Create Activity now filters **Activity Type** and **Activity Queue** based on the selected **Activity Area** (and type for queues). All filtering is derived from **Gen validate probes** — no hardcoded compatibility rules.

Users are guided to valid combinations **before** submit. Invalid combinations surface configuration errors and block creation.

---

## 2. Dependency model

ABRA does not expose Area→Type or Area+Type→Queue relationships as OData foreign keys. **Gen `POST crmactivities?validation=true`** is the authoritative source.

```
Activity Area
    ↓ validate-probe filter
Allowed Types

Activity Area + Activity Type
    ↓ validate-probe filter
Allowed Queues
```

### DEMO matrix (evidence, not hardcoded)

| Area | Allowed types | Allowed queues (per type) |
|------|---------------|---------------------------|
| **Sp** (`2000000101`) | Tel, Obch | Tel → PrHo, OdHo; Obch → NP, PS, RK |
| **TT** (`3000000101`) | Te (auto) | Te → **none** |

Evidence: [`analysis/spikes/sprint-4-3b-2a-classification-dependency-results.json`](../analysis/spikes/sprint-4-3b-2a-classification-dependency-results.json)

---

## 3. API contracts

All endpoints require session bearer token. Query params: `q`, `take` (1–50), `skip`.

### `GET /api/v1/activity-areas`

Unchanged — full catalog from `crmactivityareas`.

### `GET /api/v1/activity-types?areaId={id}`

| Param | Required | Behaviour |
|-------|----------|-----------|
| `areaId` | No | When present: validate-probe filter for area. When absent: full catalog (backward compatible). |

**Examples (DEMO):**

| `areaId` | Result |
|----------|--------|
| `2000000101` (Sp) | Tel, Obch |
| `3000000101` (TT) | Te |

### `GET /api/v1/activity-queues?areaId={id}&activityTypeId={id}`

| Param | Required | Behaviour |
|-------|----------|-----------|
| `areaId` | With `activityTypeId` | Validate-probe filter for area+type |
| `activityTypeId` | With `areaId` | Validate-probe filter for area+type |
| Either absent | — | Full catalog (backward compatible) |

**Examples (DEMO):**

| Area | Type | Result |
|------|------|--------|
| Sp | Tel | PrHo, OdHo |
| Sp | Obch | NP, PS, RK |
| TT | Te | `[]` |

### Response shape (unchanged)

```json
{
  "items": [
    { "id": "2000000101", "code": "Tel", "name": "Telefón", "displayName": "Tel Telefón" }
  ],
  "total": 1,
  "hasMore": false
}
```

---

## 4. Validate-probe filtering (backend)

**Service:** `ClassificationValidateProbeService` (`MobileCrm.Adapter.Gen`)

### Type probe (per candidate type)

1. Load all types from `crmactivitytypes`.
2. For each candidate, build minimal activity body with:
   - `ActivityArea_ID` = selected area
   - `ActivityType_ID` = candidate
   - `ActQueue_ID` = any catalog queue (probe placeholder)
   - Reference fields from `Gen.ReferenceDefaults` + `ClassificationProbeFirmId`
3. `POST crmactivities?validation=true`
4. **Allowed** when:
   - No `activitytype_id` field error, **and**
   - Resolved type matches candidate (handles TT coercion edge case)

### Queue probe (per candidate queue)

1. Load all queues from `crmactivityqueues`.
2. For each candidate, probe with area + type + candidate queue.
3. If type `issheduled=true` (Obch on DEMO), include `NextContact$DATE` + `TradeDate$DATE`.
4. **Allowed** when no `actqueue_id` field error and resolved queue matches candidate.

### Configuration

`appsettings.json`:

```json
{
  "Gen": {
    "ClassificationProbeFirmId": "4000000101",
    "ReferenceDefaults": {
      "DivisionId": "2000000101",
      "SolverRoleId": "1000000101"
    }
  }
}
```

Probe firm must be a valid DEMO firm for validate payloads.

---

## 5. Validation flow (frontend)

```mermaid
sequenceDiagram
  participant UI as CreateActivityPage
  participant API as Adapter
  participant Gen as Gen validate

  UI->>API: GET /activity-areas
  Note over UI: User selects Area (or auto)
  UI->>API: GET /activity-types?areaId=...
  API->>Gen: probe each type candidate
  API-->>UI: filtered types
  Note over UI: 0 → config error; 1 → auto/hide; N → picker
  UI->>API: GET /activity-queues?areaId=...&activityTypeId=...
  API->>Gen: probe each queue candidate
  API-->>UI: filtered queues
  Note over UI: 0 → config error + create disabled
```

### Cascade rules

| Event | Action |
|-------|--------|
| **Area changes** | Clear type + queue; reload types |
| **Type changes** | Clear queue; reload queues |

Implemented via `parentKey` on `useAbraCatalogSelector` — value resets when parent key changes.

### Selector enablement

| Selector | Enabled when |
|----------|--------------|
| Area | `classification.area` flag |
| Type | Firm selected + area ready (area selected or area hidden) |
| Queue | Firm + area ready + type selected + type not in config error |

### Auto-selection (unchanged ABRA pattern)

| Count | Behaviour |
|-------|-----------|
| 0 | Configuration error — field message + submit disabled |
| 1 | Auto-select; picker hidden when `autoHideSingleValue` |
| 2+ | Picker shown; required selection |

**TT example:** one type (Te) → auto-selected, picker hidden → queue probe returns 0 → queue configuration error.

---

## 6. Configuration error messages (Slovak)

| Condition | Message |
|-----------|---------|
| 0 types for area | Pre vybranú oblasť aktivity nie sú v ABRA nakonfigurované žiadne typy aktivít. |
| 0 queues for area+type | Pre vybranú kombináciu oblasti a typu aktivity nie sú v ABRA nakonfigurované žiadne rady aktivít. |
| 0 areas (unchanged) | Chyba konfigurácie — nie sú dostupné žiadne hodnoty. |

Create button: `disabled={busy || classificationConfigurationError}`.

---

## 7. Files changed

| Layer | File | Change |
|-------|------|--------|
| Gen | `ClassificationValidateProbeService.cs` | **New** — probe filtering |
| Gen | `GenValidation.cs` | `HasFieldError()` |
| Gen | `GenOptions.cs` | `ClassificationProbeFirmId` |
| Gen | `ServiceCollectionExtensions.cs` | Register probe service |
| Adapter | `ClassificationLookupControllers.cs` | `areaId` / `activityTypeId` query params |
| Adapter | `appsettings.json` | Probe firm id |
| Web | `api/classification.ts` | Dependent query params |
| Web | `api/queryKeys.ts` | Keys include parent ids |
| Web | `hooks/useAbraCatalogSelector.ts` | `parentKey` cascade reset |
| Web | `CreateActivityPage.tsx` | Dependent selectors + error messages |
| Web | `i18n/locales/sk-SK.ts` | Specific configuration messages |
| Verify | `scripts/verify_sprint_4_3b_2b_dependent_classification.py` | Scenarios A–D + regression |

---

## 8. Verification matrix

**Script:** `scripts/verify_sprint_4_3b_2b_dependent_classification.py`  
**Run:** `ADAPTER_URL=http://localhost:5088/api/v1 python scripts/verify_sprint_4_3b_2b_dependent_classification.py`

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| A | Area = Sp → types | Tel, Obch | **PASS** |
| B | Sp + Tel → queues | PrHo, OdHo | **PASS** |
| C | Sp + Obch → queues | NP, PS, RK | **PASS** |
| D | TT → types | Te only (auto) | **PASS** |
| D | TT + Te → queues | `[]` | **PASS** |
| — | Global `/activity-types` | 3 types | **PASS** |
| — | Global `/activity-queues` | 5 queues | **PASS** |
| — | Session classification flags | unchanged | **PASS** |

**Result: 8/8 PASS** (2026-06-12, adapter build `.adapter-4-3b-2b-verify-out` on port 5088)

---

## 9. Screenshots

Capture manually in Mobile CRM Create Activity:

| # | Steps | Expected UI |
|---|-------|-------------|
| 1 | Firm selected, Area = Sp | Type picker: Tel, Obch |
| 2 | Sp + Tel | Queue picker: PrHo, OdHo |
| 3 | Sp + Obch | Queue picker: NP, PS, RK |
| 4 | Area = TT | Type Te auto-selected (hidden); queue config error; Create disabled |

*(Screenshots not embedded — add PNGs to `implementation/assets/sprint-4-3b-2b/` when captured.)*

---

## 10. Regression checklist

No changes to these flows in 4.3B.2B scope (spot-check / prior verify scripts):

| Area | Verify |
|------|--------|
| My Day | `scripts/verify_sprint_4_1_1_myday_ownership.py` |
| Activity Detail | Manual / existing E2E |
| Notes | Unchanged |
| Complete | Unchanged |
| Handover | Unchanged |
| Assignment | `scripts/verify_sprint_4_1_assignment.py` |
| Business Dimensions | `scripts/verify_sprint_4_2b_business_dimensions.py` |
| Period Resolution | `scripts/verify_sprint_4_2b_3_period_resolution.py` |
| Classification create (Sp) | `scripts/verify_sprint_4_3b_classification.py` |
| Invalid combo UX (post-submit) | `scripts/verify_sprint_4_3b_1_classification_validation_ux.py` |

Dependent filtering **prevents** most invalid combos before submit; 4.3B.1 post-submit messaging remains as fallback.

---

## 11. Design constraints

1. **No hardcoded rules** — compatibility inferred only from Gen validate responses.
2. **Backward compatible APIs** — omitting `areaId` / `activityTypeId` returns full catalogs.
3. **Gen is single source of truth** — same validate endpoint used for create and probes.
4. **Performance** — probes run server-side per request; acceptable for DEMO catalog sizes (≤3 types, ≤5 queues). Future: cache per session if needed.

---

## 12. Related documents

- [4.3B.2A analysis](sprint-4-3b-2a-classification-dependency-analysis.md)
- [4.3B classification](sprint-4-3b-activity-classification.md)
- [4.3B.1 validation UX](sprint-4-3b-1-classification-validation-ux.md)
