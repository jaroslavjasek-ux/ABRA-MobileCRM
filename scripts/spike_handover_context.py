#!/usr/bin/env python3
"""Investigate Description/Answer on DEMO handover chains."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "http://localhost/demo"
DEFAULT_USER = "api"
DEFAULT_PASS = "123"


def load_config() -> dict:
    try:
        import yaml

        return yaml.safe_load((ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))
    except ImportError:
        return {
            "abra": {
                "base_url": DEFAULT_BASE,
                "auth": {"username": DEFAULT_USER, "password": DEFAULT_PASS},
            }
        }


def get(cfg: dict, path: str) -> dict:
    auth = cfg["abra"]["auth"]
    base = cfg["abra"]["base_url"].rstrip("/")
    raw = base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
    headers = {"Authorization": f"Basic {raw}", "Accept": "application/json"}
    req = Request(f"{base}{path}", headers=headers)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def summarize(activity: dict) -> None:
    print(
        activity.get("displayname"),
        "id=",
        activity.get("id"),
        "status=",
        activity.get("status"),
        "source=",
        activity.get("source_id"),
    )
    desc = (activity.get("description") or "").strip()
    ans = (activity.get("answer") or "").strip()
    print("  description:", repr(desc[:120]) if desc else "(empty)")
    print("  answer:", repr(ans[:120]) if ans else "(empty)")
    print()


def main() -> None:
    cfg = load_config()

    print("=== DEMO NP chain (seed) ===")
    for aid in ["6000000101", "8000000101", "9000000101", "A000000101"]:
        summarize(
            get(
                cfg,
                f"/crmactivities/{aid}?select=ID,DisplayName,Subject,Description,Answer,Status,source_id",
            )
        )

    print("=== Recent activities with source_id (take 10) ===")
    rows = get(
        cfg,
        "/crmactivities?select=ID,DisplayName,Description,Answer,Status,source_id&where=source_id ne null&take=10&orderby=ID desc",
    )
    for row in rows.get("value") or rows if isinstance(rows, list) else []:
        if isinstance(row, dict):
            summarize(row)

    print("=== Search NP-15 / NP-16 by DisplayName ===")
    for name in ["NP-15", "NP-16"]:
        q = get(
            cfg,
            f"/crmactivities?select=ID,DisplayName,Description,Answer,Status,source_id&where=displayname eq '{name}/2026' or displayname eq '{name}'&take=5",
        )
        items = q.get("value") or []
        if not items:
            q2 = get(
                cfg,
                f"/crmactivities?select=ID,DisplayName,Description,Answer,Status,source_id&where=contains(displayname,'{name}')&take=5",
            )
            items = q2.get("value") or []
        print(f"--- {name} matches: {len(items)} ---")
        for row in items:
            summarize(row)
            parent = row.get("source_id")
            if parent:
                print("  parent:")
                summarize(
                    get(
                        cfg,
                        f"/crmactivities/{parent}?select=ID,DisplayName,Description,Answer,Status,source_id",
                    )
                )


if __name__ == "__main__":
    main()
