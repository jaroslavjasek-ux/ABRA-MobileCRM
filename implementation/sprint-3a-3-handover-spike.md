# Sprint 3A.3 — Activity handover (“Odovzdať”) spike

**Status:** Complete (DEMO Gen 26, API simulation)  
**Date:** 2026-06-08  
**Goal:** Determine whether native ABRA handover should replace custom follow-up activity creation.

**Environment:** `http://localhost/demo`, credentials `api` / `123`

---

## 1. Executive summary

| Finding | Detail |
|---------|--------|
| **Dedicated handover API** | **None** — no `/handover`, `/odovzdat`, or similar endpoint on `crmactivities` |
| **Native handover primitive** | **`Source_ID` on `POST /crmactivities`** — links child to predecessor; **auto-sets source to `Status 3` (Odovzdané)** |
| **`pmchangestate`** | Changes `PMState_ID` / ownership — **does not create a follow-up activity** |
| **Desktop NP chain** | DEMO seed shows multi-step chains via `source_id`; all steps `Status 3`; uses **`ActivityProcess_ID`** progression |
| **Custom create without `Source_ID`** | Source stays **`Status 2` (Dokončené)**; no chain link |

### Decision (recommended)

**B+ — Continue custom follow-up create (Sprint 3A.1), enhanced with native `Source_ID`.**

Do **not** replace 3A.1 with `pmchangestate` or a separate “handover workflow” API (none exists). **Do** add `Source_ID = completedActivityId` to the follow-up POST payload so Gen applies native handover semantics (source → Odovzdané, chain link, new document number on child).

Full desktop **activity process** automation (`ActivityProcess_ID` step chain) is **out of scope for Mobile CRM MVP** — optional Phase 2 for Mobile Projects.

---

## 2. Desktop observations (inferred)

> **Note:** Desktop ABRA Gen UI was not operated in this spike. Behaviour below is inferred from DEMO seed data, OpenAPI schema, and live API simulation that models Gen server rules triggered by desktop “Odovzdať”.

### 2.1 DEMO handover chain (seed data)

Activities with `Status = 3` and `source_id` chain (firm `C000000101`, type **Obchodný prípad**):

| Step | ID | DisplayName | `source_id` | `activityprocess_id` | Subject (summary) |
|------|-----|-------------|-------------|----------------------|-------------------|
| 1 | `6000000101` | NP-2/2006 | *(null)* | `2000000101` Nový kontakt | záujem o nákup žeriavu |
| 2 | `8000000101` | NP-4/2006 | `6000000101` | `2000000101` | propagačné materiály |
| 3 | `9000000101` | NP-5/2006 | `8000000101` | `4000000101` Návrh na prezentáciu | návrh na termín |
| 4 | `A000000101` | NP-6/2006 | `9000000101` | `5000000101` Uskutočnená prezentácia | uskutočnená prezentácia |

**Desktop-like behaviour inferred:**

1. Each “Odovzdať” creates a **new activity** (new `DisplayName` / number series).
2. New activity references predecessor via **`Source_ID`** (`source_id` in GET).
3. Predecessor ends in **`Status 3` (Odovzdané)**.
4. Process-driven installs advance **`ActivityProcess_ID`** to the next CRM process step.
5. **`Answer` / `Description`** on older steps can remain (history on closed rows); subjects differ per step.

### 2.2 API simulation (2026-06-08)

| Test | Action | Source after | Child |
|------|--------|--------------|-------|
| **A** | Complete → `PUT Status 3` → `POST` with `Source_ID` | `Status 3`, `Answer` retained | `Status 0`, new `DisplayName`, `source_id` set |
| **B** | Complete → `POST` with `Source_ID` only | **`Status 3` auto** (no explicit PUT 3) | `Status 0`, linked |
| **C** | Complete → `POST` **without** `Source_ID` (3A.1 today) | **`Status 2` unchanged** | `Status 0`, **no** `source_id` |
| **D** | `PUT pmchangestate` on completed activity | `Status 3` unchanged at PM layer | **No child created** |

