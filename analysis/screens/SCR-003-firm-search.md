# SCR-003: Firm search

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-003 |
| **Business hub** | **Firm** — entry to primary **customer** hub |
| **MVP capabilities** | M2 — Search and open Firm |
| **Persona** | Field sales representative |
| **Journey** | UJ-002 — Find firm before visit |
| **Online required** | Yes |

## Purpose

Let the rep **find a customer (Firm)** quickly by name, company ID (IČO), or internal code while on the road, then open the firm record for visit preparation.

## User goals

- Locate the correct customer among similar names
- See enough context in results to disambiguate (city, ICO)
- Open full firm detail in one tap
- Recover from no results or search errors

## Information displayed

| Zone | Content | Gen source |
|------|---------|------------|
| Search field | Query input with clear button | Local state |
| Hint text | “Search by name, IČO, or code” | Copy |
| Results list | Matching firms (paginated) | `Firm` collection `GET` |
| Result row | Name, ICO, city/locality, internal code | `Firm` fields TBD |
| Loading | Skeleton or spinner while querying | Client |
| Empty | No matches for query | — |
| Initial | Prompt to type (min 2–3 chars) before search | Product rule |

### Firm result row (minimum fields)

| Label | Gen field (working) |
|-------|---------------------|
| Name | `Name` |
| IČO | `ICO` (or local equivalent) |
| City | Address city field TBD (`City`, `Locality`, etc.) |
| Code | `Code` or `FirmCode` |

## Available actions

| Action | Behaviour | Gen |
|--------|-----------|-----|
| Type query | Debounced search (e.g. 300 ms) | `GET /firm?where=...` |
| Clear search | Reset list to initial state | — |
| Tap result | Open SCR-004 Firm detail for `Firm.ID` | No |
| Pull to refresh | Re-run current query | `GET` |
| Cancel / back | Return to SCR-002 Home | — |

**Blocked when offline:** Search (show banner; no stale result list as authoritative).

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-002 My Day | **Customers** tab or search action |
| **Incoming** | SCR-004 Firm detail | Back from detail |
| **Incoming** | SCR-007 Log visit | Firm picker (create mode) |
| **Outgoing** | SCR-004 Firm detail | Tap result |
| **Outgoing** | SCR-002 My Day | **My Day** tab |
| **Outgoing** | SCR-009 Connection error | Search fails |

## Related ABRA business objects

| Object | Relationship | Operations |
|--------|--------------|------------|
| **Firm** | Sole search target | `GET` collection |

### Search predicates (working)

| User input | Suggested `where` clause (verify on OpenAPI) |
|------------|-----------------------------------------------|
| Name | `Name like '*{term}*'` |
| IČO | `ICO eq '{term}'` or like |
| Code | `Code eq '{term}'` |

Combined OR across fields for single search box (implementation validates performance).

### Fields to `select`

`ID`, `Name`, `ICO`, address summary fields, `Code`, optional `PMState_ID` if needed for inactive firms filter.

### Filters (product)

- [ ] Hide inactive / blocked firms (`PMState_ID` or equivalent)
- [ ] Respect Gen row-level permissions (automatic via token)

## Open design notes

- [ ] Minimum characters before search
- [ ] Recent firms (client-only UX list of IDs — **not** Gen truth, optional Phase 1.1)
- [ ] Barcode / scan customer code (out of MVP)

## Acceptance hints

- p95 search latency per NFR-P1
- Pagination with `take` / `skip` or cursor per Gen API
- Tapping result always passes `Firm.ID` to detail screen
