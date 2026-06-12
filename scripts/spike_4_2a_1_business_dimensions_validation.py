#!/usr/bin/env python3
"""Sprint 4.2A.1 — Business dimensions validation & relationships (DEMO Gen). Analysis only."""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

GEN = "http://localhost/demo"
AUTH = "Basic " + base64.b64encode(b"api:123").decode()
OUT_PATH = "analysis/spikes/sprint-4-2a-1-business-dimensions-validation-results.json"

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


def field(row: object, *names: str):
    if not isinstance(row, dict):
        return None
    for name in names:
        for key in (name, name.lower()):
            if key in row and row[key] not in (None, ""):
                return row[key]
    return None


def normalize_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("value"), list):
            return [row for row in payload["value"] if isinstance(row, dict)]
        if payload.get("ID") or payload.get("id"):
            return [payload]
    return []


def validation_errors(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {"count": -1, "values": [], "raw": payload}
    meta = payload.get("@meta") or payload.get("meta") or {}
    validation = meta.get("validation") or {}
    errors = validation.get("errors") or {}
    values = errors.get("values") or []
    return {
        "count": errors.get("count", len(values)),
        "values": values,
    }


def lookup_dimension(bo: str, term: str) -> dict | None:
    select = quote("ID,DisplayName,Code,Name,Firm_ID")
    for field_name in ("Code", "Name"):
        where = quote(f"{field_name} like '*{term}*'")
        _, rows = gen_req("GET", f"{bo}?select={select}&where={where}&take=10")
        items = normalize_list(rows)
        if items:
            return items[0]
    return None


def activity_dims(row: dict | None) -> dict:
    if not row:
        return {}
    return {
        "bustransaction_id": field(row, "bustransaction_id", "BusTransaction_ID"),
        "busorder_id": field(row, "busorder_id", "BusOrder_ID"),
        "busproject_id": field(row, "busproject_id", "BusProject_ID"),
    }


def main() -> int:
    out: dict = {
        "at": datetime.now(timezone.utc).isoformat(),
        "spike": "sprint-4-2a-1-business-dimensions-validation",
    }

    firm_select = quote("ID,Name,Code,DisplayName")
    galenit_where = quote("Name like '*Galenit*'")
    _, galenit_rows = gen_req("GET", f"firms?select={firm_select}&where={galenit_where}&take=10")
    galenit_items = normalize_list(galenit_rows)
    out["galenit_search"] = {"count": len(galenit_items), "items": galenit_items}
    galenit_id = field(galenit_items[0], "ID", "id") if galenit_items else None

    refs = {
        "bustransactions": lookup_dimension("bustransactions", "Výstavy"),
        "busorders": lookup_dimension("busorders", "Služby"),
        "busprojects": lookup_dimension("busprojects", "Dealer"),
    }
    out["reference_dimensions"] = refs

    select = quote("ID,DisplayName,Code,Name,Firm_ID")
    survey: dict = {}
    for bo in ("bustransactions", "busorders", "busprojects"):
        _, rows = gen_req("GET", f"{bo}?select={select}&take=100")
        items = normalize_list(rows)
        with_firm = [row for row in items if field(row, "Firm_ID", "firm_id")]
        survey[bo] = {
            "total": len(items),
            "withFirmId": len(with_firm),
            "sampleFirmIds": sorted({field(row, "Firm_ID", "firm_id") for row in with_firm}),
            "allRows": items,
        }
    out["firmIdSurvey"] = survey

    bc_id = field(refs.get("bustransactions"), "ID", "id")
    wo_id = field(refs.get("busorders"), "ID", "id")
    pr_id = field(refs.get("busprojects"), "ID", "id")

    if galenit_id:
        act_select = quote(
            "ID,Subject,Firm_ID,bustransaction_id,busorder_id,busproject_id,division_id"
        )
        where = quote(f"Firm_ID eq '{galenit_id}'")
        _, acts = gen_req("GET", f"crmactivities?select={act_select}&where={where}&take=30")
        galenit_acts = normalize_list(acts)
        out["galenitActivities"] = galenit_acts

        rich = []
        for act in galenit_acts:
            dims = activity_dims(act)
            if any(dims.values()):
                rich.append({"id": field(act, "ID", "id"), "subject": field(act, "Subject", "subject"), **dims})
        out["galenitActivitiesWithDimensions"] = rich

    ref_activity = None
    for dim_field, dim_id in (
        ("bustransaction_id", bc_id),
        ("busorder_id", wo_id),
        ("busproject_id", pr_id),
    ):
        if not dim_id:
            continue
        act_select = quote("ID,Subject,Firm_ID,bustransaction_id,busorder_id,busproject_id,division_id")
        where = quote(f"{dim_field} eq '{dim_id}'")
        _, acts = gen_req("GET", f"crmactivities?select={act_select}&where={where}&take=20")
        items = normalize_list(acts)
        out[f"activitiesBy_{dim_field}"] = items
        for act in items:
            dims = activity_dims(act)
            if dims.get("bustransaction_id") == bc_id and dims.get("busorder_id") == wo_id and dims.get("busproject_id") == pr_id:
                ref_activity = act
                break
        if ref_activity:
            break

    if ref_activity:
        act_id = field(ref_activity, "ID", "id")
        _, full = gen_req("GET", f"crmactivities/{act_id}")
        out["referenceActivity"] = {
            "listRow": ref_activity,
            "fullGet": full if isinstance(full, dict) else None,
        }
        if isinstance(full, dict):
            _, firm = gen_req("GET", f"firms/{field(full, 'Firm_ID', 'firm_id')}?select=ID,Name,Code")
            out["referenceActivityFirm"] = firm

    scheduled = (
        datetime.now(timezone.utc) + timedelta(days=6)
    ).replace(hour=10, minute=0, second=0, microsecond=0)
    scheduled_s = scheduled.isoformat().replace("+00:00", ".000Z")
    base = {
        "Subject": "4.2A.1 validation probe",
        "ActivityType_ID": "2000000101",
        "SheduledStart$DATE": scheduled_s,
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        **REF_DEFAULTS,
    }

    required_tests: dict = {}
    for name, body in (
        ("missing_firm", dict(base)),
        ("missing_division", {**base, "Firm_ID": galenit_id or "3300000101"}),
        ("missing_both", {"Subject": base["Subject"], "ActivityType_ID": base["ActivityType_ID"], "SheduledStart$DATE": scheduled_s}),
    ):
        st, payload = gen_req("POST", "crmactivities?validation=true", body)
        required_tests[name] = {"status": st, "errors": validation_errors(payload)}
    out["requiredFieldValidation"] = required_tests

    firm_a = galenit_id or "3300000101"
    firm_b = "3000000101"
    mismatch_tests: list[dict] = []
    for label, firm_id in (("galenit_firm", firm_a), ("other_firm", firm_b)):
        body = {
            **base,
            "Firm_ID": firm_id,
            "BusTransaction_ID": bc_id,
            "BusOrder_ID": wo_id,
            "BusProject_ID": pr_id,
        }
        st_v, validated = gen_req("POST", "crmactivities?validation=true", body)
        st_c, committed = gen_req("POST", "crmactivities", body)
        act_id = field(committed, "ID", "id") if isinstance(committed, dict) else None
        persisted = {}
        if act_id:
            _, got = gen_req("GET", f"crmactivities/{act_id}")
            persisted = activity_dims(got if isinstance(got, dict) else None)
        mismatch_tests.append(
            {
                "label": label,
                "firmId": firm_id,
                "validate": {"status": st_v, "errors": validation_errors(validated)},
                "create": {"status": st_c, "errors": validation_errors(committed), "activityId": act_id},
                "persisted": persisted,
            }
        )
    out["dimensionWithFirmTests"] = mismatch_tests

    source_id = mismatch_tests[0]["create"]["activityId"] if mismatch_tests else None
    if source_id:
        _, source = gen_req("GET", f"crmactivities/{source_id}")
        child_base = {
            **base,
            "Subject": "4.2A.1 handover source only",
            "Firm_ID": field(source, "Firm_ID", "firm_id") if isinstance(source, dict) else firm_a,
            "Source_ID": source_id,
        }
        st_v, validated = gen_req("POST", "crmactivities?validation=true", child_base)
        st_c, committed = gen_req("POST", "crmactivities", child_base)
        child_id = field(committed, "ID", "id") if isinstance(committed, dict) else None
        child_dims = {}
        if child_id:
            _, child = gen_req("GET", f"crmactivities/{child_id}")
            child_dims = activity_dims(child if isinstance(child, dict) else None)
        out["handoverSourceOnly"] = {
            "sourceId": source_id,
            "sourceDims": activity_dims(source if isinstance(source, dict) else None),
            "validate": {"status": st_v, "errors": validation_errors(validated)},
            "create": {"status": st_c, "activityId": child_id},
            "childDims": child_dims,
            "genAutoInherited": child_dims == activity_dims(source if isinstance(source, dict) else None),
        }

        child_explicit = {
            **child_base,
            "Subject": "4.2A.1 handover explicit copy",
            **{k: v for k, v in {
                "BusTransaction_ID": field(source, "bustransaction_id", "BusTransaction_ID"),
                "BusOrder_ID": field(source, "busorder_id", "BusOrder_ID"),
                "BusProject_ID": field(source, "busproject_id", "BusProject_ID"),
            }.items() if v},
        }
        st_v2, validated2 = gen_req("POST", "crmactivities?validation=true", child_explicit)
        st_c2, committed2 = gen_req("POST", "crmactivities", child_explicit)
        child_id2 = field(committed2, "ID", "id") if isinstance(committed2, dict) else None
        child_dims2 = {}
        if child_id2:
            _, child2 = gen_req("GET", f"crmactivities/{child_id2}")
            child_dims2 = activity_dims(child2 if isinstance(child2, dict) else None)
        out["handoverExplicitCopy"] = {
            "validate": {"status": st_v2, "errors": validation_errors(validated2)},
            "create": {"status": st_c2, "activityId": child_id2},
            "childDims": child_dims2,
        }

    filter_tests: list[dict] = []
    for bo in ("bustransactions", "busorders", "busprojects"):
        for firm_id in filter(None, [galenit_id, firm_a, firm_b]):
            where = quote(f"Firm_ID eq '{firm_id}'")
            st, rows = gen_req("GET", f"{bo}?select={select}&where={where}&take=20")
            filter_tests.append(
                {
                    "bo": bo,
                    "firmId": firm_id,
                    "status": st,
                    "count": len(normalize_list(rows)),
                    "items": normalize_list(rows),
                }
            )
    out["firmFilterTests"] = filter_tests

    _, type_row = gen_req(
        "GET",
        "activitytypes/2000000101?select=ID,BusTransactionReq,BusOrderReq,BusProjectReq",
    )
    out["activityTypeRequirements"] = type_row if isinstance(type_row, dict) else None

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps({"written": OUT_PATH, "galenitId": galenit_id, "referenceActivity": bool(ref_activity)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
