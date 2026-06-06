# MVP scope — ABRA Mobile CRM

**Status:** Draft — subject to product workshop  
**Version:** 0.1  
**Last updated:** 2026-06-04

## Goal

Deliver a **usable mobile CRM** for field sales that reads and writes **ABRA Gen** data online, covering the highest-frequency day-in-the-life scenarios.

## In scope (MVP)

| # | Capability | Notes |
|---|------------|-------|
| M1 | Authenticate user against company identity + Gen API access | Mechanism TBD in architecture |
| M2 | Search and open **Firm** (customer hub) | List + detail; **commercial health** on detail |
| M3 | View firm-related **contacts** | Read from Gen |
| M4 | View recent **activities** / tasks for firm | Gen BO mapping TBD |
| M5 | **Create / complete** a visit or activity record | Write to Gen |
| M6 | **Dashboard**: today’s visits and overdue tasks | Aggregated from Gen queries |
| M7 | Basic **error and loading** UX for online-only | No offline queue |

## Out of scope (MVP)

| Item | Rationale | Target |
|------|-----------|--------|
| Offline mode & sync queue | ADR 0002 | Post-MVP ADR if needed |
| Full order entry / pricing engine | Complexity | Phase 2 |
| Custom reporting / BI | Use Gen reporting | Phase 2 |
| Admin configuration UI | Use Gen admin | Phase 2 |
| iOS + Android if stack picks one first | Delivery | Document in architecture ADR |
| Duplicate local CRM database | ADR 0001 | Never |

## Open questions

- [ ] Which Gen BO represents “activity” / visit?
- [ ] Required document types for MVP (offer vs order)?
- [ ] Geolocation on check-in required?
- [ ] Languages: SK/CZ/EN?

## Acceptance (MVP release)

- [ ] All **In scope** items implemented against Gen OpenAPI (no mock as production path)
- [ ] Signed-off journeys in [`../user-journeys/`](../user-journeys/)
- [ ] Security review for token storage and Gen permissions
- [ ] No authoritative business data stored outside Gen

## Change control

Changes to **In scope** / **Out of scope** require product owner approval and an ADR or version bump on this file.
