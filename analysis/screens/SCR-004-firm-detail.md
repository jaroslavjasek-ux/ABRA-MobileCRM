# SCR-004: Firm detail

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-004 |
| **Business hub** | **Firm** — primary **customer** hub (domain model v0.2) |
| **MVP capabilities** | M2, M3, M4 — Firm detail; contacts; recent activities; commercial health |
| **Persona** | Field sales representative |
| **Journeys** | UJ-002 (prepare visit), UJ-003 (after visit context) |
| **Online required** | Yes |

## Purpose

Present a **customer 360°** read-only view: identity, **commercial health**, people, recent interactions, and (placeholders) pipeline and documents. Central anchor for “who is this customer?”

## User goals

- Confirm the correct customer before a visit
- See **credit and blocking context** before selling or collecting
- Call or navigate using address / phone from Gen
- Pick the right contact
- Review recent interactions
- Start or complete a visit for this firm
- Phase 2: open deals, quotes, and orders from the same place

## Information displayed

| Zone | Content | Gen source |
|------|---------|------------|
| Header | Firm name, commercial status badge (active / blocked / watch) | Firm |
| Summary card | IČO, DIČ, internal code, segment (if in Gen) | Firm |
| **Commercial health** | See § Commercial health section below | Commercial health signal |
| Address block | Main address formatted | Firm |
| Quick actions row | Phone, e-mail, map link | Firm |
| **Contacts** section | Contacts with name, role, phone | Contact |
| **Recent activities** section | Last 5–10 activities | Activity |
| **Pipeline snapshot** (optional MVP) | Open deal count or headline opportunity | Sales opportunity — if Gen CRM |
| **Opportunities** (Phase 2 placeholder) | List teaser → SCR-011 / SCR-012 | Sales opportunity |
| **Quotes** (Phase 2 placeholder) | List teaser → SCR-013 | Sales offer |
| **Orders** (Phase 2 placeholder) | List teaser → SCR-014 | Sales order |
| Loading / error | Per-section | — |

### Commercial health section (MVP)

Read-only **risk context for selling** (domain rule P-07). Not a separate screen.

| Element | Business meaning | MVP |
|---------|------------------|-----|
| Status line | Active / blocked / watch for sales | Yes |
| Credit indicator | Within limit / over limit / unknown | If Gen exposes |
| Overdue indicator | Any overdue receivable yes/no (not full ledger) | If Gen exposes |
| Visit guidance | Short text e.g. “Do not offer credit sales” | Derived from Gen rules |
| Phase 2 expansion | Ageing buckets, limit %, amounts | Links to receivable position detail in Gen UI policy |

**Empty / hidden:** If Gen denies finance fields, show status line only or “Contact finance” per permissions.

### Firm header fields (minimum)

| Label | Gen field (working) |
|-------|---------------------|
| Name | `Name` |
| Status | `PMState_ID` or status enumeration |
| IČO | `ICO` |
| DIČ | `DIC` |
| Code | `Code` |

### Phase 2 placeholder sections (UI)

| Section | MVP behaviour | Phase 2 behaviour |
|---------|---------------|-------------------|
| Opportunities | Hidden or single-line snapshot | List → SCR-012; “View all” → SCR-011 filtered |
| Quotes | Label + “Available in Phase 2” or hidden | List → SCR-013 |
| Orders | Label + “Available in Phase 2” or hidden | List → SCR-014 |

### Contact preview row

| Label | Gen field (working) |
|-------|---------------------|
| Full name | `Name` or `FirstName` + `LastName` |
| Role | Position / title TBD |
| Phone | `Phone`, `Mobile` TBD |

### Activity preview row

| Label | Gen field (working) |
|-------|---------------------|
| Date | `StartDate` / `DueDate` |
| Type + status | Enumerations |
| Subject | `Subject` |

## Available actions

| Action | Behaviour |
|--------|-----------|
| Back | SCR-003 (search) or SCR-002 (My Day) per stack |
| Tap phone / e-mail / maps | OS handlers |
| Tap contact row | SCR-005 Contact detail |
| Tap activity row | SCR-006 Activity detail |
| **Log visit** | SCR-007 with `Firm_ID` pre-filled |
| Tap pipeline snapshot / opportunity row | SCR-012 or SCR-011 (Phase 2) |
| Tap quote / order row | SCR-013 / SCR-014 (Phase 2) |
| Pull to refresh | Reload all sections from Gen |

**Not in MVP:** Edit firm, create contact, create quote/order.

**Blocked by commercial health (Gen rule P-04):** Log visit or Phase 2 drafts when firm blocked — show message from Gen.

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-003 Firm search | Tap result (primary customer hub entry) |
| **Incoming** | SCR-002 My Day | Tap firm on agenda row |
| **Incoming** | SCR-005, SCR-006, SCR-007 | Back navigation |
| **Incoming** | SCR-012 (Phase 2) | Back from opportunity |
| **Outgoing** | SCR-005 Contact detail | Tap contact |
| **Outgoing** | SCR-006 Activity detail | Tap activity |
| **Outgoing** | SCR-007 Log visit | CTA |
| **Outgoing** | SCR-003 Firm search | Back / Customers tab |
| **Outgoing** | SCR-002 My Day | Tab |
| **Outgoing** | SCR-011–014 | Phase 2 commercial |

## Related ABRA business objects

| Object | Role |
|--------|------|
| **Firm** | Primary |
| **Commercial health signal** | Read-only aggregate on firm |
| **Contact**, **Activity** | Sections |
| **Sales opportunity** | Snapshot (MVP optional) / list (Phase 2) |
| **Sales offer**, **Sales order** | Phase 2 placeholders |

## Open design notes

- [ ] Section order: commercial health immediately under header (recommended)
- [ ] Show primary contact flag
- [ ] Pipeline snapshot when Gen has no CRM — hide section

## Acceptance hints

- Commercial health never editable on this screen
- Single `Firm_ID` in route
- Phase 2 placeholders do not imply local data — labels only in MVP
