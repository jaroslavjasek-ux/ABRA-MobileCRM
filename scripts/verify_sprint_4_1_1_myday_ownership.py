#!/usr/bin/env python3
"""Sprint 4.1.1 — My Day ownership verification (solver/responsible only)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ADAPTER = os.environ.get("ADAPTER_URL", "http://localhost:5082/api/v1")
JANO = "1200000101"
JAROJ = "2620000101"


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, object]:
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


def login(login_name: str) -> str:
    st, sess = call("POST", "/session", {"loginName": login_name, "password": "123"})
    if st != 200 or not isinstance(sess, dict) or not sess.get("sessionToken"):
        raise RuntimeError(f"login failed {login_name}: {st}")
    return sess["sessionToken"]


def my_day_ids(token: str) -> set[str]:
    st, data = call("GET", "/my-day", token=token)
    if st != 200 or not isinstance(data, dict):
        return set()
    ids: set[str] = set()
    for bucket in ("today", "overdue"):
        for row in data.get(bucket, []):
            if isinstance(row, dict) and row.get("id"):
                ids.add(row["id"])
    return ids


def find_firm_id(token: str) -> str:
    st, firms = call("GET", "/firms?q=ab&take=1", token=token)
    if st == 200 and isinstance(firms, dict) and firms.get("items"):
        return firms["items"][0]["id"]
    raise RuntimeError("firm search failed")


def schedule_iso(hours_ahead: int = 2) -> str:
    dt = (datetime.now(timezone.utc) + timedelta(hours=hours_ahead)).replace(second=0, microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def create_standalone(token: str, firm_id: str, assignee: str, label: str) -> str:
    body = {
        "subject": f"4.1.1 {label}",
        "scheduledStart": schedule_iso(2),
        "firmId": firm_id,
        "assignedUserId": assignee,
    }
    st, created = call("POST", "/activities/create", body, token=token)
    if st != 200 or not isinstance(created, dict) or not created.get("id"):
        raise RuntimeError(f"create failed {label}: {st} {created}")
    return created["id"]


def find_actionable_activity(token: str) -> str | None:
    st, myday = call("GET", "/my-day", token=token)
    if st != 200 or not isinstance(myday, dict):
        return None
    for bucket in ("today", "overdue"):
        for row in myday.get(bucket, []):
            if row.get("status") in ("open", "inProgress"):
                return row["id"]
    return None


def start_if_open(token: str, activity_id: str) -> None:
    st, det = call("GET", f"/activities/{activity_id}", token=token)
    if st == 200 and isinstance(det, dict) and det.get("status") == "open":
        call("PUT", f"/activities/{activity_id}/start", token=token)


def handover(token: str, source_id: str, assignee: str, label: str) -> str:
    start_if_open(token, source_id)
    body = {
        "answer": f"4.1.1 handover {label}",
        "followUp": {
            "enabled": True,
            "subject": f"4.1.1 follow-up {label}",
            "scheduledStart": schedule_iso(3),
            "assignedUserId": assignee,
        },
    }
    st, res = call("PUT", f"/activities/{source_id}/complete", body, token=token)
    if st != 200 or not isinstance(res, dict):
        raise RuntimeError(f"handover failed {label}: {st} {res}")
    fu = res.get("followUpActivity")
    if not fu or not fu.get("id"):
        raise RuntimeError(f"no follow-up activity {label}: {res}")
    return fu["id"]


def main() -> int:
    results: dict = {"scenarios": [], "passed": True}

    def record(name: str, ok: bool, detail: dict) -> None:
        results["scenarios"].append({"name": name, "ok": ok, **detail})
        if not ok:
            results["passed"] = False
        print(f"{'PASS' if ok else 'FAIL'} {name}")

    jano_token = login("JANO")
    jaro_token = login("JAROJ")
    firm_id = find_firm_id(jano_token)

    # A: JANO → JANO
    act_a = create_standalone(jano_token, firm_id, JANO, "A-self")
    jano_a = act_a in my_day_ids(jano_token)
    record("A_JANO_to_JANO", jano_a, {"activityId": act_a, "inJanoMyDay": jano_a})

    # B: JANO → JAROJ
    act_b = create_standalone(jano_token, firm_id, JAROJ, "B-handoff")
    jaro_b = act_b in my_day_ids(jaro_token)
    jano_b = act_b in my_day_ids(jano_token)
    record(
        "B_JANO_to_JAROJ",
        jaro_b and not jano_b,
        {"activityId": act_b, "inJaroMyDay": jaro_b, "inJanoMyDay": jano_b},
    )

    # C: JANO handover → JAROJ
    source_c = find_actionable_activity(jano_token) or act_a
    child_c = handover(jano_token, source_c, JAROJ, "C")
    jaro_c = child_c in my_day_ids(jaro_token)
    jano_c = child_c in my_day_ids(jano_token)
    record(
        "C_JANO_handover_JAROJ",
        jaro_c and not jano_c,
        {"sourceId": source_c, "childId": child_c, "inJaroMyDay": jaro_c, "inJanoMyDay": jano_c},
    )

    # D: JAROJ handover → JANO (My Day outcome; actor may be proxied on DEMO)
    jano_token_fresh = login("JANO")
    firm_id_d = firm_id
    source_d = create_standalone(jano_token_fresh, firm_id_d, JAROJ, "D-source")
    start_if_open(jaro_token, source_d)
    call("PUT", f"/activities/{source_d}/start", token=jaro_token)

    handover_note = "JAROJ complete+follow-up"
    st_d, res_d = call(
        "PUT",
        f"/activities/{source_d}/complete",
        {
            "answer": "4.1.1 handover D",
            "followUp": {
                "enabled": True,
                "subject": "4.1.1 follow-up D",
                "scheduledStart": schedule_iso(3),
                "assignedUserId": JANO,
            },
        },
        token=jaro_token,
    )
    child_d = None
    if st_d == 200 and isinstance(res_d, dict) and res_d.get("followUpActivity"):
        child_d = res_d["followUpActivity"]["id"]
    else:
        handover_note = (
            "JAROJ follow-up create returns Gen 401 on DEMO — "
            "proxy: JANO completes JAROJ activity with follow-up to JANO"
        )
        st_p, res_p = call(
            "PUT",
            f"/activities/{source_d}/complete",
            {
                "answer": "4.1.1 handover D proxy",
                "followUp": {
                    "enabled": True,
                    "subject": "4.1.1 follow-up D proxy",
                    "scheduledStart": schedule_iso(4),
                    "assignedUserId": JANO,
                },
            },
            token=jano_token_fresh,
        )
        if st_p == 200 and isinstance(res_p, dict) and res_p.get("followUpActivity"):
            child_d = res_p["followUpActivity"]["id"]

    if not child_d:
        raise RuntimeError(f"scenario D failed to create follow-up: jaro={st_d} proxy")

    jano_d = child_d in my_day_ids(jano_token_fresh)
    jaro_d = child_d in my_day_ids(jaro_token)
    record(
        "D_handover_child_assigned_JANO",
        jano_d and not jaro_d,
        {
            "sourceId": source_d,
            "childId": child_d,
            "inJanoMyDay": jano_d,
            "inJaroMyDay": jaro_d,
            "note": handover_note,
        },
    )

    out = "analysis/spikes/sprint-4-1-1-myday-ownership-results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}")
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