**Test activity IDs (safe to delete):** `S100000101` / `U100000101`, `V100000101` / `W100000101`, `X100000101` / `Y100000101`, `0200000101` / `1200000101`.

---

## 3. What records are created

| Mechanism | Records created | Source terminal state |
|-----------|-----------------|------------------------|
| **`POST` + `Source_ID`** | **One new** `crmactivity` (child) | Source → **`Status 3`** automatically |
| **`PUT Status 3` only** | None | Source → `Status 3` |
| **`pmchangestate`** | None | PM state / owner may change; no new activity |
| **Custom `POST` (no `Source_ID`)** | One new activity | Source stays **`Status 2`** |

Native handover = **one new activity** + **source closed as Odovzdané**.

---

## 4. Field copy / regenerate matrix

### 4.1 Copied when `Source_ID` set (must be in POST body — Gen does not auto-copy all)

| Field | Auto-copied? | Evidence |
|-------|:------------:|----------|
| `Firm_ID` | **No** — must send | Child empty if omitted |
| `ActivityType_ID` | **No** — must send | Same |
| `ActQueue_ID`, `Period_ID`, `Division_ID`, `SolverRole_ID`, `ActivityArea_ID` | **No** — must send | Same as 3A.1 spike |
| `Person_ID` | **No** — must send | Same |
| `ResponsibleUser_ID` / `SolverUser_ID` | **No** — must send | Session user used in tests |
| `BusTransaction_ID` (Business Case) | **No** | Child null unless explicit in POST |
| `BusProject_ID` (Project) | **No** | Child null unless explicit |
| `BusOrder_ID` (Work Order) | **No** | Child null unless explicit |
| `Description` / `Answer` | **No** | Child blank; **source retains** outcome text |
| `Subject` | **No** | User/supplied on child |
| `SheduledStart$DATE` | **No** | User/supplied on child |
| `ActivityProcess_ID` | **No** | Desktop chain sets next process manually / via workflow |

### 4.2 Regenerated by Gen

| Field | Behaviour |
|-------|-----------|
| `ID` | New 10-char id on child |
| `DisplayName` | **New document number** (e.g. `PrHo-1/2026`) |
| `Status` (child) | **`0` (Otvorená)** in API tests |
| `Status` (source) | **`3` (Odovzdaná)** when child committed with `Source_ID` |
| `CreatedBy_ID` | Current API user |
| `source_id` (child) | Set to predecessor id |
| `ObjVersion` | Reset on child |

### 4.3 Not populated (DEMO)

| Field | Observation |
|-------|-------------|
| `NewRelatedDocument_ID` | Empty on source after handover |
| `NewRelatedType` | `0` (Neznámy) — enum value `1` = CRM Aktivity exists but unused in tests |

Chain link is via **`Source_ID` on child**, not `NewRelatedDocument_ID` on parent.

---

## 5. Activity chain linking

```
[Source activity]  ──Source_ID──►  [Child activity]
     Status 3                         Status 0
     DisplayName: PrHo-13/2006        DisplayName: PrHo-1/2026
     source_id: null                  source_id: {source id}
```

**Query chain:**

```http
GET crmactivities?where=source_id eq '{parentId}'&select=ID,DisplayName,Status,source_id
```

**Reverse walk:** read `source_id` on child until null (DEMO root `6000000101`).

OpenAPI documents `Source_ID` as: *“Odkaz na aktivitu, z ktorej bola akt. odovzdaná”*.

---

## 6. History preservation

| Data | Source after handover | Child |
|------|----------------------|-------|
| `Answer` (outcome) | **Preserved** (`Outcome for handover spike` on `S100000101`) | Empty unless sent |
| `Description` | **Preserved** | Empty unless sent |
| `Subject` | Unchanged | New subject |
| Status | **3** (terminal) | **0** (actionable) |

Mobile CRM: completed outcome remains on **source** activity detail (history). Follow-up is a **new** open row.

---

## 7. Dimensions (Business Case / Work Order / Project)

| Dimension | Gen field | Inherited via `Source_ID` alone? |
|-----------|-----------|:--------------------------------:|
| Business Case | `BusTransaction_ID` | **No** |
| Work Order | `BusOrder_ID` | **No** |
| Project | `BusProject_ID` | **No** |

