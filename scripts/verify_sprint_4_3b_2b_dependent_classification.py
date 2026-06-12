#!/usr/bin/env python3
"""Sprint 4.3B.2B verification: dependent classification selectors via Gen validate probes."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5088/api/v1")

AREA_SP = "2000000101"
AREA_TT = "3000000101"
TYPE_TEL = "2000000101"
TYPE_OBCH = "3000000101"
TYPE_TE = "4000000101"
QUEUE_PRHO = "2000000101"
QUEUE_ODHO = "3000000101"
QUEUE_NP = "4000000101"
QUEUE_PS = "5000000101"
QUEUE_RK = "6000000101"


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict | list | None]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(f"{ADAPTER}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=180) as resp:
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
        raise RuntimeError(f"login failed for {login_name}: {st} {sess}")
    return sess["sessionToken"]


def item_codes(payload: dict | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    items = payload.get("items") or []
    codes: list[str] = []
    for item in items:
        display = str(item.get("displayName") or "")
        code = display.split()[0] if display else str(item.get("code") or item.get("id") or "")
        codes.append(code)
    return codes


def item_ids(payload: dict | None) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    return {str(item.get("id")) for item in (payload.get("items") or []) if item.get("id")}


def check(name: str, ok: bool, detail: str) -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    return ok


def main() -> int:
    print("Sprint 4.3B.2B — dependent classification selectors")
    print(f"Adapter: {ADAPTER}")
    print()

    token = login("JANO")
    passed = 0
    total = 0

    # Scenario A — Sp types
    st, types_sp = call("GET", f"/activity-types?areaId={AREA_SP}&take=50", token=token)
    total += 1
    codes = item_codes(types_sp if isinstance(types_sp, dict) else None)
    ids = item_ids(types_sp if isinstance(types_sp, dict) else None)
    ok = (
        st == 200
        and ids == {TYPE_TEL, TYPE_OBCH}
        and set(codes) >= {"Tel", "Obch"}
    )
    if check("Scenario A — Sp types (Tel, Obch)", ok, f"status={st}, codes={codes}, ids={sorted(ids)}"):
        passed += 1

    # Scenario B — Sp + Tel queues
    st, queues_tel = call(
        "GET",
        f"/activity-queues?areaId={AREA_SP}&activityTypeId={TYPE_TEL}&take=50",
        token=token,
    )
    total += 1
    ids = item_ids(queues_tel if isinstance(queues_tel, dict) else None)
    ok = st == 200 and ids == {QUEUE_PRHO, QUEUE_ODHO}
    if check("Scenario B — Sp+Tel queues (PrHo, OdHo)", ok, f"status={st}, ids={sorted(ids)}"):
        passed += 1

    # Scenario C — Sp + Obch queues
    st, queues_obch = call(
        "GET",
        f"/activity-queues?areaId={AREA_SP}&activityTypeId={TYPE_OBCH}&take=50",
        token=token,
    )
    total += 1
    ids = item_ids(queues_obch if isinstance(queues_obch, dict) else None)
    ok = st == 200 and ids == {QUEUE_NP, QUEUE_PS, QUEUE_RK}
    if check("Scenario C — Sp+Obch queues (NP, PS, RK)", ok, f"status={st}, ids={sorted(ids)}"):
        passed += 1

    # Scenario D — TT types (single Te) + TT+Te queues (empty)
    st, types_tt = call("GET", f"/activity-types?areaId={AREA_TT}&take=50", token=token)
    total += 1
    tt_ids = item_ids(types_tt if isinstance(types_tt, dict) else None)
    ok_tt_types = st == 200 and tt_ids == {TYPE_TE}
    if check("Scenario D — TT types (Te only)", ok_tt_types, f"status={st}, ids={sorted(tt_ids)}"):
        passed += 1

    st, queues_tt = call(
        "GET",
        f"/activity-queues?areaId={AREA_TT}&activityTypeId={TYPE_TE}&take=50",
        token=token,
    )
    total += 1
    tt_queue_ids = item_ids(queues_tt if isinstance(queues_tt, dict) else None)
    ok_tt_queues = st == 200 and len(tt_queue_ids) == 0
    if check("Scenario D — TT+Te queues (empty)", ok_tt_queues, f"status={st}, ids={sorted(tt_queue_ids)}"):
        passed += 1

    # Regression — unfiltered endpoints still work
    st, all_types = call("GET", "/activity-types?take=50", token=token)
    total += 1
    all_type_ids = item_ids(all_types if isinstance(all_types, dict) else None)
    ok = st == 200 and {TYPE_TEL, TYPE_OBCH, TYPE_TE}.issubset(all_type_ids)
    if check("Regression — global activity-types", ok, f"status={st}, count={len(all_type_ids)}"):
        passed += 1

    st, all_queues = call("GET", "/activity-queues?take=50", token=token)
    total += 1
    all_queue_ids = item_ids(all_queues if isinstance(all_queues, dict) else None)
    ok = st == 200 and len(all_queue_ids) >= 5
    if check("Regression — global activity-queues", ok, f"status={st}, count={len(all_queue_ids)}"):
        passed += 1

    # Session classification flags unchanged
    st, sess = call("GET", "/session", token=token)
    total += 1
    clf = (sess or {}).get("activityFeatures", {}).get("classification", {}) if isinstance(sess, dict) else {}
    ok = (
        st == 200
        and clf.get("area") is True
        and clf.get("type") is True
        and clf.get("queue") is True
        and clf.get("autoHideSingleValue") is True
    )
    if check("Regression — session classification flags", ok, f"status={st}, classification={clf}"):
        passed += 1

    print()
    print(f"Result: {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
