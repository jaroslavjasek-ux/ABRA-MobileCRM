# Sprint 0 — Backlog

**Sprint:** 0  
**Vertical slice:** Login → Session validation → My Day  
**Plan:** [sprint-0-plan.md](sprint-0-plan.md) · **Acceptance:** [sprint-0-acceptance-criteria.md](sprint-0-acceptance-criteria.md)

**Task states:** `todo` | `in_progress` | `done` | `deferred`

---

## Summary

| Area | Task count | IDs |
|------|------------|-----|
| Scaffold | 6 | S-* |
| Backend | 22 | B-* |
| Frontend | 22 | F-* |
| Testing | 12 | T-* |

---

## Scaffold (S)

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| S-01 | Create `MobileCrm.sln`, `src/MobileCrm.Adapter`, `src/MobileCrm.Adapter.Gen`, `tests/MobileCrm.Adapter.Tests` per [dev architecture §3](../architecture/development-architecture-v1.md) | Dev | — | S |
| S-02 | Create `src/MobileCrm.Web` (Vite + React + TS strict), `package.json`, `tests` placeholder for Vitest/Playwright | Dev | — | S |
| S-03 | Add `config/adapter.appsettings.template.json`, `config/web.env.template`; document copy to local gitignored config | Dev | S-01 | S |
| S-04 | Configure Vite dev proxy `/api` → adapter base URL | Dev | S-01, S-02 | S |
| S-05 | Add root `README` section: run adapter + run web (ports, config) | Dev | S-03, S-04 | S |
| S-06 | Add hand-maintained TS types under `src/api/types/` for `SessionResponse`, `MyDayResponse`, `ActivitySummary`, `SalesRepresentative`, `ApiError` aligned with API v1 §6–7 | Dev | — | S |

---

## Backend (B)

### B — Foundation

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| B-01 | `Program.cs`: Kestrel, controllers, JSON camelCase, problem details off (use contract envelope) | BE | S-01 | S |
| B-02 | `GET /health` liveness | BE | B-01 | S |
| B-03 | `CorrelationIdMiddleware` — read/generate `X-Correlation-Id`, attach to log context | BE | B-01 | S |
| B-04 | `GenClient` base: HttpClient from config `Gen:BaseUrl`, `Gen:Connection`, Basic auth handler for sandbox | BE | S-03 | M |
| B-05 | Gen smoke test helper or health check: `GET currentuser` with machine credentials (dev only) | BE | B-04 | S |

### B — Error envelope

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| B-06 | `ExceptionEnvelopeMiddleware` — map to `{ error: { code, message, details?, traceId } }` per API v1 §5.4 | BE | B-03 | M |
| B-07 | Map Gen 401 → `UNAUTHORIZED` 401; Gen unreachable → `SERVICE_UNAVAILABLE` 503 | BE | B-06 | S |

### B — Session

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| B-08 | `ISessionStore` in-memory implementation (session id → Gen auth context + `repUserId`) | BE | B-01 | S |
| B-09 | `GenAuthBridge`: validate `loginName`/`password` via Gen (Basic) + `GET currentuser` | BE | B-04, B-08 | M |
| B-10 | `SessionController`: `POST /session` — body validation, call bridge, issue Bearer token (opaque id), return `SessionResponse` | BE | B-09, B-06 | M |
| B-11 | `SessionController`: `GET /session` — require Bearer, refresh `SalesRepresentative` from `currentuser` (+ optional `securityusers` select) | BE | B-09, B-10 | M |
| B-12 | `SessionController`: `DELETE /session` — invalidate store entry, 204 | BE | B-08, B-10 | S |
| B-13 | Map `representative`: `id`, `loginName`, `displayName`, `email`; optional `employeeNumber` from `employees?where=Person_ID` (SR §4.2) | BE | B-11 | S |
| B-14 | Auth filter: reject missing/invalid Bearer on protected routes with `UNAUTHORIZED` | BE | B-10 | S |

### B — My Day

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| B-15 | `CrmActivityMapper`: Gen row → `ActivitySummary` (`Status` 0–3, `SheduledStart$DATE` → `scheduledStart`, etc.) | BE | B-04 | M |
| B-16 | `MyDayQueryBuilder`: ownership OR filter with `repUserId` (SR §5.2) | BE | B-15 | M |
| B-17 | Date predicates for `today` and `overdue` on `SheduledStart$DATE` + status rules per API v1 §7.2 (OQ-SR-04 fallback documented) | BE | B-16 | L |
| B-18 | `GET crmactivities` execution — allowlisted `select` (SR §5.3, LC-02); 1–2 queries for today/overdue | BE | B-17 | M |
| B-19 | Firm name enrichment: distinct `Firm_ID` → `GET firms/{id}?select=ID,Name` deduped | BE | B-18 | M |
| B-20 | `MyDayController`: `GET /my-day` — query params `date`, `take`; response `MyDayResponse` with counts | BE | B-19, B-14 | M |
| B-21 | Set `isOverdue` on summary rows per contract (server-derived) | BE | B-15 | S |
| B-22 | Unit tests: mapper status enum, OR `where` string builder (no Gen) | BE | B-15, B-16 | S |

### B — Optional / stretch

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| B-23 | `GET /health/ready` — probes Gen `currentuser` | BE | B-05 | S |
| B-24 | Serve empty `wwwroot` placeholder for future combined deploy | BE | B-01 | S |

---

## Frontend (F)

