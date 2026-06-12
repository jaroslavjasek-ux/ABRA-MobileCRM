#!/usr/bin/env python3
"""Sprint 4.3B.2A — Activity classification dependency analysis (DEMO Gen)."""

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
OUT = "analysis/spikes/sprint-4-3b-2a-classification-dependency-results.json"


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


def norm_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        return [x for x in payload["value"] if isinstance(x, dict)]
    return []


def field(row: dict | None, *names: str):
    if not row:
        return None
    for name in names:
        for key in (name, name.lower()):
            if key in row and row[key] not in (None, ""):
                return row[key]
    return None


def list_bo(collection: str, select: str, where: str | None = None, take: int = 50) -> dict:
    path = f"{collection}?select={quote(select)}&take={take}"
    if where:
        path += f"&where={quote(where)}"
    st, payload = req("GET", path)
    items = norm_list(payload)
    return {"endpoint": path, "status": st, "count": len(items), "items": items, "raw": payload if st != 200 else None}


def detail_bo(collection: str, obj_id: str, select: str | None = None) -> dict:
    path = f"{collection}/{obj_id}"
    if select:
        path += f"?select={quote(select)}"
    st, payload = req("GET", path)
    return {"path": path, "status": st, "body": payload if isinstance(payload, dict) else payload}


def validate_combo(name: str, body: dict) -> dict:
    st, payload = req("POST", "crmactivities?validation=true", body)
    errs = []
    if isinstance(payload, dict):
        meta = payload.get("@meta") or payload.get("meta") or {}
        values = ((meta.get("validation") or {}).get("errors") or {}).get("values") or []
        for item in values:
            if isinstance(item, dict):
                for fk, detail in item.items():
                    if isinstance(detail, dict):
                        errs.append({
                            "field": fk,
                            "code": detail.get("@code"),
                            "message": detail.get("@description"),
                        })
    return {
        "name": name,
        "status": st,
        "errorCount": len(errs),
        "errors": errs,
        "resolved": {
            "activityarea_id": field(payload if isinstance(payload, dict) else None, "activityarea_id"),
            "activitytype_id": field(payload if isinstance(payload, dict) else None, "activitytype_id"),
            "actqueue_id": field(payload if isinstance(payload, dict) else None, "actqueue_id"),
        } if isinstance(payload, dict) else {},
    }


def base_create(**extra: str) -> dict:
    body = {
        "Subject": "4.3B.2A dependency probe",
        "Firm_ID": "4000000101",
        "SheduledStart$DATE": "2026-06-20T10:00:00.000Z",
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        "Division_ID": "2000000101",
        "SolverRole_ID": "1000000101",
    }
    body.update(extra)
    return body


