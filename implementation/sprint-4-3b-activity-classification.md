# Sprint 4.3B — Activity Classification Implementation

**Status:** Complete  
**Date:** 2026-06-11  
**Depends on:** [4.3A analysis](sprint-4-3a-activity-classification-analysis.md), [4.2B dimensions](sprint-4-2b-business-dimensions.md), [4.2B.3 period fix](sprint-4-2b-3-period-resolution-fix.md)

---

## 1. Summary

Implemented activity classification on **Create Activity** using the generic ABRA Desktop selection pattern:

| Values | Behaviour |
|--------|-----------|
| **0** | Configuration error — creation blocked |
| **1** | Auto-select; picker hidden when `autoHideSingleValue` |
| **2+** | Picker shown; selection required when mandatory |

**DEMO result (Scenario A):** Area hidden (1 value), Type + Queue pickers visible.

---

## 2. Configuration model

`appsettings.json`:

```json
{
  "ActivityClassification": {
    "Area": true,
    "Type": true,
    "Queue": true,
    "Process": false,
    "AutoHideSingleValue": true
  }
}
```

| Flag | Purpose |
|------|---------|
| `Area` | Enable area lookup + payload field |
| `Type` | Enable type lookup; **required** on create |
| `Queue` | Enable queue lookup; **required** on create |
| `Process` | Reserved; **not exposed** in 4.3B |
| `AutoHideSingleValue` | Hide picker when catalog has exactly one value |

Structural defaults (`Division_ID`, `SolverRole_ID`) remain in `Gen.ReferenceDefaults`. Classification no longer hardcoded from config when user selects values.

---

## 3. Session contract

`GET /api/v1/session` → `activityFeatures.classification`:

```json
{
  "activityFeatures": {
    "createActivity": true,
    "dimensions": { "businessCase": true, "workOrder": true, "project": true },
    "classification": {
      "area": true,
      "type": true,
      "queue": true,
      "process": false,
      "autoHideSingleValue": true
    }
  }
}
```

---

## 4. Lookup API contracts

All endpoints require session bearer token. Query params: `q`, `take` (1–50, default 30), `skip`.

### `GET /api/v1/activity-areas`

Gen source: `crmactivityareas`

```json
{
  "items": [
    { "id": "2000000101", "code": "Sp", "name": "Spoločná", "displayName": "Sp Spoločná" }
  ],
  "total": 1,
  "hasMore": false
}
```

### `GET /api/v1/activity-types`

Gen source: `crmactivitytypes`

```json
{
  "items": [
    { "id": "2000000101", "code": "Tel", "name": "Telefón", "displayName": "Tel Telefón" },
    { "id": "3000000101", "code": "Obch", "name": "Obchodný prípad", "displayName": "Obch Obchodný prípad" }
  ],
  "total": 2,
  "hasMore": false
}
```

### `GET /api/v1/activity-queues`

Gen source: `crmactivityqueues`

```json
{
  "items": [
    { "id": "2000000101", "code": "PrHo", "name": "Prichádzajúci hovor", "displayName": "PrHo - Prichádzajúci hovor" },
    { "id": "4000000101", "code": "NP", "name": "Nový predaj", "displayName": "NP - Nový predaj" }
  ],
  "total": 5,
  "hasMore": false
}
```

**Not implemented:** `activity-processes` (analysis only per scope).

---

## 5. Create payload

`POST /api/v1/activities/create` — new optional fields:

| API field | Gen field | Required when |
|-----------|-----------|---------------|
| `activityAreaId` | `ActivityArea_ID` | Optional (Gen auto-resolves if omitted) |
| `activityTypeId` | `ActivityType_ID` | `ActivityClassification.Type = true` |
| `actQueueId` | `ActQueue_ID` | `ActivityClassification.Queue = true` |

**Example (NP + Obch):**

```json
{
  "subject": "Nová aktivita",
  "scheduledStart": "2026-06-13T10:00:00.000Z",
  "firmId": "4000000101",
  "activityTypeId": "3000000101",
  "actQueueId": "4000000101",
  "activityAreaId": "2000000101"
}
```

**Result:** `NP-28/2026`, `period_id: 3F80000101`

**Validate merge unchanged:** `ActivityArea_ID`, `period_id` merged from Gen validate response before commit ([4.2B.3](sprint-4-2b-3-period-resolution-fix.md)).

---

## 6. Selector framework (reusable)

### `useAbraCatalogSelector` (`src/MobileCrm.Web/src/hooks/useAbraCatalogSelector.ts`)

