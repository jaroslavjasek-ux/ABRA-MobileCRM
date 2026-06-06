# ADR 0004: Thin ABRA Adapter for Gen integration

**Status:** Proposed  
**Date:** 2026-06-04  
**Study:** [`architecture/abra-integration-decision-study.md`](../../architecture/abra-integration-decision-study.md)

## Context

Integration spikes against localhost DEMO validated `currentuser`, `securityusers`, `employees`, `persons`, `firms`, and `crmactivities`. Findings show non-trivial identity mapping, validate-then-commit writes, `firmperson` assembly via full firm reads, invalid `select` tokens per BO, and mixed activity ownership fields.

The mobile MVP has six data-heavy screens (My Day, firm search/detail, contact/activity detail, log visit) that would each reimplement the same Gen rules if the client called OpenAPI directly.

## Decision

For **MVP** and **Phase 2**, use a **thin ABRA Adapter** between UI and Gen:

- **MVP:** Implement as a **client-side integration module** with stable methods (`bootstrapSession`, `getMyDay`, `getFirmDetail`, `saveActivity`, etc.). Gen remains the only source of truth; the adapter maps projections and orchestrates `?validation=true` only.
- **Phase 2:** Extend the same boundary for pipeline, quotes, and orders; add per-deployment policy config.

**Packaging (ADR 0005):** MVP implements this boundary as a **server-hosted ASP.NET Core service** exposing [Mobile CRM API v1](../../architecture/mobile-crm-api-v1.md). Logical role unchanged; physical deployment is co-located with Gen per [Solution Architecture v1](../../architecture/solution-architecture-v1.md).

We **reject** direct per-screen OpenAPI consumption as the primary pattern because spike evidence concentrates complexity in shared policies (writes, contacts, identity, safe `select` lists), not in individual UI layouts.

## Consequences

**Positive**

- Single place for validate-then-commit, `repUserId`, activity ownership OR-filters, and `firmperson` parsing.
- Screens depend on stable view models; easier testing with mocked adapter.
- Customer-specific Gen differences isolated in adapter configuration.

**Negative**

- Up-front adapter design before all screens are wired.
- Adapter must not cache data as offline truth (ADR 0002).
- Total Gen HTTP traffic unchanged unless adapter dedupes (e.g. firm names on My Day).

**Follow-ups**

- Close spike open questions OQ-SR-04, OQ-LC-04 (My Day date `where`) before locking `getMyDay`.
- Document allowlisted `select` per BO in adapter reference.
- Revisit server BFF if mobile must not hold Gen credentials.
