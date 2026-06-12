#!/usr/bin/env python3
import base64
import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

GEN = "http://localhost/demo"
AUTH = "Basic " + base64.b64encode(b"api:123").decode()


def req(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    headers = {"Authorization": AUTH, "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = Request(f"{GEN}/{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as ex:
        return ex.code, json.loads(ex.read().decode("utf-8"))


def errs(payload: dict) -> list[dict]:
    meta = payload.get("@meta") or payload.get("meta") or {}
    values = (meta.get("validation") or {}).get("errors", {}).get("values") or []
    out: list[dict] = []
    for value in values:
        for key, detail in value.items():
            if isinstance(detail, dict):
                out.append(
                    {
                        "field": key,
                        "label": detail.get("@displaylabel"),
                        "description": detail.get("@description"),
                        "code": detail.get("@code"),
                    }
                )
    return out


scheduled = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat().replace("+00:00", ".000Z")
base = {
    "Subject": "firm/division probe",
    "ActivityType_ID": "2000000101",
    "SheduledStart$DATE": scheduled,
    "ResponsibleUser_ID": "2610000101",
    "SolverUser_ID": "2610000101",
    "ActQueue_ID": "2000000101",
    "Period_ID": "4000000101",
    "SolverRole_ID": "1000000101",
    "ActivityArea_ID": "2000000101",
}
tests = {
    "no_firm_has_division": {**base, "Division_ID": "2000000101"},
    "no_division_has_firm": {**base, "Firm_ID": "4000000101"},
    "neither": dict(base),
    "both": {**base, "Firm_ID": "4000000101", "Division_ID": "2000000101"},
}
result = {}
for name, body in tests.items():
    st_v, validated = req("POST", "crmactivities?validation=true", body)
    st_c, committed = req("POST", "crmactivities", body)
    result[name] = {
        "validate": {"status": st_v, "errors": errs(validated)},
        "create": {"status": st_c, "errors": errs(committed)},
    }
print(json.dumps(result, indent=2, ensure_ascii=False))
