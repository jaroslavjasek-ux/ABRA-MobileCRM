# ABRA Mobile CRM

Mobile CRM for **field sales representatives**, integrated with **ABRA Gen** as the single source of truth for business data.

## Status

**Pre-implementation** — documentation and structure only. Application code is not started yet.

## Principles

| Principle | Meaning |
|-----------|---------|
| **ABRA Gen = source of truth** | Firms, contacts, activities, documents, and catalog data live in ABRA Gen. The app reads and writes via OpenAPI; it does not own authoritative business entities. |
| **MVP first** | Scope is defined in [`analysis/requirements/mvp-scope.md`](analysis/requirements/mvp-scope.md). Defer non-MVP features until after first release. |
| **Online only** | No offline-first sync or local master data. Connectivity to ABRA Gen is required for core workflows. |
| **Documentation first** | Analysis, architecture, and ADRs precede code. Changes to behaviour start in docs. |

## Repository layout

```text
analysis/          # Business analysis (personas, requirements, journeys)
architecture/      # Solution design, ABRA Gen integration, ADRs
implementation/    # Sprint plans, backlogs, acceptance criteria
docs/              # Project docs index, glossary, decision log
src/               # Application source (placeholder — Sprint 0 not started)
tests/             # Automated tests (placeholder — not started)
config/            # Non-secret configuration templates
scripts/           # Tooling (OpenAPI audit, codegen helpers — later)
.cursor/rules/     # Cursor AI project rules
```

## Documentation entry points

| Topic | Path |
|-------|------|
| Doc index | [`docs/README.md`](docs/README.md) |
| MVP scope | [`analysis/requirements/mvp-scope.md`](analysis/requirements/mvp-scope.md) |
| Architecture overview | [`architecture/README.md`](architecture/README.md) |
| ABRA Gen integration | [`architecture/abra-gen-integration.md`](architecture/abra-gen-integration.md) |
| Online architecture | [`architecture/online-architecture.md`](architecture/online-architecture.md) |
| Architecture decisions | [`docs/decisions/`](docs/decisions/) |
| Sprint 0 plan | [`implementation/sprint-0-plan.md`](implementation/sprint-0-plan.md) |
| Sprint 1 plan | [`implementation/sprint-1-plan.md`](implementation/sprint-1-plan.md) |

## Git setup

From the repository root:

```powershell
git init
git add .
git commit -m "chore: initial documentation-first project scaffold"
```

Optional remote:

```powershell
git remote add origin <your-remote-url>
git branch -M main
git push -u origin main
```

See [`docs/development/git-setup.md`](docs/development/git-setup.md) for branch naming and workflow notes.

## Related ABRA projects

Patterns for ABRA Gen OpenAPI usage are aligned with sibling repositories (e.g. Material Cutting). This project applies the same **Gen-as-truth** rule to CRM scenarios for mobile field sales.

## License

TBD — set before first public release.
