# ADR 0005: Solution Architecture v1 (MVP stack)

**Status:** Accepted (amended)  
**Date:** 2026-06-04  
**Amended:** 2026-06-04 — frontend per browser-only product constraint  
**Specification:** [`architecture/solution-architecture-v1.md`](../../architecture/solution-architecture-v1.md) (v1.1.0)  
**Frontend rationale:** [ADR 0006 v2 — Frontend technology](0006-frontend-technology.md)

## Context

MVP requires a smallest maintainable system covering SCR-001–010, online-only operation (ADR 0002), Gen as source of truth (ADR 0001), a thin adapter (ADR 0004 Proposed), and the normative [Mobile CRM API v1](../../architecture/mobile-crm-api-v1.md). Stack choices were open in [`architecture/mvp/solution-overview.md`](../../architecture/mvp/solution-overview.md).

Validated spikes show non-trivial Gen integration (validate-then-commit, `firmperson` assembly, ownership OR filters) that must not be duplicated in UI code.

**Product constraint (2026-06-04):** ABRA Mobile CRM is a **browser-based web application**. Native mobile apps are out of scope. See [ADR 0006 v2](0006-frontend-technology.md).

## Decision

Adopt **Solution Architecture v1.1** with these MVP choices:

| Area | Decision |
|------|----------|
| Frontend | **React 18+ TypeScript SPA (Vite)** — mobile browser; optional PWA install enhancement only |
| Adapter | **ASP.NET Core 8** Web API — implements [mobile-crm-api-v1.md](../../architecture/mobile-crm-api-v1.md) and [adapter mapping](../../architecture/mobile-crm-api-v1-adapter-mapping.md) (**unchanged**) |
| Adapter packaging | **Server-hosted** thin BFF (refines ADR 0004 in-app minimum; aligns with REST contract) |
| Authentication | Browser **Bearer session token** (or httpOnly cookie same-origin) to BFF after `POST /session`; BFF holds Gen auth context |
| Deployment | **Per-customer**: Gen + adapter on customer network; **static web UI** co-hosted or reverse-proxied with adapter; users on VPN/mobile browser |
| Logging | **Serilog** structured JSON on adapter; browser **minimal** client logging + optional error reporting (e.g. Sentry) |
| Monitoring | **`/health`** + HTTP metrics on adapter; optional Application Insights / OpenTelemetry |

No application code in this ADR — documentation and planned `src/` layout only.

### Amendment note (supersedes original frontend row)

Original ADR 0005 (2026-06-04) selected **.NET MAUI 8**. That is **withdrawn** because native mobile is out of scope. Adapter, API contract, auth model, and per-customer adapter deployment **remain**. Only the **client runtime** changes to React SPA.

## Consequences

**Positive**

- Frontend isolated from Gen drift via stable API contract.
- Gen credentials remain off the browser; BFF holds Gen context after login.
- Static web deploy minimises customer update complexity.
- Operational baseline (health, correlation, structured logs) on adapter without heavy APM mandate.

**Negative**

- TypeScript + C# split (mitigated by OpenAPI codegen).
- Web session storage requires explicit security review (not OS keystore).
- Session store on adapter still required before horizontal scale (Redis later).

**Follow-ups**

- Accept or amend [ADR 0004](0004-thin-abra-adapter.md) to reference server-hosted adapter.
- Close spike OQs OQ-SR-04, OQ-LC-04, OQ-LC-01 before SCR-002 / SCR-007 release.
- Publish OpenAPI for `mobile-crm-api-v1` and generate TypeScript client.
