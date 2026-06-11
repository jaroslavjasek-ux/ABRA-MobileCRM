#!/usr/bin/env python3
"""Sprint 4.0B verification: standalone activity create on DEMO Gen."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = "http://localhost:5082/api/v1"
LOGIN = {"loginName": "api", "password": "123"}


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict | list | None]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(f"{ADAPTER}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as ex:
        raw = ex.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return ex.code, payload


def main() -> int:
    results: dict = {"steps": [], "passed": True}

    def step(name: str, ok: bool, detail: dict | None = None) -> None:
        entry = {"name": name, "ok": ok}
        if detail:
            entry.update(detail)
        results["steps"].append(entry)
        if not ok:
            results["passed"] = False
        print(f"{'PASS' if ok else 'FAIL'} {name}")

    st, session = call("POST", "/session", LOGIN)
    token = session.get("sessionToken") if isinstance(session, dict) else None
    step("login", st == 200 and bool(token), {"status": st})

    st, session_get = call("GET", "/session", token=token)
    features = session_get.get("activityFeatures") if isinstance(session_get, dict) else None
    step(
        "session.activityFeatures.createActivity",
        st == 200 and features == {"createActivity": True},
        {"status": st, "activityFeatures": features},
    )

    st, firms = call("GET", "/firms?q=ab&take=5", token=token)
    firm_id = None
    if isinstance(firms, dict) and firms.get("items"):
        firm_id = firms["items"][0]["id"]
    step("firm_search", st == 200 and bool(firm_id), {"status": st, "firmId": firm_id})

    scheduled = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(second=0, microsecond=0)
    create_body = {
        "subject": f"Sprint 4.0B verify {scheduled.strftime('%H:%M')}",
        "scheduledStart": scheduled.isoformat().replace("+00:00", "Z"),
        "firmId": firm_id,
        "description": "Created by verify_standalone_create.py",
    }
    st, created = call("POST", "/activities/create", create_body, token=token)
    activity_id = created.get("id") if isinstance(created, dict) else None
    step(
        "create_standalone",
        st == 200 and bool(activity_id),
        {
            "status": st,
            "activityId": activity_id,
            "documentNumber": created.get("documentNumber") if isinstance(created, dict) else None,
            "error": created.get("error") if isinstance(created, dict) else created,
        },
    )

    if activity_id:
        st, detail = call("GET", f"/activities/{activity_id}", token=token)
        owner_ok = isinstance(detail, dict) and detail.get("ownerId") == session_get.get("representative", {}).get("id")
        status_ok = isinstance(detail, dict) and detail.get("status") == "open"
        doc_ok = isinstance(detail, dict) and bool(detail.get("documentNumber"))
        step(
            "created_detail",
            st == 200 and status_ok and doc_ok and owner_ok,
            {
                "status": st,
                "activityStatus": detail.get("status") if isinstance(detail, dict) else None,
                "documentNumber": detail.get("documentNumber") if isinstance(detail, dict) else None,
                "ownerId": detail.get("ownerId") if isinstance(detail, dict) else None,
            },
        )

        st, my_day = call("GET", "/my-day", token=token)
        today_ids = [a.get("id") for a in my_day.get("today", [])] if isinstance(my_day, dict) else []
        step(
            "my_day_visibility",
            st == 200 and activity_id in today_ids,
            {"status": st, "inToday": activity_id in today_ids},
        )

    out = "analysis/spikes/sprint-4-0b-standalone-create-results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}")
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
