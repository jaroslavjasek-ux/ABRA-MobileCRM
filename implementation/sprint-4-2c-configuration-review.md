# Sprint 4.2C — Configuration & Feature Flags Review

**Status:** Analysis complete  
**Date:** 2026-06-11  
**Scope:** Inventory of runtime configuration before Sprint 4.3 (Activity Classification). **No code changes.**

**Baseline sprints:** 4.0B (create), 4.1 (assignment), 4.2B (dimensions), 4.2B.1 (UI), 4.2B.3 (period resolution)

---

## 1. Executive summary

| Area | Configured? | Exposed via session? | Backend enforced? | Frontend enforced? |
|------|:-----------:|:--------------------:|:-----------------:|:------------------:|
| Create Activity | ✓ | ✓ `createActivity` | ✗ | ✓ nav + route redirect |
| Business dimensions (3) | ✓ | ✓ `dimensions.*` | ✗ (APIs always on) | ✓ per-picker hide |
| Assignment on create | ✗ | ✗ | N/A (always in create API) | ✓ UI when create enabled |
| Reference defaults | ✓ | ✗ | ✓ standalone create | N/A (hidden) |
| Activity classification | ✗ | ✗ | N/A | N/A (4.3) |
| UI / typography | ✗ | ✗ | N/A | CSS only (4.2B.1) |

**Tenant model:** One adapter deployment = one `appsettings.json` (per customer/environment). No per-user or per-representative feature flags in Gen.

**Restart:** Adapter configuration changes require **adapter process restart** to take effect (`IOptions<T>` snapshot). Frontend picks up new flags on **next `GET /session`** (React Query may cache up to 30s globally).

---

## 2. Configuration inventory

| Section | Setting | Config path (appsettings) | Default | Purpose |
|---------|---------|---------------------------|---------|---------|
| **ActivityFeatures** | `CreateActivity` | `ActivityFeatures:CreateActivity` | `true` | Enable standalone Create Activity feature |
| **ActivityDimensions** | `BusinessCase` | `ActivityDimensions:BusinessCase` | `true` | Show Obchodný prípad picker on create |
| **ActivityDimensions** | `WorkOrder` | `ActivityDimensions:WorkOrder` | `true` | Show Zákazka picker on create |
| **ActivityDimensions** | `Project` | `ActivityDimensions:Project` | `true` | Show Projekt picker on create |
| **Gen** | `BaseUrl` | `Gen:BaseUrl` | `http://localhost/demo` | Gen API root URL |
| **Gen** | `TimeoutSeconds` | `Gen:TimeoutSeconds` | `60` | HTTP client timeout |
| **Gen** | `TimeZoneId` | `Gen:TimeZoneId` | `Europe/Bratislava` | My Day date bucketing (today/overdue) |
| **Gen** | `FirmSearchWhereTemplate` | `Gen:FirmSearchWhereTemplate` | OData name/code/ICO template | Firm search query |
| **Gen** | `FirmSearchExcludeHidden` | `Gen:FirmSearchExcludeHidden` | `true` | Exclude hidden firms from search |
| **Gen** | `FirmListSelect` | `Gen:FirmListSelect` | field list | OData `$select` for firm list |
| **Gen** | `PersonContactSelect` | `Gen:PersonContactSelect` | field list | OData `$select` for contacts |
| **ReferenceDefaults** | `ActQueueId` | `Gen:ReferenceDefaults:ActQueueId` | `2000000101` | Activity queue / series on standalone create |
| **ReferenceDefaults** | `PeriodId` | `Gen:ReferenceDefaults:PeriodId` | `4000000101` | **Config gate only** (see §4) |
| **ReferenceDefaults** | `DivisionId` | `Gen:ReferenceDefaults:DivisionId` | `2000000101` | Stredisko on standalone create |
| **ReferenceDefaults** | `SolverRoleId` | `Gen:ReferenceDefaults:SolverRoleId` | `1000000101` | Solver role on standalone create |
| **ReferenceDefaults** | `ActivityAreaId` | `Gen:ReferenceDefaults:ActivityAreaId` | `2000000101` | Activity area on standalone create |
| **ReferenceDefaults** | `ActivityTypeId` | `Gen:ReferenceDefaults:ActivityTypeId` | `2000000101` | Activity type on standalone create (Telefón on DEMO) |
| **Gen.SmokeTest** | `LoginName` / `Password` | `Gen:SmokeTest:*` | empty | Optional Gen ping for `/health/ready` |
| **Logging** | `LogLevel` | `Logging:LogLevel` | Information | ASP.NET logging |
| **Hosting** | `AllowedHosts` | `AllowedHosts` | `*` | Host filtering |
| **Frontend** | API base URL | `VITE_API_BASE_URL` (build env) | `/api/v1` | Web → adapter URL |
| **Dev proxy** | Vite proxy target | `vite.config.ts` | `http://localhost:5080` | Local dev only (not runtime config file) |
| **CORS** | Allowed origins | `Program.cs` (hardcoded) | `localhost:5173` | Dev CORS policy |

