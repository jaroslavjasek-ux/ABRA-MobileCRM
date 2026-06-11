# Sprint 4.2A — Business Dimensions Analysis

**Status:** Analysis complete  
**Date:** 2026-06-09  
**Baseline:** Sprint 4.1 (create + assignment), Sprint 3 (handover chain)  
**Goal:** Technical and UX design for Business Case, Work Order, and Project on activities — **no implementation**.

**Evidence:** OpenAPI index, [Sprint 3A.2 dimensions](sprint-3a-2-activity-dimensions-analysis.md), adapter `ActivityCreateService` / `ActivityMapper`, live DEMO Gen spike [`scripts/spike_4_2a_business_dimensions.py`](../scripts/spike_4_2a_business_dimensions.py) → [`analysis/spikes/sprint-4-2a-business-dimensions-results.json`](../analysis/spikes/sprint-4-2a-business-dimensions-results.json).

**Environment:** `http://localhost/demo`, credentials `api` / `123`

---

## 1. Executive summary

| Topic | Finding |
|-------|---------|
| **Mapping** | Business Case → `BusTransaction_ID` (`bustransactions`); Work Order → `BusOrder_ID` (`busorders`); Project → `BusProject_ID` (`busprojects`) |
| **Gen APIs** | All three BOs support list (`take`/`skip`), detail GET, `Firm_ID` filter (empty on DEMO seed) |
| **Activity CRUD** | Validate + create pass with each dimension alone or combined; PUT update persists dimensions |
| **Handover inheritance** | **YES** when adapter copies from source GET (already in `BuildFollowUpGenPayload`); Gen does **not** auto-copy via `Source_ID` alone |
| **Filtering UX** | **Recommend Option B** — firm-scoped lists when `Firm_ID` is set on BO rows; fallback global list + client filter on DEMO/production gaps |
| **Config** | `activityDimensions` flags in adapter config + `session.activityFeatures` extension |
| **Mobile Projects** | Same `ActivityContext` / `DimensionRef` model reusable; enable all dimensions by default in Projects module |
| **4.2B scope** | Phase 1: pickers on **Create Activity**; display on detail; handover inherits (already backend-ready) |

---

## 2. Task 1 — Gen API revalidation

### 2.1 Mapping (confirmed)

| Mobile CRM | Slovak (OpenAPI) | Gen BO | Activity FK (POST) | Activity FK (GET) |
|------------|------------------|--------|--------------------|-------------------|
| Business Case | Obchodný prípad | `bustransactions` | `BusTransaction_ID` | `bustransaction_id` |
| Work Order | Zákazka | `busorders` | `BusOrder_ID` | `busorder_id` |
| Project | Projekt | `busprojects` | `BusProject_ID` | `busproject_id` |

OpenAPI refs: `architecture/reference/spike/openapis-index.json` → `bustransactions`, `busorders`, `busprojects`.

### 2.2 Business Cases (`bustransactions`)

| Capability | Result (DEMO 2026-06-09) |
|------------|--------------------------|
| **Endpoint** | `GET bustransactions`, `GET bustransactions/{id}` |
| **Fields** | `ID`, `DisplayName`, `Code`, `Name`, `Firm_ID` — all returned in `select` |
| **Paging** | `take` + `skip` — **works** (`take=5` → 2 rows; `skip=3` → 0) |
| **Filter by firm** | `where=Firm_ID eq '{firmId}'` — **works**, returns **0** on DEMO (seed `Firm_ID: null`) |
| **Search** | `DisplayName like '*…*'` → **400** on DEMO; `Code like '*S*'` → **works** (1 row) |
| **Performance** | List `take=5`: ~418 ms first call; subsequent ~15–25 ms |

**Example list:**

```http
GET /demo/bustransactions?select=ID,DisplayName,Code,Name,Firm_ID&take=5
```

```json
[
  {
    "ID": "3000000101",
    "DisplayName": "Zľavy Zľavové akcie",
    "Code": "Zľavy",
    "Name": "Zľavové akcie",
    "Firm_ID": null
  }
]
```

### 2.3 Work Orders (`busorders`)

