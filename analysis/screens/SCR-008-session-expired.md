# SCR-008: Session expired

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-008 |
| **MVP capabilities** | M1, M7 — Auth recovery; error UX |
| **Persona** | Field sales representative |
| **Online required** | Yes (to re-authenticate) |

## Purpose

Interrupt the user when the **API token or session is no longer valid** (expired, revoked, or 401 from Gen/IdP) and guide them to sign in again without implying data was saved.

## User goals

- Understand that they need to sign in again (not a generic crash)
- Return to login without losing awareness of unsaved work (see below)
- Re-authenticate and resume work when possible

## Information displayed

| Zone | Content |
|------|---------|
| Icon / illustration | Session timeout visual |
| Title | “Session expired” (localized) |
| Message | Explain re-login required; unsaved form data cannot be submitted |
| Detail (optional) | Error code for support (non-PII) |

**If shown over SCR-007 with dirty form:** Explicit warning that **visit was not saved** to Gen.

## Available actions

| Action | Behaviour |
|--------|-----------|
| Sign in again | Clear tokens → SCR-001 Login |
| Contact support (link) | Mailto or intranet URL | Organisational |

**Not offered:** Continue without login, offline mode, or “save locally”.

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | Any authenticated screen | 401 / 403 token expiry |
| **Incoming** | SCR-007 Log visit | Save returned 401 |
| **Outgoing** | SCR-001 Login | Sign in again |
| **Outgoing** | SCR-010 App loading | After login, restore intended route TBD |

### Post-login redirect (working)

| Last screen | Return to |
|-------------|-----------|
| SCR-007 dirty | SCR-007 with form **cleared** (no local draft — ADR 0002) or SCR-004 |
| Other | SCR-002 My Day (or SCR-003 if Firm-first) |

## Related ABRA business objects

| Object | Role |
|--------|------|
| *(none)* | No CRM read/write on this screen |
| **Gen API session** | Invalidated; must re-issue token via SCR-001 flow |
| **IdP session** | May require full credential login |

## Open design notes

- [ ] Refresh token silent renew vs full screen
- [ ] Background 401 handling without losing navigation stack

## Acceptance hints

- No CRM data displayed except warning context
- Never store unsaved activity locally as pending sync
- Sign in again always routes through SCR-001
