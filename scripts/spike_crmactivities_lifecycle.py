#!/usr/bin/env python3
"""Live lifecycle spike for crmactivities — writes JSON log only."""
from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "spikes" / "crmactivities-lifecycle-results.json"


def load_config() -> dict:
    path = ROOT / "config" / "config.yaml"
    if yaml is None:
        raise RuntimeError("pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def request(
    method: str,
    url: str,
    cfg: dict,
    body: dict | None = None,
) -> tuple[int, Any, str]:
    auth = cfg["abra"]["auth"]
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    token = (auth.get("bearer_token") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        raw = base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
        headers["Authorization"] = f"Basic {raw}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=int(cfg["abra"].get("timeout_sec") or 60)) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else None, text[:2000]
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:2000]}
        return e.code, payload, text[:2000]


def main() -> int:
    cfg = load_config()
    base = cfg["abra"]["base_url"].rstrip("/")
    log: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "steps": [],
    }

    def step(name: str, method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
        q = ""
        if "?" not in path and method in ("POST", "PUT") and "validation" not in path:
            q = "?validation=true"
        url = f"{base}/{path.lstrip('/')}{q}"
        status, payload, raw = request(method, url, cfg, body)
        log["steps"].append(
            {
                "name": name,
                "method": method,
                "url": url,
                "status": status,
                "body_sent": body,
                "response": payload,
                "raw_preview": raw if status >= 400 else None,
            }
        )
        print(f"{name}: {status}")
        return status, payload

    # Read: list
    st, listed = step(
        "read_list",
        "GET",
        "crmactivities?" + urlencode({"take": 3, "select": "ID,Subject,Status,Firm_ID,ResponsibleUser_ID,SheduledStart$DATE"}),
    )

    # Supporting refs
    st, firms = step("read_firm_sample", "GET", "firms?" + urlencode({"take": 1, "select": "ID,Name"}))
    firm_id = None
    if st == 200 and isinstance(firms, list) and firms:
        firm_id = firms[0].get("ID")

    st, user = step("read_currentuser", "GET", "currentuser")
    user_id = None
    if st == 200 and isinstance(user, dict):
        user_id = user.get("ID") or user.get("id")

    st, types = step("read_activity_types", "GET", "crmactivitytypes?" + urlencode({"take": 5, "select": "ID,Code,Name"}))
    type_id = None
    if st == 200 and isinstance(types, list) and types:
        type_id = types[0].get("ID")

    sample_id = None
    if isinstance(listed, list) and listed:
        sample_id = listed[0].get("ID")
        step(
            "read_detail",
            "GET",
            f"crmactivities/{sample_id}?"
            + urlencode(
                {
                    "select": "ID,Subject,Description,Status,PMState_ID,Firm_ID,Person_ID,"
                    "ResponsibleUser_ID,ResponsibleCustomerPerson_ID,ActivityType_ID,SheduledStart$DATE,RealEnd$DATE"
                }
            ),
        )

    # Create validate
    create_body: dict[str, Any] = {
        "Subject": "Mobile CRM spike visit",
        "Description": "Lifecycle validation — safe to delete",
    }
    if firm_id:
        create_body["Firm_ID"] = firm_id
    if user_id:
        create_body["ResponsibleUser_ID"] = user_id
    if type_id:
        create_body["ActivityType_ID"] = type_id

    st, validated = step("create_validate", "POST", "crmactivities?validation=true", create_body)

    # Create
    st, created = step("create", "POST", "crmactivities?validation=true", create_body)
    spike_target = sample_id
    log["create_persisted"] = False
    if st in (200, 201) and isinstance(created, dict):
        created_id = created.get("ID") or created.get("id")
        meta = created.get("@meta") or created.get("meta") or {}
        validation = meta.get("validation") or {}
        err_count = (validation.get("errors") or {}).get("count") or 0
        log["create_persisted"] = st == 201 or err_count == 0
        log["create_preview_id"] = created_id
        if log["create_persisted"] and created_id:
            spike_target = created_id
    log["spike_target_id"] = spike_target

    if spike_target:
        activity_id = spike_target
        update_body = {
            "ID": activity_id,
            "Description": "Updated by Mobile CRM lifecycle spike",
        }
        if firm_id:
            update_body["Firm_ID"] = firm_id
        step("update_validate", "PUT", f"crmactivities/{activity_id}?validation=true", update_body)
        step("update", "PUT", f"crmactivities/{activity_id}?validation=true", update_body)

        # Complete via Status enum
        complete_body = {
            "ID": activity_id,
            "Status": 2,
            "Description": "Completed by Mobile CRM lifecycle spike",
            "Answer": "Visit outcome recorded in spike",
        }
        if firm_id:
            complete_body["Firm_ID"] = firm_id
        step("complete_status", "PUT", f"crmactivities/{activity_id}?validation=true", complete_body)

        st, after = step(
            "read_after_complete",
            "GET",
            f"crmactivities/{activity_id}?" + urlencode({"select": "ID,Status,Description,Answer,RealEnd$DATE,PMState_ID"}),
        )
        log["final_activity"] = after

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
