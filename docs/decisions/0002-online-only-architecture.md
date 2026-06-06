# ADR 0002: Online-only architecture

**Status:** Accepted  
**Date:** 2026-06-04

## Context

Mobile apps often support offline queues and later sync. That requires conflict rules, idempotency, and a local entity store — contradicting ADR 0001 for MVP timeline and team size.

## Decision

Adopt an **online-only** architecture for MVP and initial releases:

- Core user journeys (search firm, view detail, log activity, create document) **require** connectivity to ABRA Gen (directly or via BFF).
- Show clear **unavailable** states when the network or Gen is unreachable; do not silently queue business writes locally as if they succeeded.
- Defer offline drafts, background sync, and “work queue” patterns to a future ADR if product requires them.

## Consequences

- **Positive:** Simpler security, testing, and data model; faster MVP.
- **Negative:** Poor connectivity areas need user expectation management.
- **Action:** Document connectivity assumptions in [`analysis/requirements/non-functional.md`](../../analysis/requirements/non-functional.md).
