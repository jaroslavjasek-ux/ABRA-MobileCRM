# SCR-012: Opportunity detail (Phase 2 placeholder)

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-012 |
| **Business hub** | Reached from **Pipeline** (SCR-011) or **Firm** (SCR-004) |
| **Phase** | **Phase 2** — placeholder |
| **Status** | Placeholder specification |

## Purpose

Show one **sales opportunity**: stage, value, dates, firm, related activities, **quotes**, and **orders** — all Gen-sourced.

## User goals (Phase 2)

- Understand deal status before a visit
- Jump to firm, log activity against this deal, open quote/order

## Information displayed (planned)

| Zone | Content |
|------|---------|
| Header | Opportunity name, stage badge |
| Summary | Amount, probability, expected close, owner |
| Firm card | → SCR-004 |
| **Activities** | Linked customer interactions |
| **Quotes** (Phase 2) | Open sales offers — list → SCR-013 |
| **Orders** (Phase 2) | Open sales orders — list → SCR-014 |
| Commercial health | If Gen ties risk to deal (read-only) |

## Available actions (planned)

| Action | Target |
|--------|--------|
| Update stage | Gen rules |
| Log visit | SCR-007 with firm + opportunity pre-filled |
| New quote | SCR-013 (draft) |
| Back | SCR-011 or SCR-004 |

## Navigation paths

| Direction | Target |
|-----------|--------|
| **Incoming** | SCR-011 Pipeline |
| **Incoming** | SCR-004 Firm detail | Tap opportunity in pipeline snapshot |
| **Outgoing** | SCR-004, SCR-006, SCR-007, SCR-013, SCR-014 |

## Related ABRA business objects

| Object | Role |
|--------|------|
| **Sales opportunity** | Primary |
| **Firm**, **Activity**, **Sales offer**, **Sales order** | Related |

## MVP behaviour

Not implemented. Firm detail may show read-only snapshot linking here in Phase 2.
