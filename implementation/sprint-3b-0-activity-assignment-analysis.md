# Sprint 3B.0 — Activity assignment analysis

**Status:** Analysis complete (DEMO Gen 26)  
**Date:** 2026-06-08  
**Goal:** Understand how ABRA Gen assigns activities to users and roles, how Mobile CRM **Môj deň** determines ownership, and what this implies for handover UI.

**No implementation in this sprint.**

**Evidence:** Live DEMO API (`http://localhost/demo`, `api` / `123`), OpenAPI `crmactivities.json`, adapter code (`MyDayService`, `ActivityMapper`), spike script [`scripts/spike_3b0_activity_assignment.py`](../scripts/spike_3b0_activity_assignment.py) → [`analysis/spikes/sprint-3b0-activity-assignment-results.json`](../analysis/spikes/sprint-3b0-activity-assignment-results.json).

> **Desktop note:** ABRA Gen desktop UI was **not operated** in this spike. Desktop field mappings below are inferred from OpenAPI Slovak labels, DEMO seed data, and prior handover spikes. Native Gen **Môj deň** role-pool behaviour is **inferred**, not observed in the Win client.

---

## 1. Executive summary

| Topic | Finding |
|-------|---------|
| **Primary assignment fields** | `SolverRole_ID` (role pool) + `SolverUser_ID` (concrete user). Optional parallel pair: `ResponsibleRole_ID` + `ResponsibleUser_ID`. |
| **`Owner_ID` on activity** | **Does not exist** on `crmactivity`. Mobile `ownerId` in API is an alias for `ResponsibleUser_ID`. |
| **`CreatedBy_ID`** | Set by Gen to the API/desktop user on create. **Always affects Mobile My Day** (included in ownership filter). |
| **Mobile My Day ownership** | `ResponsibleUser_ID` **OR** `SolverUser_ID` **OR** `CreatedBy_ID` = session rep. **`SolverRole_ID` is ignored.** |
| **Role-only assignment** | Activity visible in Mobile My Day **only to creator** (via `CreatedBy_ID`), **not** to role members — **parity gap vs expected Gen desktop behaviour**. |
| **Roles / users API** | `securityroles`, `securityusers`, nested `securityroles/{id}/securityusers` and `securityusers/{id}/securityroles`. No `representatives` BO on DEMO OpenAPI index. |
| **Handover follow-up** | Inherit `SolverRole_ID` from source; let user pick `SolverUser_ID` (or leave empty for role pool); default `ResponsibleUser_ID` to session rep unless user overrides. |

---

## 2. Activity ownership model

### 2.1 Field reference

| Field | OpenAPI label (SK) | Purpose | Writable (POST/PUT) | Mobile My Day | Mobile detail / actions |
|-------|-------------------|---------|:-------------------:|:-------------:|:------------------------:|
| **`SolverRole_ID`** | Rola riešiteľa / Odkaz na rolu riešiteľa | Assigns activity to a **role pool** when no concrete solver is set. Required reference on DEMO create (from `ActQueue` / source). | ✓ | **No** | **No** (not in `IsOwnedByRepresentative`) |
| **`SolverUser_ID`** | Riešiteľ / Odkaz na riešiteľa | Concrete user who should solve the activity. | ✓ | **Yes** | **Yes** |
| **`ResponsibleUser_ID`** | Zodpovedná osoba | Accountable person (may differ from solver). | ✓ | **Yes** | **Yes** |
| **`ResponsibleRole_ID`** | Zodpovedná rola | Role pool for responsible person. | ✓ | **No** | **No** |
| **`CreatedBy_ID`** | Vytvoril | User who created the row (Gen sets on POST). | ✓ (Gen default) | **Yes** | **Yes** |
| **`Owner_ID`** | — | **Not on `crmactivity`.** Mobile maps `ownerId` → `ResponsibleUser_ID` only. | — | Via `ResponsibleUser_ID` | Via `ResponsibleUser_ID` |
| **`ResolvedBy_ID`** | Skutočný riešiteľ | Who actually resolved (runtime / completion). Separate from planned `SolverUser_ID`. | ✓ | **No** | **No** |

**Related (out of scope for My Day, relevant for desktop):**

