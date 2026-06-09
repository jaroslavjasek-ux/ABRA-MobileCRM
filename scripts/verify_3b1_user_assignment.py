#!/usr/bin/env python3
"""Sprint 3B.1 — verify follow-up user assignment via Mobile CRM adapter."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ADAPTER = "http://localhost:5080"
USER_A = "2610000101"  # API
USER_B = "1200000101"  # JANO


def req(method: str, url: str, body: dict | None = None, token: str | None = None) -> tuple[int, object]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            text = resp.read().decode()
            return resp.status, json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        text = e.read().decode()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:2000]}
        return e.code, payload


def login(login_name: str, password: str) -> tuple[str, str]:
    st, data = req("POST", f"{ADAPTER}/api/v1/session", {"loginName": login_name, "password": password})
    if st != 200 or not isinstance(data, dict):
        raise RuntimeError(f"login failed {st}: {data}")
    token = data.get("sessionToken") or ""
    rep_id = (data.get("representative") or {}).get("id") or ""
    return token, rep_id


def my_day_ids(token: str) -> set[str]:
    st, data = req("GET", f"{ADAPTER}/api/v1/my-day?take=50", token=token)
    if st != 200 or not isinstance(data, dict):
        return set()
    ids: set[str] = set()
    for bucket in ("today", "overdue"):
        for row in data.get(bucket) or []:
            if isinstance(row, dict) and row.get("id"):
                ids.add(row["id"])
    return ids


def main() -> None:
    log: dict = {"adapter": ADAPTER}

    token_a, rep_a = login("api", "123")
    log["user_a"] = {"rep_id": rep_a, "login": "api"}

    # Find an in-progress activity for API user to complete
    st, activities = req("GET", f"{ADAPTER}/api/v1/my-day?take=20", token=token_a)
    if st != 200:
        raise SystemExit(f"My Day failed: {st}")

    candidate = None
    for bucket in ("today", "overdue"):
        for row in activities.get(bucket) or []:
            if row.get("status") == "inProgress":
                candidate = row
                break
        if candidate:
            break

    if not candidate:
        # start an open one
        for bucket in ("today", "overdue"):
            for row in activities.get(bucket) or []:
                if row.get("status") == "open" and row.get("canEdit", True):
                    st_s, _ = req("PUT", f"{ADAPTER}/api/v1/activities/{row['id']}/start", token=token_a)
                    if st_s == 200:
                        candidate = row
                        break
            if candidate:
                break

    if not candidate:
        raise SystemExit("No actionable activity for API user")

    activity_id = candidate["id"]
    log["source_activity_id"] = activity_id

    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    complete_body = {
        "answer": "3B.1 assignment verification",
        "followUp": {
            "enabled": True,
            "subject": "3B.1 follow-up assigned to JANO",
            "scheduledStart": scheduled.isoformat().replace("+00:00", "Z"),
            "assignedUserId": USER_B,
        },
    }

    st_c, completed = req(
        "PUT",
        f"{ADAPTER}/api/v1/activities/{activity_id}/complete",
        complete_body,
        token_a,
    )
    log["complete_status"] = st_c
    log["complete_response"] = completed

    if st_c != 200 or not isinstance(completed, dict):
        print(json.dumps(log, indent=2, ensure_ascii=False))
        raise SystemExit("Complete failed")

    follow_up = completed.get("followUpActivity") or {}
    follow_id = follow_up.get("id")
    log["follow_up_id"] = follow_id

    if follow_id:
        st_d, detail = req("GET", f"{ADAPTER}/api/v1/activities/{follow_id}", token=token_a)
        log["follow_up_detail_for_a"] = {"status": st_d, "ownerId": (detail or {}).get("ownerId"), "ownerDisplayName": (detail or {}).get("ownerDisplayName")}

    my_day_a = my_day_ids(token_a)
    log["user_a_my_day_contains_follow_up"] = follow_id in my_day_a if follow_id else None

    try:
        token_b, rep_b = login("JANO", "123")
        log["user_b"] = {"rep_id": rep_b, "login": "JANO"}
        my_day_b = my_day_ids(token_b)
        log["user_b_my_day_contains_follow_up"] = follow_id in my_day_b if follow_id else None

        if follow_id:
            st_start, started = req("PUT", f"{ADAPTER}/api/v1/activities/{follow_id}/start", token=token_b)
            log["user_b_start_status"] = st_start
            if st_start == 200 and isinstance(started, dict):
                st_complete, done = req(
                    "PUT",
                    f"{ADAPTER}/api/v1/activities/{follow_id}/complete",
                    {"answer": "Completed by JANO"},
                    token_b,
                )
                log["user_b_complete_status"] = st_complete
    except Exception as ex:
        log["user_b_error"] = str(ex)

    print(json.dumps(log, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
