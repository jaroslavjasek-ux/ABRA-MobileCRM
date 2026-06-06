# Sprint 1 — Backlog

**Sprint:** 1  
**Vertical slice:** Firm search → Firm detail → Contact detail  
**Prerequisite:** [Sprint 0](sprint-0-backlog.md) complete  
**Plan:** [sprint-1-plan.md](sprint-1-plan.md) · **Acceptance:** [sprint-1-acceptance-criteria.md](sprint-1-acceptance-criteria.md)

---

## Summary

| Area | Task count | IDs |
|------|------------|-----|
| Backend | 28 | B-25–B-52 |
| Frontend | 16 | F-27–F-42 |
| Testing | 11 | T-14–T-24 |

---

## Backend (B)

### B — Firm search (`GET /firms`)

| ID | Task | Deps | Size |
|----|------|------|------|
| B-25 | `FirmsController`: `GET /firms` — validate `q` min length 2 (prefer 200 + empty per API) | Sprint 0 B-14 | S |
| B-26 | `FirmSearchQueryBuilder` — configurable `where` on Name/Code/OrgIdentNumber (document DEMO template) | B-25 | L |
| B-27 | `FirmSummaryMapper` — `ID`, `Name`, `Code`, `OrgIdentNumber` → `businessRegistrationNumber`, `city` from address projection | B-26 | M |
| B-28 | Exclude `Hidden eq true` when supported | B-26 | S |
| B-29 | Pagination `take`/`skip`; cap take at 50; return `PagedResult` shape | B-25 | S |
| B-30 | Map Gen list errors → contract envelope | B-06 | S |
| B-31 | Integration test: search known substring returns ≥1 firm on DEMO | B-25–29, Gen | M |
| B-32 | Integration test: `q` length 1 → empty items (no 500) | B-25 | S |

### B — Firm detail (`GET /firms/{firmId}`)

| ID | Task | Deps | Size |
|----|------|------|------|
| B-33 | `FirmsController`: `GET /firms/{firmId}` — 404 when not found | B-25 | S |
| B-34 | `GenFirmReader` — `GET firms/{id}` full payload (OQ-CM-01: no invalid nested select) | B-04 | M |
| B-35 | `FirmpersonParser` — extract `firmpersons[]`; map to `ContactSummary`; sort by PosIndex; set `isPrimary` per BR-CM-05 | B-34 | L |
| B-36 | Filter contacts: skip `IsEmployee`, `Hidden` persons | B-35 | S |
| B-37 | `AddressMapper` — `residenceaddress_id` → `mainAddress`; `electronicaddress_id` → `electronicAddress` | B-34 | M |
| B-38 | Resolve contact `phone1`/`email` on list cards per CM-07 (firmperson embed → person optional batch) | B-35, B-37 | M |
| B-39 | `FirmDetailMapper` — header fields, `taxNumber`, `commercialStatus`, `website`, `primaryContactId` | B-34 | M |
| B-40 | `commercialHealth` — return `null` until workshop (stub mapper) | B-39 | S |
| B-41 | `recentActivities` — provisional `crmactivities?where=Firm_ID`; on failure return `[]` + log | B-04, LC spike | M |
| B-42 | Optional `meta.availability` for bestEffort sections | B-39 | S |
| B-43 | Integration test: `GET firms/{demoFirmId}` returns contacts array length ≥0; EUROCAR ≥1 contact | B-33–36, Gen | M |
| B-44 | Unit test: `FirmpersonParser` primary selection (`InitialFirmPerson_ID` vs PosIndex) | B-35 | S |
| B-45 | Unit test: employee person excluded from contact list | B-36 | S |

### B — Contact detail (`GET /contacts/{contactId}`)

| ID | Task | Deps | Size |
|----|------|------|------|
| B-46 | `ContactsController`: `GET /contacts/{contactId}` | Sprint 0 B-14 | S |
| B-47 | `GET persons/{id}` with allowlisted select (contact spike §7.1) | B-04 | M |
| B-48 | Address embed or `GET addresses/{id}` when phones/email missing | B-47 | M |
| B-49 | `ContactDetailMapper` — `ContactDetailResponse`; `isPrimary` when `firmId` query matches firm context | B-46 | M |
| B-50 | Load `firmName` via `GET firms/{firmId}?select=ID,Name` or cache from prior request | B-49 | S |
| B-51 | 404 when person hidden or not found | B-47 | S |
| B-52 | Integration test: contact detail for EUROCAR person `6000000101` (or documented id) | B-46–51, Gen | M |

---

## Frontend (F)

### F — API and types

| ID | Task | Deps | Size |
|----|------|------|------|
| F-27 | Extend `api/types` — `FirmSummary`, `PagedResult`, `FirmDetailResponse`, `ContactSummary`, `ContactDetailResponse`, `CommercialHealth` | API v1 §6 | S |
| F-28 | `api/firms.ts` — `searchFirms(q, take, skip)`, `getFirmDetail(firmId, recentTake?)` | F-03 | S |
| F-29 | `api/contacts.ts` — `getContact(contactId, firmId?)` | F-03 | S |
| F-30 | Query keys: `firms.search(q, skip)`, `firms.detail(id)`, `contacts.detail(id, firmId)` | F-04 | S |
| F-31 | `useFirmSearchQuery` with debounce 300ms; enabled when `q.length >= 2` | F-28, F-30 | M |
| F-32 | `useFirmDetailQuery`; `useContactDetailQuery` | F-28, F-29 | S |