| Field | Notes |
|-------|-------|
| `ActualSolverRole_ID` / `ActualSolverUser_ID` | Appear on a related Gen schema (not primary `crmactivity` header). Labels match desktop “Rola riešiteľa” / “Riešiteľ” in some views. |
| `PassSolverRole` (on `crmactivityqueue`) | “Prevziať rolu riešiteľa pri predaní” — queue config may copy solver role on native handover. |

### 2.2 Mobile CRM implementation (current)

Ownership filter (`ActivityMapper.BuildOwnershipWhere`):

```46:47:src/MobileCrm.Adapter.Gen/ActivityMapper.cs
    public static string BuildOwnershipWhere(string repUserId) =>
        $"(ResponsibleUser_ID eq '{repUserId}' or SolverUser_ID eq '{repUserId}' or CreatedBy_ID eq '{repUserId}')";
```

Detail edit guards use the same three fields (`IsOwnedByRepresentative`).

My Day adds further filters (`MyDayService`):

1. `Status` → `open` or `inProgress` only  
2. Ownership filter above  
3. `SheduledStart$DATE` on selected agenda date (today) or before it (overdue)

**Session representative:** `GET currentuser` → `id` stored as `repUserId` in Mobile session. This is a `securityuser` id, not a separate “representative” entity on DEMO.

---

## 3. My Day logic

### 3.1 Why an activity appears in Môj deň (Mobile CRM)

An activity is shown when **all** conditions hold:

| # | Condition | Source |
|---|-----------|--------|
| 1 | `ResponsibleUser_ID = rep` **or** `SolverUser_ID = rep` **or** `CreatedBy_ID = rep` | `BuildOwnershipWhere` |
| 2 | `Status` is `0` (Otvorená) or `1` (Riešená) | `IsOpenStatus` |
| 3 | `SheduledStart$DATE` is on the selected agenda date, or before it (overdue) | `MyDayService` timezone bucket |

**Not considered:** `SolverRole_ID`, `ResponsibleRole_ID`, role membership, firm access, or Gen agenda permissions.

### 3.2 Visibility matrix (Mobile CRM — verified on DEMO)

Test activities created 2026-06-08 with `Status = 0`, `SheduledStart$DATE` = today. Visibility = ownership filter match (date/status assumed satisfied).

| Scenario | Assignment persisted | JANO (`1200000101`) | Role member (not solver) | Named solver | API creator (`2610000101`) |
|----------|---------------------|:-------------------:|:------------------------:|:------------:|:--------------------------:|
| **SolverUser only** | `SolverUser_ID = JANO` | ✓ | ✗ | JANO ✓ | ✓ (`CreatedBy`) |
| **SolverRole only** | `SolverRole_ID = Technik`, `SolverUser_ID = null` | ✗ | DARA (Technik) **✗** | — | ✓ (`CreatedBy`) |
| **ResponsibleUser only** | `ResponsibleUser_ID = JANO` | ✓ | ✗ | — | ✓ (`CreatedBy`) |
| **SolverRole + SolverUser** | `SolverRole_ID = Obchodník`, `SolverUser_ID = JANO` | ✓ | MANE (Obchodník) **✗** | JANO ✓ | ✓ (`CreatedBy`) |
| **Combination (resp + role, no solver)** | `ResponsibleUser_ID = JANO`, `SolverRole_ID = Obchodník` | ✓ (via Responsible) | MANE **✗** | — | ✓ (`CreatedBy`) |

**Compact matrix (research question 2):**

| Scenario | Visible in Mobile My Day? |
|----------|:-------------------------:|
| SolverUser only | **Yes** (for that user + creator) |
| SolverRole only | **No** for role members; **Yes** only for creator |
| ResponsibleUser only | **Yes** (for responsible user + creator) |
| Combination (role + user) | **Yes** for `SolverUser` / `ResponsibleUser`; **not** for role-only members |

### 3.3 Gen native Môj deň (inferred)

ABRA desktop **Môj deň** is expected to include activities assigned to the user’s **roles** when `SolverUser_ID` is empty (role pool). DEMO confirms role membership via `GET securityroles/{roleId}/securityusers`.

Mobile CRM **does not replicate this today**. This is the largest product parity risk for field sales / handover workflows.

---

## 4. Activity handover test scenarios (A / B / C)

Created via `POST /crmactivities` (validate → commit) on DEMO. Reference fields inherited from seed activity `2000000101`.

### Scenario A — Obchodník + Jaroslav Novák

