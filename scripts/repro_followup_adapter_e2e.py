#!/usr/bin/env python3
"""E2E adapter complete+follow-up with note, verify child Description/Answer."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import os

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5080")
GEN = "http://localhost/demo"
JAROJ = "2620000101"


def adapter(method, path, body=None, token=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(ADAPTER + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, json.loads(resp.read().decode())


def gen_get(activity_id: str) -> dict:
    auth = "Basic " + base64.b64encode(b"api:123").decode()
    req = urllib.request.Request(
        f"{GEN}/crmactivities/{activity_id}",
        headers={"Authorization": auth, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    _, sess = adapter("POST", "/api/v1/session", {"loginName": "JANO", "password": "123"})
    token = sess["sessionToken"]

    _, myday = adapter("GET", "/api/v1/my-day?take=30", token=token)
    act = None
    for bucket in ("today", "overdue"):
        for row in myday.get(bucket, []):
            if row.get("status") in ("open", "inProgress"):
                act = row
                break
        if act:
            break
    if not act:
        raise SystemExit("no open/inProgress activity in My Day")

    aid = act["id"]
    print("activity", aid, act.get("documentNumber"), act.get("status"))

    if act.get("status") == "open":
        adapter("PUT", f"/api/v1/activities/{aid}/start", token=token)

    adapter("PUT", f"/api/v1/activities/{aid}/note", {"note": "E2E note for context repro"}, token=token)

    _, before = adapter("GET", f"/api/v1/activities/{aid}", token=token)
    print("before desc", repr(before.get("description")))
    print("before ans", repr((before.get("answer") or "")[:120]))

    scheduled = datetime.now(timezone.utc) + timedelta(hours=1)
    _, res = adapter(
        "PUT",
        f"/api/v1/activities/{aid}/complete",
        {
            "answer": "E2E outcome " + datetime.now().isoformat(),
            "followUp": {
                "enabled": True,
                "subject": "E2E follow-up context",
                "scheduledStart": scheduled.isoformat().replace("+00:00", "Z"),
                "assignedUserId": JAROJ,
            },
        },
        token=token,
    )
    fu = res.get("followUpActivity")
    print("complete followUp", fu)
    if not fu:
        print(json.dumps(res, indent=2)[:2000])
        return

    fid = fu["id"]
    _, det = adapter("GET", f"/api/v1/activities/{fid}", token=token)
    print("child adapter desc", repr(det.get("description")))
    print("child adapter ans", repr((det.get("answer") or "")[:200]))

    raw = gen_get(fid)
    print(
        "child gen desc",
        repr(raw.get("description") or raw.get("Description")),
        "ans",
        repr((raw.get("answer") or raw.get("Answer") or "")[:200]),
    )


if __name__ == "__main__":
    main()
