#!/usr/bin/env python3
"""Sprint 4.2B.2 — Period_ID resolution investigation (DEMO Gen)."""

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
OUT = "analysis/spikes/sprint-4-2b-2-period-resolution-results.json"

CONFIG_PERIOD = "4000000101"
DESKTOP_PERIOD = "3F80000101"
REF_ACTIVITY = "E120000101"
GALENIT = "4000000101"
ACTIVITY_TYPE = "2000000101"
REF_DEFAULTS = {
    "ActQueue_ID": "2000000101",
    "Period_ID": CONFIG_PERIOD,
    "Division_ID": "2000000101",
    "SolverRole_ID": "1000000101",
    "ActivityArea_ID": "2000000101",
}


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
    return []


def val_errors(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {"count": -1, "values": []}
    meta = payload.get("@meta") or payload.get("meta") or {}
    errs = (meta.get("validation") or {}).get("errors") or {}
    return {"count": errs.get("count", len(errs.get("values") or [])), "values": errs.get("values") or []}


def scheduled_2026() -> str:
    dt = datetime(2026, 6, 11, 15, 40, 0, tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", ".000Z")


def main() -> int:
    out: dict = {"at": datetime.now(timezone.utc).isoformat(), "spike": "sprint-4-2b-2-period-resolution"}

    # Period master data probes
    period_probes: list[dict] = []
    for path in [
        "accountingperiods?take=20",
        "accountingperiods?select=ID,Code,Name,DisplayName,Year,StartDate,EndDate&take=50",
        "periods?take=20",
        "crmperiods?take=20",
    ]:
        st, payload = req("GET", path)
        period_probes.append(
            {
                "path": path,
                "status": st,
                "count": len(norm_list(payload)) if st == 200 else 0,
                "sample": norm_list(payload)[:5] if st == 200 else payload,
            }
        )
    out["periodListProbes"] = period_probes

    for period_id in (CONFIG_PERIOD, DESKTOP_PERIOD):
        st, detail = req("GET", f"accountingperiods/{period_id}")
        if st != 200:
            st, detail = req("GET", f"periods/{period_id}")
        out[f"periodDetail_{period_id}"] = {"status": st, "body": detail}

    # Reference activities
    for act_id in (REF_ACTIVITY,):
        st, act = req("GET", f"crmactivities/{act_id}")
        out[f"activity_{act_id}"] = {
            "displayname": field(act, "DisplayName", "displayname"),
            "period_id": field(act, "period_id", "Period_ID"),
            "sheduledstart": field(act, "sheduledstart$date", "SheduledStart$DATE"),
        }

    # Mobile-like activities with */2006
    st, acts = req(
        "GET",
        "crmactivities?"
        + quote("select=ID,DisplayName,period_id,sheduledstart$date,Subject")
        + "&"
        + quote("where=DisplayName like '*PrHo*2006*'")
        + "&take=5",
    )
    out["mobileLikeActivities2006"] = norm_list(acts)

    st, acts2026 = req(
        "GET",
        "crmactivities?"
        + quote("select=ID,DisplayName,period_id,sheduledstart$date,Subject")
        + "&"
        + quote("where=DisplayName like '*2026*'")
        + "&take=10",
    )
    out["activities2026Display"] = norm_list(acts2026)

    sched = scheduled_2026()
    scenarios: list[dict] = []

    def run_scenario(name: str, body: dict, commit: bool = False) -> dict:
        st_v, validated = req("POST", "crmactivities?validation=true", body)
        result = {
            "name": name,
            "requestBody": body,
            "validateStatus": st_v,
            "validateErrors": val_errors(validated),
            "validatePeriodId": field(validated, "period_id", "Period_ID") if isinstance(validated, dict) else None,
            "validateDisplayName": field(validated, "DisplayName", "displayname") if isinstance(validated, dict) else None,
        }
        if commit:
            st_c, committed = req("POST", "crmactivities", body)
            act_id = field(committed, "ID", "id") if isinstance(committed, dict) else None
            persisted = {}
            if act_id:
                _, got = req("GET", f"crmactivities/{act_id}")
                persisted = {
                    "id": act_id,
                    "displayname": field(got, "DisplayName", "displayname"),
                    "period_id": field(got, "period_id", "Period_ID"),
                    "sheduledstart": field(got, "sheduledstart$date", "SheduledStart$DATE"),
                }
            result["commitStatus"] = st_c
            result["commitErrors"] = val_errors(committed)
            result["persisted"] = persisted
        return result

    base_mobile = {
        "Subject": "4.2B.2 period probe mobile payload",
        "Firm_ID": GALENIT,
        "ActivityType_ID": ACTIVITY_TYPE,
        "SheduledStart$DATE": sched,
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        **REF_DEFAULTS,
    }

    scenarios.append(run_scenario("mobile_config_period_validate_only", base_mobile))
    scenarios.append(run_scenario("mobile_config_period_commit", dict(base_mobile), commit=True))

    no_period = {k: v for k, v in base_mobile.items() if k != "Period_ID"}
    scenarios.append(run_scenario("no_period_validate", no_period))
    merged_body = dict(no_period)
    st_v, validated = req("POST", "crmactivities?validation=true", no_period)
    if isinstance(validated, dict):
        pid = field(validated, "period_id", "Period_ID")
        if pid:
            merged_body["Period_ID"] = pid
        for key in ("ActQueue_ID", "Division_ID", "SolverRole_ID", "ActivityArea_ID"):
            lk = key.lower()
            val = field(validated, key, lk)
            if val:
                merged_body[key] = val
    scenarios.append(run_scenario("validate_merge_then_commit", merged_body, commit=True))

    desktop_period_body = dict(base_mobile)
    desktop_period_body["Period_ID"] = DESKTOP_PERIOD
    scenarios.append(run_scenario("desktop_period_commit", desktop_period_body, commit=True))

    date_only = {
        "Subject": "4.2B.2 date only probe",
        "Firm_ID": GALENIT,
        "ActivityType_ID": ACTIVITY_TYPE,
        "SheduledStart$DATE": sched,
        "ResponsibleUser_ID": "2610000101",
        "SolverUser_ID": "2610000101",
        "ActQueue_ID": REF_DEFAULTS["ActQueue_ID"],
        "Division_ID": REF_DEFAULTS["Division_ID"],
        "SolverRole_ID": REF_DEFAULTS["SolverRole_ID"],
        "ActivityArea_ID": REF_DEFAULTS["ActivityArea_ID"],
    }
    scenarios.append(run_scenario("no_period_no_config_period", date_only))

    out["scenarios"] = scenarios

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps({"written": OUT, "scenarios": len(scenarios)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