**Verified:** Source `X100000101` had all three dimensions; child `Y100000101` had **null** on all three. Explicit POST copied dimensions successfully (`Z100000101` child).

**Recommendation:** Copy from source in adapter (same as 3A.2 dimension design) when feature flags enabled.

---

## 8. Ownership

| Field | Source after handover | Child |
|-------|----------------------|-------|
| `ResponsibleUser_ID` | Unchanged on source | Set in POST (session rep in tests) |
| `SolverUser_ID` | Unchanged on source | Set in POST |
| `CreatedBy_ID` | Original creator | API user |

DEMO NP chain: all steps share `SolverUser_ID = 1300000101`. Mobile should default child ownership to **session rep** (3A.1), not blindly copy source solver if reassignment is intended.

---

## 9. Document numbers

| | Source | Child |
|---|--------|-------|
| **Regenerated?** | **No** — keeps `PrHo-13/2006` | **Yes** — `PrHo-1/2026` |
| Mobile maps | `documentNumber` | `documentNumber` |

Never send `DisplayName` on create.

---

## 10. Gen API investigation

### 10.1 Dedicated handover endpoints

**None found** on `crmactivities` OpenAPI paths:

| Path | Method | Creates follow-up? |
|------|--------|:------------------:|
| `/crmactivities` | POST | **Yes** (with `Source_ID`) |
| `/crmactivities/{id}` | PUT | Status / field update only |
| `/crmactivities/{id}/pmchangestate` | PUT | **No** |
| `/crmactivities/{id}/pmchangestatebytransition` | PUT | **No** (0 transitions on DEMO) |
| `/crmactivities/{id}/editlock` | GET/PUT | Lock only |

### 10.2 Status enum (`crmactivity.Status`)

| Value | SK caption | Mobile |
|------:|------------|--------|
| 0 | Neriešené | `open` |
| 1 | V procese | `inProgress` |
| 2 | Dokončené | `completed` |
| 3 | Odovzdané | `handedOver` |

Handover terminal state = **`3`**, distinct from complete (`2`).

### 10.3 `pmchangestate` / `pmchangestatebytransition`

```json
// PUT /crmactivities/{id}/pmchangestate
{ "pmstate_id": "CADEF00000", "responsibleuser_id": "2610000101" }
```

- Updates process state metadata on **same** document.
- Does **not** set `Status 3` or create child.
- `GET pmstatestransitions` → **empty** on DEMO.
- `pmstates` exist with `systemstate` mapping (separate from activity `Status`).

**Conclusion:** PM workflow is **orthogonal** to Odovzdať / follow-up create. Sprint 2B was correct to avoid `pmchangestate` for complete.

### 10.4 Activity process (`ActivityProcess_ID`)

DEMO NP chain uses escalating process steps (`2000000101` → `3000000101` → `4000000101` → `5000000101`).

`POST` with `ActivityProcess_ID` + `Source_ID` on completed seed → **2 validation errors** (process rules not satisfied from API without desktop context).

**Conclusion:** Full desktop parity may require **process engine** configuration; not available as a simple REST handover call.

### 10.5 Payload before / after handover (API test B)

**Before** (`V100000101`, completed):

```json
{ "status": 2, "answer": "done source2", "source_id": null }
```

**After** `POST` child `W100000101` with `Source_ID: V100000101`:

| Activity | status | source_id | displayname |
|----------|--------|-----------|-------------|
| Source `V100000101` | **3** | null | *(unchanged)* |
| Child `W100000101` | **0** | `V100000101` | new number |

---

## 11. Recommended Mobile CRM implementation

### 11.1 Extend Sprint 3A.1 `ActivityCreateService`

After successful **complete**, when follow-up enabled:

```csharp
body["Source_ID"] = completedActivityId;  // native handover link
// Do NOT separately PUT Status 3 — Gen sets source to 3 on child commit
```

Keep existing:

- Validate-then-commit `POST`
- Inherit firm, type, refs, person, dimensions (explicit copy)
- Session rep as `ResponsibleUser_ID` / `SolverUser_ID`
- User `subject`, `scheduledStart`, optional `description`