| Capability | Result (DEMO) |
|------------|---------------|
| **Endpoint** | `GET busorders`, `GET busorders/{id}` |
| **Fields** | `ID`, `DisplayName`, `Code`, `Name`, `Firm_ID` |
| **Paging** | `take` + `skip` — **works** (3 rows at `take=5`) |
| **Filter by firm** | `Firm_ID eq` — **works**, **0 rows** on DEMO |
| **Search** | `Code like '*S*'` — **works** (3 rows); `DisplayName like` → **400** |
| **Performance** | List `take=5`: ~46 ms |

**Example detail:**

```http
GET /demo/busorders/A000000101?select=ID,DisplayName,Code,Name,Firm_ID
```

```json
{
  "ID": "A000000101",
  "DisplayName": "S Služby",
  "Code": "S",
  "Name": "Služby",
  "Firm_ID": null
}
```

### 2.4 Projects (`busprojects`)

| Capability | Result (DEMO) |
|------------|---------------|
| **Endpoint** | `GET busprojects`, `GET busprojects/{id}` |
| **Fields** | `ID`, `DisplayName`, `Code`, `Name`, `Firm_ID` |
| **Paging** | `take` + `skip` — **works** (4 total; `skip=3` → 1) |
| **Filter by firm** | **0 rows** on DEMO |
| **Search** | `Code like '*S*'` — **0 rows**; use `Name`/`Code` per BO |
| **Performance** | List `take=5`: ~80 ms |

### 2.5 Adapter code today

| Area | State |
|------|-------|
| `ActivityMapper.GetBus*Id` | ✓ Read from activity JSON |
| `ActivityCreateService.BuildFollowUpGenPayload` | ✓ Copies non-null dimensions from **source** on handover/follow-up |
| `BuildStandaloneGenPayload` | ✗ Does **not** set dimensions (4.2B) |
| Mobile API / UI | ✗ No dimension fields or pickers |
| Activity detail DTO | ✗ Dimensions not mapped to API response |

**Delta since Sprint 3A.2:** Follow-up dimension **copy is implemented** in adapter (3B+). Standalone create (4.0B/4.1) still omits dimensions. No new BO list endpoints.

---

## 3. Task 2 — Activity behaviour on DEMO

### 3.1 Create scenarios (Gen validate → commit)

Activity type `2000000101` (Telefón): `BusTransactionReq`, `BusOrderReq`, `BusProjectReq` = **0** (optional).

| Scenario | Validate | Commit | Activity ID | Persisted (full GET) |
|----------|:--------:|:------:|-------------|----------------------|
| Business Case only | 0 errors | 201 | `U110000101` | `bustransaction_id=3000000101` |
| Work Order only | 0 errors | 201 | `W110000101` | `busorder_id=A000000101` |
| Project only | 0 errors | 201 | `Y110000101` | `busproject_id=2000000101` |
| All three | 0 errors | 201 | `0210000101` | All three IDs set |
| None | 0 errors | 201 | `2210000101` | All null |

**Note:** Selective GET with PascalCase `BusTransaction_ID` in `select` returned null in spike tooling; **full GET** confirms persistence.

### 3.2 Update

`PUT crmactivities/{id}` with all three dimension IDs on `0210000101`:

| Field | After PUT |
|-------|-----------|
| `bustransaction_id` | `3000000101` |
| `busorder_id` | `A000000101` |
| `busproject_id` | `2000000101` |

**Result:** ✓ Update passes and persists.

### 3.3 Complete

`PUT /api/v1/activities/{id}/complete` on dimension-rich activity:

| Result | Detail |
|--------|--------|
| HTTP **409** `NOT_EDITABLE` | Activity was **open**, not **in progress** — Mobile adapter requires start before complete |
| Dimensions after attempt | **Unchanged** — all three IDs still present on source GET |

**Conclusion:** Complete workflow does not strip dimensions. 4.2B should re-verify complete after `start` in E2E; no dimension-specific blocker found.

### 3.4 Handover (follow-up create)

Child created with `Source_ID` + explicit dimension copy (adapter behaviour):

| | Source `0210000101` | Child `4210000101` |
|--|---------------------|---------------------|
| `bustransaction_id` | `3000000101` | `3000000101` |
| `busorder_id` | `A000000101` | `A000000101` |
| `busproject_id` | `2000000101` | `2000000101` |

