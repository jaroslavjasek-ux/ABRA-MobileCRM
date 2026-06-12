#!/usr/bin/env python3
"""Sprint 4.2B verification: optional business dimensions on standalone create."""

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
GEN = os.environ.get("GEN_URL", "http://localhost/demo")

BC_ID = "3000000101"
WO_ID = "A000000101"
PROJ_ID = "2000000101"


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
                payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, list) and payload:
                    return payload[0]
                return payload if isinstance(payload, dict) else None
        except HTTPError:
            if attempt < 2:
                time.sleep(0.5)
    return None


def gen_field(row: dict | None, name: str) -> str | None:
    if not row:
        return None
    return row.get(name) or row.get(name.lower())


def login(login_name: str, password: str = "123") -> str:
    st, sess = call("POST", "/session", {"loginName": login_name, "password": password})
    if st != 200 or not isinstance(sess, dict) or not sess.get("sessionToken"):
        raise RuntimeError(f"login failed for {login_name}: {st} {sess}")
    return sess["sessionToken"]


def find_firm_id(token: str) -> str:
    st, firms = call("GET", "/firms?q=ab&take=1", token=token)
    if st != 200 or not isinstance(firms, dict) or not firms.get("items"):
        raise RuntimeError(f"firm search failed: {st} {firms}")
    return firms["items"][0]["id"]


def scheduled_start() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=2)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_activity(token: str, firm_id: str, suffix: str, **dimensions: str | None) -> tuple[bool, str, dict | None]:
    body: dict = {
        "subject": f"4.2B verify {suffix} {int(time.time())}",
        "scheduledStart": scheduled_start(),
        "firmId": firm_id,
    }
    for key, value in dimensions.items():
        if value:
            body[key] = value

    st, created = call("POST", "/activities/create", body, token=token)
    if st != 200 or not isinstance(created, dict) or not created.get("id"):
        return False, f"create failed {st}: {created}", None

    activity_id = created["id"]
    gen_row = gen_get(
        f"crmactivities/{activity_id}?select=ID,BusTransaction_ID,BusOrder_ID,BusProject_ID"
    )
    if not gen_row:
        return False, f"Gen GET failed for {activity_id}", created

    checks = {
        "businessCaseId": ("BusTransaction_ID", dimensions.get("businessCaseId")),
        "workOrderId": ("BusOrder_ID", dimensions.get("workOrderId")),
        "projectId": ("BusProject_ID", dimensions.get("projectId")),
    }
    for label, (gen_name, expected) in checks.items():
        actual = gen_field(gen_row, gen_name)
        if expected:
            if actual != expected:
                return False, f"{label} expected {expected!r}, got {actual!r}", created
        elif actual:
            return False, f"{label} expected empty, got {actual!r}", created

    return True, activity_id, created


def verify_lookups(token: str, firm_id: str) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    endpoints = [
        ("business-cases", BC_ID),
        ("work-orders", WO_ID),
        ("projects", PROJ_ID),
    ]
    for path, sample_id in endpoints:
        st, data = call("GET", f"/{path}?take=10&firmId={firm_id}", token=token)
        if st != 200 or not isinstance(data, dict):
            results.append((path, False, f"HTTP {st}"))
            continue
        items = data.get("items") or []
        if not items:
            results.append((path, False, "empty items"))
            continue
        first = items[0]
        if not first.get("id") or not first.get("displayName"):
            results.append((path, False, f"bad shape: {first}"))
            continue
        has_sample = any(row.get("id") == sample_id for row in items)
        msg = f"{len(items)} items; sample {'found' if has_sample else 'not in page'}"
        results.append((path, True, msg))
    return results


def main() -> int:
    print("Sprint 4.2B — business dimensions on create")
    print(f"Adapter: {ADAPTER}")
    print(f"Gen: {GEN}")
    print()

    token = login("JANO")
    firm_id = find_firm_id(token)

    st, session = call("GET", "/session", token=token)
    dims = (session or {}).get("activityFeatures", {}).get("dimensions", {}) if isinstance(session, dict) else {}
    print(f"Session dimensions flags: {dims}")
    print()

    print("Lookup APIs:")
    for path, ok, msg in verify_lookups(token, firm_id):
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] GET /{path}: {msg}")
    print()

    scenarios = [
        ("none", {}),
        ("businessCase only", {"businessCaseId": BC_ID}),
        ("workOrder only", {"workOrderId": WO_ID}),
        ("project only", {"projectId": PROJ_ID}),
        ("all three", {"businessCaseId": BC_ID, "workOrderId": WO_ID, "projectId": PROJ_ID}),
    ]

    failed = 0
    print("Create scenarios:")
    for name, dimension_kwargs in scenarios:
        ok, msg, _ = create_activity(token, firm_id, name.replace(" ", "-"), **dimension_kwargs)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{status}] {name}: {msg}")

    print()
    if failed:
        print(f"FAILED ({failed} scenario(s))")
        return 1

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
