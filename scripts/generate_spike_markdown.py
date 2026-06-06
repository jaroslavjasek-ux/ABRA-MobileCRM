#!/usr/bin/env python3
"""Generate spike markdown reports from discovery JSON artefacts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPIKE = ROOT / "architecture" / "reference" / "spike"

# Curated Mobile CRM entity → confirmed / candidate Gen controllers (post-discovery)
ENTITY_VALIDATION: list[dict] = [
    {
        "entity": "Firm",
        "phase": "MVP",
        "expected": "Firm",
        "confirmed": "firms",
        "schema": "firm",
        "mobile_crud": "R",
        "gen_crud": "RCUD",
        "status": "Confirmed",
    },
    {
        "entity": "Contact",
        "phase": "MVP",
        "expected": "Contact (TBD)",
        "confirmed": "persons (+ FirmPersons link)",
        "schema": "person",
        "mobile_crud": "R",
        "gen_crud": "RCUD",
        "status": "Candidate",
    },
    {
        "entity": "Activity",
        "phase": "MVP",
        "expected": "Activity (TBD)",
        "confirmed": "crmactivities",
        "schema": "crmactivity",
        "mobile_crud": "R,C,U",
        "gen_crud": "RCUD",
        "status": "Confirmed",
    },
    {
        "entity": "Activity type / status",
        "phase": "MVP",
        "expected": "Enumerations",
        "confirmed": "crmactivitytypes, crmactivityareas, crmactivityqueues",
        "schema": "—",
        "mobile_crud": "R",
        "gen_crud": "RCUD",
        "status": "Confirmed",
    },
    {
        "entity": "Sales representative",
        "phase": "MVP",
        "expected": "User / Employee (TBD)",
        "confirmed": "currentuser, securityusers, employees",
        "schema": "—",
        "mobile_crud": "R",
        "gen_crud": "R/U",
        "status": "Candidate",
    },
    {
        "entity": "Commercial health signal",
        "phase": "MVP",
        "expected": "Derived from Firm + finance",
        "confirmed": "firms fields (PMState_ID, LimitAmount, Insolvency*, Unreliable*); monthfirminformations; issuedinvoices (detail)",
        "schema": "firm / monthfirminformation",
        "mobile_crud": "R",
        "gen_crud": "R",
        "status": "Partial",
    },
    {
        "entity": "Pipeline snapshot",
        "phase": "MVP optional",
        "expected": "Opportunity aggregate",
        "confirmed": "busorders filtered by Firm_ID",
        "schema": "busorder",
        "mobile_crud": "R",
        "gen_crud": "RCUD",
        "status": "Candidate",
    },
    {
        "entity": "Sales opportunity",
        "phase": "Phase 2",
        "expected": "Opportunity (TBD)",
        "confirmed": "busorders (Zákazka)",
        "schema": "busorder",
        "mobile_crud": "R,C,U",
        "gen_crud": "RCUD",
        "status": "Candidate",
    },
    {
        "entity": "Calendar appointment",
        "phase": "Phase 2",
        "expected": "Calendar (TBD)",
        "confirmed": "No dedicated meeting BO found; schedule on crmactivities (StartDate$, PlannedEndDate$)",
        "schema": "crmactivity",
        "mobile_crud": "R",
        "gen_crud": "RCUD",
        "status": "Gap / merged model",
    },
    {
        "entity": "Sales offer (Quote)",
        "phase": "Phase 2",
        "expected": "Sales offer (TBD)",
        "confirmed": "issuedoffers (ponuka vydaná)",
        "schema": "issuedoffer",
        "mobile_crud": "R,C,U",
        "gen_crud": "RCUD",
        "status": "Confirmed",
    },
    {
        "entity": "Sales order (Order)",
        "phase": "Phase 2",
        "expected": "Sales order (TBD)",
        "confirmed": "issuedorders (objednávka vydaná); busorders is deal not sales order",
        "schema": "issuedorder",
        "mobile_crud": "R,C,U",
        "gen_crud": "RCUD",
        "status": "Confirmed",
    },
    {
        "entity": "Document line",
        "phase": "Phase 2",
        "expected": "Nested lines",
        "confirmed": "issuedofferrows, issuedorderrows (avoid sub-path 26+ pattern)",
        "schema": "nested on header",
        "mobile_crud": "R,C,U,D",
        "gen_crud": "via header",
        "status": "Candidate",
    },
    {
        "entity": "Product",
        "phase": "Phase 2",
        "expected": "StoreCard / Product",
        "confirmed": "storecards; crmproducts (CRM product catalogue)",
        "schema": "storecard / crmproduct",
        "mobile_crud": "R",
        "gen_crud": "RCUD",
        "status": "Confirmed",
    },
    {
        "entity": "Price",
        "phase": "Phase 2",
        "expected": "Derived",
        "confirmed": "Document + storecard pricing fields (TBD spike)",
        "schema": "—",
        "mobile_crud": "R",
        "gen_crud": "R",
        "status": "TBD",
    },
    {
        "entity": "Stock availability",
        "phase": "Phase 2",
        "expected": "Stock view",
        "confirmed": "storecards (expand stock); TBD dedicated stock BO",
        "schema": "storecard",
        "mobile_crud": "R",
        "gen_crud": "R",
        "status": "TBD",
    },
    {
        "entity": "Receivable position",
        "phase": "Phase 2",
        "expected": "Receivable summary",
        "confirmed": "issuedinvoices + firm Balance*/Limit*; duetermlimits",
        "schema": "—",
        "mobile_crud": "R",
        "gen_crud": "R",
        "status": "Partial",
    },
    {
        "entity": "My Day",
        "phase": "MVP",
        "expected": "—",
        "confirmed": "Composite: crmactivities (+ future calendar)",
        "schema": "—",
        "mobile_crud": "—",
        "gen_crud": "—",
        "status": "N/A",
    },
    {
        "entity": "Authentication session",
        "phase": "MVP",
        "expected": "Auth context",
        "confirmed": "currentuser; securityusers",
        "schema": "—",
        "mobile_crud": "C,R,U,D",
        "gen_crud": "—",
        "status": "Candidate",
    },
]


def load(name: str):
    return json.loads((SPIKE / name).read_text(encoding="utf-8"))


def main() -> None:
    index = load("openapis-index.json")
    meta = index["meta"] if "meta" in index else load("discovery-meta.json")
    controllers = index["controllers"]
    print(f"Loaded {len(controllers)} controllers")
    # Markdown generation is in committed files; script reserved for regeneration
    print("See business-object-inventory.md, crm-object-validation.md, gap-analysis.md")


if __name__ == "__main__":
    main()