**Result:** ✓ Handover create passes; dimensions match source.

### 3.5 Validation matrix (summary)

| Operation | BC only | WO only | Proj only | All three | None |
|-----------|:-------:|:-------:|:---------:|:---------:|:----:|
| Validate | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create | ✓ | ✓ | ✓ | ✓ | ✓ |
| Update | ✓ | ✓ | ✓ | ✓ | ✓ |
| Complete* | ✓† | ✓† | ✓† | ✓† | ✓† |
| Handover | ✓ | ✓ | ✓ | ✓ | ✓ |

\* Via adapter complete API.  
† Dimensions retained; complete requires **start** first (409 otherwise) — not dimension-related.

---

## 4. Task 3 — Inheritance behaviour

### 4.1 Current adapter (handover / follow-up)

```268:284:src/MobileCrm.Adapter.Gen/ActivityCreateService.cs
        var busTransactionId = ActivityMapper.GetBusTransactionId(sourceRoot);
        if (!string.IsNullOrWhiteSpace(busTransactionId))
        {
            body["BusTransaction_ID"] = busTransactionId;
        }
        // ... BusOrder_ID, BusProject_ID similarly
```

| Question | Answer |
|----------|--------|
| Does Gen auto-inherit dimensions via `Source_ID`? | **No** — confirmed in [3A.2](sprint-3a-2-activity-dimensions-analysis.md) and reconfirmed 2026-06-09 |
| Does Mobile adapter inherit on handover? | **Yes** — copies non-null IDs from source GET into child POST |
| Standalone create? | **No inheritance** — no source activity |
| User override on handover (4.2B)? | Not in adapter today; 4.2B Phase 2 may add optional picker overrides |

### 4.2 Inheritance matrix

| Child create path | `BusTransaction_ID` | `BusOrder_ID` | `BusProject_ID` |
|-------------------|:-------------------:|:-------------:|:---------------:|
| Follow-up / handover (current code) | Copy if source set | Copy if source set | Copy if source set |
| Standalone create (4.0B) | Omit | Omit | Omit |
| Standalone create (4.2B planned) | User picker / omit | User picker / omit | User picker / omit |

---

## 5. Task 4 — Filtering strategy

### 5.1 Options

| Option | Behaviour | Pros | Cons |
|--------|-----------|------|------|
| **A — Global list** | Show all BC/WO/Project rows | Simple; works on DEMO | Long lists in production; unrelated firms |
| **B — Firm-scoped** | `where=Firm_ID eq '{activityFirmId}'` | Matches user mental model (“deals for Alfa”) | Empty on DEMO; depends on data quality |

### 5.2 Recommendation: **Option B with fallback**

When user selects firm **Alfa s.r.o.** on Create Activity:

1. **Primary:** Load each dimension list filtered by `Firm_ID eq '{firmId}'`.
2. **If empty** (DEMO or unlinked data): Fallback to **global list** (`take=50`) with **client-side** filter on `DisplayName` / `Code` / `Name` as user types.
3. **Search:** Prefer server `Code like '*{q}*'` or `Name like '*{q}*'` (DEMO rejects `DisplayName like`); supplement with client filter on loaded page.
4. **Validation:** When BO row has non-null `Firm_ID`, reject selection if `Firm_ID ≠ activity.Firm_ID` (422).

Repeat same pattern for **Business Cases**, **Work Orders**, and **Projects**.

### 5.3 UX flow

```
Firma selected → enable dimension pickers (if feature flags on)
    → fetch firm-scoped lists (parallel)
    → empty? fetch global take=50 + local typeahead
    → optional: show hint "Žiadne zákazky pre tohto zákazníka — zobrazujem všetky"
```

### 5.4 Performance notes (DEMO)

| BO | Typical list latency |
|----|---------------------|
| `bustransactions` | 15–420 ms |
| `busorders` | 15–50 ms |
| `busprojects` | 20–80 ms |

Production: cache dimension pages per `firmId` in React Query (`staleTime` 60s); paginate with `take`/`skip` or “load more”.

---

## 6. Task 5 — Configuration model

### 6.1 Proposed adapter config

