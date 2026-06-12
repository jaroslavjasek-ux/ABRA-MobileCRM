#!/usr/bin/env python3
"""Extra probes for 4.3B.2A — append to results JSON."""
from __future__ import annotations

import base64
import json
from urllib.request import Request, urlopen

AUTH = "Basic " + base64.b64encode(b"api:123").decode()
OUT = "analysis/spikes/sprint-4-3b-2a-classification-dependency-results.json"

AREA_SP = "2000000101"
AREA_TT = "3000000101"
TYPES = {"Tel": "2000000101", "Obch": "3000000101", "Te": "4000000101"}
QUEUES = {"PrHo": "2000000101", "OdHo": "3000000101", "NP": "4000000101", "PS": "5000000101", "RK": "6000000101"}


def post(body: dict) -> dict:
    r = Request(
        "http://localhost/demo/crmactivities?validation=true",
        data=json.dumps(body).encode(),
        headers={"Authorization": AUTH, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(r, timeout=60) as resp:
        return json.loads(resp.read())


def base(**extra):
    b = {
        "Subject": "4.3B.2A extra",
        "Firm_ID": "4000000101",
        "SheduledStart$DATE": "2026-06-20T10:00:00.000Z",
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        "Division_ID": "2000000101",
        "SolverRole_ID": "1000000101",
    }
    b.update(extra)
    return b


def errs(p: dict) -> list[dict]:
    out = []
    for item in ((p.get("@meta") or {}).get("validation") or {}).get("errors", {}).get("values", []):
        if isinstance(item, dict):
            for fk, d in item.items():
                if isinstance(d, dict):
                    out.append({"field": fk, "code": d.get("@code")})
    return out


def type_ok(area_id: str, type_id: str) -> dict:
    p = post(base(ActivityArea_ID=area_id, ActivityType_ID=type_id, ActQueue_ID=QUEUES["PrHo"]))
    e = errs(p)
    type_err = any(x["field"] == "activitytype_id" for x in e)
    queue_err = any(x["field"] == "actqueue_id" for x in e)
    return {
        "requestedType": type_id,
        "resolvedType": p.get("activitytype_id"),
        "typeError": type_err,
        "queueError": queue_err,
        "errors": e,
    }


def queue_ok(area_id: str, type_id: str, queue_id: str) -> dict:
    extra = {"ActivityArea_ID": area_id, "ActivityType_ID": type_id, "ActQueue_ID": queue_id}
    if type_id == TYPES["Obch"]:
        extra["NextContact$DATE"] = "2026-07-01T10:00:00.000Z"
        extra["TradeDate$DATE"] = "2026-08-01T10:00:00.000Z"
    p = post(base(**extra))
    e = errs(p)
    return {
        "queue": queue_id,
        "errorCount": len(e),
        "errors": e,
        "resolvedQueue": p.get("actqueue_id"),
    }


def main():
    with open(OUT, encoding="utf-8") as f:
        data = json.load(f)

    # Area-only validate — what does Gen resolve?
    for label, aid in [("Sp", AREA_SP), ("TT", AREA_TT)]:
        p = post(base(ActivityArea_ID=aid))
        data[f"validateAreaOnly_{label}"] = {
            "resolved": {
                "activityarea_id": p.get("activityarea_id"),
                "activitytype_id": p.get("activitytype_id"),
                "actqueue_id": p.get("actqueue_id"),
            },
            "errors": errs(p),
        }

    # Type compatibility matrix per area
    for area_label, aid in [("Sp", AREA_SP), ("TT", AREA_TT)]:
        data[f"typeCompatibility_{area_label}"] = {
            name: type_ok(aid, tid) for name, tid in TYPES.items()
        }

    # Queue compatibility for valid area+type pairs
    data["queueCompatibility"] = {
        "Sp_Tel": {q: queue_ok(AREA_SP, TYPES["Tel"], qid) for q, qid in QUEUES.items()},
        "Sp_Obch": {q: queue_ok(AREA_SP, TYPES["Obch"], qid) for q, qid in QUEUES.items()},
        "TT_Te": {q: queue_ok(AREA_TT, TYPES["Te"], qid) for q, qid in QUEUES.items()},
    }

    # crmmenuitems — desktop menu config?
    try:
        r = Request(
            "http://localhost/demo/crmmenuitems?take=50",
            headers={"Authorization": AUTH},
        )
        with urlopen(r, timeout=30) as resp:
            data["crmmenuitems_sample"] = json.loads(resp.read())
    except Exception as ex:
        data["crmmenuitems_sample"] = str(ex)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("updated", OUT)


if __name__ == "__main__":
    main()
