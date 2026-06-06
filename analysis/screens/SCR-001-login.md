# SCR-001: Login

| Attribute | Value |
|-----------|-------|
| **Screen ID** | SCR-001 |
| **MVP capabilities** | M1 — Authenticate user |
| **Persona** | Field sales representative |
| **Online required** | Yes (initial token exchange) |

## Purpose

Establish an authenticated session that grants the mobile app permission to call **ABRA Gen OpenAPI** on behalf of the user. This is the gate for all CRM data; no business data is shown before successful login.

## User goals

- Sign in quickly with company credentials
- Understand if login failed (wrong password, no Gen access, network down)
- Reach **My Day** (operational hub) without repeating login on every app open (session persistence TBD)

## Information displayed

| Zone | Content | Source |
|------|---------|--------|
| Branding | App name, optional company logo | Local assets |
| Status | Loading indicator during auth | Client state |
| Error area | Message for failed login (generic + support hint) | IdP / Gen / network response |
| Environment hint (dev only) | Target Gen connection label | `config` (non-prod) |

**Not displayed:** Firm lists, cached CRM data, or “continue offline” option (ADR 0002).

## Available actions

| Action | Behaviour | Gen / IdP |
|--------|-----------|-----------|
| Sign in | Submit credentials → obtain tokens → validate Gen reachability | IdP + Gen auth |
| Forgot password | Open company password reset URL (external browser) | IdP (organisational) |
| Retry after error | Clear error, re-enable form | Same as sign in |

**Disabled when:** No network (show connection guidance, link to SCR-009 pattern).

## Navigation paths

| Direction | Target | Condition |
|-----------|--------|-----------|
| **Incoming** | SCR-010 App loading | No valid refresh token / first launch |
| **Incoming** | SCR-008 Session expired | Prior session invalid |
| **Outgoing** | SCR-002 My Day | Login + Gen token OK (or SCR-003 if D-10 Firm-first) |
| **Outgoing** | SCR-009 Connection error | Network or Gen unreachable during login |
| **Outgoing** | SCR-010 App loading | Re-check session after background (optional) |

**Back:** Not applicable as root auth screen (no back to unauthenticated CRM).

## Related ABRA business objects

| Object | Role on this screen | Operations |
|--------|---------------------|------------|
| *(none for CRM entities)* | Login does not read Firm/Contact/Activity | — |
| **Gen API session** | Bearer or documented token used on subsequent calls | Token issue / refresh TBD in auth ADR |
| **Gen user context** | Implicit via token (permissions for Firm, Activity) | Optional lightweight `GET` health e.g. user profile BO TBD |

## Open design notes

- [ ] IdP: Entra ID, AD FS, or Gen-native credentials
- [ ] Biometric unlock for stored refresh token (Phase 1.1?)
- [ ] Multi-factor authentication flow

## Acceptance hints

- Successful login lands on SCR-002 within NFR targets
- Failed Gen permission shows actionable message (contact administrator)
- No Firm/Activity data written to local DB on this screen
