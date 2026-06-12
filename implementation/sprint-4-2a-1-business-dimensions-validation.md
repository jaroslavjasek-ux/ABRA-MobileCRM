# Sprint 4.2A.1 — Business Dimensions Validation & Relationships

**Status:** Analysis complete  
**Date:** 2026-06-11  
**Depends on:** [4.2A business dimensions analysis](sprint-4-2a-business-dimensions-analysis.md), [3A.2 dimensions](sprint-3a-2-activity-dimensions-analysis.md)  
**Goal:** Remove uncertainty around Business Case, Work Order, Project, and their relationship to Firm before / during Sprint 4.2B.

**Evidence:** Live DEMO Gen spike [`scripts/spike_4_2a_1_business_dimensions_validation.py`](../scripts/spike_4_2a_1_business_dimensions_validation.py) → [`analysis/spikes/sprint-4-2a-1-business-dimensions-validation-results.json`](../analysis/spikes/sprint-4-2a-1-business-dimensions-validation-results.json); firm/division probe [`scripts/spike_4_2a_1_firm_division_probe.py`](../scripts/spike_4_2a_1_firm_division_probe.py).

**Environment:** `http://localhost/demo`, credentials `api` / `123`

---

## 1. Executive summary

| Topic | Finding |
|-------|---------|
| **Mandatory activity fields (desktop)** | **Firma** (`Firm_ID`) and **Stredisko** (`Division_ID`) are required in ABRA desktop UX |
| **API vs desktop** | Gen API **strictly enforces Stredisko** on validate/create when other refs are set; **Firma** may still commit via API without `Firm_ID` in some payloads — Mobile adapter already requires `firmId` |
| **Dimension ↔ Firm link (DEMO data)** | All BO rows have `Firm_ID: null` — dimensions exist **independently** of firm in seed data |
| **Firm filter syntax** | `where=Firm_ID eq '{id}'` is **supported** on all three BOs but returns **0 rows** on DEMO |
| **Cross-firm validation** | **Not enforced** on DEMO — Galenit + Výstavy/Služby/Dealer passes; other firm + same dimension IDs also passes |
| **Handover inheritance** | Gen does **not** copy `Bus*` via `Source_ID` alone — Mobile CRM **must send explicitly** (adapter already does in `BuildFollowUpGenPayload`) |
| **Reference activity** | `E120000101` — Galenit + Výstavy + Služby + Dealer — confirms UI ↔ Gen mapping |
| **UX recommendation** | **Option B with global fallback** — firm-scoped lists when `Firm_ID` is populated; fallback to global catalog on DEMO / empty filter |

---

## 2. Task 1 — Lookup discovery

### 2.1 Business Cases (`bustransactions`)

| Property | Value |
|----------|-------|
| **List endpoint** | `GET bustransactions?select=ID,DisplayName,Code,Name,Firm_ID&take=&skip=` |
| **Detail endpoint** | `GET bustransactions/{id}?select=…` |

**Reference record — Výstavy:**

```json
{
  "ID": "5000000101",
  "DisplayName": "Výstavy Výstavy",
  "Code": "Výstavy",
  "Name": "Výstavy",
  "Firm_ID": null
}
```

**Full DEMO catalog (2 rows):**

| ID | Code | Name | DisplayName | Firm_ID |
|----|------|------|-------------|---------|
| `3000000101` | Zľavy | Zľavové akcie | Zľavy Zľavové akcie | null |
| `5000000101` | Výstavy | Výstavy | Výstavy Výstavy | null |

---

### 2.2 Work Orders (`busorders`)

| Property | Value |
|----------|-------|
| **List endpoint** | `GET busorders?select=ID,DisplayName,Code,Name,Firm_ID&take=&skip=` |
| **Detail endpoint** | `GET busorders/{id}?select=…` |

**Reference record — Služby:**

