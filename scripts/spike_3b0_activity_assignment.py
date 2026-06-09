#!/usr/bin/env python3
"""Sprint 3B.0 — activity assignment / My Day visibility spike."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "analysis" / "spikes" / "sprint-3b0-activity-assignment-results.json"

BASE = "http://localhost/demo"
AUTH = base64.b64encode(b"api:123").decode()
HEADERS = {
    "Authorization": f"Basic {AUTH}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

IDS = {
    "JANO": "1200000101",
    "API": "2610000101",
    "MANE": "1300000101",
    "DARA": "4300000101",
    "Obchodnik": "6000000101",
    "Technik": "1500000101",
    "Predajca": "1000000101",
}


def req(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            text = resp.read().decode()
            return resp.status, json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        text = e.read().decode()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:2000]}
        return e.code, payload


def unwrap_list(payload: object) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("value") or []
    return []


def ownership_visible(rep_id: str, activity_id: str) -> bool:
    where = (
        f"(ResponsibleUser_ID eq '{rep_id}' or SolverUser_ID eq '{rep_id}' "
        f"or CreatedBy_ID eq '{rep_id}') and ID eq '{activity_id}'"
    )
    st, data = req("GET", f"crmactivities?select=ID&where={urllib.parse.quote(where)}&take=1")
    return st == 200 and len(unwrap_list(data)) > 0


def role_membership_visible(role_id: str, rep_id: str) -> bool:
    st, data = req("GET", f"securityroles/{role_id}/securityusers?take=50")
    if st != 200:
        return False
    return any((u.get("id") or u.get("ID")) == rep_id for u in unwrap_list(data))


def create_activity(label: str, solver_role: str, solver_user: str | None, resp_user: str | None, src: dict) -> dict:
    today = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    end = today + timedelta(hours=2)
    body: dict = {
        "Subject": f"3B0-{label}",
        "Description": "Sprint 3B.0 assignment test — safe to delete",
        "Status": 0,
        "Firm_ID": src["firm_id"],
        "ActivityType_ID": src["activitytype_id"],
        "SheduledStart$DATE": today.isoformat().replace("+00:00", "Z"),
        "SheduledEnd$DATE": end.isoformat().replace("+00:00", "Z"),
        "ActQueue_ID": src["actqueue_id"],
        "Period_ID": src["period_id"],
        "Division_ID": src["division_id"],
        "SolverRole_ID": solver_role,
        "ActivityArea_ID": src["activityarea_id"],
    }
    if solver_user:
        body["SolverUser_ID"] = solver_user
    if resp_user:
        body["ResponsibleUser_ID"] = resp_user

    st_v, validated = req("POST", "crmactivities?validation=true", body)
    meta = (validated.get("@meta") if isinstance(validated, dict) else {}) or {}
    errors = (meta.get("validation") or {}).get("errors") or {}
    err_count = errors.get("count", 0) if isinstance(errors, dict) else len(errors)
    result: dict = {"label": label, "validate_status": st_v, "validate_errors": errors}
    if st_v != 200 or err_count:
        return result

    st_c, committed = req("POST", "crmactivities", body)
    aid = None
    if isinstance(committed, dict):
        aid = committed.get("id") or committed.get("ID")
    result["commit_status"] = st_c
    result["activity_id"] = aid

    if aid:
        _, got = req(
            "GET",
            f"crmactivities/{aid}?select=ID,DisplayName,ResponsibleUser_ID,SolverUser_ID,"
            "SolverRole_ID,ResponsibleRole_ID,CreatedBy_ID,Status",
        )
        result["persisted"] = got

    return result


def main() -> None:
    log: dict = {"base_url": BASE, "ids": IDS, "scenarios": [], "api_probes": {}}

    _, src = req("GET", "crmactivities/2000000101")
    if not isinstance(src, dict):
        raise SystemExit("source activity missing")

    scenarios = [
        ("A-Obchodnik-JANO", IDS["Obchodnik"], IDS["JANO"], None),
        ("B-Technik-NULL", IDS["Technik"], None, None),
        ("C-Technik-DARA", IDS["Technik"], IDS["DARA"], None),
        ("D-SolverUser-only-JANO", IDS["Predajca"], IDS["JANO"], None),
        ("E-ResponsibleUser-only-JANO", IDS["Predajca"], None, IDS["JANO"]),
    ]

    created: list[dict] = []
    for label, role, solver, resp in scenarios:
        created.append(create_activity(label, role, solver, resp, src))

    reps = [
        ("JANO", IDS["JANO"]),
        ("MANE", IDS["MANE"]),
        ("DARA", IDS["DARA"]),
        ("API", IDS["API"]),
    ]
    for item in created:
        aid = item.get("activity_id")
        vis: dict = {}
        role_vis: dict = {}
        if aid:
            for name, rep_id in reps:
                vis[name] = ownership_visible(rep_id, aid)
            persisted = item.get("persisted") or {}
            solver_role = persisted.get("solverrole_id") or persisted.get("SolverRole_ID")
            if solver_role:
                for name, rep_id in reps:
                    role_vis[name] = role_membership_visible(solver_role, rep_id)
        item["mobile_myday_ownership_filter"] = vis
        item["solver_role_membership"] = role_vis

    log["scenarios"] = created

    for ep in [
        "securityroles?take=5&select=ID,Name,ShortName",
        "securityusers?take=5&select=ID,Name,LoginName",
        "securityroles/6000000101/securityusers?take=10",
        "securityroles/1500000101/securityusers?take=10",
        "securityusers/1200000101/securityroles?take=10",
        "currentuser",
    ]:
        st, data = req("GET", ep)
        log["api_probes"][ep] = {"status": st, "response": data}

    # matrix-only scenarios without create
    matrix_tests = []
    for field, user_id in [
        ("SolverUser_ID", IDS["JANO"]),
        ("ResponsibleUser_ID", IDS["JANO"]),
        ("CreatedBy_ID", IDS["JANO"]),
    ]:
        where = f"{field} eq '{user_id}' and Status eq 0"
        st, data = req(
            "GET",
            f"crmactivities?select=ID,Subject,{field},SolverRole_ID,ResponsibleUser_ID,SolverUser_ID"
            f"&where={urllib.parse.quote(where)}&take=3",
        )
        matrix_tests.append({"field": field, "user": user_id, "status": st, "sample": unwrap_list(data)[:2]})
    log["open_activity_samples"] = matrix_tests

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(log, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
