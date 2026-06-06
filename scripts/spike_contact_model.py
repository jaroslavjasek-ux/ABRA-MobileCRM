#!/usr/bin/env python3
"""Contact model spike — firms, persons, firmperson links. JSON log only."""
from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "spikes" / "contact-model-results.json"


def load_config() -> dict:
    if yaml is None:
        raise RuntimeError("pip install pyyaml")
    return yaml.safe_load((ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))


def request(method: str, url: str, cfg: dict) -> tuple[int, Any, str]:
    auth = cfg["abra"]["auth"]
    headers = {"Accept": "application/json"}
    token = (auth.get("bearer_token") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        raw = base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
        headers["Authorization"] = f"Basic {raw}"
    req = Request(url, headers=headers, method=method)
    try:
        with urlopen(req, timeout=int(cfg["abra"].get("timeout_sec") or 60)) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else None, text[:2500]
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:2500]}
        return e.code, payload, text[:2500]


def main() -> int:
    cfg = load_config()
    base = cfg["abra"]["base_url"].rstrip("/")
    log: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "steps": [],
    }

    def step(name: str, path: str) -> tuple[int, Any]:
        url = f"{base}/{path.lstrip('/')}"
        status, payload, raw = request("GET", url, cfg)
        log["steps"].append(
            {
                "name": name,
                "url": url,
                "status": status,
                "response": payload,
                "raw_preview": raw if status >= 400 else None,
            }
        )
        print(f"{name}: {status}")
        return status, payload

    firm_sel = "ID,Name,Code,InitialFirmPerson_ID,ResponsibleUser_ID,Hidden"
    st, firms = step(
        "firms_list",
        "firms?" + urlencode({"take": 5, "select": firm_sel}),
    )
    firm_id = None
    if st == 200 and isinstance(firms, list) and firms:
        firm_id = firms[0].get("ID") or firms[0].get("id")

    if firm_id:
        step("firm_detail_full", f"firms/{firm_id}")
        step(
            "firm_detail_select",
            f"firms/{firm_id}?" + urlencode({"select": firm_sel}),
        )

    person_sel = (
        "ID,FirstName,LastName,FullName,DisplayName,Title,Suffix,Grade,"
        "Address_ID,ResponsibleUser_ID,ResponsibleRole_ID,Hidden,IsEmployee,IsOwned"
    )
    st, persons = step(
        "persons_list",
        "persons?" + urlencode({"take": 5, "select": person_sel}),
    )
    person_id = None
    if st == 200 and isinstance(persons, list) and persons:
        person_id = persons[0].get("ID") or persons[0].get("id")

    if person_id:
        step("person_detail_full", f"persons/{person_id}")
        step(
            "person_detail_select",
            f"persons/{person_id}?" + urlencode({"select": person_sel}),
        )
        addr_id = None
        for s in log["steps"]:
            if s["name"] == "person_detail_select" and s["status"] == 200:
                r = s["response"]
                if isinstance(r, dict):
                    addr_id = r.get("address_id") or r.get("Address_ID")
        if addr_id and addr_id not in ("__________", None, ""):
            step(
                "address_detail",
                f"addresses/{addr_id}?"
                + urlencode({"select": "ID,EMail,PhoneNumber1,PhoneNumber2,FaxNumber,City,Street"}),
            )
        step("person_xrelations", f"persons/{person_id}/xrelations")

    # Filter persons by firm (common patterns)
    if firm_id:
        for where in [
            f"Firm_ID eq '{firm_id}'",
            f"Parent_ID eq '{firm_id}'",
        ]:
            w = quote(where, safe="")
            step(
                f"persons_where_{where.split()[0]}",
                "persons?" + urlencode({"take": 3, "select": person_sel, "where": where}),
            )

    # Firm with most contacts heuristic: read firms with firmpersons count via detail on sample customers
    for fid in ["AAA1000000", "3000000101", "4000000101"]:
        step(f"firm_contacts_full_{fid}", f"firms/{fid}")

    step("person_eurocar_contact", "persons/6000000101")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
