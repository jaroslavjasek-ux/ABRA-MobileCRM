# SCR-014: Order detail (Phase 2 placeholder)

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-014 |
| **Business name** | **Order** (= sales order in domain model) |
| **Phase** | **Phase 2** — placeholder |
| **Not a primary hub** | Accessed from SCR-004 Firm or SCR-012 Opportunity only |

## Purpose

View (and optionally edit draft) a **sales order** in Gen — lines, totals, status.

## User goals (Phase 2)

- Check open order status at customer
- Draft order lines on visit when policy allows

## Information displayed (planned)

| Zone | Content |
|------|---------|
| Header | Order number, status, date |
| Firm / opportunity | Links to SCR-004 / SCR-012 |
| Lines | Product, qty, price, delivery |
| Totals | Gen-calculated |

## Available actions (planned)

| Action | Notes |
|--------|-------|
| Add line | Product picker |
| Save draft | Draft state only |
| Confirm / post | Gen workflow |

## Navigation paths

| Direction | Target |
|-----------|--------|
| **Incoming** | SCR-004, SCR-012 |
| **Outgoing** | Back to origin |

## Related ABRA business objects

| Object | Role |
|--------|------|
| **Sales order** | Primary |
| **Document line**, **Product**, **Price**, **Stock availability** | Lines / checks |
| **Firm**, **Sales opportunity** | Parents |

## MVP behaviour

**Not implemented.** SCR-004 shows a disabled/“coming Phase 2” **Orders** section placeholder.
