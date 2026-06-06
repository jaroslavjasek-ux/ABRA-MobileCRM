# Persona: Field sales representative

## Summary

**Eva** — regional sales rep, 80% time on the road, uses phone for customer visits and quick lookups. Expects consumer-grade mobile UX but must trust that data matches the office ERP.

## Goals

- Find customer (firm) and contacts before a visit
- See open activities, orders, and receivables context
- Log visit outcome and next step in one session
- Create or advance a sales document when deal is ready

## Frustrations

- Slow or confusing ERP web UI on phone
- Uncertainty whether mobile changes “count” in the system
- Lost connectivity without knowing if data saved

## Constraints (product)

- **Online-only MVP:** must see clear error when offline; no false “saved” (ADR 0002).
- **Gen truth:** will not maintain a personal spreadsheet as parallel CRM.

## Devices & context

- Smartphone, one hand, outdoor brightness, intermittent 4G
- Short sessions (2–10 minutes) between driving and meetings

## Success metrics (MVP)

- Time to open firm detail from search &lt; 5 s on good network (target, validate in NFR)
- Visit logged in Gen visible to back office within one API round-trip
- Zero duplicate firm records created via mobile (validation rules TBD)