def main() -> int:
    area_sp = "2000000101"
    area_tt = "3000000101"
    type_tel = "2000000101"
    type_obch = "3000000101"
    type_te = None  # resolve from catalog
    queue_prho = "2000000101"
    queue_np = "4000000101"

    out: dict = {
        "at": datetime.now(timezone.utc).isoformat(),
        "spike": "sprint-4-3b-2a-classification-dependency",
    }

    # --- Catalogs ---
    out["catalogs"] = {
        "areas": list_bo("crmactivityareas", "ID,Code,Name,DisplayName"),
        "types_global": list_bo("crmactivitytypes", "ID,Code,Name,DisplayName"),
        "types_with_area_field": list_bo("crmactivitytypes", "ID,Code,Name,DisplayName,ActivityArea_ID"),
        "queues_global": list_bo("crmactivityqueues", "ID,Code,Name,DisplayName"),
        "queues_with_type_field": list_bo("crmactivityqueues", "ID,Code,Name,DisplayName,ActivityType_ID"),
    }

    for item in out["catalogs"]["types_global"]["items"]:
        if field(item, "Code") == "Te":
            type_te = field(item, "ID")

    # --- Area → Type query probes ---
    area_type_queries = []
    for area_id, label in [(area_sp, "Sp"), (area_tt, "TT")]:
        for where_tpl in [
            f"ActivityArea_ID eq '{area_id}'",
            f"activityarea_id eq '{area_id}'",
            f"ActivityArea_ID.ID eq '{area_id}'",
        ]:
            area_type_queries.append({
                "area": label,
                "areaId": area_id,
                **list_bo("crmactivitytypes", "ID,Code,Name,DisplayName,ActivityArea_ID", where=where_tpl),
            })
    out["areaToTypeQueries"] = area_type_queries

    # --- Area detail (nested collections?) ---
    out["areaDetails"] = {
        "Sp": detail_bo("crmactivityareas", area_sp),
        "TT": detail_bo("crmactivityareas", area_tt),
    }

    # --- Type details (ActivityArea_ID on type?) ---
    type_ids = {field(i, "ID"): field(i, "Code") for i in out["catalogs"]["types_global"]["items"]}
    out["typeDetails"] = {}
    for tid, code in type_ids.items():
        out["typeDetails"][code or tid] = detail_bo("crmactivitytypes", tid)

    # --- Queue details ---
    out["queueDetails"] = {
        "PrHo": detail_bo("crmactivityqueues", queue_prho),
        "NP": detail_bo("crmactivityqueues", queue_np),
    }

    # --- Type → Queue query probes ---
    type_queue_queries = []
    for type_id, label in [(type_tel, "Tel"), (type_obch, "Obch"), (type_te, "Te")]:
        if not type_id:
            continue
        for where_tpl in [
            f"ActivityType_ID eq '{type_id}'",
            f"activitytype_id eq '{type_id}'",
        ]:
            type_queue_queries.append({
                "type": label,
                "typeId": type_id,
                **list_bo("crmactivityqueues", "ID,Code,Name,DisplayName,ActivityType_ID", where=where_tpl),
            })
    out["typeToQueueQueries"] = type_queue_queries

    # --- Area+Type → Queue query probes ---
    combo_queue_queries = []
    combos = [
        ("Sp", area_sp, "Tel", type_tel),
        ("Sp", area_sp, "Obch", type_obch),
        ("TT", area_tt, "Te", type_te),
        ("TT", area_tt, "Tel", type_tel),
    ]
    for al, aid, tl, tid in combos:
        if not tid:
            continue
        for where_tpl in [
            f"ActivityType_ID eq '{tid}' and ActivityArea_ID eq '{aid}'",
            f"ActivityArea_ID eq '{aid}'",
        ]:
            combo_queue_queries.append({
                "area": al,
                "type": tl,
                **list_bo("crmactivityqueues", "ID,Code,Name,DisplayName", where=where_tpl),
            })
    out["areaTypeToQueueQueries"] = combo_queue_queries

    # --- Validate matrix: which combos pass ---
    validate_matrix = []
    test_combos = [
        ("sp_tel_prho", area_sp, type_tel, queue_prho),
        ("sp_obch_np", area_sp, type_obch, queue_np, {"NextContact$DATE": "2026-07-01T10:00:00.000Z", "TradeDate$DATE": "2026-08-01T10:00:00.000Z"}),
        ("tt_te_prho", area_tt, type_te, queue_prho),
        ("tt_tel_prho", area_tt, type_tel, queue_prho),
        ("tt_te_np", area_tt, type_te, queue_np),
    ]
    for entry in test_combos:
        name, aid, tid, qid = entry[:4]
        extra_dates = entry[4] if len(entry) > 4 else {}
        if not tid:
            continue
        body = base_create(ActivityArea_ID=aid, ActivityType_ID=tid, ActQueue_ID=qid, **extra_dates)
        validate_matrix.append(validate_combo(name, body))
    out["validateMatrix"] = validate_matrix

    # --- Reference activities by area ---
    for area_id, label in [(area_sp, "Sp"), (area_tt, "TT")]:
        st, payload = req(
            "GET",
            f"crmactivities?select=ID,DisplayName,activityarea_id,activitytype_id,actqueue_id&where={quote(f'activityarea_id eq \"{area_id}\"')}&take=10",
        )
        out[f"sampleActivities_{label}"] = {"status": st, "items": norm_list(payload)}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({"written": OUT}, indent=2))
    print("types:", out["catalogs"]["types_global"]["count"])
    print("Te id:", type_te)
    for q in area_type_queries:
        if q.get("status") == 200 and q.get("count", 0) > 0:
            print(f"  area {q['area']} filter -> {q['count']} types")
    for v in validate_matrix:
        print(f"  validate {v['name']}: errors={v['errorCount']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
