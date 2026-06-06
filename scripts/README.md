# Scripts

Developer and CI tooling for Gen discovery and validation spikes.

## Scripts

| Script | Purpose |
|--------|---------|
| [`discover_abra_gen_openapi.py`](discover_abra_gen_openapi.py) | Enumerate Gen controllers; export spike JSON |
| [`spike_crmactivities_lifecycle.py`](spike_crmactivities_lifecycle.py) | Live `crmactivities` lifecycle → `analysis/spikes/crmactivities-lifecycle-results.json` |
| [`spike_contact_model.py`](spike_contact_model.py) | Contact model spike → `analysis/spikes/contact-model-results.json` |
| [`spike_sales_representative.py`](spike_sales_representative.py) | Sales rep identity spike → `analysis/spikes/sales-representative-results.json` |
| [`generate_spike_markdown.py`](generate_spike_markdown.py) | Helper / future regen of spike markdown |

**Spike outputs:** [`../architecture/reference/spike/`](../architecture/reference/spike/)

```powershell
pip install pyyaml
python scripts/discover_abra_gen_openapi.py
```

Requires `config/config.yaml` (copy from `config/config.example.yaml`).

Scripts must not embed credentials; read from environment or local gitignored config.