### F — Foundation

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| F-01 | `main.tsx`: Router, `QueryClientProvider`, `AuthProvider`, mobile viewport meta, global CSS tokens | FE | S-02 | S |
| F-02 | `app/config.ts`: `VITE_API_BASE_URL` default `/api/v1` | FE | S-04 | S |
| F-03 | `api/client.ts`: fetch wrapper, JSON parse, `ApiError`, Bearer injection, timeout | FE | S-06, F-02 | M |
| F-04 | `api/queryKeys.ts`: `session`, `myDay(date)` | FE | F-03 | S |
| F-05 | `auth/sessionStorage.ts` + `auth/AuthContext.tsx` + `useAuth` | FE | F-03 | M |
| F-06 | `lib/errors.ts`: map `error.code` → navigation targets | FE | F-03 | S |

### F — API modules

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| F-07 | `api/session.ts`: `postSession`, `getSession`, `deleteSession` | FE | F-03 | S |
| F-08 | `api/myDay.ts`: `getMyDay(date?, take?)` | FE | F-03 | S |
| F-09 | `useSessionQuery` / `useLoginMutation` / `useLogoutMutation` hooks | FE | F-07, F-05 | M |
| F-10 | `useMyDayQuery` with `staleTime`, refetch helpers | FE | F-08, F-04 | S |

### F — Routes and system screens

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| F-11 | `app/routes.tsx`: public + `/app` guarded routes per [dev architecture §5](../architecture/development-architecture-v1.md) | FE | F-05 | M |
| F-12 | `RequireAuth` guard — redirect `/login?returnTo=` | FE | F-11, F-05 | S |
| F-13 | `features/system/AppLoadingPage.tsx` (SCR-010): token? → `GET /session` → `/app/my-day` or `/login` | FE | F-09, F-11 | M |
| F-14 | `features/login/LoginPage.tsx` (SCR-001): form, loading, error display, `POST /session` | FE | F-09, F-13 | M |
| F-15 | `features/system/SessionExpiredPage.tsx` (SCR-008) + clear token | FE | F-06, F-11 | S |
| F-16 | `features/system/ConnectionErrorPage.tsx` (SCR-009) + `state.from` retry | FE | F-06, F-11 | S |
| F-17 | Global query `onError` / mutation handler: 401 → SCR-008; 503 → SCR-009 | FE | F-06, F-10 | M |
| F-18 | `hooks/useOnlineStatus.ts` + `ConnectivityBanner` on authenticated layout | FE | F-11 | S |

### F — My Day and shell

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| F-19 | `features/system/AuthenticatedLayout.tsx`: header, bottom nav — **My Day** active, **Customers** disabled/stub | FE | F-12 | M |
| F-20 | `features/my-day/MyDayPage.tsx` (SCR-002): greeting, date, today/overdue sections | FE | F-10, F-19 | M |
| F-21 | List row component: firm name, time, subject, status badge; loading skeleton | FE | F-20 | M |
| F-22 | Pull-to-refresh → `refetch` My Day query | FE | F-20 | S |
| F-23 | Empty states for zero today / zero overdue | FE | F-20 | S |
| F-24 | Row tap: navigate stub or toast “Sprint 1” (no SCR-006 yet) — **optional** | FE | F-21 | S |

### F — Stretch

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| F-25 | Logout control in layout → `DELETE /session` + `/login` | FE | F-09, F-19 | S |
| F-26 | Display `representative.displayName` in My Day header | FE | F-20, F-09 | S |

---

## Testing (T)

| ID | Task | Owner | Deps | Size |
|----|------|-------|------|------|
| T-01 | Adapter test fixture: `WebApplicationFactory`, mock `ISessionStore` optional | QA/BE | B-01 | S |
| T-02 | Integration: `POST /session` invalid credentials → 401 + envelope | QA/BE | B-10 | S |
| T-03 | Integration: `POST /session` valid sandbox user → 200 + `representative.id` | QA/BE | B-10, Gen DEMO | M |
| T-04 | Integration: `GET /session` without token → 401 | QA/BE | B-11 | S |
| T-05 | Integration: `GET /session` with token → 200 | QA/BE | B-11, T-03 | S |
| T-06 | Integration: `GET /my-day` without token → 401 | QA/BE | B-20 | S |
| T-07 | Integration: `GET /my-day` authenticated → 200 + `today`/`overdue` arrays (may be empty) | QA/BE | B-20, T-03 | M |
| T-08 | Integration: assert no `ResponsibleCustomerPerson_ID` in Gen request (log inspect or mock handler) | QA/BE | B-18 | S |
| T-09 | Vitest: `ApiError` parse; auth context reducer/storage | QA/FE | F-03, F-05 | S |
| T-10 | Vitest: My Day list renders empty + populated fixtures | QA/FE | F-21 | S |
| T-11 | Playwright: mobile viewport — cold `/app/loading` → login → My Day shows sections | QA/FE | F-13–F-23, T-03 | L |
| T-12 | Playwright: expired session — force 401 → session-expired → login | QA/FE | F-15, F-17 | M |
| T-13 | Manual: execute [acceptance script](sprint-0-acceptance-criteria.md) on DEMO; record user + date | QA | All | S |

---

## Suggested sprint board order

1. S-01 → S-06, S-02 → S-04  
2. B-01 → B-07 → B-08 → B-14 (session path)  
3. B-15 → B-22 (my-day path)  
4. F-01 → F-18 (parallel with B-10+)  
5. F-19 → F-26  
6. T-01 → T-13  

---

## Deferred from Sprint 0 (create tickets)

| Item | Backlog note |
|------|----------------|
| OpenAPI codegen | Sprint 1 — replace S-06 hand types |
| Firm/activity navigation from My Day row | Sprint 1–2 |
| Customers tab functional | Sprint 1 |
| Redis session store | Before TEST hardening |
| `vite-plugin-pwa` | Post–MVP shell |

---

## Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | Initial Sprint 0 backlog |
