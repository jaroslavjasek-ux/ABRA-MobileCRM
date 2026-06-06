# Architectural principles

## 1. Single source of truth

All business state lives in **ABRA Gen**. Mobile app and optional BFF are **views and commands**, not masters.

## 2. Online-first (MVP)

Design for continuous connectivity. Optimise for clear failure modes, not for offline replication.

## 3. API contract driven

Integrate via **published OpenAPI**. Field names and query patterns (`select`, `where`, `expand`, `validation=true`) match Gen documentation and verified behaviour on target version.

## 4. Thin edges

- **Mobile:** presentation, validation UX, navigation.
- **BFF (if any):** auth termination, response shaping, correlation — no long-lived business entity store.

## 5. Security in depth

Identity, authorization, and row-level rules enforced by **Gen permissions**. Mobile does not bypass server rules.

## 6. Evolvable MVP

Structure modules by **user journey** and **Gen resource**, not by premature microservices.

## 7. Documentation parity

Architecture changes without updating `abra-gen-integration.md` and relevant ADRs are incomplete.