### 11.2 Complete + follow-up sequence

```
1. PUT complete source (Status 2 + Answer)     ← existing Sprint 2B
2. POST follow-up with Source_ID + context     ← 3A.1 + this spike
3. GET source + GET child                      ← verify source Status 3, child Status 0
4. Return completed detail + followUp { id, documentNumber }
```

**Do not** call `PUT Status 3` before step 2 — redundant; `Source_ID` commit handles it.

### 11.3 API response extension

```typescript
followUp?: {
  id: string;
  documentNumber: string;
  scheduledStart: string;
  sourceActivityId: string;  // provenance
}
```

### 11.4 UI implications

| State | My Day | Detail actions |
|-------|--------|----------------|
| Source `handedOver` (3) | Hidden | Read-only history |
| Child `open` (0) | Visible (if scheduled + owned) | Začať riešiť / etc. |

User sees outcome on **completed/handover** activity; new task appears separately on agenda.

### 11.5 What we are NOT implementing (MVP)

- `pmchangestatebytransition` driven handover
- Automatic `ActivityProcess_ID` advancement
- `NewRelatedDocument_ID` / `NewRelatedType` linking

---

## 12. Decision matrix

| Criterion | A) Native handover workflow | B) Custom follow-up only | **B+ Recommended** |
|-----------|----------------------------|--------------------------|---------------------|
| Gen API surface | `Source_ID` POST | `POST` without link | `POST` **with** `Source_ID` |
| Source → Odovzdané | **Automatic** | Stays Dokončené | **Automatic** |
| Chain in ABRA | **Yes** | No | **Yes** |
| Control of child fields | Same POST payload | Full | Full |
| Adapter complexity | Low (add one field) | Already built | **+1 field on 3A.1** |
| Desktop process parity | Partial | None | Partial (good enough for CRM) |
| pmchangestate required | No | No | No |

### Final decision

**B+ — Continue custom follow-up activity creation, add native `Source_ID` handover link.**

Rationale:

1. There is **no** separate handover REST action — native behaviour **is** `POST` with `Source_ID`.
2. Sprint 3A.1 infrastructure remains valid; one field + inherit rules closes the gap.
3. `pmchangestate` does **not** replace follow-up scheduling.
4. Activity **process** chains are a later enhancement (Mobile Projects), not a blocker for CRM follow-up.

---

## 13. Implementation tasks (Sprint 3A.4)

| # | Task |
|---|------|
| 1 | Add `Source_ID` to `ActivityCreateService.BuildGenPayload` when `sourceActivityId` is the just-completed activity |
| 2 | Remove any planned manual `PUT Status 3` on source after follow-up |
| 3 | Copy optional dimensions from source (3A.2) when config enabled |
| 4 | Extend `CompleteAsync` to call create after complete (3A design) |
| 5 | Verify E2E: source `handedOver`, child `open`, chain queryable |

---

## 14. Open questions

| ID | Question |
|----|----------|
| OQ-3A3-01 | Production: does `Source_ID` POST always auto-set source to `Status 3`, or installation-dependent? |
| OQ-3A3-02 | Should child default `ActivityType_ID` from source or from next `ActivityProcess_ID` when process configured? |
| OQ-3A3-03 | Desktop “Odovzdať” with dialog — which fields does UI pre-fill beyond Gen API defaults? (Needs workshop) |
| OQ-3A3-04 | Is `Status 2` without follow-up acceptable long-term, or must CRM always hand over? |

---

## 15. References

| Document | Relevance |
|----------|-----------|
| [sprint-3a-1-activity-create.md](sprint-3a-1-activity-create.md) | Create infrastructure |
| [sprint-3a-2-activity-dimensions-analysis.md](sprint-3a-2-activity-dimensions-analysis.md) | Dimension copy rules |
| [sprint-2b-activity-completion-design.md](sprint-2b-activity-completion-design.md) | Status 2 vs 3 |
| OpenAPI `crmactivities.json` | `Source_ID`, `Status`, `pmchangestate` |
| DEMO chain `6000000101` → `A000000101` | Desktop-like history |
