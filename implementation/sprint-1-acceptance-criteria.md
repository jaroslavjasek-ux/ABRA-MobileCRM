# Sprint 1 — Acceptance Criteria

**Sprint:** 1  
**Vertical slice:** Firm search → Firm detail → Contact detail  
**Prerequisite:** [Sprint 0 acceptance](sprint-0-acceptance-criteria.md) passed  
**Plan:** [sprint-1-plan.md](sprint-1-plan.md) · **Backlog:** [sprint-1-backlog.md](sprint-1-backlog.md)

**Test data (document per environment):**

| Artefact | DEMO reference |
|----------|----------------|
| Search term | Substring matching EUROCAR or known firm name |
| Firm with contacts | `3000000101` (EUROCAR) — contact spike §8 |
| Contact person | `6000000101` linked via firmperson |

---

## 1. Epic — Customer hub E2E

### AC-S1-E2E-01 — Search to contact

| Step | Given | When | Then |
|------|-------|------|------|
| 1 | User logged in | Tap **Customers** tab | SCR-003 firm search opens (`/app/firms`) |
| 2 | — | Type ≥2 char query matching test firm | `GET /firms?q=` returns results; list shows name + registration/city/code |
| 3 | — | Tap firm row | SCR-004 firm detail loads |
| 4 | Firm has contacts | View contacts section | At least one contact; **primary** indicated per server `isPrimary` |
| 5 | — | Tap contact | SCR-005 opens with `?firmId=`; name and firm link shown |
| 6 | — | Tap phone or email | OS handler opens (tel:/mailto:) |
| 7 | — | Back to firm, back to search | N-05: returns to search when opened from Customers tab |

### AC-S1-E2E-02 — My Day to firm

| Given | When | Then |
|-------|------|------|
| My Day shows activity with `firmName` | Tap firm name | Navigates to SCR-004 for that `firmId` |

### AC-S1-E2E-03 — Regression Sprint 0

| Criterion |
|-----------|
| Login and My Day still work per AC-S0-E2E-01/02 |

---

## 2. API — `GET /firms`

### AC-S1-API-FIRMS-01

| # | Criterion |
|---|-----------|
| 1 | `GET /api/v1/firms?q={term}&take=20&skip=0` with Bearer returns **200** and `{ items, total, hasMore }` |
| 2 | Each item is `FirmSummary` with `id`, `name`, `code`, `businessRegistrationNumber` (when Gen has value), `city` (when available), `commercialStatus` |
| 3 | `q` shorter than 2 characters returns **200** with `items: []` (or documented 400 — must match implementation) |
| 4 | Unauthenticated → **401** |
| 5 | Hidden firms excluded when Gen filter applied |

---

## 3. API — `GET /firms/{firmId}`

### AC-S1-API-FIRM-01

| # | Criterion |
|---|-----------|
| 1 | Valid `firmId` returns **200** `FirmDetailResponse` with `id`, `name`, `code`, `mainAddress`, `contacts[]` |
| 2 | Unknown `firmId` returns **404** `NOT_FOUND` |
| 3 | Contacts built from **`firmpersons`** — integration evidence: no `persons?where=Firm_ID` in logs |
| 4 | No contact with `IsEmployee` in customer list |
| 5 | `primaryContactId` matches contact with `isPrimary: true` when contacts exist |
| 6 | `commercialHealth` may be `null` — not an error |
| 7 | `recentActivities` may be `[]` — not an error |
| 8 | `website` populated when Gen provides firm web field |

### AC-S1-API-FIRM-02 — Address and phone (spike CM-07)

| # | Criterion |
|---|-----------|
| 1 | `mainAddress` includes company phone/email when `residenceaddress_id` or `electronicaddress_id` populated on DEMO firm |
| 2 | Contact card shows `phone1` or `email` when available on person or firmperson address |

---

## 4. API — `GET /contacts/{contactId}`

### AC-S1-API-CONTACT-01

| # | Criterion |
|---|-----------|
| 1 | `GET /api/v1/contacts/{id}?firmId={firmId}` returns **200** `ContactDetailResponse` |
| 2 | Includes `firstName`, `lastName`, `displayName`, `firmId`, `firmName`, `address`, `jobTitle` |
| 3 | With valid `firmId`, `isPrimary` reflects firm-context primary flag |
| 4 | Invalid/hidden person → **404** |
| 5 | Unauthenticated → **401** |

---

## 5. UI — SCR-003

### AC-S1-UI-SEARCH-01

| # | Criterion |
|---|-----------|
| 1 | Search field with debounce; no API call until `q.length >= 2` |
| 2 | Hint: search by name, registration number, or code |
| 3 | Loading and empty states |
| 4 | Mobile viewport 390×844 — usable list, no horizontal scroll |
| 5 | Pull-to-refresh refetches search |

---

## 6. UI — SCR-004

### AC-S1-UI-DETAIL-01

| # | Criterion |
|---|-----------|
| 1 | Firm name and commercial status visible in header |
| 2 | Registration and tax fields when returned by API |
| 3 | Main address formatted; tap-to-call company phone when present |
| 4 | Contacts section with primary marker |
| 5 | Commercial health section hidden when `commercialHealth` null |
| 6 | Recent activities section hidden or empty state when no rows |
| 7 | Phase 2 placeholders visible but not interactive |
| 8 | Pull-to-refresh refetches firm detail |

---

## 7. UI — SCR-005

### AC-S1-UI-CONTACT-01

| # | Criterion |
|---|-----------|
| 1 | Contact name and job title displayed |
| 2 | Firm name navigates to SCR-004 |
| 3 | Phone and email use `tel:` and `mailto:` when non-empty |
| 4 | Back returns to firm detail |

---

## 8. Navigation rules

| Rule | Acceptance |
|------|------------|
| N-02 | Customers tab always opens firm search |
| N-03 | My Day tab still opens My Day (regression) |
| N-05 | Back from firm detail after search path returns to search |

---

## 9. Non-functional

| ID | Criterion |
|----|-----------|
| AC-S1-NFR-01 | Firm search p95 &lt; 3s on TEST (NFR-P1) — measure once |
| AC-S1-NFR-02 | Firm detail p95 &lt; 5s on TEST (NFR-P2) — measure once |
| AC-S1-NFR-03 | Only `/api/v1/firms` and `/api/v1/contacts` added — no Gen URLs in browser |

---

## 10. Testing gate

| Gate | Requirement |
|------|-------------|
| Automated | T-14, T-15, T-16 pass (or documented manual substitute) |
| E2E | T-21, T-22 pass |
| Regression | T-25 (Sprint 0 smoke) |
| Manual | AC-S1-E2E-01 signed off with environment + test user |

---

## 11. Demo script (~8 minutes)

1. Login → My Day (Sprint 0).  
2. Tap **Customers** → search “EURO” (or documented term) → open EUROCAR.  
3. Show address, contacts, primary badge.  
4. Open contact → call/email links.  
5. Back → search → back to My Day tab.  
6. Tap firm from activity row → same firm detail.  
7. Network tab: only `/api/v1/firms` and `/api/v1/contacts` — no Gen.  

---

## 12. Out of scope — not accepted in Sprint 1

| Item |
|------|
| Log visit / activity create |
| Activity detail from recent activities |
| Contact create/edit |
| Global person search |
| Populated commercial health (required) |
| Working pipeline/quotes/orders |

---

## 13. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | Initial Sprint 1 acceptance criteria |