| | Value |
|---|-------|
| `SolverRole_ID` | `6000000101` (Obchodník) |
| `SolverUser_ID` | `1200000101` (Jaroslav Novák / JANO) |
| **Activity** | `J200000101` / `PrHo-18/2006` |

| User | Sees in Mobile My Day? | Reason |
|------|:----------------------:|--------|
| Jaroslav Novák (JANO) | ✓ | `SolverUser_ID` |
| Martin Nejedlý (MANE) — Obchodník role member | ✗ | Role not in ownership filter |
| API (creator) | ✓ | `CreatedBy_ID` |

### Scenario B — Technik + NULL user

| | Value |
|---|-------|
| `SolverRole_ID` | `1500000101` (Technik) |
| `SolverUser_ID` | `null` |
| **Activity** | `L200000101` / `PrHo-19/2006` |

| User | Sees in Mobile My Day? | Reason |
|------|:----------------------:|--------|
| Daniel Raščík (DARA) — Technik role member | ✗ | Role ignored by Mobile |
| JANO | ✗ | No user/resp match |
| API (creator) | ✓ | `CreatedBy_ID` |

**Gen desktop (inferred):** DARA and other Technik users would likely see this in native Môj deň.

### Scenario C — Technik + konkrétny technik

| | Value |
|---|-------|
| `SolverRole_ID` | `1500000101` (Technik) |
| `SolverUser_ID` | `4300000101` (Daniel Raščík / DARA) |
| **Activity** | `N200000101` / `PrHo-20/2006` |

| User | Sees in Mobile My Day? | Reason |
|------|:----------------------:|--------|
| DARA | ✓ | `SolverUser_ID` |
| JANO | ✗ | — |
| API (creator) | ✓ | `CreatedBy_ID` |

---

## 5. Roles / users API

### 5.1 Available endpoints (DEMO)

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `GET currentuser` | Session user (Mobile rep id) | Returns `id`, `loginname`, `name` |
| `GET securityroles` | List roles | `select=ID,Name,ShortName` works |
| `GET securityroles/{id}` | Role detail | e.g. Obchodník `6000000101`, Technik `1500000101` |
| `GET securityusers` | List users | `select=ID,Name,LoginName` |
| `GET securityusers/{id}` | User detail | |
| `GET securityroles/{roleId}/securityusers` | **Users in role** | Primary API for role → user picker |
| `GET securityusers/{userId}/securityroles` | **Roles for user** | JANO has Supervisor, Riaditeľ, compat role — **not** Obchodník |
| `GET securitygroups` | Role groups | Not explored in depth |

**Not found on DEMO OpenAPI index:** `representatives`, `securityuserroles` (standalone collection returned empty / unavailable).

### 5.2 DEMO ids (reference)

| Entity | ID | Login / short |
|--------|-----|---------------|
| API (integration user) | `2610000101` | API |
| Jaroslav Novák | `1200000101` | JANO |
| Martin Nejedlý (Obchodník) | `1300000101` | MANE |
| Daniel Raščík (Technik) | `4300000101` | DARA |
| Rola Obchodník | `6000000101` | Obchodník |
| Rola Technik | `1500000101` | Technik |
| Rola Predajca (common default on seed activities) | `1000000101` | Predajca |

### 5.3 Example requests

**List roles:**

```http
GET /demo/securityroles?take=20&select=ID,Name,ShortName
Authorization: Basic …
```

**List users:**

```http
GET /demo/securityusers?take=50&select=ID,Name,LoginName
Authorization: Basic …
```

**Users belonging to Technik role:**

```http
GET /demo/securityroles/1500000101/securityusers?take=50
Authorization: Basic …
```

Response (excerpt): Daniel Raščík (`4300000101`), Jan Novák (`2600000101`, locked).

**Roles for a user:**

```http
GET /demo/securityusers/1200000101/securityroles?take=20
Authorization: Basic …
```

**Filter users by id:**

```http
GET /demo/securityusers?where=ID%20eq%20'1200000101'&select=ID,Name,LoginName
Authorization: Basic …
```

### 5.4 List-query limitation

On DEMO, `crmactivities` list `where` on `SolverUser_ID` or `ResponsibleUser_ID` returned **HTTP 400**. `CreatedBy_ID` filter works. Mobile adapter uses the combined ownership OR clause — verify before relying on role-expanded queries.

