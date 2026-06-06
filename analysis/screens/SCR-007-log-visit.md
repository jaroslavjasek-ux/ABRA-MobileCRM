# SCR-007: Log visit

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-007 |
| **Business hub** | **My Day** / **Firm** (write path; returns to origin hub) |
| **MVP capabilities** | M5 — Create / complete visit or activity |
| **Persona** | Field sales representative |
| **Journey** | UJ-003 — Log visit outcome |
| **Online required** | Yes (writes blocked offline) |

## Purpose

Capture or update a **field visit (activity)** in ABRA Gen: schedule a new visit, record outcome after meeting, or complete an existing open activity.

## Modes

| Mode | Entry | Gen operation |
|------|-------|---------------|
| **Create** | FAB on SCR-002; Log visit on SCR-004 | `POST` Activity |
| **Complete** | Complete on SCR-006 | `PUT` Activity (status + outcome) |
| **Edit** | Edit on SCR-006 (open only) | `PUT` Activity |

## User goals

- Record what happened on the visit in under 2 minutes
- Tie visit to the correct firm (and contact if applicable)
- Set or confirm date/time
- Mark activity complete so back office sees it in Gen immediately
- Cancel without saving partial data to Gen

## Information displayed

| Zone | Content | Mode |
|------|---------|------|
| Firm selector | Selected firm name + change | Create (required); locked in Complete/Edit if pre-filled |
| Contact selector (optional) | Dropdown of firm contacts | All modes |
| Opportunity selector | Phase 2 placeholder — link to open deal | Phase 2 |
| Activity type | Visit / call / task (enum) | Create / Edit |
| Date & time | Start (and end optional) | All |
| Subject | Short title | All |
| Notes | Multi-line outcome / plan | All |
| Status | Open vs completed (Complete mode defaults to completed) | Complete / Edit |
| Validation errors | Field-level from Gen `validation=true` | On save fail |
| Saving overlay | Non-dismissible while POST/PUT in flight | Save |

**Pre-filled from route:**

- `Firm_ID` from SCR-004 / SCR-005
- `Activity_ID` + fields from SCR-006 in Complete/Edit

## Available actions

| Action | Behaviour | Gen |
|--------|-----------|-----|
| Select firm | Open SCR-003 picker or modal search (create only) | — |
| Select contact | List from `GET` contacts for firm | Read |
| Save | Validate client-side → `POST` or `PUT` with `?validation=true` | Write |
| Cancel | Discard; confirm if dirty | — |
| Change firm | Only in create before save | — |

**Blocked when offline:** Save (show message; no queue).

**On save success:** Navigate back to **origin hub** per N-04 (SCR-002 My Day, SCR-004 Firm, or SCR-006) and show brief success toast.

**On Gen validation error:** Stay on form; show field errors from API body.

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-002 My Day | Log visit FAB |
| **Incoming** | SCR-004 Firm detail | Log visit CTA |
| **Incoming** | SCR-005 Contact detail | Optional log visit |
| **Incoming** | SCR-006 Activity detail | Complete / Edit |
| **Outgoing** | SCR-003 Firm search | Pick firm (create) |
| **Outgoing** | SCR-002 / SCR-004 / SCR-006 | Save success or cancel |
| **Outgoing** | SCR-009 Connection error | Save failed — network |
| **Outgoing** | SCR-008 Session expired | 401 on save |

## Related ABRA business objects

| Object | Relationship | Operations |
|--------|--------------|------------|
| **Activity** (TBD) | Created or updated record | `POST`, `PUT` with `validation=true` |
| **Firm** | Required link | `Firm_ID` on body |
| **Contact** | Optional link | `Contact_ID` TBD |
| **User / Employee** | Auto-set responsible to current user | Default on `POST` |

### Minimum write payload (working)

| Field | Create | Complete |
|-------|--------|----------|
| `Firm_ID` | Required | Read-only |
| `Subject` | Required | Optional update |
| `StartDate` | Required | Optional |
| `Description` | Optional | Outcome notes |
| `Status` | Open (default) | Completed |
| `ActivityType` | Required enum | — |

### API pattern (ABRA 26+)

```http
POST /{connection}/activity?validation=true
PUT  /{connection}/activity/{id}?validation=true
```

Nested collections on activity header (if any) follow header POST/PUT rules — confirm on OpenAPI spike.

## Open design notes

- [ ] Required fields match Gen business rules (not only UI)
- [ ] Default start time = now for create
- [ ] Duplicate visit prevention (same firm + same day) — Gen rule or app warning?
- [ ] Geolocation on save (MVP scope question)

## Acceptance hints

- No save when offline
- Successful save visible in Gen within one round-trip
- Cancel does not call Gen
- Create from SCR-002 without firm forces firm selection before save (via SCR-003)
- Firm blocked (commercial health P-04) prevents save with clear message