Generic hook implementing ABRA catalog rules. Reusable for future fields and business dimensions refactor.

| Prop | Purpose |
|------|---------|
| `enabled` | Session flag gate |
| `required` | Mandatory when multiple values |
| `autoHideSingleValue` | Hide picker for single-value catalogs |
| `queryKey` / `queryFn` | React Query lookup |

### `CatalogSelectField` (`src/MobileCrm.Web/src/components/CatalogSelectField.tsx`)

Renders picker, configuration error, or nothing (auto-hidden single value).

**No field-specific logic** — Area, Type, and Queue use identical components with different `required` flags.

---

## 7. UI behaviour

Section **Klasifikácia aktivity** on Create Activity:

- **Placement:** After Obchodné väzby, before Termín
- **Visibility:** When firm selected and any classification flag enabled

### DEMO Scenario A

| Field | Catalog | UI |
|-------|---------|-----|
| Oblasť aktivity | 1 (`Sp`) | **Hidden** (auto-selected) |
| Typ aktivity | 2 | **Picker** required |
| Rad aktivity | 5 | **Picker** required |

### Screenshots

Capture manually from running app (`npm run dev` + adapter on 5086):

1. Create Activity with firm selected — Type + Queue visible, Area hidden
2. Type picker open showing Tel / Obchodný prípad
3. Created activity detail showing `NP-xx/2026` or `PrHo-xx/2026`

---

## 8. Backend changes

| File | Change |
|------|--------|
| `ClassificationLookupService.cs` | Gen catalog search |
| `ClassificationLookupControllers.cs` | Three lookup endpoints |
| `ActivityClassificationOptions.cs` | Config POCO |
| `ReferenceDefaultsService.cs` | `TryGetStandaloneDefaults` (Division + SolverRole only) |
| `ActivityCreateService.cs` | User-selected type/queue/area in payload |
| `ActivitiesController.cs` | Validate required type/queue when flags on |
| `SessionController.cs` | Expose `classification.*` |

---

## 9. Verification matrix

Script: [`scripts/verify_sprint_4_3b_classification.py`](../scripts/verify_sprint_4_3b_classification.py)

Run:

```bash
ADAPTER_URL=http://localhost:5086/api/v1 python scripts/verify_sprint_4_3b_classification.py
```

| # | Scenario | Result (2026-06-11) |
|---|----------|---------------------|
| 1 | Session `classification` flags | PASS |
| 2 | `GET /activity-areas` (≥1) | PASS |
| 3 | `GET /activity-types` (≥2) | PASS |
| 4 | `GET /activity-queues` (≥5) | PASS |
| 5 | Missing type/queue → 422 | PASS |
| 6 | Queue NP → `NP-28/2026` | PASS |
| 7 | NP period `3F80000101` (2026) | PASS |
| 8 | Queue PrHo → `PrHo-33/2026` | PASS |
| 9 | PrHo period 2026 | PASS |
| 10 | Omit area → Gen resolves `2000000101` | PASS |
| 11 | `GET /my-day` regression | PASS |

**13/13 PASS** on DEMO via adapter `.adapter-4-3b-verify-out` port 5086.

---

## 10. Regression checklist

| Area | Status | Notes |
|------|--------|-------|
| My Day | PASS | Verified in script |
| Notes | Not automated | No create-path changes |
| Complete | Not automated | Unchanged |
| Handover / follow-up | Not automated | Uses source activity refs, not standalone defaults |
| Assignment | Not automated | Unchanged |
| Business Dimensions | Not automated | Section unchanged; same page |
| Period resolution | PASS | `3F80000101` on NP + PrHo creates |
| Activity Process | N/A | Not in UI or payload |

---

## 11. Out of scope (deferred)

- Activity Process picker (`crmactivityprocesses`)
- Obch-specific `nextcontact$date` / `tradedate$date` UI
- Refactor business dimensions to `useAbraCatalogSelector` (hook ready)
- Classification display on activity detail

---

## 12. Artefacts

| Path | Purpose |
|------|---------|
| `implementation/sprint-4-3a-activity-classification-analysis.md` | Analysis |
| `implementation/sprint-4-3b-activity-classification.md` | This doc |
| `scripts/verify_sprint_4_3b_classification.py` | Verification |
| `src/MobileCrm.Web/src/hooks/useAbraCatalogSelector.ts` | Generic selector |
| `src/MobileCrm.Web/src/components/CatalogSelectField.tsx` | Generic field UI |