---

## 6. Desktop behaviour (inferred)

### 6.1 UI control → Gen field mapping

| Desktop control (SK) | Gen field | Writable | Typical effect |
|---------------------|-----------|:--------:|----------------|
| **Rola riešiteľa** | `SolverRole_ID` | ✓ | Sets role pool; may clear or constrain user picker to role members |
| **Riešiteľ** | `SolverUser_ID` | ✓ | Sets concrete solver; role often remains as context |
| Zodpovedná rola | `ResponsibleRole_ID` | ✓ | Parallel “responsible” role pool |
| Zodpovedná osoba | `ResponsibleUser_ID` | ✓ | Parallel accountable user |
| Skutočný riešiteľ | `ResolvedBy_ID` | ✓ | Filled when work is actually done (may differ from planned solver) |

**“Kto bude riešiť?”** in Mobile should map to the **solver pair**: `SolverRole_ID` + `SolverUser_ID`.

### 6.2 Observed persistence rules (API create)

| Input | Gen persisted |
|-------|---------------|
| Only `SolverRole_ID` | Role set; `SolverUser_ID` null; `CreatedBy_ID` = API user |
| `SolverRole_ID` + `SolverUser_ID` | Both stored independently |
| Only `SolverUser_ID` | User set; role from POST body (required ref field) |
| `ResponsibleUser_ID` without solver | Responsible set; solver null |

`ResponsibleRole_ID` was **not auto-filled** from `SolverRole_ID` in tests (remained null).

### 6.3 PUT mutation

Direct `PUT` assignment change was **not completed** in this spike (HTTP 400 without full validate-then-commit flow). Desktop edits are assumed to use the same fields via standard Gen document PUT. Adapter already uses validate-then-commit for status changes.

---

## 7. Follow-up / handover inheritance

Context: Sprint 3A.4 follow-up create (`ActivityCreateService`) today:

| Field | Current behaviour |
|-------|-------------------|
| `SolverRole_ID` | **Inherit** from source (required ref) |
| `SolverUser_ID` | Inherit from source, fallback **session rep** |
| `ResponsibleUser_ID` | Inherit from source, fallback **session rep** |
| `CreatedBy_ID` | Gen sets to **API user** on POST |
| `Source_ID` | Set → source becomes `Status 3` (Odovzdané) |

### 7.1 Recommendation

| Field | On handover / follow-up | Rationale |
|-------|-------------------------|-----------|
| **`SolverRole_ID`** | **Inherit** from source (allow override in UI) | Required Gen reference; matches queue / `PassSolverRole` semantics; desktop chains keep process role context |
| **`SolverUser_ID`** | **User selects** (default: empty or session rep) | Handover often reassigns to another person or role pool; blind inherit leaves work with previous solver |
| **`ResponsibleUser_ID`** | **Default session rep**; allow override | Accountability moves to person doing handover; may differ from solver |

**Do not** rely on `CreatedBy_ID` for assignment — it only reflects who called the API and creates **creator visibility** in My Day even when assignee is someone else.

### 7.2 Suggested follow-up defaults

| UI choice | POST payload |
|-----------|--------------|
| “Ponechať rolu” | `SolverRole_ID` = source |
| “Priradiť mne” | `SolverUser_ID` = session rep, keep role |
| “Rola bez konkrétneho človeka” | `SolverUser_ID` = null, `SolverRole_ID` = selected role |
| “Konkrétny kolega” | `SolverUser_ID` = pick, `SolverRole_ID` = pick (user’s role or source role) |

---

## 8. Risks

| Risk | Severity | Detail |
|------|----------|--------|
| **Role pool invisible in Mobile My Day** | **High** | Scenario B: Technik role members never see activity; only API creator does. Breaks “assign to Technik” without naming a person. |
| **Creator always sees activity** | **Medium** | `CreatedBy_ID` in filter → integration user or handing-over rep sees tasks they assigned to others. |
| **`Owner_ID` naming confusion** | **Low** | API `ownerId` is `ResponsibleUser_ID`, not a separate Gen ownership concept. |
| **Responsible vs solver split** | **Medium** | Users may set only one of the pair; Mobile treats both as ownership but UI may not explain the difference. |
| **JANO ∉ Obchodník role** | **Low** (DEMO) | Real assignability is user-based (`SolverUser_ID`), not role membership — matches Mobile filter but differs from role-pool mental model. |
| **List `where` on solver fields** | **Low** | Some Gen list filters return 400; adapter must keep OR ownership clause valid on DEMO. |
| **Desktop parity unverified** | **Medium** | Native Môj deň role logic not observed in Win client this sprint. |