### F — Navigation and shell

| ID | Task | Deps | Size |
|----|------|------|------|
| F-33 | Add routes `/app/firms`, `/app/firms/:firmId`, `/app/contacts/:contactId` | F-11 | S |
| F-34 | Enable **Customers** tab → `/app/firms` (remove Sprint 0 stub) | F-19, F-33 | S |
| F-35 | `lib/navigation.ts` — `backFromFirmDetail()` per N-05 | F-33 | S |

### F — SCR-003 Firm search

| ID | Task | Deps | Size |
|----|------|------|------|
| F-36 | `FirmSearchPage` — search input, clear, hint copy | F-31, F-34 | M |
| F-37 | Result list rows: name, `businessRegistrationNumber`, city, code | F-36 | M |
| F-38 | Loading skeleton, empty state, initial prompt (&lt;2 chars) | F-36 | S |
| F-39 | Tap row → `/app/firms/:firmId`; pagination or “load more” if `hasMore` | F-36 | M |
| F-40 | Pull-to-refresh on search results | F-36 | S |

### F — SCR-004 Firm detail

| ID | Task | Deps | Size |
|----|------|------|------|
| F-41 | `FirmDetailPage` — header, status badge, registration/tax/code | F-32 | M |
| F-42 | Address block + `tel:`/`mailto:`/`https:` for website | F-41 | M |
| F-43 | Contacts section — list with primary indicator, tap → contact detail with `?firmId=` | F-41 | M |
| F-44 | Commercial health section — render when non-null; hide when null | F-41 | S |
| F-45 | Recent activities section — list or hide when empty; tap row stub “Sprint 2” | F-41 | S |
| F-46 | Phase 2 placeholder blocks (pipeline/quotes/orders) — static copy only | F-41 | S |
| F-47 | Pull-to-refresh; 404 firm not found state | F-41 | S |
| F-48 | Back button using N-05 | F-35, F-41 | S |

### F — SCR-005 Contact detail

| ID | Task | Deps | Size |
|----|------|------|------|
| F-49 | `ContactDetailPage` — header, job title, address phones/email | F-32, F-33 | M |
| F-50 | Firm name link → `/app/firms/:firmId` | F-49 | S |
| F-51 | `tel:` and `mailto:` links | F-49 | S |
| F-52 | Back → firm detail; pull-to-refresh | F-49 | S |

### F — Integration with Sprint 0

| ID | Task | Deps | Size |
|----|------|------|------|
| F-53 | My Day activity row — tap `firmName` → `/app/firms/:firmId` | F-21, F-33 | S |
| F-54 | Optional: header **Log visit** on firm detail disabled with “Sprint 2” tooltip | F-41 | S |

---

## Testing (T)

| ID | Task | Deps | Size |
|----|------|------|------|
| T-14 | Integration: `GET /firms?q=…` authenticated → 200 paged shape | B-25–29 | M |
| T-15 | Integration: `GET /firms/{id}` → contacts[], `mainAddress` | B-33–39 | M |
| T-16 | Integration: `GET /contacts/{id}?firmId=` → 200 | B-46–51 | M |
| T-17 | Integration: assert adapter never calls `persons?where=Firm_ID` (grep/log) | B-35 | S |
| T-18 | Vitest: `FirmpersonParser` fixtures (unit mirror if parser in shared test data) | B-44 | S |
| T-19 | Vitest: firm search debounce hook | F-31 | S |
| T-20 | Vitest: contact list renders primary badge | F-43 | S |
| T-21 | Playwright: Customers tab → search → open firm → open contact | F-36–52 | L |
| T-22 | Playwright: My Day → tap firm → firm detail | F-53 | M |
| T-23 | Playwright: back from firm detail to search (N-05) | F-48 | S |
| T-24 | Manual: [acceptance script](sprint-1-acceptance-criteria.md) | All | S |
| T-25 | Regression: Sprint 0 login + My Day smoke | T-11 | S |

---

## Suggested board order

1. B-25 → B-32  
2. B-33 → B-45 (parallel F-27–F-30)  
3. B-46 → B-52  
4. F-33 → F-40 → F-41 → F-48 → F-49 → F-52  
5. F-53, T-14–T-25  

---

## Deferred (tickets)

| Item | Sprint |
|------|--------|
| `GET /firms/{id}/contacts` endpoint | 2 (log visit picker) |
| Firm search “my customers only” filter | OQ-SR-05 |
| Optimized firm payload (OQ-CM-01) | Hardening |
| i18n framework | Post-MVP |
| OpenAPI codegen for firm/contact types | When spec published |

---

## Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | Initial Sprint 1 backlog |