**Options classes:** `ActivityFeatureOptions`, `ActivityDimensionOptions`, `GenOptions`, `ActivityReferenceDefaultsOptions`  
**Registration:** `Program.cs` → `Configure<T>(GetSection(...))`

---

## 3. Task 1 — Activity Features

### Session shape (actual)

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

Note: `dimensions` is nested under `activityFeatures` in the API (not a top-level `activityDimensions` key). Config file uses separate section `ActivityDimensions`.

### Flag: `createActivity`

| Property | Value |
|----------|-------|
| **Config** | `ActivityFeatures:CreateActivity` (`ActivityFeatureOptions.CreateActivity`) |
| **Default** | `true` |
| **Purpose** | Gate standalone **Nová aktivita** feature (Sprint 4.0B) |
| **Frontend** | `AuthenticatedLayout` — bottom nav link; `CreateActivityPage` — redirect to My Day if false |
| **Backend** | Exposed in session only; **`POST /api/v1/activities/create` is NOT blocked** when false |
| **Tenant-specific** | Per adapter deployment |
| **Restart** | Adapter restart required |
| **Dynamic UI** | On next session fetch after restart (React Query `staleTime` 30s default) |

### Assignment (Sprint 4.1)

No separate feature flag. Assignee picker is part of Create Activity when that page is reachable. Backend always accepts optional `assignedUserId` on create.

---

## 4. Task 2 — Business Dimensions

### Config (appsettings)

```json
"ActivityDimensions": {
  "BusinessCase": true,
  "WorkOrder": true,
  "Project": true
}
```

Class: `ActivityDimensionOptions` (`ActivityDimensionOptions.SectionName = "ActivityDimensions"`).

### Session mapping

| Config (PascalCase) | Session (camelCase) |
|---------------------|---------------------|
| `BusinessCase` | `activityFeatures.dimensions.businessCase` |
| `WorkOrder` | `activityFeatures.dimensions.workOrder` |
| `Project` | `activityFeatures.dimensions.project` |

### Per-dimension behaviour

| Dimension | Frontend when `false` | Frontend when `true` | Backend lookup API |
|-----------|----------------------|----------------------|-------------------|
| Business Case | Hide picker + section if all false | `GET /business-cases` on create | **Always available** (no flag check) |
| Work Order | Hide picker | `GET /work-orders` | **Always available** |
| Project | Hide picker | `GET /projects` | **Always available** |

**Independent enable/disable?** **Yes** on frontend — each boolean controls its own `<select>`. Section **Obchodné väzby** shows only if at least one dimension flag is true and firm is selected.

**Backend create:** Accepts optional `businessCaseId`, `workOrderId`, `projectId` regardless of flags (Sprint 4.2B design: flags affect UI only).

**Restart:** Adapter restart required for config change.

---

## 5. Task 3 — Reference Defaults

Path: `Gen:ReferenceDefaults` → `ReferenceDefaultsService` → `ActivityCreateService`.

| Key | Gen field | Used where | Still needed after 4.2B.3? |
|-----|-----------|------------|----------------------------|
| `ActQueueId` | `ActQueue_ID` | Standalone create payload | **Yes** — sent explicitly |
| `PeriodId` | `Period_ID` | `TryGetConfiguredDefaults` gate only | **Required in config** but **not sent** on standalone create; Gen resolves from `SheduledStart$DATE` via validate merge ([4.2B.3](sprint-4-2b-3-period-resolution-fix.md)) |
| `DivisionId` | `Division_ID` | Standalone create payload | **Yes** — Stredisko |
| `SolverRoleId` | `SolverRole_ID` | Standalone create payload | **Yes** |
| `ActivityAreaId` | `ActivityArea_ID` | Standalone create payload | **Yes** |
| `ActivityTypeId` | `ActivityType_ID` | Standalone create payload | **Yes** — fixed type until 4.3 pickers |

**Follow-up / handover:** Inherits `ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`, `ActivityArea_ID`, `ActivityType_ID` from **source activity** — not from `ReferenceDefaults` (except validate merge on follow-up path).

**Validate merge fields** (`MergeFromValidateResponse`): `activityarea_id`, `actqueue_id`, `period_id`, `division_id`, `solverrole_id`, `activitytype_id` — used on standalone create success path for period (and on error-retry rounds).

**Tenant-specific:** Yes — DEMO IDs must match tenant Gen seed data.

---

## 6. Task 4 — Session contract

### `GET /api/v1/session` / `POST /api/v1/session` response