```json
{
  "ID": "A000000101",
  "DisplayName": "S Služby",
  "Code": "S",
  "Name": "Služby",
  "Firm_ID": null
}
```

**Note:** UI label **Zákazka** maps to BO `busorders`. `DisplayName` is composite (`Code` + `Name`); search by `Code`/`Name`, not `DisplayName like` (400 on DEMO).

---

### 2.3 Projects (`busprojects`)

| Property | Value |
|----------|-------|
| **List endpoint** | `GET busprojects?select=ID,DisplayName,Code,Name,Firm_ID&take=&skip=` |
| **Detail endpoint** | `GET busprojects/{id}?select=…` |

**Reference record — Dealer:**

```json
{
  "ID": "2000000101",
  "DisplayName": "Dealer Sprostredkovanie predaja",
  "Code": "Dealer",
  "Name": "Sprostredkovanie predaja",
  "Firm_ID": null
}
```

---

## 3. Task 2 — Relationship analysis

### 3.1 Relationship matrix

| Dimension | BO | `Firm_ID` on BO row (DEMO) | Can exist without firm? | Filterable by `Firm_ID`? | Observed on DEMO |
|-----------|-----|:--------------------------:|:-----------------------:|:------------------------:|------------------|
| Business Case | `bustransactions` | Always **null** | **Yes** | Syntax **yes**, data **no** | 0 rows for Galenit `4000000101` |
| Work Order | `busorders` | Always **null** | **Yes** | Syntax **yes**, data **no** | 0 rows for Galenit |
| Project | `busprojects` | Always **null** | **Yes** | Syntax **yes**, data **no** | 0 rows for Galenit |

**Survey:** `take=100` on each BO → **0 of 2/3/4 rows** have non-null `Firm_ID`.

### 3.2 Interpretation

On DEMO, business dimensions behave as a **global catalog**. The manually created reference activity (`E120000101`) links **Galenit a.s.** to catalog entries that have **no firm FK** on the BO row. This is valid Gen behaviour — firm association is on the **activity**, not necessarily mirrored on the dimension master data.

**Production expectation:** When `Firm_ID` is populated on BO rows, firm-scoped filtering becomes meaningful. Until then, firm-driven pickers will appear empty without a fallback.

### 3.3 Per-dimension answers

| Question | Business Case | Work Order | Project |
|----------|:-------------:|:----------:|:-------:|
| Can it exist independently of Firm? | **Yes** (DEMO) | **Yes** | **Yes** |
| Can it be filtered by Firm? | **API yes**, DEMO empty | **API yes**, DEMO empty | **API yes**, DEMO empty |

**Example — firm filter (Galenit `4000000101`):**

```http
GET bustransactions?select=ID,DisplayName,Code,Name,Firm_ID&where=Firm_ID eq '4000000101'&take=20
→ 200 OK, 0 rows
```

Same for `busorders` and `busprojects`.

---

## 4. Task 3 — Lookup filtering capability

### 4.1 Supported filter parameters

Gen OData list endpoints accept **`where`** clauses only. There is no dedicated `firmId` query parameter on Gen itself; Mobile adapter exposes `firmId` as:

```http
where=Firm_ID eq '{firmId}'
```

**Not found / not applicable on Gen list APIs:**

| Param | Supported? |
|-------|:----------:|
| `firmId` (adapter maps to `Firm_ID eq`) | ✓ (adapter) |
| `companyId` | ✗ |
| `firm` | ✗ |
| `parentId` | ✗ |

**Search:** `Code like '*{q}*'` or `Name like '*{q}*'` — works. `DisplayName like` → **400**.

**Paging:** `take` + `skip` — works on all three BOs.

### 4.2 Can Mobile CRM implement firm-driven pickers?

| Step | Feasible? | DEMO behaviour |
|------|:---------:|----------------|
| Select Firm | ✓ | Required in Mobile create |
| Show related Business Cases | ✓ API | **Empty** → need fallback |
| Show related Work Orders | ✓ API | **Empty** → need fallback |
| Show related Projects | ✓ API | **Empty** → need fallback |

