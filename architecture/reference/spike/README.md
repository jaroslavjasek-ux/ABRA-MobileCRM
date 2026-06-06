# ABRA Gen API discovery spike

**Run date (UTC):** 2026-06-04  
**Server:** `http://localhost/demo` (from `config/config.yaml`)  
**Method:** `GET /api-docs/openapis` + per-controller OpenAPI (`?distrib=false`)

## Artefacts

| File | Description |
|------|-------------|
| [business-object-inventory.md](business-object-inventory.md) | All 521 controllers; CRM subset |
| [crm-object-validation.md](crm-object-validation.md) | Mobile CRM entities vs Gen |
| [gap-analysis.md](gap-analysis.md) | Gaps, risks, next validation steps |
| `openapis-index.json` | Full index export |
| `crm-controllers-detail.json` | CRM-related controller summaries |
| `discovery-meta.json` | Run metadata |
| `openapi/*.json` | Raw OpenAPI per controller (regenerable) |

## Re-run

```powershell
cd D:\ABRA\ABRA-MobileCRM
pip install pyyaml
python scripts/discover_abra_gen_openapi.py
```

Copy `config/config.example.yaml` → `config/config.yaml` for other environments.
