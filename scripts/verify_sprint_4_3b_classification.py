#!/usr/bin/env python3
"""Sprint 4.3B verification: activity classification on standalone create."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5086/api/v1")
GEN = os.environ.get("GEN_URL", "http://localhost/demo")

AREA_ID = "2000000101"
TYPE_TEL = "2000000101"
TYPE_OBCH = "3000000101"
QUEUE_PRHO = "2000000101"
QUEUE_NP = "4000000101"
PERIOD_2026 = "3F80000101"


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
    for q in ("gal", "ab"):
        st, firms = call("GET", f"/firms?q={q}&take=1", token=token)
        if st == 200 and isinstance(firms, dict) and firms.get("items"):
            return firms["items"][0]["id"]
    raise RuntimeError("firm search failed")


def scheduled_start() -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=2)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_with_classification(
    token: str,
    firm_id: str,
    label: str,
    *,
    act_queue_id: str,
    activity_type_id: str,
    activity_area_id: str | None = AREA_ID,
) -> tuple[bool, str, dict | None]:
    body: dict = {
        "subject": f"4.3B verify {label} {int(time.time())}",
        "scheduledStart": scheduled_start(),
        "firmId": firm_id,
        "actQueueId": act_queue_id,
        "activityTypeId": activity_type_id,
    }
    if activity_area_id:
        body["activityAreaId"] = activity_area_id

    st, created = call("POST", "/activities/create", body, token=token)
    if st != 200 or not isinstance(created, dict) or not created.get("id"):
        return False, f"create failed {st}: {created}", None

    activity_id = created["id"]
    gen_row = gen_get(
        f"crmactivities/{activity_id}?select=ID,DisplayName,actqueue_id,activitytype_id,activityarea_id,period_id"
    )
    return True, activity_id, gen_row


def check(name: str, ok: bool, detail: str) -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    return ok


def main() -> int:
    print("Sprint 4.3B — activity classification on standalone create")
    print(f"Adapter: {ADAPTER}")
    print(f"Gen: {GEN}")
    print()

    token = login("JANO")
    firm_id = find_firm_id(token)
    results: list[bool] = []

    # Session contract
    st, sess = call("GET", "/session", token=token)
    clf = (sess or {}).get("activityFeatures", {}).get("classification", {}) if isinstance(sess, dict) else {}
    results.append(check(
        "session classification flags",
        st == 200 and clf.get("area") is True and clf.get("type") is True and clf.get("queue") is True,
        str(clf),
    ))

    # Lookup APIs
    for path, min_count in (("/activity-areas", 1), ("/activity-types", 2), ("/activity-queues", 5)):
        st, data = call("GET", f"{path}?take=50", token=token)
        count = len(data.get("items", [])) if isinstance(data, dict) else 0
        results.append(check(f"GET {path}", st == 200 and count >= min_count, f"status={st} count={count}"))

    # Missing classification rejected
    st, err = call("POST", "/activities/create", {
        "subject": "4.3B missing classification",
        "scheduledStart": scheduled_start(),
        "firmId": firm_id,
    }, token=token)
    results.append(check(
        "missing type/queue rejected",
        st == 422,
        f"status={st}",
    ))

    # NP queue numbering
    ok, activity_id, gen_row = create_with_classification(
        token, firm_id, "np",
        act_queue_id=QUEUE_NP,
        activity_type_id=TYPE_OBCH,
    )
    display = gen_field(gen_row, "DisplayName") or ""
    period = gen_field(gen_row, "period_id")
    results.append(check("create NP queue", ok, activity_id if ok else "failed"))
    results.append(check(
        "NP document prefix",
        bool(re.match(r"^NP-\d+/2026$", display)),
        display,
    ))
    results.append(check("NP period 2026", period == PERIOD_2026, period or "missing"))

    # PrHo queue numbering
    ok, activity_id, gen_row = create_with_classification(
        token, firm_id, "prho",
        act_queue_id=QUEUE_PRHO,
        activity_type_id=TYPE_TEL,
    )
    display = gen_field(gen_row, "DisplayName") or ""
    period = gen_field(gen_row, "period_id")
    results.append(check("create PrHo queue", ok, activity_id if ok else "failed"))
    results.append(check(
        "PrHo document prefix",
        bool(re.match(r"^PrHo-\d+/2026$", display)),
        display,
    ))
    results.append(check("PrHo period 2026", period == PERIOD_2026, period or "missing"))

    # Area auto via omit (Gen merge still applies when area omitted)
    ok, activity_id, gen_row = create_with_classification(
        token, firm_id, "omit-area",
        act_queue_id=QUEUE_PRHO,
        activity_type_id=TYPE_TEL,
        activity_area_id=None,
    )
    area = gen_field(gen_row, "activityarea_id")
    results.append(check("omit area resolved", ok and area == AREA_ID, area or "missing"))

    # Regression: My Day still works
    st, my_day = call("GET", "/my-day", token=token)
    results.append(check("GET /my-day", st == 200 and isinstance(my_day, dict), f"status={st}"))

    print()
    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
