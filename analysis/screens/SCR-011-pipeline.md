# SCR-011: Pipeline (Phase 2 placeholder)

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-011 |
| **Business hub** | **Pipeline** — primary **commercial** hub (domain model v0.2) |
| **Phase** | **Phase 2** — not in MVP build |
| **Status** | Placeholder specification |

## Purpose

List and filter **sales opportunities** (open deals) for the rep — the commercial counterpart to **My Day** (time) and **Firm** (relationship). All data from ABRA Gen; no shadow pipeline.

## User goals (Phase 2)

- See my open deals by stage
- Open an opportunity and related firm, activities, quotes, orders
- Update stage where Gen permits

## Information displayed (planned)

| Zone | Content |
|------|---------|
| Filters | My deals / team (per Gen permissions), stage, sort |
| List row | Opportunity name, firm, stage, amount, expected close |
| Empty | No open opportunities |

## Available actions (planned)

| Action | Target |
|--------|--------|
| Tap row | SCR-012 Opportunity detail |
| Pull to refresh | Reload from Gen |
| Tab **Customers** | SCR-003 |
| Tab **My Day** | SCR-002 |

## Navigation paths

| Direction | Target |
|-----------|--------|
| **Incoming** | Bottom tab Pipeline (Phase 2) |
| **Incoming** | SCR-004 Firm detail | “View pipeline” on firm (optional shortcut) |
| **Outgoing** | SCR-012 Opportunity detail |
| **Outgoing** | SCR-004 Firm detail | Tap firm on row |
| **Outgoing** | SCR-002 My Day | Tab |

## Related ABRA business objects

| Object | Role |
|--------|------|
| **Sales opportunity** | Primary list |
| **Firm** | Display on row |
| **Sales representative** | Ownership filter |

## MVP behaviour

Screen **not implemented** in MVP. Optional **pipeline snapshot** on SCR-004 Firm detail only (read-only summary).
