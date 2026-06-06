# SCR-006: Activity detail

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-006 |
| **Business hub** | **My Day** (operational drill-down) |
| **MVP capabilities** | M4 — View activities; entry point for M5 complete |
| **Persona** | Field sales representative |
| **Journeys** | UJ-001, UJ-003 |
| **Online required** | Yes |

## Purpose

Display **full context of one CRM activity** (visit, task, call) and allow the rep to **complete** or **edit** it when status is open — without duplicating data outside Gen.

## User goals

- Understand what was planned (time, firm, subject, notes)
- Open the related customer record
- Mark activity complete or update outcome after visit
- See who owns the activity and current status

## Information displayed

| Zone | Content | Gen source |
|------|---------|------------|
| Header | Activity type + status badge | `Activity` |
| Subject / title | Main line | `Subject` TBD |
| Schedule | Start, end, due date/time | Date fields TBD |
| Firm card | Firm name, address snippet | `Firm_ID` → `Firm` |
| Contact (optional) | Linked contact name | `Contact_ID` TBD |
| Description | Full notes / body | `Description` / `Note` |
| Outcome (if completed) | Result text, completion timestamp | Status + outcome fields TBD |
| Owner | Responsible user display name | `Responsible_ID` TBD |

## Available actions

| Action | Behaviour | Gen |
|--------|-----------|-----|
| Back | SCR-002 or SCR-004 (based on stack) | — |
| Tap firm card | SCR-004 Firm detail | No |
| Tap contact | SCR-005 Contact detail | No |
| **Complete visit** | Open SCR-007 Log visit (complete mode) | Pre-fill from activity |
| **Edit** (if open) | SCR-007 Log visit (edit mode) — same form | `PUT` on save |
| Pull to refresh | Reload activity | `GET` |

**Hidden when status = completed/cancelled:** Complete / Edit (read-only except refresh).

**Not in MVP:** Delete activity, reassign owner, attach files.

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-002 My Day | Tap agenda row |
| **Incoming** | SCR-004 Firm detail | Tap recent activity |
| **Incoming** | SCR-007 Log visit | Back after save |
| **Outgoing** | SCR-004 Firm detail | Tap firm (customer hub) |
| **Outgoing** | SCR-005 Contact detail | Tap contact |
| **Outgoing** | SCR-007 Log visit | Complete / Edit |
| **Outgoing** | SCR-002 My Day | Back (operational hub) |
| **Outgoing** | SCR-012 Opportunity detail | Phase 2 — linked deal |

## Related ABRA business objects

| Object | Relationship | Operations |
|--------|--------------|------------|
| **Activity** (TBD) | Primary | `GET /activity/{id}?select=...&expand=Firm_ID(...)` |
| **Firm** | Related customer | Expand or secondary `GET` |
| **Contact** | Optional attendee | Expand or `Contact_ID` |
| **User / Employee** | Owner display | Expand `Responsible_ID` |

### Status values (working)

| UI status | Gen value TBD |
|-----------|---------------|
| Open | Planned / in progress |
| Completed | Done |
| Cancelled | Cancelled |

## Open design notes

- [ ] Map Gen activity types to icons (visit vs phone vs task)
- [ ] Whether “Complete” requires outcome notes (validation rule)
- [ ] Geolocation stamp on complete (MVP open question)

## Acceptance hints

- Activity ID from route only; 404 → friendly error
- Complete flow persists via Gen `PUT` with `validation=true`
- Completed activities cannot be edited unless Gen allows (mirror Gen rules)
