#!/usr/bin/env python3
"""Sprint 4.2A — Business dimensions analysis spike (DEMO Gen)."""

from __future__ import annotations

import base64
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

GEN = "http://localhost/demo"
ADAPTER = "http://localhost:5082/api/v1"
AUTH = "Basic " + base64.b64encode(b"api:123").decode()

# Known DEMO dimension IDs (from sprint-3a-2)
DIM_BUS_TRANSACTION = "3000000101"
DIM_BUS_ORDER = "A000000101"
DIM_BUS_PROJECT = "2000000101"
DIM_FIRM = "3000000101"
DIM_FIRM_ALT = "3300000101"
ACTIVITY_TYPE = "2000000101"
REF_DEFAULTS = {
    "ActQueue_ID": "2000000101",
    "Period_ID": "4000000101",
    "Division_ID": "2000000101",
    "SolverRole_ID": "1000000101",
    "ActivityArea_ID": "2000000101",
}


def gen_req(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    url = f"{GEN}/{path.lstrip('/')}"
    headers = {"Authorization": AUTH, "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as ex:
        raw = ex.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return ex.code, payload


def adapter_req(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, object]:
    url = f"{ADAPTER}{path}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as ex:
        raw = ex.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return ex.code, payload


def validation_error_count(payload: object) -> int:
    if not isinstance(payload, dict):
        return -1
    meta = payload.get("@meta") or payload.get("meta") or {}
    validation = meta.get("validation") or {}
    errors = validation.get("errors") or {}
    if isinstance(errors.get("count"), int):
        return errors["count"]
    values = errors.get("values")
    if isinstance(values, list):
        return len(values)
    return 0


def normalize_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("value"), list):
            return [r for r in payload["value"] if isinstance(r, dict)]
        if payload.get("ID") or payload.get("id"):
            return [payload]
    return []


def field(row: dict, *names: str):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
        ln = n.lower()
        if ln in row and row[ln] not in (None, ""):
            return row[ln]
    return None


def probe_dimension_bo(name: str, firm_id: str) -> dict:
    select = quote("ID,DisplayName,Code,Name,Firm_ID")
    result: dict = {"bo": name, "tests": []}

    def add(test: str, path: str, ok: bool, detail: dict):
        result["tests"].append({"test": test, "path": path, "ok": ok, **detail})

    # List take
    t0 = time.perf_counter()
    st, rows = gen_req("GET", f"{name}?select={select}&take=5")
    elapsed = round((time.perf_counter() - t0) * 1000)
    items = normalize_list(rows)
    add(
        "list_take_5",
        f"{name}?select=...&take=5",
        st == 200,
        {"status": st, "count": len(items), "elapsedMs": elapsed, "sample": items[:2]},
    )

    # Paging skip
    t0 = time.perf_counter()
    st2, rows2 = gen_req("GET", f"{name}?select={select}&take=3&skip=3")
    elapsed2 = round((time.perf_counter() - t0) * 1000)
    add(
        "list_skip",
        f"{name}?take=3&skip=3",
        st2 == 200,
        {"status": st2, "count": len(normalize_list(rows2)), "elapsedMs": elapsed2},
    )

    # Filter by firm
    where = quote(f"Firm_ID eq '{firm_id}'")
    t0 = time.perf_counter()
    st3, rows3 = gen_req("GET", f"{name}?select={select}&where={where}&take=20")
    elapsed3 = round((time.perf_counter() - t0) * 1000)
    firm_items = normalize_list(rows3)
    add(
        "filter_firm",
        f"{name}?where=Firm_ID eq '{firm_id}'",
        st3 == 200,
        {"status": st3, "count": len(firm_items), "elapsedMs": elapsed3, "sample": firm_items[:2]},
    )

    # Search DisplayName contains (OData like)
    qstar = quote("*Služby*")
    where_search = quote(f"DisplayName like '{qstar}'")
    t0 = time.perf_counter()
    st4, rows4 = gen_req("GET", f"{name}?select={select}&where={where_search}&take=10")
    elapsed4 = round((time.perf_counter() - t0) * 1000)
    search_items = normalize_list(rows4)
    add(
        "search_displayname",
        f"{name}?where=DisplayName like '*…*'",
        st4 == 200,
        {"status": st4, "count": len(search_items), "elapsedMs": elapsed4, "sample": search_items[:2]},
    )

    # Detail by known id
    sample_id = field(items[0], "ID", "id") if items else None
    if sample_id:
        st5, detail = gen_req("GET", f"{name}/{sample_id}?select={select}")
        add(
            "detail_by_id",
            f"{name}/{sample_id}",
            st5 == 200 and isinstance(detail, dict),
            {"status": st5, "fields": {k: field(detail, k) for k in ("ID", "DisplayName", "Code", "Name", "Firm_ID")} if isinstance(detail, dict) else None},
        )

    return result


def create_activity_gen(dims: dict[str, str | None], label: str) -> dict:
    scheduled = (datetime.now(timezone.utc) + timedelta(days=3)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    body = {
        "Subject": f"4.2A {label}",
        "Firm_ID": DIM_FIRM,
        "ActivityType_ID": ACTIVITY_TYPE,
        "SheduledStart$DATE": scheduled.isoformat().replace("+00:00", ".000Z"),
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        **REF_DEFAULTS,
    }
    for key, val in dims.items():
        if val:
            body[key] = val

    st_v, validated = gen_req("POST", "crmactivities?validation=true", body)
    err_v = validation_error_count(validated)
    st_c, committed = gen_req("POST", "crmactivities", body)
    err_c = validation_error_count(committed)
    act_id = field(committed, "ID", "id") if isinstance(committed, dict) else None
    if not act_id and isinstance(validated, dict):
        act_id = field(validated, "ID", "id")

    persisted = {}
    if act_id:
        _, got = gen_req(
            "GET",
            f"crmactivities/{act_id}?select=ID,BusTransaction_ID,BusOrder_ID,BusProject_ID,bustransaction_id,busorder_id,busproject_id",
        )
        if isinstance(got, dict):
            persisted = {
                "bustransaction_id": field(got, "bustransaction_id", "BusTransaction_ID"),
                "busorder_id": field(got, "busorder_id", "BusOrder_ID"),
                "busproject_id": field(got, "busproject_id", "BusProject_ID"),
            }

    return {
        "label": label,
        "dims": dims,
        "validateStatus": st_v,
        "validateErrors": err_v,
        "commitStatus": st_c,
        "commitErrors": err_c,
        "activityId": act_id,
        "persisted": persisted,
        "ok": err_v == 0 and st_c in (200, 201) and err_c == 0,
    }


def test_update_complete_handover(source_id: str) -> dict:
    out: dict = {"sourceId": source_id, "steps": []}

    # Update dimension via PUT
    put_body = {
        "Firm_ID": DIM_FIRM,
        "BusTransaction_ID": DIM_BUS_TRANSACTION,
        "BusOrder_ID": DIM_BUS_ORDER,
        "BusProject_ID": DIM_BUS_PROJECT,
    }
    st_u, updated = gen_req("PUT", f"crmactivities/{source_id}", put_body)
    _, got_u = gen_req("GET", f"crmactivities/{source_id}")
    out["steps"].append(
        {
            "name": "update_dimensions",
            "ok": st_u in (200, 201),
            "status": st_u,
            "persisted": {
                "bustransaction_id": field(got_u, "bustransaction_id") if isinstance(got_u, dict) else None,
                "busorder_id": field(got_u, "busorder_id") if isinstance(got_u, dict) else None,
                "busproject_id": field(got_u, "busproject_id") if isinstance(got_u, dict) else None,
            },
        }
    )

    # Complete via adapter if available
    try:
        _, sess = adapter_req("POST", "/session", {"loginName": "api", "password": "123"})
        token = sess.get("sessionToken") if isinstance(sess, dict) else None
        if token:
            st_c, completed = adapter_req(
                "PUT",
                f"/activities/{source_id}/complete",
                {"answer": "4.2A complete test", "followUp": {"enabled": False}},
                token,
            )
            _, got_c = gen_req("GET", f"crmactivities/{source_id}")
            out["steps"].append(
                {
                    "name": "complete",
                    "ok": st_c == 200,
                    "status": st_c,
                    "dimsAfterComplete": {
                        "bustransaction_id": field(got_c, "bustransaction_id") if isinstance(got_c, dict) else None,
                        "busorder_id": field(got_c, "busorder_id") if isinstance(got_c, dict) else None,
                        "busproject_id": field(got_c, "busproject_id") if isinstance(got_c, dict) else None,
                    },
                }
            )
    except Exception as ex:
        out["steps"].append({"name": "complete", "ok": False, "error": str(ex)})

    # Handover / follow-up with Source_ID (Gen direct)
    scheduled = (datetime.now(timezone.utc) + timedelta(days=4)).replace(
        hour=11, minute=0, second=0, microsecond=0
    )
    child_body = {
        "Subject": "4.2A handover child",
        "Firm_ID": DIM_FIRM,
        "ActivityType_ID": ACTIVITY_TYPE,
        "SheduledStart$DATE": scheduled.isoformat().replace("+00:00", ".000Z"),
        "Source_ID": source_id,
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        **REF_DEFAULTS,
        "BusTransaction_ID": field(got_u, "bustransaction_id", "BusTransaction_ID"),
        "BusOrder_ID": field(got_u, "busorder_id", "BusOrder_ID"),
        "BusProject_ID": field(got_u, "busproject_id", "BusProject_ID"),
    }
    # Remove None keys
    child_body = {k: v for k, v in child_body.items() if v}

    st_v, _ = gen_req("POST", "crmactivities?validation=true", child_body)
    st_h, child = gen_req("POST", "crmactivities", child_body)
    child_id = field(child, "ID", "id") if isinstance(child, dict) else None
    inherited = {}
    if child_id:
        _, got_child = gen_req("GET", f"crmactivities/{child_id}")
        if isinstance(got_child, dict):
            inherited = {
                "bustransaction_id": field(got_child, "bustransaction_id"),
                "busorder_id": field(got_child, "busorder_id"),
                "busproject_id": field(got_child, "busproject_id"),
            }

    source_dims = {
        "bustransaction_id": field(got_u, "bustransaction_id") if isinstance(got_u, dict) else None,
        "busorder_id": field(got_u, "busorder_id") if isinstance(got_u, dict) else None,
        "busproject_id": field(got_u, "busproject_id") if isinstance(got_u, dict) else None,
    }
    out["steps"].append(
        {
            "name": "handover_create",
            "ok": st_h in (200, 201) and child_id,
            "status": st_h,
            "validateStatus": st_v,
            "childId": child_id,
            "sourceDims": source_dims,
            "childDims": inherited,
            "inheritedMatch": inherited == {k: v for k, v in source_dims.items() if v},
        }
    )

    return out


def firm_filter_survey() -> dict:
    """Compare global list vs firm-filtered counts across BOs."""
    select = quote("ID,DisplayName,Firm_ID")
    survey = {}
    for bo in ("bustransactions", "busorders", "busprojects"):
        _, all_rows = gen_req("GET", f"{bo}?select={select}&take=100")
        all_items = normalize_list(all_rows)
        with_firm = [r for r in all_items if field(r, "Firm_ID", "firm_id")]
        for firm in (DIM_FIRM, DIM_FIRM_ALT):
            where = quote(f"Firm_ID eq '{firm}'")
            _, filtered = gen_req("GET", f"{bo}?select={select}&where={where}&take=100")
            filt_items = normalize_list(filtered)
            survey.setdefault(bo, {})[firm] = {
                "globalTake100": len(all_items),
                "rowsWithFirmIdInSample": len(with_firm),
                "firmFilterCount": len(filt_items),
                "sampleFirmIds": list({field(r, "Firm_ID", "firm_id") for r in all_items[:20] if field(r, "Firm_ID", "firm_id")})[:5],
            }
    return survey


def main() -> int:
    log: dict = {
        "at": datetime.now(timezone.utc).isoformat(),
        "spike": "sprint-4-2a-business-dimensions",
        "dimensionApis": [],
        "activityScenarios": [],
        "lifecycle": None,
        "firmFilterSurvey": None,
        "activityTypeFlags": None,
    }

    for bo in ("bustransactions", "busorders", "busprojects"):
        log["dimensionApis"].append(probe_dimension_bo(bo, DIM_FIRM))

    scenarios = [
        ("business_case_only", {"BusTransaction_ID": DIM_BUS_TRANSACTION}),
        ("work_order_only", {"BusOrder_ID": DIM_BUS_ORDER}),
        ("project_only", {"BusProject_ID": DIM_BUS_PROJECT}),
        (
            "all_three",
            {
                "BusTransaction_ID": DIM_BUS_TRANSACTION,
                "BusOrder_ID": DIM_BUS_ORDER,
                "BusProject_ID": DIM_BUS_PROJECT,
            },
        ),
        ("none", {}),
    ]
    for label, dims in scenarios:
        log["activityScenarios"].append(create_activity_gen(dims, label))

    all_three = next((s for s in log["activityScenarios"] if s["label"] == "all_three" and s.get("activityId")), None)
    if all_three and all_three.get("activityId"):
        log["lifecycle"] = test_update_complete_handover(all_three["activityId"])

    log["firmFilterSurvey"] = firm_filter_survey()

    st, flags = gen_req(
        "GET",
        f"crmactivitytypes/{ACTIVITY_TYPE}?select=ID,BusOrderReq,BusProjectReq,BusTransactionReq",
    )
    log["activityTypeFlags"] = {"status": st, "flags": flags}

    out_path = "analysis/spikes/sprint-4-2a-business-dimensions-results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_path}")

    failed = 0
    for s in log["activityScenarios"]:
        print(f"{'PASS' if s['ok'] else 'FAIL'} create {s['label']} id={s.get('activityId')}")
        if not s["ok"]:
            failed += 1
    if log.get("lifecycle"):
        for step in log["lifecycle"]["steps"]:
            print(f"{'PASS' if step.get('ok') else 'FAIL'} lifecycle {step['name']}")
            if not step.get("ok"):
                failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
