# SCR-005: Contact detail

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-005 |
| **Business hub** | **Firm** (secondary — contact under customer) |
| **MVP capabilities** | M3 — View firm-related contacts |
| **Persona** | Field sales representative |
| **Journey** | UJ-002 — Identify contact before visit |
| **Online required** | Yes |

## Purpose

Show **read-only detail** for one contact person linked to a firm so the rep can call the right person and confirm role/title before or during a visit.

## User goals

- Verify contact identity and role
- Reach the contact by phone or email immediately
- Return to firm context without losing place

## Information displayed

| Zone | Content | Gen source |
|------|---------|------------|
| Header | Contact full name | `Contact` |
| Firm link | Parent firm name (tappable) | `Firm` via `Firm_ID` |
| Role | Job title / department | Contact fields TBD |
| Phones | Mobile, landline (labeled) | `Phone`, `Mobile`, etc. |
| Email | Primary email | `Email` TBD |
| Notes | Short note field if exists in Gen | `Note` / `Description` TBD |
| Metadata | Last modified (optional) | Gen audit fields TBD |

**Not displayed in MVP:** Edit history, social links, create/edit forms.

## Available actions

| Action | Behaviour | Gen |
|--------|-----------|-----|
| Back | Return to SCR-004 Firm detail | — |
| Tap firm name | Navigate to SCR-004 for linked `Firm_ID` | No |
| Tap phone | OS phone dialer | — |
| Tap email | OS mail composer | — |
| **Log visit** (optional header) | SCR-007 with `Firm_ID` + contact reference if Gen supports | No until save |
| Pull to refresh | Reload contact | `GET` |

**Not in MVP:** Edit contact, delete, add new contact.

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-004 Firm detail | Tap contact row |
| **Outgoing** | SCR-004 Firm detail | Back |
| **Outgoing** | SCR-007 Log visit | Log visit with firm context |
| **Outgoing** | SCR-002 My Day | Tab (optional) |
| **Outgoing** | SCR-009 Connection error | Load failure |

## Related ABRA business objects

| Object | Relationship | Operations |
|--------|--------------|------------|
| **Contact** (TBD BO name) | Primary record | `GET /contact/{id}?select=...` |
| **Firm** | Parent reference | `Firm_ID` on contact; optional `GET` or embedded expand |

### Linking convention (working)

| Field on Contact | Points to |
|------------------|-----------|
| `Firm_ID` | `Firm.ID` |

Alternative: contacts only via `Firm` expand — then detail uses embedded ID from list.

## Open design notes

- [ ] Confirm Contact BO name in customer Gen (Person, FirmContact, etc.)
- [ ] Photo / avatar from Gen attachments (out of MVP?)
- [ ] Pass `Contact_ID` into SCR-007 for activity attendee field

## Acceptance hints

- Read-only; no local persistence of contact as master
- Missing phone shows “—” not hidden failure
- Permission denied shows section error, not crash