### 4.3 Recommended approach (unchanged from 4.2A, validated)

**Option B with fallback:**

1. After firm selection, query each BO with `Firm_ID eq '{firmId}'`.
2. If result empty → query global list (`take=50`, optional `q` on Code/Name).
3. Optional client-side filter on loaded `displayName`.
4. **Production enhancement:** when selected row has non-null `Firm_ID` and `Firm_ID ≠ activity.Firm_ID`, reject with 422 before POST.

---

## 5. Task 4 — Validation rules

### 5.1 Mandatory fields — Firma & Stredisko

Desktop errors (user-reported):

| Slovak UI | Gen field | API `@displaylabel` |
|-----------|-----------|---------------------|
| Firma | `Firm_ID` / `firm_id` | *(not returned in sampled API errors)* |
| Stredisko | `Division_ID` / `division_id` | Stredisko |

**Controlled API tests** (`scripts/spike_4_2a_1_firm_division_probe.py`):

| Scenario | Validate | Create | Errors |
|----------|:--------:|:------:|--------|
| Firm + Division set | ✓ 0 errors | ✓ 201 | — |
| Firm set, **no Division** | ✗ | ✗ 400 | `division_id` — *Chyba v zadaní položky Stredisko* (code 824) |
| **No Firm**, Division set | ✓ 0 errors | ✓ 201 | *(none — API allows commit)* |
| Neither Firm nor Division | ✗ | ✗ 400 | Stredisko + other reference errors |

**Implication for Mobile CRM:**

- **Stredisko** is covered by tenant `ReferenceDefaults.DivisionId` on standalone create (Sprint 4.0B).
- **Firma** must remain **required** in Mobile API/UI even if Gen API is permissive in edge cases — matches desktop behaviour.

### 5.2 Dimension validation — cross-firm mismatch

**Test:** Reference dimensions (Výstavy / Služby / Dealer) with:

| Firm | Validate | Create | Persisted dims |
|------|:--------:|:------:|----------------|
| Galenit `4000000101` | ✓ 0 errors | ✓ 201 | All three IDs set |
| Other firm `3000000101` | ✓ 0 errors | ✓ 201 | Same three IDs set |

**Conclusion on DEMO:** Gen does **not** reject dimension IDs that are not “owned” by the selected firm, because BO rows have `Firm_ID: null`. **Cannot reproduce** “Firma = A, Projekt = B (belongs elsewhere)” failure on DEMO.

| Dimension | Validate (mismatch) | Create (mismatch) | Error message |
|-----------|:-------------------:|:-----------------:|---------------|
| Business Case | ✓ pass | ✓ pass | — |
| Work Order | ✓ pass | ✓ pass | — |
| Project | ✓ pass | ✓ pass | — |

**Production:** Re-test when BO `Firm_ID` is populated; add adapter-side guard if Gen does not enforce.

### 5.3 Activity type requirement flags

Reference activity uses type `3000000101` (Obchodný prípad). Telefón type `2000000101`:

```http
GET crmactivitytypes/2000000101?select=BusTransactionReq,BusOrderReq,BusProjectReq
```

```json
{ "BusTransactionReq": 0, "BusOrderReq": 0, "BusProjectReq": 0 }
```

All dimensions **optional** for default Mobile create type. `*Req` flags can make pickers required per type in future (see 4.2A §6.3).

### 5.4 Validation matrix (summary)

| Test | Validate | Create | Notes |
|------|:--------:|:------:|-------|
| No dimensions | ✓ | ✓ | — |
| BC only | ✓ | ✓ | — |
| WO only | ✓ | ✓ | — |
| Project only | ✓ | ✓ | — |
| All three | ✓ | ✓ | Reference combo |
| Galenit + ref dims | ✓ | ✓ | Matches manual activity |
| Other firm + same dims | ✓ | ✓ | No cross-firm rejection on DEMO |
| Missing Stredisko | ✗ | ✗ | Code 824 |
| Missing Firma (API) | ✓ | ✓ | Desktop stricter; Mobile requires firm |

