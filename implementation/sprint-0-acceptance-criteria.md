# Sprint 0 — Acceptance Criteria

**Sprint:** 0  
**Vertical slice:** Login → Session validation → My Day  
**Plan:** [sprint-0-plan.md](sprint-0-plan.md) · **Backlog:** [sprint-0-backlog.md](sprint-0-backlog.md)

**Environment:** Gen sandbox (e.g. DEMO) + adapter + web dev proxy or combined TEST host.  
**Test user:** Document `loginName` used — must have at least one activity visible via OR ownership filter on test date (see [sales rep spike §5.2](../analysis/spikes/sales-representative-model.md)).

---

## 1. Epic: End-to-end vertical slice

### AC-S0-E2E-01 — Happy path (cold start)

| Step | Given | When | Then |
|------|-------|------|------|
| 1 | No session token in browser | User opens `/` or `/app/loading` | SCR-010 loading shown |
| 2 | Valid Gen credentials | User completes SCR-001 login | `POST /session` returns 200; token stored; navigate to `/app/my-day` |
| 3 | Authenticated | My Day loads | `GET /my-day` returns 200; **Today** and **Overdue** sections render (may be empty) |
| 4 | Response includes activities | Lists display | Each row shows **firm name**, **scheduled time**, **subject**, **status** per contract `ActivitySummary` |
| 5 | Network tab | Inspect browser requests | **Only** calls to `/api/v1/*` — **no** direct Gen URLs |

### AC-S0-E2E-02 — Return visit (session validation)

| Step | Given | When | Then |
|------|-------|------|------|
| 1 | Valid token from prior login | User opens app (SCR-010) | `GET /session` called with Bearer |
| 2 | Session valid | Bootstrap completes | User lands on `/app/my-day` **without** re-entering password |
| 3 | Session invalid/expired | `GET /session` returns 401 | User routed to SCR-008 or login |

### AC-S0-E2E-03 — Pull-to-refresh

| Given | When | Then |
|-------|------|------|
| User on SCR-002 | Pull-to-refresh gesture | `GET /my-day` refetched; list updates; loading indicator shown during fetch |

---

## 2. Session API (adapter)

### AC-S0-API-SESSION-01 — Login

| ID | Criterion |
|----|-----------|
| 1 | `POST /api/v1/session` with valid `loginName`/`password` returns **200** and body matches `SessionResponse` ( `representative` required fields: `id`, `loginName`, `displayName` ) |
| 2 | `representative.id` equals Gen `currentuser.id` for same credentials (spike SR-01) |
| 3 | Invalid credentials return **401** with `error.code` = `UNAUTHORIZED` |
| 4 | Gen unreachable returns **503** with `error.code` = `SERVICE_UNAVAILABLE` |
| 5 | Response does not include Gen password or raw Gen error stacks |

### AC-S0-API-SESSION-02 — Session check

| ID | Criterion |
|----|-----------|
| 1 | `GET /api/v1/session` with valid Bearer returns **200** and same representative shape |
| 2 | Missing or invalid Bearer returns **401** / `UNAUTHORIZED` |
| 3 | Optional: `DELETE /api/v1/session` returns **204** and subsequent `GET` returns 401 |

---

## 3. My Day API (adapter)

### AC-S0-API-MYDAY-01 — List contract

| ID | Criterion |
|----|-----------|
| 1 | `GET /api/v1/my-day` with valid Bearer returns **200** and `MyDayResponse`: `date`, `representative`, `today[]`, `overdue[]`, `todayCount`, `overdueCount` |
| 2 | Without Bearer returns **401** |
| 3 | Each activity item includes contract fields: `id`, `subject`, `status`, `firmId`, `firmName`, `scheduledStart`, `isOverdue` |
| 4 | `status` values are CRM enums (`open`, `inProgress`, `completed`, `handedOver`) — not raw Gen integers in JSON |
| 5 | Adapter uses **`crmactivities`** only (not `tasks`) — verified in logs or integration test |

### AC-S0-API-MYDAY-02 — Ownership filter (spike)

| ID | Criterion |
|----|-----------|
| 1 | Activities returned satisfy adapter policy: **any** of `ResponsibleUser_ID`, `SolverUser_ID`, `CreatedBy_ID` = session `representative.id` (OR filter) |
| 2 | Test user documented where DEMO data uses `CreatedBy_ID` / `SolverUser_ID` when `ResponsibleUser_ID` is null |

