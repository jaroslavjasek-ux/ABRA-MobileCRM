#!/usr/bin/env python3
import base64
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ADAPTER = "http://localhost:5080"
JAROJ = "2620000101"


def req(method, url, body=None, token=None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def main():
    _, sess = req("POST", f"{ADAPTER}/api/v1/session", {"loginName": "JANO", "password": "123"})
    token = sess["sessionToken"]
    print("session rep", sess["representative"]["id"])

    _, myday = req("GET", f"{ADAPTER}/api/v1/my-day?take=20", token=token)
    act = None
    for bucket in ("today", "overdue"):
        for row in myday.get(bucket, []):
            if row.get("status") == "inProgress":
                act = row
                break
        if act:
            break
    if not act:
        for bucket in ("today", "overdue"):
            for row in myday.get(bucket, []):
                if row.get("status") == "open":
                    st, _ = req("PUT", f"{ADAPTER}/api/v1/activities/{row['id']}/start", token=token)
                    if st == 200:
                        act = row
                        break
            if act:
                break
    if not act:
        raise SystemExit("no actionable activity")
    print("activity", act["id"])

    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    body = {
        "answer": "3B.1 bugfix test",
        "followUp": {
            "enabled": True,
            "subject": "assign JAROJ test",
            "scheduledStart": scheduled.isoformat().replace("+00:00", "Z"),
            "assignedUserId": JAROJ,
        },
    }
    print("payload", json.dumps(body))
    st, res = req("PUT", f"{ADAPTER}/api/v1/activities/{act['id']}/complete", body, token)
    print("complete status", st)
    fu = (res or {}).get("followUpActivity")
    print("followUp", fu)
    if fu and fu.get("id"):
        _, det = req("GET", f"{ADAPTER}/api/v1/activities/{fu['id']}", token=token)
        print("detail ownerId", det.get("ownerId"), det.get("ownerDisplayName"))
        auth = "Basic " + base64.b64encode(b"api:123").decode()
        gr = json.load(
            urllib.request.urlopen(
                urllib.request.Request(
                    f"http://localhost/demo/crmactivities/{fu['id']}?select=ID,SolverUser_ID,ResponsibleUser_ID,CreatedBy_ID",
                    headers={"Authorization": auth},
                )
            )
        )
        print("gen raw", gr)


if __name__ == "__main__":
    main()
