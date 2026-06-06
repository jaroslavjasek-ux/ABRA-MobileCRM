#!/usr/bin/env python3
"""Sales representative identity spike — JSON log only."""
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
OUT = ROOT / "analysis" / "spikes" / "sales-representative-results.json"


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
            return resp.status, json.loads(text) if text else None, text[:3000]
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:3000]}
        return e.code, payload, text[:3000]


def main() -> int:
    cfg = load_config()
    base = cfg["abra"]["base_url"].rstrip("/")
    log: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "auth_username": cfg["abra"]["auth"].get("username"),
        "steps": [],
    }

    def step(name: str, path: str) -> tuple[int, Any]:
        url = f"{base}/{path.lstrip('/')}"
        status, payload, raw = request("GET", url, cfg)
        log["steps"].append(
            {"name": name, "url": url, "status": status, "response": payload, "raw_preview": raw if status >= 400 else None}
        )
        print(f"{name}: {status}")
        return status, payload

    st, cu = step("currentuser", "currentuser")
    user_id = None
    login = None
    if st == 200 and isinstance(cu, dict):
        user_id = cu.get("id") or cu.get("ID")
        login = cu.get("loginname") or cu.get("LoginName")
        log["currentuser_id"] = user_id
        log["currentuser_login"] = login

    if user_id:
        step(
            "securityuser_by_id",
            f"securityusers/{user_id}?"
            + urlencode({"select": "ID,LoginName,Name,DisplayName,Person_ID,IsActive"}),
        )
        if login:
            w = f"LoginName eq '{login}'"
            step(
                "securityusers_by_login",
                "securityusers?" + urlencode({"take": 3, "select": "ID,LoginName,Name,Person_ID", "where": w}),
            )

    st, users = step(
        "securityusers_sample",
        "securityusers?" + urlencode({"take": 5, "select": "ID,LoginName,Name,Person_ID,IsActive"}),
    )
    person_id = None
    for s in log["steps"]:
        if s["status"] != 200:
            continue
        r = s["response"]
        if s["name"] in ("securityuser_by_id", "securityuser_by_id_minimal") and isinstance(r, dict):
            person_id = r.get("Person_ID") or r.get("person_id")
        if s["name"] == "securityusers_by_login" and isinstance(r, list) and r:
            person_id = person_id or r[0].get("Person_ID") or r[0].get("person_id")
    if not person_id and st == 200 and isinstance(users, list) and users:
        person_id = users[0].get("Person_ID") or users[0].get("person_id")

    if person_id and person_id not in ("0000000000", "__________", None, ""):
        step(
            "person_for_user",
            f"persons/{person_id}?" + urlencode({"select": "ID,FirstName,LastName,DisplayName,IsEmployee"}),
        )
        step(
            "employees_by_person",
            "employees?"
            + urlencode(
                {
                    "take": 3,
                    "select": "ID,Person_ID,PersonalNumber,EmployeeName,Hidden",
                    "where": f"Person_ID eq '{person_id}'",
                }
            ),
        )

    if user_id:
        step(
            "employees_by_id_same_as_user",
            f"employees/{user_id}?" + urlencode({"select": "ID,Person_ID,PersonalNumber,EmployeeName"}),
        )

    # My activities filters
    act_sel = "ID,Subject,Status,Firm_ID,ResponsibleUser_ID,SolverUser_ID,CreatedBy_ID,SheduledStart$DATE"
    demo_rep = "1300000101"
    for rep_id in ([user_id] if user_id else []) + [demo_rep]:
        for where in [
            f"ResponsibleUser_ID eq '{rep_id}'",
            f"CreatedBy_ID eq '{rep_id}'",
            f"SolverUser_ID eq '{rep_id}'",
        ]:
            label = f"crmactivities_{rep_id}_{where.split()[0]}"
            step(
                label,
                "crmactivities?" + urlencode({"take": 3, "select": act_sel, "where": where}),
            )

    st, acts = step("crmactivities_sample", "crmactivities?" + urlencode({"take": 5, "select": act_sel}))
    if st == 200 and isinstance(acts, list):
        reps = set()
        for a in acts:
            for k in ("ResponsibleUser_ID", "CreatedBy_ID", "SolverUser_ID"):
                v = a.get(k) or a.get(k.lower())
                if v:
                    reps.add(f"{k}={v}")
        log["activity_user_fields_sample"] = sorted(reps)

    # My customers
    firm_sel = "ID,Name,Code,ResponsibleUser_ID,ResponsibleRole_ID,Hidden"
    for rep_id in ([user_id] if user_id else []) + [demo_rep]:
        step(
            f"firms_ResponsibleUser_{rep_id}",
            "firms?"
            + urlencode({"take": 5, "select": firm_sel, "where": f"ResponsibleUser_ID eq '{rep_id}'"}),
        )
    step(
        "firms_with_any_rep",
        "firms?" + urlencode({"take": 5, "select": firm_sel, "where": "ResponsibleUser_ID ne null"}),
    )
    step("firms_sample", "firms?" + urlencode({"take": 5, "select": firm_sel}))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