---

## 6. Task 5 — Activity inheritance (handover)

### 6.1 Scenario

Source activity with all three dimensions (Galenit + Výstavy / Služby / Dealer).

### 6.2 Gen `Source_ID` only (no explicit `Bus*`)

| | Source `5220000101` | Child `9220000101` |
|--|---------------------|---------------------|
| `bustransaction_id` | `5000000101` | **null** |
| `busorder_id` | `A000000101` | **null** |
| `busproject_id` | `2000000101` | **null** |

**Result:** Gen does **not** auto-inherit dimensions from parent via `Source_ID` alone.

### 6.3 Explicit copy in POST body

Child `0220000101` / `B220000101` with `BusTransaction_ID`, `BusOrder_ID`, `BusProject_ID` copied from source:

| Field | Child value |
|-------|-------------|
| `bustransaction_id` | `5000000101` |
| `busorder_id` | `A000000101` |
| `busproject_id` | `2000000101` |

**Result:** ✓ Persists when Mobile CRM sends IDs explicitly.

### 6.4 Inheritance matrix

| Child create path | `BusTransaction_ID` | `BusOrder_ID` | `BusProject_ID` |
|-------------------|:-------------------:|:-------------:|:---------------:|
| Handover — `Source_ID` only | ✗ not copied | ✗ | ✗ |
| Handover — explicit copy (adapter) | ✓ | ✓ | ✓ |
| Standalone create — user picker | User choice / omit | User choice / omit | User choice / omit |

**Adapter today:** `BuildFollowUpGenPayload` copies from source GET — **correct**; no change needed for handover.

---

## 7. Task 6 — Reference activity analysis

### 7.1 Identified activity

| Property | Value |
|----------|-------|
| **ID** | `E120000101` |
| **Subject** | Test Zákazka, Obchodný prípad a Projekt |
| **DisplayName** | NP-25/2026 |
| **Created** | 2026-06-11 (manual desktop) |

### 7.2 Mapping table

| UI field (Slovak) | Gen field (GET) | Gen field (POST) | ID | Resolved display |
|-------------------|-----------------|------------------|-----|------------------|
| **Firma** | `firm_id` | `Firm_ID` | `4000000101` | Galenit a.s. (`00003`) |
| **Obchodný prípad** | `bustransaction_id` | `BusTransaction_ID` | `5000000101` | Výstavy |
| **Zákazka** | `busorder_id` | `BusOrder_ID` | `A000000101` | Služby (`S`) |
| **Projekt** | `busproject_id` | `BusProject_ID` | `2000000101` | Dealer |
| **Stredisko** | `division_id` | `Division_ID` | `2000000101` | *(tenant default on Mobile create)* |
| **Typ aktivity** | `activitytype_id` | `ActivityType_ID` | `3000000101` | Obchodný prípad |

### 7.3 Reference activity payload excerpt (full GET)

```json
{
  "id": "E120000101",
  "subject": "Test Zákazka, Obchodný prípad a Projekt",
  "firm_id": "4000000101",
  "bustransaction_id": "5000000101",
  "busorder_id": "A000000101",
  "busproject_id": "2000000101",
  "division_id": "2000000101",
  "activitytype_id": "3000000101",
  "actqueue_id": "4000000101",
  "period_id": "3F80000101",
  "solverrole_id": "6000000101"
}
```

**Validate response:** Not captured from desktop session; API recreate with same IDs → **0 validation errors**, create **201**.

---

## 8. Task 7 — UX recommendation

### 8.1 Option A — Independent selectors

```
Firma
Obchodný prípad
Zákazka
Projekt
```

| Pros | Cons |
|------|------|
| Simple; works on DEMO global catalog | User can pick unrelated dimensions |
| No empty lists after firm select | Does not match production firm-linked data model |

