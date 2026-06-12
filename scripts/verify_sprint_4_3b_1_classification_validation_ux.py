#!/usr/bin/env python3
"""Sprint 4.3B.1 verification: classification validation UX on standalone create."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5086/api/v1")
GEN = os.environ.get("GEN_URL", "http://localhost/demo")

AREA_TT = "3000000101"
TYPE_TEL = "2000000101"
QUEUE_PRHO = "2000000101"


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


def login(login_name: str, password: str = "123") -> str:
    st, sess = call("POST", "/session", {"loginName": login_name, "password": password})
    if st != 200 or not isinstance(sess, dict) or not sess.get("sessionToken"):
        raise RuntimeError(f"login failed: {st} {sess}")
    return sess["sessionToken"]


def find_firm_id(token: str) -> str:
    for q in ("gal", "ab"):
        st, firms = call("GET", f"/firms?q={q}&take=1", token=token)
        if st == 200 and isinstance(firms, dict) and firms.get("items"):
            return firms["items"][0]["id"]
    raise RuntimeError("firm search failed")


def scheduled_start() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=2)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def error_code(payload: dict | list | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    err = payload.get("error")
    if isinstance(err, dict):
        return err.get("code")
    return None


def error_message(payload: dict | list | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    err = payload.get("error")
    if isinstance(err, dict):
        return err.get("message")
    return None


def check(name: str, ok: bool, detail: str) -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    return ok


def main() -> int:
    print("Sprint 4.3B.1 — classification validation UX")
    print(f"Adapter: {ADAPTER}")
    print()

    token = login("JANO")
    firm_id = find_firm_id(token)
    results: list[bool] = []

    # Valid classification still works
    st, created = call("POST", "/activities/create", {
        "subject": f"4.3B.1 valid {int(time.time())}",
        "scheduledStart": scheduled_start(),
        "firmId": firm_id,
        "activityAreaId": "2000000101",
        "activityTypeId": TYPE_TEL,
        "actQueueId": QUEUE_PRHO,
    }, token=token)
    results.append(check("valid classification creates", st == 200 and isinstance(created, dict), f"status={st}"))

    # TT area + global type/queue → CLASSIFICATION_INVALID
    st, err = call("POST", "/activities/create", {
        "subject": f"4.3B.1 tt invalid {int(time.time())}",
        "scheduledStart": scheduled_start(),
        "firmId": firm_id,
        "activityAreaId": AREA_TT,
        "activityTypeId": TYPE_TEL,
        "actQueueId": QUEUE_PRHO,
    }, token=token)
    code = error_code(err)
    msg = error_message(err) or ""
    results.append(check("TT area returns 422", st == 422, f"status={st}"))
    results.append(check("error code CLASSIFICATION_INVALID", code == "CLASSIFICATION_INVALID", code or "missing"))
    results.append(check(
        "message is not generic Gen rejection",
        "Gen rejected" not in msg,
        msg[:120],
    ))
    results.append(check(
        "message mentions classification",
        "classification" in msg.lower(),
        msg[:120],
    ))

    # Missing queue still VALIDATION_FAILED (unchanged)
    st, err = call("POST", "/activities/create", {
        "subject": f"4.3B.1 missing queue {int(time.time())}",
        "scheduledStart": scheduled_start(),
        "firmId": firm_id,
        "activityTypeId": TYPE_TEL,
    }, token=token)
    results.append(check(
        "adapter missing queue still 422",
        st == 422,
        f"status={st} code={error_code(err)}",
    ))

    print()
    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