### AC-S0-API-MYDAY-03 — Date slices

| ID | Criterion |
|----|-----------|
| 1 | `today` items have `scheduledStart` on agenda `date` (per adapter timezone config) and statuses consistent with API v1 default (open + inProgress unless product widens) |
| 2 | `overdue` items have `status` in open/inProgress and `scheduledStart` before start of agenda `date` |
| 3 | Query param `date=YYYY-MM-DD` changes agenda date when provided |
| 4 | If date `where` fails on Gen, defect logged with OQ-SR-04 — not silent wrong data |

### AC-S0-API-MYDAY-04 — Firm names

| ID | Criterion |
|----|-----------|
| 1 | When activity has `firmId`, `firmName` is populated (non-empty) for list display — via firm lookup, not raw Gen field in browser |

---

## 4. Frontend (browser)

### AC-S0-UI-LOGIN-01 — SCR-001

| ID | Criterion |
|----|-----------|
| 1 | Login form: `loginName`, `password`, submit disabled while loading |
| 2 | Failed login shows human-readable message (from `error.message`) |
| 3 | No firm/activity data visible on login screen |
| 4 | Successful login navigates to My Day (N-01) |

### AC-S0-UI-LOADING-01 — SCR-010

| ID | Criterion |
|----|-----------|
| 1 | Loading screen shows branding/spinner; no business lists |
| 2 | No token → redirect login |
| 3 | Token + valid session → My Day |

### AC-S0-UI-MYDAY-01 — SCR-002

| ID | Criterion |
|----|-----------|
| 1 | Header shows user-friendly name and agenda date |
| 2 | **Today** and **Overdue** sections with distinct headings |
| 3 | Empty state copy when section has zero items |
| 4 | Connectivity banner reflects offline (SCR-009 pattern) when `navigator.onLine` false |
| 5 | Layout usable on **390×844** viewport — no horizontal scroll on list |
| 6 | **Customers** tab not functional — disabled or labelled future sprint |

### AC-S0-UI-ERRORS-01 — SCR-008 / SCR-009

| ID | Criterion |
|----|-----------|
| 1 | API 401 on protected route clears session and shows session-expired or login |
| 2 | API 503 or network failure on My Day shows connection-error with retry |
| 3 | Retry returns user to prior route when possible (N-07) |

---

## 5. Non-functional (Sprint 0)

| ID | Criterion |
|----|-----------|
| AC-S0-NFR-01 | All adapter logs for session/my-day include correlation id; no passwords in logs |
| AC-S0-NFR-02 | Session token not stored in `localStorage` (sessionStorage or httpOnly cookie only) |
| AC-S0-NFR-03 | `GET /health` returns 200 when adapter process up |
| AC-S0-NFR-04 | Local dev documented: start adapter + web with proxy in under 15 minutes for new developer |

---

## 6. Testing gate

Sprint 0 is **accepted** when:

| Gate | Requirement |
|------|-------------|
| Automated | T-03, T-05, T-07 pass in CI against configured Gen sandbox (or skip CI Gen with documented manual substitute) |
| E2E | T-11 passes locally |
| Manual | AC-S0-E2E-01 executed and signed off (name, date, environment in test log) |
| Regression | No `tasks` controller calls; no `ResponsibleCustomerPerson_ID` in activity select |

---

## 7. Demo script (5 minutes)

1. Start adapter + web; open mobile browser emulator → `https://localhost:.../app/loading`.  
2. Observe redirect to login; enter sandbox credentials.  
3. Land on My Day — point out Today / Overdue sections and row fields.  
4. Pull-to-refresh — data reloads.  
5. Open DevTools → Network — show only `/api/v1/session` and `/api/v1/my-day`.  
6. Invalidate session (clear storage or wait expiry) → reload → session-expired/login.  
7. Stop adapter → refresh → connection error + retry.

---

## 8. Out of scope — not accepted in Sprint 0

| Item | Reason |
|------|--------|
| Firm search opens from Customers tab | Sprint 1 |
| Activity detail from row tap | Sprint 2 |
| Log visit FAB working end-to-end | Sprint 2 |
| Commercial health on any screen | Sprint 1+ |
| Offline queue or cached business data | ADR 0002 |
| Native app install | Product constraint |

---

## 9. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | Initial Sprint 0 acceptance criteria |
