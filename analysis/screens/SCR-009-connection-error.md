# SCR-009: Connection / service error

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-009 |
| **MVP capabilities** | M7 — Error and loading UX; online-only |
| **Persona** | Field sales representative |
| **Online required** | N/A (shown when not available) |

## Purpose

Communicate **loss of connectivity or ABRA Gen unavailability** clearly so the rep does not assume data was saved. Supports full-page blocking and complements an inline **connectivity banner** on other screens.

## Presentation variants

| Variant | When | Blocks UI |
|---------|------|-----------|
| **Full page** | Initial load failure (dashboard, firm detail) | Yes |
| **Banner** | Transient loss during session | No — sits on SCR-002, SCR-003, etc. |
| **Modal on save** | SCR-007 save failed — timeout | Dismiss back to form |

This document covers **full-page** SCR-009; banner behaviour is referenced from SCR-002.

## User goals

- Know the app is not connected to Gen (not “empty CRM”)
- Retry when back online
- Return to a safe screen without corrupting data

## Information displayed

| Zone | Content |
|------|---------|
| Icon | Offline / server error |
| Title | “No connection” or “Service unavailable” |
| Message | Check network; ABRA Gen may be down; **changes are not saved** |
| Last attempt (optional) | Timestamp of last failed request |
| Gen status (optional) | Distinguish DNS vs HTTP 503 |

## Available actions

| Action | Behaviour |
|--------|-----------|
| Retry | Ping Gen health / repeat failed request |
| Go to My Day | SCR-002 (if partial session still valid) |
| Sign out | SCR-001 if auth also invalid |

**On SCR-007:** Retry returns to form; Save remains disabled until online.

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-001 Login | Login cannot reach Gen |
| **Incoming** | SCR-002 My Day | Agenda load failed |
| **Incoming** | SCR-003, SCR-004, SCR-006 | Read failed |
| **Incoming** | SCR-007 | Save timeout |
| **Outgoing** | Previous screen | Retry success |
| **Outgoing** | SCR-002 My Day | Go to operational hub |
| **Outgoing** | SCR-003 Firm search | Go to customer hub (optional action) |
| **Outgoing** | SCR-001 Login | Sign out |

## Related ABRA business objects

| Object | Role |
|--------|------|
| *(none)* | No business reads/writes while blocked |
| **Gen OpenAPI** | Target of health check (`GET` lightweight resource or `/health` if exposed) |

### Health check (working)

Optional: `GET /firm?take=1&select=ID` with short timeout to prove Gen reachable.

## Open design notes

- [ ] Auto-retry with exponential backoff on banner only
- [ ] Distinguish device offline vs Gen 503 copy
- [ ] iOS / Android airplane mode detection

## Acceptance hints

- Writes never queued locally (ADR 0002)
- Retry does not create duplicate activities
- Full page vs banner rules documented per screen