```json
{
  "ActivityFeatures": {
    "CreateActivity": true
  },
  "ActivityDimensions": {
    "BusinessCase": true,
    "WorkOrder": true,
    "Project": true
  }
}
```

| Class | Section |
|-------|---------|
| `ActivityFeatureOptions` | Existing — extend sibling `ActivityDimensionOptions` |
| `GenOptions` | Unchanged reference defaults |

### 6.2 Session capabilities (extend 4.0B pattern)

```json
{
  "activityFeatures": {
    "createActivity": true,
    "dimensions": {
      "businessCase": true,
      "workOrder": true,
      "project": true
    }
  }
}
```

Frontend reads flags once from `GET /session`; hides disabled pickers without redeploy.

### 6.3 Override: activity type `*Req` flags

```http
GET crmactivitytypes/{id}?select=BusTransactionReq,BusOrderReq,BusProjectReq
```

| `*Req` | Config `true` | UI | Adapter |
|--------|:-------------:|-----|---------|
| 0 optional | ✓ | Optional picker | Send when selected |
| 1 required | ✓ | **Required** picker | Must send valid ID |
| 2 hidden | ✓ | Hidden | Never send |
| any | **false** | Hidden | Never send |

**Precedence:** `*Req === 2` wins over config `true` (log warning in adapter).

### 6.4 Default behaviour (4.2B)

| Module | Suggested defaults |
|--------|-------------------|
| **Mobile CRM** | All `false` until customer enables (matches roadmap) |
| **DEMO dev** | All `true` for testing |

---

## 7. Task 6 — Mobile Projects compatibility

### 7.1 Shared model (from 3A.2 — still valid)

```typescript
interface ActivityContext {
  firm: FirmRef;
  contact?: ContactRef;
  businessCase?: DimensionRef;
  workOrder?: DimensionRef;
  project?: DimensionRef;
}

interface DimensionRef {
  id: string;
  displayName: string;
  code?: string;
}
```

### 7.2 Reuse across products

| Future Projects feature | Dimension use |
|-------------------------|---------------|
| **Project work** | `BusProject_ID` primary; optional WO/BC |
| **Time reporting** | Activity + dimensions as cost/analytic context (same FKs on `crmactivities`) |
| **Service activities** | `BusOrder_ID` (zákazka) links service order |
| **Technician work logs** | Same activity note/complete/history; dimensions unchanged |

### 7.3 Projects-specific extensions (later, no CRM redesign)

| Enhancement | Approach |
|-------------|----------|
| Cascade pickers | `busprojectsource` / `busordersource` filters — additive API query params |
| Stricter firm link | Enforce `Firm_ID` match when BO has firm |
| Default flags | Projects app config: all dimensions `true` |

**Avoid:** Separate parallel field names or duplicate BO services — one adapter dimension layer serves CRM and Projects.

---

## 8. Task 7 — Sprint 4.2B implementation design

### 8.1 Backend

#### New / extended services

| Component | Responsibility |
|-----------|----------------|
| `IDimensionLookupService` | Firm-scoped + search list for three BO types |
| `ActivityMapper` | Already has getters — add optional display resolve |
| `ActivityCreateService` | Extend `BuildStandaloneGenPayload` with dimension IDs |
| `ApiMapping` | Map dimension DTOs on detail response |

#### API changes

| Endpoint | Change |
|----------|--------|
| `GET /api/v1/firms/{firmId}/business-cases?q=&take=&skip=` | New — wraps `bustransactions` |
| `GET /api/v1/firms/{firmId}/work-orders?…` | New — wraps `busorders` |
| `GET /api/v1/firms/{firmId}/projects?…` | New — wraps `busprojects` |
| `POST /api/v1/activities/create` | Add optional `businessCaseId`, `workOrderId`, `projectId` |
| `GET /api/v1/activities/{id}` | Add optional `businessCase`, `workOrder`, `project` objects |
| `GET /api/v1/session` | Extend `activityFeatures.dimensions` |

#### DTO sketch

```csharp
public sealed class ActivityDimensionDto
{
    public required string Id { get; init; }
    public required string DisplayName { get; init; }
    public string? Code { get; init; }
}

// StandaloneCreateActivityRequestDto
public string? BusinessCaseId { get; init; }
public string? WorkOrderId { get; init; }
public string? ProjectId { get; init; }
```

