#!/usr/bin/env python3
"""Sprint 4.1 verification: assignment on standalone activity create."""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5082/api/v1")
GEN = "http://localhost/demo"

JANO = "1200000101"
JAROJ = "2620000101"


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict | list | None]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(f"{ADAPTER}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as ex:
        raw = ex.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return ex.code, payload


def gen_get(path: str) -> dict | None:
    auth = "Basic " + base64.b64encode(b"api:123").decode()
    req = Request(f"{GEN}/{path.lstrip('/')}", headers={"Authorization": auth})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError:
            if attempt < 2:
                time.sleep(0.5)
    return None


def gen_field(row: dict | None, name: str) -> str | None:
    if not row:
        return None
    return row.get(name) or row.get(name.lower())


def login(login_name: str, password: str = "123") -> tuple[str, dict]:
    st, sess = call("POST", "/session", {"loginName": login_name, "password": password})
    if st != 200 or not isinstance(sess, dict) or not sess.get("sessionToken"):
        raise RuntimeError(f"login failed for {login_name}: {st} {sess}")
    return sess["sessionToken"], sess["representative"]


def my_day_ids(token: str) -> set[str]:
    st, data = call("GET", "/my-day", token=token)
    if st != 200 or not isinstance(data, dict):
        return set()
    ids: set[str] = set()
    for bucket in ("today", "overdue"):
        for row in data.get(bucket, []):
            if row.get("id"):
                ids.add(row["id"])
    return ids


def find_firm_id(token: str) -> str:
    st, firms = call("GET", "/firms?q=ab&take=1", token=token)
    if st == 200 and isinstance(firms, dict) and firms.get("items"):
        return firms["items"][0]["id"]
    raise RuntimeError("firm search failed")


def create_activity(token: str, firm_id: str, assigned_user_id: str, label: str) -> dict:
    scheduled = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(second=0, microsecond=0)
    body = {
        "subject": f"Sprint 4.1 {label} {scheduled.strftime('%H%M')}",
        "scheduledStart": scheduled.isoformat().replace("+00:00", "Z"),
        "firmId": firm_id,
        "assignedUserId": assigned_user_id,
    }
    st, created = call("POST", "/activities/create", body, token=token)
    if st != 200 or not isinstance(created, dict) or not created.get("id"):
        raise RuntimeError(f"create failed: {st} {created}")
    return created


def main() -> int:
    results: dict = {"adapter": ADAPTER, "scenarios": [], "passed": True}

    def record(name: str, ok: bool, detail: dict) -> None:
        results["scenarios"].append({"name": name, "ok": ok, **detail})
        if not ok:
            results["passed"] = False
        print(f"{'PASS' if ok else 'FAIL'} {name}")

    jano_token, jano_rep = login("JANO")
    jaro_token, jaro_rep = login("JAROJ")
    firm_id = find_firm_id(jano_token)

    # Scenario A: JANO → JANO
    created_a = create_activity(jano_token, firm_id, JANO, "A-self")
    gen_a = gen_get(f"crmactivities/{created_a['id']}?select=ID,SolverUser_ID,ResponsibleUser_ID,CreatedBy_ID")
    jano_day_a = created_a["id"] in my_day_ids(jano_token)
    record(
        "A_JANO_creates_for_JANO",
        gen_field(gen_a, "SolverUser_ID") == JANO
        and gen_field(gen_a, "ResponsibleUser_ID") == JANO
        and created_a.get("ownerId") == JANO
        and jano_day_a,
        {
            "activityId": created_a["id"],
            "solverUserId": gen_field(gen_a, "SolverUser_ID"),
            "responsibleUserId": gen_field(gen_a, "ResponsibleUser_ID"),
            "createdById": gen_field(gen_a, "CreatedBy_ID"),
            "inJanoMyDay": jano_day_a,
        },
    )

    # Scenario B: JANO → JAROJ
    created_b = create_activity(jano_token, firm_id, JAROJ, "B-handoff")
    gen_b = gen_get(f"crmactivities/{created_b['id']}?select=ID,SolverUser_ID,ResponsibleUser_ID,CreatedBy_ID")
    jaro_day_b = created_b["id"] in my_day_ids(jaro_token)
    jano_day_b = created_b["id"] in my_day_ids(jano_token)
    record(
        "B_JANO_creates_for_JAROJ_assignee_my_day",
        gen_field(gen_b, "SolverUser_ID") == JAROJ
        and gen_field(gen_b, "ResponsibleUser_ID") == JAROJ
        and created_b.get("ownerId") == JAROJ
        and jaro_day_b,
        {
            "activityId": created_b["id"],
            "solverUserId": gen_field(gen_b, "SolverUser_ID"),
            "inJaroMyDay": jaro_day_b,
            "inJanoMyDay": jano_day_b,
            "createdById": gen_field(gen_b, "CreatedBy_ID"),
            "note": "JANO may still see via CreatedBy_ID (Gen platform rule)",
        },
    )

    # Scenario C: JANO → another user (API)
    api_id = "2610000101"
    created_c = create_activity(jano_token, firm_id, api_id, "C-api")
    gen_c = gen_get(f"crmactivities/{created_c['id']}?select=ID,SolverUser_ID,ResponsibleUser_ID,CreatedBy_ID")
    api_token, _ = login("api")
    api_day_c = created_c["id"] in my_day_ids(api_token)
    record(
        "C_JANO_creates_for_API",
        gen_field(gen_c, "SolverUser_ID") == api_id and api_day_c,
        {
            "activityId": created_c["id"],
            "solverUserId": gen_field(gen_c, "SolverUser_ID"),
            "inApiMyDay": api_day_c,
        },
    )

    out = "analysis/spikes/sprint-4-1-assignment-results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}")
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