| Property | Source | Consumer |
|----------|--------|----------|
| `representative` | Gen `securityusers` / profile lookup | `AuthContext`, headers, assignee default |
| `representative.id` | Gen user ID | Create assignee default, ownership |
| `representative.loginName` | Gen | Display |
| `representative.displayName` | Gen | Display, assignee fallback option |
| `representative.email` | Gen | Optional display |
| `representative.employeeNumber` | Gen | Optional display |
| `sessionToken` | Adapter `InMemorySessionStore` | `Authorization: Bearer` (also returned on login) |
| `expiresAt` | Always `null` today | Unused |
| `capabilities` | **Hardcoded** in `SessionController` | **Not consumed** by current frontend |
| `capabilities[]` | `activities.read`, `activities.write`, `firms.read` | — |
| `activityFeatures.createActivity` | `ActivityFeatures:CreateActivity` | `AuthenticatedLayout`, `CreateActivityPage` |
| `activityFeatures.dimensions.businessCase` | `ActivityDimensions:BusinessCase` | `CreateActivityPage` |
| `activityFeatures.dimensions.workOrder` | `ActivityDimensions:WorkOrder` | `CreateActivityPage` |
| `activityFeatures.dimensions.project` | `ActivityDimensions:Project` | `CreateActivityPage` |
| `provider.name` | Hardcoded `"abra-gen"` | Informational (unused in UI) |
| `provider.version` | Hardcoded `"demo"` | Informational |

**Not exposed (gap vs 4.0A design):** `defaults.activityTypeId`, `defaults.activityTypeName`, `classification.*` flags.

**Frontend session cache:** Global React Query `staleTime: 30_000` ms (`providers.tsx`). Create page dimension queries use 60s. Config change mid-session may lag until refetch.

---

## 7. Task 5 — Hidden / additional configuration

### Feature flags (explicit)

| Flag | Location |
|------|----------|
| `CreateActivity` | `ActivityFeatureOptions` |
| `BusinessCase`, `WorkOrder`, `Project` | `ActivityDimensionOptions` |

No other `*Feature*` or `*Options` classes exist in the adapter.

### Environment variables

| Variable | Effect |
|----------|--------|
| `ASPNETCORE_ENVIRONMENT` | Loads `appsettings.{Environment}.json` overlay (e.g. Development) |
| `ASPNETCORE_URLS` | Listen URLs (overrides `launchSettings.json`) |
| `VITE_API_BASE_URL` | Frontend build-time API base (default `/api/v1`) |

Standard .NET config override: `Gen__BaseUrl`, `ActivityFeatures__CreateActivity`, etc.

### Non-configurable runtime behaviour

| Item | Location | Notes |
|------|----------|-------|
| CORS origins | `Program.cs` | Dev hosts only |
| Session store | `InMemorySessionStore` | Not durable; not configurable |
| Validate merge rounds | `ActivityCreateService.MaxValidateRounds` | Code constant |
| My Day ownership filter | `ActivityMapper.BuildOwnershipWhere` | Code, not config |
| i18n locale | Frontend `sk-SK` | Not runtime-configurable |

### Health / ops

| Endpoint | Config dependency |
|----------|-------------------|
| `GET /health` | None |
| `GET /health/ready` | `Gen:SmokeTest:LoginName` + `Password` (optional Gen ping) |

---

## 8. Feature flags matrix

| Flag | Frontend effect | Backend effect |
|------|-----------------|----------------|
| `createActivity` | Nav link + create route; redirect if false | Session only; **create API still works** |
| `dimensions.businessCase` | Hide/show BC picker | None; lookup + create accept IDs |
| `dimensions.workOrder` | Hide/show WO picker | None |
| `dimensions.project` | Hide/show project picker | None |

---

## 9. Restart requirements

| Setting | Adapter restart | Frontend rebuild | Session refetch |
|---------|:---------------:|:----------------:|:---------------:|
| `ActivityFeatures:*` | **Yes** | No | Yes (or wait staleTime) |
| `ActivityDimensions:*` | **Yes** | No | Yes |
| `Gen:ReferenceDefaults:*` | **Yes** | No | No |
| `Gen:BaseUrl` | **Yes** | No | No |
| `Gen:TimeZoneId` | **Yes** | No | No |
| `VITE_API_BASE_URL` | No | **Yes** | No |
| CSS / UI (4.2B.1) | No | **Yes** (deploy) | No |

`IOptions<T>` values are bound at application startup; `SessionController` caches option snapshots in constructor.

---

## 10. Task 6 — Future classification readiness

### Proposed config (4.3 target)

```json
{
  "activityFeatures": {
    "createActivity": true,
    "dimensions": { ... },
    "classification": {
      "area": false,
      "type": false,
      "queue": false,
      "process": false
    }
  }
}
```

Or separate `ActivityClassification` section mirroring `ActivityDimensions`.

### Feasibility: **High** — same pattern as Business Dimensions

