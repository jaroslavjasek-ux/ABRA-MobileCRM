# SCR-002: My Day

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-002 |
| **Business hub** | **My Day** — primary **operational** hub (domain model v0.2) |
| **MVP capabilities** | M4, M6 — Activities view; today’s visits and overdue |
| **Persona** | Field sales representative |
| **Journey** | UJ-001 — Morning agenda |
| **Online required** | Yes |
| **Phase** | MVP (activities); Phase 2 adds calendar rows in same hub |

## Purpose

Give the rep a **time-oriented starting point**: what to do now and what is late. This screen implements the **My Day** hub — not a separate Gen entity, but the operational home for **activities** (and later **calendar appointments**) sourced from ABRA Gen.

## User goals

- See today’s scheduled customer work at a glance
- Spot overdue items that need attention
- Open an activity or linked customer in one tap
- Start logging a new visit without searching first
- Switch to the **Firm** hub when the task is “which customer?” not “what time?”

## Information displayed

| Zone | Content | Gen source |
|------|---------|------------|
| Header | User greeting (first name), date | User / employee in Gen |
| Connectivity strip | Online / syncing / error (see SCR-009 banner) | — |
| **Today** section | Activities for current calendar day (assigned to user) | Activity |
| **Overdue** section | Open activities with due date before today | Activity |
| Empty states | Copy when no items today / no overdue | — |
| List row | Firm name, time, type, status badge, subject | Activity + Firm |
| Phase 2 placeholder | **Calendar** rows merged into same list (see SCR-002 Phase 2 note) | Calendar appointment |

### Activity list row (minimum fields)

| Label | Gen field (working) |
|-------|---------------------|
| Firm name | `Firm_ID` → Firm name |
| Start / due | `StartDate`, `DueDate` (TBD) |
| Type | Activity type enumeration |
| Status | Open / completed / cancelled |
| Subject | `Subject` or `Description` (TBD) |

### Phase 2 — unified agenda (same screen)

| Row type | Distinguisher | Action |
|----------|---------------|--------|
| CRM activity | Type icon “visit/task” | → SCR-006 |
| Calendar appointment | Type icon “calendar” | → appointment detail TBD or SCR-006 if linked |

## Available actions

| Action | Behaviour | Writes Gen? |
|--------|-----------|-------------|
| Tap activity row | Open SCR-006 Activity detail | No |
| Tap firm name on row | Open SCR-004 Firm detail (customer hub) | No |
| **Log visit** (FAB or header) | Open SCR-007 Log visit (create, firm optional) | No until save |
| **Customers** (tab or button) | Open SCR-003 Firm search (customer hub entry) | No |
| Pull to refresh | Re-run today + overdue queries | No |
| Profile / sign out (overflow) | Sign out → SCR-001 | No |
| Phase 2: **Pipeline** tab | → SCR-011 Pipeline | No |

**Blocked when offline:** Writes; reads show error state per ADR 0002 (no cached list as truth).

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-001 Login | After successful auth |
| **Incoming** | SCR-010 App loading | Cold start; default hub if org setting D-10 = My Day |
| **Incoming** | SCR-007, SCR-006 | Back after save / back stack |
| **Outgoing** | SCR-003 Firm search | Customers tab / search |
| **Outgoing** | SCR-006 Activity detail | Tap activity |
| **Outgoing** | SCR-004 Firm detail | Tap firm on row |
| **Outgoing** | SCR-007 Log visit | Log visit FAB |
| **Outgoing** | SCR-011 Pipeline | Phase 2 tab only |
| **Outgoing** | SCR-008 Session expired | 401 |
| **Outgoing** | SCR-009 Connection error | Load failure |

### App chrome (MVP)

| Element | Target |
|---------|--------|
| Bottom tab **My Day** | SCR-002 (this screen) |
| Bottom tab **Customers** | SCR-003 Firm search |
| Default landing | SCR-002 unless organisation chooses Firm-first (D-10) → then SCR-003 |

## Related ABRA business objects

| Object | Role |
|--------|------|
| **Activity** | Primary list source for MVP |
| **Firm** | Display name on rows |
| **Sales representative** | Filter “my” work |
| **Calendar appointment** | Phase 2 rows in same hub |

## Open design notes

- [ ] Maximum items per section before “View all”
- [ ] Collapsed “completed today” section
- [ ] Phase 2: visual distinction calendar vs CRM activity (P-08 linking)

## Acceptance hints

- Screen title and tab label are **My Day**, not “Dashboard” or “Activities”
- Empty and error states are distinct
- All list data refreshed from Gen; no offline replica