#### Validation rules

| Rule | Layer |
|------|-------|
| Feature flag off | Omit field; 422 if client sends ID |
| `*Req === 1` | 422 if missing when type requires |
| `*Req === 2` | Strip/ignore client value |
| Invalid FK | Gen validate → 422 |
| Firm mismatch | 422 when BO `Firm_ID` set and ≠ activity firm |
| Handover | Inherit from source; optional override IDs in 4.2B Phase 2 |

#### Inheritance rules (unchanged for handover)

Copy non-null source dimensions unless user override provided (Phase 2).

### 8.2 Frontend

#### Create Activity (Phase 1)

Insert after **Priradený používateľ**, before **Popis** (only if flags enabled):

| Field | Control |
|-------|---------|
| Obchodný prípad | Optional/required select + search |
| Zákazka | Optional/required select + search |
| Projekt | Optional/required select + search |

- Disabled until firm selected.
- Labels: `DisplayName` (or `Code — Name`).
- Reuse firm-search typeahead pattern; `staleTime` caching.

#### Activity detail

Read-only rows when dimension present:

| Section | Content |
|---------|---------|
| Obchodný prípad | `displayName` |
| Zákazka | `displayName` |
| Projekt | `displayName` |

#### Feature flags

`session.activityFeatures.dimensions.*` gates visibility.

#### Edit Activity (future)

Out of 4.2B Phase 1 — design for `PUT /activities/{id}` dimension update when `canEdit`.

### 8.3 Rollout plan

| Phase | Scope |
|-------|--------|
| **4.2B Phase 1** | Config + session flags; firm-scoped list APIs; create activity pickers; detail display; standalone create mapping |
| **4.2B Phase 2** | Handover form optional dimension override; inherit default from source |
| **4.2C / 4.3+** | Edit activity dimensions; activity-type required enforcement UI; classification pickers (4.3) |

### 8.4 Testing plan (4.2B)

| Test | Expect |
|------|--------|
| Create with each dimension | IDs on Gen GET |
| Create with all three | All persisted |
| Firm filter | Returns subset when data linked |
| Handover | Child inherits BC/WO/Proj |
| Feature flag off | Field hidden; omitted from POST |
| `*Req=1` type | 422 without required dimension |

---

## 9. UX recommendations

| Topic | Recommendation |
|-------|----------------|
| Picker order | Business Case → Work Order → Project (optional cascade in Projects later) |
| Labels | Slovak: Obchodný prípad, Zákazka, Projekt |
| Empty firm list | Show hint + global fallback |
| Required firm first | Dimension pickers locked until firm chosen |
| Detail | Show dimension name, not raw ID |
| Handover | No extra fields in Phase 1 — silent inherit; Phase 2 add advanced override |

---

## 10. Open questions

| ID | Question |
|----|----------|
| OQ-4.2A-01 | Production: what % of `busorders` have `Firm_ID` populated? |
| OQ-4.2A-02 | Hard vs soft firm-dimension consistency rule? |
| OQ-4.2A-03 | Expose pipeline `PipeLineStatus_ID` with work order picker? (out of 4.2B) |
| OQ-4.2A-04 | Max `take` for dimension lists on mobile — 30 or 50? |

---

## 11. Evidence files

| Artifact | Path |
|----------|------|
| Spike script | `scripts/spike_4_2a_business_dimensions.py` |
| Live results | `analysis/spikes/sprint-4-2a-business-dimensions-results.json` |
| Prior analysis | `implementation/sprint-3a-2-activity-dimensions-analysis.md` |
| Handover copy | `src/MobileCrm.Adapter.Gen/ActivityCreateService.cs` |

---

## 12. Screenshots (for 4.2B implementation)

Not applicable in analysis sprint. Suggested captures after 4.2B:

1. Create form with three dimension pickers (firm selected)
2. Empty firm-scoped state with fallback hint
3. Activity detail showing Obchodný prípad / Zákazka / Projekt
4. Handover child detail with inherited dimensions

---

*No code, frontend, or backend changes in Sprint 4.2A.*