| Dimension (4.2B) | Classification (4.3) analogue |
|------------------|-------------------------------|
| `ActivityDimensionOptions` | `ActivityClassificationOptions` (new) |
| `DimensionLookupService` + 3 controllers | Lookup services for `crmactivitytypes`, `crmactivityareas`, `crmactivityqueues`, `crmactivityprocesses` |
| Session `dimensions.*` | Session `classification.*` |
| Create page optional pickers | Create page type/area/queue/process pickers |
| Feature flags UI-only | Same; optional backend gate if desired |

### Gen readiness (from 4.0A)

| Picker | Gen BO | List endpoint |
|--------|--------|---------------|
| Activity Type | `crmactivitytypes` | `GET crmactivitytypes` |
| Activity Area | `crmactivityareas` | `GET crmactivityareas` |
| Queue / Series | `crmactivityqueues` | `GET crmactivityqueues` |
| Process | `crmactivityprocesses` | *(verify OpenAPI)* |

**Existing shortcut:** `ReferenceDefaults.ActivityTypeId` already sets type on standalone create — 4.3 replaces/configures this with picker + flags.

**Gen type rules:** `crmactivitytypes.BusTransactionReq` / `BusOrderReq` / `BusProjectReq` / area linkage — adapter should combine config flags with Gen `*Req` flags (documented in 4.2A).

**Period / reference fields:** Classification pickers are orthogonal; period resolution (4.2B.3) should remain date-driven via validate merge.

### Gaps to close before 4.3

1. Expose `defaults.activityTypeName` in session (4.0A design) for read-only label when type picker disabled.
2. Decide backend enforcement for disabled classification flags (dimensions pattern = UI only).
3. Replace or override `ReferenceDefaults.ActivityTypeId` when type picker enabled.
4. Consider `IOptionsMonitor` or per-request `IOptionsSnapshot` if hot config reload needed (optional).

---

## 11. Recommended future configuration model

### Structure

```json
{
  "ActivityFeatures": {
    "CreateActivity": true
  },
  "ActivityDimensions": {
    "BusinessCase": true,
    "WorkOrder": true,
    "Project": true
  },
  "ActivityClassification": {
    "ActivityType": false,
    "ActivityArea": false,
    "ActQueue": false,
    "ActivityProcess": false
  },
  "Gen": {
    "ReferenceDefaults": {
      "ActQueueId": "...",
      "PeriodId": "...",
      "DivisionId": "...",
      "SolverRoleId": "...",
      "ActivityAreaId": "...",
      "ActivityTypeId": "..."
    }
  }
}
```

### Principles

| Principle | Recommendation |
|-----------|----------------|
| **Session as feature contract** | All UI flags under `activityFeatures` (nested `dimensions`, `classification`) |
| **Reference defaults** | Keep for hidden technical fields; reduce reliance as pickers ship |
| **Period** | Never hardcode in payload; always Gen validate merge from date |
| **Customer deployments** | One `appsettings.{Customer}.json` per tenant; document required Gen IDs |
| **Security** | Enforce `createActivity` on `POST /activities/create` (currently UI-only) |
| **Backend flag parity** | Optionally gate lookup APIs when dimension/classification disabled |

### Customer-specific deployments

| Deployment | Typical overrides |
|------------|-------------------|
| DEMO dev | All features `true`; DEMO reference IDs |
| Customer UAT | Dimension flags per rollout; classification off until 4.3 |
| Production | Minimal surface: `createActivity` + required dimensions only |

---

## 12. Sprint coverage map

| Sprint | Configuration introduced | Runtime configurable? |
|--------|-------------------------|:---------------------:|
| 4.0B | `ActivityFeatures.CreateActivity`, `ReferenceDefaults` | ✓ |
| 4.1 | — (assignment uses existing create) | — |
| 4.2B | `ActivityDimensions.*` | ✓ |
| 4.2B.1 | — (CSS tokens in `global.css`) | ✗ |
| 4.2B.3 | — (behaviour: period from validate; `PeriodId` config gate only) | partial |

---

## 13. Artefacts

| File | Role |
|------|------|
| `src/MobileCrm.Adapter/appsettings.json` | Primary config |
| `src/MobileCrm.Adapter/appsettings.Development.json` | Dev overlay (logging, smoke test) |
| `src/MobileCrm.Adapter.Gen/ActivityFeatureOptions.cs` | Create feature |
| `src/MobileCrm.Adapter.Gen/ActivityDimensionOptions.cs` | Dimension flags |
| `src/MobileCrm.Adapter.Gen/GenOptions.cs` | Gen + reference defaults |
| `src/MobileCrm.Adapter/Controllers/SessionController.cs` | Session projection |
| `src/MobileCrm.Web/src/api/types.ts` | Frontend session types |
| `implementation/sprint-4-0a-activity-creation-analysis.md` | Future classification design reference |