---

## 9. Recommendation — Mobile CRM model

### 9.1 “Kto bude riešiť?”

Expose two linked pickers matching Gen / desktop:

| Mobile label | Gen field | Required? | Picker data source |
|--------------|-----------|-----------|-------------------|
| **Rola riešiteľa** | `SolverRole_ID` | Yes (ref field) | `GET securityroles` |
| **Riešiteľ** | `SolverUser_ID` | No (nullable = role pool) | `GET securityroles/{SolverRole_ID}/securityusers` (filtered) |

**UX rules:**

1. Changing role refreshes user list; clear user if not in new role.  
2. Allow **empty Riešiteľ** when assigning to role pool (scenario B).  
3. Do **not** show `ResponsibleUser_ID` / `ResponsibleRole_ID` in MVP handover unless product asks — keep defaults server-side (session rep).  
4. On complete + schedule next step: pre-fill role from source; leave solver **empty** or default to session rep based on product choice (recommend **user pick** with session rep as default).

### 9.2 My Day parity decision (needed in 3B.1)

| Option | Behaviour |
|--------|-----------|
| **A — Keep user-only filter** | Simple; role-pool tasks invisible unless creator or named solver. |
| **B — Add role expansion** | Include activities where `SolverRole_ID` matches any of session user’s roles **and** `SolverUser_ID` is null. Closer to Gen desktop. |

**Recommend Option B** for field handover unless performance / query complexity blocks it (requires `securityusers/{id}/securityroles` cache + expanded `where` or post-filter).

---

## 10. Proposed Sprint 3B.1 scope

**Goal:** Assignment pickers for handover / follow-up and read APIs for roles and users. **No My Day filter change unless Option B is approved.**

### In scope

| Item | Description |
|------|-------------|
| **B1-1** | Adapter: `GET /api/v1/roles` → Gen `securityroles` (paginated, search by name) |
| **B1-2** | Adapter: `GET /api/v1/roles/{id}/users` → Gen `securityroles/{id}/securityusers` |
| **B1-3** | Adapter: `GET /api/v1/users` (optional search) → Gen `securityusers` for colleague picker |
| **B1-4** | Extend follow-up / create payload with `solverRoleId`, `solverUserId` (optional overrides) |
| **B1-5** | Web: “Kto bude riešiť?” section on completion handover form — role select + dependent user select |
| **B1-6** | Validation: user must belong to selected role (client + server) |
| **B1-7** | Docs + DEMO E2E: scenarios A/B/C visible to expected users **after** My Day decision |

### Out of scope (3B.1)

| Item | Defer to |
|------|----------|
| My Day role-pool expansion (Option B) | 3B.2 if approved |
| `ResponsibleRole_ID` / `ResponsibleUser_ID` UI | Later |
| Native desktop PUT assignment parity test | Manual QA |
| `pmchangestate` reassignment | Not needed — use POST fields |
| Activity list for “all team tasks” | Separate backlog |

### Acceptance hints

1. Handover form can assign to **Technik role only** (no user) and Gen persists `SolverUser_ID = null`.  
2. Handover form can assign to **JANO** under **Obchodník** role.  
3. Role user picker loads from `securityroles/{id}/securityusers`, not full user list.  
4. Follow-up activity inherits `SolverRole_ID` from source when user does not change role.

---

## 11. References

| Document | Relevance |
|----------|-----------|
| [sprint-3a-followup-spike.md](sprint-3a-followup-spike.md) | My Day rules, create ownership |
| [sprint-3a-3-handover-spike.md](sprint-3a-3-handover-spike.md) | `Source_ID`, ownership on handover |
| [sprint-3a-4-schedule-next-activity.md](sprint-3a-4-schedule-next-activity.md) | Current follow-up defaults |
| [analysis/spikes/sprint-3b0-activity-assignment-results.json](../analysis/spikes/sprint-3b0-activity-assignment-results.json) | Raw scenario results |

**Test activities (safe to delete):** `J200000101`, `L200000101`, `N200000101`, `P200000101`, `R200000101`.
