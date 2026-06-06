# ADR 0001: ABRA Gen as sole source of truth

**Status:** Accepted  
**Date:** 2026-06-04

## Context

Field sales CRM needs customer, contact, activity, and document data. Duplicate master data in a mobile app or side database causes sync conflicts and reporting drift.

## Decision

**ABRA Gen** is the only system of record. The Mobile CRM:

- Reads and writes business entities **only** through ABRA Gen OpenAPI (or a thin BFF that proxies Gen without persisting authoritative copies).
- May cache responses **transiently** for UX (e.g. in-memory, short TTL) but must not treat cache or local storage as truth.
- Stores at most **non-business** data locally (e.g. auth tokens, UI preferences) with explicit documentation.

## Consequences

- **Positive:** Single reporting and permission model in Gen; no reconciliation layer.
- **Positive:** Aligns with other ABRA integrations in the organisation.
- **Negative:** UX depends on Gen availability and API latency (see ADR 0002).
- **Action:** Map each MVP feature to concrete Gen BOs in [`architecture/abra-gen-integration.md`](../../architecture/abra-gen-integration.md).