### 8.2 Option B — Firm-driven selectors

```
Firma
  ↓
Obchodný prípad
  ↓
Zákazka
  ↓
Projekt
```

| Pros | Cons |
|------|------|
| Matches ABRA mental model when `Firm_ID` is set on BOs | **Empty lists on DEMO** without fallback |
| Reduces invalid combinations in production | Slightly more complex loading logic |

### 8.3 Final recommendation — **Option B with global fallback**

1. **Require firm first** (already in Create Activity).
2. **Load dimensions firm-scoped** (`firmId` query param).
3. **If empty**, load global catalog and optionally show hint: *Žiadne väzby pre zákazníka — zobrazujem celý zoznam*.
4. **Clear dimension picks** when firm changes.
5. **Do not** chain BC → WO → Project (no parent-child between dimension BOs observed).
6. Keep all three pickers **optional** unless `crmactivitytypes.*Req` mandates otherwise.

---

## 9. Implementation recommendation for Sprint 4.2B

| Area | Recommendation | Priority |
|------|----------------|----------|
| Lookup APIs | `firmId` filter + global fallback | P0 |
| Create DTO | Optional `businessCaseId`, `workOrderId`, `projectId` → `Bus*` | P0 |
| UI | Option B with fallback; section below firm/contact | P0 |
| Firm required | Keep Mobile validation regardless of Gen permissiveness | P0 |
| Stredisko | Continue `ReferenceDefaults.DivisionId` — not a user picker | P0 |
| Cross-firm guard | Adapter 422 when BO `Firm_ID` ≠ activity firm | P1 (production data) |
| Handover | Keep explicit copy — **do not** rely on `Source_ID` | Done in adapter |
| Detail display | Show dimensions on activity detail | P2 (out of 4.2B scope) |
| `*Req` flags | Drive required/hidden pickers per activity type | P2 |

### 9.1 Gaps found vs desktop testing

| Desktop observation | API finding | Mobile action |
|--------------------|-------------|---------------|
| Firma required | API may create without `Firm_ID` in edge case | Keep `firmId` required in adapter + UI |
| Stredisko required | API enforces `division_id` error 824 | `ReferenceDefaults` already supplies `Division_ID` |
| Dimensions with Galenit | Valid with global catalog IDs | Firm-scoped lookup + fallback |

### 9.2 DEMO reference IDs (quick copy)

| Entity | ID |
|--------|-----|
| Galenit a.s. | `4000000101` |
| Výstavy (BC) | `5000000101` |
| Služby (WO) | `A000000101` |
| Dealer (Projekt) | `2000000101` |
| Reference activity | `E120000101` |

---

## 10. Artefacts

| File | Purpose |
|------|---------|
| [`scripts/spike_4_2a_1_business_dimensions_validation.py`](../scripts/spike_4_2a_1_business_dimensions_validation.py) | Main spike |
| [`scripts/spike_4_2a_1_firm_division_probe.py`](../scripts/spike_4_2a_1_firm_division_probe.py) | Firma / Stredisko validation |
| [`analysis/spikes/sprint-4-2a-1-business-dimensions-validation-results.json`](../analysis/spikes/sprint-4-2a-1-business-dimensions-validation-results.json) | Machine-readable results |
| [`implementation/sprint-4-2a-business-dimensions-analysis.md`](sprint-4-2a-business-dimensions-analysis.md) | Prior 4.2A baseline |

---

## 11. Open questions (production)

1. Are `Firm_ID` values populated on `bustransactions` / `busorders` / `busprojects` in customer tenants?
2. Does Gen enforce firm–dimension consistency when `Firm_ID` is set on BO rows?
3. Should activity type `3000000101` (Obchodný prípad) drive different `*Req` flags than `2000000101` (Telefón)?

Re-run spike scripts on customer DEMO/UAT when firm-linked dimension data exists.
