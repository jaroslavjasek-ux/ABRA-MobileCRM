# Git setup and workflow

## Initialisation

Run from repository root (`ABRA-MobileCRM`):

```powershell
git init
git add .
git status
git commit -m "chore: initial documentation-first project scaffold"
```

## Recommended branches

| Branch | Use |
|--------|-----|
| `main` | Stable, reviewable docs and releases |
| `feature/<ticket>-<short-name>` | Scope or doc updates |
| `docs/<topic>` | Documentation-only changes |

## Commit message convention

```
<type>: <summary>

[optional body]
```

Types: `docs`, `analysis`, `architecture`, `chore`, `feat`, `fix`, `test` (use `feat`/`fix` when code exists).

Examples:

- `docs: add firm search user journey`
- `architecture: map MVP activities to Gen BOs`
- `chore: refresh OpenAPI reference snapshot`

## Remote

```powershell
git remote add origin https://github.com/<org>/ABRA-MobileCRM.git
git branch -M main
git push -u origin main
```

## What not to commit

See root [`.gitignore`](../../.gitignore): `.env`, keystores, local `config/local.yaml`, generated OpenAPI dumps (unless team policy says otherwise).

## Hooks

No project hooks yet. Add pre-commit when `src/` and formatters are introduced.
