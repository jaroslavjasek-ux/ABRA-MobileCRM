#!/usr/bin/env python3
"""Sprint 3A P0 — follow-up crmactivities POST validate-then-commit spike."""
from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "analysis" / "spikes" / "follow-up-activity-create-results.json"
OUT_MD = ROOT / "analysis" / "spikes" / "follow-up-activity-create.md"

# Gen response (lowercase) -> POST body (PascalCase) fields to merge after validate
MERGE_FIELD_MAP: dict[str, str] = {
    "activityarea_id": "ActivityArea_ID",
    "actqueue_id": "ActQueue_ID",
    "period_id": "Period_ID",
    "division_id": "Division_ID",
    "solverrole_id": "SolverRole_ID",
    "firmoffice_id": "FirmOffice_ID",
    "activityprocess_id": "ActivityProcess_ID",
    "responsiblerole_id": "ResponsibleRole_ID",
}


def load_config() -> dict:
    path = ROOT / "config" / "config.yaml"
    if yaml is None:
        raise RuntimeError("pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def request(
    method: str,
    url: str,
    cfg: dict,
    body: dict | None = None,
) -> tuple[int, Any, str]:
    auth = cfg["abra"]["auth"]
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    token = (auth.get("bearer_token") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        raw = base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
        headers["Authorization"] = f"Basic {raw}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=int(cfg["abra"].get("timeout_sec") or 60)) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else None, text
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw": text[:4000]}
        return e.code, payload, text


def validation_error_count(payload: Any) -> int:
    if not isinstance(payload, dict):
        return 0
    meta = payload.get("@meta") or payload.get("meta") or {}
    validation = meta.get("validation") or {}
    errors = validation.get("errors") or {}
    count = errors.get("count")
    if isinstance(count, int):
        return count
    values = errors.get("values")
    if isinstance(values, list):
        return len(values)
    return 0


def validation_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    meta = payload.get("@meta") or payload.get("meta") or {}
    validation = meta.get("validation") or {}
    errors = validation.get("errors") or {}
    values = errors.get("values") or []
    keys: list[str] = []
    for item in values:
        if isinstance(item, dict):
            keys.extend(item.keys())
    return keys


def get_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    return payload.get("ID") or payload.get("id")


def get_display_name(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    return payload.get("DisplayName") or payload.get("displayname")


def merge_validate_into_body(body: dict[str, Any], validated: dict[str, Any]) -> dict[str, Any]:
    merged = dict(body)
    for src, dest in MERGE_FIELD_MAP.items():
        val = validated.get(src)
        if val is not None and val != "":
            merged[dest] = val
    return merged


def iso_schedule(days_ahead: int = 1) -> str:
    dt = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    dt = dt.replace(hour=10, minute=0, second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def main() -> int:
    cfg = load_config()
    base = cfg["abra"]["base_url"].rstrip("/")
    log: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "spike": "sprint-3a-follow-up-create",
        "steps": [],
        "scenarios": [],
        "findings": {},
    }

    def step(name: str, method: str, path: str, body: dict | None = None) -> tuple[int, Any, str]:
        url = f"{base}/{path.lstrip('/')}"
        status, payload, raw = request(method, url, cfg, body)
        log["steps"].append(
            {
                "name": name,
                "method": method,
                "url": url,
                "status": status,
                "body_sent": body,
                "response": payload,
                "validation_error_count": validation_error_count(payload),
                "validation_error_fields": validation_errors(payload),
            }
        )
        print(f"{name}: HTTP {status} errors={validation_error_count(payload)}")
        return status, payload, raw

    # --- Context: current user ---
    _, user, _ = step("read_currentuser", "GET", "currentuser")
    user_id = get_id(user) if isinstance(user, dict) else None

    # --- Context: completed activity (Status 2 or 3) with firm + type ---
    where = quote("Status eq 2 or Status eq 3")
    select = "ID,DisplayName,Subject,Status,Firm_ID,Person_ID,ActivityType_ID,ResponsibleUser_ID,SolverUser_ID,CreatedBy_ID,SheduledStart$DATE"
    _, completed_list, _ = step(
        "read_completed_activities",
        "GET",
        f"crmactivities?select={select}&where={where}&take=5",
    )

    source: dict[str, Any] | None = None
    if isinstance(completed_list, list):
        for row in completed_list:
            if row.get("Firm_ID") and row.get("ActivityType_ID"):
                source = row
                break
        if source is None and completed_list:
            source = completed_list[0]

    log["source_activity"] = source
    if not source:
        print("No completed activity context found")
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    source_id = source.get("ID")
    firm_id = source.get("Firm_ID")
    type_id = source.get("ActivityType_ID")
    person_id = source.get("Person_ID")
    responsible_id = source.get("ResponsibleUser_ID")
    solver_id = source.get("SolverUser_ID")

    _, source_detail, _ = step("read_source_detail", "GET", f"crmactivities/{source_id}")

    source_refs = {}
    if isinstance(source_detail, dict):
        ref_map = {
            "actqueue_id": "ActQueue_ID",
            "period_id": "Period_ID",
            "division_id": "Division_ID",
            "solverrole_id": "SolverRole_ID",
            "activityarea_id": "ActivityArea_ID",
            "firmoffice_id": "FirmOffice_ID",
            "activityprocess_id": "ActivityProcess_ID",
        }
        for src, dest in ref_map.items():
            val = source_detail.get(src)
            if val is not None and val != "":
                source_refs[dest] = val
    log["source_reference_fields"] = source_refs

    scheduled = iso_schedule(2)

    def run_create_scenario(
        name: str,
        initial_body: dict[str, Any],
        *,
        inherit_source_refs: bool,
        merge_after_validate: bool,
        commit_with_validation_flag: bool,
        max_validate_rounds: int = 3,
    ) -> dict[str, Any]:
        scenario: dict[str, Any] = {
            "name": name,
            "initial_payload": dict(initial_body),
            "inherit_source_refs": inherit_source_refs,
            "merge_after_validate": merge_after_validate,
            "commit_with_validation_flag": commit_with_validation_flag,
        }

        body = dict(initial_body)
        if inherit_source_refs:
            body.update(source_refs)

        validated: Any = None
        err_count = -1
        for round_idx in range(1, max_validate_rounds + 1):
            st_v, validated, _ = step(
                f"{name}_validate_r{round_idx}",
                "POST",
                "crmactivities?validation=true",
                body,
            )
            err_count = validation_error_count(validated)
            if err_count == 0:
                scenario["validate_rounds"] = round_idx
                break
            if merge_after_validate and isinstance(validated, dict):
                body = merge_validate_into_body(body, validated)
            else:
                break

        scenario["validate_status"] = st_v
        scenario["validate_error_count"] = err_count
        scenario["validate_error_fields"] = validation_errors(validated)
        scenario["validate_preview_id"] = get_id(validated) if isinstance(validated, dict) else None
        scenario["validate_preview_displayname"] = get_display_name(validated) if isinstance(validated, dict) else None

        commit_body = dict(body)
        scenario["commit_payload"] = commit_body

        commit_path = "crmactivities?validation=true" if commit_with_validation_flag else "crmactivities"
        st_c, committed, _ = step(f"{name}_commit", "POST", commit_path, commit_body)
        scenario["commit_status"] = st_c
        scenario["commit_error_count"] = validation_error_count(committed)
        scenario["commit_response_id"] = get_id(committed) if isinstance(committed, dict) else None
        scenario["commit_response_displayname"] = get_display_name(committed) if isinstance(committed, dict) else None

        created_id = scenario["commit_response_id"]
        scenario["persisted"] = False
        scenario["persisted_id"] = None
        scenario["persisted_displayname"] = None
        scenario["persisted_status"] = None

        if created_id:
            st_g, got, _ = step(
                f"{name}_get_after_commit",
                "GET",
                f"crmactivities/{created_id}?select=ID,DisplayName,Subject,Status,Firm_ID,ActivityType_ID,ResponsibleUser_ID,SolverUser_ID,SheduledStart$DATE",
            )
            if st_g == 200 and isinstance(got, dict):
                scenario["persisted"] = True
                scenario["persisted_id"] = got.get("ID") or got.get("id")
                scenario["persisted_displayname"] = got.get("DisplayName") or got.get("displayname")
                scenario["persisted_status"] = got.get("Status") if "Status" in got else got.get("status")

        return scenario

    # Scenario A: minimal (no ResponsibleUser_ID)
    minimal_body: dict[str, Any] = {
        "Subject": "Sprint 3A follow-up test (minimal)",
        "Firm_ID": firm_id,
        "ActivityType_ID": type_id,
        "SheduledStart$DATE": scheduled,
        "Description": "P0 spike — safe to delete",
    }
    if person_id and person_id not in ("0000000000", "__________"):
        minimal_body["Person_ID"] = person_id

    log["scenarios"].append(
        run_create_scenario(
            "A_minimal_no_source_refs",
            minimal_body,
            inherit_source_refs=False,
            merge_after_validate=True,
            commit_with_validation_flag=False,
        )
    )

    # Scenario B: user fields + inherited Gen reference fields from completed source
    with_refs = dict(minimal_body)
    with_refs["Subject"] = "Sprint 3A follow-up test (source refs, no owner)"
    log["scenarios"].append(
        run_create_scenario(
            "B_source_refs_no_owner",
            with_refs,
            inherit_source_refs=True,
            merge_after_validate=True,
            commit_with_validation_flag=False,
        )
    )

    # Scenario C: source refs + session owner (recommended follow-up path)
    with_owner = dict(minimal_body)
    with_owner["Subject"] = "Sprint 3A follow-up test (source refs + session owner)"
    if user_id:
        with_owner["ResponsibleUser_ID"] = user_id
        with_owner["SolverUser_ID"] = user_id

    log["scenarios"].append(
        run_create_scenario(
            "C_source_refs_session_owner",
            with_owner,
            inherit_source_refs=True,
            merge_after_validate=True,
            commit_with_validation_flag=False,
        )
    )

    # Scenario D: source refs + inherited owner from completed activity
    inherited_owner = dict(minimal_body)
    inherited_owner["Subject"] = "Sprint 3A follow-up test (source refs + inherited owner)"
    owner = responsible_id or solver_id or user_id
    if owner:
        inherited_owner["ResponsibleUser_ID"] = owner
        inherited_owner["SolverUser_ID"] = owner

    log["scenarios"].append(
        run_create_scenario(
            "D_source_refs_inherited_owner",
            inherited_owner,
            inherit_source_refs=True,
            merge_after_validate=True,
            commit_with_validation_flag=False,
        )
    )

    # Scenario E: commit WITH ?validation=true only (anti-pattern control)
    control_body = dict(with_owner)
    control_body["Subject"] = "Sprint 3A follow-up test (validate-only commit control)"
    log["scenarios"].append(
        run_create_scenario(
            "E_commit_with_validation_flag",
            control_body,
            inherit_source_refs=True,
            merge_after_validate=True,
            commit_with_validation_flag=True,
        )
    )

    # My Day check for first persisted scenario with session owner
    my_day_hit: dict[str, Any] | None = None
    for sc in log["scenarios"]:
        if sc.get("persisted") and sc.get("persisted_id") and user_id:
            pid = sc["persisted_id"]
            ownership_where = quote(
                f"(ResponsibleUser_ID eq '{user_id}' or SolverUser_ID eq '{user_id}' or CreatedBy_ID eq '{user_id}')"
            )
            _, myday_rows, _ = step(
                f"my_day_check_{sc['name']}",
                "GET",
                f"crmactivities?select=ID,DisplayName,Status,SheduledStart$DATE&where={ownership_where}&take=50",
            )
            found = False
            if isinstance(myday_rows, list):
                for row in myday_rows:
                    rid = row.get("ID") or row.get("id")
                    if rid == pid:
                        found = True
                        my_day_hit = {
                            "scenario": sc["name"],
                            "activity_id": pid,
                            "in_ownership_query": True,
                            "status": row.get("Status") if "Status" in row else row.get("status"),
                            "scheduled_start": row.get("SheduledStart$DATE") or row.get("sheduledstart$date"),
                        }
                        break
            if not found:
                my_day_hit = {
                    "scenario": sc["name"],
                    "activity_id": pid,
                    "in_ownership_query": False,
                }
            break

    log["my_day_check"] = my_day_hit

    # Pick best successful scenario
    best = next((s for s in log["scenarios"] if s.get("persisted")), None)
    log["findings"] = {
        "source_activity_id": source_id,
        "successful_scenario": best["name"] if best else None,
        "validation_payload": best["initial_payload"] if best else minimal_body,
        "commit_payload": best["commit_payload"] if best else None,
        "resulting_activity_id": best["persisted_id"] if best else None,
        "resulting_document_number": best["persisted_displayname"] if best else None,
        "merge_required": any(s.get("validate_error_count", 0) > 0 for s in log["scenarios"]),
        "responsible_user_required_for_my_day": not any(
            s.get("persisted") and s["name"] == "B_source_refs_no_owner"
            for s in log["scenarios"]
        ),
        "source_reference_fields_required": any(
            s.get("persisted") for s in log["scenarios"] if s.get("inherit_source_refs")
        ),
        "document_number_auto_generated": bool(best and best.get("persisted_displayname")),
        "my_day_visible": my_day_hit.get("in_ownership_query") if my_day_hit else None,
    }

    if best:
        log["recommended_dto"] = {
            "followUpRequest": {
                "enabled": True,
                "subject": "string (required)",
                "scheduledStart": "ISO-8601 instant (required)",
                "description": "string (optional)",
            },
            "genCreatePayload": {
                "userSupplied": [
                    "Subject",
                    "SheduledStart$DATE",
                    "Description (optional)",
                ],
                "inheritedFromCompletedActivity": [
                    "Firm_ID",
                    "ActivityType_ID",
                    "Person_ID (when set)",
                    "ActQueue_ID",
                    "Period_ID",
                    "Division_ID",
                    "SolverRole_ID",
                    "ActivityArea_ID",
                    "FirmOffice_ID (when set)",
                ],
                "ownership": {
                    "ResponsibleUser_ID": "session rep (recommended for My Day)",
                    "SolverUser_ID": "same as ResponsibleUser_ID on DEMO",
                },
                "genAssigned": ["ID", "DisplayName", "Status (0)", "CreatedBy_ID"],
                "validateThenCommit": {
                    "validate": "POST crmactivities?validation=true",
                    "commit": "POST crmactivities (no validation flag)",
                    "mergeFromValidateResponse": True,
                    "successHttp": [201, 200],
                    "persistCheck": "GET crmactivities/{id}",
                },
            },
            "successfulCommitPayload": best.get("commit_payload"),
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(log)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if best else 1


def write_markdown(log: dict[str, Any]) -> None:
    findings = log.get("findings") or {}
    lines = [
        "# Sprint 3A P0 — Follow-up activity create spike",
        "",
        f"**Run (UTC):** {log.get('at')}",
        f"**Base URL:** {log.get('base_url')}",
        "",
        "## Source context (completed activity)",
        "",
        "```json",
        json.dumps(log.get("source_activity"), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Scenario results",
        "",
    ]

    for sc in log.get("scenarios") or []:
        lines.extend(
            [
                f"### {sc.get('name')}",
                "",
                f"- Validate errors: **{sc.get('validate_error_count')}** `{sc.get('validate_error_fields')}`",
                f"- Commit HTTP: **{sc.get('commit_status')}**",
                f"- Persisted (GET): **{sc.get('persisted')}**",
                f"- ID: `{sc.get('persisted_id')}`",
                f"- DisplayName: `{sc.get('persisted_displayname')}`",
                "",
                "**Validate payload:**",
                "```json",
                json.dumps(sc.get("initial_payload"), ensure_ascii=False, indent=2),
                "```",
                "",
                "**Commit payload:**",
                "```json",
                json.dumps(sc.get("commit_payload"), ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Findings summary",
            "",
            f"- **Successful scenario:** {findings.get('successful_scenario')}",
            f"- **Resulting ID:** `{findings.get('resulting_activity_id')}`",
            f"- **Resulting document number (DisplayName):** `{findings.get('resulting_document_number')}`",
            f"- **Merge validate → commit required:** {findings.get('merge_required')}",
            f"- **Source reference fields required (ActQueue, Period, …):** {findings.get('source_reference_fields_required')}",
            f"- **ResponsibleUser_ID required for My Day:** {findings.get('responsible_user_required_for_my_day')}",
            f"- **Document number auto-generated:** {findings.get('document_number_auto_generated')}",
            f"- **Visible in My Day ownership query:** {findings.get('my_day_visible')}",
            "",
            "## Recommended Sprint 3A follow-up DTO",
            "",
            "See `follow-up-activity-create-results.json` → `recommended_dto` (appended by spike runner if success).",
            "",
            f"**Raw log:** [`follow-up-activity-create-results.json`](follow-up-activity-create-results.json)",
            "",
        ]
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
