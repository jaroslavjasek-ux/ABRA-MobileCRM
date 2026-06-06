#!/usr/bin/env python3
"""
ABRA Gen OpenAPI discovery spike for Mobile CRM.
Enumerates business objects from api-docs/openapis and produces spike artefacts.
No application code — discovery only.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "analysis" / "domain" / "gen-business-object-mapping.md"

# Mobile CRM entities → search terms for matching discovered controller names
ENTITY_MATCH_TERMS: dict[str, list[str]] = {
    "Firm": ["firm", "firms"],
    "Firm address": ["address", "deliveryplace", "firmaddress"],
    "Firm commercial status": ["firm", "pmstate"],
    "Contact": ["contact", "person", "firmperson", "businesspartnercontact"],
    "Activity": ["crmactivity", "activity", "task", "event"],
    "Activity type / status": ["crmactivitytype", "crmactivityarea", "activitytype"],
    "Calendar appointment": ["calendar", "appointment", "meeting", "schedule"],
    "Sales representative": ["user", "employee", "worker", "person"],
    "Commercial health signal": ["firm", "receivable", "credit", "balance", "limit"],
    "Pipeline snapshot": ["opportunity", "crmopportunity", "deal"],
    "Sales opportunity": ["opportunity", "crmopportunity", "deal", "pipeline"],
    "Sales offer (Quote)": ["receivedorder", "issuedorder", "offer", "quote", "bid"],
    "Sales order (Order)": ["receivedorder", "issuedorder", "order"],
    "Document line": [],  # nested — matched via parent docs
    "Product": ["storecard", "product", "article"],
    "Price": ["pricelist", "price"],
    "Stock availability": ["stock", "storecard", "warehouse"],
    "Receivable position": ["receivable", "invoice", "balance", "claim"],
    "My Day": [],
    "Authentication session": ["user", "auth"],
}


def load_config() -> dict[str, Any]:
    for name in ("config.yaml", "config.local.yaml"):
        path = ROOT / "config" / name
        if path.exists():
            if yaml is None:
                raise RuntimeError("PyYAML required: pip install pyyaml")
            with path.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError("No config/config.yaml — copy from config.example.yaml")


def auth_headers(cfg: dict[str, Any]) -> dict[str, str]:
    import base64

    auth = cfg["abra"].get("auth") or {}
    headers = {"Accept": "application/json"}
    token = (auth.get("bearer_token") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
        return headers
    user = auth.get("username") or ""
    password = auth.get("password") or ""
    if user:
        raw = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
        headers["Authorization"] = f"Basic {raw}"
    api_key = (auth.get("api_key") or "").strip()
    if api_key:
        headers[auth.get("api_key_header") or "X-Api-Key"] = api_key
    return headers


def fetch_json(url: str, cfg: dict[str, Any]) -> Any:
    req = Request(url, headers=auth_headers(cfg))
    timeout = int(cfg["abra"].get("timeout_sec") or 60)
    verify = cfg["abra"].get("verify_ssl", True)
    ctx = None
    if not verify:
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_base(base_url: str) -> str:
    return base_url.rstrip("/")


def parse_openapis_index(data: Any) -> list[dict[str, str]]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "items" in data:
        items = data["items"]
    else:
        raise ValueError(f"Unexpected openapis index shape: {type(data)}")
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name or name == "openapi":
            continue
        out.append(
            {
                "name": name,
                "description": (item.get("description") or "").strip(),
                "boclsid": (item.get("boclsid") or "").strip(),
                "ref": (item.get("$ref") or item.get("ref") or "").strip(),
            }
        )
    return sorted(out, key=lambda x: x["name"].lower())


def is_crm_related(name: str, description: str, keywords: list[str]) -> bool:
    blob = f"{name} {description}".lower()
    return any(k in blob for k in keywords)


def summarize_openapi_paths(spec: dict[str, Any]) -> dict[str, Any]:
    paths = spec.get("paths") or {}
    collection_get = False
    collection_post = False
    by_id_get = False
    by_id_put = False
    by_id_delete = False
    deprecated_paths: list[str] = []
    root_path = ""

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        mlower = {k.lower(): k for k in methods if k not in ("parameters", "servers")}
        if re.fullmatch(r"^/[^/]+$", path) or path.endswith("s") and path.count("/") == 1:
            root_path = root_path or path
        if "get" in mlower and path.count("/") == 1:
            collection_get = True
        if "post" in mlower and path.count("/") == 1:
            collection_post = True
        if "{id}" in path or "{id1}" in path:
            if "get" in mlower:
                by_id_get = True
            if "put" in mlower:
                by_id_put = True
            if "delete" in mlower:
                by_id_delete = True
        for meth, spec_m in methods.items():
            if isinstance(spec_m, dict) and spec_m.get("deprecated"):
                deprecated_paths.append(f"{meth.upper()} {path}")

    schema_name = None
    for p in paths:
        seg = p.strip("/").split("/")[0] if p else ""
        if seg:
            schema_name = seg.rstrip("s")  # heuristic
            break

    return {
        "root_path": root_path,
        "schema_guess": schema_name,
        "collection_get": collection_get,
        "collection_post": collection_post,
        "by_id_get": by_id_get,
        "by_id_put": by_id_put,
        "by_id_delete": by_id_delete,
        "path_count": len(paths),
        "deprecated_count": len(deprecated_paths),
        "deprecated_sample": deprecated_paths[:5],
    }


def infer_crud(summary: dict[str, Any]) -> str:
    parts = []
    if summary.get("collection_get") or summary.get("by_id_get"):
        parts.append("R")
    if summary.get("collection_post"):
        parts.append("C")
    if summary.get("by_id_put"):
        parts.append("U")
    if summary.get("by_id_delete"):
        parts.append("D")
    return "".join(parts) if parts else "—"


def match_entities(controller_name: str, description: str) -> list[str]:
    blob = f"{controller_name} {description}".lower()
    matched: list[str] = []
    for entity, terms in ENTITY_MATCH_TERMS.items():
        if not terms:
            continue
        if any(t in blob for t in terms):
            matched.append(entity)
    return matched


def best_candidates_for_entity(
    entity: str, controllers: list[dict[str, Any]], keywords: list[str]
) -> list[str]:
    terms = ENTITY_MATCH_TERMS.get(entity, [])
    if not terms:
        return []
    hits: list[tuple[int, str]] = []
    for c in controllers:
        name = c["name"].lower()
        desc = (c.get("description") or "").lower()
        score = sum(2 if t in name else (1 if t in desc else 0) for t in terms)
        if score > 0:
            hits.append((score, c["name"]))
    hits.sort(key=lambda x: (-x[0], x[1]))
    return [h[1] for h in hits[:5]]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    cfg = load_config()
    base = normalize_base(cfg["abra"]["base_url"])
    keywords = cfg.get("discovery", {}).get("crm_keywords") or []
    out_dir = ROOT / cfg.get("discovery", {}).get("output_dir", "architecture/reference/spike")
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "index_url": f"{base}/api-docs/openapis",
    }

    print(f"Fetching {meta['index_url']} ...")
    try:
        index_raw = fetch_json(meta["index_url"], cfg)
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        write_json(out_dir / "discovery-error.json", {"meta": meta, "error": str(e)})
        return 1

    controllers = parse_openapis_index(index_raw)
    meta["total_controllers"] = len(controllers)
    write_json(out_dir / "openapis-index.json", {"meta": meta, "controllers": controllers})

    crm_controllers = [
        c for c in controllers if is_crm_related(c["name"], c["description"], keywords)
    ]
    meta["crm_controller_count"] = len(crm_controllers)

    # Fetch OpenAPI summary for CRM-related controllers (cap to avoid long run)
    max_detail = int(cfg.get("discovery", {}).get("max_crm_detail_fetch") or 80)
    detailed: list[dict[str, Any]] = []
    for i, c in enumerate(crm_controllers[:max_detail]):
        ref = c["ref"]
        if not ref:
            ref = f"{base}/api-docs/openapi/{c['name']}?distrib=false"
        if "distrib=false" not in ref:
            ref = ref + ("&" if "?" in ref else "?") + "distrib=false"
        print(f"  [{i+1}/{min(len(crm_controllers), max_detail)}] {c['name']}")
        entry = {**c, "openapi_url": ref, "fetch_error": None}
        try:
            spec = fetch_json(ref, cfg)
            summary = summarize_openapi_paths(spec)
            entry["summary"] = summary
            entry["inferred_crud"] = infer_crud(summary)
            entry["matched_entities"] = match_entities(c["name"], c["description"])
            write_json(out_dir / "openapi" / f"{c['name']}.json", spec)
        except (HTTPError, URLError, TimeoutError) as e:
            entry["fetch_error"] = str(e)
            entry["summary"] = {}
            entry["inferred_crud"] = "?"
            entry["matched_entities"] = match_entities(c["name"], c["description"])
        detailed.append(entry)

    write_json(
        out_dir / "crm-controllers-detail.json",
        {"meta": meta, "controllers": detailed},
    )

    # Also fetch firm + crmactivity if present (MVP P0) even if keyword miss
    p0_names = ["firms", "firm", "crmactivities", "crmactivity", "contacts", "contact"]
    for pname in p0_names:
        if any(c["name"].lower() == pname for c in detailed):
            continue
        hit = next((c for c in controllers if c["name"].lower() == pname), None)
        if not hit:
            continue
        print(f"  [P0 extra] {hit['name']}")
        ref = hit["ref"] or f"{base}/api-docs/openapi/{hit['name']}?distrib=false"
        if "distrib=false" not in ref:
            ref = ref + ("&" if "?" in ref else "?") + "distrib=false"
        entry = {**hit, "openapi_url": ref, "fetch_error": None, "p0_extra": True}
        try:
            spec = fetch_json(ref, cfg)
            entry["summary"] = summarize_openapi_paths(spec)
            entry["inferred_crud"] = infer_crud(entry["summary"])
            entry["matched_entities"] = match_entities(hit["name"], hit["description"])
        except (HTTPError, URLError, TimeoutError) as e:
            entry["fetch_error"] = str(e)
        if not any(d["name"] == hit["name"] for d in detailed):
            detailed.append(entry)

    write_json(out_dir / "discovery-meta.json", meta)
    print(f"\nDone: {len(controllers)} controllers, {len(crm_controllers)} CRM-related, {len(detailed)} detailed.")
    print(f"Output: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
