#!/usr/bin/env python3
"""Sprint 4.2B.3 verification: period resolved from activity date on standalone create."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5082/api/v1")
GEN = os.environ.get("GEN_URL", "http://localhost/demo")

PERIOD_2026 = "3F80000101"
PERIOD_2006 = "4000000101"
SCHEDULED_2026 = "2026-06-11T15:40:00.000Z"


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
    with urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
        return payload if isinstance(payload, dict) else None


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
    st, firms = call("GET", "/firms?q=gal&take=1", token=token)
    if st != 200 or not isinstance(firms, dict) or not firms.get("items"):
        st, firms = call("GET", "/firms?q=ab&take=1", token=token)
    if st != 200 or not isinstance(firms, dict) or not firms.get("items"):
        raise RuntimeError(f"firm search failed: {st} {firms}")
    return firms["items"][0]["id"]


def main() -> int:
    print("Sprint 4.2B.3 — period resolution on standalone create")
    print(f"Adapter: {ADAPTER}")
    print(f"Gen: {GEN}")
    print()

    token = login("JANO")
    firm_id = find_firm_id(token)

    body = {
        "subject": f"4.2B.3 period verify {int(time.time())}",
        "scheduledStart": SCHEDULED_2026,
        "firmId": firm_id,
        "assignedUserId": "1200000101",
    }
    st, created = call("POST", "/activities/create", body, token=token)
    if st != 200 or not isinstance(created, dict) or not created.get("id"):
        print(f"[FAIL] create: HTTP {st} {created}")
        return 1

    act_id = created["id"]
    gen_row = gen_get(f"crmactivities/{act_id}?select=ID,DisplayName,period_id,sheduledstart$date")
    period_id = gen_field(gen_row, "period_id")
    display = gen_field(gen_row, "DisplayName") or gen_field(gen_row, "displayname") or ""

    print(f"Activity ID: {act_id}")
    print(f"DisplayName: {display}")
    print(f"period_id: {period_id}")
    print(f"scheduled: {gen_field(gen_row, 'sheduledstart$date')}")
    print()

    failed = 0
    if period_id != PERIOD_2026:
        print(f"[FAIL] expected period_id {PERIOD_2026}, got {period_id!r}")
        failed += 1
    else:
        print("[PASS] period_id is 2026 accounting period")

    if period_id == PERIOD_2006:
        print("[FAIL] still using 2006 period from config")
        failed += 1

    if not re.search(r"/2026$", display):
        print(f"[FAIL] document number should end with /2026, got {display!r}")
        failed += 1
    else:
        print("[PASS] document number ends with /2026")

    # Regression: dimensions endpoint still works
    st, bc = call("GET", "/business-cases?take=1", token=token)
    if st == 200:
        print("[PASS] business-cases lookup")
    else:
        print(f"[FAIL] business-cases lookup HTTP {st}")
        failed += 1

    st, my_day = call("GET", "/my-day", token=token)
    if st == 200:
        print("[PASS] my-day")
    else:
        print(f"[FAIL] my-day HTTP {st}")
        failed += 1

    print()
    if failed:
        print(f"FAILED ({failed} check(s))")
        return 1

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
