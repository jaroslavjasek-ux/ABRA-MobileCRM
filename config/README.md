# Configuration templates

Non-secret configuration templates for environments. Copy to `local.yaml` (gitignored) for developer machines.

## Planned files (when implementation starts)

| File | Purpose |
|------|---------|
| `config.example.yaml` | Gen base URL, connection name, feature flags |
| `.env.example` | Environment variable names for CI and local |

## Example shape (illustrative)

```yaml
# config.example.yaml — do not put secrets in committed files
abra:
  base_url: "https://gen.example.local/demo"
  connection: "demo"
  # token via ABRA_BEARER_TOKEN env
app:
  environment: development
```

See [`../architecture/abra-gen-integration.md`](../architecture/abra-gen-integration.md) for integration rules.
