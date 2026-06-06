# ADR 0003: Documentation-first delivery

**Status:** Accepted  
**Date:** 2026-06-04

## Context

Greenfield mobile CRM with Gen integration benefits from shared understanding before framework choices harden wrong assumptions.

## Decision

**Documentation leads code:**

1. Analysis and architecture folders are populated and reviewed before `src/` implementation.
2. Scope and Gen mappings are updated in markdown **in the same change** as behavioural code (once coding starts).
3. Significant technical choices get an ADR before merge.

## Consequences

- **Positive:** Onboarding and AI-assisted development use stable context (`AGENTS.md`, `.cursor/rules/`).
- **Negative:** Short-term velocity trades for fewer reversals later.
- **Action:** Keep [`docs/README.md`](../README.md) index current when adding new doc areas.
