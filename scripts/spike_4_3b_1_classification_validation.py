#!/usr/bin/env python3
"""Sprint 4.3B.1 — Gen classification validation error spike."""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

GEN = "http://localhost/demo"
AUTH = "Basic " + base64.b64encode(b"api:123").decode()
OUT = "analysis/spikes/sprint-4-3b-1-classification-validation-results.json"

AREA_SP = "2000000101"
AREA_TT = "3000000101"
TYPE_TEL = "2000000101"
TYPE_OBCH = "3000000101"
QUEUE_PRHO = "2000000101"
QUEUE_NP = "4000000101"
FIRM = "4000000101"
SCHEDULED = "2026-06-15T10:00:00.000Z"


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


def val_errors(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {"count": -1, "values": []}
    meta = payload.get("@meta") or payload.get("meta") or {}
    errs = (meta.get("validation") or {}).get("errors") or {}
    vals = errs.get("values") or []
    return {"count": errs.get("count", len(vals)), "values": vals}


def parse_error_entries(values: list) -> list[dict]:
    entries: list[dict] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        for field, detail in item.items():
            if not isinstance(detail, dict):
                continue
            entries.append({
                "field": field,
                "code": detail.get("@code"),
                "message": detail.get("@description"),
                "displayLabel": detail.get("@displaylabel"),
                "clsid": detail.get("@clsid"),
            })
    return entries


def base_payload(**extra: str) -> dict:
    body = {
        "Subject": "4.3B.1 classification validation probe",
        "Firm_ID": FIRM,
        "SheduledStart$DATE": SCHEDULED,
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        "Division_ID": "2000000101",
        "SolverRole_ID": "1000000101",
    }
    body.update(extra)
    return body


def probe(name: str, body: dict) -> dict:
    st, payload = req("POST", "crmactivities?validation=true", body)
    errs = val_errors(payload)
    entries = parse_error_entries(errs.get("values", []))
    return {
        "name": name,
        "request": body,
        "status": st,
        "errorCount": errs.get("count"),
        "errors": entries,
        "classificationErrors": [
            e for e in entries
            if e["field"] in ("activityarea_id", "activitytype_id", "actqueue_id", "period_id")
        ],
    }


def main() -> int:
    probes = [
        probe("valid_sp_tel_prho", base_payload(
            ActivityArea_ID=AREA_SP,
            ActivityType_ID=TYPE_TEL,
            ActQueue_ID=QUEUE_PRHO,
        )),
        probe("tt_area_with_sp_type_queue", base_payload(
            ActivityArea_ID=AREA_TT,
            ActivityType_ID=TYPE_TEL,
            ActQueue_ID=QUEUE_PRHO,
        )),
        probe("tt_area_obch_np", {
            **base_payload(
                ActivityArea_ID=AREA_TT,
                ActivityType_ID=TYPE_OBCH,
                ActQueue_ID=QUEUE_NP,
            ),
            "NextContact$DATE": "2026-07-01T10:00:00.000Z",
            "TradeDate$DATE": "2026-08-01T10:00:00.000Z",
        }),
        probe("omit_type_with_tt_area", base_payload(
            ActivityArea_ID=AREA_TT,
            ActQueue_ID=QUEUE_PRHO,
        )),
        probe("omit_queue", base_payload(
            ActivityArea_ID=AREA_SP,
            ActivityType_ID=TYPE_TEL,
        )),
        probe("invalid_type_id", base_payload(
            ActivityArea_ID=AREA_SP,
            ActivityType_ID="9999999901",
            ActQueue_ID=QUEUE_PRHO,
        )),
    ]

    # Commit probe for TT area (may create or fail)
    commit_body = base_payload(
        ActivityArea_ID=AREA_TT,
        ActivityType_ID=TYPE_TEL,
        ActQueue_ID=QUEUE_PRHO,
    )
    st_commit, commit_payload = req("POST", "crmactivities", commit_body)
    commit_probe = {
        "name": "commit_tt_area_tel_prho",
        "status": st_commit,
        "errorCount": val_errors(commit_payload).get("count") if isinstance(commit_payload, dict) else None,
        "errors": parse_error_entries(val_errors(commit_payload).get("values", [])),
    }

    out = {
        "at": datetime.now(timezone.utc).isoformat(),
        "spike": "sprint-4-3b-1-classification-validation",
        "catalogs": {
            "areas": [
                {"id": AREA_SP, "code": "Sp"},
                {"id": AREA_TT, "code": "TT"},
            ],
        },
        "probes": probes,
        "commitProbe": commit_probe,
        "errorCodeSummary": {
            "800": "Rad aktivít (actqueue_id)",
            "801": "Obdobie / period (often queue-related)",
            "803": "Typ aktivity (activitytype_id)",
        },
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({"written": OUT, "probeCount": len(probes)}, indent=2))
    for p in probes:
        print(f"  {p['name']}: errors={p['errorCount']} classification={len(p['classificationErrors'])}")
    print(f"  commit: status={commit_probe['status']} errors={commit_probe['errorCount']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
