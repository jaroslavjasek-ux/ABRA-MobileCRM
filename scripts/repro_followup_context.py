#!/usr/bin/env python3
"""Reproduce follow-up Description/Answer inheritance against Gen DEMO + adapter."""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

GEN = "http://localhost/demo"
ADAPTER = "http://localhost:5080"
JAROJ = "2620000101"


def basic_auth(user: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def gen_req(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
    headers = {"Accept": "application/json", "Authorization": basic_auth("api", "123")}
    data = json.dumps(body).encode() if body is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(GEN + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
            return resp.status, json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        text = e.read().decode()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:4000]}
        return e.code, payload


def adapter_req(method: str, path: str, body: dict | None = None, token: str | None = None):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(ADAPTER + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def summarize_gen_activity(a: dict, label: str = "") -> None:
    if label:
        print(f"--- {label} ---")
    print(
        "displayname:",
        a.get("displayname") or a.get("DisplayName"),
        "id:",
        a.get("id") or a.get("ID"),
        "status:",
        a.get("status") or a.get("Status"),
        "source:",
        a.get("source_id") or a.get("Source_ID"),
    )
    desc = (a.get("description") or a.get("Description") or "").strip()
    ans = (a.get("answer") or a.get("Answer") or "").strip()
    print("description:", repr(desc[:200]) if desc else "(empty)")
    print("answer:", repr(ans[:200]) if ans else "(empty)")
    print()


def find_by_display_name(name: str) -> list[dict]:
    for clause in (
        f"displayname eq '{name}/2026'",
        f"displayname eq '{name}'",
        f"startswith(displayname,'{name}')",
    ):
        where = urllib.parse.quote(clause)
        st, data = gen_req(
            "GET",
            f"/crmactivities?select=ID,DisplayName,Description,Answer,Status,source_id&where={where}&take=10",
        )
        if st == 200 and (data.get("value") or []):
            return data.get("value") or []
    where = urllib.parse.quote(f"displayname eq '{name}/2026'")
    st, data = gen_req("GET", f"/crmactivities?select=ID,DisplayName,Description,Answer,Status,source_id&where={where}&take=10")
    if st != 200:
        print("search failed", st, data)
        return []
    return data.get("value") or []


def test_post_description_answer(source_id: str) -> None:
    print("=== Direct Gen POST with Description + Answer ===")
    st, source = gen_req("GET", f"/crmactivities/{source_id}")
    if st != 200:
        print("source GET failed", st, source)
        return
    summarize_gen_activity(source, "source before POST")

    src_desc = (source.get("description") or "").strip()
    src_ans = (source.get("answer") or "").strip()
    refs = {
        k: source.get(k)
        for k in (
            "firm_id",
            "activitytype_id",
            "actqueue_id",
            "period_id",
            "division_id",
            "solverrole_id",
            "activityarea_id",
        )
    }
    scheduled = datetime.now(timezone.utc) + timedelta(hours=1)
    body = {
        "Subject": "context inheritance spike",
        "Firm_ID": refs["firm_id"],
        "ActivityType_ID": refs["activitytype_id"],
        "SheduledStart$DATE": scheduled.isoformat().replace("+00:00", "Z"),
        "ResponsibleUser_ID": JAROJ,
        "SolverUser_ID": JAROJ,
        "Source_ID": source_id,
        "ActQueue_ID": refs["actqueue_id"],
        "Period_ID": refs["period_id"],
        "Division_ID": refs["division_id"],
        "SolverRole_ID": refs["solverrole_id"],
        "ActivityArea_ID": refs["activityarea_id"],
        "Description": src_desc or "TEST DESCRIPTION",
        "Answer": src_ans or "TEST ANSWER",
    }
    print("POST body Description/Answer lengths:", len(body["Description"]), len(body["Answer"]))

    st, validate = gen_req("POST", "/crmactivities?validation=true", body)
    print("validate status", st)
    if isinstance(validate, dict):
        meta = (validate.get("@meta") or {}).get("validation") or {}
        print("validate errors", (meta.get("errors") or {}).get("count"))

    st, commit = gen_req("POST", "/crmactivities", body)
    print("commit status", st)
    child_id = None
    if isinstance(commit, dict):
        child_id = commit.get("id") or commit.get("ID")
        summarize_gen_activity(commit, "commit response")
    if not child_id:
        print("no child id", commit)
        return

    st, child = gen_req("GET", f"/crmactivities/{child_id}")
    summarize_gen_activity(child or {}, "child GET after commit")


def test_adapter_complete_flow() -> None:
    print("=== Adapter complete + follow-up ===")
    st, sess = adapter_req("POST", "/api/v1/session", {"loginName": "JANO", "password": "123"})
    if st != 200:
        print("session failed", st, sess)
        return
    token = sess["sessionToken"]

    st, myday = adapter_req("GET", "/api/v1/my-day?take=30", token=token)
    act = None
    for bucket in ("today", "overdue"):
        for row in myday.get(bucket, []):
            if row.get("status") == "inProgress":
                act = row
                break
        if act:
            break
    if not act:
        print("no in-progress activity")
        return

    aid = act["id"]
    print("using activity", aid, act.get("documentNumber"))

    st, before = adapter_req("GET", f"/api/v1/activities/{aid}", token=token)
    print("before description:", repr((before.get("description") or "")[:120]))
    print("before answer:", repr((before.get("answer") or "")[:120]))

    scheduled = datetime.now(timezone.utc) + timedelta(hours=1)
    body = {
        "answer": "repro outcome " + datetime.now().isoformat(),
        "followUp": {
            "enabled": True,
            "subject": "context repro follow-up",
            "scheduledStart": scheduled.isoformat().replace("+00:00", "Z"),
            "assignedUserId": JAROJ,
        },
    }
    st, res = adapter_req("PUT", f"/api/v1/activities/{aid}/complete", body, token=token)
    print("complete status", st)
    fu = (res or {}).get("followUpActivity")
    print("followUp", fu)
    if not fu or not fu.get("id"):
        print("complete response", json.dumps(res, indent=2)[:2000])
        return

    fid = fu["id"]
    st, det = adapter_req("GET", f"/api/v1/activities/{fid}", token=token)
    print("adapter child description:", repr((det.get("description") or "")[:200]))
    print("adapter child answer:", repr((det.get("answer") or "")[:200]))

    st, gen_child = gen_req("GET", f"/crmactivities/{fid}?select=ID,DisplayName,Description,Answer,Status,source_id")
    summarize_gen_activity(gen_child or {}, "gen raw child")


def main() -> None:
    for name in ("NP-17", "NP-18"):
        rows = find_by_display_name(name)
        print(f"=== Search {name}: {len(rows)} ===")
        for row in rows:
            summarize_gen_activity(row)
            if row.get("source_id"):
                st, parent = gen_req(
                    "GET",
                    f"/crmactivities/{row['source_id']}?select=ID,DisplayName,Description,Answer,Status,source_id",
                )
                summarize_gen_activity(parent or {}, "parent")

    rows17 = find_by_display_name("NP-17")
    if rows17:
        test_post_description_answer(rows17[0]["id"])

    try:
        test_adapter_complete_flow()
    except urllib.error.URLError as e:
        print("adapter not reachable:", e)


if __name__ == "__main__":
    main()
