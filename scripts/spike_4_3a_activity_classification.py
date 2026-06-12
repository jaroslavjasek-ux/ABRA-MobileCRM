#!/usr/bin/env python3
"""Sprint 4.3A — Activity classification analysis (DEMO Gen)."""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

GEN = "http://localhost/demo"
AUTH = "Basic " + base64.b64encode(b"api:123").decode()
OUT = "analysis/spikes/sprint-4-3a-activity-classification-results.json"

REF_DEFAULTS = {
    "ActQueue_ID": "2000000101",
    "Division_ID": "2000000101",
    "SolverRole_ID": "1000000101",
    "ActivityArea_ID": "2000000101",
    "ActivityType_ID": "2000000101",
}
GALENIT = "4000000101"
SCHEDULED = "2026-06-11T10:00:00.000Z"


def req(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    url = f"{GEN}/{path.lstrip('/')}"
    headers = {"Authorization": AUTH, "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    r = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(r, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as ex:
        raw = ex.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return ex.code, payload


def field(row: object, *names: str):
    if not isinstance(row, dict):
        return None
    for name in names:
        for key in (name, name.lower()):
            if key in row and row[key] not in (None, ""):
                return row[key]
    return None


def norm_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        return [x for x in payload["value"] if isinstance(x, dict)]
    if isinstance(payload, dict) and (payload.get("ID") or payload.get("id")):
        return [payload]
    return []


def val_errors(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {"count": -1, "values": []}
    meta = payload.get("@meta") or payload.get("meta") or {}
    errs = (meta.get("validation") or {}).get("errors") or {}
    vals = errs.get("values") or []
    return {"count": errs.get("count", len(vals)), "values": vals}


def error_fields(payload: object) -> list[str]:
    out: list[str] = []
    for item in val_errors(payload).get("values") or []:
        if isinstance(item, dict):
            out.extend(item.keys())
    return out


def list_bo(name: str, select: str, take: int = 100) -> dict:
    st, rows = req("GET", f"{name}?select={quote(select)}&take={take}")
    items = norm_list(rows)
    return {"endpoint": name, "status": st, "count": len(items), "items": items}


def validate_probe(name: str, body: dict) -> dict:
    st, payload = req("POST", "crmactivities?validation=true", body)
    return {
        "name": name,
        "request": body,
        "status": st,
        "errors": val_errors(payload),
        "errorFields": error_fields(payload),
        "resolved": {
            "activityarea_id": field(payload, "activityarea_id", "ActivityArea_ID"),
            "activitytype_id": field(payload, "activitytype_id", "ActivityType_ID"),
            "actqueue_id": field(payload, "actqueue_id", "ActQueue_ID"),
            "activityprocess_id": field(payload, "activityprocess_id", "ActivityProcess_ID"),
            "period_id": field(payload, "period_id", "Period_ID"),
            "division_id": field(payload, "division_id", "Division_ID"),
            "solverrole_id": field(payload, "solverrole_id", "SolverRole_ID"),
            "displayname": field(payload, "DisplayName", "displayname"),
        },
    }


def main() -> int:
    out: dict = {"at": datetime.now(timezone.utc).isoformat(), "spike": "sprint-4-3a-activity-classification"}

    out["catalogs"] = {
        "areas": list_bo("crmactivityareas", "ID,Code,Name,DisplayName"),
        "types": list_bo("crmactivitytypes", "ID,Code,Name,DisplayName,ActivityArea_ID,BusTransactionReq,BusOrderReq,BusProjectReq"),
        "queues": list_bo("crmactivityqueues", "ID,Code,Name,DisplayName"),
        "processes": list_bo("crmactivityprocesses", "ID,Code,Name,DisplayName"),
    }

    for bo, sample_id in [
        ("crmactivityareas", "2000000101"),
        ("crmactivitytypes", "2000000101"),
        ("crmactivitytypes", "3000000101"),
        ("crmactivityqueues", "2000000101"),
        ("crmactivityqueues", "4000000101"),
    ]:
        st, detail = req("GET", f"{bo}/{sample_id}")
        out[f"detail_{bo}_{sample_id}"] = {"status": st, "body": detail if isinstance(detail, dict) else detail}

    # Reference activities with known display prefixes
    for act_id in ("E120000101", "5320000101"):
        st, act = req(
            "GET",
            f"crmactivities/{act_id}?select=ID,DisplayName,activityarea_id,activitytype_id,actqueue_id,activityprocess_id,processisrequired",
        )
        out[f"referenceActivity_{act_id}"] = act if isinstance(act, dict) else None

    # Survey recent activities for process usage
    st, acts = req(
        "GET",
        "crmactivities?"
        + quote("select=ID,DisplayName,activityarea_id,activitytype_id,actqueue_id,activityprocess_id,processisrequired")
        + "&take=30",
    )
    items = norm_list(acts)
    with_process = [a for a in items if field(a, "activityprocess_id")]
    out["activitySurvey"] = {
        "sampleSize": len(items),
        "withProcess": len(with_process),
        "uniqueAreas": sorted({field(a, "activityarea_id") for a in items if field(a, "activityarea_id")}),
        "uniqueTypes": sorted({field(a, "activitytype_id") for a in items if field(a, "activitytype_id")}),
        "uniqueQueues": sorted({field(a, "actqueue_id") for a in items if field(a, "actqueue_id")}),
        "samples": items[:10],
    }

    # Validate probes
    base = {
        "Subject": "4.3A classification probe",
        "Firm_ID": GALENIT,
        "SheduledStart$DATE": SCHEDULED,
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        "Division_ID": REF_DEFAULTS["Division_ID"],
        "SolverRole_ID": REF_DEFAULTS["SolverRole_ID"],
    }

    probes: list[dict] = []
    probes.append(validate_probe("minimal_user_only", {**base, "ActivityType_ID": REF_DEFAULTS["ActivityType_ID"]}))
    probes.append(validate_probe("no_classification_refs", dict(base)))
    probes.append(
        validate_probe(
            "full_config_defaults",
            {
                **base,
                **REF_DEFAULTS,
            },
        )
    )
    probes.append(
        validate_probe(
            "type_obch_no_queue",
            {
                **base,
                "ActivityType_ID": "3000000101",
                "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
            },
        )
    )
    probes.append(
        validate_probe(
            "queue_np_only",
            {
                **base,
                "ActQueue_ID": "4000000101",
                "ActivityType_ID": "3000000101",
                "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
            },
        )
    )
    probes.append(
        validate_probe(
            "queue_prho_only",
            {
                **base,
                "ActQueue_ID": "2000000101",
                "ActivityType_ID": REF_DEFAULTS["ActivityType_ID"],
                "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
            },
        )
    )
    probes.append(
        validate_probe(
            "omit_area",
            {
                **base,
                "ActivityType_ID": REF_DEFAULTS["ActivityType_ID"],
                "ActQueue_ID": REF_DEFAULTS["ActQueue_ID"],
            },
        )
    )
    probes.append(
        validate_probe(
            "omit_type",
            {
                **base,
                "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
                "ActQueue_ID": REF_DEFAULTS["ActQueue_ID"],
            },
        )
    )
    probes.append(
        validate_probe(
            "omit_queue",
            {
                **base,
                "ActivityType_ID": REF_DEFAULTS["ActivityType_ID"],
                "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
            },
        )
    )

    # Commit test: queue determines numbering prefix
    commit_tests: list[dict] = []
    for label, queue_id, type_id in [
        ("np_queue", "4000000101", "3000000101"),
        ("prho_queue", "2000000101", "2000000101"),
    ]:
        body = {
            **base,
            "Subject": f"4.3A commit {label}",
            "ActQueue_ID": queue_id,
            "ActivityType_ID": type_id,
            "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
        }
        st_v, validated = req("POST", "crmactivities?validation=true", body)
        merged = dict(body)
        for key, gen_key in [
            ("Period_ID", "period_id"),
            ("ActQueue_ID", "actqueue_id"),
            ("ActivityArea_ID", "activityarea_id"),
            ("ActivityType_ID", "activitytype_id"),
            ("Division_ID", "division_id"),
            ("SolverRole_ID", "solverrole_id"),
        ]:
            val = field(validated, gen_key, key)
            if val:
                merged[key] = val
        st_c, committed = req("POST", "crmactivities", merged)
        act_id = field(committed, "ID", "id")
        display = None
        if act_id:
            _, got = req("GET", f"crmactivities/{act_id}?select=ID,DisplayName,actqueue_id,activitytype_id")
            display = field(got, "DisplayName", "displayname")
        commit_tests.append(
            {
                "label": label,
                "queueId": queue_id,
                "typeId": type_id,
                "commitStatus": st_c,
                "activityId": act_id,
                "displayName": display,
            }
        )
    out["validateProbes"] = probes
    out["commitTests"] = commit_tests

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps({"written": OUT, "areas": out["catalogs"]["areas"]["count"], "types": out["catalogs"]["types"]["count"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
