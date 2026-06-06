# Tests (not started)

Test layout will mirror `src/` once code exists.

## Planned structure

```text
tests/
  unit/             # Mappers, query builders, validators
  integration/      # Gen sandbox API contract tests
  e2e/              # Mobile journey automation
```

## Principles

- **Integration tests** validate real Gen OpenAPI behaviour on a designated sandbox — not mocks for contract truth.
- **E2E** cover MVP journeys UJ-001–UJ-003.
- No tests that require committing secrets; use CI variables.

## MVP test goals

| Area | Goal |
|------|------|
| Firm search | `where` / `select` match OpenAPI |
| Firm detail | `expand` returns required nested data |
| Log visit | `POST`/`PUT` with `validation=true` succeeds on sandbox |
