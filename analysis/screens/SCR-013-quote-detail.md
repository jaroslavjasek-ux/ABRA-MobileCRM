# SCR-013: Quote detail (Phase 2 placeholder)

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-013 |
| **Business name** | **Quote** (= sales offer in domain model) |
| **Phase** | **Phase 2** — placeholder |
| **Not a primary hub** | Accessed from SCR-004 Firm or SCR-012 Opportunity only |

## Purpose

View (and optionally edit draft) a **quotation / sales offer** document in Gen — lines, totals, status.

## User goals (Phase 2)

- Review open quote on site
- Add or change lines on draft per Gen rules

## Information displayed (planned)

| Zone | Content |
|------|---------|
| Header | Document number, status, date |
| Firm / opportunity | Links to SCR-004 / SCR-012 |
| Lines | Product, qty, price, delivery |
| Totals | Gen-calculated |

## Available actions (planned)

| Action | Notes |
|--------|-------|
| Add line | Product picker (secondary hub) |
| Save draft | Gen draft state only (P-05) |
| Confirm | Gen-only if not allowed on mobile |

## Navigation paths

| Direction | Target |
|-----------|--------|
| **Incoming** | SCR-004, SCR-012 |
| **Outgoing** | Back to origin; SCR-004 firm |

## Related ABRA business objects

| Object | Role |
|--------|------|
| **Sales offer** | Primary |
| **Document line**, **Product**, **Price** | Lines |
| **Firm**, **Sales opportunity** | Parents |

## MVP behaviour

**Not implemented.** SCR-004 shows a disabled/“coming Phase 2” **Quotes** section placeholder.
